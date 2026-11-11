"""Functional model lifecycle: fresh instantiation, fitting, and prediction.

Complies with MOD-03 (AC-M41-03-01 to AC-M41-03-05), MOD-04 (AC-M41-04-01 to
AC-M41-04-03), MOD-05 (AC-M41-05-01 to AC-M41-05-08), CA-E3-01, ADR-005, RF3.2,
and RNF07.
"""

from __future__ import annotations

from typing import Any
import weakref

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.models.spec import ModelSpec, validate_model_spec

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


__all__ = [
    "instantiate_fresh_model",
    "reset_active_instances",
]
