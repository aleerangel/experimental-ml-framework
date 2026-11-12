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

class _ActiveInstancesRegistry:
    """Identity-based active instances registry to detect singletons and shared memory leakage.

    Complies with MOD-03 (AC-M41-03-03), CA-E3-01, and AUD-M4-02.
    Checks strictly object identity ('is'), never value equality ('=='), and supports both
    hashable and unhashable model objects without memory retention.
    """

    def __init__(self) -> None:
        self._refs: dict[int, weakref.ref[Any]] = {}
        self._non_weakable: set[int] = set()

    def register_or_check(self, instance: Any, model_id: str) -> None:
        """Register instance or raise ContractViolationError if it is already active."""
        obj_id = id(instance)

        # Check weakref registry
        if obj_id in self._refs:
            live = self._refs[obj_id]()
            if live is not None and live is instance:
                raise ContractViolationError(
                    f"Instance isolation breach: estimator_factory for model '{model_id}' "
                    f"returned a singleton or previously instantiated active instance {instance!r}."
                )

        # Check non-weakable fallback
        if obj_id in self._non_weakable:
            raise ContractViolationError(
                f"Instance isolation breach: estimator_factory for model '{model_id}' "
                f"returned a singleton or previously instantiated active instance {instance!r}."
            )

        def _cleanup(ref: weakref.ref[Any], target_id: int = obj_id) -> None:
            self._refs.pop(target_id, None)

        try:
            self._refs[obj_id] = weakref.ref(instance, _cleanup)
        except TypeError:
            self._non_weakable.add(obj_id)

    def clear(self) -> None:
        self._refs.clear()
        self._non_weakable.clear()


# Track active model instances by identity to detect singletons and shared memory leakage (AC-M41-03-03, CA-E3-01, AUD-M4-02)
_ACTIVE_INSTANCES = _ActiveInstancesRegistry()


def reset_active_instances() -> None:
    """Clear the active instances registry (primarily for test fixture isolation)."""
    _ACTIVE_INSTANCES.clear()


def instantiate_fresh_model(model_spec: ModelSpec, seed: int | None = None) -> Any:
    """Instantiate a completely uncoupled, fresh model instance via estimator_factory.

    Enforces strict instance isolation (CA-E3-01, AUD-M4-02) so that weights, states, or hyperparameters
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

    # Detect singleton or reused memory instance by identity (AUD-M4-02)
    _ACTIVE_INSTANCES.register_or_check(instance, model_spec.model_id)

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


def _is_model_fitted(model: Any) -> bool:
    """Check whether a model instance has been fitted."""
    if hasattr(model, "__is_fitted__"):
        return bool(model.__is_fitted__)
    if hasattr(model, "is_fitted"):
        attr = getattr(model, "is_fitted")
        return bool(attr() if callable(attr) else attr)
    if hasattr(model, "__dict__"):
        for k in model.__dict__:
            if k.endswith("_") and not k.startswith("_"):
                return True
    return False


def predict_model(
    model: Any,
    model_spec: ModelSpec,
    X_eval: np.ndarray,
) -> dict[str, np.ndarray | None]:
    """Execute model prediction and enforce standard tripartite output verification.

    Returns a standardized dictionary containing 'y_pred', 'y_std', and 'y_proba' (MOD-05).

    Args:
        model: Fitted model instance or analytical model.
        model_spec: Declarative specification of the model.
        X_eval: 2D NumPy array of evaluation predictors.

    Returns:
        Dictionary with keys 'y_pred', 'y_std', and 'y_proba'.

    Raises:
        ContractViolationError: If model is unfitted, if X_eval dimensions are invalid,
            or if outputs violate declared capabilities (dimensions, bounds, non-negativity).
    """
    validate_model_spec(model_spec)

    if not isinstance(X_eval, np.ndarray):
        X_eval = np.asarray(X_eval)

    if X_eval.ndim != 2:
        raise ContractViolationError(
            f"X_eval must be a 2D array, got ndim={X_eval.ndim} with shape {X_eval.shape}"
        )

    n_samples = X_eval.shape[0]
    if n_samples == 0:
        raise ContractViolationError("X_eval must not be empty (N=0)")

    # Verify fitted state for trainable models (AC-M41-05-06)
    if model_spec.capabilities.requires_fit and not _is_model_fitted(model):
        raise ContractViolationError(
            f"Model '{model_spec.model_id}' declared requires_fit=True but has not been fitted."
        )

    if not hasattr(model, "predict") or not callable(model.predict):
        raise ContractViolationError(
            f"Model '{model_spec.model_id}' lacks a callable predict() method."
        )

    # 1. Prediction & Uncertainty acquisition
    y_pred: np.ndarray | None = None
    y_std: np.ndarray | None = None

    if model_spec.capabilities.supports_uncertainty:
        if hasattr(model, "predict_std") and callable(model.predict_std):
            y_pred = model.predict(X_eval)
            y_std = model.predict_std(X_eval)
        elif hasattr(model, "predict_uncertainty") and callable(model.predict_uncertainty):
            y_pred = model.predict(X_eval)
            y_std = model.predict_uncertainty(X_eval)
        else:
            try:
                res = model.predict(X_eval, return_std=True)
                if isinstance(res, tuple) and len(res) == 2:
                    y_pred, y_std = res
                else:
                    y_pred = res
            except (TypeError, Exception):
                y_pred = model.predict(X_eval)
    else:
        y_pred = model.predict(X_eval)

    # 2. Validate y_pred (AC-M41-05-01)
    if y_pred is None:
        raise ContractViolationError(f"Model '{model_spec.model_id}' predict() returned None")
    if not isinstance(y_pred, np.ndarray):
        y_pred = np.asarray(y_pred)
    if y_pred.ndim != 1 or y_pred.shape[0] != n_samples:
        raise ContractViolationError(
            f"y_pred shape {y_pred.shape} must be a 1D array of length {n_samples}"
        )

    # 3. Validate y_std (AC-M41-05-02, AC-M41-05-04, AC-M41-05-07)
    if model_spec.capabilities.supports_uncertainty:
        if y_std is None:
            raise ContractViolationError(
                f"Model '{model_spec.model_id}' declared supports_uncertainty=True "
                f"but produced None for y_std."
            )
        if not isinstance(y_std, np.ndarray):
            y_std = np.asarray(y_std)
        if y_std.ndim != 1 or y_std.shape[0] != n_samples:
            raise ContractViolationError(
                f"y_std shape {y_std.shape} must be a 1D array of length {n_samples}"
            )
        if not np.all(np.isfinite(y_std)):
            raise ContractViolationError(
                f"y_std contains non-finite values (NaN or Inf)"
            )
        if np.any(y_std < 0.0):
            raise ContractViolationError(
                f"y_std contains negative uncertainty values (< 0.0)"
            )
    else:
        y_std = None

    # 4. Validate y_proba (AC-M41-05-03, AC-M41-05-05, AC-M41-05-08)
    y_proba: np.ndarray | None = None
    if model_spec.capabilities.supports_predict_proba:
        if not hasattr(model, "predict_proba") or not callable(model.predict_proba):
            raise ContractViolationError(
                f"Model '{model_spec.model_id}' declared supports_predict_proba=True "
                f"but lacks a callable predict_proba() method."
            )
        raw_proba = model.predict_proba(X_eval)
        if raw_proba is None:
            raise ContractViolationError(
                f"Model '{model_spec.model_id}' predict_proba() returned None"
            )
        if not isinstance(raw_proba, np.ndarray):
            y_proba = np.asarray(raw_proba)
        else:
            y_proba = raw_proba

        if y_proba.ndim != 2 or y_proba.shape[0] != n_samples:
            raise ContractViolationError(
                f"y_proba shape {y_proba.shape} must be 2D with {n_samples} rows."
            )
        if not np.all(np.isfinite(y_proba)):
            raise ContractViolationError("y_proba contains non-finite values (NaN or Inf)")
        if np.any(y_proba < 0.0) or np.any(y_proba > 1.0):
            raise ContractViolationError(
                "y_proba values must be strictly bounded in [0.0, 1.0]"
            )
        row_sums = np.sum(y_proba, axis=1)
        if not np.allclose(row_sums, 1.0, atol=1e-5):
            raise ContractViolationError(
                f"y_proba row sums must equal 1.0 within numerical tolerance, got {row_sums}"
            )
    else:
        # Strictly None even if supports_decision_function is True (AC-M41-05-05)
        y_proba = None

    return {
        "y_pred": y_pred,
        "y_std": y_std,
        "y_proba": y_proba,
    }


__all__ = [
    "instantiate_fresh_model",
    "reset_active_instances",
    "fit_model",
    "predict_model",
]
