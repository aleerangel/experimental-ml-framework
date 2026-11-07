# m2-2-preparation-plan-sanitization Tasks (M2.2 Preparation Plan and Sanitized Dataset View)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m2-2-preparation-plan-sanitization/design.md`
**Status**: Approved
**Approved**: 2026-11-07 - user: "aprovado"
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates
**Run unit**: .venv/bin/pytest tests/unit/data/test_preparation.py -v
**Run integration**: .venv/bin/pytest tests/integration/test_preparation_integration.py -v

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001`, `AD-002`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 10 requirements (`PREP-01` to `PREP-10`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Data Preparation Models & Types (`src/experimental_ml/data/preparation.py`) | unit | 1:1 AC mapping: dataclass immutability, frozen slots, RuleKind enumeration, mapping proxy wrapping | `tests/unit/data/test_preparation.py` | `.venv/bin/pytest tests/unit/data/test_preparation.py -v` |
| Catalog Admissibility & Plan Construction (`src/experimental_ml/data/preparation.py`) | unit | 1:1 AC mapping: closed catalog admissibility, orphan/duplicate rule rejection, canonical sorting, plan digest, READY vs INCOMPLETE | `tests/unit/data/test_preparation.py` | `.venv/bin/pytest tests/unit/data/test_preparation.py -v` |
| Sanitization Engine & Invariants (`src/experimental_ml/data/preparation.py`) | unit | 1:1 AC mapping: row dropping, column exclusion, binary target mapping, bit-identical deferred preservation, non-emptiness validation | `tests/unit/data/test_preparation.py` | `.venv/bin/pytest tests/unit/data/test_preparation.py -v` |
| Preparation Integration & Architecture Invariants (`tests/integration/test_preparation_integration.py`) | integration | End-to-end preparation & sanitization pipeline, bundle immutability, determinism, layer import direction, symbol count alignment | `tests/integration/test_preparation_integration.py` | `.venv/bin/pytest tests/integration/test_preparation_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After tasks with unit tests in preparation | `.venv/bin/pytest tests/unit/data/test_preparation.py -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Preparation Models & Admissibility Engine (`P1.1`)

Define immutable data models for rules, plans, and sanitized views, and implement the closed catalog admissibility validator.

```
T1 → T2
```

### Phase 2: Plan Construction & Coverage Audit Engine (`P1.2`)

Implement `create_preparation_plan` with full coverage audit, canonical digest, and `READY`/`INCOMPLETE` status resolution.

```
T3
```

### Phase 3: Sanitization Engine & Dataset View Invariants (`P1.3`)

Implement `sanitize_dataset` executing structural rules, non-emptiness guards, bit-identical preservation, and canonical hash calculation.

```
T4 → T5
```

### Phase 4: Integration & Cross-Cutting Architectural Invariants (`P1.4`)

Expose public API symbols in `data/__init__.py` and verify end-to-end pipeline, determinism, bundle immutability, and import directions.

```
T6
```

---

## Task Breakdown

### Phase 1: Preparation Models & Admissibility Engine (`P1.1`)

#### T1: Define preparation data models and contracts in `data/preparation.py`

**What**: Create `src/experimental_ml/data/preparation.py` defining `RuleKind` (Literal), `PlanStatus` (Literal), `PreparationRule` (frozen dataclass, slots=True, with immutable parameter conversion to `MappingProxyType`), `UnresolvedFinding` (frozen dataclass, slots=True), `PreparationPlan` (frozen dataclass, slots=True), and `SanitizedDatasetView` (frozen dataclass, slots=True). Add co-located unit tests in `tests/unit/data/test_preparation.py`.
**Where**: `src/experimental_ml/data/preparation.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/findings.py`, `src/experimental_ml/core/types.py`, `src/experimental_ml/data/schema.py`
**Requirement**: PREP-01, PREP-06

**Done when**:
- [x] `PreparationRule`, `UnresolvedFinding`, `PreparationPlan`, `SanitizedDatasetView` defined with `frozen=True, slots=True`
- [x] `PreparationRule.parameters` immutable (`MappingProxyType`)
- [x] Unit tests verify immutability (mutations raise `FrozenInstanceError`) and slot constraints
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/data/test_preparation.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(data): definir modelos de dados e contratos de preparacao`

---

#### T2: Implement closed catalog admissibility validator in `data/preparation.py`

**What**: Implement `_validate_rule_admissibility(rule, profile)` adhering to the closed catalog: `DROP_ROWS` (admissible only for `E1_TARGET_MISSING`, `E1_GROUP_EMPTY_VALUES`, `E1_FEATURE_MISSING`), `EXCLUDE_COLUMN` (admissible only for `E1_FEATURE_MISSING`, `E1_CONSTANT_FEATURE_COLUMN`, `E1_COLUMN_ALL_MISSING`, `E1_IDENTIFIER_COLUMN_SUSPECTED`, `E1_CATEGORICAL_UNENCODED`; forbidden on target, group, observation_id), `MAP_BINARY_TARGET` (admissible only for `E1_TARGET_BINARY_UNMAPPED`, requires `positive_label`), `DEFER_INTRA_FOLD` (admissible only for `E1_FEATURE_MISSING` with strategy in `MEAN`/`MEDIAN`/`MODE` or `E1_CATEGORICAL_UNENCODED` with `encoding_strategy`), `ACCEPT_AS_IS` (admissible for `E1_FEATURE_MISSING`, `E1_CONSTANT_FEATURE_COLUMN`, `E1_COLUMN_ALL_MISSING`, `E1_IDENTIFIER_COLUMN_SUSPECTED`, `E1_CATEGORICAL_UNENCODED`). Raise `ConfigurationError` on unknown finding code, heuristic warning target, duplicate rules for same finding, or parameter violation. Add co-located unit tests in `tests/unit/data/test_preparation.py`.
**Where**: `src/experimental_ml/data/preparation.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/core/exceptions.py`, `src/experimental_ml/core/findings.py`
**Requirement**: PREP-03

**Done when**:
- [x] Catalog admissibility checked against finding code and column role
- [x] Rejects rules targeting non-`CONFIRMED_ISSUE` or non-existent finding with `ConfigurationError`
- [x] Rejects duplicate rules targeting same `(finding_code, column)` with `ConfigurationError`
- [x] Rejects invalid parameters (e.g. missing `positive_label`, invalid imputation strategy) with `ConfigurationError`
- [x] Unit tests for valid and invalid admissibility pass in `tests/unit/data/test_preparation.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/data/test_preparation.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(data): implementar validador de admissibilidade do catalogo fechado`

---

### Phase 2: Plan Construction & Coverage Audit Engine (`P1.2`)

#### T3: Implement `create_preparation_plan` in `data/preparation.py`

**What**: Implement `create_preparation_plan(profile, rules)` accepting `DatasetProfile` and a sequence of `PreparationRule` (or dicts converted to `PreparationRule`). Verify finding coverage against all `CONFIRMED_ISSUE` in `profile.findings`. If all confirmed issues have exactly one admissible rule, return `PreparationPlan` with `status = "READY"`, rules sorted canonically by `(finding_code, column or "")`, `source_dataset_hash = profile.source_dataset_hash`, `source_profile_digest` computed canonically, and `plan_digest` (SHA-256 over rules, source_dataset_hash, profile_digest). If any confirmed issue lacks a rule or is irresolvable (`E1_TARGET_ALL_MISSING`, `E1_TARGET_ZERO_VARIANCE`, `E1_TARGET_CLASS_COUNT_INVALID`, `E1_TARGET_NOT_NUMERIC`), return `PreparationPlan` with `status = "INCOMPLETE"`, empty `plan_digest = ""`, and `unresolved_findings` listing all uncovered items sorted canonically. Add co-located unit tests in `tests/unit/data/test_preparation.py`.
**Where**: `src/experimental_ml/data/preparation.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/core/digest.py`, `src/experimental_ml/data/profiling.py`
**Requirement**: PREP-01, PREP-02

**Done when**:
- [ ] Full coverage returns `PreparationPlan` with `status = "READY"` and canonical `plan_digest`
- [ ] Missing rule or irresolvable issue returns `status = "INCOMPLETE"` with `unresolved_findings`
- [ ] Rules are deterministically sorted in canonical order
- [ ] Unit tests for `PREP-01` and `PREP-02` pass in `tests/unit/data/test_preparation.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/data/test_preparation.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(data): implementar construcao de plano de preparacao e calculo de digest`

---

### Phase 3: Sanitization Engine & Dataset View Invariants (`P1.3`)

#### T4: Implement row filtering and binary target mapping in `data/preparation.py`

**What**: Implement initial pipeline of `sanitize_dataset(bundle, profile, plan)`: validate that `plan.status == "READY"` (raise `ContractViolationError` if not), validate hash bindings (`plan.source_dataset_hash == bundle.dataset_hash` and `plan.source_profile_digest == profile_digest`, raise `DataIntegrityError` if mismatched). For each rule in plan, execute `DROP_ROWS` for missing values in target, group, or specified feature columns, computing the boolean mask of dropped rows while preserving the original relative order of remaining rows. If `MAP_BINARY_TARGET` is present, encode target into `np.int64` (`positive_label -> 1`, alternative -> `0`) and record `target_label_mapping`. Verify non-emptiness of rows ($N > 0$, raise `DataIntegrityError` if empty). Add co-located unit tests in `tests/unit/data/test_preparation.py`.
**Where**: `src/experimental_ml/data/preparation.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/core/exceptions.py`, `src/experimental_ml/data/schema.py`
**Requirement**: PREP-04, PREP-05, PREP-08, PREP-09

**Done when**:
- [ ] Raises `ContractViolationError` on non-`READY` plan
- [ ] Raises `DataIntegrityError` on hash/digest mismatch
- [ ] `DROP_ROWS` drops rows with nulls, maintains relative order of remaining IDs, and records `dropped_observation_ids`
- [ ] `MAP_BINARY_TARGET` encodes target to `int64` {0, 1} and records mapping
- [ ] Raises `DataIntegrityError` if dropped rows result in 0 rows remaining
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/data/test_preparation.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(data): implementar filtragem de linhas e mapeamento de alvo binario`

---

#### T5: Implement column exclusion, bit-identical preservation, and view assembly in `data/preparation.py`

**What**: Complete `sanitize_dataset`: execute `EXCLUDE_COLUMN` removing specified columns from the output column map and updating `schema.columns`. For columns under `DEFER_INTRA_FOLD` or `ACCEPT_AS_IS`, copy filtered slice into output columns **100% bit-identical**, preserving exact values and missing values untouched. Compute `candidate_feature_cols` as all schema feature columns excluding target, group, observation_id, time, ignore, and excluded columns. Validate that `len(candidate_feature_cols) > 0` (raise `DataIntegrityError` if 0). Set all array buffers `writeable = False`. Compute new canonical `dataset_hash` via `core.dataset_hash(columns, schema, observation_ids)`. Construct and return `SanitizedDatasetView`. Verify that input `bundle` remains unmodified (`bundle.dataset_hash` unchanged). Add co-located unit tests in `tests/unit/data/test_preparation.py`.
**Where**: `src/experimental_ml/data/preparation.py`
**Depends on**: T4
**Reuses**: `src/experimental_ml/core/hashing.py`, `src/experimental_ml/data/bundle.py`
**Requirement**: PREP-04, PREP-06, PREP-07, PREP-09, PREP-10

**Done when**:
- [ ] `EXCLUDE_COLUMN` excludes column from output and schema
- [ ] `DEFER_INTRA_FOLD` and `ACCEPT_AS_IS` columns are bit-identical to source slice
- [ ] `candidate_feature_cols` correctly computed; raises `DataIntegrityError` if 0 feature columns remain
- [ ] Output column arrays are immutable (`writeable = False`)
- [ ] `SanitizedDatasetView.dataset_hash` canonically matches `core.dataset_hash(...)`
- [ ] Source `bundle` buffers and `bundle.dataset_hash` remain intact
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/data/test_preparation.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(data): implementar exclusao de colunas e montagem de SanitizedDatasetView`

---

### Phase 4: Integration & Cross-Cutting Architectural Invariants (`P1.4`)

#### T6: Expose public symbols in `data/__init__.py` and add integration test suite

**What**: Export `PreparationRule`, `PreparationPlan`, `SanitizedDatasetView`, `create_preparation_plan`, `sanitize_dataset` in `src/experimental_ml/data/__init__.py`. Add integration test suite in `tests/integration/test_preparation_integration.py` exercising end-to-end flow from profiling to plan to sanitization on realistic datasets, verifying determinism across runs, bundle immutability, import direction (`data` does not import `validation` or `models`), and public symbol integrity.
**Where**: `src/experimental_ml/data/__init__.py`
**Depends on**: T5
**Reuses**: `src/experimental_ml/data/__init__.py`, `tests/integration/test_profiling_integration.py`
**Requirement**: PREP-10

**Done when**:
- [ ] Public symbols exported from `experimental_ml.data`
- [ ] Integration tests verify determinism: identical inputs produce identical `dataset_hash` and `plan_digest`
- [ ] Integration tests verify bundle immutability before and after sanitization
- [ ] Architectural import direction tests confirm zero illegal cross-layer imports
- [ ] Full gate check passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration
**Gate**: full
**Commit**: `feat(data): exportar simbolos publicos de preparacao e suite de integracao`

---

## Checks

The checks below verify every acceptance criterion (`PREP-01` to `PREP-10`). Each check settles an observable claim against its exact proof.

**C1** - `create_preparation_plan` with full admissible coverage returns `PreparationPlan` with `status = "READY"`, bound hashes, and canonical rules order (`PREP-01`, AC 1)
Proof: run unit | tests/unit/data/test_preparation.py::test_prep_01_ready_plan_canonical_order PASSED

**C2** - `create_preparation_plan` with uncovered or irresolvable findings returns `status = "INCOMPLETE"` with `unresolved_findings` (`PREP-02`, AC 2)
Proof: run unit | tests/unit/data/test_preparation.py::test_prep_02_incomplete_plan_unresolved_findings PASSED

**C3** - `create_preparation_plan` raises `ConfigurationError` for orphan rules, duplicate rules, invalid parameters, or rule kinds not admissible for finding code (`PREP-03`, AC 3)
Proof: run unit | tests/unit/data/test_preparation.py::test_prep_03_invalid_rule_admissibility_and_configuration_error PASSED

**C4** - `sanitize_dataset` applies only `DROP_ROWS`, `EXCLUDE_COLUMN`, and `MAP_BINARY_TARGET`, returning immutable `SanitizedDatasetView` (`PREP-04`, AC 4)
Proof: run unit | tests/unit/data/test_preparation.py::test_prep_04_sanitize_dataset_structural_rules PASSED

**C5** - `sanitize_dataset` raises `ContractViolationError` if plan is not `READY`, and `DataIntegrityError` if hashes/digests diverge (`PREP-05`, AC 5)
Proof: run unit | tests/unit/data/test_preparation.py::test_prep_05_binding_validation_and_status_check PASSED

**C6** - `SanitizedDatasetView` exposes immutable tuple `observation_ids` preserving original relative order, `candidate_feature_cols`, `dropped_observation_ids`, and `dataset_hash` matching `core.dataset_hash(...)` (`PREP-06`, AC 6)
Proof: run unit | tests/unit/data/test_preparation.py::test_prep_06_sanitized_view_contract_and_dataset_hash PASSED

**C7** - Columns covered by `DEFER_INTRA_FOLD` or `ACCEPT_AS_IS` remain 100% bit-identical (including missing values) between source bundle and sanitized view (`PREP-07`, AC 7)
Proof: run unit | tests/unit/data/test_preparation.py::test_prep_07_bit_identical_deferred_and_accepted_columns PASSED

**C8** - `MAP_BINARY_TARGET` encodes target as `int64` with `positive_label` mapped to 1 and alternative to 0, recording mapping in `target_label_mapping` (`PREP-08`, AC 8)
Proof: run unit | tests/unit/data/test_preparation.py::test_prep_08_binary_target_mapping_and_encoding PASSED

**C9** - `sanitize_dataset` raises `DataIntegrityError` if sanitization results in 0 valid observations or 0 candidate feature columns (`PREP-09`, AC 9)
Proof: run unit | tests/unit/data/test_preparation.py::test_prep_09_empty_dataset_or_features_raises_integrity_error PASSED

**C10** - `sanitize_dataset` leaves source `bundle` and buffers unchanged, and identical inputs yield identical view `dataset_hash` and plan digest (`PREP-10`, AC 10)
Proof: run integration | tests/integration/test_preparation_integration.py::test_prep_10_immutability_and_determinism PASSED

---

## Handoff

**Settled mid-build**: none
**Dispatched**: none
**Walked**: pending Execute phase

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1 ------→ T2
Phase 2:  T3
Phase 3:  T4 ------→ T5
Phase 4:  T6
```

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1: Preparation models and types (`data/preparation.py`) | Data models + immutability unit tests | ✅ Granular |
| T2: Closed catalog admissibility validator (`data/preparation.py`) | Admissibility validator + unit tests | ✅ Granular |
| T3: Plan builder & coverage audit (`data/preparation.py`) | Plan builder + canonical digest + unit tests | ✅ Granular |
| T4: Row filtering and binary target mapping (`data/preparation.py`) | Row dropping + target mapping + unit tests | ✅ Granular |
| T5: Column exclusion, deferred preservation & view assembly (`data/preparation.py`) | Column exclusion + bit preservation + view assembly | ✅ Granular |
| T6: Module exports and integration test suite (`data/__init__.py`) | Public exports + end-to-end integration suite | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | Phase 1 root (`T1`) | ✅ Match |
| T2 | T1 | `T1 → T2` | ✅ Match |
| T3 | T2 | Phase 2 start after Phase 1 (`T3`) | ✅ Match |
| T4 | T3 | Phase 3 start after Phase 2 (`T4`) | ✅ Match |
| T5 | T4 | `T4 → T5` | ✅ Match |
| T6 | T5 | Phase 4 start after Phase 3 (`T6`) | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1: Preparation models and types | Data Preparation Models & Types (`src/experimental_ml/data/preparation.py`) | unit | unit | ✅ OK |
| T2: Closed catalog admissibility | Catalog Admissibility & Plan Construction (`src/experimental_ml/data/preparation.py`) | unit | unit | ✅ OK |
| T3: Plan builder & coverage audit | Catalog Admissibility & Plan Construction (`src/experimental_ml/data/preparation.py`) | unit | unit | ✅ OK |
| T4: Row filtering and binary target mapping | Sanitization Engine & Invariants (`src/experimental_ml/data/preparation.py`) | unit | unit | ✅ OK |
| T5: Column exclusion, deferred preservation & view assembly | Sanitization Engine & Invariants (`src/experimental_ml/data/preparation.py`) | unit | unit | ✅ OK |
| T6: Module exports and integration test suite | Preparation Integration & Architecture Invariants (`tests/integration/test_preparation_integration.py`) | integration | integration | ✅ OK |
