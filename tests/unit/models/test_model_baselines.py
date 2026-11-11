"""Unit tests for canonical baseline models and analytical reference models.

Covers MOD-08 (AC-M41-08-01 to AC-M41-08-05) and checks C30, C31, C32, C33, C34.
"""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.baselines import (
    AnalyticalBiometricModel,
    DummyBaselineModel,
)
from experimental_ml.models.execution import fit_model, predict_model
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily


def test_m41_08_01_dummy_baseline_regression_mean() -> None:
    """AC-M41-08-01 / C30: DummyBaselineModel with strategy 'mean' outputs target mean as y_pred and std as y_std."""
    spec = ModelSpec(
        model_id="baseline_mean",
        display_name="Baseline Mean",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
        capabilities=ModelCapabilities(
            requires_fit=True,
            supports_predict=True,
            supports_uncertainty=True,
        ),
        description="Mean baseline",
        scientific_justification="Regression baseline",
    )
    model = DummyBaselineModel(strategy="mean")
    X_train = np.array([[1.0], [2.0], [3.0], [4.0]])
    y_train = np.array([2.0, 4.0, 6.0, 8.0])

    fitted_model, _ = fit_model(model, spec, X_train, y_train)

    X_eval = np.array([[10.0], [20.0]])
    out = predict_model(fitted_model, spec, X_eval)

    expected_mean = np.mean(y_train)  # 5.0
    expected_std = np.std(y_train, ddof=1)  # ~2.581988897

    assert np.allclose(out["y_pred"], [expected_mean, expected_mean])
    assert np.allclose(out["y_std"], [expected_std, expected_std])
    assert out["y_proba"] is None


def test_m41_08_02_dummy_baseline_regression_median() -> None:
    """AC-M41-08-02 / C31: DummyBaselineModel with strategy 'median' outputs target median as y_pred and MAD as y_std."""
    spec = ModelSpec(
        model_id="baseline_median",
        display_name="Baseline Median",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed: DummyBaselineModel(strategy="median"),
        capabilities=ModelCapabilities(
            requires_fit=True,
            supports_predict=True,
            supports_uncertainty=True,
        ),
        description="Median baseline",
        scientific_justification="Robust regression baseline",
    )
    model = DummyBaselineModel(strategy="median")
    X_train = np.array([[1.0], [2.0], [3.0], [4.0], [5.0]])
    y_train = np.array([1.0, 2.0, 3.0, 4.0, 100.0])  # outlier present

    fitted_model, _ = fit_model(model, spec, X_train, y_train)

    X_eval = np.array([[10.0]])
    out = predict_model(fitted_model, spec, X_eval)

    expected_median = np.median(y_train)  # 3.0
    expected_mad = np.median(np.abs(y_train - expected_median))  # median of [2, 1, 0, 1, 97] -> 1.0

    assert np.allclose(out["y_pred"], [expected_median])
    assert np.allclose(out["y_std"], [expected_mad])


def test_m41_08_03_dummy_baseline_classification_most_frequent() -> None:
    """AC-M41-08-03 / C32: DummyBaselineModel with strategy 'most_frequent' resolves ties lexicographically and produces probabilities."""
    spec = ModelSpec(
        model_id="baseline_frequent",
        display_name="Baseline Frequent",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed: DummyBaselineModel(strategy="most_frequent"),
        capabilities=ModelCapabilities(
            requires_fit=True,
            supports_predict=True,
            supports_predict_proba=True,
        ),
        description="Frequent baseline",
        scientific_justification="Classification baseline",
    )
    # Tie between "class_b" and "class_a" (each appears 2 times)
    model = DummyBaselineModel(strategy="most_frequent")
    X_train = np.array([[1.0], [2.0], [3.0], [4.0]])
    y_train = np.array(["class_b", "class_a", "class_b", "class_a"])

    fitted_model, _ = fit_model(model, spec, X_train, y_train)

    X_eval = np.array([[10.0], [20.0]])
    out = predict_model(fitted_model, spec, X_eval)

    # Lexicographical order: "class_a" comes before "class_b"
    assert np.array_equal(out["y_pred"], ["class_a", "class_a"])
    assert out["y_proba"] is not None
    assert out["y_proba"].shape == (2, 2)
    # Both classes have 50% frequency
    assert np.allclose(out["y_proba"], [[0.5, 0.5], [0.5, 0.5]])


def test_m41_08_04_analytical_biometric_model_direct_eval() -> None:
    """AC-M41-08-04 / C33: AnalyticalBiometricModel evaluates formula directly without fitting."""
    spec = ModelSpec(
        model_id="clutter_analytical",
        display_name="Analytical Clutter Model",
        family=ModelFamily.BIOMETRIC_MODEL,
        estimator_factory=lambda seed: AnalyticalBiometricModel(
            formula_name="clutter_index",
            coefficients={"intercept": 10.0, "w0": 2.0, "w1": 3.0},
            required_features=(0, 1),
        ),
        capabilities=ModelCapabilities(
            requires_fit=False,
            supports_predict=True,
        ),
        description="Analytical equation",
        scientific_justification="Domain equation",
    )
    model = AnalyticalBiometricModel(
        formula_name="clutter_index",
        coefficients={"intercept": 10.0, "w0": 2.0, "w1": 3.0},
        required_features=(0, 1),
    )
    # fit_model bypasses training
    fitted_model, diag = fit_model(
        model, spec, np.array([[1.0, 2.0]]), np.array([100.0])
    )
    assert fitted_model is model
    assert diag.diagnostics["requires_fit"] is False

    # Evaluation: 10.0 + 2.0 * col0 + 3.0 * col1
    # Sample 1: 10 + 2*1 + 3*2 = 18
    # Sample 2: 10 + 2*4 + 3*5 = 33
    X_eval = np.array([[1.0, 2.0], [4.0, 5.0]])
    out = predict_model(fitted_model, spec, X_eval)

    assert np.allclose(out["y_pred"], [18.0, 33.0])


def test_m41_08_05_analytical_biometric_model_missing_feature_rejection() -> None:
    """AC-M41-08-05 / C34: AnalyticalBiometricModel raises ContractViolationError when required features missing."""
    spec = ModelSpec(
        model_id="clutter_analytical",
        display_name="Analytical Clutter Model",
        family=ModelFamily.BIOMETRIC_MODEL,
        estimator_factory=lambda seed: AnalyticalBiometricModel(required_features=(0, 3)),
        capabilities=ModelCapabilities(requires_fit=False, supports_predict=True),
        description="Analytical equation",
        scientific_justification="Domain equation",
    )
    model = AnalyticalBiometricModel(required_features=(0, 3))
    # X_eval has only 2 features (indices 0 and 1), missing index 3
    X_eval = np.array([[1.0, 2.0], [3.0, 4.0]])

    with pytest.raises(ContractViolationError, match="requires feature index 3"):
        predict_model(model, spec, X_eval)
