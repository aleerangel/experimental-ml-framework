# m1-4-datasets-schemas Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m1-4-datasets-schemas/design.md`
**Status**: Approved
**Approved**: 2026-11-04 - user: "Siga o fluxo do TLC a partir daqui, avançando para a próxima fase do milestone e conduzindo o processo até a implementação e verificação, respeitando os critérios de aceitação já definidos."
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates
**Run unit**: .venv/bin/pytest tests/unit/test_data_schemas.py -v

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied; datasets & schemas foundational package according to spec ACs.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Domain Schema (`src/experimental_ml/data/schema.py`) | unit | 1:1 AC mapping: all frozen structures, NFC normalization, role disjunction, Wave 2 blocking, and config_hash | `tests/unit/test_data_schemas.py` | `.venv/bin/pytest tests/unit/test_data_schemas.py -v` |
| Domain Types (`src/experimental_ml/data/types.py`) | unit | 1:1 AC mapping: ColumnDescriptor and DatasetBundle immutability, mapping encapsulation, and slots | `tests/unit/test_data_schemas.py` | `.venv/bin/pytest tests/unit/test_data_schemas.py -v` |
| Parsing Engine (`src/experimental_ml/data/parsing.py`) | unit | 1:1 AC mapping: delimiter sniffing, RFC 4180 quotes, ragged rows detection, whitespace delimitation, missing tokens | `tests/unit/test_data_schemas.py` | `.venv/bin/pytest tests/unit/test_data_schemas.py -v` |
| Validation & ObservationId (`src/experimental_ml/data/validation.py`) | unit | 1:1 AC mapping: ObservationId generation/validation, unique IDs, semantic descriptor defaults, schema-data consistency | `tests/unit/test_data_schemas.py` | `.venv/bin/pytest tests/unit/test_data_schemas.py -v` |
| Ingestion & Immutability (`src/experimental_ml/data/loader.py`) | unit | 1:1 AC mapping: defensive copying, bytes buffer-backed arrays (refusing setflags), object scalar immutability, tripartite hashing | `tests/unit/test_data_schemas.py` | `.venv/bin/pytest tests/unit/test_data_schemas.py -v` |
| Query Utilities (`src/experimental_ml/data/query.py`) | unit | 1:1 AC mapping: get_column_array copy/view, slice_bundle_by_observation_ids ordered slicing, hash recalculation | `tests/unit/test_data_schemas.py` | `.venv/bin/pytest tests/unit/test_data_schemas.py -v` |
| Public API Root (`src/experimental_ml/data/__init__.py`) | none | - (build gate only: public re-export exposure) | `src/experimental_ml/data/__init__.py` | quick gate only |
| Unit Test Suite (`tests/unit/test_data_schemas.py`) | unit | 100% pass across all 29 requirements | `tests/unit/test_data_schemas.py` | `.venv/bin/pytest tests/unit/test_data_schemas.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After single-file edits in data | `.venv/bin/python -m py_compile src/experimental_ml/data/*.py` |
| Full | After unit test updates | `.venv/bin/pytest tests/unit/test_data_schemas.py -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases and tasks are ordered and run sequentially - each task completes before the next begins.

### Phase 1: Schema Specification, Types & Tabular Parsing Engine

Implement `ColumnSemanticType`, `DatasetSchemaSpec`, `ColumnDescriptor`, `DatasetBundle`, and the tabular parsing/delimiter sniffer with comprehensive unit tests.

```
T1 → T2 → T3
```

### Phase 2: Schema Validation, ObservationId, Loader with Bytes Buffer Immutability & Query Utilities

Implement schema validation, observation ID assignment, `load_dataset` with defensive copying and buffer-level immutability, query utilities, and public exports.

```
T4 → T5 → T6 → T7
```

---

## Task Breakdown

### Phase 1: Schema Specification, Types & Tabular Parsing Engine

#### T1: Implement schema specification and semantic typing (`schema.py`)

**What**: Create `src/experimental_ml/data/schema.py` defining `ColumnSemanticType`, `DatasetSchemaSpec`, and `validate_schema_spec`, enforcing NFC normalization, disjunction of roles, whitespace/control character rejection, Wave 2 blocking, and `config_hash` compatibility.
**Where**: `src/experimental_ml/data/schema.py`
**Depends on**: None
**Reuses**: `experimental_ml.core.enums.StrEnum`, `experimental_ml.core.enums.TaskType`, `experimental_ml.core.findings.ConfigurationError`, `experimental_ml.core.hashing.config_hash`
**Requirement**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06

**Done when**:
- [ ] `src/experimental_ml/data/schema.py` created
- [ ] `ColumnSemanticType(StrEnum)` defined with 6 canonical members
- [ ] `DatasetSchemaSpec` frozen dataclass with NFC normalization and read-only mappings
- [ ] Empty or whitespace-only column names and control characters raise `ConfigurationError`
- [ ] `MULTI_TARGET_REGRESSION`, non-string targets, or `target_transform_spec != None` raise `ConfigurationError`
- [ ] Overlapping column roles raise `ConfigurationError`
- [ ] `config_hash(schema)` produces deterministic 64-hex SHA-256 invariant to NFD/NFC and key order
- [ ] Unit tests for schema specification pass in `tests/unit/test_data_schemas.py`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/test_data_schemas.py -v`

**Tests**: unit
**Gate**: quick

---

#### T2: Implement domain types (`types.py`)

**What**: Create `src/experimental_ml/data/types.py` defining `ColumnDescriptor` and `DatasetBundle` with frozen dataclasses, slots, and encapsulated read-only mappings.
**Where**: `src/experimental_ml/data/types.py`
**Depends on**: T1
**Reuses**: `experimental_ml.core.types.ObservationId`, `src/experimental_ml/data/schema.py`
**Requirement**: DATA-01, DATA-12

**Done when**:
- [ ] `src/experimental_ml/data/types.py` created with `ColumnDescriptor` and `DatasetBundle`
- [ ] Both structures are `@dataclass(frozen=True, slots=True)`
- [ ] Columns and descriptors encapsulated via `MappingProxyType`
- [ ] Unit tests for domain types pass in `tests/unit/test_data_schemas.py`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/test_data_schemas.py -v`

**Tests**: unit
**Gate**: quick

---

#### T3: Implement tabular parsing engine (`parsing.py`)

**What**: Create `src/experimental_ml/data/parsing.py` defining `SUPPORTED_DELIMITERS`, `detect_delimiter`, and `parse_tabular_text`, supporting RFC 4180 quotes, whitespace sequences, ragged row detection, header validation, and missing token mapping.
**Where**: `src/experimental_ml/data/parsing.py`
**Depends on**: T2
**Reuses**: `experimental_ml.core.findings.DataIntegrityError`
**Requirement**: DATA-15, DATA-16, DATA-17, DATA-18, DATA-19, DATA-20, DATA-21, DATA-22

**Done when**:
- [ ] `src/experimental_ml/data/parsing.py` created with `SUPPORTED_DELIMITERS`, `detect_delimiter`, and `parse_tabular_text`
- [ ] Strict sniffer inspects up to 100 lines; raises `DataIntegrityError` on ambiguity or inconsistent counts
- [ ] Explicit delimiter overrides automatic detection
- [ ] Ragged rows raise `DataIntegrityError` with 1-based line number and expected vs actual column count
- [ ] Empty files, whitespace-only files, or zero data rows raise `DataIntegrityError`
- [ ] RFC 4180 double-quoted fields with internal delimiters and escaped quotes supported
- [ ] Missing tokens mapped to sentinels (`None` / `np.nan`)
- [ ] Header NFC normalization and duplicate/empty column detection
- [ ] Unit tests for parsing pass in `tests/unit/test_data_schemas.py`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/test_data_schemas.py -v`

**Tests**: unit
**Gate**: quick

---

### Phase 2: Schema Validation, ObservationId, Loader with Bytes Buffer Immutability & Query Utilities

#### T4: Implement schema validation and ObservationId assignment (`validation.py`)

**What**: Create `src/experimental_ml/data/validation.py` defining `assign_or_validate_observation_ids` and `validate_dataset_schema`, handling `ObservationId` sequential generation (`obs_000000`), source ID extraction/uniqueness validation, `ColumnDescriptor` assignment with neutral defaults, and feature candidate validation (`len(feature_cols) >= 1`).
**Where**: `src/experimental_ml/data/validation.py`
**Depends on**: T3
**Reuses**: `experimental_ml.core.types.ObservationId`, `experimental_ml.core.findings.DataIntegrityError`
**Requirement**: DATA-23, DATA-24, DATA-25, DATA-26, DATA-27

**Done when**:
- [ ] `src/experimental_ml/data/validation.py` created
- [ ] `assign_or_validate_observation_ids` deterministically generates `obs_000000` when `observation_id_col` is None
- [ ] When `observation_id_col` is provided, non-nullness and strict uniqueness are verified; duplicates/nulls raise `DataIntegrityError`
- [ ] `ColumnDescriptor` correctly populates index, role, physical_type, semantic_type, and is_semantic_declared (declared vs default fallback)
- [ ] Undeclared semantic type column missing from data raises `DataIntegrityError`
- [ ] Datasets with $N=0$, $M=0$, missing schema columns, or `len(feature_cols) == 0` raise `DataIntegrityError`
- [ ] Unit tests for validation and observation IDs pass in `tests/unit/test_data_schemas.py`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/test_data_schemas.py -v`

**Tests**: unit
**Gate**: quick

---

#### T5: Implement dataset loader with buffer-level immutability and tripartite hashing (`loader.py`)

**What**: Create `src/experimental_ml/data/loader.py` implementing `build_immutable_column` (using `np.frombuffer` over `bytes` for numeric/bool arrays, and immutable scalar validation for `object` arrays) and `load_dataset` for files and in-memory structures, computing `raw_source_hash`, `dataset_hash`, and `schema_hash`.
**Where**: `src/experimental_ml/data/loader.py`
**Depends on**: T4
**Reuses**: `experimental_ml.core.hashing.dataset_hash`, `experimental_ml.core.hashing.config_hash`, `experimental_ml.core.findings.DataIntegrityError`
**Requirement**: DATA-07, DATA-08, DATA-09, DATA-10, DATA-11, DATA-12, DATA-13, DATA-14

**Done when**:
- [ ] `src/experimental_ml/data/loader.py` created
- [ ] `load_dataset` accepts file paths (`.csv`, `.txt`, `.tsv`) and in-memory structures (`dict`, `ndarray`, records, `DataFrame` duck-typing)
- [ ] Defensive copies ensure mutations on caller's source post-load have zero effect on `bundle.columns`
- [ ] Numeric/bool arrays backed by `bytes` buffer: calling `arr.setflags(write=True)` raises `ValueError`
- [ ] Object columns contain strictly immutable scalars (`str`, `int`, `float`, `bool`, `None`); mutable objects (`list`, `dict`) raise `DataIntegrityError`
- [ ] Missing values preserved (`np.nan` in float64, `None` in object) without silent dropping
- [ ] Metadata fields (`schema`, `n_rows`, `n_cols`, `column_names`, `feature_cols`, `descriptors`, `observation_ids`, `dataset_hash`, `raw_source_hash`, `schema_hash`, `memory_bytes`, `source_path`) populated
- [ ] `dataset_hash` canonical binary digest invariant to line endings (`\r\n` vs `\n`) or CSV vs memory
- [ ] `raw_source_hash` reflects disk bytes or memory source
- [ ] Unit tests for loader and immutability pass in `tests/unit/test_data_schemas.py`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/test_data_schemas.py -v`

**Tests**: unit
**Gate**: quick

---

#### T6: Implement functional query and ordered slicing utilities (`query.py`)

**What**: Create `src/experimental_ml/data/query.py` implementing `get_column_array` (read-only view with `copy=False` or independent copy with `copy=True`) and `slice_bundle_by_observation_ids` (strictly ordered sub-bundle with updated metadata and recalculated `dataset_hash`).
**Where**: `src/experimental_ml/data/query.py`
**Depends on**: T5
**Reuses**: `src/experimental_ml/data/types.py`, `experimental_ml.core.findings.DataIntegrityError`, `experimental_ml.core.hashing.dataset_hash`
**Requirement**: DATA-28, DATA-29

**Done when**:
- [ ] `src/experimental_ml/data/query.py` created
- [ ] `get_column_array(bundle, col, copy=False)` returns read-only array; `copy=True` returns writeable copy; non-existent column raises `DataIntegrityError`
- [ ] `slice_bundle_by_observation_ids` slices bundle strictly preserving the requested ID order, recalculating `n_rows`, `descriptors`, and `dataset_hash`
- [ ] Empty ID list, duplicates, or non-existent IDs raise `DataIntegrityError`
- [ ] Unit tests for query utilities pass in `tests/unit/test_data_schemas.py`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/test_data_schemas.py -v`

**Tests**: unit
**Gate**: quick

---

#### T7: Implement package root re-exports, full test suite pass and build verification (`__init__.py`)

**What**: Create `src/experimental_ml/data/__init__.py` exporting all public symbols in `__all__`, verify that all 29 requirements pass with 100% test coverage, and execute repository-wide test gates.
**Where**: `src/experimental_ml/data/__init__.py`
**Depends on**: T6
**Reuses**: `src/experimental_ml/data/*`
**Requirement**: All 29 requirements (DATA-01 to DATA-29)

**Done when**:
- [ ] `src/experimental_ml/data/__init__.py` exposes all public symbols in `__all__`
- [ ] Full test suite in `tests/unit/test_data_schemas.py` passes all 29 checks
- [ ] Zero regressions in existing smoke, core, and metrics tests: `.venv/bin/pytest tests/ -v` passes 100%
- [ ] Gate check passes: `.venv/bin/pytest tests/ -v`

**Tests**: unit
**Gate**: build

---

## Checks

**C1** - Frozen immutable data structures DatasetSchemaSpec, ColumnDescriptor, DatasetBundle and ColumnSemanticType enum exist in experimental_ml.data (DATA-01, AC 1)
Proof: run unit | test_domain_structures_and_enum_immutable PASSED

**C2** - DatasetSchemaSpec normalizes column names with Unicode NFC, converts ignore_cols to tuple and encapsulates mappings (DATA-02, AC 2)
Proof: run unit | test_schema_spec_nfc_normalization_and_encapsulation PASSED

**C3** - DatasetSchemaSpec raises ConfigurationError for empty, whitespace-only or control-containing column names (DATA-03, AC 3)
Proof: run unit | test_schema_spec_rejects_empty_and_control_chars PASSED

**C4** - DatasetSchemaSpec raises ConfigurationError for Wave 2 features MULTI_TARGET_REGRESSION, non-string target_col, or target_transform_spec (DATA-04, AC 4)
Proof: run unit | test_schema_spec_blocks_wave2_features PASSED

**C5** - DatasetSchemaSpec raises ConfigurationError when any column name is assigned to multiple structural roles (DATA-05, AC 5)
Proof: run unit | test_schema_spec_enforces_disjoint_roles PASSED

**C6** - config_hash produces a deterministic 64-hex SHA-256 invariant to Unicode NFD/NFC and key order (DATA-06, AC 6)
Proof: run unit | test_schema_spec_config_hash_invariance PASSED

**C7** - load_dataset loads tabular files and in-memory structures returning immutable DatasetBundle with complete data ownership (DATA-07, AC 1)
Proof: run unit | test_load_dataset_sources_and_bundle_ownership PASSED

**C8** - Ingestion creates defensive memory copies so modifying caller source post-load has zero effect on bundle (DATA-08, AC 2)
Proof: run unit | test_load_dataset_defensive_copies_isolation PASSED

**C9** - Numeric and boolean columns in DatasetBundle are backed by immutable bytes buffers refusing setflags write reactivation with ValueError (DATA-09, AC 3)
Proof: run unit | test_bundle_numeric_columns_buffer_immutability PASSED

**C10** - Object columns contain strictly immutable scalars with writeable=False and mutable objects raise DataIntegrityError (DATA-10, AC 4)
Proof: run unit | test_bundle_object_columns_scalar_immutability PASSED

**C11** - Ingestion preserves original missing values without silent imputation, row deletion, or scaling (DATA-11, AC 5)
Proof: run unit | test_load_dataset_preserves_missing_values PASSED

**C12** - DatasetBundle records complete structural metadata including schema, dimensions, descriptors, hashes, and memory bytes (DATA-12, AC 6)
Proof: run unit | test_bundle_structural_metadata_completeness PASSED

**C13** - dataset_hash computes canonical in-memory binary digest matching between CSV and memory and distinguishing int vs float (DATA-13, AC 7)
Proof: run unit | test_dataset_hash_canonical_in_memory_digest PASSED

**C14** - raw_source_hash computes digest of raw source input matching disk file bytes or memory structure (DATA-14, AC 8)
Proof: run unit | test_raw_source_hash_file_and_memory PASSED

**C15** - Tabular parser supports delimiters comma, semicolon, tab, pipe, and whitespace sequences honoring RFC 4180 quotes (DATA-15, AC 1)
Proof: run unit | test_tabular_parsing_supported_delimiters_and_quotes PASSED

**C16** - Automatic delimiter detection verifies constant column count M >= 2 across sampled lines (DATA-16, AC 2)
Proof: run unit | test_delimiter_sniffer_automatic_detection PASSED

**C17** - Ambiguous or non-uniform delimiters raise DataIntegrityError prompting explicit delimiter declaration (DATA-17, AC 3)
Proof: run unit | test_delimiter_sniffer_ambiguity_raises_error PASSED

**C18** - Explicit delimiter overrides automatic detection and parses strictly (DATA-18, AC 4)
Proof: run unit | test_explicit_delimiter_overrides_detection PASSED

**C19** - Ragged rows raise DataIntegrityError detailing 1-based line number and expected vs actual column count (DATA-19, AC 5)
Proof: run unit | test_ragged_rows_raise_data_integrity_error PASSED

**C20** - Empty file, whitespace-only file, or header-only file with zero data rows raises DataIntegrityError (DATA-20, AC 6)
Proof: run unit | test_empty_or_zero_rows_file_raises_error PASSED

**C21** - has_header=False assigns column_names or generates canonical positional names, raising error on length mismatch (DATA-21, AC 7)
Proof: run unit | test_parsing_has_header_false_and_column_names PASSED

**C22** - Header line containing empty column names after trimming or duplicate names after NFC normalization raises DataIntegrityError (DATA-22, AC 8)
Proof: run unit | test_header_validation_empty_or_duplicate_names PASSED

**C23** - ColumnDescriptor correctly populated with index, role, physical_type, semantic_type, and null count (DATA-23, AC 1)
Proof: run unit | test_column_descriptor_fields_and_roles PASSED

**C24** - Explicit column_semantic_types sets is_semantic_declared=True, undeclared applies neutral defaults, and unknown columns raise error (DATA-24, AC 2-4)
Proof: run unit | test_semantic_types_declared_vs_default_fallbacks PASSED

**C25** - When observation_id_col is None, load_dataset deterministically generates obs_000000 sequential identifiers (DATA-25, AC 1)
Proof: run unit | test_observation_ids_positional_generation PASSED

**C26** - When observation_id_col is specified, non-nullness and strict uniqueness are verified, raising DataIntegrityError on violations (DATA-26, AC 2-3)
Proof: run unit | test_observation_ids_source_column_validation PASSED

**C27** - Datasets with zero rows, zero columns, missing schema columns, or zero feature columns raise DataIntegrityError (DATA-27, AC 4-5)
Proof: run unit | test_dataset_schema_validation_structural_errors PASSED

**C28** - get_column_array returns read-only array when copy=False (refusing write reactivation) and writeable copy when copy=True (DATA-28, AC 1)
Proof: run unit | test_get_column_array_view_and_copy PASSED

**C29** - slice_bundle_by_observation_ids returns ordered immutable sub-bundle recalculating dataset_hash, and rejects invalid IDs (DATA-29, AC 2-3)
Proof: run unit | test_slice_bundle_by_observation_ids_ordering_and_hash PASSED

---

## Acceptance Walkthrough (ACCEPTANCE.md)

Alongside `tasks.md`, `ACCEPTANCE.md` is maintained defining:
1. Environment preparation and import verification of `experimental_ml.data`.
2. Public API consumer tests covering schema specification, tabular loading, array immutability, delimiter detection, and tripartite hashes.
3. Integrated slicing and observation ID preservation scenario.
4. Approval matrix mapped to criteria `AC-M1.4-1` through `AC-M1.4-10`.

---

## Handoff

The feature's live state, written as it happens.

**Settled mid-build:** none
**Dispatched:** none
**Walked:** pending
