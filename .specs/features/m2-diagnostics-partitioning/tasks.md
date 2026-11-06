# m2-diagnostics-partitioning Tasks (M2.1 Dataset Profiling)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m2-diagnostics-partitioning/design.md`
**Status**: Ready
**Approved**: 2026-11-06 - user: "inicie"
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates
**Run unit**: .venv/bin/pytest tests/unit/data/test_profiling.py -v
**Run integration**: .venv/bin/pytest tests/integration/test_profiling_integration.py -v

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001`, `AD-002`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 12 requirements (`PROF-01` to `PROF-12`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Data Profiling Models & Configuration (`src/experimental_ml/data/profiling.py`) | unit | 1:1 AC mapping: `ProfileConfig` threshold boundaries, dataclass immutability, slot constraints, distribution models | `tests/unit/data/test_profiling.py` | `.venv/bin/pytest tests/unit/data/test_profiling.py -v` |
| Statistical Calculation Engines (`src/experimental_ml/data/profiling.py`) | unit | 1:1 AC mapping: numeric distributions, categorical frequencies, tie-breaking, duplicate rows, target/group analysis | `tests/unit/data/test_profiling.py` | `.venv/bin/pytest tests/unit/data/test_profiling.py -v` |
| Findings Catalog & Profiler API (`src/experimental_ml/data/profiling.py`) | unit | 1:1 AC mapping: 15 finding conditions, binary target mutual exclusivity, canonical sorting, determinism and bundle immutability | `tests/unit/data/test_profiling.py` | `.venv/bin/pytest tests/unit/data/test_profiling.py -v` |
| Profiling Integration & Architecture Invariants (`tests/integration/test_profiling_integration.py`) | integration | End-to-end profiling on realistic datasets, layer import direction, single runtime dependency, symbol count alignment | `tests/integration/test_profiling_integration.py` | `.venv/bin/pytest tests/integration/test_profiling_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After tasks with unit tests in profiling | `.venv/bin/pytest tests/unit/data/test_profiling.py -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Profiling Models & Configuration (`P1.1`)

Define immutable data structures for profiles and `ProfileConfig` with threshold boundary validation.

```
T1
```

### Phase 2: Statistical Calculation Engines (`P1.2`, `P1.3`)

Implement numeric, categorical, duplicate rows, target, and group statistical calculation engines.

```
T2 → T3
```

### Phase 3: Closed Findings Catalog & Public Profiler API (`P1.4`, `P1.5`)

Implement the 15-finding rules engine, canonical sorting, and the public `profile_dataset` entry point.

```
T4 → T5
```

### Phase 4: Integration & Cross-Cutting Invariants (`P1.6`)

Implement end-to-end integration tests, architectural layer import verification, and symbol count tests.

```
T6
```

---

## Task Breakdown

### Phase 1: Profiling Models & Configuration (`P1.1`)

#### T1: Implement `ProfileConfig` and specialized distribution data models in `data/profiling.py`

**What**: Create `src/experimental_ml/data/profiling.py` defining `ProfileConfig` with threshold validation in `__post_init__` (raising `ConfigurationError` on invalid bounds), and immutable frozen slots dataclasses: `NumericDistributionStats`, `CategoryFrequency`, `CategoricalDistributionStats`, `ColumnProfile`, `TargetProfile`, `GroupProfile`, `DuplicateRowsProfile`, and `DatasetProfile`. Add co-located unit tests in `tests/unit/data/test_profiling.py`.
**Where**: `src/experimental_ml/data/profiling.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/findings.py`, `src/experimental_ml/core/types.py`, `src/experimental_ml/data/schema.py`
**Requirement**: PROF-11

**Done when**:
- [x] `ProfileConfig` implemented with frozen slots and threshold boundary checks in `__post_init__`
- [x] Passing an invalid threshold raises `ConfigurationError` with informative message
- [x] All distribution models defined with `frozen=True, slots=True`
- [x] Unit tests for `ProfileConfig` boundary validation pass in `tests/unit/data/test_profiling.py`
- [x] Gate check passes: `.venv/bin/pytest tests/unit/data/test_profiling.py -v`

**Tests**: unit
**Gate**: quick

**Commit**: `feat(data): define profiling data structures and ProfileConfig validation`

---

### Phase 2: Statistical Calculation Engines (`P1.2`, `P1.3`)

#### T2: Implement numeric and categorical distribution calculation engines in `data/profiling.py`

**What**: Implement in `src/experimental_ml/data/profiling.py` the numeric distribution calculator (`mean`, `std` with `ddof=1`, `min`, `max`, `q1`, `median`, `q3`, `range`, `iqr`) with graceful handling of $N=0$ (all `None`), $N=1$ (`std=None`), zero variance (`std=0.0`), and the categorical frequency calculator (cardinality, value/type identity, deterministic tie-breaking `(type(v).__name__, str(v))`, truncation to `max_categories_reported`, `remainder_count`, `remainder_proportion`). Add unit tests in `tests/unit/data/test_profiling.py`.
**Where**: `src/experimental_ml/data/profiling.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/core/scalars.py`, `src/experimental_ml/data/profiling.py`
**Requirement**: PROF-02, PROF-03, PROF-12

**Done when**:
- [x] Numeric statistics compute mean, std (`ddof=1`), min, max, quartis, range, IQR over valid values
- [x] $N=0$ returns `None` for all numeric metrics without raising
- [x] $N=1$ returns point values and `std=None` without raising
- [x] Categorical frequency calculator counts non-missing values, sorts by count descending then UTF-8 value ascending, and applies `max_categories_reported` truncation
- [x] Heterogeneous scalar types in `object` columns are handled without comparison type errors
- [x] Unit tests covering `PROF-02`, `PROF-03`, and `PROF-12` pass in `tests/unit/data/test_profiling.py`
- [x] Gate check passes: `.venv/bin/pytest tests/unit/data/test_profiling.py -v`

**Tests**: unit
**Gate**: quick

**Commit**: `feat(data): implement numeric and categorical distribution calculation engines`

---

#### T3: Implement target, group, and duplicate rows analysis engines in `data/profiling.py`

**What**: Implement in `src/experimental_ml/data/profiling.py` the target distribution analyzer (`REGRESSION` with numeric stats, Fisher-Pearson `skewness` for $N \ge 3$ and $std > 0$, and IQR fence outliers; classification with class frequencies and majority/minority ratio), the group analyzer (group count, min/median/max group sizes), and the duplicate rows detection engine (comparing all columns except `observation_id`, missing value normalization via `_MISSING_SENTINEL`, scalar type tagging, deterministic order, `max_listed_ids` truncation). Add unit tests in `tests/unit/data/test_profiling.py`.
**Where**: `src/experimental_ml/data/profiling.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/core/scalars.py`, `src/experimental_ml/core/types.py`, `src/experimental_ml/data/profiling.py`
**Requirement**: PROF-04, PROF-05, PROF-06

**Done when**:
- [x] Target profile computes regression stats, skewness, and IQR fence outliers, or classification frequencies and majority/minority ratio
- [x] Regression target with $N < 3$ or zero variance sets `skewness = None`
- [x] Group profile calculates $N_{\text{groups}}$ and min, median, max group sizes when `group_col` is declared
- [x] Duplicate rows engine compares all columns except `observation_id`, treats missing values as equal, tags types to prevent cross-type collisions, and truncates at `max_listed_ids`
- [x] Unit tests covering `PROF-04`, `PROF-05`, and `PROF-06` pass in `tests/unit/data/test_profiling.py`
- [x] Gate check passes: `.venv/bin/pytest tests/unit/data/test_profiling.py -v`

**Tests**: unit
**Gate**: quick

**Commit**: `feat(data): implement target, group, and duplicate rows analysis engines`

---

### Phase 3: Closed Findings Catalog & Public Profiler API (`P1.4`, `P1.5`)

#### T4: Implement closed catalog evaluator and canonical finding sorting in `data/profiling.py`

**What**: Implement in `src/experimental_ml/data/profiling.py` the evaluation of the 15 closed findings: 8 `CONFIRMED_ISSUE` (`E1_TARGET_MISSING`, `E1_GROUP_MISSING`, `E1_FEATURE_MISSING`, `E1_CONSTANT_COLUMN`, `E1_CATEGORICAL_UNENCODED`, `E1_TARGET_BINARY_UNMAPPED`, `E1_TARGET_CLASS_COUNT_INVALID`, `E1_TARGET_NOT_NUMERIC`) and 7 `HEURISTIC_WARNING` (`W1_POSSIBLE_IDENTIFIER`, `W1_NEAR_CONSTANT_COLUMN`, `W1_SCALE_DISPARITY`, `W1_CLASS_IMBALANCE`, `W1_RARE_CLASS`, `W1_SMALL_GROUPS`, `W1_DUPLICATE_ROWS`). Enforce mutual exclusivity of binary classification target findings, eligible variables and $\ge 2$ non-zero absolute medians for scale disparity, and canonical sorting by `(severity, code, column)`. Add unit tests in `tests/unit/data/test_profiling.py`.
**Where**: `src/experimental_ml/data/profiling.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/core/findings.py`, `src/experimental_ml/core/enums.py`, `src/experimental_ml/data/profiling.py`
**Requirement**: PROF-07, PROF-08, PROF-09

**Done when**:
- [x] All 15 finding conditions evaluated with exact catalog codes and severities
- [x] `E1_TARGET_BINARY_UNMAPPED` and `E1_TARGET_CLASS_COUNT_INVALID` are mutually exclusive and never co-emitted
- [x] `W1_SCALE_DISPARITY` evaluates only eligible numeric features and requires $\ge 2$ non-zero absolute medians
- [x] Heuristic conditions emit only `HEURISTIC_WARNING` and never `CONFIRMED_ISSUE`
- [x] Findings sorted deterministically by severity (confirmed first), code, and column
- [x] Unit tests covering `PROF-07`, `PROF-08`, and `PROF-09` pass in `tests/unit/data/test_profiling.py`
- [x] Gate check passes: `.venv/bin/pytest tests/unit/data/test_profiling.py -v`

**Tests**: unit
**Gate**: quick

**Commit**: `feat(data): implement closed findings catalog evaluator and canonical sorting`

---

#### T5: Implement public `profile_dataset` functional entry point and export in `data/__init__.py`

**What**: Implement `profile_dataset(bundle: DatasetBundle, config: ProfileConfig | None = None) -> DatasetProfile` in `src/experimental_ml/data/profiling.py` and re-export `profile_dataset`, `DatasetProfile`, `ColumnProfile`, and `ProfileConfig` in `src/experimental_ml/data/__init__.py`. Ensure zero side-effects on `bundle.dataset_hash` and array buffers, and verify determinism across repeated calls. Add unit tests in `tests/unit/data/test_profiling.py`.
**Where**: `src/experimental_ml/data/profiling.py`
**Depends on**: T4
**Reuses**: `src/experimental_ml/data/types.py`, `src/experimental_ml/data/profiling.py`, `src/experimental_ml/data/__init__.py`
**Requirement**: PROF-01, PROF-10

**Done when**:
- [ ] `profile_dataset` entry point accepts `bundle` and optional `config` and returns frozen `DatasetProfile`
- [ ] Public symbols `profile_dataset`, `DatasetProfile`, `ColumnProfile`, `ProfileConfig` exported in `src/experimental_ml/data/__init__.py` and included in `__all__`
- [ ] Source `bundle.dataset_hash` and all underlying column buffers remain bit-identical before and after profiling
- [ ] Repeated calls with identical inputs produce equal `DatasetProfile` objects
- [ ] Unit tests covering `PROF-01` and `PROF-10` pass in `tests/unit/data/test_profiling.py`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/data/test_profiling.py -v`

**Tests**: unit
**Gate**: quick

**Commit**: `feat(data): expose profile_dataset public API with determinism and immutability guarantees`

---

### Phase 4: Integration & Cross-Cutting Invariants (`P1.6`)

#### T6: Implement cross-cutting integration suite and architectural invariants for M2.1

**What**: Create `tests/integration/test_profiling_integration.py` to verify end-to-end profiling on realistic synthetic datasets (regression with outliers, binary classification with unmapped labels, multiclass, grouped data, duplicate rows), and verify architectural invariants: import direction (`core` ← `data`, no `validation` import), single runtime dependency (`numpy>=1.24.0`), exported symbol count in `data` (17 symbols), and regression of existing test suite.
**Where**: `tests/integration/test_profiling_integration.py`
**Depends on**: T5
**Reuses**: `src/experimental_ml/data/__init__.py`, `tests/integration/test_m1_foundation_integration.py`
**Requirement**: PROF-01, PROF-07, PROF-10

**Done when**:
- [ ] Integration tests exercise realistic tabular datasets through `load_dataset` and `profile_dataset`
- [ ] Import direction verified by AST/module inspection: `data` imports `core`, never `validation`
- [ ] No new runtime dependencies added to `pyproject.toml`
- [ ] Exported symbol count in `experimental_ml.data` verified to match expected count
- [ ] Full project test suite passes with zero regressions: `.venv/bin/pytest tests/ -v`
- [ ] Gate check passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration
**Gate**: full

**Commit**: `test(integration): add profiling end-to-end integration suite and invariant tests`

---

## Checks

**C1** - `profile_dataset` returns immutable `DatasetProfile` with `source_dataset_hash == bundle.dataset_hash`, dimensions, memory, and per-column `ColumnProfile` with missing counts (`PROF-01`, AC 1)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_01_structural_profile_and_column_profiles PASSED

**C2** - Numeric statistics calculate mean, std (`ddof=1`), min, max, q1, median, q3, range, IQR over valid values and return `None` when undefined (`PROF-02`, AC 2)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_02_numeric_distribution_statistics PASSED

**C3** - Categorical/object/boolean columns report cardinality, category frequencies ordered by count descending then UTF-8 value ascending, capped at `max_categories_reported` with remainder (`PROF-03`, AC 3)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_03_categorical_distribution_and_frequencies PASSED

**C4** - Duplicate rows ignoring only `observation_id` report `n_duplicate_rows`, duplicate `ObservationId` values up to `max_listed_ids`, and truncation flag (`PROF-04`, AC 4)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_04_duplicate_rows_detection PASSED

**C5** - Target profile reports distribution, skewness, and IQR fence outliers for regression, and class frequencies with majority-to-minority ratio for classification (`PROF-05`, AC 5)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_05_target_profile_regression_and_classification PASSED

**C6** - Group profile reports number of groups and min, median, and max group sizes when `group_col` is declared (`PROF-06`, AC 6)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_06_group_profile_statistics PASSED

**C7** - Catalog findings emit exactly one finding per matching condition, built with `make_finding`/`make_warning`, carrying `column` in context, ordered by severity, code, and column (`PROF-07`, AC 7)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_07_catalog_findings_and_canonical_ordering PASSED

**C8** - Heuristic conditions emit only `HEURISTIC_WARNING` and never `CONFIRMED_ISSUE` (`PROF-08`, AC 8)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_08_severity_separation_heuristics_vs_issues PASSED

**C9** - Binary classification with non-missing classes != {0, 1} emits `E1_TARGET_BINARY_UNMAPPED`, and with class count != 2 emits `E1_TARGET_CLASS_COUNT_INVALID`, mutually exclusively (`PROF-09`, AC 9)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_09_binary_target_unmapped_and_class_count PASSED

**C10** - `profile_dataset` preserves `bundle.dataset_hash` and array buffers unchanged, and repeated calls yield equal profiles (`PROF-10`, AC 10)
Proof: run integration | tests/integration/test_profiling_integration.py::test_prof_10_immutability_and_determinism PASSED

**C11** - `ProfileConfig` raises `ConfigurationError` when any threshold is outside valid bounds before computing statistics (`PROF-11`, AC 11)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_11_profile_config_threshold_validation PASSED

**C12** - Fully missing column reports all statistics as `None`, emits `E1_CONSTANT_COLUMN` and `E1_FEATURE_MISSING` for features, and raises no exception (`PROF-12`, AC 12)
Proof: run unit | tests/unit/data/test_profiling.py::test_prof_12_fully_missing_column_handling PASSED

---

## Handoff

**Settled mid-build**: none
**Dispatched**: none
**Walked**: pending Execute phase

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1
Phase 2:  T2 ------→ T3
Phase 3:  T4 ------→ T5
Phase 4:  T6
```

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1: Profile data structures & config validation (`data/profiling.py`) | Data models + boundary validation unit tests | ✅ Granular |
| T2: Numeric and categorical distribution engines (`data/profiling.py`) | Distribution calculators + unit tests | ✅ Granular |
| T3: Target, group, duplicate rows engines (`data/profiling.py`) | Specialized analyzers + unit tests | ✅ Granular |
| T4: Findings catalog & canonical sorting (`data/profiling.py`) | Rules engine + canonical sort + unit tests | ✅ Granular |
| T5: Public `profile_dataset` entry point & exports (`data/__init__.py`) | Functional entry point + immutability tests | ✅ Granular |
| T6: Integration suite & invariant verification (`test_profiling_integration.py`) | Integration test suite + layer invariants | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | Phase 1 root (`T1`) | ✅ Match |
| T2 | T1 | Phase 2 start after Phase 1 (`T2`) | ✅ Match |
| T3 | T2 | `T2 → T3` | ✅ Match |
| T4 | T3 | Phase 3 start after Phase 2 (`T4`) | ✅ Match |
| T5 | T4 | `T4 → T5` | ✅ Match |
| T6 | T5 | Phase 4 start after Phase 3 (`T6`) | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1: Profile data structures & config | Data Profiling Models (`src/experimental_ml/data/profiling.py`) | unit | unit | ✅ OK |
| T2: Distribution engines | Statistical Calculation Engines (`src/experimental_ml/data/profiling.py`) | unit | unit | ✅ OK |
| T3: Target, group, duplicate engines | Statistical Calculation Engines (`src/experimental_ml/data/profiling.py`) | unit | unit | ✅ OK |
| T4: Findings catalog & sorting | Findings Catalog & API (`src/experimental_ml/data/profiling.py`) | unit | unit | ✅ OK |
| T5: Public `profile_dataset` entry point | Findings Catalog & API (`src/experimental_ml/data/profiling.py`) | unit | unit | ✅ OK |
| T6: Integration & invariants | Integration (`tests/integration/test_profiling_integration.py`) | integration | integration | ✅ OK |
