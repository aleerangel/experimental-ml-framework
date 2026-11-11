"""Nested cross-validation engine for intra-fold hyperparameter tuning."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from experimental_ml.core.enums import MetricDirection, MetricStatus
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.metrics.catalog import METRICS_CATALOG
from experimental_ml.models.execution import fit_model, instantiate_fresh_model, predict_model
from experimental_ml.models.spec import ModelSpec, validate_model_spec
from experimental_ml.tuning.candidates import generate_candidates
from experimental_ml.tuning.partitioning import split_inner_folds
from experimental_ml.tuning.types import (
    HyperparameterSearchSpec,
    TuningOptimizationError,
    TuningResult,
    TuningTrialRecord,
)
from experimental_ml.tuning.validation import validate_search_spec

__all__ = ["run_nested_tuning"]


def _apply_params_to_instance(instance: Any, params: dict[str, Any]) -> None:
    """Apply candidate hyperparameter dictionary to an estimator instance."""
    if hasattr(instance, "set_params") and callable(instance.set_params):
        instance.set_params(**params)
    else:
        for k, v in params.items():
            try:
                setattr(instance, k, v)
            except Exception:
                pass


def run_nested_tuning(
    spec: HyperparameterSearchSpec,
    model_spec: ModelSpec,
    X_train: np.ndarray,
    y_train: np.ndarray,
    seed: int | None = None,
) -> TuningResult:
    """Execute nested cross-validation hyperparameter search within outer training partition.

    Enforces strict anti-leakage isolation (CA-E4B-01), fresh instance allocation (CA-E3-01),
    and ADR-005 rules regarding UNDEFINED_NAN disqualification.

    Parameters
    ----------
    spec:
        Declarative specification for the hyperparameter search space.
    model_spec:
        Declarative specification of the model to instantiate and tune.
    X_train:
        2D NumPy array of outer training predictors.
    y_train:
        1D NumPy array of outer training targets.
    seed:
        Optional integer override for RNG seed.

    Returns
    -------
    TuningResult
        Consolidated outcome with best parameter configuration and complete trial history.

    Raises
    ------
    ContractViolationError
        If input arrays are invalid, 1D/3D, empty, non-finite, or length mismatched.
    TuningOptimizationError
        If all hyperparameter candidate trials fail, encounter exceptions, or produce UNDEFINED_NAN.
    """
    validate_search_spec(spec)
    validate_model_spec(model_spec)

    if not isinstance(X_train, np.ndarray):
        X_train = np.asarray(X_train)
    if not isinstance(y_train, np.ndarray):
        y_train = np.asarray(y_train)

    if X_train.ndim != 2:
        raise ContractViolationError(
            f"X_train must be a 2D array, got ndim={X_train.ndim} with shape {X_train.shape}"
        )
    if y_train.ndim != 1:
        raise ContractViolationError(
            f"y_train must be a 1D array, got ndim={y_train.ndim} with shape {y_train.shape}"
        )

    n_samples_x = X_train.shape[0]
    n_samples_y = y_train.shape[0]
    if n_samples_x == 0 or n_samples_y == 0:
        raise ContractViolationError("Training arrays cannot be empty")
    if n_samples_x != n_samples_y:
        raise ContractViolationError(
            f"Sample count mismatch: X_train has {n_samples_x}, y_train has {n_samples_y}"
        )

    if not np.all(np.isfinite(X_train)):
        raise ContractViolationError("X_train contains NaN or Inf values")
    if not np.all(np.isfinite(y_train)):
        raise ContractViolationError("y_train contains NaN or Inf values")

    effective_seed = seed if seed is not None else spec.seed
    candidates = generate_candidates(spec)
    inner_splits = split_inner_folds(
        n_samples=n_samples_x,
        n_folds=spec.inner_cv_folds,
        seed=effective_seed,
    )

    metric_id = spec.optimization_metric.strip().lower()
    metric_entry = METRICS_CATALOG[metric_id]

    trials: list[TuningTrialRecord] = []

    for trial_idx, candidate_params in enumerate(candidates):
        fold_scores: list[float] = []
        trial_status = MetricStatus.VALID
        trial_error: str | None = None

        for fold_idx, (inner_train_idx, inner_val_idx) in enumerate(inner_splits):
            X_in_train = X_train[inner_train_idx]
            y_in_train = y_train[inner_train_idx]
            X_in_val = X_train[inner_val_idx]
            y_in_val = y_train[inner_val_idx]

            fold_seed = (
                (effective_seed + trial_idx * 1000 + fold_idx) % (2**31 - 1)
                if effective_seed is not None
                else None
            )

            try:
                # Instantiate fresh unshared model instance (CA-E3-01)
                instance = instantiate_fresh_model(model_spec, seed=fold_seed)
                _apply_params_to_instance(instance, dict(candidate_params))

                # Fit and predict inside inner fold
                fit_model(instance, model_spec, X_in_train, y_in_train)
                preds = predict_model(instance, model_spec, X_in_val)

                if metric_entry.requires_probabilities:
                    y_prob = preds.get("y_proba")
                    if y_prob is None:
                        raise ContractViolationError(
                            f"Model '{model_spec.model_id}' did not produce required y_proba for metric {metric_id!r}"
                        )
                    metric_val = metric_entry.func(y_in_val, y_prob)
                else:
                    y_pred = preds["y_pred"]
                    if y_pred is None:
                        raise ContractViolationError(
                            f"Model '{model_spec.model_id}' did not produce required y_pred"
                        )
                    metric_val = metric_entry.func(y_in_val, y_pred)

                score_float = float(metric_val.value)
                if metric_val.status != MetricStatus.VALID or not math.isfinite(score_float):
                    trial_status = MetricStatus.UNDEFINED_NAN
                    fold_scores.append(float("nan"))
                else:
                    fold_scores.append(score_float)

            except Exception as exc:
                trial_status = MetricStatus.UNDEFINED_NAN
                fold_scores.append(float("nan"))
                trial_error = f"Fold {fold_idx} error: {exc}"

        if trial_status == MetricStatus.VALID and all(math.isfinite(s) for s in fold_scores):
            mean_score = float(np.mean(fold_scores))
        else:
            trial_status = MetricStatus.UNDEFINED_NAN
            mean_score = float("nan")

        trial_record = TuningTrialRecord(
            trial_index=trial_idx,
            params=candidate_params,
            fold_scores=fold_scores,
            mean_score=mean_score,
            status=trial_status,
            error_message=trial_error,
        )
        trials.append(trial_record)

    # Disqualification and total failure verification (ADR-005)
    valid_trials = [t for t in trials if t.status == MetricStatus.VALID and math.isfinite(t.mean_score)]
    if not valid_trials:
        errors = [f"Trial {t.trial_index} ({dict(t.params)}): {t.error_message or 'UNDEFINED_NAN'}" for t in trials]
        raise TuningOptimizationError(
            f"All {len(trials)} hyperparameter candidate trials failed or produced UNDEFINED_NAN. "
            f"Candidate trial summary: {'; '.join(errors)}"
        )

    # Deterministic selection based on optimization direction
    # Primary sort: score according to direction. Secondary sort: lowest trial_index
    if spec.direction == MetricDirection.MAXIMIZE:
        best_trial = max(
            valid_trials,
            key=lambda t: (t.mean_score, -t.trial_index),
        )
    else:
        best_trial = min(
            valid_trials,
            key=lambda t: (t.mean_score, t.trial_index),
        )

    return TuningResult(
        best_params=best_trial.params,
        best_score=best_trial.mean_score,
        best_trial_index=best_trial.trial_index,
        trials=trials,
        search_strategy=spec.search_strategy,
        optimization_metric=spec.optimization_metric,
    )
