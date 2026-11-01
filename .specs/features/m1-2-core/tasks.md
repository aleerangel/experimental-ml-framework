# m1-2-core Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: none - core contracts follow ADR-007 and ADR-008
**Status**: Approved
**Approved**: 2026-10-31 - user: "avança"
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates
**Run unit**: `.venv/bin/pytest tests/unit/test_core.py -v`

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied; core foundational types and algorithms according to spec ACs.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Packaging / Dependencies (`pyproject.toml`) | none | - (build gate only: valid TOML, dependencies declared) | `pyproject.toml` | quick gate only |
| Domain Types & Identifiers (`src/experimental_ml/core/types.py`) | unit | 1:1 AC mapping: all identifier constructors, whitespace stripping, rejection of empty/invalid strings | `tests/unit/test_core.py` | `.venv/bin/pytest tests/unit/test_core.py -v` |
| Fundamental Enums (`src/experimental_ml/core/enums.py`) | unit | 1:1 AC mapping: all enum members, string compatibility, native JSON serialization | `tests/unit/test_core.py` | `.venv/bin/pytest tests/unit/test_core.py -v` |
| Diagnostic Findings & Exceptions (`src/experimental_ml/core/findings.py`) | unit | 1:1 AC mapping: make_finding, make_warning, immutability, exception hierarchy | `tests/unit/test_core.py` | `.venv/bin/pytest tests/unit/test_core.py -v` |
| Seed Derivation (`src/experimental_ml/core/seeds.py`) | unit | 1:1 AC mapping: SeedSequence determinism, count validation, child seed spawning | `tests/unit/test_core.py` | `.venv/bin/pytest tests/unit/test_core.py -v` |
| Canonical & Dataset Hashing (`src/experimental_ml/core/hashing.py`) | unit | 1:1 AC mapping: ADR-007 canonical rules (NFC, key sorting, scalar/collection distinction, NaN/-0.0) and dataset hashing | `tests/unit/test_core.py` | `.venv/bin/pytest tests/unit/test_core.py -v` |
| Core Package Root (`src/experimental_ml/core/__init__.py`) | none | - (build gate only: public API re-export exposure) | `src/experimental_ml/core/__init__.py` | quick gate only |
| Unit Test Suite (`tests/unit/test_core.py`) | unit | 100% pass across all 18 core requirements | `tests/unit/test_core.py` | `.venv/bin/pytest tests/unit/test_core.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After single-file edits in core | `.venv/bin/python -m py_compile src/experimental_ml/core/*.py` |
| Full | After unit test suite or hashing implementation | `.venv/bin/pytest tests/unit/test_core.py -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Environment & Domain Foundation

Add NumPy dependency and implement fundamental domain types, enums and diagnostic findings.

```
T1 → T2 → T3 → T4
```

### Phase 2: Cryptographic Hashing, Random Seeds & Unit Verification

Implement hierarchical seed derivation, canonical hashing (ADR-007), package re-exports and comprehensive unit test suite.

```
T5 → T6 → T7 → T8
```

---

## Task Breakdown

### Phase 1: Environment & Domain Foundation

#### T1: Add numpy dependency to pyproject.toml and synchronize virtual environment

**What**: Update `pyproject.toml` to declare `numpy>=1.24.0` in `dependencies` and install into `.venv`.
**Where**: `pyproject.toml`
**Depends on**: None
**Reuses**: None
**Requirement**: CORE-07, CORE-10

**Done when**:
- [ ] `pyproject.toml` defines `dependencies = ["numpy>=1.24.0"]`
- [ ] Package is reinstalled in editable mode in `.venv` with `pip install -e ".[dev]"`
- [ ] Gate check passes: `.venv/bin/python -c "import numpy; print(numpy.__version__)"`

**Tests**: none
**Gate**: quick

---

#### T2: Implement domain identifier types and validation in src/experimental_ml/core/types.py

**What**: Create `src/experimental_ml/core/types.py` defining immutable domain identifier types (`ExperimentId`, `PartitionPlanId`, `ScenarioId`, `ModelId`, `CellId`, `ComparisonId`, `ArtifactId`, `ObservationId`) with strict whitespace stripping and non-empty validation.
**Where**: `src/experimental_ml/core/types.py`
**Depends on**: T1
**Reuses**: None
**Requirement**: CORE-01, CORE-02, CORE-03

**Done when**:
- [ ] `src/experimental_ml/core/types.py` created
- [ ] All 8 identifier types defined as immutable string subclasses
- [ ] Constructor validates non-empty strings and strips whitespace
- [ ] Rejects empty strings or non-string inputs with `ValueError`
- [ ] Gate check passes: `.venv/bin/python -m py_compile src/experimental_ml/core/types.py`

**Tests**: unit
**Gate**: quick

---

#### T3: Implement fundamental enums in src/experimental_ml/core/enums.py

**What**: Create `src/experimental_ml/core/enums.py` defining all domain enums (`TaskType`, `ExecutionStatus`, `FindingSeverity`, `MetricDirection`, `AggregationScope`, `MetricStatus`, `ErrorPolicy`) as string-compatible enums.
**Where**: `src/experimental_ml/core/enums.py`
**Depends on**: T2
**Reuses**: None
**Requirement**: CORE-04, CORE-05, CORE-06

**Done when**:
- [ ] `src/experimental_ml/core/enums.py` created
- [ ] Enums defined inheriting from `str, Enum`
- [ ] All specified members present with exact string values
- [ ] Supports direct equality with string literals and native JSON serialization
- [ ] Gate check passes: `.venv/bin/python -m py_compile src/experimental_ml/core/enums.py`

**Tests**: unit
**Gate**: quick

---

#### T4: Implement diagnostic findings and exceptions in src/experimental_ml/core/findings.py

**What**: Create `src/experimental_ml/core/findings.py` with immutable `Finding` structure, `make_finding` (`CONFIRMED_ISSUE`), `make_warning` (`HEURISTIC_WARNING`), and custom exceptions (`ContractViolationError`, `DataIntegrityError`, `ConfigurationError`).
**Where**: `src/experimental_ml/core/findings.py`
**Depends on**: T3
**Reuses**: None
**Requirement**: CORE-17, CORE-18

**Done when**:
- [ ] `src/experimental_ml/core/findings.py` created
- [ ] `Finding` defined as immutable dataclass/NamedTuple with severity, code, message, and context
- [ ] `make_finding` and `make_warning` constructors implemented
- [ ] `ContractViolationError`, `DataIntegrityError`, and `ConfigurationError` defined
- [ ] Gate check passes: `.venv/bin/python -m py_compile src/experimental_ml/core/findings.py`

**Tests**: unit
**Gate**: quick

---

### Phase 2: Cryptographic Hashing, Random Seeds & Unit Verification

#### T5: Implement hierarchical seed derivation in src/experimental_ml/core/seeds.py

**What**: Create `src/experimental_ml/core/seeds.py` implementing pure functions `derive_seeds` and `spawn_child_seeds` based on `numpy.random.SeedSequence`.
**Where**: `src/experimental_ml/core/seeds.py`
**Depends on**: T1
**Reuses**: None
**Requirement**: CORE-07, CORE-08, CORE-09

**Done when**:
- [ ] `src/experimental_ml/core/seeds.py` created
- [ ] `derive_seeds(master_seed, count)` returns deterministic tuple of integers
- [ ] `spawn_child_seeds(parent_seed, count)` returns independent child seed tuple
- [ ] Rejects `count < 1` with `ValueError`
- [ ] Gate check passes: `.venv/bin/python -m py_compile src/experimental_ml/core/seeds.py`

**Tests**: unit
**Gate**: quick

---

#### T6: Implement canonical config_hash and dataset_hash in src/experimental_ml/core/hashing.py

**What**: Create `src/experimental_ml/core/hashing.py` implementing canonical serialization and hashing (`config_hash` and `dataset_hash`) compliant with ADR-007.
**Where**: `src/experimental_ml/core/hashing.py`
**Depends on**: T5
**Reuses**: None
**Requirement**: CORE-10, CORE-11, CORE-12, CORE-13, CORE-14, CORE-15, CORE-16

**Done when**:
- [ ] `src/experimental_ml/core/hashing.py` created
- [ ] `config_hash(obj)` produces 64-char lowercase SHA-256 with Unicode NFC normalization
- [ ] Strict scalar distinction (`True != 1`, `1 != 1.0`), collection distinction (`tuple != list`), set ordering by item hash
- [ ] Special floats normalized (`-0.0 -> 0.0`, `NaN -> {"__float_special__": "NaN"}`)
- [ ] `dataset_hash` handles raw files (CSV/TXT) and in-memory tabular data with little-endian buffers
- [ ] Gate check passes: `.venv/bin/python -m py_compile src/experimental_ml/core/hashing.py`

**Tests**: unit
**Gate**: quick

---

#### T7: Expose core public API in src/experimental_ml/core/__init__.py

**What**: Create `src/experimental_ml/core/__init__.py` re-exporting all public types, enums, functions and exceptions in `__all__`.
**Where**: `src/experimental_ml/core/__init__.py`
**Depends on**: T6
**Reuses**: None
**Requirement**: CORE-01, CORE-04, CORE-07, CORE-10, CORE-17

**Done when**:
- [ ] `src/experimental_ml/core/__init__.py` created
- [ ] Re-exports all public identifiers, enums, functions, and exceptions
- [ ] `__all__` explicitly declared
- [ ] Gate check passes: `.venv/bin/python -c "import experimental_ml.core; print(dir(experimental_ml.core))"`

**Tests**: none
**Gate**: quick

---

#### T8: Implement comprehensive unit test suite in tests/unit/test_core.py

**What**: Create `tests/unit/test_core.py` with automated tests covering all 18 requirements across identifiers, enums, seeds, canonical hashing, dataset hashing, and findings.
**Where**: `tests/unit/test_core.py`
**Depends on**: T7
**Reuses**: None
**Requirement**: CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, CORE-06, CORE-07, CORE-08, CORE-09, CORE-10, CORE-11, CORE-12, CORE-13, CORE-14, CORE-15, CORE-16, CORE-17, CORE-18

**Done when**:
- [ ] `tests/unit/test_core.py` created
- [ ] All 18 checks C1..C18 mapped to test functions
- [ ] Test suite executes with 100% pass via pytest
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/test_core.py -v`

**Tests**: unit
**Gate**: full

---

## Checks

**C1** - Domain identifiers are immutable string types (CORE-01, AC 1)
Proof: run unit | test_identifier_types_immutable PASSED

**C2** - Identifier constructors validate non-empty and stripped strings (CORE-02, AC 2)
Proof: run unit | test_identifier_validation_non_empty PASSED

**C3** - Empty or invalid identifiers raise ValueError (CORE-03, AC 3)
Proof: run unit | test_identifier_invalid_value_error PASSED

**C4** - TaskType and ExecutionStatus define exact specified canonical members (CORE-04, AC 1-2)
Proof: run unit | test_task_type_and_execution_status_enums PASSED

**C5** - FindingSeverity, MetricDirection, and AggregationScope define exact members (CORE-05, AC 3-5)
Proof: run unit | test_finding_metric_aggregation_enums PASSED

**C6** - MetricStatus and ErrorPolicy define exact members and serialize to JSON (CORE-06, AC 6-8)
Proof: run unit | test_metric_status_and_error_policy_enums PASSED

**C7** - Function derive_seeds produces tuple of integers via SeedSequence (CORE-07, AC 1)
Proof: run unit | test_derive_seeds_returns_tuple PASSED

**C8** - Same master seed produces identical seed tuple deterministically (CORE-08, AC 2-3)
Proof: run unit | test_derive_seeds_determinism PASSED

**C9** - Function spawn_child_seeds derives independent seeds and rejects count < 1 (CORE-09, AC 4-5)
Proof: run unit | test_spawn_child_seeds_validation PASSED

**C10** - Function config_hash returns 64-character lowercase hexadecimal SHA-256 (CORE-10, AC 1)
Proof: run unit | test_config_hash_sha256_format PASSED

**C11** - Function config_hash normalizes Unicode NFC and sorts mapping keys (CORE-11, AC 2-3)
Proof: run unit | test_config_hash_unicode_and_key_order PASSED

**C12** - Function config_hash strictly distinguishes bool vs int, int vs float, and tuple vs list (CORE-12, AC 4-5)
Proof: run unit | test_config_hash_strict_types PASSED

**C13** - Function config_hash normalizes -0.0 to 0.0 and canonicalizes NaN/Inf (CORE-13, AC 6-7)
Proof: run unit | test_config_hash_special_floats PASSED

**C14** - Function dataset_hash computes SHA-256 for CSV/TXT file and schema (CORE-14, AC 1-2)
Proof: run unit | test_dataset_hash_file_and_schema PASSED

**C15** - Function dataset_hash computes deterministic hash for in-memory data (CORE-15, AC 3-4)
Proof: run unit | test_dataset_hash_in_memory PASSED

**C16** - Function dataset_hash raises FileNotFoundError for nonexistent file (CORE-16, AC 5)
Proof: run unit | test_dataset_hash_file_not_found PASSED

**C17** - Constructors make_finding and make_warning create structured findings (CORE-17, AC 1-2)
Proof: run unit | test_make_finding_and_make_warning PASSED

**C18** - Framework exceptions are defined and Finding objects are immutable (CORE-18, AC 3-4)
Proof: run unit | test_core_exceptions_and_finding_immutability PASSED

---

## Handoff

The feature's live state, written as it happens - a compaction gives no warning.

**Settled mid-build:** none
**Dispatched:** none
**Walked:** none

---

## Phase Execution Map

Visual representation of task ordering. Phases run in sequence, and tasks within a phase run in order:

```
Phase 1: Environment & Domain Foundation
  T1 (pyproject.toml) -> T2 (src/experimental_ml/core/types.py) -> T3 (src/experimental_ml/core/enums.py) -> T4 (src/experimental_ml/core/findings.py)

Phase 2: Cryptographic Hashing, Random Seeds & Unit Verification
  T5 (src/experimental_ml/core/seeds.py) -> T6 (src/experimental_ml/core/hashing.py) -> T7 (src/experimental_ml/core/__init__.py) -> T8 (tests/unit/test_core.py)
```
