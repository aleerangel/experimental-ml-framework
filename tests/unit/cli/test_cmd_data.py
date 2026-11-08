"""Unit tests for 'expml data' subcommands (cli/cmd_data.py).

Verifies CLI-01, CLI-02, CLI-03, CLI-08 and Checks C1, C2, C3.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from experimental_ml.cli.main import main
from experimental_ml.stages.stage_gates import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    SANITIZED_VIEW_REL_PATH,
)


def _create_sample_dataset(tmp_path: Path) -> tuple[Path, Path]:
    """Helper creating a sample CSV data file and schema JSON."""
    csv_file = tmp_path / "data.csv"
    csv_content = (
        "id,feat_num,feat_cat,target\n"
        "1,10.5,A,1\n"
        "2,,B,0\n"
        "3,30.2,A,1\n"
        "4,40.1,C,0\n"
        "5,50.0,B,1\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

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

    return csv_file, schema_file


def test_cli_01_data_profile_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI-01 (Check C1): expml data profile produces descriptor and profile, exits code 0."""
    csv_file, schema_file = _create_sample_dataset(tmp_path)
    output_dir = tmp_path / "experiment_01"

    code = main([
        "data", "profile",
        "--data", str(csv_file),
        "--schema", str(schema_file),
        "--output-dir", str(output_dir),
    ])
    captured = capsys.readouterr()

    # 1. Successful exit code
    assert code == 0

    # 2. Artifacts created
    desc_file = output_dir / DATASET_DESCRIPTOR_REL_PATH
    prof_file = output_dir / DATASET_PROFILE_REL_PATH
    assert desc_file.exists()
    assert prof_file.exists()

    # 3. Output contains dimensions and findings
    assert "Dataset profiled: 5 rows x 4 columns" in captured.out
    assert "Findings identified" in captured.out
    assert "E1_FEATURE_MISSING" in captured.out
    assert "E1_CATEGORICAL_UNENCODED" in captured.out

    # 4. Overwrite protection without --force exits code 2
    code_no_force = main([
        "data", "profile",
        "--data", str(csv_file),
        "--schema", str(schema_file),
        "--output-dir", str(output_dir),
    ])
    assert code_no_force == 2

    # 5. Overwrite with --force succeeds
    code_force = main([
        "data", "profile",
        "--data", str(csv_file),
        "--schema", str(schema_file),
        "--output-dir", str(output_dir),
        "--force",
    ])
    assert code_force == 0


def test_cli_03_data_sanitize_incomplete_plan_rejected(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI-03 (Check C3): INCOMPLETE plan prints unresolved issues, doesn't write plan, exits code 2."""
    csv_file, schema_file = _create_sample_dataset(tmp_path)
    exp_dir = tmp_path / "experiment_02"

    # Run profile first
    main([
        "data", "profile",
        "--data", str(csv_file),
        "--schema", str(schema_file),
        "--output-dir", str(exp_dir),
    ])
    capsys.readouterr()

    # Incomplete rules (missing rule for E1_CATEGORICAL_UNENCODED on feat_cat)
    incomplete_rules_file = tmp_path / "incomplete_rules.json"
    incomplete_rules = [
        {"finding_code": "E1_FEATURE_MISSING", "column": "feat_num", "kind": "DROP_ROWS"},
    ]
    incomplete_rules_file.write_text(json.dumps(incomplete_rules), encoding="utf-8")

    code = main([
        "data", "sanitize",
        "--experiment-dir", str(exp_dir),
        "--rules", str(incomplete_rules_file),
    ])
    captured = capsys.readouterr()

    # Exit code 2
    assert code == 2

    # Error output lists unresolved findings
    assert "Preparation plan is INCOMPLETE" in captured.err
    assert "E1_CATEGORICAL_UNENCODED" in captured.err

    # Crucial: configuration/preparation_plan.json MUST NOT be created
    plan_file = exp_dir / PREPARATION_PLAN_REL_PATH
    assert not plan_file.exists()


def test_cli_02_data_sanitize_ready_plan(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI-02 (Check C2): Complete rules create preparation_plan.json and sanitized_view.json, exit 0."""
    csv_file, schema_file = _create_sample_dataset(tmp_path)
    exp_dir = tmp_path / "experiment_03"

    # Profile first
    main([
        "data", "profile",
        "--data", str(csv_file),
        "--schema", str(schema_file),
        "--output-dir", str(exp_dir),
    ])
    capsys.readouterr()

    # Complete rules covering both confirmed findings
    complete_rules_file = tmp_path / "complete_rules.json"
    complete_rules = [
        {"finding_code": "E1_FEATURE_MISSING", "column": "feat_num", "kind": "DROP_ROWS"},
        {"finding_code": "E1_CATEGORICAL_UNENCODED", "column": "feat_cat", "kind": "ACCEPT_AS_IS"},
    ]
    complete_rules_file.write_text(json.dumps(complete_rules), encoding="utf-8")

    code = main([
        "data", "sanitize",
        "--experiment-dir", str(exp_dir),
        "--rules", str(complete_rules_file),
    ])
    captured = capsys.readouterr()

    # Exit code 0
    assert code == 0

    # Artifacts created
    plan_file = exp_dir / PREPARATION_PLAN_REL_PATH
    view_file = exp_dir / SANITIZED_VIEW_REL_PATH
    assert plan_file.exists()
    assert view_file.exists()

    assert "Dataset sanitized successfully." in captured.out
    assert "Surviving observations: 4 (dropped: 1)" in captured.out


def test_cli_08_data_profile_force_flag_behavior(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI-08: Output files cannot be overwritten unless --force is passed."""
    csv_file, schema_file = _create_sample_dataset(tmp_path)
    output_dir = tmp_path / "experiment_force"

    # First run succeeds
    code1 = main([
        "data", "profile",
        "--data", str(csv_file),
        "--schema", str(schema_file),
        "--output-dir", str(output_dir),
    ])
    assert code1 == 0

    # Second run without --force exits with code 2 (FileExistsError / ConfigurationError)
    capsys.readouterr()
    code2 = main([
        "data", "profile",
        "--data", str(csv_file),
        "--schema", str(schema_file),
        "--output-dir", str(output_dir),
    ])
    assert code2 == 2
    captured = capsys.readouterr()
    assert "Error:" in captured.err

    # Third run with --force succeeds
    code3 = main([
        "data", "profile",
        "--data", str(csv_file),
        "--schema", str(schema_file),
        "--output-dir", str(output_dir),
        "--force",
    ])
    assert code3 == 0
