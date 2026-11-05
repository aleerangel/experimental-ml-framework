# m1-5-foundation-hardening Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m1-5-foundation-hardening/design.md`
**Status**: Draft
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates
**Run unit**: .venv/bin/pytest tests/ -v

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001`, `AD-002`), `engenharia_software/ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 15 requirements (`HARD-01` to `HARD-15`).

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Core Hashing & Scalar Missingness (`src/experimental_ml/core/hashing.py`) | unit | 1:1 AC mapping: `is_nan_scalar`/`is_missing_scalar` across Python & NumPy floats, unambiguous binary framing in `dataset_hash`, scalar type tags in `object`, `observation_ids` framing without `data` coupling | `tests/unit/test_core.py` | `.venv/bin/pytest tests/unit/test_core.py -v` |
| Data Ingestion & Validation (`src/experimental_ml/data/loader.py`) | unit | 1:1 AC mapping: unified missingness (`None`/`float` NaN/`np.floating` NaN), `dtype=object` immutable scalar whitelist, semantic preservation in `ColumnDescriptor`, `int64` `OverflowError` handling, and `dataset_hash` delegation | `tests/unit/test_data_schemas.py` | `.venv/bin/pytest tests/unit/test_data_schemas.py -v` |
| Data Query & Slicing (`src/experimental_ml/data/query.py`) | unit | 1:1 AC mapping: `slice_bundle_by_observation_ids` input validation, `ObservationId` conversion/preservation, `is_missing_scalar` descriptor recount, and `dataset_hash` delegation with `observation_ids` | `tests/unit/test_data_schemas.py` | `.venv/bin/pytest tests/unit/test_data_schemas.py -v` |
| Cross-Module Integration & Documentation (`tests/integration/test_m1_foundation_integration.py`) | integration | End-to-end `core` + `data` + `metrics` flow, cross-process hash determinism (`PYTHONHASHSEED`), subprocess execution of all `README.md` Python blocks, and audit finding governance checks | `tests/integration/test_m1_foundation_integration.py` | `.venv/bin/pytest tests/integration/test_m1_foundation_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After tasks with unit tests in `core` or `data` | `.venv/bin/pytest tests/unit/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Core Hashing & Missingness Unification (`P0.1`, `P0.2`, `P0.5`)

Centralize scalar `NaN`/missingness detection and implement unambiguous tabular/scalar binary framing and `observation_ids` support in `experimental_ml.core.hashing` while preserving `data -> core` direction.

```
T1
```

### Phase 2: Data Layer Hardening (`P0.2`, `P0.3`, `P0.4`, `P0.5`, `AUD-F-007`)

Harden `experimental_ml.data` ingestion, validation, and slicing to use `is_missing_scalar`, enforce the `dtype=object` immutable scalar whitelist and `int64` bounds, preserve `ObservationId` instances, and delegate `dataset_hash` with `observation_ids`.

```
T2 → T3
```

### Phase 3: Documentation Alignment, Cross-Module Integration & Governance Closure (`P0.6`, `AUD-F-002`, `AUD-F-010`, `AUD-F-013`, `HARD-15`)

Align project documentation (`README.md`, `ARQUITETURA_E_CONTRATOS.md`, `ETAPA_ATUAL_ENGENHARIA.md`), add the cross-module integration test suite (`tests/integration/test_m1_foundation_integration.py`), and record the final disposition of all 16 audit findings in `RESULTS.md`.

```
T4 → T5
```

---

## Task Breakdown

### Phase 1: Core Hashing & Missingness Unification (`P0.1`, `P0.2`, `P0.5`)

#### T1: Implement centralized NaN detection, unambiguous binary framing, and `observation_ids` support in `core/hashing.py`

**What**: Update `src/experimental_ml/core/hashing.py` (and re-export in `src/experimental_ml/core/__init__.py`) to define `is_nan_scalar(val)` and `is_missing_scalar(val)`, add the keyword-only `observation_ids` parameter to `dataset_hash(data_or_path, schema=None, *, observation_ids=None)` without importing `experimental_ml.data`, and enforce unambiguous binary framing (presence flags, column count `<Q`, NFC column name lengths `<Q`, exact domain string framing for `observation_ids`, and scalar type tags in `object` columns), with unit tests in `tests/unit/test_core.py`.
**Where**: `src/experimental_ml/core/hashing.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/findings.py`, `tests/unit/test_core.py`
**Requirement**: HARD-01, HARD-02, HARD-03, HARD-05

**Done when**:
- [ ] `is_nan_scalar(val)` and `is_missing_scalar(val)` implemented in `src/experimental_ml/core/hashing.py` and exported in `src/experimental_ml/core/__init__.py`
- [ ] `dataset_hash(data_or_path, schema=None, *, observation_ids=None)` frames `schema` flag, `observation_ids` flag/count/lengths, `b"TABULAR"`, column count `<Q`, and NFC column name byte lengths `<Q`
- [ ] `_hash_column_binary` prefixes scalar type tags (`str`, `bytes`, `bool`, `int`, `float`) in `object` columns and uses `is_missing_scalar(val)` for `b"\x00"`
- [ ] `dataset_hash({"ab": [1.0], "c": [2.0]}) != dataset_hash({"a": [1.0], "bc": [2.0]})` and `"1"`, `1`, `1.0`, `True`, `b"1"` produce distinct hashes
- [ ] Co-located unit tests added in `tests/unit/test_core.py` covering `HARD-01`, `HARD-02`, `HARD-03`, and `HARD-05`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/ -v`
- [ ] Test count: all unit tests in `tests/unit/test_core.py` pass (no silent deletions)

**Tests**: unit
**Gate**: quick

**Commit**: `fix(core): harden dataset_hash framing and centralize NaN scalar detection`

---

### Phase 2: Data Layer Hardening (`P0.2`, `P0.3`, `P0.4`, `P0.5`, `AUD-F-007`)

#### T2: Harden `data/loader.py` and `data/validation.py` with unified missingness, `object` scalar whitelist, `int64` overflow handling, and `observation_ids` hash delegation

**What**: Update `src/experimental_ml/data/loader.py` and `src/experimental_ml/data/validation.py` to replace local `isinstance(..., float) and math.isnan(...)` checks with `is_missing_scalar`, enforce the `dtype=object` immutable scalar whitelist (normalizing `None`/`float` NaN/`np.floating` NaN to `None`, materializing `DomainIdentifier`/`StrEnum` as NFC `str` while preserving `ColumnDescriptor` semantic metadata, and rejecting mutable objects/subclasses/special numeric types with `DataIntegrityError`), catch `OverflowError` on integers outside $[-2^{63}, 2^{63}-1]$ as `DataIntegrityError`, and pass `observation_ids=observation_ids` to `core_dataset_hash`, with unit tests in `tests/unit/test_data_schemas.py`.
**Where**: `src/experimental_ml/data/loader.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/core/hashing.py`, `src/experimental_ml/data/validation.py`, `tests/unit/test_data_schemas.py`
**Requirement**: HARD-04, HARD-06, HARD-09, HARD-10, HARD-11

**Done when**:
- [ ] `loader.py` and `validation.py` use `is_missing_scalar` from `experimental_ml.core.hashing`, accurately counting `np.float16(np.nan)` and `np.float32(np.nan)` in `ColumnDescriptor.n_missing`
- [ ] `_coerce_column_values` normalizes `None`, `float` NaN, and `np.floating` NaN to `None` in `object` columns and preserves `ColumnDescriptor.semantic_type` when materializing `DomainIdentifier` and `StrEnum`
- [ ] `_coerce_column_values` rejects `SimpleNamespace`, mutable containers, user subclasses with `__dict__`, `complex`, `Decimal`, and `Fraction` with `DataIntegrityError`
- [ ] Integers outside $[-2^{63}, 2^{63}-1]$ raise `DataIntegrityError` instead of `OverflowError`
- [ ] `load_dataset` computes `b_hash = core_dataset_hash(immutable_columns, schema, observation_ids=observation_ids)`
- [ ] Co-located unit tests added in `tests/unit/test_data_schemas.py` covering `HARD-04`, `HARD-06`, `HARD-09`, `HARD-10`, and `HARD-11`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/ -v`
- [ ] Test count: all unit tests in `tests/unit/` pass (no silent deletions)

**Tests**: unit
**Gate**: quick

**Commit**: `fix(data): enforce object scalar whitelist, int64 bounds, and unified NaN handling`

---

#### T3: Harden `slice_bundle_by_observation_ids` in `data/query.py` to validate and preserve `ObservationId` and delegate `dataset_hash`

**What**: Update `src/experimental_ml/data/query.py` so `slice_bundle_by_observation_ids` rejects bare `str`/`bytes` and non-`Sequence` inputs, validates and converts each item to `ObservationId` (raising `DataIntegrityError` on invalid types, malformed strings, duplicates, or unknown IDs), returns `observation_ids` as `tuple[ObservationId, ...]`, uses `is_missing_scalar` when recounting `n_missing`, and computes `new_hash = core_dataset_hash(new_columns, bundle.schema, observation_ids=sliced_obs_ids)`, with unit tests in `tests/unit/test_data_schemas.py`.
**Where**: `src/experimental_ml/data/query.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/core/types.py`, `src/experimental_ml/core/hashing.py`, `tests/unit/test_data_schemas.py`
**Requirement**: HARD-04, HARD-06, HARD-07, HARD-08

**Done when**:
- [ ] `slice_bundle_by_observation_ids` returns `tuple[ObservationId, ...]` in caller-requested order whether called with `ObservationId` or valid `str` elements
- [ ] Bare `str`/`bytes`, empty sequences, `int`/`None` elements, invalid `ObservationId` strings, duplicates, and absent IDs raise `DataIntegrityError`
- [ ] Slicing identical rows with distinct `observation_ids` produces distinct `dataset_hash` values equal to `core.dataset_hash(sliced.columns, sliced.schema, observation_ids=sliced.observation_ids)`
- [ ] Co-located unit tests added in `tests/unit/test_data_schemas.py` covering `HARD-04`, `HARD-07`, and `HARD-08`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/ -v`
- [ ] Test count: all unit tests in `tests/unit/` pass (no silent deletions)

**Tests**: unit
**Gate**: quick

**Commit**: `fix(data): preserve ObservationId instances and observation_ids hash in slice_bundle`

---

### Phase 3: Documentation Alignment, Cross-Module Integration & Governance Closure (`P0.6`, `AUD-F-002`, `AUD-F-010`, `AUD-F-013`, `HARD-15`)

#### T4: Fix `README.md` executable examples and architecture docs, and create `tests/integration/test_m1_foundation_integration.py`

**What**: Update `README.md` (fixing Python blocks 3 and 4 and the repository directory tree), `engenharia_software/ARQUITETURA_E_CONTRATOS.md` (documenting `dataset_hash` sensitivity to column order and `observation_ids` and `is_nan_scalar`/`is_missing_scalar` exports), and `engenharia_software/ETAPA_ATUAL_ENGENHARIA.md` (fixing `experimental_ml.data.__all__` symbol count to 13 and `core.__all__` to 27), and create `tests/integration/test_m1_foundation_integration.py` testing `core` + `data` + `metrics` integration, cross-process `PYTHONHASHSEED` determinism, and subprocess execution of all `README.md` Python code blocks.
**Where**: `tests/integration/test_m1_foundation_integration.py`
**Depends on**: T3
**Reuses**: `README.md`, `engenharia_software/ARQUITETURA_E_CONTRATOS.md`, `engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`
**Requirement**: HARD-12, HARD-13, HARD-14

**Done when**:
- [ ] `README.md` Python blocks 3 and 4 fixed (`is_better` with valid/undefined `MetricValue`, `spec.rtol`, `column_semantic_types=`, `len(bundle.feature_cols)`) and directory tree aligned with disk
- [ ] `ARQUITETURA_E_CONTRATOS.md` and `ETAPA_ATUAL_ENGENHARIA.md` aligned with the implemented contracts and symbol counts (`13` in `data`, `27` in `core`)
- [ ] `tests/integration/test_m1_foundation_integration.py` created and passing (`core` + `data` + `metrics` workflow, cross-process `PYTHONHASHSEED` determinism, and subprocess execution of all 4 `README.md` Python blocks)
- [ ] Gate check passes: `.venv/bin/pytest tests/ -v`
- [ ] Test count: all unit and integration tests pass (no silent deletions)

**Tests**: integration
**Gate**: full

**Commit**: `test(integration): add M1 cross-module integration suite and align documentation`

---

#### T5: Record final audit finding dispositions (`10 RESOLVIDO`, `6 ADIADO`) and M2 readiness verdict in `RESULTS.md`

**What**: Create `.specs/features/m1-5-foundation-hardening/RESULTS.md` documenting the revised remediation plan, the historical investigation of `AUD-F-012` (confirming `m1-1-setup-cli-smoke/verification.md` is not retroactively fabricated), the final traceability table for all 16 audit findings (`10 RESOLVIDO`, `6 ADIADO` with explicit target milestone/justification), and the updated readiness verdict for Milestone M2, with an automated governance check in `tests/integration/test_m1_foundation_integration.py`.
**Where**: `.specs/features/m1-5-foundation-hardening/RESULTS.md`
**Depends on**: T4
**Reuses**: `.specs/features/m1-integrity-review/reports/06-achados.md`, `.specs/features/m1-integrity-review/reports/07-plano-correcoes.md`, `tests/integration/test_m1_foundation_integration.py`
**Requirement**: HARD-15

**Done when**:
- [ ] `.specs/features/m1-5-foundation-hardening/RESULTS.md` created with complete traceability of `AUD-F-001` through `AUD-F-016` (`10 RESOLVIDO`, `6 ADIADO`) and historical record of `AUD-F-012`
- [ ] `.specs/features/m1-integrity-review/` remains untouched (`0` bytes of git diff) and `.specs/features/m1-1-setup-cli-smoke/verification.md` does not exist
- [ ] Governance verification test in `tests/integration/test_m1_foundation_integration.py` passes
- [ ] Gate check passes: `.venv/bin/pytest tests/ -v`
- [ ] Test count: all unit and integration tests pass (no silent deletions)

**Tests**: integration
**Gate**: full

**Commit**: `docs(specs): record M1.5 remediation results and audit finding traceability`

---

## Checks

**C1** - `core.dataset_hash` frames column count and NFC column name byte lengths so adjacent column name concatenations never collide and tabular inputs are deterministic (`HARD-01`, AC 1)
Proof: run unit | tests/unit/test_core.py::test_hard_01_dataset_hash_column_boundary_framing_and_determinism PASSED

**C2** - `core.dataset_hash` prefixes scalar type tags in `object` columns so `"1"`, `1`, `1.0`, `True`, and `b"1"` produce distinct digests and missing values serialize as `b"\x00"` (`HARD-02`, AC 2)
Proof: run unit | tests/unit/test_core.py::test_hard_02_dataset_hash_object_scalar_type_tags_and_missing PASSED

**C3** - `core.dataset_hash(data_or_path, schema=None, *, observation_ids=None)` incorporates `observation_ids` using exact domain string representation without importing `experimental_ml.data` (`HARD-03`, AC 3)
Proof: run unit | tests/unit/test_core.py::test_hard_03_dataset_hash_observation_ids_and_architecture_direction PASSED

**C4** - `load_dataset` and `slice_bundle_by_observation_ids` delegate to `core.dataset_hash(bundle.columns, bundle.schema, observation_ids=bundle.observation_ids)` so slices with identical values and distinct `observation_ids` have distinct hashes (`HARD-04`, AC 4)
Proof: run unit | tests/unit/test_data_schemas.py::test_hard_04_bundle_dataset_hash_delegates_observation_ids PASSED

**C5** - `is_nan_scalar` and `is_missing_scalar` in `experimental_ml.core.hashing` detect Python `float("nan")` and `np.floating` NaN (`float16`, `float32`, `float64`) while returning `False` for finite values and `bool` (`HARD-05`, AC 5)
Proof: run unit | tests/unit/test_core.py::test_hard_05_is_nan_and_missing_scalar_centralized PASSED

**C6** - `load_dataset`, `slice_bundle_by_observation_ids`, and `assign_or_validate_observation_ids` use `is_missing_scalar` and accurately count `np.float16(np.nan)` and `np.float32(np.nan)` in `ColumnDescriptor.n_missing` (`HARD-06`, AC 6)
Proof: run unit | tests/unit/test_data_schemas.py::test_hard_06_numpy_floating_nan_counted_across_data_layer PASSED

**C7** - `slice_bundle_by_observation_ids` converts valid `str` inputs and preserves `tuple[ObservationId, ...]` in caller-requested order (`HARD-07`, AC 1)
Proof: run unit | tests/unit/test_data_schemas.py::test_hard_07_slice_bundle_preserves_observation_id_instances PASSED

**C8** - `slice_bundle_by_observation_ids` raises `DataIntegrityError` on bare `str`/`bytes`, empty sequence, invalid types, malformed `ObservationId` strings, duplicates, or absent IDs (`HARD-08`, AC 2)
Proof: run unit | tests/unit/test_data_schemas.py::test_hard_08_slice_bundle_rejects_invalid_observation_id_inputs PASSED

**C9** - `load_dataset` unifies `None`, `float` NaN, and `np.floating` NaN as `None` in `object` columns and materializes `DomainIdentifier`/`StrEnum` as NFC `str` while preserving `ColumnDescriptor` semantic metadata (`HARD-09`, AC 3)
Proof: run unit | tests/unit/test_data_schemas.py::test_hard_09_object_column_missingness_and_semantic_preservation PASSED

**C10** - `load_dataset` rejects mutable containers, `SimpleNamespace`, user subclasses with `__dict__`, `complex`, `Decimal`, and `Fraction` in `object` columns with `DataIntegrityError` (`HARD-10`, AC 4)
Proof: run unit | tests/unit/test_data_schemas.py::test_hard_10_object_column_rejects_non_whitelisted_types PASSED

**C11** - `load_dataset` accepts exact `int64` boundary values $[-2^{63}, 2^{63}-1]$ and raises `DataIntegrityError` on integer overflow outside `int64` (`HARD-11`, AC 5)
Proof: run unit | tests/unit/test_data_schemas.py::test_hard_11_int64_overflow_raises_data_integrity_error PASSED

**C12** - Every fenced `python` code block in `README.md` executes in an isolated subprocess with exit code `0` (`HARD-12`, AC 1)
Proof: run unit | tests/integration/test_m1_foundation_integration.py::test_hard_12_readme_python_blocks_execute_cleanly PASSED

**C13** - `README.md`, `ARQUITETURA_E_CONTRATOS.md`, and `ETAPA_ATUAL_ENGENHARIA.md` match on-disk files, exported symbol counts (`13` in `data`, `27` in `core`), and `dataset_hash` semantics (`HARD-13`, AC 2)
Proof: run unit | tests/integration/test_m1_foundation_integration.py::test_hard_13_documentation_and_symbol_counts_aligned PASSED

**C14** - `tests/integration/test_m1_foundation_integration.py` verifies end-to-end `core` + `data` + `metrics` integration and cross-process `PYTHONHASHSEED` hash determinism (`HARD-14`, AC 3)
Proof: run unit | tests/integration/test_m1_foundation_integration.py::test_hard_14_end_to_end_core_data_metrics_and_cross_process_hash PASSED

**C15** - `.specs/features/m1-5-foundation-hardening/RESULTS.md` records all 16 audit findings (`10 RESOLVIDO`, `6 ADIADO`), preserves `.specs/features/m1-integrity-review/` untouched, and does not fabricate `m1-1-setup-cli-smoke/verification.md` (`HARD-15`, AC 4)
Proof: run unit | tests/integration/test_m1_foundation_integration.py::test_hard_15_audit_findings_governance_and_integrity_preservation PASSED

---

## Handoff

**Settled mid-build:** none
**Dispatched:** none
**Walked:** pending Execute phase

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3

Phase 1:  T1
Phase 2:  T2 ------→ T3
Phase 3:  T4 ------→ T5
```

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1: Core hashing & NaN scalar unification (`core/hashing.py`) | 1 core module + co-located unit tests | ✅ Granular |
| T2: Loader & validation hardening (`data/loader.py`) | 1 data ingestion flow + co-located unit tests | ✅ Granular |
| T3: Slicing `ObservationId` & hash delegation (`data/query.py`) | 1 query function + co-located unit tests | ✅ Granular |
| T4: Docs alignment & cross-module integration suite (`test_m1_foundation_integration.py`) | 1 integration test module + doc fixes | ✅ Granular |
| T5: Audit governance closure (`RESULTS.md`) | 1 governance record + verification test | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | Phase 1 root (`T1`) | ✅ Match |
| T2 | T1 | Phase 2 start after Phase 1 (`T2`) | ✅ Match |
| T3 | T2 | `T2 → T3` | ✅ Match |
| T4 | T3 | Phase 3 start after Phase 2 (`T4`) | ✅ Match |
| T5 | T4 | `T4 → T5` | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1: Core hashing & NaN detection | Core Hashing (`src/experimental_ml/core/hashing.py`) | unit | unit | ✅ OK |
| T2: Data loader & validation hardening | Data Ingestion (`src/experimental_ml/data/loader.py`) | unit | unit | ✅ OK |
| T3: Data query slicing hardening | Data Query (`src/experimental_ml/data/query.py`) | unit | unit | ✅ OK |
| T4: Docs & cross-module integration suite | Integration (`tests/integration/test_m1_foundation_integration.py`) | integration | integration | ✅ OK |
| T5: Audit governance closure | Integration (`RESULTS.md` + governance check) | integration | integration | ✅ OK |

