"""Unit tests for partition subcommands.

Complies with CLI-04 (Check C4), CLI-05 (Check C5), CLI-07, CLI-08, and CLI-11.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

import pytest

from experimental_ml.cli.main import main
from experimental_ml.core.storage import read_json, write_json_atomic
from experimental_ml.stages.stage_gates import (
    PARTITION_PLAN_REL_PATH,
    SPLITS_CSV_GZ_REL_PATH,
    SPLITS_SCHEMA_REL_PATH,
)


def _setup_prepared_experiment(tmp_path: Path) -> Path:
    """Helper to prepare an experiment up to sanitized view."""
    exp_dir = tmp_path / "experiment_base"
    raw_csv = tmp_path / "raw_data.csv"
    raw_csv.write_text(
        "id,feat_num,feat_cat,target\n"
        "1,10.0,A,1\n"
        "2,20.0,B,0\n"
        "3,15.0,A,1\n"
        "4,40.0,C,0\n"
        "5,50.0,B,1\n"
        "6,60.0,A,0\n",
        encoding="utf-8",
    )

    schema_file = tmp_path / "schema.json"
    schema_dict = {
        "target_col": "target",
        "task_type": "BINARY_CLASSIFICATION",
        "column_semantic_types": {
            "feat_num": "NUMERIC_CONTINUOUS",
            "feat_cat": "CATEGORICAL",
        },
    }
    schema_file.write_text(json.dumps(schema_dict), encoding="utf-8")

    # 1. Profile
    code_prof = main([
        "data", "profile",
        "--data", str(raw_csv),
        "--schema", str(schema_file),
        "--output-dir", str(exp_dir),
    ])
    assert code_prof == 0

    # 2. Sanitize with rules
    rules_file = tmp_path / "rules.json"
    rules = [
        {"finding_code": "E1_CATEGORICAL_UNENCODED", "column": "feat_cat", "kind": "ACCEPT_AS_IS"},
    ]
    rules_file.write_text(json.dumps(rules), encoding="utf-8")

    code_san = main([
        "data", "sanitize",
        "--experiment-dir", str(exp_dir),
        "--rules", str(rules_file),
    ])
    assert code_san == 0

    return exp_dir


def test_cli_04_partition_build_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI-04 (Check C4): expml partition build creates plan, splits.csv.gz, splits.schema.json, exits 0."""
    exp_dir = _setup_prepared_experiment(tmp_path)
    capsys.readouterr()

    config_file = tmp_path / "partition_config.json"
    config_dict = {
        "strategy": "KFOLD",
        "regime": "CV_ONLY",
        "n_splits": 3,
        "master_seed": 42,
    }
    config_file.write_text(json.dumps(config_dict), encoding="utf-8")

    code = main([
        "partition", "build",
        "--experiment-dir", str(exp_dir),
        "--config", str(config_file),
    ])
    captured = capsys.readouterr()

    # 1. Exits with code 0
    assert code == 0

    # 2. Artifacts created
    plan_path = exp_dir / PARTITION_PLAN_REL_PATH
    splits_path = exp_dir / SPLITS_CSV_GZ_REL_PATH
    schema_path = exp_dir / SPLITS_SCHEMA_REL_PATH

    assert plan_path.exists()
    assert splits_path.exists()
    assert schema_path.exists()

    # 3. Informative summary output
    assert "Partition plan built successfully: regime=CV_ONLY, strategy=KFOLD" in captured.out
    assert "Observations: total=6, development=6, holdout=0" in captured.out
    assert "Fold 0: train=4, val=2" in captured.out
    assert "Fold 1: train=4, val=2" in captured.out
    assert "Fold 2: train=4, val=2" in captured.out

    # 4. CLI-11: No raw 64-char hash digests in stdout
    raw_hash_pattern = re.compile(r"\b[0-9a-f]{64}\b")
    assert not raw_hash_pattern.search(captured.out)
    assert not raw_hash_pattern.search(captured.err)


def test_cli_04_partition_build_seed_override(tmp_path: Path) -> None:
    """CLI-04: --seed overrides master_seed from partition config file."""
    exp_dir = _setup_prepared_experiment(tmp_path)

    config_file = tmp_path / "partition_config.json"
    config_dict = {
        "strategy": "KFOLD",
        "regime": "CV_ONLY",
        "n_splits": 3,
        "master_seed": 42,
    }
    config_file.write_text(json.dumps(config_dict), encoding="utf-8")

    code = main([
        "partition", "build",
        "--experiment-dir", str(exp_dir),
        "--config", str(config_file),
        "--seed", "999",
    ])
    assert code == 0

    plan_path = exp_dir / PARTITION_PLAN_REL_PATH
    plan_dict = read_json(plan_path)
    assert plan_dict["config"]["master_seed"] == 999


def test_cli_05_partition_verify_clean_and_tampered(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI-05 (Check C5): expml partition verify exits 0 when clean, and 2 when tampered."""
    exp_dir = _setup_prepared_experiment(tmp_path)

    config_file = tmp_path / "partition_config.json"
    config_dict = {
        "strategy": "KFOLD",
        "regime": "CV_ONLY",
        "n_splits": 3,
        "master_seed": 42,
    }
    config_file.write_text(json.dumps(config_dict), encoding="utf-8")

    # Build first
    code_build = main([
        "partition", "build",
        "--experiment-dir", str(exp_dir),
        "--config", str(config_file),
    ])
    assert code_build == 0
    capsys.readouterr()

    # 1. Clean verify exits with code 0
    code_clean = main([
        "partition", "verify",
        "--experiment-dir", str(exp_dir),
    ])
    captured_clean = capsys.readouterr()
    assert code_clean == 0
    assert "Partition plan verification PASSED" in captured_clean.out

    # 2. Tamper partition_plan.json -> verify exits with code 2 without traceback
    plan_path = exp_dir / PARTITION_PLAN_REL_PATH
    plan_dict = read_json(plan_path)
    plan_dict["source_dataset_hash"] = "0" * 64
    write_json_atomic(plan_path, plan_dict, overwrite=True)

    code_tampered = main([
        "partition", "verify",
        "--experiment-dir", str(exp_dir),
    ])
    captured_tampered = capsys.readouterr()
    assert code_tampered == 2
    assert "Error:" in captured_tampered.err
    assert "Traceback" not in captured_tampered.err


def test_cli_07_upstream_gate_missing_blocked(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI-07: partition commands fail with exit code 2 when upstream preparation gate is unmet."""
    empty_exp_dir = tmp_path / "empty_exp"
    empty_exp_dir.mkdir()

    config_file = tmp_path / "cfg.json"
    config_file.write_text(json.dumps({"strategy": "KFOLD", "n_splits": 3}), encoding="utf-8")

    # partition build fails on empty experiment
    code_build = main([
        "partition", "build",
        "--experiment-dir", str(empty_exp_dir),
        "--config", str(config_file),
    ])
    captured_build = capsys.readouterr()
    assert code_build == 2
    assert "Error:" in captured_build.err
    assert "Traceback" not in captured_build.err

    # partition verify fails on empty experiment
    code_verify = main([
        "partition", "verify",
        "--experiment-dir", str(empty_exp_dir),
    ])
    captured_verify = capsys.readouterr()
    assert code_verify == 2
    assert "Error:" in captured_verify.err
    assert "Traceback" not in captured_verify.err


def test_cli_08_partition_build_force_flag_behavior(tmp_path: Path) -> None:
    """CLI-08: partition build refuses overwrite without --force, succeeds with --force."""
    exp_dir = _setup_prepared_experiment(tmp_path)

    config_file = tmp_path / "partition_config.json"
    config_dict = {
        "strategy": "KFOLD",
        "regime": "CV_ONLY",
        "n_splits": 3,
        "master_seed": 42,
    }
    config_file.write_text(json.dumps(config_dict), encoding="utf-8")

    # First build
    code1 = main([
        "partition", "build",
        "--experiment-dir", str(exp_dir),
        "--config", str(config_file),
    ])
    assert code1 == 0

    # Second build without --force fails with code 2
    code2 = main([
        "partition", "build",
        "--experiment-dir", str(exp_dir),
        "--config", str(config_file),
    ])
    assert code2 == 2

    # Third build with --force succeeds with code 0
    code3 = main([
        "partition", "build",
        "--experiment-dir", str(exp_dir),
        "--config", str(config_file),
        "--force",
    ])
    assert code3 == 0
