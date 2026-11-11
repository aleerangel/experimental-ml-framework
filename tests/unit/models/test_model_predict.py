"""Unit tests for functional model prediction and tripartite output contracts.

Covers MOD-05 (AC-M41-05-01 to AC-M41-05-08) and checks C16, C17, C18, C19, C20, C21, C22, C23.
"""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.execution import fit_model, predict_model
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily


class MockFullModel:
    def __init__(
        self,
        y_pred: np.ndarray | None = None,
        y_std: np.ndarray | None = None,
        y_proba: np.ndarray | None = None,
    ) -> None:
        self.y_pred_val = y_pred
        self.y_std_val = y_std
        self.y_proba_val = y_proba
        self.fitted_ = True

    def fit(self, X: np.ndarray, y: np.ndarray) -> MockFullModel:
        self.fitted_ = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.y_pred_val is not None:
            return self.y_pred_val
        return np.ones(X.shape[0]) * 42.0

    def predict_std(self, X: np.ndarray) -> np.ndarray:
        if self.y_std_val is not None:
            return self.y_std_val
        return np.ones(X.shape[0]) * 1.5

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.y_proba_val is not None:
            return self.y_proba_val
        n = X.shape[0]
        return np.tile([0.7, 0.3], (n, 1))

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        return np.ones(X.shape[0]) * 2.5


def _make_spec(
    supports_uncertainty: bool = False,
    supports_predict_proba: bool = False,
    supports_decision_function: bool = False,
    requires_fit: bool = True,
) -> ModelSpec:
    return ModelSpec(
        model_id="pred_model",
        display_name="Prediction Model",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory=MockFullModel,
        capabilities=ModelCapabilities(
            requires_fit=requires_fit,
            supports_predict=True,
            supports_uncertainty=supports_uncertainty,
            supports_predict_proba=supports_predict_proba,
            supports_decision_function=supports_decision_function,
        ),
        description="Model for testing prediction contracts",
        scientific_justification="Prediction output testing",
    )


def test_m41_05_01_predict_model_output_structure() -> None:
    """AC-M41-05-01 / C16: predict_model returns dict with y_pred, y_std, y_proba; y_pred length matches N."""
    spec = _make_spec()
    model = MockFullModel()
    X_eval = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

    out = predict_model(model, spec, X_eval)

    assert isinstance(out, dict)
    assert set(out.keys()) == {"y_pred", "y_std", "y_proba"}
    assert isinstance(out["y_pred"], np.ndarray)
    assert out["y_pred"].ndim == 1
    assert out["y_pred"].shape[0] == 3
    assert np.allclose(out["y_pred"], [42.0, 42.0, 42.0])


def test_m41_05_02_predict_model_uncertainty_valid() -> None:
    """AC-M41-05-02 / C17: predict_model produces 1D finite non-negative y_std when supports_uncertainty=True."""
    spec = _make_spec(supports_uncertainty=True)
    model = MockFullModel(y_std=np.array([0.1, 0.5, 0.0]))
    X_eval = np.array([[1.0], [2.0], [3.0]])

    out = predict_model(model, spec, X_eval)

    assert isinstance(out["y_std"], np.ndarray)
    assert out["y_std"].ndim == 1
    assert out["y_std"].shape[0] == 3
    assert np.all(np.isfinite(out["y_std"]))
    assert np.all(out["y_std"] >= 0.0)


def test_m41_05_03_predict_model_predict_proba_valid() -> None:
    """AC-M41-05-03 / C18: predict_model produces 2D y_proba bounded in [0, 1] summing to 1.0."""
    spec = _make_spec(supports_predict_proba=True)
    proba = np.array([[0.8, 0.2], [0.4, 0.6], [0.5, 0.5]])
    model = MockFullModel(y_proba=proba)
    X_eval = np.array([[1.0], [2.0], [3.0]])

    out = predict_model(model, spec, X_eval)

    assert isinstance(out["y_proba"], np.ndarray)
    assert out["y_proba"].ndim == 2
    assert out["y_proba"].shape == (3, 2)
    assert np.all(out["y_proba"] >= 0.0)
    assert np.all(out["y_proba"] <= 1.0)
    assert np.allclose(np.sum(out["y_proba"], axis=1), 1.0)


def test_m41_05_04_predict_model_uncertainty_disabled_none() -> None:
    """AC-M41-05-04 / C19: predict_model sets y_std to None when supports_uncertainty=False."""
    spec = _make_spec(supports_uncertainty=False)
    model = MockFullModel(y_std=np.array([1.0, 2.0]))
    X_eval = np.array([[1.0], [2.0]])

    out = predict_model(model, spec, X_eval)
    assert out["y_std"] is None


def test_m41_05_05_predict_model_predict_proba_disabled_none() -> None:
    """AC-M41-05-05 / C20: predict_model sets y_proba to None when supports_predict_proba=False (even with decision_function)."""
    spec = _make_spec(supports_predict_proba=False, supports_decision_function=True)
    model = MockFullModel()
    X_eval = np.array([[1.0], [2.0]])

    out = predict_model(model, spec, X_eval)
    assert out["y_proba"] is None


def test_m41_05_06_predict_model_unfitted_rejection() -> None:
    """AC-M41-05-06 / C21: predict_model raises ContractViolationError when model is unfitted."""
    spec = _make_spec(requires_fit=True)

    class UnfittedModel:
        def predict(self, X: np.ndarray) -> np.ndarray:
            return np.ones(X.shape[0])

    unfitted = UnfittedModel()
    X_eval = np.array([[1.0], [2.0]])

    with pytest.raises(ContractViolationError, match="has not been fitted"):
        predict_model(unfitted, spec, X_eval)


def test_m41_05_07_predict_model_uncertainty_runtime_violation() -> None:
    """AC-M41-05-07 / C22: predict_model raises ContractViolationError on invalid/negative y_std."""
    spec = _make_spec(supports_uncertainty=True)
    X_eval = np.array([[1.0], [2.0]])

    # Negative uncertainty
    model_neg = MockFullModel(y_std=np.array([1.0, -0.5]))
    with pytest.raises(ContractViolationError, match="negative uncertainty"):
        predict_model(model_neg, spec, X_eval)

    # Non-finite uncertainty
    model_nan = MockFullModel(y_std=np.array([1.0, float("nan")]))
    with pytest.raises(ContractViolationError, match="non-finite values"):
        predict_model(model_nan, spec, X_eval)

    # Mismatched length
    model_short = MockFullModel(y_std=np.array([1.0]))
    with pytest.raises(ContractViolationError, match="y_std shape"):
        predict_model(model_short, spec, X_eval)


def test_m41_05_08_predict_model_predict_proba_runtime_violation() -> None:
    """AC-M41-05-08 / C23: predict_model raises ContractViolationError on invalid probabilities."""
    spec = _make_spec(supports_predict_proba=True)
    X_eval = np.array([[1.0], [2.0]])

    # Values not bounded in [0, 1]
    model_oob = MockFullModel(y_proba=np.array([[1.2, -0.2], [0.5, 0.5]]))
    with pytest.raises(ContractViolationError, match="strictly bounded in \\[0.0, 1.0\\]"):
        predict_model(model_oob, spec, X_eval)

    # Row sums not 1.0
    model_unnorm = MockFullModel(y_proba=np.array([[0.3, 0.3], [0.5, 0.5]]))
    with pytest.raises(ContractViolationError, match="row sums must equal 1.0"):
        predict_model(model_unnorm, spec, X_eval)

    # 1D proba array (must be 2D)
    model_1d = MockFullModel(y_proba=np.array([0.5, 0.5]))
    with pytest.raises(ContractViolationError, match="must be 2D"):
        predict_model(model_1d, spec, X_eval)
