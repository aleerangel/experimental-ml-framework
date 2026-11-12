"""Transversal end-to-end integration tests for expml run CLI lifecycle and runtime purity.

Covers ORCH-28, XCUT-02, CLI-10, CLI-11, and Checks C20 to C22.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import pytest


def _get_expml_cmd() -> list[str]:
    """Resolve command prefix to execute expml CLI."""
    expml_path = shutil.which("expml")
    if expml_path:
        return [expml_path]
    candidate = Path(sys.executable).parent / "expml"
    if candidate.exists():
        return [str(candidate)]
    return [sys.executable, "-m", "experimental_ml.cli.main"]


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Execute CLI command in an isolated subprocess."""
    cmd = _get_expml_cmd() + args
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_m54_05_01_e2e_cli_pipeline_lifecycle(tmp_path: Path) -> None:
    """C20: Ciclo ponta a ponta da CLI executa etapas 1 a 4B com sucesso (ORCH-28, AC 5)."""
    sha256_regex = re.compile(r"\b[0-9a-f]{64}\b", re.IGNORECASE)

    raw_csv = tmp_path / "raw.csv"
    raw_csv.write_text(
        "id,x1,x2,y\n"
        "1,1.0,10.0,2.0\n"
        "2,2.0,20.0,4.0\n"
        "3,3.0,30.0,6.0\n"
        "4,4.0,40.0,8.0\n"
        "5,5.0,50.0,10.0\n"
        "6,6.0,60.0,12.0\n"
        "7,7.0,70.0,14.0\n"
        "8,8.0,80.0,16.0\n"
        "9,9.0,90.0,18.0\n",
        encoding="utf-8",
    )

    schema_file = tmp_path / "schema.json"
    schema_file.write_text(
        json.dumps({
            "target_col": "y",
            "observation_id_col": "id",
            "task_type": "REGRESSION",
            "column_semantic_types": {
                "x1": "NUMERIC_CONTINUOUS",
                "x2": "NUMERIC_CONTINUOUS",
                "y": "NUMERIC_CONTINUOUS",
            },
        }),
        encoding="utf-8",
    )

    exp_dir = tmp_path / "experiment"

    # Step 1: data profile
    p1 = _run_cli([
        "data", "profile",
        "--data", str(raw_csv),
        "--schema", str(schema_file),
        "--output-dir", str(exp_dir),
    ])
    assert p1.returncode == 0, f"data profile failed: {p1.stderr}"

    # Step 2: data sanitize
    rules_file = tmp_path / "rules.json"
    rules_file.write_text("[]", encoding="utf-8")
    p2 = _run_cli([
        "data", "sanitize",
        "--experiment-dir", str(exp_dir),
        "--rules", str(rules_file),
    ])
    assert p2.returncode == 0, f"data sanitize failed: {p2.stderr}"

    # Step 3: partition build (3 folds)
    part_file = tmp_path / "partition.json"
    part_file.write_text(
        json.dumps({
            "strategy": "KFOLD",
            "regime": "CV_ONLY",
            "n_splits": 3,
            "master_seed": 42,
        }),
        encoding="utf-8",
    )
    p3 = _run_cli([
        "partition", "build",
        "--experiment-dir", str(exp_dir),
        "--config", str(part_file),
    ])
    assert p3.returncode == 0, f"partition build failed: {p3.stderr}"

    # Step 4: features scenarios
    scenarios_file = tmp_path / "scenarios.json"
    scenarios_file.write_text(
        json.dumps([
            {
                "scenario_id": "sc1",
                "name": "Scenario 1",
                "description": "Univariate baseline",
                "scientific_justification": "Primary comparator",
                "mode": "FIXED",
                "selected_features": ["x1"],
            }
        ]),
        encoding="utf-8",
    )
    p4 = _run_cli([
        "features", "scenarios",
        "--experiment-dir", str(exp_dir),
        "--scenarios", str(scenarios_file),
    ])
    assert p4.returncode == 0, f"features scenarios failed: {p4.stderr}"

    # Step 5: models validate
    models_file = tmp_path / "models.json"
    models_file.write_text(
        json.dumps({
            "models": [
                {
                    "model_id": "dummy_mean",
                    "display_name": "Dummy Mean Baseline",
                    "family": "BASELINE",
                    "estimator_factory": "DUMMY_BASELINE_MEAN",
                    "capabilities": {"requires_fit": True},
                    "description": "Baseline model predicting the mean",
                    "scientific_justification": "Comparator baseline",
                }
            ]
        }),
        encoding="utf-8",
    )
    p5 = _run_cli([
        "models", "validate",
        "--experiment-dir", str(exp_dir),
        "--models", str(models_file),
    ])
    assert p5.returncode == 0, f"models validate failed: {p5.stderr}"

    # Step 6: expml run start
    p6 = _run_cli([
        "run", "start",
        "--experiment-dir", str(exp_dir),
        "-j", "2",
    ])
    assert p6.returncode == 0, f"run start failed: {p6.stderr}"
    assert "Experiment matrix execution completed" in p6.stdout
    assert "Total cells: 3" in p6.stdout
    assert "Completed cells: 3" in p6.stdout
    assert not sha256_regex.search(p6.stdout), "Cryptographic hash leak in run start output"

    # Step 7: expml run status
    run_dir = exp_dir / "runs"
    p7 = _run_cli(["run", "status", "--run-dir", str(run_dir)])
    assert p7.returncode == 0, f"run status failed: {p7.stderr}"
    assert "Completed: 3 (100.0%)" in p7.stdout
    assert not sha256_regex.search(p7.stdout), "Cryptographic hash leak in run status output"

    # Step 8: expml run verify
    p8 = _run_cli(["run", "verify", "--run-dir", str(run_dir)])
    assert p8.returncode == 0, f"run verify failed: {p8.stderr}"
    assert "Status: READY" in p8.stdout
    assert not sha256_regex.search(p8.stdout), "Cryptographic hash leak in run verify output"

    # Step 9: Verify physical artifacts on disk
    assert (run_dir / "execution_state.json").exists()
    assert len(list((run_dir / "cells").glob("*.json"))) == 3
    assert len(list((run_dir / "predictions").glob("*.json"))) == 3
    assert (run_dir / "oof" / "oof_dummy_mean__sc1.json").exists()


def test_m54_05_02_e2e_cli_crash_recovery(tmp_path: Path) -> None:
    """C21: Ciclo de recuperação via expml run resume recupera execução interrompida (ORCH-28, AC 5)."""
    raw_csv = tmp_path / "raw.csv"
    raw_csv.write_text(
        "id,x1,x2,y\n"
        "1,1.0,10.0,2.0\n"
        "2,2.0,20.0,4.0\n"
        "3,3.0,30.0,6.0\n"
        "4,4.0,40.0,8.0\n"
        "5,5.0,50.0,10.0\n"
        "6,6.0,60.0,12.0\n",
        encoding="utf-8",
    )

    schema_file = tmp_path / "schema.json"
    schema_file.write_text(
        json.dumps({
            "target_col": "y",
            "observation_id_col": "id",
            "task_type": "REGRESSION",
            "column_semantic_types": {
                "x1": "NUMERIC_CONTINUOUS",
                "x2": "NUMERIC_CONTINUOUS",
                "y": "NUMERIC_CONTINUOUS",
            },
        }),
        encoding="utf-8",
    )

    exp_dir = tmp_path / "exp"
    _run_cli(["data", "profile", "--data", str(raw_csv), "--schema", str(schema_file), "--output-dir", str(exp_dir)])

    rules_file = tmp_path / "rules.json"
    rules_file.write_text("[]", encoding="utf-8")
    _run_cli(["data", "sanitize", "--experiment-dir", str(exp_dir), "--rules", str(rules_file)])

    part_file = tmp_path / "part.json"
    part_file.write_text(json.dumps({"strategy": "KFOLD", "regime": "CV_ONLY", "n_splits": 2, "master_seed": 42}), encoding="utf-8")
    _run_cli(["partition", "build", "--experiment-dir", str(exp_dir), "--config", str(part_file)])

    scenarios_file = tmp_path / "scenarios.json"
    scenarios_file.write_text(
        json.dumps([{
            "scenario_id": "sc1", "name": "SC1", "description": "D", "scientific_justification": "J",
            "mode": "FIXED", "selected_features": ["x1"],
        }]),
        encoding="utf-8",
    )
    _run_cli(["features", "scenarios", "--experiment-dir", str(exp_dir), "--scenarios", str(scenarios_file)])

    models_file = tmp_path / "models.json"
    models_file.write_text(
        json.dumps({"models": [{
            "model_id": "dummy_mean", "display_name": "Dummy", "family": "BASELINE",
            "estimator_factory": "DUMMY_BASELINE_MEAN", "capabilities": {"requires_fit": True},
            "description": "D", "scientific_justification": "J",
        }]}),
        encoding="utf-8",
    )
    _run_cli(["models", "validate", "--experiment-dir", str(exp_dir), "--models", str(models_file)])

    # 1. Run start to create initial state
    p_start = _run_cli(["run", "start", "--experiment-dir", str(exp_dir)])
    assert p_start.returncode == 0

    run_dir = exp_dir / "runs"
    state_file = run_dir / "execution_state.json"
    state_dict = json.loads(state_file.read_text(encoding="utf-8"))

    # Simulate crash / partial state: mark a cell as FAILED and remove its prediction file
    first_cid = next(iter(state_dict["cell_statuses"].keys()))
    state_dict["cell_statuses"][first_cid] = "FAILED"
    state_dict["completed_cells"] -= 1
    state_dict["failed_cells"] += 1
    state_file.write_text(json.dumps(state_dict), encoding="utf-8")

    pred_file = run_dir / "predictions" / f"pred_{first_cid}.json"
    if pred_file.exists():
        pred_file.unlink()

    # 2. Check status reflects the failure
    p_status = _run_cli(["run", "status", "--run-dir", str(run_dir)])
    assert p_status.returncode == 0
    assert "Failed: 1" in p_status.stdout

    # 3. Resume with --retry-failed
    p_resume = _run_cli([
        "run", "resume",
        "--run-dir", str(run_dir),
        "--retry-failed",
    ])
    assert p_resume.returncode == 0, f"resume failed: {p_resume.stderr}"
    assert "Failed cells: 0" in p_resume.stdout

    # 4. Verify gate succeeds on resumed run
    p_verify = _run_cli(["run", "verify", "--run-dir", str(run_dir)])
    assert p_verify.returncode == 0, f"verify failed: {p_verify.stderr}"
    assert "Status: READY" in p_verify.stdout


def test_m54_05_03_cli_runtime_purity_xcut_02() -> None:
    """C22: Pureza estrita de runtime: apenas biblioteca padrão e numpy>=1.24.0 (XCUT-02, CLI-10)."""
    # 1. Verify module-level imports of main and cmd_run do NOT import numpy or heavy packages (CLI-10)
    code_cli10 = (
        "import sys\n"
        "import experimental_ml.cli.main\n"
        "import experimental_ml.cli.cmd_run\n"
        "forbidden = ['numpy', 'scipy', 'pandas', 'sklearn', 'torch', 'qiskit', 'pyarrow']\n"
        "loaded = [p for p in forbidden if p in sys.modules]\n"
        "assert not loaded, f'Forbidden modules loaded at CLI module level: {loaded}'\n"
        "print('CLI-10 purity verified!')\n"
    )
    p_cli10 = subprocess.run([sys.executable, "-c", code_cli10], capture_output=True, text=True)
    assert p_cli10.returncode == 0, f"CLI-10 purity check failed: {p_cli10.stderr}"

    # 2. Verify runtime execution purity: only standard library and numpy loaded (XCUT-02)
    code_xcut02 = (
        "import sys\n"
        "from experimental_ml.cli.main import build_parser\n"
        "import experimental_ml.orchestration\n"
        "forbidden = ['scipy', 'pandas', 'sklearn', 'torch', 'qiskit', 'pyarrow']\n"
        "loaded = [p for p in forbidden if p in sys.modules]\n"
        "assert not loaded, f'Forbidden modules loaded in runtime: {loaded}'\n"
        "print('XCUT-02 purity verified!')\n"
    )
    p_xcut02 = subprocess.run([sys.executable, "-c", code_xcut02], capture_output=True, text=True)
    assert p_xcut02.returncode == 0, f"XCUT-02 purity check failed: {p_xcut02.stderr}"
