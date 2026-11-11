"""Unit tests for models stage gate verification (MPC-04)."""

from pathlib import Path
import pytest

from experimental_ml.core.findings import ContractViolationError, DataIntegrityError
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.models.baselines import DummyBaselineModel
from experimental_ml.models.catalog import ModelsCatalog
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.storage import save_models_catalog
from experimental_ml.models.types import ModelCapabilities, ModelFamily
from experimental_ml.stages.stage_gates import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    MODELS_CATALOG_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    verify_models_gate,
)


def _setup_stage1_ready(exp_dir: Path, status: str = "READY") -> None:
    data_hash = "source_hash_123"
    desc = {
        "dataset_hash": data_hash,
        "n_observations": 10,
        "n_columns": 2,
        "column_names": ["x", "y"],
        "column_types": {"x": "float64", "y": "float64"},
    }
    write_json_atomic(exp_dir / DATASET_DESCRIPTOR_REL_PATH, desc)

    prof = {
        "source_dataset_hash": data_hash,
        "n_rows": 10,
        "n_cols": 2,
        "memory_bytes": 160,
        "columns": {},
        "findings": [],
    }
    write_json_atomic(exp_dir / DATASET_PROFILE_REL_PATH, prof)

    plan = {
        "status": status,
        "source_dataset_hash": data_hash,
        "rules": [],
    }
    write_json_atomic(exp_dir / PREPARATION_PLAN_REL_PATH, plan)


def _create_sample_catalog() -> ModelsCatalog:
    spec = ModelSpec(
        model_id="baseline_mean",
        display_name="Baseline Mean",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
        capabilities=ModelCapabilities(requires_fit=True),
        description="Predicts y_train mean",
        scientific_justification="Baseline comparator",
    )
    return ModelsCatalog(models=[spec])


def test_m44_04_01_verify_models_gate_valid(tmp_path: Path) -> None:
    """C10: verify_models_gate verifies models gate when artifacts are valid."""
    exp_dir = tmp_path / "exp"
    _setup_stage1_ready(exp_dir, status="READY")

    catalog = _create_sample_catalog()
    save_models_catalog(catalog, exp_dir / MODELS_CATALOG_REL_PATH)

    verified = verify_models_gate(exp_dir)
    assert isinstance(verified, ModelsCatalog)
    assert len(verified.models) == 1
    assert verified.models[0].model_id == "baseline_mean"


def test_m44_04_02_verify_models_gate_missing_or_empty(tmp_path: Path) -> None:
    """C11: verify_models_gate raises error when models.json is missing or catalog is empty."""
    exp_dir = tmp_path / "exp"
    _setup_stage1_ready(exp_dir, status="READY")

    # 1. Missing models.json
    with pytest.raises(DataIntegrityError, match="Models catalog missing"):
        verify_models_gate(exp_dir)

    # 2. Empty models list
    write_json_atomic(
        exp_dir / MODELS_CATALOG_REL_PATH,
        {"models": [], "metadata": {}},
    )
    with pytest.raises(ContractViolationError, match="cannot be empty"):
        verify_models_gate(exp_dir)


def test_m44_04_03_verify_models_gate_unmet_precondition(tmp_path: Path) -> None:
    """C12: verify_models_gate raises ContractViolationError when preparation gate is not READY."""
    exp_dir = tmp_path / "exp"
    # Stage 1 has status BLOCKED
    _setup_stage1_ready(exp_dir, status="BLOCKED")

    catalog = _create_sample_catalog()
    save_models_catalog(catalog, exp_dir / MODELS_CATALOG_REL_PATH)

    with pytest.raises(ContractViolationError, match="not READY"):
        verify_models_gate(exp_dir)
