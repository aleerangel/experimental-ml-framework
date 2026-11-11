"""Model diagnostics extraction and immutable snapshot creation.

Complies with MOD-06 (AC-M41-06-01 to AC-M41-06-04), ADR-005, RF3.6, and RNF07.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.models.spec import ModelSpec, validate_model_spec
from experimental_ml.models.types import ModelDiagnostics


def _to_immutable_primitive(val: Any) -> Any:
    """Recursively convert values to immutable primitives and MappingProxyType.

    Raises ContractViolationError if an unsupported mutable complex object is encountered
    (AC-M41-06-03).
    """
    if val is None or isinstance(val, (int, float, str, bool, bytes)):
        return val

    if isinstance(val, (np.integer, np.floating, np.bool_)):
        return val.item()

    if isinstance(val, np.ndarray):
        # Convert small or 1D arrays to tuples of primitives
        if val.ndim <= 1:
            return tuple(x.item() if hasattr(x, "item") else x for x in val)
        return tuple(_to_immutable_primitive(row) for row in val)

    if isinstance(val, (list, tuple, set, frozenset)):
        return tuple(_to_immutable_primitive(item) for item in val)

    if isinstance(val, Mapping):
        converted_mapping = {
            str(k): _to_immutable_primitive(v) for k, v in val.items()
        }
        return MappingProxyType(converted_mapping)

    # If it's a known non-primitive complex object (function, generator, thread, socket, arbitrary custom class)
    # that is not handled, raise ContractViolationError per AC-M41-06-03
    raise ContractViolationError(
        f"Unsupported mutable complex object in model diagnostics: {type(val).__name__} ({val!r})"
    )


def extract_model_diagnostics(
    model: Any,
    model_spec: ModelSpec,
    phase: str = "fit",
) -> ModelDiagnostics:
    """Extract an independent, immutable snapshot of internal model diagnostics.

    Guarantees deep snapshot immutability (AC-M41-06-02) such that mutating the fitted
    model after extraction never alters the returned ModelDiagnostics, and extraction
    never mutates the model itself (AC-M41-06-04).

    Args:
        model: Model instance (fitted or analytical).
        model_spec: Declarative specification for the model.
        phase: Execution phase name (default: 'fit').

    Returns:
        Immutable ModelDiagnostics snapshot.

    Raises:
        ContractViolationError: If unsupported mutable complex objects are encountered.
        ConfigurationError: If model_spec or phase is invalid.
    """
    validate_model_spec(model_spec)
    if not isinstance(phase, str) or not phase.strip():
        raise ConfigurationError(f"phase must be a non-empty string, got {phase!r}")

    extracted_dict: dict[str, Any] = {}

    # 1. Custom get_diagnostics() method if present
    if hasattr(model, "get_diagnostics") and callable(model.get_diagnostics):
        try:
            custom_diag = model.get_diagnostics()
            if isinstance(custom_diag, Mapping):
                for k, v in custom_diag.items():
                    extracted_dict[str(k)] = _to_immutable_primitive(v)
            else:
                raise ContractViolationError(
                    f"get_diagnostics() must return a Mapping, got {type(custom_diag).__name__}"
                )
        except ContractViolationError:
            raise
        except Exception as exc:
            raise ContractViolationError(f"Error calling get_diagnostics() on model: {exc}") from exc
    else:
        # 2. Inspect attributes ending with '_' (canonical scikit-learn / estimator pattern)
        if hasattr(model, "__dict__"):
            for attr_name, attr_val in model.__dict__.items():
                if attr_name.endswith("_") and not attr_name.startswith("_"):
                    extracted_dict[attr_name] = _to_immutable_primitive(attr_val)

    # 3. Always include model_spec parameters for context
    extracted_dict["model_id"] = model_spec.model_id
    extracted_dict["family"] = model_spec.family.value
    extracted_dict["requires_fit"] = model_spec.capabilities.requires_fit

    now_iso = datetime.now(timezone.utc).isoformat()

    return ModelDiagnostics(
        model_id=model_spec.model_id,
        phase=phase.strip(),
        diagnostics=MappingProxyType(extracted_dict),
        extracted_at=now_iso,
    )


__all__ = [
    "extract_model_diagnostics",
]
