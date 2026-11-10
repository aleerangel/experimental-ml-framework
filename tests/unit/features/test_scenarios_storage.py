"""Unit tests for feature scenarios persistence and stage gate (SCN-07, SCN-08)."""

from pathlib import Path
import tempfile
import pytest

from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
)
from experimental_ml.features.scenarios import (
    FeatureScenario,
    ScenariosCatalog,
    load_scenarios,
    save_scenarios,
)
from experimental_ml.stages.stage_gates import verify_scenarios_gate


def _make_dummy_view(dataset_hash: str = "hash_stage_gate_test_123"):
    """Mock sanitized view for stage gate unit tests."""
    class DummySchema:
        def __init__(self):
            self.target_col = "target"
            self.group_col = None
            self.observation_id_col = "obs_id"
            self.time_col = None
            self.ignore_cols = ()

    class DummyView:
        def __init__(self, d_hash: str):
            self.candidate_feature_cols = ("f1", "f2")
            self.schema = DummySchema()
            self.dataset_hash = d_hash

    return DummyView(dataset_hash)


def test_scn_07_save_and_load_scenarios() -> None:
    """Proof C7: Verify save_scenarios write_json_atomic roundtrip and overwrite protection (SCN-07)."""
    s1 = FeatureScenario("s1", "Name", "Desc", "Just", "FIXED", ("f1",))
    catalog = ScenariosCatalog(
        scenarios=(s1,),
        dataset_hash="hash_save_load_999",
        metadata={"author": "researcher"},
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        dest_path = Path(tmpdir) / "configuration" / "scenarios.json"

        # 1. Initial atomic save
        save_scenarios(catalog, dest_path, overwrite=False)
        assert dest_path.exists()

        # 2. Overwrite protection: overwrite=False raises ConfigurationError
        with pytest.raises(ConfigurationError, match="Target artifact already exists"):
            save_scenarios(catalog, dest_path, overwrite=False)

        # 3. Successful overwrite when overwrite=True
        save_scenarios(catalog, dest_path, overwrite=True)

        # 4. Load and verify semantic equivalence
        loaded = load_scenarios(dest_path)
        assert loaded.dataset_hash == "hash_save_load_999"
        assert len(loaded.scenarios) == 1
        assert loaded.scenarios[0].scenario_id == "s1"
        assert loaded.metadata["author"] == "researcher"


def test_verify_scenarios_gate_valid_and_failures() -> None:
    """Verify verify_scenarios_gate missing file, hash mismatch, and success (SCN-08)."""
    view = _make_dummy_view(dataset_hash="hash_expected_123")
    s1 = FeatureScenario("s1", "Name", "Desc", "Just", "FIXED", ("f1",))
    catalog = ScenariosCatalog(scenarios=(s1,), dataset_hash="hash_expected_123")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "scenarios.json"

        # 1. Missing file raises ContractViolationError
        with pytest.raises(ContractViolationError, match="file not found"):
            verify_scenarios_gate(file_path, view)

        # 2. Hash mismatch raises DataIntegrityError
        mismatched_catalog = ScenariosCatalog(scenarios=(s1,), dataset_hash="different_hash_456")
        save_scenarios(mismatched_catalog, file_path)

        with pytest.raises(DataIntegrityError, match="dataset_hash mismatch"):
            verify_scenarios_gate(file_path, view)

        # 3. Success when hash matches and scenarios are valid against view
        save_scenarios(catalog, file_path, overwrite=True)
        verified = verify_scenarios_gate(file_path, view)
        assert verified.dataset_hash == "hash_expected_123"
        assert len(verified.scenarios) == 1
