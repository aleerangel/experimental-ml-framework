"""Unit tests for functional model fitting and analytical bypass.

Covers MOD-04 (AC-M41-04-01 to AC-M41-04-03) and checks C13, C14, C15.
"""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.execution import fit_model
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelDiagnostics, ModelFamily


class MockTrainableModel:
    def __init__(self) -> None:
        self.fitted_with: tuple[np.ndarray, np.ndarray] | None = None
        self.coef_ = None

    def fit(self, X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None) -> MockTrainableModel:
        self.fitted_with = (X, y)
        self.coef_ = np.array([0.5, -0.2])
        return self


class MockAnalyticalModel:
    def __init__(self) -> None:
        self.was_fit_called = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> MockAnalyticalModel:
        self.was_fit_called = True
        return self


def _make_spec(requires_fit: bool = True, supports_sample_weight: bool = False) -> ModelSpec:
    return ModelSpec(
        model_id="test_model",
        display_name="Test Model",
        family=ModelFamily.CLASSICAL_ML if requires_fit else ModelFamily.ANALYTICAL_EQUATION,
        estimator_factory=MockTrainableModel if requires_fit else MockAnalyticalModel,
        capabilities=ModelCapabilities(
            requires_fit=requires_fit,
            supports_sample_weight=supports_sample_weight,
        ),
        description="Test specification",
        scientific_justification="Testing fit behavior",
    )


def test_m41_04_01_fit_model_trainable() -> None:
    """AC-M41-04-01 / C13: fit_model trains trainable model exclusively on training arrays."""
    spec = _make_spec(requires_fit=True)
    model = MockTrainableModel()
    X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    y = np.array([10.0, 20.0, 30.0])

    fitted_model, diag = fit_model(model, spec, X, y)

    assert fitted_model is model
    assert fitted_model.fitted_with is not None
    assert np.array_equal(fitted_model.fitted_with[0], X)
    assert np.array_equal(fitted_model.fitted_with[1], y)
    assert isinstance(diag, ModelDiagnostics)
    assert diag.phase == "fit"
    assert diag.model_id == "test_model"
    assert "coef_" in diag.diagnostics


def test_m41_04_02_fit_model_analytical_bypass() -> None:
    """AC-M41-04-02 / C14: fit_model bypasses training as a transparent no-op when requires_fit=False."""
    spec = _make_spec(requires_fit=False)
    model = MockAnalyticalModel()
    X = np.array([[1.0, 2.0], [3.0, 4.0]])
    y = np.array([1.5, 2.5])

    fitted_model, diag = fit_model(model, spec, X, y)

    assert fitted_model is model
    assert model.was_fit_called is False
    assert isinstance(diag, ModelDiagnostics)
    assert diag.phase == "fit"
    assert diag.diagnostics["requires_fit"] is False


def test_m41_04_03_fit_model_dimension_mismatch_and_empty() -> None:
    """AC-M41-04-03 / C15: fit_model raises ContractViolationError on mismatched or empty arrays."""
    spec = _make_spec(requires_fit=True)
    model = MockTrainableModel()

    # Mismatched sample count
    X_mismatch = np.array([[1.0, 2.0], [3.0, 4.0]])  # 2 samples
    y_mismatch = np.array([10.0, 20.0, 30.0])  # 3 samples
    with pytest.raises(ContractViolationError, match="Mismatched sample counts"):
        fit_model(model, spec, X_mismatch, y_mismatch)

    # Empty arrays
    X_empty = np.empty((0, 2))
    y_empty = np.empty((0,))
    with pytest.raises(ContractViolationError, match="must not be empty"):
        fit_model(model, spec, X_empty, y_empty)

    # 1D X_train (must be 2D)
    X_1d = np.array([1.0, 2.0, 3.0])
    y_1d = np.array([1.0, 2.0, 3.0])
    with pytest.raises(ContractViolationError, match="X_train must be a 2D array"):
        fit_model(model, spec, X_1d, y_1d)

    # 2D y_train (must be 1D)
    X_2d = np.array([[1.0], [2.0]])
    y_2d = np.array([[1.0], [2.0]])
    with pytest.raises(ContractViolationError, match="y_train must be a 1D array"):
        fit_model(model, spec, X_2d, y_2d)
