# m2-4-artifacts-stage-gates Tasks (M2.4 Artifacts Persistence & Stage Gates)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m2-4-artifacts-stage-gates/design.md`
**Status**: Approved
**Approved**: 2026-11-07 - user: "aprovado"
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates
**Run unit**: .venv/bin/pytest tests/unit/core/test_storage.py tests/unit/data/test_codecs.py tests/unit/validation/test_splits_storage.py tests/unit/stages/test_stage_gates.py -v
**Run integration**: .venv/bin/pytest tests/integration/test_artifacts_stage_gates_integration.py -v

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001`, `AD-002`, `AD-003`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 7 requirements (`STORE-01` to `STORE-07`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Core Atomic Storage (`src/experimental_ml/core/storage.py`) | unit | 1:1 AC mapping: atomic replacement via tempfile, cleanup on error, overwrite protection (ConfigurationError) | `tests/unit/core/test_storage.py` | `.venv/bin/pytest tests/unit/core/test_storage.py -v` |
| Data Descriptors & Codecs (`src/experimental_ml/data/descriptors.py`, `codecs.py`) | unit | 1:1 AC mapping: lossless round-trip, no NaN/Infinity, immutability, slots | `tests/unit/data/test_codecs.py` | `.venv/bin/pytest tests/unit/data/test_codecs.py -v` |
| Validation Codecs & Splits Storage (`src/experimental_ml/validation/codecs.py`, `storage.py`) | unit | 1:1 AC mapping: deterministic gzip bytes, plan serialization, schema metadata | `tests/unit/validation/test_splits_storage.py` | `.venv/bin/pytest tests/unit/validation/test_splits_storage.py -v` |
| Stage Gates & Integrity Verification (`src/experimental_ml/stages/stage_gates.py`) | unit | 1:1 AC mapping: stage layout, incomplete plan rejection (ContractViolationError), hash divergence & tampering (DataIntegrityError) | `tests/unit/stages/test_stage_gates.py` | `.venv/bin/pytest tests/unit/stages/test_stage_gates.py -v` |
| Stage Gates Integration & Invariants (`tests/integration/test_artifacts_stage_gates_integration.py`) | integration | End-to-end pipeline artifact persistence, cross-stage verification, import isolation | `tests/integration/test_artifacts_stage_gates_integration.py` | `.venv/bin/pytest tests/integration/test_artifacts_stage_gates_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After tasks with unit tests | `.venv/bin/pytest tests/unit/core/test_storage.py tests/unit/data/test_codecs.py tests/unit/validation/test_splits_storage.py tests/unit/stages/test_stage_gates.py -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Core Atomic Storage & Overwrite Protection (`P1.1`)

Implement atomic JSON storage with tempfile replacement, failure cleanup, and overwrite rejection.

```
T1
```

### Phase 2: Data & Validation Codecs & Splits Storage (`P1.2`)

Implement lossless bidirectional codecs for data and validation objects, and deterministic splits.csv.gz writer.

```
T2 → T3
```

### Phase 3: Stage Gates & Inter-Stage Verification (`P1.3`)

Implement stage gate validators checking experiment layout, preparation readiness, cryptographic hash linkages, and partition consistency.

```
T4
```

### Phase 4: Public Exports & Integration Suite (`P1.4`)

Expose public functions, verify end-to-end artifact creation and validation, and verify architectural import isolation.

```
T5
```

---

## Task Breakdown

### Phase 1: Core Atomic Storage & Overwrite Protection (`P1.1`)

#### T1: Implement `write_json_atomic` and `read_json` in `core/storage.py`

**What**: Create `src/experimental_ml/core/storage.py` implementing `write_json_atomic(path, payload, *, overwrite=False, indent=2)` and `read_json(path)`. Ensure target existence check raising `ConfigurationError` when `overwrite=False` (STORE-07). Write to `NamedTemporaryFile` in target's directory, flush and `os.fsync`, rename via `os.replace`. Catch exceptions, unlink temp file silently, leaving target intact (STORE-01). Add unit tests in `tests/unit/core/test_storage.py`.
**Where**: `src/experimental_ml/core/storage.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/findings.py` (`ConfigurationError`)
**Requirement**: STORE-01, STORE-07

**Done when**:
- [x] `write_json_atomic` writes valid UTF-8 JSON atomically via tempfile and `os.replace`
- [x] Target pre-existence raises `ConfigurationError` when `overwrite=False`
- [x] Write or serialization failure deletes temporary file without polluting or corrupting target path
- [x] `read_json` decodes stored documents accurately
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/core/test_storage.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(core): implementar escrita atomica de json e protecao de sobrescrita`

---

### Phase 2: Data & Validation Codecs & Splits Storage (`P1.2`)

#### T2: Implement Data descriptors and codecs in `data/descriptors.py` and `data/codecs.py`

**What**: Create `src/experimental_ml/data/descriptors.py` defining `DatasetDescriptor` and `SanitizedViewDescriptor` (frozen dataclasses with slots). Create `src/experimental_ml/data/codecs.py` with `to_dict` and `from_dict` functions for `DatasetDescriptor`, `SanitizedViewDescriptor`, `DatasetProfile`, and `PreparationPlan`. Guarantee lossless conversions without `NaN` or `Infinity` (STORE-02). Add unit tests in `tests/unit/data/test_codecs.py`.
**Where**: `src/experimental_ml/data/codecs.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/data/types.py`, `src/experimental_ml/data/profiling.py`, `src/experimental_ml/data/preparation.py`
**Requirement**: STORE-02, STORE-03

**Done when**:
- [x] `DatasetDescriptor` and `SanitizedViewDescriptor` defined with frozen slots
- [x] Lossless bidirectional codecs round-trip without information loss
- [x] Codecs reject or serialize floating NaNs as `None` in conformity with RFC 8259
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/data/test_codecs.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(data): implementar descritores e codecs de perfil e saneamento`

---

#### T3: Implement Validation codecs and deterministic `splits.csv.gz` writer in `validation/`

**What**: Create `src/experimental_ml/validation/codecs.py` with `partition_plan_to_dict` and `partition_plan_from_dict`. Create `src/experimental_ml/validation/storage.py` implementing `write_splits_csv_gz(path, plan, *, overwrite=False)` with deterministic `gzip.GzipFile(mtime=0.0)`, `read_splits_csv_gz`, and `write_splits_schema` (STORE-04). Add unit tests in `tests/unit/validation/test_splits_storage.py`.
**Where**: `src/experimental_ml/validation/storage.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/validation/types.py`, `src/experimental_ml/core/storage.py`
**Requirement**: STORE-02, STORE-04

**Done when**:
- [x] `partition_plan_to_dict` / `from_dict` provides lossless round-trip
- [x] `write_splits_csv_gz` produces bit-identical gzip files across repeated calls
- [x] Correct mapping of observation IDs to fold roles (`TRAIN`, `VAL`) and holdout (`DEVELOPMENT`, `HOLDOUT`)
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/validation/test_splits_storage.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(validation): implementar codecs de particao e gravador deterministico de splits`

---

### Phase 3: Stage Gates & Inter-Stage Verification (`P1.3`)

#### T4: Implement `verify_preparation_gate` and `verify_partition_gate` in `stages/stage_gates.py`

**What**: Create `src/experimental_ml/stages/stage_gates.py` implementing stage gate verifications for experiment directory layout (`data/`, `configuration/`, `partitions/`). Implement `verify_preparation_gate(experiment_dir)` raising `ContractViolationError` if `preparation_plan.json` is missing or not `READY`, and `DataIntegrityError` if dataset hashes diverge. Implement `verify_partition_gate(experiment_dir)` checking linkage to `sanitized_view.json` and verifying that `splits.csv.gz` strictly matches `partition_plan.json` (STORE-05, STORE-06). Add unit tests in `tests/unit/stages/test_stage_gates.py`.
**Where**: `src/experimental_ml/stages/stage_gates.py`
**Depends on**: T2, T3
**Reuses**: `src/experimental_ml/core/findings.py`, `src/experimental_ml/core/storage.py`, `src/experimental_ml/data/codecs.py`, `src/experimental_ml/validation/storage.py`
**Requirement**: STORE-03, STORE-05, STORE-06

**Done when**:
- [x] Experiment directory layout verified against ARQUITETURA §5 and D11
- [x] Incomplete preparation plans raise `ContractViolationError`
- [x] Hash divergences between descriptor, profile, view, and plan raise `DataIntegrityError`
- [x] Contradictions between `splits.csv.gz` and `partition_plan.json` raise `DataIntegrityError`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/stages/test_stage_gates.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(stages): implementar portoes de verificacao de integridade entre etapas`

---

### Phase 4: Public Exports & Integration Suite (`P1.4`)

#### T5: Expose public symbols and implement end-to-end integration test suite

**What**: Expose storage, codecs, and stage gate functions in `experimental_ml.core`, `experimental_ml.data`, `experimental_ml.validation`, and `experimental_ml.stages`. Create `tests/integration/test_artifacts_stage_gates_integration.py` verifying full end-to-end execution (profiling -> plan -> sanitization -> partition -> stage verification), bit-identical reproducibility, tamper detection, and layer import isolation.
**Where**: `tests/integration/test_artifacts_stage_gates_integration.py`
**Depends on**: T4
**Reuses**: All sub-marco modules
**Requirement**: STORE-01 to STORE-07

**Done when**:
- [x] Public symbols exported from their respective packages
- [x] End-to-end integration test verifies the full artifact lifecycle and stage gate validation
- [x] Tamper detection verifies that modifying any artifact causes stage gate failure
- [x] Architectural import isolation confirmed (`core` does not import higher layers; `data` does not import `validation` or `stages`)
- [x] Full gate check passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration
**Gate**: full
**Commit**: `feat(stages): exportar simbolos publicos e suite integracao persistencia`

---

## Checks

The checks below verify every acceptance criterion (`STORE-01` to `STORE-07`). Each check settles an observable claim against its exact proof.

**C1** - `write_json_atomic` serializes payload to a temporary file in target directory, performs atomic replacement via `os.replace`, and leaves target absent/untouched on write failure (`STORE-01`, AC 1)
Proof: run unit | tests/unit/core/test_storage.py::test_store_01_atomic_write_and_failure_cleanup PASSED

**C2** - `to_dict` and `from_dict` provide lossless round-trip conversions for `DatasetProfile`, `PreparationPlan`, `PartitionPlan`, and stage descriptors, without `NaN` or `Infinity` (`STORE-02`, AC 2)
Proof: run unit | tests/unit/data/test_codecs.py::test_store_02_lossless_codecs_roundtrip PASSED

**C3** - Creation and validation of standard experiment directory layout containing descriptor, profile, preparation plan, sanitized view, partition plan, splits CSV, and splits schema (`STORE-03`, AC 3)
Proof: run integration | tests/integration/test_artifacts_stage_gates_integration.py::test_store_03_experiment_directory_layout PASSED

**C4** - `write_splits_csv_gz` produces gzip-compressed CSV mapping observation IDs to per-fold and holdout roles with bit-identical bytes across repeated writes (`STORE-04`, AC 4)
Proof: run unit | tests/unit/validation/test_splits_storage.py::test_store_04_splits_csv_gz_deterministic PASSED

**C5** - `verify_preparation_gate` and `verify_partition_gate` detect hash divergence raising `DataIntegrityError`, and reject missing or incomplete preparation plans raising `ContractViolationError` (`STORE-05`, AC 5)
Proof: run unit | tests/unit/stages/test_stage_gates.py::test_store_05_hash_divergence_and_incomplete_plan_rejection PASSED

**C6** - `verify_partition_gate` detects contradictions between `splits.csv.gz` and `partition_plan.json`, or tampered artifacts, raising `DataIntegrityError` (`STORE-06`, AC 6)
Proof: run unit | tests/unit/stages/test_stage_gates.py::test_store_06_splits_tampering_and_mismatch_rejection PASSED

**C7** - Rejection of write operations on pre-existing artifacts without `overwrite=True`, raising `ConfigurationError` (`STORE-07`, AC 7)
Proof: run unit | tests/unit/core/test_storage.py::test_store_07_overwrite_protection_configuration_error PASSED

---

## Handoff

**Settled mid-build**: none
**Dispatched**: Verifier (validate.md)
**Walked**: all tasks completed (T1-T5)
