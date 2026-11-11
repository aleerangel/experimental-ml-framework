# m4-3-nested-tuning Tasks (M4.3 Otimização de Hiperparâmetros Aninhada Intra-Fold)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m4-3-nested-tuning/design.md`  
**Status**: Approved  
**Approved**: 2026-11-11 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/tuning/ -v  
**Run integration**: .venv/bin/pytest tests/integration/tuning/ -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001` a `AD-006`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 7 requirements (`TUN-01` to `TUN-07`) and transversal invariants (`ADR-003`, `ADR-005`, `XCUT-02`).

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Tuning Types & Enums (`src/experimental_ml/tuning/types.py`) | unit | 1:1 AC mapping: SearchStrategy enum, HyperparameterSearchSpec, TuningTrialRecord, TuningResult, TuningOptimizationError | `tests/unit/tuning/test_tuning_types.py` | `.venv/bin/pytest tests/unit/tuning/test_tuning_types.py -v` |
| Declarative Validation (`src/experimental_ml/tuning/validation.py`) | unit | 1:1 AC mapping: validate_search_spec constraint enforcement, METRICS_CATALOG direction checks, inner folds | `tests/unit/tuning/test_tuning_validation.py` | `.venv/bin/pytest tests/unit/tuning/test_tuning_validation.py -v` |
| Candidate Generation (`src/experimental_ml/tuning/candidates.py`) | unit | 1:1 AC mapping: Cartesian product grid search, deterministic seed sampling random search, fixed single candidate | `tests/unit/tuning/test_tuning_candidates.py` | `.venv/bin/pytest tests/unit/tuning/test_tuning_candidates.py -v` |
| Inner Fold Partitioning (`src/experimental_ml/tuning/partitioning.py`) | unit | 1:1 AC mapping: Disjoint fold index splitting, anti-leakage training-only index range, N < K_inner rejection | `tests/unit/tuning/test_tuning_partitioning.py` | `.venv/bin/pytest tests/unit/tuning/test_tuning_partitioning.py -v` |
| Nested CV Engine (`src/experimental_ml/tuning/engine.py`) | unit | 1:1 AC mapping: run_nested_tuning multi-fold execution, fresh instances, direction optimization, tie-breaking | `tests/unit/tuning/test_tuning_execution.py` | `.venv/bin/pytest tests/unit/tuning/test_tuning_execution.py -v` |
| Robustness & Failures (`src/experimental_ml/tuning/engine.py`) | unit | 1:1 AC mapping: UNDEFINED_NAN disqualification, TuningOptimizationError on total failure, detail preservation | `tests/unit/tuning/test_tuning_failures.py` | `.venv/bin/pytest tests/unit/tuning/test_tuning_failures.py -v` |
| Tuning Integration & Runtime Purity (`tests/integration/tuning/test_tuning_integration.py`) | integration | Full nested CV pipeline execution, single runtime dependency (numpy>=1.24.0, zero external tuning imports) | `tests/integration/tuning/test_tuning_integration.py` | `.venv/bin/pytest tests/integration/tuning/test_tuning_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After tasks with unit tests in tuning | `.venv/bin/pytest tests/unit/tuning/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Declarative Specifications and Search Validation (`P1`)

Define domain enumerations (`SearchStrategy`), immutable specifications (`HyperparameterSearchSpec`, `TuningTrialRecord`, `TuningResult`, `TuningOptimizationError`), and pure validation logic rejecting invalid spaces or metric directions (`TUN-01`, `TUN-02`).

```
T1 --> T2
```

### Phase 2: Candidate Generation and Inner Partitioning (`P2`)

Implement deterministic parameter candidate generation for grid and random search (`TUN-03`), and pure NumPy inner fold partitioning strictly confined to outer training data (`TUN-04`).

```
T3 --> T4
```

### Phase 3: Nested Cross-Validation Engine and Robustness (`P3`)

Implement `run_nested_tuning` evaluating fresh model instances across inner folds (`TUN-05`), enforcing strict `UNDEFINED_NAN` disqualification and `TuningOptimizationError` upon total search failure (`TUN-06`).

```
T5 --> T6
```

### Phase 4: Public API Exports and Transversal Integration Suite (`P4`)

Expose public module API in `src/experimental_ml/tuning/__init__.py`, execute end-to-end integration tests, and verify runtime purity without external tuning frameworks (`TUN-07`).

```
T7
```

---

## Task Breakdown

### Phase 1: Declarative Specifications and Search Validation (`P1`)

#### T1: Define SearchStrategy enum, HyperparameterSearchSpec, TuningTrialRecord, TuningResult and TuningOptimizationError

**What**: Create `src/experimental_ml/tuning/types.py` defining `SearchStrategy` as a closed `str, Enum` with members `FIXED`, `GRID_SEARCH`, `RANDOM_SEARCH`, and `CUSTOM_TUNER`. Define `HyperparameterSearchSpec` as an immutable frozen dataclass with slots containing `search_strategy`, `param_grid`, `optimization_metric`, `direction`, `n_iter`, `inner_cv_folds`, `seed`, and `description`. Define `TuningTrialRecord` as an immutable frozen dataclass with slots containing `trial_index`, `params`, `fold_scores`, `mean_score`, `status`, and `error_message`. Define `TuningResult` as an immutable frozen dataclass with slots containing `best_params`, `best_score`, `best_trial_index`, `trials`, `search_strategy`, and `optimization_metric`. Define `TuningOptimizationError` inheriting from `ContractViolationError`. Add co-located unit tests in `tests/unit/tuning/test_tuning_types.py`.
**Where**: `src/experimental_ml/tuning/types.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/findings.py`, `src/experimental_ml/core/types.py`
**Requirement**: TUN-01

**Done when**:
- [x] `SearchStrategy` defines all 4 canonical members
- [x] `HyperparameterSearchSpec`, `TuningTrialRecord`, and `TuningResult` defined with `frozen=True` and `slots=True`
- [x] `TuningOptimizationError` inherits from `ContractViolationError`
- [x] Unit tests pass in `tests/unit/tuning/test_tuning_types.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/tuning/test_tuning_types.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(tuning): definir enums, especificacoes de busca e estruturas de resultado (TUN-01)`

---

#### T2: Implement validate_search_spec declarative validation

**What**: Create `src/experimental_ml/tuning/validation.py` implementing `validate_search_spec(spec: HyperparameterSearchSpec, metric_catalog=METRICS_CATALOG) -> HyperparameterSearchSpec`. Validate that `inner_cv_folds >= 2` and is an integer. Validate that `optimization_metric` exists in the catalog and its declared direction matches the metric's catalog direction. Validate that if `search_strategy` is `RANDOM_SEARCH`, `n_iter` is a positive integer. Validate that for `GRID_SEARCH`, `param_grid` contains non-empty sequences. Raise `ConfigurationError` on any validation failure. Add co-located unit tests in `tests/unit/tuning/test_tuning_validation.py`.
**Where**: `src/experimental_ml/tuning/validation.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/tuning/types.py`, `src/experimental_ml/metrics/catalog.py`, `src/experimental_ml/core/findings.py`
**Requirement**: TUN-02

**Done when**:
- [x] `validate_search_spec` validates valid search specifications without error
- [x] `inner_cv_folds < 2` or non-integer folds raise `ConfigurationError`
- [x] Unknown metrics or conflicting metric directions raise `ConfigurationError`
- [x] Non-positive `n_iter` in `RANDOM_SEARCH` raises `ConfigurationError`
- [x] Unit tests pass in `tests/unit/tuning/test_tuning_validation.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/tuning/test_tuning_validation.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(tuning): implementar validacao declarativa de espacos de busca e metricas (TUN-02)`

---

### Phase 2: Candidate Generation and Inner Partitioning (`P2`)

#### T3: Implement deterministic hyperparameter candidate generation

**What**: Create `src/experimental_ml/tuning/candidates.py` implementing `generate_candidates(spec: HyperparameterSearchSpec) -> tuple[MappingProxyType[str, Any], ...]`. For `FIXED`, return exactly one candidate mapping derived from `param_grid`. For `GRID_SEARCH`, generate the complete Cartesian product of all parameter values in deterministic lexicographical key order. For `RANDOM_SEARCH`, sample exactly `n_iter` parameter combinations deterministically using `np.random.default_rng(spec.seed)`. Wrap all returned candidate mappings in `MappingProxyType`. Add co-located unit tests in `tests/unit/tuning/test_tuning_candidates.py`.
**Where**: `src/experimental_ml/tuning/candidates.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/tuning/types.py`
**Requirement**: TUN-03

**Done when**:
- [x] `GRID_SEARCH` produces deterministic Cartesian product of parameter combinations
- [x] `RANDOM_SEARCH` samples exactly `n_iter` candidates deterministically with seed
- [x] `FIXED` produces a single candidate mapping
- [x] Unit tests pass in `tests/unit/tuning/test_tuning_candidates.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/tuning/test_tuning_candidates.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(tuning): implementar geracao deterministica de candidatos de hiperparametros (TUN-03)`

---

#### T4: Implement pure NumPy inner fold index partitioning

**What**: Create `src/experimental_ml/tuning/partitioning.py` implementing `split_inner_folds(n_samples: int, n_folds: int, seed: int | None = None, shuffle: bool = False) -> tuple[tuple[np.ndarray, np.ndarray], ...]`. Validate that `n_samples >= n_folds >= 2`, raising `ContractViolationError` if $N < K_{\text{inner}}$. Partition index range $0 \dots N-1$ into $K_{\text{inner}}$ folds such that $\text{Train}_{\text{inner}} \cap \text{Val}_{\text{inner}} = \emptyset$ for every fold and the union of validation folds covers all indices. Ensure partitioning depends strictly on training sample count $N$ without referencing any evaluation data (`CA-E4B-01`). Add co-located unit tests in `tests/unit/tuning/test_tuning_partitioning.py`.
**Where**: `src/experimental_ml/tuning/partitioning.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/core/findings.py`
**Requirement**: TUN-04

**Done when**:
- [ ] `split_inner_folds` partitions indices $0 \dots N-1$ into $K$ disjoint fold pairs
- [ ] Validation sets across folds form a complete partition of training indices
- [ ] $N < K_{\text{inner}}$ raises `ContractViolationError`
- [ ] Unit tests pass in `tests/unit/tuning/test_tuning_partitioning.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/tuning/test_tuning_partitioning.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(tuning): implementar particionamento interno puro em numpy sem vazamento (TUN-04)`

---

### Phase 3: Nested Cross-Validation Engine and Robustness (`P3`)

#### T5: Implement run_nested_tuning execution and metric optimization

**What**: Create `src/experimental_ml/tuning/engine.py` implementing `run_nested_tuning(spec: HyperparameterSearchSpec, model_spec: ModelSpec, X_train: np.ndarray, y_train: np.ndarray, seed: int | None = None) -> TuningResult`. Validate inputs ($X_{\text{train}}$ 2D, $y_{\text{train}}$ 1D, matching length $N$). Generate candidates and inner splits. For each candidate and inner fold, instantiate a fresh estimator instance via `instantiate_fresh_model`, fit on inner training partition, predict on inner validation partition, and evaluate the target metric via `METRICS_CATALOG[spec.optimization_metric]`. Compute mean fold score and select the winning candidate $\theta^*$ according to `spec.direction` (`MAXIMIZE` or `MINIMIZE`), resolving exact score ties deterministically by selecting the lowest trial index. Add co-located unit tests in `tests/unit/tuning/test_tuning_execution.py`.
**Where**: `src/experimental_ml/tuning/engine.py`
**Depends on**: T4
**Reuses**: `src/experimental_ml/tuning/types.py`, `src/experimental_ml/tuning/candidates.py`, `src/experimental_ml/tuning/partitioning.py`, `src/experimental_ml/models/execution.py`, `src/experimental_ml/metrics/catalog.py`
**Requirement**: TUN-05

**Done when**:
- [ ] `run_nested_tuning` evaluates candidates across inner folds using fresh model instances
- [ ] Inner fold scores are computed via `METRICS_CATALOG` and aggregated as arithmetic mean
- [ ] Winning candidate $\theta^*$ selected by declared direction with deterministic tie-breaking
- [ ] Unit tests pass in `tests/unit/tuning/test_tuning_execution.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/tuning/test_tuning_execution.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(tuning): implementar motor de nested cross-validation e selecao de parametros (TUN-05)`

---

#### T6: Implement strict undefined metric handling and total failure exception

**What**: In `src/experimental_ml/tuning/engine.py`, enforce ADR-005 rules: if any inner fold produces `MetricStatus.UNDEFINED_NAN` or non-finite values, mark that trial's status as `UNDEFINED_NAN` and disqualify it from winning over any valid candidate. If all evaluated candidates fail, encounter fit/predict exceptions, or produce `UNDEFINED_NAN`, raise `TuningOptimizationError` with trial details without coercing scores to zero. Add co-located unit tests in `tests/unit/tuning/test_tuning_failures.py`.
**Where**: `src/experimental_ml/tuning/engine.py`
**Depends on**: T5
**Reuses**: `src/experimental_ml/tuning/types.py`, `src/experimental_ml/core/types.py`
**Requirement**: TUN-06

**Done when**:
- [ ] Trials producing `UNDEFINED_NAN` in any fold are disqualified from beating valid candidates
- [ ] Total failure across all candidates raises `TuningOptimizationError`
- [ ] `TuningOptimizationError` preserves diagnostic details and inherits from `ContractViolationError`
- [ ] Unit tests pass in `tests/unit/tuning/test_tuning_failures.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/tuning/test_tuning_failures.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(tuning): implementar desqualificacao por undefined_nan e excecao de falha total (TUN-06)`

---

### Phase 4: Public API Exports and Transversal Integration Suite (`P4`)

#### T7: Expose public module API and implement transversal integration tests

**What**: Create `src/experimental_ml/tuning/__init__.py` exporting all public symbols via `__all__`. Implement transversal integration tests in `tests/integration/tuning/test_tuning_integration.py` exercising the full nested cross-validation pipeline with classical regression/classification baselines, verifying anti-leakage invariance (altering outer test set produces identical $\theta^*$), determinism under explicit seed, and runtime purity (`XCUT-02`) via subprocess inspection asserting zero mandatory imports of third-party tuning libraries (Optuna, Scikit-Learn GridSearchCV, Ray Tune).
**Where**: `src/experimental_ml/tuning/__init__.py`
**Depends on**: T6
**Reuses**: `src/experimental_ml/tuning/types.py`, `src/experimental_ml/tuning/validation.py`, `src/experimental_ml/tuning/engine.py`
**Requirement**: TUN-07

**Done when**:
- [ ] `tuning/__init__.py` cleanly exports public API in `__all__`
- [ ] End-to-end integration tests execute full nested tuning lifecycle
- [ ] Subprocess inspection asserts runtime purity without external tuning imports
- [ ] Integration tests pass in `tests/integration/tuning/test_tuning_integration.py`
- [ ] Full gate check passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(tuning): expor API publica e implementar suite de integracao transversal (TUN-07)`

---

## Checks

**Run unit**: .venv/bin/pytest tests/unit/tuning/ -v  
**Run integration**: .venv/bin/pytest tests/integration/tuning/ -v  

**C1** - `SearchStrategy` is defined as a closed `str, Enum` with all 4 canonical members (`TUN-01`, AC 1)  
Proof: run unit | tests/unit/tuning/test_tuning_types.py::test_m43_01_01_search_strategy_enum PASSED

**C2** - `HyperparameterSearchSpec` is defined as an immutable frozen dataclass with slots (`TUN-01`, AC 2)  
Proof: run unit | tests/unit/tuning/test_tuning_types.py::test_m43_01_02_search_spec_dataclass PASSED

**C3** - `TuningTrialRecord` is defined as an immutable frozen dataclass with slots (`TUN-01`, AC 3)  
Proof: run unit | tests/unit/tuning/test_tuning_types.py::test_m43_01_03_trial_record_dataclass PASSED

**C4** - `TuningResult` is defined as an immutable frozen dataclass with slots (`TUN-01`, AC 4)  
Proof: run unit | tests/unit/tuning/test_tuning_types.py::test_m43_01_04_tuning_result_dataclass PASSED

**C5** - `TuningOptimizationError` inherits from `ContractViolationError` (`TUN-01`, AC 2, 4)  
Proof: run unit | tests/unit/tuning/test_tuning_types.py::test_m43_01_05_tuning_error_inheritance PASSED

**C6** - `validate_search_spec` validates valid search specifications without mutating fields (`TUN-02`, AC 1)  
Proof: run unit | tests/unit/tuning/test_tuning_validation.py::test_m43_02_01_validate_search_spec_valid PASSED

**C7** - `validate_search_spec` raises `ConfigurationError` when inner_cv_folds < 2 (`TUN-02`, AC 2)  
Proof: run unit | tests/unit/tuning/test_tuning_validation.py::test_m43_02_02_validate_search_spec_invalid_folds PASSED

**C8** - `validate_search_spec` raises `ConfigurationError` on unknown metric or conflicting direction (`TUN-02`, AC 3)  
Proof: run unit | tests/unit/tuning/test_tuning_validation.py::test_m43_02_03_validate_search_spec_metric_direction PASSED

**C9** - `validate_search_spec` raises `ConfigurationError` on non-positive n_iter for random search (`TUN-02`, AC 4)  
Proof: run unit | tests/unit/tuning/test_tuning_validation.py::test_m43_02_04_validate_search_spec_random_n_iter PASSED

**C10** - `generate_candidates` produces deterministic Cartesian product for grid search (`TUN-03`, AC 1)  
Proof: run unit | tests/unit/tuning/test_tuning_candidates.py::test_m43_03_01_grid_search_cartesian_product PASSED

**C11** - `generate_candidates` samples exactly n_iter candidates deterministically with seed (`TUN-03`, AC 2)  
Proof: run unit | tests/unit/tuning/test_tuning_candidates.py::test_m43_03_02_random_search_seed_determinism PASSED

**C12** - `generate_candidates` produces a single candidate mapping for fixed strategy (`TUN-03`, AC 3)  
Proof: run unit | tests/unit/tuning/test_tuning_candidates.py::test_m43_03_03_fixed_strategy_single_candidate PASSED

**C13** - `split_inner_folds` partitions indices into disjoint inner folds (`TUN-04`, AC 1)  
Proof: run unit | tests/unit/tuning/test_tuning_partitioning.py::test_m43_04_01_split_inner_folds_disjointness PASSED

**C14** - `split_inner_folds` operates strictly on training indices without external leakage (`TUN-04`, AC 2)  
Proof: run unit | tests/unit/tuning/test_tuning_partitioning.py::test_m43_04_02_split_inner_folds_training_confinement PASSED

**C15** - `split_inner_folds` raises `ContractViolationError` when N < K_inner (`TUN-04`, AC 3)  
Proof: run unit | tests/unit/tuning/test_tuning_partitioning.py::test_m43_04_03_split_inner_folds_insufficient_samples PASSED

**C16** - `run_nested_tuning` instantiates fresh model instances per candidate and inner fold (`TUN-05`, AC 1)  
Proof: run unit | tests/unit/tuning/test_tuning_execution.py::test_m43_05_01_fresh_model_instances_per_fold PASSED

**C17** - `run_nested_tuning` computes internal fold metrics via catalog and aggregates mean (`TUN-05`, AC 2)  
Proof: run unit | tests/unit/tuning/test_tuning_execution.py::test_m43_05_02_metric_computation_and_aggregation PASSED

**C18** - `run_nested_tuning` selects winning candidate by declared direction with deterministic tie-breaking (`TUN-05`, AC 3)  
Proof: run unit | tests/unit/tuning/test_tuning_execution.py::test_m43_05_03_direction_selection_and_tie_breaking PASSED

**C19** - `run_nested_tuning` marks candidates producing UNDEFINED_NAN as disqualified (`TUN-06`, AC 1)  
Proof: run unit | tests/unit/tuning/test_tuning_failures.py::test_m43_06_01_undefined_nan_disqualification PASSED

**C20** - `run_nested_tuning` raises `TuningOptimizationError` when all candidates fail (`TUN-06`, AC 2)  
Proof: run unit | tests/unit/tuning/test_tuning_failures.py::test_m43_06_02_all_candidates_fail_raises_error PASSED

**C21** - `TuningOptimizationError` preserves diagnostic details and inherits from `ContractViolationError` (`TUN-06`, AC 3)  
Proof: run unit | tests/unit/tuning/test_tuning_failures.py::test_m43_06_03_error_preserves_trial_details PASSED

**C22** - Tuning subsystem cleanly exports public API via __all__ (`TUN-07`, AC 1)  
Proof: run integration | tests/integration/tuning/test_tuning_integration.py::test_m43_07_01_public_api_exports PASSED

**C23** - Tuning subsystem maintains single runtime dependency (numpy>=1.24.0) with zero external ML imports (`TUN-07`, AC 2)  
Proof: run integration | tests/integration/tuning/test_tuning_integration.py::test_m43_07_02_runtime_purity_numpy_only PASSED

**C24** - End-to-end integration test verifies full nested cross-validation tuning lifecycle (`TUN-07`, AC 1)  
Proof: run integration | tests/integration/tuning/test_tuning_integration.py::test_m43_07_03_end_to_end_tuning_lifecycle PASSED

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
| T1: Define SearchStrategy enum, HyperparameterSearchSpec, TuningTrialRecord, TuningResult and TuningOptimizationError | Tuning types, enums and specs | ✅ Granular |
| T2: Implement validate_search_spec declarative validation | Declarative validation against metrics catalog | ✅ Granular |
| T3: Implement deterministic hyperparameter candidate generation | Grid, random and fixed candidate generation | ✅ Granular |
| T4: Implement pure NumPy inner fold index partitioning | NumPy inner fold partitioning and validation | ✅ Granular |
| T5: Implement run_nested_tuning execution and metric optimization | Nested cross-validation execution engine | ✅ Granular |
| T6: Implement strict undefined metric handling and total failure exception | UNDEFINED_NAN disqualification and total failure error | ✅ Granular |
| T7: Expose public module API and implement transversal integration tests | __init__.py, public exports, runtime purity, integration pipeline | ✅ Granular |

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
| T1: Define SearchStrategy enum, HyperparameterSearchSpec, TuningTrialRecord, TuningResult and TuningOptimizationError | Tuning Types & Enums (`src/experimental_ml/tuning/types.py`) | unit | unit | ✅ OK |
| T2: Implement validate_search_spec declarative validation | Declarative Validation (`src/experimental_ml/tuning/validation.py`) | unit | unit | ✅ OK |
| T3: Implement deterministic hyperparameter candidate generation | Candidate Generation (`src/experimental_ml/tuning/candidates.py`) | unit | unit | ✅ OK |
| T4: Implement pure NumPy inner fold index partitioning | Inner Fold Partitioning (`src/experimental_ml/tuning/partitioning.py`) | unit | unit | ✅ OK |
| T5: Implement run_nested_tuning execution and metric optimization | Nested CV Engine (`src/experimental_ml/tuning/engine.py`) | unit | unit | ✅ OK |
| T6: Implement strict undefined metric handling and total failure exception | Robustness & Failures (`src/experimental_ml/tuning/engine.py`) | unit | unit | ✅ OK |
| T7: Expose public module API and implement transversal integration tests | Tuning Integration & Runtime Purity (`tests/integration/tuning/test_tuning_integration.py`) | integration | integration | ✅ OK |
