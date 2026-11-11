"""End-to-end integration test suite for Stage 3 models CLI (MPC-07).

Complies with CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11, and MPC-07.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

from experimental_ml.cli.main import build_parser
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.stages.stage_gates import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    MODELS_CATALOG_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
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


def test_m44_07_01_cli_parser_registration() -> None:
    """C19: main.py registers models subparser with validate and verify commands."""
    parser = build_parser()

    # Verify 'models validate' parses arguments
    args_val = parser.parse_args([
        "models", "validate",
        "--experiment-dir", "/tmp/exp",
        "--models", "/tmp/models.json",
        "--force",
    ])
    assert args_val.command == "models"
    assert args_val.subcommand == "validate"
    assert args_val.experiment_dir == "/tmp/exp"
    assert args_val.models == "/tmp/models.json"
    assert args_val.force is True

    # Verify 'models verify' parses arguments
    args_ver = parser.parse_args([
        "models", "verify",
        "--experiment-dir", "/tmp/exp",
    ])
    assert args_ver.command == "models"
    assert args_ver.subcommand == "verify"
    assert args_ver.experiment_dir == "/tmp/exp"


def test_m44_07_02_cli_import_purity() -> None:
    """C20: cmd_models.py maintains zero module-level heavy imports (CLI-10)."""
    cmd_models_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "experimental_ml"
        / "cli"
        / "cmd_models.py"
    )
    assert cmd_models_path.exists()

    tree = ast.parse(cmd_models_path.read_text(encoding="utf-8"), filename=str(cmd_models_path))
    forbidden = {"numpy", "scipy", "sklearn", "hashlib"}

    # Top-level body AST check: verify no top-level imports of forbidden modules
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_mod = alias.name.split(".")[0]
                assert root_mod not in forbidden, f"cmd_models.py has module-level import of '{root_mod}'"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_mod = node.module.split(".")[0]
                assert root_mod not in forbidden, f"cmd_models.py has module-level import of '{root_mod}'"

    # Runtime check in clean subprocess: importing cmd_models does not load numpy
    code = (
        "import sys\n"
        "import experimental_ml.cli.cmd_models\n"
        "forbidden = {'numpy', 'scipy', 'sklearn', 'hashlib'}\n"
        "loaded = forbidden.intersection(sys.modules.keys())\n"
        "assert not loaded, f'Loaded forbidden modules: {loaded}'\n"
    )
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert res.returncode == 0, f"Import purity runtime check failed: {res.stderr}"


def test_m44_07_03_e2e_cli_subprocess(tmp_path: Path) -> None:
    """C21: Subprocess execution validates full CLI lifecycle for models validate and verify."""
    cmd = _get_expml_cmd()
    exp_dir = tmp_path / "exp"
    _setup_stage1_ready(exp_dir)

    models_file = tmp_path / "models.json"
    models_content = [
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
    models_file.write_text(json.dumps(models_content, indent=2), encoding="utf-8")

    # Step 1: models validate (first run succeeds)
    res_val = subprocess.run(
        cmd + [
            "models", "validate",
            "--experiment-dir", str(exp_dir),
            "--models", str(models_file),
        ],
        capture_output=True,
        text=True,
    )
    assert res_val.returncode == 0, f"models validate failed: {res_val.stderr}"
    assert "Models catalog validated and saved successfully" in res_val.stdout
    assert (exp_dir / MODELS_CATALOG_REL_PATH).exists()

    # Step 2: models verify (gate passes)
    res_ver = subprocess.run(
        cmd + [
            "models", "verify",
            "--experiment-dir", str(exp_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert res_ver.returncode == 0, f"models verify failed: {res_ver.stderr}"
    assert "Models gate verified successfully" in res_ver.stdout

    # Step 3: models validate without --force fails with code 2
    res_val_dup = subprocess.run(
        cmd + [
            "models", "validate",
            "--experiment-dir", str(exp_dir),
            "--models", str(models_file),
        ],
        capture_output=True,
        text=True,
    )
    assert res_val_dup.returncode == 2
    assert "Error:" in res_val_dup.stderr

    # Step 4: models validate with --force succeeds
    res_val_force = subprocess.run(
        cmd + [
            "models", "validate",
            "--experiment-dir", str(exp_dir),
            "--models", str(models_file),
            "--force",
        ],
        capture_output=True,
        text=True,
    )
    assert res_val_force.returncode == 0
    assert "Models catalog validated and saved successfully" in res_val_force.stdout

    # Step 5: models verify with missing experiment directory fails with code 2
    res_ver_missing = subprocess.run(
        cmd + [
            "models", "verify",
            "--experiment-dir", str(tmp_path / "nonexistent"),
        ],
        capture_output=True,
        text=True,
    )
    assert res_ver_missing.returncode == 2
    assert "Error:" in res_ver_missing.stderr
