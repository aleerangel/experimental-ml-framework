"""Unit tests for FeatureScenario model, mode constraints and catalog validation (SCN-01 to SCN-06)."""

from dataclasses import FrozenInstanceError
import json
from types import MappingProxyType
import pytest

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.features.scenarios import (
    FeatureScenario,
    ScenarioMode,
    ScenariosCatalog,
    validate_scenarios,
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
        name="Top K Relevance Selection",
        description="Selects top K features by statistical relevance within fold",
        scientific_justification="Removes noise while avoiding pre-partition leakage",
        mode="DYNAMIC",
        strategy_name="TOP_K_RELEVANCE",
        strategy_params={"k": 5},
    )
    assert dyn.mode == ScenarioMode.DYNAMIC
    assert dyn.strategy_name == "TOP_K_RELEVANCE"
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


def _make_dummy_sanitized_view(
    candidate_features: tuple[str, ...],
    target_col: str = "target",
    group_col: str | None = None,
    ignore_cols: tuple[str, ...] = (),
    dataset_hash: str = "hash_dummy_view_123",
):
    """Simple test view mock providing attributes expected by validate_scenarios."""
    class DummySchema:
        def __init__(self):
            self.target_col = target_col
            self.group_col = group_col
            self.observation_id_col = "obs_id"
            self.time_col = None
            self.ignore_cols = ignore_cols

    class DummyView:
        def __init__(self):
            self.candidate_feature_cols = candidate_features
            self.schema = DummySchema()
            self.dataset_hash = dataset_hash

    return DummyView()


def test_scn_04_validate_scenarios_success() -> None:
    """Proof C4: Verify validate_scenarios succeeds with valid fixed and dynamic scenarios (SCN-04)."""
    view = _make_dummy_sanitized_view(
        candidate_features=("feat_1", "feat_2", "feat_3"),
        target_col="target",
        group_col="plot_id",
        ignore_cols=("admin_id",),
        dataset_hash="hash_view_valid_999",
    )

    s1 = FeatureScenario(
        scenario_id="s1_fixed",
        name="Fixed Subset",
        description="Features 1 and 2",
        scientific_justification="Domain subset",
        mode="FIXED",
        selected_features=("feat_1", "feat_2"),
    )
    s2 = FeatureScenario(
        scenario_id="s2_dyn",
        name="Dynamic K",
        description="Top 2 features",
        scientific_justification="Relevance filtering",
        mode="DYNAMIC",
        strategy_name="TOP_K",
        strategy_params={"k": 2},
    )

    catalog = validate_scenarios([s1, s2], view)

    assert catalog.dataset_hash == "hash_view_valid_999"
    assert len(catalog.scenarios) == 2
    assert catalog.scenarios[0].scenario_id == "s1_fixed"
    assert catalog.scenarios[1].scenario_id == "s2_dyn"


def test_scn_05_validate_scenarios_rejections() -> None:
    """Proof C5: Verify validate_scenarios rejects empty list, duplicates, protected and missing cols (SCN-05)."""
    view = _make_dummy_sanitized_view(
        candidate_features=("feat_1", "feat_2"),
        target_col="target",
        group_col="group_plot",
        ignore_cols=("id_code",),
    )

    # 1. Empty scenarios list
    with pytest.raises(ConfigurationError, match="At least one"):
        validate_scenarios([], view)

    # 2. Duplicate scenario_id
    s1 = FeatureScenario("scen_a", "Name 1", "Desc", "Just", "FIXED", ("feat_1",))
    s2 = FeatureScenario("scen_a", "Name 2", "Desc", "Just", "DYNAMIC", strategy_name="PCA")
    with pytest.raises(ConfigurationError, match="Duplicate scenario_id"):
        validate_scenarios([s1, s2], view)

    # 3. Fixed scenario with unknown feature
    s_unknown = FeatureScenario("scen_unk", "Name", "Desc", "Just", "FIXED", ("feat_1", "non_existent"))
    with pytest.raises(ContractViolationError, match="not in candidate_feature_cols"):
        validate_scenarios([s_unknown], view)

    # 4. Fixed scenario including target column
    s_target = FeatureScenario("scen_tgt", "Name", "Desc", "Just", "FIXED", ("feat_1", "target"))
    with pytest.raises(ContractViolationError, match="includes protected column 'target'"):
        validate_scenarios([s_target], view)

    # 5. Fixed scenario including group column
    s_group = FeatureScenario("scen_grp", "Name", "Desc", "Just", "FIXED", ("feat_1", "group_plot"))
    with pytest.raises(ContractViolationError, match="includes protected column 'group_plot'"):
        validate_scenarios([s_group], view)

    # 6. Fixed scenario including ignore column
    s_ign = FeatureScenario("scen_ign", "Name", "Desc", "Just", "FIXED", ("feat_1", "id_code"))
    with pytest.raises(ContractViolationError, match="includes protected column 'id_code'"):
        validate_scenarios([s_ign], view)


def test_scn_06_roundtrip_serialization() -> None:
    """Proof C6: Verify ScenariosCatalog lossless roundtrip serialization and reconstruction (SCN-06)."""
    s1 = FeatureScenario(
        scenario_id="s1_fixed",
        name="Fixed Subset",
        description="Features 1 and 2",
        scientific_justification="Domain subset",
        mode="FIXED",
        selected_features=("feat_1", "feat_2"),
        preprocessing_config={"standardize": True},
    )
    s2 = FeatureScenario(
        scenario_id="s2_dyn",
        name="Dynamic K",
        description="Top 2 features",
        scientific_justification="Relevance filtering",
        mode="DYNAMIC",
        strategy_name="TOP_K",
        strategy_params={"k": 2},
    )
    catalog = ScenariosCatalog(
        scenarios=(s1, s2),
        dataset_hash="hash_view_serialization_456",
        metadata={"created_at": "2026-11-10"},
    )

    # 1. Serialization
    data = catalog.to_dict()
    json_str = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)
    assert "hash_view_serialization_456" in json_str

    # 2. Deserialization
    reconstructed = ScenariosCatalog.from_dict(json.loads(json_str))

    assert reconstructed.dataset_hash == catalog.dataset_hash
    assert len(reconstructed.scenarios) == 2
    r_s1 = reconstructed.scenarios[0]
    assert r_s1.scenario_id == s1.scenario_id
    assert r_s1.mode == ScenarioMode.FIXED
    assert r_s1.selected_features == s1.selected_features
    assert r_s1.preprocessing_config["standardize"] is True

    r_s2 = reconstructed.scenarios[1]
    assert r_s2.scenario_id == s2.scenario_id
    assert r_s2.mode == ScenarioMode.DYNAMIC
    assert r_s2.strategy_name == "TOP_K"
    assert r_s2.strategy_params["k"] == 2

