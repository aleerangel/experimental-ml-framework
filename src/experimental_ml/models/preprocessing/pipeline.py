"""Two-layer preprocessing pipeline validation, intra-fold fitting, and stateless projection.

Complies with PRE-02 (AC-M42-02-01 to AC-M42-02-04), PRE-03 (AC-M42-03-01 to AC-M42-03-03),
PRE-04 (AC-M42-04-01 to AC-M42-04-03), ADR-002, RF3.4, CA-E3-02, and CA-E4B-01.
"""

from __future__ import annotations

import re
from typing import Any, Set

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.models.preprocessing.types import (
    PreprocessingStepSpec,
    ScalerType,
    TwoLayerPreprocessingSpec,
    TwoLayerPreprocessingState,
)

_STEP_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

_SCALER_TYPES: Set[str] = {
    ScalerType.STANDARD.value,
    ScalerType.MINMAX.value,
    ScalerType.MAXABS.value,
    ScalerType.ROBUST.value,
    ScalerType.ANGULAR.value,
}

_KNOWN_TRANSFORMER_TYPES: Set[str] = _SCALER_TYPES | {
    "PRECOMPUTED_KERNEL",
    "IMPUTER",
    "PASSTHROUGH",
    "CUSTOM",
}


def validate_two_layer_preprocessing(
    spec: TwoLayerPreprocessingSpec,
) -> TwoLayerPreprocessingSpec:
    """Validate a two-layer preprocessing specification and detect accidental duplication.

    Enforces CA-E3-02 by barring redundant scalers or duplicate transformations across
    Layer 1 and Layer 2 before any execution starts.

    Args:
        spec: TwoLayerPreprocessingSpec instance.

    Returns:
        The validated specification unmodified.

    Raises:
        ConfigurationError: If any step has an invalid ID, unrecognized type, or if
            accidental duplication between Layer 1 and Layer 2 is detected.
    """
    if not isinstance(spec, TwoLayerPreprocessingSpec):
        raise ConfigurationError(
            f"Expected TwoLayerPreprocessingSpec, got {type(spec).__name__}"
        )

    layer1_types: set[str] = set()
    layer1_scalers: set[str] = set()
    for i, step in enumerate(spec.layer1_steps):
        if not isinstance(step, PreprocessingStepSpec):
            raise ConfigurationError(
                f"Layer 1 step at index {i} must be a PreprocessingStepSpec, got {type(step).__name__}"
            )
        if not _STEP_ID_PATTERN.match(step.step_id.strip()):
            raise ConfigurationError(
                f"Layer 1 step_id {step.step_id!r} is invalid; must match '^[a-zA-Z0-9_-]+$'"
            )
        ttype = step.transformer_type.upper().strip()
        if ttype not in _KNOWN_TRANSFORMER_TYPES:
            raise ConfigurationError(
                f"Layer 1 step '{step.step_id}' declares unrecognized transformer_type {step.transformer_type!r}"
            )
        layer1_types.add(ttype)
        if ttype in _SCALER_TYPES:
            layer1_scalers.add(ttype)

    layer2_scalers: set[str] = set()
    for i, step in enumerate(spec.layer2_steps):
        if not isinstance(step, PreprocessingStepSpec):
            raise ConfigurationError(
                f"Layer 2 step at index {i} must be a PreprocessingStepSpec, got {type(step).__name__}"
            )
        if not _STEP_ID_PATTERN.match(step.step_id.strip()):
            raise ConfigurationError(
                f"Layer 2 step_id {step.step_id!r} is invalid; must match '^[a-zA-Z0-9_-]+$'"
            )
        ttype = step.transformer_type.upper().strip()
        if ttype not in _KNOWN_TRANSFORMER_TYPES:
            raise ConfigurationError(
                f"Layer 2 step '{step.step_id}' declares unrecognized transformer_type {step.transformer_type!r}"
            )

        # Accidental duplication check (CA-E3-02):
        # 1. Exact same transformation type in both Layer 1 and Layer 2
        if ttype in layer1_types and ttype != "PASSTHROUGH":
            raise ConfigurationError(
                f"Accidental duplication detected (CA-E3-02): transformer_type '{ttype}' "
                f"is declared in both Layer 1 and Layer 2."
            )
        # 2. Both layers declaring numerical scalers (e.g., standardizing twice)
        if ttype in _SCALER_TYPES:
            if layer1_scalers:
                raise ConfigurationError(
                    f"Accidental duplication detected (CA-E3-02): redundant scalers declared "
                    f"in both Layer 1 ({sorted(layer1_scalers)}) and Layer 2 ('{ttype}')."
                )
            layer2_scalers.add(ttype)

    return spec


__all__ = [
    "validate_two_layer_preprocessing",
]
