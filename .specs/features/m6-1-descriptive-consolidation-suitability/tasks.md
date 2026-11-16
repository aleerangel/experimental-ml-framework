# m6-1-descriptive-consolidation-suitability Tasks (M6.1 Consolidação Descritiva e Adequação Metodológica)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m6-1-descriptive-consolidation-suitability/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-16 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/statistics/ tests/integration/statistics/ -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `engenharia_software/ESPECIFICACAO_REQUISITOS.md`, `engenharia_software/ARQUITETURA_E_CONTRATOS.md`, `pyproject.toml`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Statistics Types & Enums (`src/experimental_ml/statistics/types.py`) | unit | 1:1 AC mapping: CoverageStatus, IncompleteComparisonPolicy, ApplicabilityStatus, AggregatedMetricStats, AggregatedTimingStats, ConfigurationSummary, DescriptiveConsolidation, MethodSuitabilityReport | `tests/unit/statistics/test_types.py` | `.venv/bin/pytest tests/unit/statistics/test_types.py -v` |
| Stage 5 Entry Gate (`src/experimental_ml/statistics/consolidation.py`) | unit | 1:1 AC mapping: validate_stage5_entry, rejection of PENDING/RUNNING, rejection of completed_cells == 0, acceptance of COMPLETED/FAILED/CANCELLED with completed >= 1 | `tests/unit/statistics/test_stage5_entry.py` | `.venv/bin/pytest tests/unit/statistics/test_stage5_entry.py -v` |
| Descriptive Consolidation Engine (`src/experimental_ml/statistics/consolidation.py`) | unit | 1:1 AC mapping: consolidate_descriptive, coverage calculation, missing folds tracking, sample std with ddof=1, median, IQR, n_valid handling (0, 1, >=2), timing aggregation, feature stability | `tests/unit/statistics/test_consolidation.py` | `.venv/bin/pytest tests/unit/statistics/test_consolidation.py -v` |
| Methodological Suitability & Incompleteness (`src/experimental_ml/statistics/suitability.py`) | unit | 1:1 AC mapping: evaluate_method_suitability, check_pairwise_comparison_eligibility, CV overlap ratios r, Nadeau-Bengio applicability, Wilcoxon J < 6 warning, holdout único multi-fold rejection, standard t rejection | `tests/unit/statistics/test_suitability.py` | `.venv/bin/pytest tests/unit/statistics/test_suitability.py -v` |
| Statistics Integration & Purity (`tests/integration/statistics/test_statistics_integration.py`) | integration | End-to-end integration of Stage 4 artifacts ingestion, descriptive summary generation, suitability reporting, runtime purity (numpy>=1.24.0, zero external imports) | `tests/integration/statistics/test_statistics_integration.py` | `.venv/bin/pytest tests/integration/statistics/test_statistics_integration.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After tasks with unit tests in statistics | `.venv/bin/pytest tests/unit/statistics/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/unit/statistics/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Domain Types, Enumerations, and Immutable Structures (`P1`)

Define domain enumerations (`CoverageStatus`, `IncompleteComparisonPolicy`, `ApplicabilityStatus`) and frozen data structures (`AggregatedMetricStats`, `AggregatedTimingStats`, `ConfigurationSummary`, `DescriptiveConsolidation`, `ApplicableMethod`, `MethodSuitabilityReport`).

```
T1
```

### Phase 2: Stage 4B to Stage 5 Transition Gate Validation (`P2`)

Implement `validate_stage5_entry` to strictly enforce prerequisites before Stage 5 execution, blocking active non-terminal cells (`PENDING`, `RUNNING`) and requiring at least one completed cell.

```
T1 --> T2
```

### Phase 3: Descriptive Metric & Timing Aggregation (`P3`)

Implement `consolidate_descriptive`, grouping results by configuration, evaluating fold coverage, tracking failed and cancelled folds, aggregating cell metrics and timings with exact mathematical conventions, and incorporating feature stability.

```
T2 --> T3
```

### Phase 4: Methodological Suitability and Incompleteness Policy (`P4`)

Implement `evaluate_method_suitability` and `check_pairwise_comparison_eligibility`, analyzing experimental design from `PartitionPlan`, computing training overlap ratios $r$, evaluating applicability of hypothesis tests, emitting structural warnings for $J < 6$, and enforcing incompleteness policies.

```
T1 --> T4
T3 --> T4
```

### Phase 5: Public API Exposure and Integration Suite (`P5`)

Expose public module API in `src/experimental_ml/statistics/__init__.py`, execute transversal integration pipeline, and verify runtime purity without third-party frameworks (`XCUT-02`).

```
T4 --> T5
```

---

## Task Breakdown

### Phase 1: Domain Types, Enumerations, and Immutable Structures

#### T1: Define statistics enums and frozen dataclasses [x]

**What**: Create `src/experimental_ml/statistics/types.py` defining `CoverageStatus`, `IncompleteComparisonPolicy`, and `ApplicabilityStatus` as closed string enums. Define `AggregatedMetricStats` with `n_valid`, `n_total`, `status`, and nullable float statistics (`mean`, `std`, `median`, `iqr`, `q25`, `q75`, `min_value`, `max_value`). Define `AggregatedTimingStats` with mean and sum durations for all cell phases. Define `ConfigurationSummary` with coverage metrics, fold lists, fold metrics, aggregated metrics, pooled OOF metrics, timing stats, and feature stability. Define `DescriptiveConsolidation` holding the configuration mapping and metadata. Define `ApplicableMethod` and `MethodSuitabilityReport`. Implement immutability checks raising `FrozenInstanceError`. Add unit tests in `tests/unit/statistics/test_types.py`.
**Where**: `src/experimental_ml/statistics/types.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/enums.py`, `src/experimental_ml/metrics/types.py`, `src/experimental_ml/features/stability.py`, `src/experimental_ml/validation/types.py`
**Requirement**: STAT-01
**Tests**: `tests/unit/statistics/test_types.py`
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_types.py -v`

---

### Phase 2: Stage 4B to Stage 5 Transition Gate Validation

#### T2: Implement validate_stage5_entry gate check [x]

**What**: Create `src/experimental_ml/statistics/consolidation.py` with `validate_stage5_entry`. Accept `MatrixExecutionState`, a run directory path, or an execution state dictionary. Verify that `execution_state.json` exists and can be parsed, raising `ContractViolationError` if missing or corrupted. Verify that no cell has active non-terminal status (`PENDING` or `RUNNING`), raising `ContractViolationError` with resume guidance. Verify that `completed_cells >= 1`, raising `ContractViolationError` if all cells failed or were cancelled. Allow proceeding when all cells are in terminal states (`COMPLETED`, `FAILED`, `CANCELLED`) with `completed_cells >= 1`. Add unit tests in `tests/unit/statistics/test_stage5_entry.py`.
**Where**: `src/experimental_ml/statistics/consolidation.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/orchestration/state.py`, `src/experimental_ml/core/exceptions.py`
**Requirement**: STAT-02
**Tests**: `tests/unit/statistics/test_stage5_entry.py`
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_stage5_entry.py -v`

---

### Phase 3: Descriptive Metric & Timing Aggregation

#### T3: Implement consolidate_descriptive function

**What**: In `src/experimental_ml/statistics/consolidation.py`, implement `consolidate_descriptive`. Group input `CellResultRecord` instances by `(model_id, scenario_id)`. For each configuration, compute total folds, completed folds, failed folds, cancelled folds, and coverage $C = \text{completed\_folds} / \text{total\_folds}$. Assign `CoverageStatus.VALID` ($C=1.0$), `CoverageStatus.PARTIAL_COVERAGE` ($0.0 < C < 1.0$), or `CoverageStatus.NO_COVERAGE` ($C=0.0$). Populate `completed_fold_ids`, `failed_fold_ids`, and `cancelled_fold_ids`. Compute `AggregatedMetricStats` for each metric: when $n_{\text{valid}} \ge 2$, calculate sample mean, sample std with `ddof=1`, median, IQR ($Q_{75} - Q_{25}$), min, and max using NumPy; when $n_{\text{valid}} = 1$, calculate mean, median, min, max, IQR ($0.0$), but set `std = None`; when $n_{\text{valid}} = 0$, set all summary fields to `None` and `status = MetricStatus.UNDEFINED_NAN`. Aggregate cell sub-phase durations into `AggregatedTimingStats` (or `None` if $C=0$). Compute feature selection stability across folds using `compute_selection_stability` when $J_{\text{completed}} \ge 2$, applying Jaccard empty set conventions (1.0 for both empty, 0.0 for unilateral empty), and returning `None` if $J_{\text{completed}} < 2$. Incorporate `pooled_oof_metrics` when available. Return `DescriptiveConsolidation`. Add unit tests in `tests/unit/statistics/test_consolidation.py`.
**Where**: `src/experimental_ml/statistics/consolidation.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/metrics/types.py`, `src/experimental_ml/features/stability.py`, `src/experimental_ml/orchestration/types.py`
**Requirement**: STAT-03
**Tests**: `tests/unit/statistics/test_consolidation.py`
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_consolidation.py -v`

---

### Phase 4: Methodological Suitability and Incompleteness Policy

#### T4: Implement evaluate_method_suitability and check_pairwise_comparison_eligibility

**What**: Create `src/experimental_ml/statistics/suitability.py` implementing `evaluate_method_suitability` and `check_pairwise_comparison_eligibility`. Extract evaluation regime from `PartitionPlan` (`CV_ONLY`, `HOLDOUT_ONLY`, `CV_AND_HOLDOUT`). Determine development partitions count $J = \text{len}(plan.folds)$. For CV regimes, calculate fold-level ratios $r_j = n_{\text{val}, j} / n_{\text{train}, j}$ and mean representative ratio $r = \frac{1}{J} \sum r_j$. Declare corrected Nadeau-Bengio paired $t$-test and paired Wilcoxon test as `APPLICABLE` for CV regimes with $J \ge 2$. Flag uncorrected standard paired $t$-test as `NOT_SUITABLE` for CV designs due to overlapping training sets. For `HOLDOUT_ONLY` ($J=1$), reject partition-level multi-fold tests as `NOT_SUITABLE` due to absence of variance across partitions, and do not recommend pooled OOF. If $J < 6$ (or $J_{\text{pareados}} < 6$) for Wilcoxon, attach a methodological warning of mathematical inability to reach $\alpha = 0.05$ (minimum exact p-value $0.0625$), while noting that $J \ge 6$ does not guarantee adequate power. In `CV_AND_HOLDOUT`, isolate holdout in `plan.holdout_ids` and scope `FINAL_HOLDOUT`. In `check_pairwise_comparison_eligibility`, under `STRICT_COMPLETE_ONLY` reject comparisons with missing folds (`coverage_status != VALID`); under `ALLOW_COMMON_SUBSET` permit comparison if $J_{\text{pareados}} \ge 2$ with mandatory conditional caveat; reject if $J_{\text{pareados}} < 2$. Add unit tests in `tests/unit/statistics/test_suitability.py`.
**Where**: `src/experimental_ml/statistics/suitability.py`
**Depends on**: T1, T3
**Reuses**: `src/experimental_ml/validation/types.py`, `src/experimental_ml/core/enums.py`
**Requirement**: STAT-04
**Tests**: `tests/unit/statistics/test_suitability.py`
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_suitability.py -v`

---

### Phase 5: Public API Exposure and Integration Suite

#### T5: Expose public statistics API and implement end-to-end integration tests

**What**: In `src/experimental_ml/statistics/__init__.py`, export `CoverageStatus`, `IncompleteComparisonPolicy`, `ApplicabilityStatus`, `AggregatedMetricStats`, `AggregatedTimingStats`, `ConfigurationSummary`, `DescriptiveConsolidation`, `ApplicableMethod`, `MethodSuitabilityReport`, `validate_stage5_entry`, `consolidate_descriptive`, `evaluate_method_suitability`, and `check_pairwise_comparison_eligibility`. Create `tests/integration/statistics/test_statistics_integration.py` exercising the full lifecycle: reading synthetic Stage 4 cell artifacts, passing gate validation, producing descriptive consolidations with partial and complete coverage, and evaluating methodological suitability across all regimes (`CV_ONLY`, `HOLDOUT_ONLY`, `CV_AND_HOLDOUT`). Verify runtime purity (`XCUT-02`), ensuring zero external imports beyond `numpy>=1.24.0` and stdlib, and zero domain coupling (`RNF02`).
**Where**: `src/experimental_ml/statistics/__init__.py`
**Depends on**: T4
**Reuses**: `src/experimental_ml/statistics/`
**Requirement**: STAT-01, STAT-02, STAT-03, STAT-04
**Tests**: `tests/integration/statistics/test_statistics_integration.py`
**Gate**: `.venv/bin/pytest tests/integration/statistics/test_statistics_integration.py -v`

---

## Checks

**C1** - CoverageStatus enum has VALID, PARTIAL_COVERAGE, and NO_COVERAGE (STAT-01, AC-M61-01-01)  
Proof: run unit | tests/unit/statistics/test_types.py::test_coverage_status_enum PASSED

**C2** - IncompleteComparisonPolicy enum has STRICT_COMPLETE_ONLY and ALLOW_COMMON_SUBSET (STAT-01, AC-M61-01-02)  
Proof: run unit | tests/unit/statistics/test_types.py::test_incomplete_comparison_policy_enum PASSED

**C3** - AggregatedMetricStats contains n_valid, n_total, status, and nullable float summary fields (STAT-01, AC-M61-01-03)  
Proof: run unit | tests/unit/statistics/test_types.py::test_aggregated_metric_stats_fields PASSED

**C4** - AggregatedTimingStats contains mean and total durations in seconds for all cell sub-phases (STAT-01, AC-M61-01-04)  
Proof: run unit | tests/unit/statistics/test_types.py::test_aggregated_timing_stats_fields PASSED

**C5** - ConfigurationSummary contains model_id, scenario_id, fold counters, coverage status, fold id tuples, and metric/timing summaries (STAT-01, AC-M61-01-05)  
Proof: run unit | tests/unit/statistics/test_types.py::test_configuration_summary_fields PASSED

**C6** - DescriptiveConsolidation contains experiment_id, partition_plan_id, total_configurations, configurations mapping, and timestamp (STAT-01, AC-M61-01-06)  
Proof: run unit | tests/unit/statistics/test_types.py::test_descriptive_consolidation_fields PASSED

**C7** - Modifying any attribute of statistics dataclasses raises FrozenInstanceError (STAT-01, AC-M61-01-07)  
Proof: run unit | tests/unit/statistics/test_types.py::test_statistics_dataclasses_frozen_immutability PASSED

**C8** - Missing or corrupted execution_state.json raises ContractViolationError (STAT-02, AC-M61-02-01)  
Proof: run unit | tests/unit/statistics/test_stage5_entry.py::test_validate_stage5_entry_missing_or_corrupt_state PASSED

**C9** - Active non-terminal cells (PENDING or RUNNING) raise ContractViolationError with resume message (STAT-02, AC-M61-02-02)  
Proof: run unit | tests/unit/statistics/test_stage5_entry.py::test_validate_stage5_entry_non_terminal_cells_blocked PASSED

**C10** - Execution state with completed_cells == 0 raises ContractViolationError (STAT-02, AC-M61-02-03)  
Proof: run unit | tests/unit/statistics/test_stage5_entry.py::test_validate_stage5_entry_zero_completed_cells_blocked PASSED

**C11** - All cells terminal (COMPLETED, FAILED, CANCELLED) with completed_cells >= 1 allows Stage 5 entry (STAT-02, AC-M61-02-04)  
Proof: run unit | tests/unit/statistics/test_stage5_entry.py::test_validate_stage5_entry_terminal_states_allowed PASSED

**C12** - consolidate_descriptive groups cell results by unique (model_id, scenario_id) configuration (STAT-03, AC-M61-03-01)  
Proof: run unit | tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_groups_by_configuration PASSED

**C13** - Configuration coverage C is computed correctly, assigning VALID, PARTIAL_COVERAGE, or NO_COVERAGE (STAT-03, AC-M61-03-02)  
Proof: run unit | tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_coverage_status_mapping PASSED

**C14** - FAILED and CANCELLED folds are recorded in failed_fold_ids and cancelled_fold_ids without metric coercion (STAT-03, AC-M61-03-03)  
Proof: run unit | tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_failed_and_cancelled_folds_recorded PASSED

**C15** - AggregatedMetricStats computes mean, sample std (ddof=1), median, IQR, min, max when n_valid >= 2 (STAT-03, AC-M61-03-04)  
Proof: run unit | tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_multi_fold PASSED

**C16** - AggregatedMetricStats computes mean, median, min, max, but sets std = None when n_valid == 1 (STAT-03, AC-M61-03-05)  
Proof: run unit | tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_single_fold PASSED

**C17** - AggregatedMetricStats sets all summary fields to None and status to UNDEFINED_NAN when n_valid == 0 (STAT-03, AC-M61-03-06)  
Proof: run unit | tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_zero_valid PASSED

**C18** - Consolidated OOF prediction records are incorporated into pooled_oof_metrics of ConfigurationSummary (STAT-03, AC-M61-03-07)  
Proof: run unit | tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_incorporates_pooled_oof PASSED

**C19** - Timing breakdown across completed folds is aggregated into mean and sum durations (STAT-03, AC-M61-03-08)  
Proof: run unit | tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_timing_aggregation PASSED

**C20** - Pairwise feature selection stability across folds uses compute_selection_stability with Jaccard empty set conventions (STAT-03, AC-M61-03-09)  
Proof: run unit | tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_feature_stability PASSED

**C21** - evaluate_method_suitability extracts evaluation regime, development folds J, fold ratios r_j, and mean ratio r (STAT-04, AC-M61-04-01)  
Proof: run unit | tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_extracts_regime_and_ratios PASSED

**C22** - CV_ONLY and CV_AND_HOLDOUT with J >= 2 declare corrected Nadeau-Bengio and Wilcoxon as applicable (STAT-04, AC-M61-04-02)  
Proof: run unit | tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_cv_applicable_methods PASSED

**C23** - Uncorrected standard paired t-test is flagged as NOT_SUITABLE for CV designs (STAT-04, AC-M61-04-03)  
Proof: run unit | tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_flags_uncorrected_t_test PASSED

**C24** - HOLDOUT_ONLY (J=1) rejects multi-fold paired tests as NOT_SUITABLE and does not recommend pooled OOF (STAT-04, AC-M61-04-04)  
Proof: run unit | tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_holdout_only_rejection PASSED

**C25** - Wilcoxon with J < 6 attaches mathematical warning of inability to reach alpha = 0.05 and power caveats (STAT-04, AC-M61-04-05)  
Proof: run unit | tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_wilcoxon_small_sample_warning PASSED

**C26** - CV_AND_HOLDOUT isolates holdout in plan.holdout_ids, keeping J restricted to development folds (STAT-04, AC-M61-04-06)  
Proof: run unit | tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_cv_and_holdout_isolation PASSED

**C27** - IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY rejects comparisons if coverage is not VALID (STAT-04, AC-M61-04-07)  
Proof: run unit | tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_strict_policy PASSED

**C28** - IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET permits comparison if J_paired >= 2 with conditional caveat (STAT-04, AC-M61-04-08)  
Proof: run unit | tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_common_subset_policy PASSED

**C29** - Pairwise comparison with J_paired < 2 is declared NOT_APPLICABLE regardless of policy (STAT-04, AC-M61-04-09)  
Proof: run unit | tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_insufficient_pairs PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T3
- **Next Task:** T3
