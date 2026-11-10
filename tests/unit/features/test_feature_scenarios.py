"""Unit tests for FeatureScenario model, mode constraints and catalog validation (SCN-01 to SCN-06)."""

from dataclasses import FrozenInstanceError
import json
from types import MappingProxyType
import pytest

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.features.scenarios import (
    FeatureScenario,
    ScenarioMode,
)


def test_scn_01_feature_scenario_immutability() -> None:
    """Proof C1: Verify FeatureScenario frozen immutability and slug validation (SCN-01)."""
    scenario = FeatureScenario(
        scenario_id="biometric_subset_v1",
        name="Biometric Baseline",
        description="Features containing diameter, height, and site index",
        scientific_justification="Established forestry literature baseline",
        mode=ScenarioMode.FIXED,
        selected_features=("diameter", "height", "site_index"),
        preprocessing_config={"scale": True},
    )

    assert scenario.scenario_id == "biometric_subset_v1"
    assert scenario.name == "Biometric Baseline"
    assert scenario.mode == ScenarioMode.FIXED
    assert isinstance(scenario.selected_features, tuple)
    assert isinstance(scenario.preprocessing_config, MappingProxyType)
    assert scenario.preprocessing_config["scale"] is True

    # Immutability verification
    with pytest.raises(FrozenInstanceError):
        scenario.name = "Mutated"  # type: ignore

    # Invalid slug with spaces or illegal characters
    with pytest.raises(ConfigurationError, match="scenario_id"):
        FeatureScenario(
            scenario_id="invalid slug with spaces",
            name="Valid Name",
            description="Valid",
            scientific_justification="Valid",
            mode="FIXED",
            selected_features=("f1",),
        )

    # Empty string validation
    with pytest.raises(ConfigurationError, match="name"):
        FeatureScenario(
            scenario_id="valid_slug",
            name="   ",
            description="Valid",
            scientific_justification="Valid",
            mode="FIXED",
            selected_features=("f1",),
        )


def test_scn_02_fixed_scenario_constraints() -> None:
    """Proof C2: Verify fixed scenario requires non-empty unique features and forbids dynamic fields (SCN-02)."""
    # 1. Missing selected_features
    with pytest.raises(ConfigurationError, match="non-empty sequence of 'selected_features'"):
        FeatureScenario(
            scenario_id="fixed_empty",
            name="Empty Fixed",
            description="Desc",
            scientific_justification="Just",
            mode="FIXED",
            selected_features=(),
        )

    # 2. Duplicate features in selected_features
    with pytest.raises(ConfigurationError, match="duplicate features"):
        FeatureScenario(
            scenario_id="fixed_dupes",
            name="Dupe Fixed",
            description="Desc",
            scientific_justification="Just",
            mode="FIXED",
            selected_features=("feat_a", "feat_b", "feat_a"),
        )

    # 3. Fixed scenario specifying strategy_name
    with pytest.raises(ConfigurationError, match="cannot specify 'strategy_name'"):
        FeatureScenario(
            scenario_id="fixed_with_strat",
            name="Invalid Fixed",
            description="Desc",
            scientific_justification="Just",
            mode="FIXED",
            selected_features=("feat_a", "feat_b"),
            strategy_name="VARIANCE_THRESHOLD",
        )

    # 4. Fixed scenario specifying strategy_params
    with pytest.raises(ConfigurationError, match="cannot specify non-empty 'strategy_params'"):
        FeatureScenario(
            scenario_id="fixed_with_params",
            name="Invalid Fixed",
            description="Desc",
            scientific_justification="Just",
            mode="FIXED",
            selected_features=("feat_a",),
            strategy_params={"threshold": 0.05},
        )


def test_scn_03_dynamic_scenario_anti_leakage() -> None:
    """Proof C3: Verify dynamic scenario enforces strategy_name and strictly forbids selected_features (SCN-03)."""
    # 1. Valid dynamic scenario
    dyn = FeatureScenario(
        scenario_id="top_k_relevance",
        name="Top K Mutual Information",
        description="Selects top K features by mutual information within fold",
        scientific_justification="Removes noise while avoiding pre-partition leakage",
        mode="DYNAMIC",
        strategy_name="MUTUAL_INFO_TOP_K",
        strategy_params={"k": 5},
    )
    assert dyn.mode == ScenarioMode.DYNAMIC
    assert dyn.strategy_name == "MUTUAL_INFO_TOP_K"
    assert dyn.selected_features == ()
    assert dyn.strategy_params["k"] == 5

    # 2. Missing strategy_name
    with pytest.raises(ConfigurationError, match="requires a non-empty 'strategy_name'"):
        FeatureScenario(
            scenario_id="dyn_no_strat",
            name="Dyn No Strat",
            description="Desc",
            scientific_justification="Just",
            mode="DYNAMIC",
            strategy_name=None,
        )

    # 3. Dynamic scenario with pre-calculated selected_features (anti-leakage guard)
    with pytest.raises(ContractViolationError, match="cannot specify 'selected_features'"):
        FeatureScenario(
            scenario_id="dyn_leaked",
            name="Leaked Dynamic",
            description="Desc",
            scientific_justification="Just",
            mode="DYNAMIC",
            strategy_name="VARIANCE_THRESHOLD",
            selected_features=("feat_a", "feat_b"),
        )
