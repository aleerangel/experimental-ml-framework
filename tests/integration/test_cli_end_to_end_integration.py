"""End-to-end integration acceptance test suite via expml CLI subprocess.

Complies with CLI-10, CLI-11, and CLI-12 (Check C10).
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from experimental_ml.stages.stage_gates import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    PARTITION_PLAN_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    SANITIZED_VIEW_REL_PATH,
    SPLITS_CSV_GZ_REL_PATH,
    SPLITS_SCHEMA_REL_PATH,
)
from experimental_ml.validation.storage import read_splits_csv_gz


def _get_expml_executable() -> list[str]:
    """Find expml executable or construct fallback invocation."""
    expml_path = shutil.which("expml")
    if expml_path:
        return [expml_path]
    candidate = Path(sys.executable).parent / "expml"
    if candidate.exists():
        return [str(candidate)]
    return [sys.executable, "-m", "experimental_ml.cli.main"]


def test_cli_12_end_to_end_subprocess_acceptance_scenario(tmp_path: Path) -> None:
    """CLI-12 (Check C10): Complete pipeline executed via CLI in two independent directories.

    Verifies:
    1. Subprocess execution exits with code 0 for profile, sanitize, partition build, and verify.
    2. Zero raw 64-character hash digests appear in stdout/stderr of any subprocess call (CLI-11).
    3. Exactly bit-identical partition_plan.json bytes across both directory runs.
    4. Exactly bit-identical splits.csv.gz bytes (due to mtime=0.0) and identical decompressed content.
    5. Clean stage gates and full artifact hierarchy generated.
    """
    cmd_prefix = _get_expml_executable()
    raw_hash_pattern = re.compile(r"\b[0-9a-f]{64}\b")

    # Shared input data and configurations
    shared_dir = tmp_path / "inputs"
    shared_dir.mkdir()

    raw_csv = shared_dir / "dataset.csv"
    raw_csv.write_text(
        "id,feature_num,feature_cat,target\n"
        "1,10.5,typeA,1\n"
        "2,20.0,typeB,0\n"
        "3,,typeA,1\n"
        "4,40.1,typeC,0\n"
        "5,50.3,typeB,1\n"
        "6,60.2,typeA,0\n"
        "7,70.9,typeC,1\n"
        "8,80.4,typeB,0\n",
        encoding="utf-8",
    )

    schema_file = shared_dir / "schema.json"
    schema_payload = {
        "target_col": "target",
        "task_type": "BINARY_CLASSIFICATION",
        "column_semantic_types": {
            "feature_num": "NUMERIC_CONTINUOUS",
            "feature_cat": "CATEGORICAL",
        },
    }
    schema_file.write_text(json.dumps(schema_payload, indent=2), encoding="utf-8")

    rules_file = shared_dir / "rules.json"
    rules_payload = [
        {"finding_code": "E1_FEATURE_MISSING", "column": "feature_num", "kind": "DROP_ROWS"},
        {"finding_code": "E1_CATEGORICAL_UNENCODED", "column": "feature_cat", "kind": "ACCEPT_AS_IS"},
    ]
    rules_file.write_text(json.dumps(rules_payload, indent=2), encoding="utf-8")

    part_cfg_file = shared_dir / "partition_config.json"
    part_cfg_payload = {
        "strategy": "KFOLD",
        "regime": "CV_ONLY",
        "n_splits": 3,
        "master_seed": 2026,
    }
    part_cfg_file.write_text(json.dumps(part_cfg_payload, indent=2), encoding="utf-8")

    def run_subcommand(subargs: list[str]) -> subprocess.CompletedProcess[str]:
        full_cmd = cmd_prefix + subargs
        res = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert res.returncode == 0, f"Command {full_cmd} failed ({res.returncode}):\nSTDERR: {res.stderr}\nSTDOUT: {res.stdout}"
        # CLI-11 check on output
        assert not raw_hash_pattern.search(res.stdout), f"Raw hash found in stdout of {subargs}: {res.stdout}"
        assert not raw_hash_pattern.search(res.stderr), f"Raw hash found in stderr of {subargs}: {res.stderr}"
        return res

    # Directory 1 execution
    dir_1 = tmp_path / "experiment_run_1"
    run_subcommand(["data", "profile", "--data", str(raw_csv), "--schema", str(schema_file), "--output-dir", str(dir_1)])
    run_subcommand(["data", "sanitize", "--experiment-dir", str(dir_1), "--rules", str(rules_file)])
    run_subcommand(["partition", "build", "--experiment-dir", str(dir_1), "--config", str(part_cfg_file)])
    run_subcommand(["partition", "verify", "--experiment-dir", str(dir_1)])

    # Directory 2 execution (independent)
    dir_2 = tmp_path / "experiment_run_2"
    run_subcommand(["data", "profile", "--data", str(raw_csv), "--schema", str(schema_file), "--output-dir", str(dir_2)])
    run_subcommand(["data", "sanitize", "--experiment-dir", str(dir_2), "--rules", str(rules_file)])
    run_subcommand(["partition", "build", "--experiment-dir", str(dir_2), "--config", str(part_cfg_file)])
    run_subcommand(["partition", "verify", "--experiment-dir", str(dir_2)])

    # Verify all expected artifacts exist in both directories
    for exp_dir in (dir_1, dir_2):
        assert (exp_dir / DATASET_DESCRIPTOR_REL_PATH).exists()
        assert (exp_dir / DATASET_PROFILE_REL_PATH).exists()
        assert (exp_dir / PREPARATION_PLAN_REL_PATH).exists()
        assert (exp_dir / SANITIZED_VIEW_REL_PATH).exists()
        assert (exp_dir / PARTITION_PLAN_REL_PATH).exists()
        assert (exp_dir / SPLITS_CSV_GZ_REL_PATH).exists()
        assert (exp_dir / SPLITS_SCHEMA_REL_PATH).exists()

    # CLI-12: Compare bit-identical byte equivalence
    plan_bytes_1 = (dir_1 / PARTITION_PLAN_REL_PATH).read_bytes()
    plan_bytes_2 = (dir_2 / PARTITION_PLAN_REL_PATH).read_bytes()
    assert plan_bytes_1 == plan_bytes_2, "partition_plan.json byte sequences differ across runs!"

    splits_gz_bytes_1 = (dir_1 / SPLITS_CSV_GZ_REL_PATH).read_bytes()
    splits_gz_bytes_2 = (dir_2 / SPLITS_CSV_GZ_REL_PATH).read_bytes()
    assert splits_gz_bytes_1 == splits_gz_bytes_2, "splits.csv.gz compressed bytes differ across runs!"

    splits_rows_1 = read_splits_csv_gz(dir_1 / SPLITS_CSV_GZ_REL_PATH)
    splits_rows_2 = read_splits_csv_gz(dir_2 / SPLITS_CSV_GZ_REL_PATH)
    assert splits_rows_1 == splits_rows_2, "Decompressed splits rows differ across runs!"
    # 8 raw rows minus 1 missing row dropped = 7 surviving rows
    assert len(splits_rows_1) == 7
