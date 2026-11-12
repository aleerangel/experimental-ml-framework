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
