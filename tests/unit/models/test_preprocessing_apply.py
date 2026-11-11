"""Unit tests for stateless evaluation projection and state immutability in two-layer preprocessing.

Covers PRE-04 (AC-M42-04-01 to AC-M42-04-03) and checks C12, C13, C14.
"""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.preprocessing.pipeline import (
    apply_two_layer_preprocessing,
    fit_two_layer_preprocessing,
)
from experimental_ml.models.preprocessing.types import (
    PreprocessingStepSpec,
    TwoLayerPreprocessingSpec,
)


def test_m42_04_01_apply_two_layer_preprocessing_projection() -> None:
    """AC-M42-04-01 / C12: apply_two_layer_preprocessing projects evaluation data using strictly stored parameters."""
    s1 = PreprocessingStepSpec(step_id="s1", transformer_type="PASSTHROUGH")
    s2 = PreprocessingStepSpec(step_id="scaler", transformer_type="STANDARD")
    spec = TwoLayerPreprocessingSpec(layer1_steps=(s1,), layer2_steps=(s2,))

    X_train = np.array([[10.0], [20.0], [30.0]])  # mean=20, std=sqrt(200/3)=8.1649658
    state = fit_two_layer_preprocessing(spec, X_train)

    # Evaluation data: sample with 20.0 should project exactly to 0.0 (centered by train mean)
    X_eval = np.array([[20.0]])
    X_eval_proj = apply_two_layer_preprocessing(state, X_eval)

    assert np.allclose(X_eval_proj[0, 0], 0.0)


def test_m42_04_02_apply_two_layer_preprocessing_state_immutability() -> None:
    """AC-M42-04-02 / C13: apply_two_layer_preprocessing never re-estimates or alters any parameter in fitted state."""
    s1 = PreprocessingStepSpec(step_id="s1", transformer_type="PASSTHROUGH")
    s2 = PreprocessingStepSpec(step_id="scaler", transformer_type="STANDARD")
    spec = TwoLayerPreprocessingSpec(layer1_steps=(s1,), layer2_steps=(s2,))

    X_train = np.array([[0.0], [10.0]])  # mean=5.0
    state = fit_two_layer_preprocessing(spec, X_train)

    scaler_before = state.layer2_fitted_state[0]
    mean_before = float(scaler_before.mean_[0])
    scale_before = float(scaler_before.scale_[0])

    # Transform drastically different evaluation data
    X_eval_extreme = np.array([[1000.0], [5000.0]])
    apply_two_layer_preprocessing(state, X_eval_extreme)

    # State parameters must remain completely unchanged
    scaler_after = state.layer2_fitted_state[0]
    assert float(scaler_after.mean_[0]) == mean_before
    assert float(scaler_after.scale_[0]) == scale_before


def test_m42_04_03_apply_two_layer_preprocessing_feature_count_mismatch() -> None:
    """AC-M42-04-03 / C14: apply_two_layer_preprocessing raises ContractViolationError on feature count mismatch."""
    s1 = PreprocessingStepSpec(step_id="scaler", transformer_type="STANDARD")
    spec = TwoLayerPreprocessingSpec(layer1_steps=(s1,))

    X_train = np.array([[1.0, 2.0], [3.0, 4.0]])  # 2 features
    state = fit_two_layer_preprocessing(spec, X_train)

    # Evaluation data with 3 features
    X_eval_bad = np.array([[1.0, 2.0, 3.0]])
    with pytest.raises(ContractViolationError, match="Feature count mismatch"):
        apply_two_layer_preprocessing(state, X_eval_bad)
