"""Preprocessing subsystem: two-layer pipelines, pure scalers, and kernel adapters.

Complies with PRE-01 to PRE-07, ADR-002, RF3.4, and XCUT-02.
"""

from __future__ import annotations

from experimental_ml.models.preprocessing.kernel import (
    PrecomputedKernelAdapter,
)
from experimental_ml.models.preprocessing.pipeline import (
    apply_two_layer_preprocessing,
    fit_two_layer_preprocessing,
    validate_two_layer_preprocessing,
)
from experimental_ml.models.preprocessing.scalers import (
    AngularScaler,
    MaxAbsScaler,
    MinMaxScaler,
    RobustScaler,
    StandardScaler,
)
from experimental_ml.models.preprocessing.types import (
    PreprocessingStepSpec,
    ScalerType,
    TwoLayerPreprocessingSpec,
    TwoLayerPreprocessingState,
)

__all__ = [
    "ScalerType",
    "PreprocessingStepSpec",
    "TwoLayerPreprocessingSpec",
    "TwoLayerPreprocessingState",
    "StandardScaler",
    "MinMaxScaler",
    "MaxAbsScaler",
    "RobustScaler",
    "AngularScaler",
    "PrecomputedKernelAdapter",
    "validate_two_layer_preprocessing",
    "fit_two_layer_preprocessing",
    "apply_two_layer_preprocessing",
]
