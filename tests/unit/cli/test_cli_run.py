"""Unit tests for 'expml run' command handlers and argument parsing.

Complies with CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11, ORCH-22 to ORCH-27.
Checks C1 through C19.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pytest

from experimental_ml.cli.main import build_parser, main


# ==============================================================================
# Phase 1: T1 - Parsing and CLI Dispatcher Tests (C1 to C5)
# ==============================================================================


def test_m54_01_01_cli_run_help_and_subparsers(capsys: pytest.CaptureFixture[str]) -> None:
    """C1: Ponto de entrada expõe subparser run com start, resume, status e verify."""
    # 1. Main help mentions 'run'
    code_help = main(["--help"])
    captured = capsys.readouterr()
    assert code_help == 0
    assert "run" in captured.out

    # 2. 'run --help' lists all 4 subcommands
    code_run_help = main(["run", "--help"])
    captured_run = capsys.readouterr()
    assert code_run_help == 0
    assert "start" in captured_run.out
    assert "resume" in captured_run.out
    assert "status" in captured_run.out
    assert "verify" in captured_run.out

    # 3. 'run' without subcommand exits with code 2
    code_no_sub = main(["run"])
    captured_no_sub = capsys.readouterr()
    assert code_no_sub == 2
    assert "subcommand required for 'run'" in captured_no_sub.err


def test_m54_01_02_run_start_args_parsing() -> None:
    """C2: Subparser run start valida argumentos obrigatórios e opcionais."""
    parser = build_parser()

    # 1. Valid arguments with short and long flags
    args = parser.parse_args([
        "run", "start",
        "--experiment-dir", "/tmp/exp_test",
        "--run-dir", "/tmp/custom_runs",
        "-j", "4",
        "--error-policy", "fail_fast",
        "--no-oof",
        "--force",
    ])
    assert args.command == "run"
    assert args.subcommand == "start"
    assert args.experiment_dir == "/tmp/exp_test"
    assert args.run_dir == "/tmp/custom_runs"
    assert args.parallel == 4
    assert args.error_policy == "fail_fast"
    assert args.no_oof is True
    assert args.force is True

    # 2. Defaults
    args_defaults = parser.parse_args([
        "run", "start",
        "--experiment-dir", "/tmp/exp_default",
    ])
    assert args_defaults.run_dir is None
    assert args_defaults.parallel == 1
    assert args_defaults.error_policy == "fault_tolerant"
    assert args_defaults.no_oof is False
    assert args_defaults.force is False

    # 3. Missing required --experiment-dir
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["run", "start"])
    assert exc_info.value.code == 2


def test_m54_01_03_run_resume_args_parsing() -> None:
    """C3: Subparser run resume valida argumentos obrigatórios e opcionais."""
    parser = build_parser()

    # 1. Valid arguments
    args = parser.parse_args([
        "run", "resume",
        "--run-dir", "/tmp/resume_runs",
        "--experiment-dir", "/tmp/exp_opt",
        "--jobs", "2",
        "--retry-failed",
        "--no-oof",
    ])
    assert args.command == "run"
    assert args.subcommand == "resume"
    assert args.run_dir == "/tmp/resume_runs"
    assert args.experiment_dir == "/tmp/exp_opt"
    assert args.parallel == 2
    assert args.retry_failed is True
    assert args.no_oof is True

    # 2. Defaults
    args_defaults = parser.parse_args([
        "run", "resume",
        "--run-dir", "/tmp/resume_runs",
    ])
    assert args_defaults.experiment_dir is None
    assert args_defaults.parallel == 1
    assert args_defaults.retry_failed is False
    assert args_defaults.no_oof is False

    # 3. Missing required --run-dir
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["run", "resume"])
    assert exc_info.value.code == 2


def test_m54_01_04_run_status_args_parsing() -> None:
    """C4: Subparser run status valida argumentos obrigatórios."""
    parser = build_parser()

    # 1. Valid arguments
    args = parser.parse_args(["run", "status", "--run-dir", "/tmp/status_runs"])
    assert args.command == "run"
    assert args.subcommand == "status"
    assert args.run_dir == "/tmp/status_runs"

    # 2. Missing required --run-dir
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["run", "status"])
    assert exc_info.value.code == 2


def test_m54_01_05_run_verify_args_parsing() -> None:
    """C5: Subparser run verify valida argumentos obrigatórios."""
    parser = build_parser()

    # 1. Valid arguments
    args = parser.parse_args(["run", "verify", "--run-dir", "/tmp/verify_runs"])
    assert args.command == "run"
    assert args.subcommand == "verify"
    assert args.run_dir == "/tmp/verify_runs"

    # 2. Missing required --run-dir
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["run", "verify"])
    assert exc_info.value.code == 2


# ==============================================================================
# Helper: Setup fully prepared experiment (Stages 1, 2, 3, 4A)
# ==============================================================================


def _setup_fully_prepared_experiment(tmp_path: Path) -> Path:
    """Helper that creates an experiment directory with Stages 1, 2, 3, 4A completed."""
    import json
    exp_dir = tmp_path / "exp"
    raw_csv = tmp_path / "raw_data.csv"
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
    schema_dict = {
        "target_col": "y",
        "observation_id_col": "id",
        "task_type": "REGRESSION",
        "column_semantic_types": {
            "x1": "NUMERIC_CONTINUOUS",
            "x2": "NUMERIC_CONTINUOUS",
            "y": "NUMERIC_CONTINUOUS",
        },
    }
    schema_file.write_text(json.dumps(schema_dict), encoding="utf-8")

    # Step 1: data profile
    code = main([
        "data", "profile",
        "--data", str(raw_csv),
        "--schema", str(schema_file),
        "--output-dir", str(exp_dir),
    ])
    assert code == 0

    # Step 2: data sanitize
    rules_file = tmp_path / "rules.json"
    rules_file.write_text("[]", encoding="utf-8")
    code = main([
        "data", "sanitize",
        "--experiment-dir", str(exp_dir),
        "--rules", str(rules_file),
    ])
    assert code == 0

    # Step 3: partition build (3 folds)
    part_file = tmp_path / "partition_config.json"
    part_dict = {
        "strategy": "KFOLD",
        "regime": "CV_ONLY",
        "n_splits": 3,
        "master_seed": 42,
    }
    part_file.write_text(json.dumps(part_dict), encoding="utf-8")
    code = main([
        "partition", "build",
        "--experiment-dir", str(exp_dir),
        "--config", str(part_file),
    ])
    assert code == 0

    # Step 4: features scenarios
    scenarios_file = tmp_path / "scenarios.json"
    scenarios_list = [
        {
            "scenario_id": "sc_baseline",
            "name": "Baseline",
            "description": "Baseline",
            "scientific_justification": "Baseline",
            "mode": "FIXED",
            "selected_features": ["x1"],
        }
    ]
    scenarios_file.write_text(json.dumps(scenarios_list), encoding="utf-8")
    code = main([
        "features", "scenarios",
        "--experiment-dir", str(exp_dir),
        "--scenarios", str(scenarios_file),
    ])
    assert code == 0

    # Step 5: models validate
    models_file = tmp_path / "models.json"
    models_dict = {
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
    models_file.write_text(json.dumps(models_dict), encoding="utf-8")
    code = main([
        "models", "validate",
        "--experiment-dir", str(exp_dir),
        "--models", str(models_file),
    ])
    assert code == 0

    return exp_dir


# ==============================================================================
# Phase 2: T2 - expml run start Tests (C6 to C11)
# ==============================================================================


def test_m54_02_01_run_start_default_execution(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C6: expml run start executa matriz completa e consolida OOF em runs (ORCH-23, AC 1, AC 5)."""
    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    capsys.readouterr()

    code = main(["run", "start", "--experiment-dir", str(exp_dir)])
    captured = capsys.readouterr()

    # 1. Exit code 0
    assert code == 0
    assert "Experiment matrix execution completed" in captured.out
    assert "Total cells: 3" in captured.out
    assert "Completed cells: 3" in captured.out

    # 2. Artifacts created in <exp_dir>/runs
    run_dir = exp_dir / "runs"
    assert (run_dir / "execution_state.json").exists()
    assert len(list((run_dir / "cells").glob("*.json"))) == 3
    assert len(list((run_dir / "predictions").glob("*.json"))) == 3
    assert (run_dir / "oof" / "oof_dummy_mean__sc_baseline.json").exists()


def test_m54_02_02_run_start_custom_run_dir(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C7: expml run start com --run-dir customizado grava artefatos no diretório indicado (ORCH-23, AC 2)."""
    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    custom_run = tmp_path / "custom_execution_dir"
    capsys.readouterr()

    code = main([
        "run", "start",
        "--experiment-dir", str(exp_dir),
        "--run-dir", str(custom_run),
    ])
    assert code == 0

    assert (custom_run / "execution_state.json").exists()
    assert (custom_run / "oof" / "oof_dummy_mean__sc_baseline.json").exists()


def test_m54_02_03_run_start_parallel_dispatch(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C8: expml run start com -j N despacha execução em paralelo (ORCH-23, AC 3)."""
    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    capsys.readouterr()

    code = main([
        "run", "start",
        "--experiment-dir", str(exp_dir),
        "-j", "2",
    ])
    assert code == 0
    assert (exp_dir / "runs" / "execution_state.json").exists()


def test_m54_02_04_run_start_fail_fast(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C9: expml run start com --error-policy fail_fast interrompe após primeira falha (ORCH-23, AC 4)."""
    import json
    exp_dir = _setup_fully_prepared_experiment(tmp_path)

    # Invalidate model factory to trigger cell execution failure
    models_path = exp_dir / "configuration" / "models.json"
    models_dict = json.loads(models_path.read_text(encoding="utf-8"))
    models_dict["models"][0]["estimator_factory"] = "non_existent_module:dummy_class"
    models_path.write_text(json.dumps(models_dict), encoding="utf-8")
    capsys.readouterr()

    code = main([
        "run", "start",
        "--experiment-dir", str(exp_dir),
        "--error-policy", "fail_fast",
    ])
    captured = capsys.readouterr()
    assert code in (1, 2)
    assert "fail_fast" in captured.err.lower() or "error" in captured.err.lower()


def test_m54_02_05_run_start_no_oof(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C10: expml run start com --no-oof desativa consolidação out-of-fold (ORCH-23, AC 6)."""
    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    capsys.readouterr()

    code = main([
        "run", "start",
        "--experiment-dir", str(exp_dir),
        "--no-oof",
    ])
    assert code == 0

    run_dir = exp_dir / "runs"
    assert (run_dir / "execution_state.json").exists()
    assert not (run_dir / "oof").exists()


def test_m54_02_06_run_start_overwrite_protection(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C11: expml run start recusa sobrescrita de execução existente sem --force (ORCH-23, AC 7)."""
    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    capsys.readouterr()

    # 1. First execution succeeds
    code1 = main(["run", "start", "--experiment-dir", str(exp_dir)])
    assert code1 == 0

    # 2. Second execution without --force fails with code 2
    code2 = main(["run", "start", "--experiment-dir", str(exp_dir)])
    captured2 = capsys.readouterr()
    assert code2 == 2
    assert "already contains execution_state.json" in captured2.err
    assert "--force" in captured2.err

    # 3. Third execution with --force succeeds
    code3 = main(["run", "start", "--experiment-dir", str(exp_dir), "--force"])
    assert code3 == 0


# ==============================================================================
# Phase 3: T3 - expml run resume and status Tests (C12 to C15)
# ==============================================================================


def test_m54_03_01_run_resume_skips_completed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C12: expml run resume pula células concluídas e reexecuta pendentes (ORCH-24, AC 1)."""
    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    capsys.readouterr()

    # 1. Run start to completion
    code_start = main(["run", "start", "--experiment-dir", str(exp_dir)])
    assert code_start == 0

    run_dir = exp_dir / "runs"
    mtimes_before = {p: p.stat().st_mtime_ns for p in (run_dir / "cells").glob("*.json")}
    capsys.readouterr()

    # 2. Run resume with no pending cells
    code_resume = main(["run", "resume", "--run-dir", str(run_dir)])
    captured_resume = capsys.readouterr()

    assert code_resume == 0
    assert "Experiment matrix execution resumed and completed" in captured_resume.out
    assert "Completed cells: 3" in captured_resume.out

    # 3. Existing completed cell artifacts should not have been overwritten
    mtimes_after = {p: p.stat().st_mtime_ns for p in (run_dir / "cells").glob("*.json")}
    assert mtimes_before == mtimes_after


def test_m54_03_02_run_resume_retry_failed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C13: expml run resume com --retry-failed reexecuta células falhas (ORCH-24, AC 2)."""
    import json
    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    capsys.readouterr()

    # 1. Run start
    code_start = main(["run", "start", "--experiment-dir", str(exp_dir)])
    assert code_start == 0

    run_dir = exp_dir / "runs"
    state_file = run_dir / "execution_state.json"
    state_dict = json.loads(state_file.read_text(encoding="utf-8"))

    # Mark first cell as FAILED in state
    first_cid = next(iter(state_dict["cell_statuses"].keys()))
    state_dict["cell_statuses"][first_cid] = "FAILED"
    state_dict["failed_cells"] = 1
    state_dict["completed_cells"] = 2
    state_file.write_text(json.dumps(state_dict), encoding="utf-8")
    capsys.readouterr()

    # 2. Resume with --retry-failed
    code_resume = main([
        "run", "resume",
        "--run-dir", str(run_dir),
        "--retry-failed",
    ])
    captured = capsys.readouterr()

    assert code_resume == 0
    assert "Completed cells: 3" in captured.out
    assert "Failed cells: 0" in captured.out


def test_m54_03_03_run_status_read_only(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C14: expml run status realiza leitura puramente somente-leitura e exibe progresso (ORCH-25, AC 1)."""
    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    code_start = main(["run", "start", "--experiment-dir", str(exp_dir)])
    assert code_start == 0

    run_dir = exp_dir / "runs"
    state_file = run_dir / "execution_state.json"
    mtime_before = state_file.stat().st_mtime_ns
    capsys.readouterr()

    code_status = main(["run", "status", "--run-dir", str(run_dir)])
    captured = capsys.readouterr()

    assert code_status == 0
    assert "Experiment execution status:" in captured.out
    assert "Total cells: 3" in captured.out
    assert "Completed: 3 (100.0%)" in captured.out
    assert "Failed: 0" in captured.out
    assert "Pending: 0" in captured.out

    # Purely read-only: state file mtime unchanged
    mtime_after = state_file.stat().st_mtime_ns
    assert mtime_before == mtime_after


def test_m54_03_04_run_status_missing_state_returns_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C15: expml run status com diretório inválido ou sem estado retorna código 2 (ORCH-25, AC 2)."""
    empty_dir = tmp_path / "empty_run"
    empty_dir.mkdir()
    capsys.readouterr()

    code = main(["run", "status", "--run-dir", str(empty_dir)])
    captured = capsys.readouterr()

    assert code == 2
    assert "Error:" in captured.err
    assert "execution_state.json" in captured.err
    assert "Traceback" not in captured.err


# ==============================================================================
# Phase 4: T4 - expml run verify and Error Handling Tests (C16 to C19)
# ==============================================================================


def test_m54_04_01_run_verify_valid_gate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C16: expml run verify audita execução e retorna status READY com código 0 (ORCH-26, AC 1)."""
    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    code_start = main(["run", "start", "--experiment-dir", str(exp_dir)])
    assert code_start == 0

    run_dir = exp_dir / "runs"
    capsys.readouterr()

    code_verify = main(["run", "verify", "--run-dir", str(run_dir)])
    captured = capsys.readouterr()

    assert code_verify == 0
    assert "Stage 4 execution gate verified successfully:" in captured.out
    assert "Status: READY" in captured.out
    assert "Total cells: 3" in captured.out
    assert "Completed cells: 3" in captured.out
    assert "Verified configurations: 1" in captured.out


def test_m54_04_02_run_verify_corrupted_gate_returns_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C17: expml run verify com execução incompleta ou corrompida retorna código 2 (ORCH-26, AC 2)."""
    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    code_start = main(["run", "start", "--experiment-dir", str(exp_dir)])
    assert code_start == 0

    run_dir = exp_dir / "runs"

    # Delete OOF artifact to simulate corruption / missing artifact
    oof_file = run_dir / "oof" / "oof_dummy_mean__sc_baseline.json"
    oof_file.unlink()
    capsys.readouterr()

    code_verify = main(["run", "verify", "--run-dir", str(run_dir)])
    captured = capsys.readouterr()

    assert code_verify == 2
    assert "Error:" in captured.err
    assert "Traceback" not in captured.err


def test_m54_04_03_domain_errors_exit_code_2_no_traceback(capsys: pytest.CaptureFixture[str]) -> None:
    """C18: Erros de domínio e precondições são emitidos sem traceback com código 2 (ORCH-27, AC 1)."""
    capsys.readouterr()

    code = main(["run", "start", "--experiment-dir", "/non_existent_dir_12345"])
    captured = capsys.readouterr()

    assert code == 2
    assert "Error:" in captured.err
    assert "Traceback" not in captured.err


def test_m54_04_04_hash_suppression_cli_11(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C19: Resumos da CLI emitem textos limpos com supressão de hashes criptográficos (ORCH-27, AC 4)."""
    import re
    sha256_pattern = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)

    exp_dir = _setup_fully_prepared_experiment(tmp_path)
    run_dir = exp_dir / "runs"
    capsys.readouterr()

    # 1. run start
    main(["run", "start", "--experiment-dir", str(exp_dir)])
    out_start = capsys.readouterr().out
    assert not sha256_pattern.search(out_start), f"Hash leak in run start output: {out_start}"

    # 2. run status
    main(["run", "status", "--run-dir", str(run_dir)])
    out_status = capsys.readouterr().out
    assert not sha256_pattern.search(out_status), f"Hash leak in run status output: {out_status}"

    # 3. run resume
    main(["run", "resume", "--run-dir", str(run_dir)])
    out_resume = capsys.readouterr().out
    assert not sha256_pattern.search(out_resume), f"Hash leak in run resume output: {out_resume}"

    # 4. run verify
    main(["run", "verify", "--run-dir", str(run_dir)])
    out_verify = capsys.readouterr().out
    assert not sha256_pattern.search(out_verify), f"Hash leak in run verify output: {out_verify}"
