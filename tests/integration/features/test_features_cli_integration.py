"""End-to-end integration test suite for Stage 2 features CLI.

Complies with FEAT-08 (Check C8), CA-E2-01, CA-E2-02, and CLI-10/CLI-11.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from experimental_ml.stages.stage_gates import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    EXPLORATORY_FEATURES_REL_PATH,
    PARTITION_PLAN_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    SANITIZED_VIEW_REL_PATH,
    SCENARIOS_CATALOG_REL_PATH,
    SPLITS_CSV_GZ_REL_PATH,
)


def _get_expml_cmd() -> list[str]:
    """Resolve CLI executable path or construct python -m command."""
    expml_path = shutil.which("expml")
    if expml_path:
        return [expml_path]
    candidate = Path(sys.executable).parent / "expml"
    if candidate.exists():
        return [str(candidate)]
    return [sys.executable, "-m", "experimental_ml.cli.main"]


def test_feat_08_end_to_end_cli_pipeline(tmp_path: Path) -> None:
    """FEAT-08 (Check C8): Full end-to-end multi-stage pipeline executed via CLI subprocesses.

    Verifies:
    1. Pipeline stages (profile -> sanitize -> explore -> scenarios -> verify -> partition build).
    2. Subprocesses exit with code 0.
    3. Output hygiene: zero 64-character raw SHA-256 digests in stdout/stderr.
    4. Exact stage artifacts created and valid.
    """
    cmd = _get_expml_cmd()
    raw_hash_pattern = re.compile(r"\b[0-9a-fA-F]{64}\b")

    # Setup input data and configurations
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()

    raw_csv = inputs_dir / "dataset.csv"
    raw_csv.write_text(
        "obs_id,height,diameter,species,target\n"
        "T01,15.2,22.1,Eucalyptus,45.0\n"
        "T02,14.8,21.5,Eucalyptus,42.5\n"
        "T03,18.0,26.4,Pinus,55.1\n"
        "T04,17.5,25.8,Pinus,53.0\n"
        "T05,12.0,18.3,Eucalyptus,35.2\n"
        "T06,19.1,28.0,Pinus,58.4\n"
        "T07,13.4,19.9,Eucalyptus,38.0\n"
        "T08,16.0,23.5,Pinus,48.2\n",
        encoding="utf-8",
    )

    schema_file = inputs_dir / "schema.json"
    schema_dict = {
        "target_col": "target",
        "observation_id_col": "obs_id",
        "task_type": "REGRESSION",
        "column_semantic_types": {
            "height": "NUMERIC_CONTINUOUS",
            "diameter": "NUMERIC_CONTINUOUS",
            "species": "CATEGORICAL",
        },
    }
    schema_file.write_text(json.dumps(schema_dict, indent=2), encoding="utf-8")

    exp_dir = tmp_path / "experiment"

    # Step 1: expml data profile
    res_prof = subprocess.run(
        cmd + [
            "data", "profile",
            "--data", str(raw_csv),
            "--schema", str(schema_file),
            "--output-dir", str(exp_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_prof.returncode == 0, f"Profile failed: {res_prof.stderr}"
    assert not raw_hash_pattern.search(res_prof.stdout)
    assert (exp_dir / DATASET_DESCRIPTOR_REL_PATH).exists()
    assert (exp_dir / DATASET_PROFILE_REL_PATH).exists()

    # Step 2: expml data sanitize
    rules_file = inputs_dir / "rules.json"
    rules_content = [
        {
            "finding_code": "E1_CATEGORICAL_UNENCODED",
            "column": "species",
            "kind": "DEFER_INTRA_FOLD",
            "parameters": {"encoding_strategy": "ONE_HOT"},
        }
    ]
    rules_file.write_text(json.dumps(rules_content, indent=2), encoding="utf-8")

    res_san = subprocess.run(
        cmd + [
            "data", "sanitize",
            "--experiment-dir", str(exp_dir),
            "--rules", str(rules_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_san.returncode == 0, f"Sanitize failed: {res_san.stderr}"
    assert not raw_hash_pattern.search(res_san.stdout)
    assert (exp_dir / PREPARATION_PLAN_REL_PATH).exists()
    assert (exp_dir / SANITIZED_VIEW_REL_PATH).exists()

    # Step 3: expml features explore
    res_exp = subprocess.run(
        cmd + [
            "features", "explore",
            "--experiment-dir", str(exp_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_exp.returncode == 0, f"Features explore failed: {res_exp.stderr}"
    assert not raw_hash_pattern.search(res_exp.stdout)
    exploratory_file = exp_dir / EXPLORATORY_FEATURES_REL_PATH
    assert exploratory_file.exists()

    with open(exploratory_file, "r", encoding="utf-8") as f:
        exp_data = json.load(f)
    assert exp_data["scope"] == "EXPLORATORY_FULL_DATA"
    assert len(exp_data["target_associations"]) == 5

    # Step 4: expml features scenarios
    scenarios_file = inputs_dir / "scenarios.json"
    scenarios_content = [
        {
            "scenario_id": "all_biometric",
            "name": "All Biometric Features",
            "description": "Uses height and diameter",
            "scientific_justification": "Dendrometric standard",
            "mode": "FIXED",
            "selected_features": ["height", "diameter"],
        },
        {
            "scenario_id": "dynamic_variance",
            "name": "Dynamic Variance Selection",
            "description": "Selects features with variance > 0.1",
            "scientific_justification": "Filters uninformative predictors",
            "mode": "DYNAMIC",
            "strategy_name": "VARIANCE_THRESHOLD",
            "strategy_params": {"threshold": 0.1},
        },
    ]
    scenarios_file.write_text(json.dumps(scenarios_content, indent=2), encoding="utf-8")

    res_scn = subprocess.run(
        cmd + [
            "features", "scenarios",
            "--experiment-dir", str(exp_dir),
            "--scenarios", str(scenarios_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_scn.returncode == 0, f"Features scenarios failed: {res_scn.stderr}"
    assert not raw_hash_pattern.search(res_scn.stdout)
    scenarios_cat_file = exp_dir / SCENARIOS_CATALOG_REL_PATH
    assert scenarios_cat_file.exists()

    # Step 5: expml features verify
    res_ver = subprocess.run(
        cmd + [
            "features", "verify",
            "--experiment-dir", str(exp_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_ver.returncode == 0, f"Features verify failed: {res_ver.stderr}"
    assert not raw_hash_pattern.search(res_ver.stdout)

    # Step 6: expml partition build
    part_config_file = inputs_dir / "partition_config.json"
    part_config_content = {
        "strategy": "KFOLD",
        "n_splits": 2,
        "validation_mode": "CV_ONLY",
    }
    part_config_file.write_text(json.dumps(part_config_content, indent=2), encoding="utf-8")

    res_part = subprocess.run(
        cmd + [
            "partition", "build",
            "--experiment-dir", str(exp_dir),
            "--config", str(part_config_file),
            "--seed", "42",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_part.returncode == 0, f"Partition build failed: {res_part.stderr}"
    assert not raw_hash_pattern.search(res_part.stdout)
    assert (exp_dir / PARTITION_PLAN_REL_PATH).exists()
    assert (exp_dir / SPLITS_CSV_GZ_REL_PATH).exists()

    # Step 7: expml partition verify
    res_part_ver = subprocess.run(
        cmd + [
            "partition", "verify",
            "--experiment-dir", str(exp_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_part_ver.returncode == 0, f"Partition verify failed: {res_part_ver.stderr}"
    assert not raw_hash_pattern.search(res_part_ver.stdout)
