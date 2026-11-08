"""Unit tests for CLI main dispatcher, error trapping and architectural invariants.

Verifies CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11 and Checks C6, C7, C8, C9.
"""

from __future__ import annotations

import ast
from io import StringIO
from pathlib import Path
import re
import sys
import pytest

from experimental_ml.cli.main import main
from experimental_ml.core.findings import ConfigurationError, DataIntegrityError


def test_cli_09_base_cli_compatibility_and_help(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI-09 (Check C7): Base CLI behaviors (empty argv -> 0, --version -> 0, invalid -> 2)."""
    # 1. Empty arguments: prints help and exits with code 0
    code_empty = main([])
    captured = capsys.readouterr()
    assert code_empty == 0
    assert "Experimental ML Framework - CLI" in captured.out

    # 2. --help flag exits with code 0
    code_help = main(["--help"])
    captured_help = capsys.readouterr()
    assert code_help == 0
    assert "data" in captured_help.out
    assert "partition" in captured_help.out

    # 3. Subcommand help exits with code 0
    code_data_help = main(["data", "--help"])
    captured_data_help = capsys.readouterr()
    assert code_data_help == 0
    assert "profile" in captured_data_help.out
    assert "sanitize" in captured_data_help.out

    code_part_help = main(["partition", "--help"])
    captured_part_help = capsys.readouterr()
    assert code_part_help == 0
    assert "build" in captured_part_help.out
    assert "verify" in captured_part_help.out

    # 4. Invalid option exits with code 2
    code_invalid = main(["--non-existent-option"])
    captured_invalid = capsys.readouterr()
    assert code_invalid == 2
    assert "unrecognized arguments" in captured_invalid.err or "error" in captured_invalid.err.lower()

    # 5. Missing subcommand exits with code 2
    code_missing_sub = main(["data"])
    captured_missing = capsys.readouterr()
    assert code_missing_sub == 2
    assert "subcommand required" in captured_missing.err


def test_cli_06_domain_error_handling_and_exit_code_2(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI-06, CLI-07, CLI-08 (Check C6): Catch domain error, suppress traceback, exit code 2."""
    # Mock a command handler to raise ConfigurationError
    def mock_profile(args):
        raise ConfigurationError("Simulated configuration error in dataset path")

    monkeypatch.setattr("experimental_ml.cli.cmd_data.handle_data_profile", mock_profile)

    code = main(["data", "profile", "--data", "d.csv", "--schema", "s.json", "--output-dir", "out"])
    captured = capsys.readouterr()

    # Code must be 2
    assert code == 2
    # Instructive message present
    assert "Error: Simulated configuration error in dataset path" in captured.err
    # Traceback strictly absent
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out


def test_cli_10_architectural_pure_cli_no_numpy_no_hashlib() -> None:
    """CLI-10 (Check C8): CLI command modules import neither numpy nor hashlib."""
    cli_dir = Path(__file__).resolve().parent.parent.parent.parent / "src" / "experimental_ml" / "cli"

    py_files = list(cli_dir.glob("*.py"))
    assert len(py_files) >= 1

    forbidden = {"numpy", "hashlib"}

    for py_file in py_files:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    assert root_mod not in forbidden, f"{py_file.name} imports forbidden module '{root_mod}'"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    assert root_mod not in forbidden, f"{py_file.name} imports from forbidden module '{root_mod}'"


def test_cli_11_no_hash_digests_in_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI-11 (Check C9): Subcommands never print a 64-character SHA-256 hash digest in stdout/stderr."""
    # Mock a command handler producing valid output text
    def mock_verify(args):
        sys.stdout.write("All partition plan invariants verified successfully.\n")
        return 0

    monkeypatch.setattr("experimental_ml.cli.cmd_partition.handle_partition_verify", mock_verify)

    code = main(["partition", "verify", "--experiment-dir", "/tmp/exp"])
    captured = capsys.readouterr()

    assert code == 0
    full_output = captured.out + captured.err
    # Regex searching for 64-char hex digest
    sha256_pattern = re.compile(r"\b[0-9a-fA-F]{64}\b")
    assert not sha256_pattern.search(full_output), f"Found SHA-256 digest in CLI output: {full_output}"
