# m1-1-setup-cli-smoke Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: none - change is straightforward setup/smoke CLI
**Status**: Approved
**Approved**: 2026-10-31 - user: "A fase TASKS da feature m1-1-setup-cli-smoke está aprovada."
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates
**Run smoke**: `.venv/bin/pytest tests/test_smoke.py -v`

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied; Python packaging and CLI smoke test according to spec ACs.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Packaging / Configuration (`pyproject.toml`) | none | - (build gate only: valid TOML, hatchling build configuration) | `pyproject.toml` | build gate only |
| Package Initialization (`src/experimental_ml/`) | none | - (build gate only: package metadata exposure) | `src/experimental_ml/__init__.py` | build gate only |
| CLI Base Entrypoint (`src/experimental_ml/cli/`) | none | Isolated CLI logic; covered by integration smoke suite | `src/experimental_ml/cli/main.py` | quick gate only |
| Smoke Suite & CLI Integration (`tests/`) | integration | 1:1 AC mapping: import, version, CLI invocation and observable exit codes | `tests/test_smoke.py` | `.venv/bin/pytest tests/test_smoke.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After packaging, layout or single-file CLI edits | `.venv/bin/python -m py_compile src/experimental_ml/__init__.py src/experimental_ml/cli/main.py` |
| Full | After tasks with CLI smoke tests or installation verification | `.venv/bin/pytest tests/test_smoke.py -v` |
| Build | After phase completion or config-only tasks | `.venv/bin/pytest tests/test_smoke.py -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Foundation & Packaging

Initial configuration of build system, project metadata, and package root layout.

```
T1 → T2
```

### Phase 2: CLI Implementation & Smoke Verification

Implementation of CLI entrypoint, automated smoke test suite, and editable installation verification.

```
T3 → T4 → T5
```

---

## Task Breakdown

### Phase 1: Foundation & Packaging

#### T1: Configure pyproject.toml packaging metadata, dev dependencies and entrypoint

**What**: Create project `pyproject.toml` specifying Hatchling backend, metadata, optional `dev` dependencies and `expml` console script entrypoint.
**Where**: `pyproject.toml`
**Depends on**: None
**Reuses**: None
**Requirement**: SETUP-01, SETUP-03, SETUP-04

**Done when**:
- [x] `pyproject.toml` defines `[build-system]` with `requires = ["hatchling"]` and `build-backend = "hatchling.build"`
- [x] `[project]` defines `name = "experimental-ml-framework"`, `version = "0.1.0.dev0"`, and declared `requires-python = ">=3.10"`
- [x] `[project.optional-dependencies]` declares `dev = ["pytest>=7.0.0"]`
- [x] `[project.scripts]` declares `expml = "experimental_ml.cli.main:main"`
- [x] Gate check passes: `.venv/bin/python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"`

**Tests**: none
**Gate**: quick

---

#### T2: Create package root __init__.py exposing package version

**What**: Initialize source layout directory and top-level `__init__.py` exposing `__version__`.
**Where**: `src/experimental_ml/__init__.py`
**Depends on**: T1
**Reuses**: None
**Requirement**: SETUP-02

**Done when**:
- [x] `src/experimental_ml/__init__.py` created
- [x] Exposes `__version__ = "0.1.0.dev0"`
- [x] Defines `__all__ = ["__version__"]`
- [x] Gate check passes: `.venv/bin/python -c "import sys; sys.path.insert(0, 'src'); import experimental_ml; assert experimental_ml.__version__ == '0.1.0.dev0'"`

**Tests**: none
**Gate**: quick

---

### Phase 2: CLI Implementation & Smoke Verification

#### T3: Implement standalone CLI dispatcher using argparse

**What**: Implement CLI main entrypoint supporting `--version`, `--help` (`-h`), and exit code 2 for invalid arguments using only standard library modules.
**Where**: `src/experimental_ml/cli/main.py`
**Depends on**: T2
**Reuses**: None
**Requirement**: CLI-01, CLI-02, CLI-03, CLI-04

**Done when**:
- [x] `src/experimental_ml/cli/main.py` created with `build_parser()` and `main(argv=None)` entrypoint
- [x] `--version` prints version string and exits with code 0
- [x] `--help` / `-h` prints usage message and exits with code 0
- [x] Unrecognized arguments exit with code 2 and write error message to stderr
- [x] No imports of unwritten modules (`core`, `metrics`, `data`)
- [x] Gate check passes: `.venv/bin/python -m py_compile src/experimental_ml/cli/main.py`

**Tests**: none
**Gate**: quick

---

#### T4: Implement smoke test suite asserting package and CLI observable outcomes

**What**: Create comprehensive automated smoke tests in `tests/test_smoke.py` asserting package import, version attribute, and observable CLI outcomes.
**Where**: `tests/test_smoke.py`
**Depends on**: T3
**Reuses**: None
**Requirement**: SMOKE-01, SMOKE-02, SMOKE-03

**Done when**:
- [x] `tests/test_smoke.py` created with unit and integration tests covering ACs
- [x] Tests assert package import and non-empty `__version__ == "0.1.0.dev0"`
- [x] Tests assert `expml` CLI invocation for `--help` (exit 0), `--version` (exit 0), and invalid argument (exit 2)
- [x] Tests assert that `experimental_ml.cli.main` does not import unwritten modules
- [x] Gate check passes: `.venv/bin/pytest tests/test_smoke.py -v`
- [x] Test count: 12 tests pass

**Tests**: integration
**Gate**: full

---

#### T5: Perform editable installation and verify console script on PATH

**What**: Install package in virtual environment with `pip install -e ".[dev]"` and verify `expml` console script is executable directly on PATH.
**Where**: `pyproject.toml`
**Depends on**: T4
**Reuses**: None
**Requirement**: SETUP-05

**Done when**:
- [x] `.venv/bin/pip install -e ".[dev]"` completes with exit code 0
- [x] `.venv/bin/expml --version` executes directly on PATH with exit code 0
- [x] `.venv/bin/expml --help` executes directly on PATH with exit code 0
- [x] Gate check passes: `.venv/bin/expml --version && .venv/bin/pytest tests/test_smoke.py -v`

**Tests**: integration
**Gate**: full

---

## Checks

**C1** - Packaging configuration defines hatchling.build, experimental-ml-framework distribution name, and requires-python >= 3.10 (SETUP-01, AC 1)
Proof: run smoke | test_pyproject_metadata PASSED

**C2** - Source code layout rooted at src/experimental_ml/ exposes __version__ = "0.1.0.dev0" (SETUP-02, AC 2)
Proof: run smoke | test_package_version PASSED

**C3** - Optional development dependency group dev contains pytest>=7.0.0 (SETUP-03, AC 3)
Proof: run smoke | test_dev_dependencies PASSED

**C4** - Console script entrypoint registers expml = "experimental_ml.cli.main:main" (SETUP-04, AC 4)
Proof: run smoke | test_cli_entrypoint_registered PASSED

**C5** - Package installs in editable mode via pip install -e ".[dev]" and expml is executable on PATH (SETUP-05, AC 5)
Proof: run smoke | test_editable_install_and_cli_on_path PASSED

**C6** - Executing expml --version outputs declared package version and exits with code 0 (CLI-01, AC 1)
Proof: run smoke | test_cli_version_flag PASSED

**C7** - Executing expml --help outputs usage summary and exits with code 0 (CLI-02, AC 2)
Proof: run smoke | test_cli_help_flag PASSED

**C8** - Executing expml with invalid argument outputs error to stderr and exits with code 2 (CLI-03, AC 3)
Proof: run smoke | test_cli_invalid_argument PASSED

**C9** - CLI entrypoint uses only Python standard library without importing unwritten modules (CLI-04, AC 4)
Proof: run smoke | test_cli_dependencies_pure_stdlib PASSED

**C10** - Automated smoke tests in tests/test_smoke.py are discovered and executed by pytest (SMOKE-01, AC 1)
Proof: run smoke | test_smoke_discovery PASSED

**C11** - Pytest verifies that experimental_ml.__version__ is a non-empty string (SMOKE-02, AC 2)
Proof: run smoke | test_version_non_empty PASSED

**C12** - Pytest asserts observable CLI outcomes for --help, --version, and invalid arguments (SMOKE-03, AC 3)
Proof: run smoke | test_cli_observable_outcomes PASSED

---

## Handoff

The feature's live state, written as it happens - a compaction gives no warning.

**Settled mid-build:** none
**Dispatched:** none
**Walked:** T1, T2, T3, T4, T5 completed. All 12 checks passed in check_proofs.py and pytest. Ready for final review.

---

## Phase Execution Map

Visual representation of task ordering. Phases run in sequence, and tasks within a phase run in order:

```
Phase 1: Foundation & Packaging
  T1 (pyproject.toml) -> T2 (src/experimental_ml/__init__.py)

Phase 2: CLI Implementation & Smoke Verification
  T3 (src/experimental_ml/cli/main.py) -> T4 (tests/test_smoke.py) -> T5 (pyproject.toml)
```
