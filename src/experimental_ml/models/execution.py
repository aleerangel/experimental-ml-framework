"""Functional model lifecycle: fresh instantiation, fitting, and prediction.

Complies with MOD-03 (AC-M41-03-01 to AC-M41-03-05), MOD-04 (AC-M41-04-01 to
AC-M41-04-03), MOD-05 (AC-M41-05-01 to AC-M41-05-08), CA-E3-01, ADR-005, RF3.2,
and RNF07.
"""

from __future__ import annotations

from typing import Any
import weakref

import numpy as np

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.models.diagnostics import extract_model_diagnostics
from experimental_ml.models.spec import ModelSpec, validate_model_spec
from experimental_ml.models.types import ModelDiagnostics

# Track active model instances to detect singletons and shared memory leakage (AC-M41-03-03, CA-E3-01)
_ACTIVE_INSTANCES: weakref.WeakSet[Any] = weakref.WeakSet()


def reset_active_instances() -> None:
    """Clear the active instances registry (primarily for test fixture isolation)."""
    _ACTIVE_INSTANCES.clear()


def instantiate_fresh_model(model_spec: ModelSpec, seed: int | None = None) -> Any:
    """Instantiate a completely uncoupled, fresh model instance via estimator_factory.

    Enforces strict instance isolation (CA-E3-01) so that weights, states, or hyperparameters
    never leak across folds, splits, or bootstrap resamples.

    Args:
        model_spec: Declarative specification of the model.
        seed: Optional integer seed passed to estimator_factory.

    Returns:
        A newly allocated, unshared model instance.

    Raises:
        ConfigurationError: If model_spec is invalid or estimator_factory fails.
        ContractViolationError: If estimator_factory returns an active singleton or
            previously returned instance.
    """
    validate_model_spec(model_spec)

    try:
        instance = model_spec.estimator_factory(seed)
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to instantiate model '{model_spec.model_id}' with seed {seed}: {exc}"
        ) from exc

    if instance is None:
        raise ConfigurationError(
            f"estimator_factory for model '{model_spec.model_id}' returned None"
        )

    # Detect singleton or reused memory instance (AC-M41-03-03)
    try:
        if instance in _ACTIVE_INSTANCES:
            raise ContractViolationError(
                f"Instance isolation breach: estimator_factory for model '{model_spec.model_id}' "
                f"returned a singleton or previously instantiated active instance {instance!r}."
            )
        _ACTIVE_INSTANCES.add(instance)
    except TypeError:
        # Unhashable object: fallback to checking id among live references
        for live_ref in list(_ACTIVE_INSTANCES):
            if live_ref is instance:
                raise ContractViolationError(
                    f"Instance isolation breach: estimator_factory for model '{model_spec.model_id}' "
                    f"returned an unhashable active singleton instance {instance!r}."
                )

    return instance


def fit_model(
    model: Any,
    model_spec: ModelSpec,
    X_train: np.ndarray,
    y_train: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> tuple[Any, ModelDiagnostics]:
    """Train a model functional unit or transparently bypass when requires_fit=False.

    Enforces sample count consistency, dimensions, and operational capabilities (MOD-04).

    Args:
        model: Freshly instantiated model instance.
        model_spec: Declarative specification of the model.
        X_train: 2D NumPy array of training predictors.
        y_train: 1D NumPy array of training targets.
        sample_weight: Optional 1D NumPy array of sample weights.

    Returns:
        Tuple of (fitted_model, fit_diagnostics).

    Raises:
        ContractViolationError: If X_train or y_train dimensions are invalid,
            if arrays are empty, or if sample counts mismatch.
    """
    validate_model_spec(model_spec)

    if not isinstance(X_train, np.ndarray):
        X_train = np.asarray(X_train)
    if not isinstance(y_train, np.ndarray):
        y_train = np.asarray(y_train)

    # Dimensionality and sample count validation (AC-M41-04-03)
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
        raise ContractViolationError(
            f"Training arrays must not be empty, got N_x={n_samples_x}, N_y={n_samples_y}"
        )

    if n_samples_x != n_samples_y:
        raise ContractViolationError(
            f"Mismatched sample counts between predictors and target: "
            f"X_train has {n_samples_x} samples, y_train has {n_samples_y} samples"
        )

    if sample_weight is not None:
        if not model_spec.capabilities.supports_sample_weight:
            raise ContractViolationError(
                f"Model '{model_spec.model_id}' does not support sample_weight"
            )
        if not isinstance(sample_weight, np.ndarray):
            sample_weight = np.asarray(sample_weight)
        if sample_weight.ndim != 1 or sample_weight.shape[0] != n_samples_x:
            raise ContractViolationError(
                f"sample_weight shape {sample_weight.shape} must be 1D with length {n_samples_x}"
            )

    # Execution or bypass (AC-M41-04-01, AC-M41-04-02, RF3.2)
    if model_spec.capabilities.requires_fit:
        if not hasattr(model, "fit") or not callable(model.fit):
            raise ContractViolationError(
                f"Model '{model_spec.model_id}' declared requires_fit=True but lacks a callable fit() method"
            )
        if sample_weight is not None:
            model.fit(X_train, y_train, sample_weight=sample_weight)
        else:
            model.fit(X_train, y_train)

        # Mark fitted flag on the instance if not already present
        if not hasattr(model, "__is_fitted__"):
            try:
                object.__setattr__(model, "__is_fitted__", True)
            except (AttributeError, TypeError):
                try:
                    model.__is_fitted__ = True
                except Exception:
                    pass
    # If requires_fit=False, model is returned unmodified without invoking fit (AC-M41-04-02)

    fit_diag = extract_model_diagnostics(model, model_spec, phase="fit")
    return model, fit_diag


__all__ = [
    "instantiate_fresh_model",
    "reset_active_instances",
    "fit_model",
]
