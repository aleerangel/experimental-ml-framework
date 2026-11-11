"""Two-layer preprocessing pipeline validation, intra-fold fitting, and stateless projection.

Complies with PRE-02 (AC-M42-02-01 to AC-M42-02-04), PRE-03 (AC-M42-03-01 to AC-M42-03-03),
PRE-04 (AC-M42-04-01 to AC-M42-04-03), ADR-002, RF3.4, CA-E3-02, and CA-E4B-01.
"""

from __future__ import annotations

import re
from typing import Any, Set

import numpy as np

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.models.preprocessing.kernel import PrecomputedKernelAdapter
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


def _instantiate_step_transformer(step: PreprocessingStepSpec) -> Any:
    """Instantiate a transformer object from its declarative step specification."""
    ttype = step.transformer_type.upper().strip()
    params = dict(step.parameters)

    if ttype == ScalerType.STANDARD.value:
        return StandardScaler(**params)
    elif ttype == ScalerType.MINMAX.value:
        return MinMaxScaler(**params)
    elif ttype == ScalerType.MAXABS.value:
        return MaxAbsScaler(**params)
    elif ttype == ScalerType.ROBUST.value:
        return RobustScaler(**params)
    elif ttype == ScalerType.ANGULAR.value:
        return AngularScaler(**params)
    elif ttype == "PRECOMPUTED_KERNEL":
        if "kernel_func" not in params or not callable(params["kernel_func"]):
            raise ConfigurationError(
                f"PRECOMPUTED_KERNEL step '{step.step_id}' requires callable 'kernel_func' parameter"
            )
        return PrecomputedKernelAdapter(kernel_func=params["kernel_func"])
    elif ttype == "PASSTHROUGH":
        return None
    elif ttype == "CUSTOM":
        if "factory" in params and callable(params["factory"]):
            return params["factory"]()
        if "transformer" in params:
            return params["transformer"]
        raise ConfigurationError(
            f"CUSTOM step '{step.step_id}' requires 'factory' or 'transformer' parameter"
        )
    raise ConfigurationError(f"Unsupported transformer_type: {ttype}")


def fit_two_layer_preprocessing(
    spec: TwoLayerPreprocessingSpec,
    X_train: np.ndarray,
) -> TwoLayerPreprocessingState:
    """Fit two-layer preprocessing pipeline strictly on training data (CA-E4B-01).

    Layer 1 (Scenario) is fitted on X_train and used to project X_inter.
    Layer 2 (Model-specific) is fitted on X_inter.
    All fitted statistics depend strictly on X_train.

    Args:
        spec: TwoLayerPreprocessingSpec defining Layer 1 and Layer 2 steps.
        X_train: 2D NumPy array of training predictors.

    Returns:
        Immutable TwoLayerPreprocessingState containing fitted transformers.

    Raises:
        ContractViolationError: If X_train is not a 2D array, is empty (N=0),
            or contains non-finite values.
    """
    validate_two_layer_preprocessing(spec)

    if not isinstance(X_train, np.ndarray):
        X_train = np.asarray(X_train)
    if X_train.ndim != 2:
        raise ContractViolationError(
            f"X_train must be a 2D array, got ndim={X_train.ndim} with shape {X_train.shape}"
        )
    if X_train.shape[0] == 0 or X_train.shape[1] == 0:
        raise ContractViolationError(f"X_train must not be empty, got shape {X_train.shape}")
    if not np.all(np.isfinite(X_train)):
        raise ContractViolationError("X_train contains non-finite values (NaN or Inf)")

    current_X = X_train.astype(float, copy=True)
    layer1_fitted: list[Any] = []

    # 1. Fit & Transform Layer 1 steps
    for step_spec in spec.layer1_steps:
        transformer = _instantiate_step_transformer(step_spec)
        if transformer is not None:
            transformer.fit(current_X)
            current_X = transformer.transform(current_X)
        layer1_fitted.append(transformer)

    # 2. Fit & Transform Layer 2 steps on intermediate representation X_inter
    layer2_fitted: list[Any] = []
    for step_spec in spec.layer2_steps:
        transformer = _instantiate_step_transformer(step_spec)
        if transformer is not None:
            transformer.fit(current_X)
            current_X = transformer.transform(current_X)
        layer2_fitted.append(transformer)

    return TwoLayerPreprocessingState(
        spec=spec,
        layer1_fitted_state=tuple(layer1_fitted),
        layer2_fitted_state=tuple(layer2_fitted),
    )


def apply_two_layer_preprocessing(
    state: TwoLayerPreprocessingState,
    X_eval: np.ndarray,
) -> np.ndarray:
    """Project evaluation data through fitted two-layer preprocessing without state mutation.

    Applies Layer 1 followed by Layer 2 using strictly the parameters fitted on training data.

    Args:
        state: TwoLayerPreprocessingState instance.
        X_eval: 2D NumPy array of evaluation predictors.

    Returns:
        Transformed 2D NumPy array.

    Raises:
        ContractViolationError: If X_eval is not a 2D array, is empty, non-finite,
            or if feature count does not match the expected input dimensionality.
    """
    if not isinstance(state, TwoLayerPreprocessingState):
        raise ConfigurationError(
            f"Expected TwoLayerPreprocessingState, got {type(state).__name__}"
        )

    if not isinstance(X_eval, np.ndarray):
        X_eval = np.asarray(X_eval)
    if X_eval.ndim != 2:
        raise ContractViolationError(
            f"X_eval must be a 2D array, got ndim={X_eval.ndim} with shape {X_eval.shape}"
        )
    if X_eval.shape[0] == 0 or X_eval.shape[1] == 0:
        raise ContractViolationError(f"X_eval must not be empty, got shape {X_eval.shape}")
    if not np.all(np.isfinite(X_eval)):
        raise ContractViolationError("X_eval contains non-finite values (NaN or Inf)")

    current_X = X_eval.astype(float, copy=True)

    # 1. Project through Layer 1 steps
    for transformer in state.layer1_fitted_state:
        if transformer is not None:
            if hasattr(transformer, "n_features_in_") and transformer.n_features_in_ is not None:
                if current_X.shape[1] != transformer.n_features_in_:
                    raise ContractViolationError(
                        f"Feature count mismatch in Layer 1: expected {transformer.n_features_in_}, "
                        f"got {current_X.shape[1]}"
                    )
            current_X = transformer.transform(current_X)

    # 2. Project through Layer 2 steps
    for transformer in state.layer2_fitted_state:
        if transformer is not None:
            if hasattr(transformer, "n_features_in_") and transformer.n_features_in_ is not None:
                if current_X.shape[1] != transformer.n_features_in_:
                    raise ContractViolationError(
                        f"Feature count mismatch in Layer 2: expected {transformer.n_features_in_}, "
                        f"got {current_X.shape[1]}"
                    )
            current_X = transformer.transform(current_X)

    return current_X


__all__ = [
    "validate_two_layer_preprocessing",
    "fit_two_layer_preprocessing",
    "apply_two_layer_preprocessing",
]
