"""Unit tests for 'expml models validate' subcommand (MPC-05)."""

import argparse
import json
from pathlib import Path
import pytest

from experimental_ml.cli.cmd_models import handle_models_validate
from experimental_ml.core.storage import write_json_atomic
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


def _create_sample_models_json(path: Path) -> Path:
    models_data = {
        "models": [
            {
                "model_id": "dummy_mean",
                "display_name": "Dummy Mean Baseline",
                "family": "BASELINE",
                "estimator_factory": "DUMMY_BASELINE_MEAN",
                "capabilities": {
                    "requires_fit": True,
                },
                "description": "Baseline model predicting the mean",
                "scientific_justification": "Comparator baseline",
            }
        ]
    }
    path.write_text(json.dumps(models_data, indent=2), encoding="utf-8")
    return path


def test_m44_05_01_models_validate_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """C13: handle_models_validate validates and saves models.json with exit code 0."""
    exp_dir = tmp_path / "exp"
    _setup_stage1_ready(exp_dir)

    models_file = _create_sample_models_json(tmp_path / "models_input.json")
    args = argparse.Namespace(
        experiment_dir=str(exp_dir),
        models=str(models_file),
        force=False,
    )

    code = handle_models_validate(args)
    assert code == 0

    captured = capsys.readouterr()
    assert "Models catalog validated and saved successfully" in captured.out
    assert "Models count: 1" in captured.out

    dest_path = exp_dir / MODELS_CATALOG_REL_PATH
    assert dest_path.exists()


def test_m44_05_02_models_validate_overwrite_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """C14: handle_models_validate returns exit code 2 when destination exists and --force omitted."""
    exp_dir = tmp_path / "exp"
    _setup_stage1_ready(exp_dir)

    models_file = _create_sample_models_json(tmp_path / "models_input.json")
    args = argparse.Namespace(
        experiment_dir=str(exp_dir),
        models=str(models_file),
        force=False,
    )

    # First validation succeeds
    code1 = handle_models_validate(args)
    assert code1 == 0

    # Second validation without force fails with code 2
    code2 = handle_models_validate(args)
    assert code2 == 2

    captured = capsys.readouterr()
    assert "Error:" in captured.err

    # With force=True succeeds
    args_force = argparse.Namespace(
        experiment_dir=str(exp_dir),
        models=str(models_file),
        force=True,
    )
    code3 = handle_models_validate(args_force)
    assert code3 == 0


def test_m44_05_03_models_validate_invalid_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """C15: handle_models_validate returns exit code 2 when models input file is missing or invalid."""
    exp_dir = tmp_path / "exp"
    _setup_stage1_ready(exp_dir)

    # Missing models file
    args_missing = argparse.Namespace(
        experiment_dir=str(exp_dir),
        models=str(tmp_path / "nonexistent.json"),
        force=False,
    )
    code_missing = handle_models_validate(args_missing)
    assert code_missing == 2
    captured = capsys.readouterr()
    assert "Error:" in captured.err

    # Invalid models file format (neither list nor dict with models)
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text(json.dumps("invalid string payload"), encoding="utf-8")
    args_invalid = argparse.Namespace(
        experiment_dir=str(exp_dir),
        models=str(invalid_file),
        force=False,
    )
    code_invalid = handle_models_validate(args_invalid)
    assert code_invalid == 2
    captured = capsys.readouterr()
    assert "Error:" in captured.err

    # Missing experiment directory
    args_no_dir = argparse.Namespace(
        experiment_dir=str(tmp_path / "no_exp_dir"),
        models=str(invalid_file),
        force=False,
    )
    code_no_dir = handle_models_validate(args_no_dir)
    assert code_no_dir == 2
    captured = capsys.readouterr()
    assert "Error:" in captured.err
