"""Unit tests for 'expml features' subcommands (cli/cmd_features.py).

Verifies FEAT-01 to FEAT-07 and Checks C1 to C7.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from experimental_ml.cli.main import main
from experimental_ml.stages.stage_gates import (
    EXPLORATORY_FEATURES_REL_PATH,
    SCENARIOS_CATALOG_REL_PATH,
)


def _setup_sanitized_experiment(tmp_path: Path) -> Path:
    """Helper creating a valid sanitized experiment directory using expml CLI."""
    csv_file = tmp_path / "raw_data.csv"
    csv_content = (
        "id,x1,x2,target\n"
        "1,1.0,10.0,0\n"
        "2,2.0,20.0,0\n"
        "3,3.0,30.0,1\n"
        "4,4.0,40.0,1\n"
        "5,5.0,50.0,1\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    schema_file = tmp_path / "schema.json"
    schema_dict = {
        "target_col": "target",
        "observation_id_col": "id",
        "task_type": "BINARY_CLASSIFICATION",
        "column_semantic_types": {
            "x1": "NUMERIC_CONTINUOUS",
            "x2": "NUMERIC_CONTINUOUS",
        },
    }
    schema_file.write_text(json.dumps(schema_dict), encoding="utf-8")

    exp_dir = tmp_path / "exp"

    # Step 1: data profile
    code_prof = main([
        "data", "profile",
        "--data", str(csv_file),
        "--schema", str(schema_file),
        "--output-dir", str(exp_dir),
    ])
    assert code_prof == 0

    # Step 2: data sanitize
    rules_file = tmp_path / "rules.json"
    rules_file.write_text("[]", encoding="utf-8")

    code_san = main([
        "data", "sanitize",
        "--experiment-dir", str(exp_dir),
        "--rules", str(rules_file),
    ])
    assert code_san == 0

    return exp_dir


def test_feat_01_features_help(capsys: pytest.CaptureFixture[str]) -> None:
    """FEAT-01 (Check C1): expml features --help displays explore, scenarios, verify and exits code 0."""
    code = main(["features", "--help"])
    assert code == 0
    captured = capsys.readouterr()
    assert "explore" in captured.out
    assert "scenarios" in captured.out
    assert "verify" in captured.out


def test_feat_02_features_explore_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """FEAT-02 (Check C2): expml features explore writes reports/exploratory_features.json with scope and exits 0."""
    exp_dir = _setup_sanitized_experiment(tmp_path)

    code = main(["features", "explore", "--experiment-dir", str(exp_dir)])
    assert code == 0

    captured = capsys.readouterr()
    assert "Exploratory feature analysis completed successfully" in captured.out
    assert "Target column: target" in captured.out

    report_path = exp_dir / EXPLORATORY_FEATURES_REL_PATH
    assert report_path.exists()

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["scope"] == "EXPLORATORY_FULL_DATA"
    assert "target_associations" in data
    assert "pairwise_redundancy_matrix" in data


def test_feat_03_features_explore_overwrite_protection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """FEAT-03 (Check C3): expml features explore rejects overwrite without --force (code 2), succeeds with --force."""
    exp_dir = _setup_sanitized_experiment(tmp_path)

    # First run succeeds
    code1 = main(["features", "explore", "--experiment-dir", str(exp_dir)])
    assert code1 == 0

    # Second run without --force fails with code 2
    code2 = main(["features", "explore", "--experiment-dir", str(exp_dir)])
    assert code2 == 2
    captured = capsys.readouterr()
    assert "already exists" in captured.err
    assert "Use --force" in captured.err

    # Third run with --force succeeds with code 0
    code3 = main(["features", "explore", "--experiment-dir", str(exp_dir), "--force"])
    assert code3 == 0
