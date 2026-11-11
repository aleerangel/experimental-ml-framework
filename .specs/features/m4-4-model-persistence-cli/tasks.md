# m4-4-model-persistence-cli Tasks (M4.4 Persistência de Modelos, Portão de Validação e CLI)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m4-4-model-persistence-cli/design.md`  
**Status**: Approved  
**Approved**: 2026-11-11 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/models/ tests/unit/stages/ tests/unit/cli/ -v  
**Run integration**: .venv/bin/pytest tests/integration/models/ -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001` a `AD-007`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 7 requirements (`MPC-01` to `MPC-07`) and transversal invariants (`STORE-03`, `STORE-05`, `CLI-10`, `XCUT-02`).

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Models Catalog & Codecs (`src/experimental_ml/models/catalog.py`) | unit | 1:1 AC mapping: ModelsCatalog dataclass, to_dict, from_dict serialization roundtrip | `tests/unit/models/test_models_codecs.py` | `.venv/bin/pytest tests/unit/models/test_models_codecs.py -v` |
| Factory Resolution (`src/experimental_ml/models/catalog.py`) | unit | 1:1 AC mapping: built-in baselines, dotted path module:qualname, invalid resolution | `tests/unit/models/test_models_resolution.py` | `.venv/bin/pytest tests/unit/models/test_models_resolution.py -v` |
| Atomic Storage (`src/experimental_ml/models/storage.py`) | unit | 1:1 AC mapping: atomic write with tmp file, overwrite protection, loading from disk | `tests/unit/models/test_models_storage.py` | `.venv/bin/pytest tests/unit/models/test_models_storage.py -v` |
| Models Stage Gate (`src/experimental_ml/stages/stage_gates.py`) | unit | 1:1 AC mapping: verify_models_gate precondition checks, missing file, empty catalog | `tests/unit/stages/test_models_stage_gate.py` | `.venv/bin/pytest tests/unit/stages/test_models_stage_gate.py -v` |
| CLI models validate (`src/experimental_ml/cli/cmd_models.py`) | unit | 1:1 AC mapping: expml models validate handler, overwrite error, invalid input file | `tests/unit/cli/test_cli_models_validate.py` | `.venv/bin/pytest tests/unit/cli/test_cli_models_validate.py -v` |
| CLI models verify (`src/experimental_ml/cli/cmd_models.py`) | unit | 1:1 AC mapping: expml models verify handler, stage gate pass, gate failure | `tests/unit/cli/test_cli_models_verify.py` | `.venv/bin/pytest tests/unit/cli/test_cli_models_verify.py -v` |
| CLI Integration & Purity (`tests/integration/models/test_models_cli_integration.py`) | integration | Full CLI subprocess execution, zero module-level heavy imports in cmd_models (CLI-10) | `tests/integration/models/test_models_cli_integration.py` | `.venv/bin/pytest tests/integration/models/test_models_cli_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After tasks with unit tests | `.venv/bin/pytest tests/unit/models/ tests/unit/stages/ tests/unit/cli/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Models Catalog Data Model, Codecs and Factory Resolution (`P1`)

Define the immutable `ModelsCatalog` specification, dictionary codecs for JSON serialization, and deterministic estimator factory resolution for native baselines and custom import paths (`MPC-01`, `MPC-02`).

```
T1 --> T2
```

### Phase 2: Atomic Storage and Stage Gate Verification (`P2`)

Implement atomic persistence and loading functions (`save_models_catalog`, `load_models_catalog`) and the Stage 3 transition gate (`verify_models_gate`) in `stages` (`MPC-03`, `MPC-04`).

```
T3 --> T4
```

### Phase 3: CLI Subcommands Implementation (`P3`)

Implement the CLI command handlers for `expml models validate` and `expml models verify` in `cmd_models.py` with standardized error trapping and exit codes (`MPC-05`, `MPC-06`).

```
T5 --> T6
```

### Phase 4: CLI Registration, Import Purity and End-to-End Suite (`P4`)

Register the `models` subparsers in `main.py`, verify runtime import purity (`CLI-10`), and implement end-to-end integration tests (`MPC-07`).

```
T7
```

---

## Task Breakdown

### Phase 1: Models Catalog Data Model, Codecs and Factory Resolution (`P1`)

#### T1: Implement ModelsCatalog dataclass and JSON codecs

**What**: Create `src/experimental_ml/models/catalog.py` defining `ModelsCatalog` as an immutable frozen dataclass with slots containing `models: tuple[ModelSpec, ...]`, `metadata: MappingProxyType[str, Any]`, and `catalog_hash: str`. Implement serialization functions `model_spec_to_dict`, `model_spec_from_dict`, `models_catalog_to_dict`, and `models_catalog_from_dict` supporting capabilities, parameters, and optional preprocessing/tuning specs. Add co-located unit tests in `tests/unit/models/test_models_codecs.py`.
**Where**: `src/experimental_ml/models/catalog.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/models/spec.py`, `src/experimental_ml/models/types.py`, `src/experimental_ml/core/hashing.py`
**Requirement**: MPC-01

**Done when**:
- [x] `ModelsCatalog` defined with `frozen=True` and `slots=True`
- [x] `models_catalog_to_dict` and `models_catalog_from_dict` provide lossless roundtrip
- [x] Model capabilities and optional preprocessing/search specs correctly serialized
- [x] Unit tests pass in `tests/unit/models/test_models_codecs.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_models_codecs.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(models): implementar dataclass de catalogo e codecs json (MPC-01)`

---

#### T2: Implement resolve_estimator_factory for baselines and custom paths

**What**: In `src/experimental_ml/models/catalog.py`, implement `resolve_estimator_factory(factory_ref: str | Callable) -> Callable`. Support canonical baseline identifiers (`DUMMY_BASELINE_MEAN`, `DUMMY_BASELINE_MEDIAN`, `DUMMY_BASELINE_MOST_FREQUENT`, `ANALYTICAL_BIOMETRIC`), returning their respective factory functions. Support import strings in `module:qualname` format using `importlib.import_module`. Raise `ConfigurationError` if the string cannot be resolved or does not point to a callable. Add co-located unit tests in `tests/unit/models/test_models_resolution.py`.
**Where**: `src/experimental_ml/models/catalog.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/models/baselines.py`, `src/experimental_ml/core/findings.py`
**Requirement**: MPC-02

**Done when**:
- [x] Built-in baseline identifiers resolve to valid estimator factories
- [x] Import strings in `module:qualname` format resolve to valid callables
- [x] Invalid module, attribute, or non-callable references raise `ConfigurationError`
- [x] Unit tests pass in `tests/unit/models/test_models_resolution.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_models_resolution.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(models): implementar resolucao declarativa de fabricas de estimadores (MPC-02)`

---

### Phase 2: Atomic Storage and Stage Gate Verification (`P2`)

#### T3: Implement save_models_catalog and load_models_catalog with atomic persistence

**What**: Create `src/experimental_ml/models/storage.py` implementing `save_models_catalog(catalog: ModelsCatalog, path: Path | str, overwrite: bool = False) -> Path` and `load_models_catalog(path: Path | str) -> ModelsCatalog`. Validate that target destination does not exist if `overwrite=False`, raising `ConfigurationError`. Use `write_json_atomic` for safe disk writes. When loading, read JSON, reconstruct catalog via `models_catalog_from_dict`, and compute `catalog_hash`. Add co-located unit tests in `tests/unit/models/test_models_storage.py`.
**Where**: `src/experimental_ml/models/storage.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/models/catalog.py`, `src/experimental_ml/core/storage.py`, `src/experimental_ml/core/findings.py`
**Requirement**: MPC-03

**Done when**:
- [ ] `save_models_catalog` writes catalog atomically to disk
- [ ] Existing destination without overwrite raises `ConfigurationError`
- [ ] `load_models_catalog` reads and reconstructs catalog with matching hash
- [ ] Unit tests pass in `tests/unit/models/test_models_storage.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_models_storage.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(models): implementar persistencia atomica e carregamento de catalogo (MPC-03)`

---

#### T4: Implement verify_models_gate in stage_gates

**What**: In `src/experimental_ml/stages/stage_gates.py`, define `MODELS_CATALOG_REL_PATH = "configuration/models.json"` and implement `verify_models_gate(target: Path | str) -> ModelsCatalog`. If `target` is an experiment directory, verify preparation gate preconditions via `verify_preparation_gate(target)`. Verify that `configuration/models.json` exists (raising `DataIntegrityError` if absent) and load via `load_models_catalog`. Validate that catalog contains at least one model and enforce model ID uniqueness via `validate_models_catalog`. Export in `stages/__init__.py`. Add co-located unit tests in `tests/unit/stages/test_models_stage_gate.py`.
**Where**: `src/experimental_ml/stages/stage_gates.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/models/storage.py`, `src/experimental_ml/models/spec.py`, `src/experimental_ml/stages/stage_gates.py`
**Requirement**: MPC-04

**Done when**:
- [ ] `verify_models_gate` verifies preparation gate precondition
- [ ] Missing `models.json` raises `DataIntegrityError`
- [ ] Empty catalog or duplicate model IDs raise `ContractViolationError`
- [ ] Unit tests pass in `tests/unit/stages/test_models_stage_gate.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/stages/test_models_stage_gate.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stages): implementar portao de validacao de estagio para modelos (MPC-04)`

---

### Phase 3: CLI Subcommands Implementation (`P3`)

#### T5: Implement expml models validate subcommand

**What**: Create `src/experimental_ml/cli/cmd_models.py` implementing `handle_models_validate(args: argparse.Namespace) -> int`. Validate that `experiment_dir` exists. Load models input JSON from `args.models`, convert to `ModelsCatalog`, and save atomically to `experiment_dir / MODELS_CATALOG_REL_PATH` with overwrite check governed by `args.force`. Print structured summary to stdout. Handle domain errors with code 2 and success with code 0. Add co-located unit tests in `tests/unit/cli/test_cli_models_validate.py`.
**Where**: `src/experimental_ml/cli/cmd_models.py`
**Depends on**: T4
**Reuses**: `src/experimental_ml/models/catalog.py`, `src/experimental_ml/models/storage.py`, `src/experimental_ml/core/findings.py`
**Requirement**: MPC-05

**Done when**:
- [ ] `handle_models_validate` validates and saves `configuration/models.json`
- [ ] Existing `models.json` without `--force` raises error and returns code 2
- [ ] Missing models input file or invalid data returns code 2
- [ ] Unit tests pass in `tests/unit/cli/test_cli_models_validate.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/cli/test_cli_models_validate.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(cli): implementar subcomando expml models validate (MPC-05)`

---

#### T6: Implement expml models verify subcommand

**What**: In `src/experimental_ml/cli/cmd_models.py`, implement `handle_models_verify(args: argparse.Namespace) -> int`. Validate that `experiment_dir` exists. Call `verify_models_gate(experiment_dir)`. Print gate verification summary to stdout. Return 0 on success, return 2 on domain or validation error. Add co-located unit tests in `tests/unit/cli/test_cli_models_verify.py`.
**Where**: `src/experimental_ml/cli/cmd_models.py`
**Depends on**: T5
**Reuses**: `src/experimental_ml/stages/stage_gates.py`, `src/experimental_ml/core/findings.py`
**Requirement**: MPC-06

**Done when**:
- [ ] `handle_models_verify` successfully verifies valid models stage gate and returns code 0
- [ ] Missing artifacts or failed preconditions print error and return code 2
- [ ] Missing experiment directory returns code 2
- [ ] Unit tests pass in `tests/unit/cli/test_cli_models_verify.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/cli/test_cli_models_verify.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(cli): implementar subcomando expml models verify (MPC-06)`

---

### Phase 4: CLI Registration, Import Purity and End-to-End Suite (`P4`)

#### T7: Register models CLI subparsers, enforce import purity and implement end-to-end suite

**What**: In `src/experimental_ml/cli/main.py`, register the `models` command and subparsers `validate` and `verify`. Dispatch to `handle_models_validate` and `handle_models_verify`. In `src/experimental_ml/models/__init__.py`, export `ModelsCatalog`, `save_models_catalog`, `load_models_catalog`. In `tests/integration/models/test_models_cli_integration.py`, implement subprocess-based integration tests verifying `expml models validate` and `verify` end-to-end lifecycle, and assert import purity in `cmd_models.py` (`CLI-10`).
**Where**: `src/experimental_ml/cli/main.py`
**Depends on**: T6
**Reuses**: `src/experimental_ml/cli/cmd_models.py`, `src/experimental_ml/models/catalog.py`
**Requirement**: MPC-07

**Done when**:
- [ ] `main.py` registers `models` subparser with `validate` and `verify` commands
- [ ] `cmd_models.py` maintains zero file-level heavy imports (`CLI-10`)
- [ ] Subprocess integration tests execute full CLI lifecycle with exit codes 0 and 2
- [ ] Integration tests pass in `tests/integration/models/test_models_cli_integration.py`
- [ ] Full gate check passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(cli): registrar subparser de models e implementar suite de integracao (MPC-07)`

---

## Checks

**Run unit**: .venv/bin/pytest tests/unit/models/ tests/unit/stages/ tests/unit/cli/ -v  
**Run integration**: .venv/bin/pytest tests/integration/models/ -v  

**C1** - `ModelsCatalog` is defined as an immutable frozen dataclass with slots (`MPC-01`, AC 1)  
Proof: run unit | tests/unit/models/test_models_codecs.py::test_m44_01_01_models_catalog_dataclass PASSED

**C2** - `models_catalog_to_dict` serializes models, capabilities, and parameters to JSON dict (`MPC-01`, AC 2)  
Proof: run unit | tests/unit/models/test_models_codecs.py::test_m44_01_02_models_catalog_to_dict PASSED

**C3** - `models_catalog_from_dict` reconstructs immutable `ModelsCatalog` from dictionary (`MPC-01`, AC 3)  
Proof: run unit | tests/unit/models/test_models_codecs.py::test_m44_01_03_models_catalog_from_dict PASSED

**C4** - `resolve_estimator_factory` resolves canonical baseline identifiers (`MPC-02`, AC 1)  
Proof: run unit | tests/unit/models/test_models_resolution.py::test_m44_02_01_resolve_builtin_baselines PASSED

**C5** - `resolve_estimator_factory` resolves import strings in module:qualname format (`MPC-02`, AC 2)  
Proof: run unit | tests/unit/models/test_models_resolution.py::test_m44_02_02_resolve_dotted_import_path PASSED

**C6** - `resolve_estimator_factory` raises `ConfigurationError` on unresolvable references (`MPC-02`, AC 3)  
Proof: run unit | tests/unit/models/test_models_resolution.py::test_m44_02_03_resolve_invalid_reference_raises PASSED

**C7** - `save_models_catalog` writes catalog atomically and `load_models_catalog` restores it (`MPC-03`, AC 1, 3)  
Proof: run unit | tests/unit/models/test_models_storage.py::test_m44_03_01_save_and_load_roundtrip PASSED

**C8** - `save_models_catalog` raises `ConfigurationError` on existing file when overwrite=False (`MPC-03`, AC 2)  
Proof: run unit | tests/unit/models/test_models_storage.py::test_m44_03_02_save_overwrite_guard PASSED

**C9** - `load_models_catalog` raises `ConfigurationError` on missing or corrupt file (`MPC-03`, AC 3)  
Proof: run unit | tests/unit/models/test_models_storage.py::test_m44_03_03_load_missing_or_corrupt PASSED

**C10** - `verify_models_gate` verifies models gate when artifacts are valid (`MPC-04`, AC 1)  
Proof: run unit | tests/unit/stages/test_models_stage_gate.py::test_m44_04_01_verify_models_gate_valid PASSED

**C11** - `verify_models_gate` raises error when models.json is missing or catalog is empty (`MPC-04`, AC 2)  
Proof: run unit | tests/unit/stages/test_models_stage_gate.py::test_m44_04_02_verify_models_gate_missing_or_empty PASSED

**C12** - `verify_models_gate` raises `ContractViolationError` when preparation gate is not READY (`MPC-04`, AC 3)  
Proof: run unit | tests/unit/stages/test_models_stage_gate.py::test_m44_04_03_verify_models_gate_unmet_precondition PASSED

**C13** - `handle_models_validate` validates and saves models.json with exit code 0 (`MPC-05`, AC 1)  
Proof: run unit | tests/unit/cli/test_cli_models_validate.py::test_m44_05_01_models_validate_success PASSED

**C14** - `handle_models_validate` returns exit code 2 when destination exists and --force omitted (`MPC-05`, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_models_validate.py::test_m44_05_02_models_validate_overwrite_error PASSED

**C15** - `handle_models_validate` returns exit code 2 when models input file is missing or invalid (`MPC-05`, AC 3)  
Proof: run unit | tests/unit/cli/test_cli_models_validate.py::test_m44_05_03_models_validate_invalid_input PASSED

**C16** - `handle_models_verify` verifies models gate and returns exit code 0 (`MPC-06`, AC 1)  
Proof: run unit | tests/unit/cli/test_cli_models_verify.py::test_m44_06_01_models_verify_success PASSED

**C17** - `handle_models_verify` returns exit code 2 when models gate fails (`MPC-06`, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_models_verify.py::test_m44_06_02_models_verify_gate_failure PASSED

**C18** - `handle_models_verify` returns exit code 2 when experiment directory is missing (`MPC-06`, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_models_verify.py::test_m44_06_03_models_verify_missing_dir PASSED

**C19** - `main.py` registers `models` subparser with `validate` and `verify` commands (`MPC-07`, AC 1)  
Proof: run integration | tests/integration/models/test_models_cli_integration.py::test_m44_07_01_cli_parser_registration PASSED

**C20** - `cmd_models.py` maintains zero module-level heavy imports (CLI-10) (`MPC-07`, AC 1)  
Proof: run integration | tests/integration/models/test_models_cli_integration.py::test_m44_07_02_cli_import_purity PASSED

**C21** - Subprocess execution validates full CLI lifecycle for models validate and verify (`MPC-07`, AC 2)  
Proof: run integration | tests/integration/models/test_models_cli_integration.py::test_m44_07_03_e2e_cli_subprocess PASSED

---

## Handoff

**Settled mid-build**: none  
**Dispatched**: none  
**Walked**: pending  

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1 → T2
Phase 2:  T3 → T4
Phase 3:  T5 → T6
Phase 4:  T7
```

---

## Granularity Verification Checklist

| Task | Core Responsibility | Verdict |
| :--- | :--- | :--- |
| T1: Implement ModelsCatalog dataclass and JSON codecs | ModelsCatalog model, dictionary serialization and deserialization | ✅ Granular |
| T2: Implement resolve_estimator_factory for baselines and custom paths | Factory resolution for built-in baselines and dotted imports | ✅ Granular |
| T3: Implement save_models_catalog and load_models_catalog with atomic persistence | Atomic disk persistence with tmp file and catalog loading | ✅ Granular |
| T4: Implement verify_models_gate in stage_gates | Stage 3 transition gate validation with precondition checking | ✅ Granular |
| T5: Implement expml models validate subcommand | CLI handler for validating and saving models.json | ✅ Granular |
| T6: Implement expml models verify subcommand | CLI handler for verifying models stage gate | ✅ Granular |
| T7: Register models CLI subparsers, enforce import purity and implement end-to-end suite | CLI parser registration, import purity (CLI-10) and e2e integration | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| :--- | :--- | :--- | :--- |
| T1 | None | Phase 1 root (`T1`) | ✅ Match |
| T2 | T1 | Phase 1 continuation (`T1 --> T2`) | ✅ Match |
| T3 | T2 | Phase 2 start (`T2 --> T3`) | ✅ Match |
| T4 | T3 | Phase 2 continuation (`T3 --> T4`) | ✅ Match |
| T5 | T4 | Phase 3 start (`T4 --> T5`) | ✅ Match |
| T6 | T5 | Phase 3 continuation (`T5 --> T6`) | ✅ Match |
| T7 | T6 | Phase 4 start (`T6 --> T7`) | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| :--- | :--- | :--- | :--- | :--- |
| T1: Implement ModelsCatalog dataclass and JSON codecs | Models Catalog & Codecs (`src/experimental_ml/models/catalog.py`) | unit | unit | ✅ OK |
| T2: Implement resolve_estimator_factory for baselines and custom paths | Factory Resolution (`src/experimental_ml/models/catalog.py`) | unit | unit | ✅ OK |
| T3: Implement save_models_catalog and load_models_catalog with atomic persistence | Atomic Storage (`src/experimental_ml/models/storage.py`) | unit | unit | ✅ OK |
| T4: Implement verify_models_gate in stage_gates | Models Stage Gate (`src/experimental_ml/stages/stage_gates.py`) | unit | unit | ✅ OK |
| T5: Implement expml models validate subcommand | CLI models validate (`src/experimental_ml/cli/cmd_models.py`) | unit | unit | ✅ OK |
| T6: Implement expml models verify subcommand | CLI models verify (`src/experimental_ml/cli/cmd_models.py`) | unit | unit | ✅ OK |
| T7: Register models CLI subparsers, enforce import purity and implement end-to-end suite | CLI Integration & Purity (`tests/integration/models/test_models_cli_integration.py`) | integration | integration | ✅ OK |
