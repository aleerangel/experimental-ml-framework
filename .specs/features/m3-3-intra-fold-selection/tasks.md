# m3-3-intra-fold-selection Tasks (M3.3 Seleção Dinâmica Intra-Fold de Features e Estabilidade)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m3-3-intra-fold-selection/design.md`  
**Status**: Approved  
**Approved**: 2026-11-10 - user: "prossiga para o m3.3"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/features/test_selection.py tests/unit/features/test_stability.py -v  
**Run integration**: .venv/bin/pytest tests/integration/features/test_selection_integration.py -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001` a `AD-004`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 8 requirements (`SEL-01` to `SEL-08`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Intra-Fold Selection Engine (`src/experimental_ml/features/selection.py`) | unit | 1:1 AC mapping: SelectionResult frozen slots, FIXED bypass, VARIANCE_THRESHOLD, TOP_K_RELEVANCE, empty selection rejection | `tests/unit/features/test_selection.py` | `.venv/bin/pytest tests/unit/features/test_selection.py -v` |
| Evaluation Feature Projection (`src/experimental_ml/features/selection.py`) | unit | 1:1 AC mapping: apply_feature_selection column filtering, order preservation, missing column ContractViolationError | `tests/unit/features/test_selection.py` | `.venv/bin/pytest tests/unit/features/test_selection.py -v` |
| Selection Stability Metrics (`src/experimental_ml/features/stability.py`) | unit | 1:1 AC mapping: pairwise Jaccard, Kuncheva chance-corrected index, boundary edge cases, report serialization | `tests/unit/features/test_stability.py` | `.venv/bin/pytest tests/unit/features/test_stability.py -v` |
| Selection Integration & Invariants (`tests/integration/features/test_selection_integration.py`) | integration | Multi-fold selection workflow, leakage-free evaluation filtering, stability reporting, runtime purity (XCUT-02) | `tests/integration/features/test_selection_integration.py` | `.venv/bin/pytest tests/integration/features/test_selection_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After tasks with unit tests in selection or stability | `.venv/bin/pytest tests/unit/features/test_selection.py tests/unit/features/test_stability.py -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Selection Engine and Dispatcher (`P1.1`)

Define `SelectionResult` model and implement `select_features_in_fold` supporting `FIXED` bypass and dynamic strategies (`VARIANCE_THRESHOLD`, `TOP_K_RELEVANCE`).

```
T1
```

### Phase 2: Evaluation Projection Engine (`P1.2`)

Implement `apply_feature_selection` projecting fitted selection onto evaluation sets without data leakage.

```
T2
```

### Phase 3: Selection Stability Metrics (`P1.3`)

Implement `SelectionStabilityReport` and `compute_selection_stability` computing pairwise Jaccard and Kuncheva indices across multiple folds.

```
T3
```

### Phase 4: Public Exports and Integration Suite (`P1.4`)

Expose public API in `features/__init__.py`, execute end-to-end multi-fold integration tests, and verify runtime purity without SciPy/Scikit-Learn.

```
T4
```

---

## Task Breakdown

### Phase 1: Selection Engine and Dispatcher (`P1.1`)

#### T1: Implement `SelectionResult` and `select_features_in_fold`

**What**: Create `src/experimental_ml/features/selection.py` defining `SelectionResult(frozen=True, slots=True)` with `selected_features: tuple[str, ...]`, `scores: Mapping[str, float]`, `fitted_params: Mapping[str, Any]`, and `strategy_name: str`. Implement `.to_dict()` and `.from_dict()`. Implement `select_features_in_fold(X_train, y_train, scenario, random_state=None)`. If `scenario.mode == "FIXED"`, return `scenario.selected_features` immediately without touching `y_train`. If `scenario.mode == "DYNAMIC"`, dispatch to `VARIANCE_THRESHOLD` (filtering numeric features with sample variance > threshold) or `TOP_K_RELEVANCE` (ranking top-k features by association with `y_train`). Raise `DataIntegrityError` if 0 features are selected. Add co-located unit tests in `tests/unit/features/test_selection.py`.
**Where**: `src/experimental_ml/features/selection.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/features/scenarios.py`, `src/experimental_ml/features/stats.py`, `src/experimental_ml/core/findings.py`
**Requirement**: SEL-01, SEL-02, SEL-03, SEL-04, SEL-07

**Done when**:
- [x] `SelectionResult` defined with frozen slots and mapping proxies
- [x] `select_features_in_fold` bypasses calculations for `FIXED` scenarios
- [x] `VARIANCE_THRESHOLD` and `TOP_K_RELEVANCE` execute strictly on training data
- [x] Rejects empty selections with `DataIntegrityError`
- [x] Unit tests pass in `tests/unit/features/test_selection.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/features/test_selection.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(features): implementar modelo SelectionResult e motor select_features_in_fold (SEL-01 a SEL-04, SEL-07)`

---

### Phase 2: Evaluation Projection Engine (`P1.2`)

#### T2: Implement `apply_feature_selection` for evaluation data

**What**: In `src/experimental_ml/features/selection.py`, implement `apply_feature_selection(X_eval, selection_result)`. Validate that `X_eval` contains all features in `selection_result.selected_features` (raise `ContractViolationError` if any column is missing). Return a dictionary of arrays containing strictly the selected features in the exact order specified by `selection_result.selected_features`. Add co-located unit tests in `tests/unit/features/test_selection.py`.
**Where**: `src/experimental_ml/features/selection.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/core/findings.py`
**Requirement**: SEL-05

**Done when**:
- [x] `apply_feature_selection` filters columns matching `selected_features` in order
- [x] Raises `ContractViolationError` when any selected feature is missing from evaluation data
- [x] Preserves array immutability and underlying buffers
- [x] Unit tests pass in `tests/unit/features/test_selection.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/features/test_selection.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(features): implementar projecao de atributos apply_feature_selection (SEL-05)`

---

### Phase 3: Selection Stability Metrics (`P1.3`)

#### T3: Implement `compute_selection_stability` and report model

**What**: Create `src/experimental_ml/features/stability.py` defining `SelectionStabilityReport(frozen=True, slots=True)` with `mean_jaccard`, `std_jaccard`, `mean_kuncheva`, `std_kuncheva`, pairwise matrices, `n_folds`, and `n_total_candidates`. Implement `.to_dict()` and `.from_dict()`. Implement `compute_selection_stability(fold_selections, n_total_candidates)`. Validate $K \ge 2$ folds and $N \ge 1$ candidates. Compute pairwise Jaccard similarities and chance-corrected Kuncheva consistency indices: $K(S_i, S_j) = \frac{r \cdot N - k_i \cdot k_j}{\sqrt{k_i \cdot k_j \cdot (N - k_i) \cdot (N - k_j)}}$ with safe handling for edge cases ($k=0, k=N$). Add co-located unit tests in `tests/unit/features/test_stability.py`.
**Where**: `src/experimental_ml/features/stability.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/core/findings.py`
**Requirement**: SEL-06

**Done when**:
- [x] `SelectionStabilityReport` defined with immutability and JSON roundtrip
- [x] `compute_selection_stability` computes Jaccard and Kuncheva index across folds
- [x] Correctly handles chance correction (returning ~0 for random and 1.0 for identical sets)
- [x] Unit tests pass in `tests/unit/features/test_stability.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/features/test_stability.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(features): implementar metricas de estabilidade de selecao Jaccard e Kuncheva (SEL-06)`

---

### Phase 4: Public Exports and Integration Suite (`P1.4`)

#### T4: Expose public module API and implement multi-fold integration tests

**What**: In `src/experimental_ml/features/__init__.py`, export `select_features_in_fold`, `apply_feature_selection`, `SelectionResult`, `compute_selection_stability`, `SelectionStabilityReport` in `__all__`. Create `tests/integration/features/test_selection_integration.py` simulating cross-validation folds: for each fold, partition data, execute `select_features_in_fold` on training split, apply `apply_feature_selection` to validation split, measure selection stability across folds, and verify zero runtime dependencies outside NumPy (`XCUT-02`).
**Where**: `src/experimental_ml/features/__init__.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/data/`, `src/experimental_ml/features/`, `src/experimental_ml/validation/`
**Requirement**: SEL-01, SEL-02, SEL-03, SEL-04, SEL-05, SEL-06, SEL-07, SEL-08

**Done when**:
- [ ] Public symbols exported in `features/__init__.py`
- [ ] Integration suite verifies cross-fold feature selection, evaluation projection and stability calculation
- [ ] Subprocess test proves absence of external ML libraries in `sys.modules` (`XCUT-02`)
- [ ] Full test suite passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(features): exportar api publica e consolidar suite de integracao do m3-3 (SEL-01 a SEL-08)`

---

## Checks

**C1** - `select_features_in_fold` returns immutable `SelectionResult` with selected features, scores, fitted parameters, and strategy name (`SEL-01`, AC 1)  
Proof: run unit | tests/unit/features/test_selection.py::test_sel_01_selection_result_immutability PASSED

**C2** - Fixed scenarios immediately return `selected_features` without computing statistics or requiring `y_train` (`SEL-02`, AC 2)  
Proof: run unit | tests/unit/features/test_selection.py::test_sel_02_fixed_scenario_bypass PASSED

**C3** - Dynamic scenario with `VARIANCE_THRESHOLD` selects features exceeding threshold strictly on training data (`SEL-03`, AC 3)  
Proof: run unit | tests/unit/features/test_selection.py::test_sel_03_variance_threshold_selection PASSED

**C4** - Dynamic scenario with `TOP_K_RELEVANCE` ranks and selects top-k features by association with `y_train` (`SEL-04`, AC 4)  
Proof: run unit | tests/unit/features/test_selection.py::test_sel_04_top_k_relevance_selection PASSED

**C5** - `apply_feature_selection` projects selected features onto evaluation data in exact order, rejecting missing columns (`SEL-05`, AC 5)  
Proof: run unit | tests/unit/features/test_selection.py::test_sel_05_apply_feature_selection PASSED

**C6** - `compute_selection_stability` computes pairwise Jaccard and chance-corrected Kuncheva consistency indices across folds (`SEL-06`, AC 6)  
Proof: run unit | tests/unit/features/test_stability.py::test_sel_06_selection_stability_metrics PASSED

**C7** - Dynamic selection resulting in 0 features raises `DataIntegrityError` to prevent empty downstream inputs (`SEL-07`, AC 7)  
Proof: run unit | tests/unit/features/test_selection.py::test_sel_07_empty_selection_rejection PASSED

**C8** - Full multi-fold selection pipeline executes without leakage and complies with zero external runtime dependencies (`SEL-08`, AC 8)  
Proof: run integration | tests/integration/features/test_selection_integration.py::test_sel_08_multi_fold_selection_pipeline PASSED

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
| T1: Implement `SelectionResult` and `select_features_in_fold` | Selection model, FIXED bypass, dynamic strategies | ✅ Granular |
| T2: Implement `apply_feature_selection` for evaluation data | Evaluation projection, ordering, missing column validation | ✅ Granular |
| T3: Implement `compute_selection_stability` and report model | Stability report model, Jaccard and Kuncheva indices | ✅ Granular |
| T4: Expose public module API and implement multi-fold integration tests | Public exports, multi-fold pipeline, runtime purity | ✅ Granular |

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
| T1: Implement `SelectionResult` and `select_features_in_fold` | Intra-Fold Selection Engine (`src/experimental_ml/features/selection.py`) | unit | unit | ✅ OK |
| T2: Implement `apply_feature_selection` for evaluation data | Evaluation Feature Projection (`src/experimental_ml/features/selection.py`) | unit | unit | ✅ OK |
| T3: Implement `compute_selection_stability` and report model | Selection Stability Metrics (`src/experimental_ml/features/stability.py`) | unit | unit | ✅ OK |
| T4: Expose public module API and implement multi-fold integration tests | Selection Integration & Invariants (`tests/integration/features/test_selection_integration.py`) | integration | integration | ✅ OK |
