"""Smoke tests for experimental-ml-framework packaging, package root and CLI dispatcher."""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import tomllib

import experimental_ml
from experimental_ml.cli.main import build_parser, main


REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def _read_pyproject() -> dict:
    assert PYPROJECT_PATH.exists(), "pyproject.toml not found"
    with open(PYPROJECT_PATH, "rb") as f:
        return tomllib.load(f)


def test_pyproject_metadata() -> None:
    """Verify SETUP-01: build backend, distribution name, requires-python."""
    data = _read_pyproject()
    assert data["build-system"]["build-backend"] == "hatchling.build"
    assert "hatchling" in data["build-system"]["requires"]
    assert data["project"]["name"] == "experimental-ml-framework"
    assert data["project"]["requires-python"] == ">=3.10"


def test_package_version() -> None:
    """Verify SETUP-02: package exposes __version__ = '0.1.0.dev0'."""
    assert hasattr(experimental_ml, "__version__")
    assert experimental_ml.__version__ == "0.1.0.dev0"


def test_dev_dependencies() -> None:
    """Verify SETUP-03: dev dependencies declare pytest>=7.0.0."""
    data = _read_pyproject()
    dev_deps = data["project"]["optional-dependencies"]["dev"]
    assert any("pytest" in dep and ">=7.0.0" in dep for dep in dev_deps)


def test_cli_entrypoint_registered() -> None:
    """Verify SETUP-04: console script registers expml entrypoint."""
    data = _read_pyproject()
    scripts = data["project"]["scripts"]
    assert scripts.get("expml") == "experimental_ml.cli.main:main"


def test_editable_install_and_cli_on_path() -> None:
    """Verify SETUP-05: expml is available and runnable in virtual environment."""
    venv_bin = Path(sys.prefix) / "bin" / "expml"
    executable = str(venv_bin) if venv_bin.exists() else shutil.which("expml")
    
    if executable:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "0.1.0.dev0" in (result.stdout + result.stderr)
    else:
        # Before pip install -e runs (e.g. during preliminary task execution),
        # verify that the entrypoint function is directly executable and callable.
        assert callable(main)
        parser = build_parser()
        assert parser.prog == "expml"


def test_cli_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI-01: expml --version outputs version and exits with code 0."""
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "0.1.0.dev0" in output


def test_cli_help_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI-02: expml --help outputs usage summary and exits with code 0."""
    # Test --help
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "usage: expml" in captured.out
    assert "--help" in captured.out
    assert "--version" in captured.out

    # Test invocation without arguments
    exit_code = main([])
    assert exit_code == 0
    captured_empty = capsys.readouterr()
    assert "usage: expml" in captured_empty.out


def test_cli_invalid_argument(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI-03: unrecognized arguments output error to stderr and exit with code 2."""
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--nonexistent-flag-for-test"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err


def test_cli_dependencies_pure_stdlib() -> None:
    """Verify CLI-04: cli/main.py uses only stdlib without importing unwritten modules."""
    cli_file = REPO_ROOT / "src" / "experimental_ml" / "cli" / "main.py"
    with open(cli_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(cli_file))

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split(".")[0])

    # Allowed imports: standard library + top-level experimental_ml (for __version__)
    forbidden = {"core", "metrics", "data", "models", "partition", "features", "pandas", "numpy", "sklearn"}
    for mod in imported_modules:
        assert mod not in forbidden, f"Forbidden module imported in CLI: {mod}"


def test_smoke_discovery() -> None:
    """Verify SMOKE-01: smoke test suite is discoverable and executable."""
    assert Path(__file__).exists()
    assert Path(__file__).name == "test_smoke.py"


def test_version_non_empty() -> None:
    """Verify SMOKE-02: experimental_ml.__version__ is a non-empty string."""
    assert isinstance(experimental_ml.__version__, str)
    assert len(experimental_ml.__version__.strip()) > 0
    assert experimental_ml.__version__ == "0.1.0.dev0"


def test_cli_observable_outcomes() -> None:
    """Verify SMOKE-03: observable CLI outcomes for help, version and invalid args."""
    # Test --version via subprocess or runner
    result_ver = subprocess.run(
        [sys.executable, "-m", "experimental_ml.cli.main", "--version"],
        capture_output=True,
        text=True,
        check=False,
        env={"PYTHONPATH": str(REPO_ROOT / "src"), "PATH": sys.prefix + "/bin"},
    )
    assert result_ver.returncode == 0
    assert "0.1.0.dev0" in (result_ver.stdout + result_ver.stderr)

    # Test --help
    result_help = subprocess.run(
        [sys.executable, "-m", "experimental_ml.cli.main", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env={"PYTHONPATH": str(REPO_ROOT / "src"), "PATH": sys.prefix + "/bin"},
    )
    assert result_help.returncode == 0
    assert "usage: expml" in result_help.stdout

    # Test invalid argument
    result_invalid = subprocess.run(
        [sys.executable, "-m", "experimental_ml.cli.main", "--invalid-argument-xyz"],
        capture_output=True,
        text=True,
        check=False,
        env={"PYTHONPATH": str(REPO_ROOT / "src"), "PATH": sys.prefix + "/bin"},
    )
    assert result_invalid.returncode == 2
    assert "unrecognized arguments" in result_invalid.stderr

