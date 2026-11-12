"""Unit tests for 'expml models verify' subcommand (MPC-06)."""

import argparse
import json
from pathlib import Path
import pytest

from experimental_ml.cli.cmd_models import handle_models_verify
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
)


def _setup_stage1_ready(exp_dir: Path) -> None:
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
        "status": "READY",
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


def test_m44_06_01_models_verify_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """C16: handle_models_verify verifies models gate and returns exit code 0."""
    exp_dir = tmp_path / "exp"
    _setup_stage1_ready(exp_dir)

    catalog = _create_sample_catalog()
    save_models_catalog(catalog, exp_dir / MODELS_CATALOG_REL_PATH)

    args = argparse.Namespace(experiment_dir=str(exp_dir))
    code = handle_models_verify(args)
    assert code == 0

    captured = capsys.readouterr()
    assert "Models gate verified successfully" in captured.out
    assert "Models count: 1" in captured.out


def test_m44_06_02_models_verify_gate_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """C17: handle_models_verify returns exit code 2 when models gate fails."""
    exp_dir = tmp_path / "exp"
    _setup_stage1_ready(exp_dir)

    # Subcase A: Missing models.json
    args = argparse.Namespace(experiment_dir=str(exp_dir))
    code_missing = handle_models_verify(args)
    assert code_missing == 2
    captured = capsys.readouterr()
    assert "Error:" in captured.err

    # Subcase B: Empty models catalog
    empty_file = exp_dir / MODELS_CATALOG_REL_PATH
    empty_file.parent.mkdir(parents=True, exist_ok=True)
    empty_file.write_text(json.dumps({"models": []}), encoding="utf-8")

    code_empty = handle_models_verify(args)
    assert code_empty == 2
    captured_empty = capsys.readouterr()
    assert "Error:" in captured_empty.err


def test_m44_06_03_models_verify_missing_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """C18: handle_models_verify returns exit code 2 when experiment directory is missing."""
    args = argparse.Namespace(experiment_dir=str(tmp_path / "nonexistent_dir"))
    code = handle_models_verify(args)
    assert code == 2

    captured = capsys.readouterr()
    assert "Error:" in captured.err
