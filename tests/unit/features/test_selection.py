"""Unit tests for intra-fold feature selection engine (SEL-01 to SEL-04, SEL-07)."""

from dataclasses import FrozenInstanceError
from types import MappingProxyType
import numpy as np
import pytest

from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
)
from experimental_ml.features.scenarios import FeatureScenario
from experimental_ml.features.selection import (
    SelectionResult,
    apply_feature_selection,
    select_features_in_fold,
)


def test_sel_01_selection_result_immutability() -> None:
    """Proof C1: Verify SelectionResult frozen immutability and dictionary proxies (SEL-01)."""
    res = SelectionResult(
        selected_features=("feat_a", "feat_b"),
        scores={"feat_a": 0.8, "feat_b": 0.5},
        fitted_params={"threshold": 0.1},
        strategy_name="VARIANCE_THRESHOLD",
    )

    assert res.selected_features == ("feat_a", "feat_b")
    assert isinstance(res.scores, MappingProxyType)
    assert res.scores["feat_a"] == 0.8
    assert isinstance(res.fitted_params, MappingProxyType)
    assert res.strategy_name == "VARIANCE_THRESHOLD"

    with pytest.raises(FrozenInstanceError):
        res.strategy_name = "MUTATED"  # type: ignore

    # Roundtrip serialization
    data = res.to_dict()
    reconstructed = SelectionResult.from_dict(data)
    assert reconstructed.selected_features == res.selected_features
    assert reconstructed.scores == res.scores
    assert reconstructed.strategy_name == res.strategy_name


def test_sel_02_fixed_scenario_bypass() -> None:
    """Proof C2: Verify fixed scenario bypasses calculation and returns static features (SEL-02)."""
    scenario = FeatureScenario(
        scenario_id="fixed_biometric",
        name="Biometric Fixed",
        description="Fixed inputs",
        scientific_justification="Literature baseline",
        mode="FIXED",
        selected_features=("dap", "ht"),
    )

    X_train = {
        "dap": np.array([10.0, 20.0, 30.0]),
        "ht": np.array([12.0, 22.0, 32.0]),
        "noise": np.array([1.0, 2.0, 3.0]),
    }

    # Does not require y_train (passed as None)
    res = select_features_in_fold(X_train, y_train=None, scenario=scenario)

    assert res.selected_features == ("dap", "ht")
    assert res.strategy_name == "FIXED"
    assert len(res.scores) == 0


def test_sel_03_variance_threshold_selection() -> None:
    """Proof C3: Verify dynamic variance threshold selects features strictly on training data (SEL-03)."""
    scenario = FeatureScenario(
        scenario_id="dyn_var",
        name="Variance Filter",
        description="Filter low variance",
        scientific_justification="Removes quasi-constant features",
        mode="DYNAMIC",
        strategy_name="VARIANCE_THRESHOLD",
        strategy_params={"threshold": 0.5},
    )

    X_train = {
        "feat_high_var": np.array([1.0, 5.0, 10.0, 20.0]),  # var ~ 70
        "feat_med_var": np.array([1.0, 2.0, 3.0, 4.0]),    # var ~ 1.66
        "feat_low_var": np.array([1.0, 1.1, 1.0, 1.1]),    # var ~ 0.003
        "feat_const": np.array([5.0, 5.0, 5.0, 5.0]),      # var = 0.0
    }

    res = select_features_in_fold(X_train, y_train=None, scenario=scenario)

    # Only feat_high_var and feat_med_var exceed threshold 0.5
    assert res.selected_features == ("feat_high_var", "feat_med_var")
    assert res.scores["feat_high_var"] > res.scores["feat_med_var"]
    assert res.strategy_name == "VARIANCE_THRESHOLD"


def test_sel_04_top_k_relevance_selection() -> None:
    """Proof C4: Verify dynamic top-k relevance ranks features by association with y_train (SEL-04)."""
    scenario = FeatureScenario(
        scenario_id="dyn_top_2",
        name="Top 2 Features",
        description="Selects top 2 by association",
        scientific_justification="Highest univariate correlation",
        mode="DYNAMIC",
        strategy_name="TOP_K_RELEVANCE",
        strategy_params={"k": 2},
    )

    np.random.seed(123)
    n = 50
    y_train = np.linspace(10.0, 50.0, n)
    # feat_a has correlation ~ 1.0 with y
    feat_a = y_train + np.random.normal(0, 0.1, n)
    # feat_b has moderate correlation ~ 0.8 with y
    feat_b = 0.5 * y_train + np.random.normal(0, 5.0, n)
    # feat_c is pure noise
    feat_c = np.random.normal(0, 1.0, n)

    X_train = {
        "feat_a": feat_a,
        "feat_b": feat_b,
        "feat_c": feat_c,
    }

    res = select_features_in_fold(X_train, y_train=y_train, scenario=scenario)

    assert len(res.selected_features) == 2
    assert res.selected_features[0] == "feat_a"
    assert res.selected_features[1] == "feat_b"
    assert "feat_c" not in res.selected_features
    assert res.strategy_name == "TOP_K_RELEVANCE"


def test_sel_07_empty_selection_rejection() -> None:
    """Proof C7: Verify dynamic selection resulting in 0 features raises DataIntegrityError (SEL-07)."""
    scenario = FeatureScenario(
        scenario_id="dyn_high_threshold",
        name="Unreachable Threshold",
        description="Too strict",
        scientific_justification="Test",
        mode="DYNAMIC",
        strategy_name="VARIANCE_THRESHOLD",
        strategy_params={"threshold": 1000.0},
    )

    X_train = {
        "feat_1": np.array([1.0, 2.0, 3.0]),
        "feat_2": np.array([4.0, 5.0, 6.0]),
    }

    with pytest.raises(DataIntegrityError, match="resulted in 0 selected features"):
        select_features_in_fold(X_train, y_train=None, scenario=scenario)


def test_sel_05_apply_feature_selection() -> None:
    """Proof C5: Verify apply_feature_selection filters evaluation data preserving order (SEL-05)."""
    selection_res = SelectionResult(
        selected_features=("feat_b", "feat_a"),
        scores={"feat_b": 0.9, "feat_a": 0.7},
        fitted_params={},
        strategy_name="TOP_K_RELEVANCE",
    )

    X_eval = {
        "feat_a": np.array([1.0, 2.0]),
        "feat_b": np.array([3.0, 4.0]),
        "feat_c": np.array([5.0, 6.0]),
    }

    filtered = apply_feature_selection(X_eval, selection_res)

    # 1. Retains strictly selected features in exact order
    assert list(filtered.keys()) == ["feat_b", "feat_a"]
    assert np.array_equal(filtered["feat_b"], np.array([3.0, 4.0]))
    assert np.array_equal(filtered["feat_a"], np.array([1.0, 2.0]))
    assert "feat_c" not in filtered

    # 2. Missing feature in evaluation data raises ContractViolationError
    X_eval_missing = {
        "feat_a": np.array([1.0, 2.0]),
    }
    with pytest.raises(ContractViolationError, match="Selected feature 'feat_b' is missing"):
        apply_feature_selection(X_eval_missing, selection_res)

