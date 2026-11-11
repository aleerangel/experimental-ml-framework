"""Unit tests for intra-fold two-layer preprocessing fitting and anti-leakage guarantees.

Covers PRE-03 (AC-M42-03-01 to AC-M42-03-03) and checks C9, C10, C11.
"""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.preprocessing.pipeline import fit_two_layer_preprocessing
from experimental_ml.models.preprocessing.types import (
    PreprocessingStepSpec,
    TwoLayerPreprocessingSpec,
    TwoLayerPreprocessingState,
)


def test_m42_03_01_fit_two_layer_preprocessing_execution() -> None:
    """AC-M42-03-01 / C9: fit_two_layer_preprocessing fits Layer 1 and Layer 2 sequentially with intermediate projection."""
    s1 = PreprocessingStepSpec(step_id="step_l1", transformer_type="PASSTHROUGH")
    s2 = PreprocessingStepSpec(step_id="step_l2", transformer_type="STANDARD")

    spec = TwoLayerPreprocessingSpec(layer1_steps=(s1,), layer2_steps=(s2,))
    X_train = np.array([[10.0, 20.0], [30.0, 40.0], [50.0, 60.0]])

    state = fit_two_layer_preprocessing(spec, X_train)

    assert isinstance(state, TwoLayerPreprocessingState)
    assert len(state.layer1_fitted_state) == 1
    assert len(state.layer2_fitted_state) == 1
    # Check that Layer 2 scaler was fitted on intermediate array
    scaler_l2 = state.layer2_fitted_state[0]
    assert scaler_l2 is not None
    assert scaler_l2.is_fitted is True
    assert np.allclose(scaler_l2.mean_, [30.0, 40.0])


def test_m42_03_02_fit_two_layer_preprocessing_anti_leakage() -> None:
    """AC-M42-03-02 / C10: All statistics depend strictly on X_train without referencing evaluation data (CA-E4B-01)."""
    s1 = PreprocessingStepSpec(step_id="s1", transformer_type="PASSTHROUGH")
    s2 = PreprocessingStepSpec(step_id="s2", transformer_type="STANDARD")
    spec = TwoLayerPreprocessingSpec(layer1_steps=(s1,), layer2_steps=(s2,))

    X_train_only = np.array([[0.0], [10.0]])
    state = fit_two_layer_preprocessing(spec, X_train_only)
    scaler = state.layer2_fitted_state[0]

    # Mean must be exactly 5.0, computed solely on X_train_only
    assert scaler.mean_[0] == 5.0


def test_m42_03_03_fit_two_layer_preprocessing_invalid_inputs() -> None:
    """AC-M42-03-03 / C11: fit_two_layer_preprocessing raises ContractViolationError on 1D, empty, or non-finite inputs."""
    spec = TwoLayerPreprocessingSpec()

    # 1D array
    with pytest.raises(ContractViolationError, match="must be a 2D array"):
        fit_two_layer_preprocessing(spec, np.array([1.0, 2.0]))

    # Empty array (N=0)
    with pytest.raises(ContractViolationError, match="must not be empty"):
        fit_two_layer_preprocessing(spec, np.empty((0, 2)))

    # Non-finite values
    with pytest.raises(ContractViolationError, match="contains non-finite values"):
        fit_two_layer_preprocessing(spec, np.array([[1.0, float("nan")], [2.0, 3.0]]))
