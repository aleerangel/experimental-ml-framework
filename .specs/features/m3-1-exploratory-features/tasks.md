# m3-1-exploratory-features Tasks (M3.1 Relatório Exploratório de Relações de Features)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m3-1-exploratory-features/design.md`  
**Status**: Approved  
**Approved**: 2026-11-10 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/features/ -v  
**Run integration**: .venv/bin/pytest tests/integration/features/ -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001` a `AD-004`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 8 requirements (`EXP-01` to `EXP-08`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Feature Types & Models (`src/experimental_ml/features/types.py`) | unit | 1:1 AC mapping: scope constant, methodological warnings, frozen models, JSON serialization & roundtrip reconstruction | `tests/unit/features/test_feature_types.py` | `.venv/bin/pytest tests/unit/features/test_feature_types.py -v` |
| Statistical Association Engine (`src/experimental_ml/features/stats.py`) | unit | 1:1 AC mapping: Pearson, Spearman with fractional ties, Correlation Ratio eta, Cramér's V, zero variance / degeneracy UNDEFINED_NAN | `tests/unit/features/test_stats.py` | `.venv/bin/pytest tests/unit/features/test_stats.py -v` |
| Exploration Engine & Redundancy (`src/experimental_ml/features/exploration.py`) | unit | 1:1 AC mapping: input validation, target association dispatch, redundancy matrix, canonical pair ordering | `tests/unit/features/test_exploration.py` | `.venv/bin/pytest tests/unit/features/test_exploration.py -v` |
| Features Integration & Invariants (`tests/integration/features/test_features_integration.py`) | integration | End-to-end pipeline from SanitizedDatasetView, deterministic hashing, zero external runtime dependencies (XCUT-02) | `tests/integration/features/test_features_integration.py` | `.venv/bin/pytest tests/integration/features/test_features_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After tasks with unit tests in features | `.venv/bin/pytest tests/unit/features/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Feature Models and Types (`P1.1`)

Define immutable data models for association measures, redundancy pairs, exploratory feature report, scope constant, methodological warnings, and JSON serialization/deserialization.

```
T1
```

### Phase 2: Statistical Association Functions (`P1.2`)

Implement pure NumPy algorithms for Pearson correlation, Spearman rank correlation with fractional ties, Correlation Ratio ($\eta$) and Cramér's V, with strict `UNDEFINED_NAN` handling for degenerate cases.

```
T2
```

### Phase 3: Exploratory Relations and Redundancy Engine (`P1.3`)

Implement `explore_features` with view validation, task-type-aware association dispatch, pairwise predictor redundancy matrix, and thresholded canonical pair extraction.

```
T3
```

### Phase 4: Public Exports and Integration Suite (`P1.4`)

Expose public API in `src/experimental_ml/features/__init__.py`, execute end-to-end integration tests connecting M2.2 sanitized views to M3.1 exploration, and verify runtime purity without SciPy/Scikit-Learn.

```
T4
```

---

## Task Breakdown

### Phase 1: Feature Models and Types (`P1.1`)

#### T1: Define feature report models, scope constant and serialization contracts

**What**: Create `src/experimental_ml/features/types.py` defining `SCOPE_EXPLORATORY_FULL_DATA = "EXPLORATORY_FULL_DATA"`, `METHODOLOGICAL_WARNINGS`, `AssociationMeasure` (frozen dataclass/NamedTuple), `RedundancyPair` (frozen dataclass/NamedTuple), and `ExploratoryFeatureReport` (frozen dataclass/NamedTuple). Implement deterministic `.to_dict()` and `.from_dict()` serialization methods handling IEEE 754 NaN and float representations safely. Add co-located unit tests in `tests/unit/features/test_feature_types.py`.
**Where**: `src/experimental_ml/features/types.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/types.py`, `src/experimental_ml/metrics/types.py`
**Requirement**: EXP-01, EXP-07

**Done when**:
- [x] `SCOPE_EXPLORATORY_FULL_DATA` and `METHODOLOGICAL_WARNINGS` defined as immutable constants
- [x] `AssociationMeasure`, `RedundancyPair`, and `ExploratoryFeatureReport` defined with immutability guarantees
- [x] `.to_dict()` produces pure JSON primitives and `.from_dict()` perfectly reconstructs the original report
- [x] Unit tests pass in `tests/unit/features/test_feature_types.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/features/test_feature_types.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(features): definir modelos de dados e serializacao do relatorio exploratorio (EXP-01, EXP-07)`

---

### Phase 2: Statistical Association Functions (`P1.2`)

#### T2: Implement pure NumPy association metrics with strict degeneracy handling

**What**: Create `src/experimental_ml/features/stats.py` implementing `compute_pearson(x, y)`, `compute_spearman(x, y)` (with fractional ranking for ties), `compute_correlation_ratio(categories, continuous)` ($\eta$), and `compute_cramers_v(cat_x, cat_y)` ($V$) purely in NumPy (`XCUT-02`). Implement guard clauses for zero variance, constant columns, empty or single-class distributions and division by zero returning `(nan, MetricStatus.UNDEFINED_NAN)` in accordance with ADR-005. Add co-located unit tests in `tests/unit/features/test_stats.py`.
**Where**: `src/experimental_ml/features/stats.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/metrics/types.py`
**Requirement**: EXP-02, EXP-03, EXP-04, EXP-05

**Done when**:
- [x] `compute_pearson` and `compute_spearman` pass against standard mathematical definitions and handle ties via average fractional ranks
- [x] `compute_correlation_ratio` calculates $\eta = \sqrt{\text{SS}_{\text{between}} / \text{SS}_{\text{total}}} \in [0, 1]$
- [x] `compute_cramers_v` calculates $V \in [0, 1]$ derived from 2D contingency table
- [x] Zero variance, constant columns and degenerate math return `(nan, MetricStatus.UNDEFINED_NAN)`
- [x] Unit tests pass in `tests/unit/features/test_stats.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/features/test_stats.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(features): implementar metricas estatisticas de associacao em numpy puro (EXP-02, EXP-03, EXP-04, EXP-05)`

---

### Phase 3: Exploratory Relations and Redundancy Engine (`P1.3`)

#### T3: Implement `explore_features` and pairwise predictor redundancy analysis

**What**: Create `src/experimental_ml/features/exploration.py` implementing `explore_features(view, redundancy_threshold=0.85)`. Validate view type (`SanitizedDatasetView`), non-emptiness of candidate features and validity of `redundancy_threshold` in $[0.0, 1.0]$. Dispatch target associations according to task type (`REGRESSION` vs `CLASSIFICATION`) and variable types. Compute the pairwise predictor-predictor redundancy matrix across all candidate features, filter pairs exceeding the threshold ($|r| \ge \text{threshold}$ with $i < j$), and sort canonically by descending magnitude and feature names. Attach mandatory scope `EXPLORATORY_FULL_DATA` and the 3 methodological warnings. Add co-located unit tests in `tests/unit/features/test_exploration.py`.
**Where**: `src/experimental_ml/features/exploration.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/data/types.py`, `src/experimental_ml/core/exceptions.py`, `src/experimental_ml/features/types.py`, `src/experimental_ml/features/stats.py`
**Requirement**: EXP-01, EXP-06, EXP-08

**Done when**:
- [x] Rejects invalid view, non-sanitized input or invalid threshold with `ValidationError` / `ConfigurationError`
- [x] Computes target associations with correct metrics for each feature
- [x] Computes symmetric predictor redundancy matrix and extracts canonically sorted `high_redundancy_pairs`
- [x] Binds `scope = "EXPLORATORY_FULL_DATA"`, `dataset_hash` and mandatory methodological warnings
- [x] Unit tests pass in `tests/unit/features/test_exploration.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/features/test_exploration.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(features): implementar exploracao de relacoes e analise de redundancia (EXP-01, EXP-06, EXP-08)`

---

### Phase 4: Public Exports and Integration Suite (`P1.4`)

#### T4: Expose public module API and implement end-to-end integration tests

**What**: Update `src/experimental_ml/features/__init__.py` to export `explore_features`, `ExploratoryFeatureReport`, `AssociationMeasure`, `RedundancyPair`, `SCOPE_EXPLORATORY_FULL_DATA` and `METHODOLOGICAL_WARNINGS` via `__all__`. Implement `tests/integration/features/test_features_integration.py` exercising the full pipeline from raw data bundle -> profiling -> preparation plan -> sanitized view -> exploratory feature report -> JSON roundtrip, checking dataset hash preservation, and verifying zero external runtime imports (`scipy`, `sklearn` absent from `sys.modules`).
**Where**: `src/experimental_ml/features/__init__.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/data/`, `src/experimental_ml/stages/`
**Requirement**: EXP-01, EXP-02, EXP-03, EXP-04, EXP-05, EXP-06, EXP-07, EXP-08

**Done when**:
- [ ] `__init__.py` exposes public interface with strict `__all__`
- [ ] Integration tests exercise full pipeline with regression and classification datasets
- [ ] Invariance and zero external runtime dependencies verified (`XCUT-02`)
- [ ] Full test suite passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(features): exportar api publica e consolidar suite de integracao do m3-1 (EXP-01 a EXP-08)`

---

## Checks

**C1** - `explore_features` returns `ExploratoryFeatureReport` with `scope = "EXPLORATORY_FULL_DATA"`, `dataset_hash = view.dataset_hash`, and all three mandatory methodological warnings (`EXP-01`, AC 1)  
Proof: run unit | tests/unit/features/test_exploration.py::test_exp_01_mandatory_scope_and_warnings PASSED

**C2** - Continuous-continuous target associations under regression compute valid Pearson $r$ and Spearman $\rho$ with fractional ranking for ties (`EXP-02`, AC 2)  
Proof: run unit | tests/unit/features/test_stats.py::test_exp_02_pearson_and_spearman_continuous PASSED

**C3** - Categorical-continuous associations compute valid Correlation Ratio $\eta$ in $[0, 1]$ for both regression and classification (`EXP-03`, AC 3)  
Proof: run unit | tests/unit/features/test_stats.py::test_exp_03_correlation_ratio_eta PASSED

**C4** - Categorical-categorical associations compute valid Cramér's V in $[0, 1]$ derived from 2D contingency table (`EXP-04`, AC 4)  
Proof: run unit | tests/unit/features/test_stats.py::test_exp_04_cramers_v PASSED

**C5** - Zero variance, constant columns, and degenerate numeric cases return `value = nan` and `status = MetricStatus.UNDEFINED_NAN` without throwing unhandled exceptions (`EXP-05`, AC 5)  
Proof: run unit | tests/unit/features/test_stats.py::test_exp_05_degeneracy_and_undefined_nan PASSED

**C6** - Pairwise predictor redundancy matrix is fully evaluated and `high_redundancy_pairs` contains only pairs with $|r| \ge \text{threshold}$ sorted by descending magnitude and feature names (`EXP-06`, AC 6)  
Proof: run unit | tests/unit/features/test_exploration.py::test_exp_06_predictor_redundancy_and_sorting PASSED

**C7** - `report.to_dict()` and `ExploratoryFeatureReport.from_dict()` perform lossless roundtrip serialization and reconstruction conforming to JSON standards (`EXP-07`, AC 7)  
Proof: run unit | tests/unit/features/test_feature_types.py::test_exp_07_roundtrip_serialization PASSED

**C8** - Full pipeline from dataset loading to sanitized view and feature exploration executes without leaks, preserving dataset hash and zero external dependencies (`EXP-08`, AC 8)  
Proof: run integration | tests/integration/features/test_features_integration.py::test_exp_08_end_to_end_pipeline PASSED

---

## Handoff

**Settled mid-build**: none  
**Dispatched**: none  
**Walked**: pending  

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1
Phase 2:  T2
Phase 3:  T3
Phase 4:  T4
```

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1: Define feature report models, scope constant and serialization contracts | Models, constants and JSON roundtrip | ✅ Granular |
| T2: Implement pure NumPy association metrics with strict degeneracy handling | Math algorithms, ties and degeneracy handling | ✅ Granular |
| T3: Implement `explore_features` and pairwise predictor redundancy analysis | View validation, dispatch, redundancy matrix | ✅ Granular |
| T4: Expose public module API and implement end-to-end integration tests | Public API, pipeline integration and runtime purity | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | Phase 1 root (`T1`) | ✅ Match |
| T2 | T1 | Phase 2 start after Phase 1 (`T2`) | ✅ Match |
| T3 | T2 | Phase 3 start after Phase 2 (`T3`) | ✅ Match |
| T4 | T3 | Phase 4 start after Phase 3 (`T4`) | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1: Define feature report models, scope constant and serialization contracts | Feature Types & Models (`src/experimental_ml/features/types.py`) | unit | unit | ✅ OK |
| T2: Implement pure NumPy association metrics with strict degeneracy handling | Statistical Association Engine (`src/experimental_ml/features/stats.py`) | unit | unit | ✅ OK |
| T3: Implement `explore_features` and pairwise predictor redundancy analysis | Exploration Engine & Redundancy (`src/experimental_ml/features/exploration.py`) | unit | unit | ✅ OK |
| T4: Expose public module API and implement end-to-end integration tests | Features Integration & Invariants (`tests/integration/features/test_features_integration.py`) | integration | integration | ✅ OK |
