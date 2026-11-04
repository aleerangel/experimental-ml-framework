# m1-3-metrics Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m1-3-metrics/design.md`
**Status**: Approved
**Approved**: 2026-11-03 - user: "aprovado. commita"
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates
**Run unit**: `.venv/bin/pytest tests/unit/test_metrics.py -v`

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied; metrics transversal package according to spec ACs.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Domain Types & Scopes (`src/experimental_ml/metrics/types.py`) | unit | 1:1 AC mapping: all frozen structures, MetricEvaluationScope validation, coercion and immutability | `tests/unit/test_metrics.py` | `.venv/bin/pytest tests/unit/test_metrics.py -v` |
| Numerical Validation (`src/experimental_ml/metrics/validation.py`) | unit | 1:1 AC mapping: shape/finitude checks, non-finites rejection, scaled_quadratic_sum overflow boundaries | `tests/unit/test_metrics.py` | `.venv/bin/pytest tests/unit/test_metrics.py -v` |
| Regression & Kernel Metrics (`src/experimental_ml/metrics/regression.py`) | unit | 1:1 AC mapping: direct-scale errors, scale homoscedasticity, dimensionless ratios, centered/uncentered KTA, all degenerate conditions | `tests/unit/test_metrics.py` | `.venv/bin/pytest tests/unit/test_metrics.py -v` |
| Classification Metrics (`src/experimental_ml/metrics/classification.py`) | unit | 1:1 AC mapping: per-class zero division conditions, F1 denominator handling, ROC AUC tied scores/OVR, Log Loss validation and clipping | `tests/unit/test_metrics.py` | `.venv/bin/pytest tests/unit/test_metrics.py -v` |
| Metrics Catalog (`src/experimental_ml/metrics/catalog.py`) | unit | 1:1 AC mapping: all 15 metrics registered with exact metadata, compare_by_abs flag, resolution and dispatch | `tests/unit/test_metrics.py` | `.venv/bin/pytest tests/unit/test_metrics.py -v` |
| Aggregation & Ranking (`src/experimental_ml/metrics/aggregation.py`) | unit | 1:1 AC mapping: is_better with compare_by_abs, aggregate_fold_metrics (K/K, k/K, 0/K), rank_configurations strict lexicographic ordering | `tests/unit/test_metrics.py` | `.venv/bin/pytest tests/unit/test_metrics.py -v` |
| Public API Root (`src/experimental_ml/metrics/__init__.py`) | none | - (build gate only: public re-export exposure) | `src/experimental_ml/metrics/__init__.py` | quick gate only |
| Unit Test Suite (`tests/unit/test_metrics.py`) | unit | 100% pass across all 22 metrics requirements | `tests/unit/test_metrics.py` | `.venv/bin/pytest tests/unit/test_metrics.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After single-file edits in metrics | `.venv/bin/python -m py_compile src/experimental_ml/metrics/*.py` |
| Full | After unit test updates | `.venv/bin/pytest tests/unit/test_metrics.py -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Types, Scopes, Validation & Regression Metrics

Implement foundational immutable types, scope enums, numerical validators, and the 8 regression/kernel metrics with unit test coverage.

```
T1 → T2 → T3
```

### Phase 2: Classification Metrics, Catalog, Aggregation & Package Export

Implement the 7 classification metrics, the centralized catalog, aggregation/ranking (ADR-005), public re-exports, and full verification.

```
T4 → T5 → T6 → T7
```

---

## Task Breakdown

### Phase 1: Types, Scopes, Validation & Regression Metrics

#### T1: Implement domain types, scope enum and numerical validation

**What**: Create `src/experimental_ml/metrics/types.py` and `src/experimental_ml/metrics/validation.py` defining `MetricEvaluationScope`, `MetricValue`, `AggregatedMetricValue`, `MetricSpec`, `RankedCandidate`, `validate_numeric_arrays`, `validate_scope`, and `scaled_quadratic_sum`.
**Where**: `src/experimental_ml/metrics/types.py`
**Depends on**: None
**Reuses**: `experimental_ml.core.enums`, `experimental_ml.core.findings`
**Requirement**: MET-01, MET-04, MET-05, MET-21, MET-22

**Done when**:
- [x] `src/experimental_ml/metrics/types.py` and `src/experimental_ml/metrics/validation.py` created
- [x] `MetricEvaluationScope` defined with 4 canonical members and strict validation in `MetricValue` and `AggregatedMetricValue`
- [x] `scaled_quadratic_sum` protects against intermediate overflow for $|diff| > \sqrt{\text{float64.max}}$
- [x] Non-finite inputs (`NaN`/`Inf`) and dimension mismatches raise `DataIntegrityError`
- [x] Unit tests for types, scopes, and validation written in `tests/unit/test_metrics.py`
- [x] Gate check passes: `.venv/bin/pytest tests/unit/test_metrics.py -v`

**Tests**: unit
**Gate**: quick

---

#### T2: Implement direct-scale regression metrics (mae, rmse, mbe)

**What**: Implement `mae`, `rmse`, and `mbe` in `src/experimental_ml/metrics/regression.py` operating in `float64` with scale homoscedasticity and signed `mbe.value`.
**Where**: `src/experimental_ml/metrics/regression.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/metrics/types.py`, `src/experimental_ml/metrics/validation.py`
**Requirement**: MET-06, MET-07

**Done when**:
- [x] `mae`, `rmse`, and `mbe` implemented in `src/experimental_ml/metrics/regression.py`
- [x] Accuracy within `rtol=1e-12`, `atol=1e-12` against analytical vectors
- [x] `rmse(c*y, c*y_hat) == |c|*rmse(y, y_hat)` verified with `atol=0.0`
- [x] `mbe.value` preserves positive and negative signs
- [x] Unit tests for direct-scale errors written in `tests/unit/test_metrics.py`
- [x] Gate check passes: `.venv/bin/pytest tests/unit/test_metrics.py -v`

**Tests**: unit
**Gate**: quick

---

#### T3: Implement dimensionless ratio and alignment metrics (r2, rmse_rel_pct, mape, pearson, kta)

**What**: Complete `src/experimental_ml/metrics/regression.py` implementing `r2`, `rmse_rel_pct`, `mape`, `pearson`, and `kta` (with `centered: bool = False` option) and explicit `UNDEFINED_NAN` handling.
**Where**: `src/experimental_ml/metrics/regression.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/metrics/types.py`, `src/experimental_ml/metrics/validation.py`
**Requirement**: MET-08, MET-09, MET-10, MET-11

**Done when**:
- [x] `r2`, `rmse_rel_pct`, `mape`, `pearson`, and `kta` implemented
- [x] $n < 2$ or zero variance in `r2`/`pearson` returns `UNDEFINED_NAN` with `Finding`
- [x] $y_i == 0$ in `mape` returns `UNDEFINED_NAN` with `Finding` without adding $\epsilon$
- [x] $|\bar{y}| == 0$ in `rmse_rel_pct` returns `UNDEFINED_NAN` with `Finding`
- [x] `kta` supports both `centered=False` and `centered=True` ($HKH$), returning `UNDEFINED_NAN` if Gram norm is zero
- [x] Unit tests for ratios and alignment written in `tests/unit/test_metrics.py`
- [x] Gate check passes: `.venv/bin/pytest tests/unit/test_metrics.py -v`

**Tests**: unit
**Gate**: quick

---

### Phase 2: Classification Metrics, Catalog, Aggregation & Package Export

#### T4: Implement discrete classification metrics (accuracy, balanced_accuracy, precision, recall, f1)

**What**: Create `src/experimental_ml/metrics/classification.py` implementing discrete classification metrics with per-class division rules and F1 own denominator evaluation.
**Where**: `src/experimental_ml/metrics/classification.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/metrics/types.py`, `src/experimental_ml/metrics/validation.py`
**Requirement**: MET-12, MET-13, MET-14

**Done when**:
- [x] `accuracy`, `balanced_accuracy`, `precision`, `recall`, and `f1` implemented
- [x] `precision` returns `UNDEFINED_NAN` when $TP_c + FP_c = 0$, but returns valid `0.0` when $TP_c = 0$ with $FP_c > 0$
- [x] `recall` returns `UNDEFINED_NAN` when $TP_c + FN_c = 0$, but returns valid `0.0` when $TP_c = 0$ with $FN_c > 0$
- [x] `f1` evaluates $\frac{2 TP}{2 TP + FP + FN}$, returning `UNDEFINED_NAN` only if denominator is zero ($2 TP + FP + FN == 0$) and returning valid `0.0` if denominator is positive with $TP = 0$
- [x] `balanced_accuracy` returns `UNDEFINED_NAN` if $|\mathcal{C}| < 2$ or any class lacks positive support
- [x] Unit tests for discrete classification written in `tests/unit/test_metrics.py`
- [x] Gate check passes: `.venv/bin/pytest tests/unit/test_metrics.py -v`

**Tests**: unit
**Gate**: quick

---

#### T5: Implement probabilistic and ranking metrics (roc_auc, log_loss)

**What**: Complete `src/experimental_ml/metrics/classification.py` implementing `roc_auc` (Mann-Whitney U with mid-ranks and OVR) and `log_loss` (probability validation and clipping $\epsilon = 10^{-15}$).
**Where**: `src/experimental_ml/metrics/classification.py`
**Depends on**: T4
**Reuses**: `src/experimental_ml/metrics/types.py`, `src/experimental_ml/metrics/validation.py`
**Requirement**: MET-15, MET-16, MET-17

**Done when**:
- [x] `roc_auc` and `log_loss` implemented
- [x] `roc_auc` resolves ties via mid-ranks returning `0.5` for constant scores and supports multiclass OVR (`macro`/`weighted`)
- [x] `log_loss` validates distribution bounds $[-10^{-12}, 1 + 10^{-12}]$ and row sums, applying clipping $\epsilon = 10^{-15}$
- [x] Single-class $y_{\text{true}}$ returns `UNDEFINED_NAN` with `Finding`
- [x] Unit tests for probabilistic metrics written in `tests/unit/test_metrics.py`
- [x] Gate check passes: `.venv/bin/pytest tests/unit/test_metrics.py -v`

**Tests**: unit
**Gate**: quick

---

#### T6: Implement centralized catalog and resolution functions

**What**: Create `src/experimental_ml/metrics/catalog.py` registering `METRICS_CATALOG` with all 15 metrics, `compare_by_abs=True` on `mbe`, `get_metric_spec`, `list_metrics`, and `compute_metric`.
**Where**: `src/experimental_ml/metrics/catalog.py`
**Depends on**: T3, T5
**Reuses**: `src/experimental_ml/metrics/types.py`, `src/experimental_ml/metrics/regression.py`, `src/experimental_ml/metrics/classification.py`
**Requirement**: MET-02, MET-03

**Done when**:
- [ ] `METRICS_CATALOG` contains all 15 metrics with complete metadata and reference tolerances
- [ ] `compare_by_abs` is `True` for `mbe` and `False` for the other 14 metrics
- [ ] `get_metric_spec` resolves case-insensitively and raises `ConfigurationError` for unknown metrics
- [ ] `compute_metric` dispatches execution and returns `MetricValue`
- [ ] Unit tests for catalog functions written in `tests/unit/test_metrics.py`
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/test_metrics.py -v`

**Tests**: unit
**Gate**: quick

---

#### T7: Implement aggregation, comparison, ranking and public package export

**What**: Create `src/experimental_ml/metrics/aggregation.py` implementing `is_better`, `aggregate_fold_metrics`, and `rank_configurations` (ADR-005), and expose public API in `src/experimental_ml/metrics/__init__.py`.
**Where**: `src/experimental_ml/metrics/aggregation.py`
**Depends on**: T6
**Reuses**: `src/experimental_ml/metrics/types.py`, `src/experimental_ml/metrics/catalog.py`
**Requirement**: MET-18, MET-19, MET-20

**Done when**:
- [ ] `is_better` resolves `compare_by_abs` via `MetricSpec` without literal string checks and enforces that `VALID` beats `PARTIAL_COVERAGE` and `UNDEFINED_NAN`
- [ ] `aggregate_fold_metrics` computes descriptive stats and sets `VALID` ($K/K$), `PARTIAL_COVERAGE` ($k/K$) or `UNDEFINED_NAN` ($0/K$)
- [ ] `rank_configurations` applies strict lexicographic sort `(0 if VALID else 1, -coverage, directed_value, candidate_id)`, placing `UNDEFINED_NAN` at end with `rank=None`
- [ ] `src/experimental_ml/metrics/__init__.py` re-exports all public symbols in `__all__`
- [ ] Comprehensive unit test suite in `tests/unit/test_metrics.py` covers all 22 checks with 100% pass
- [ ] Gate check passes: `.venv/bin/pytest tests/unit/test_metrics.py -v` and `.venv/bin/pytest tests/ -v`

**Tests**: unit
**Gate**: full

---

## Checks

**C1** - Domain structures MetricValue, AggregatedMetricValue, MetricSpec, and RankedCandidate are immutable (MET-01, AC 1)
Proof: run unit | test_metric_structures_immutable PASSED

**C2** - MetricEvaluationScope defines 4 canonical members and rejects arbitrary scopes with ConfigurationError (MET-22, AC 2)
Proof: run unit | test_metric_evaluation_scope_validation PASSED

**C3** - METRICS_CATALOG registers all 15 metrics with compare_by_abs=True on mbe and False on others (MET-02, AC 3-4)
Proof: run unit | test_metrics_catalog_registration PASSED

**C4** - get_metric_spec and compute_metric resolve metrics and reject unknown ids with ConfigurationError (MET-03, AC 5-6)
Proof: run unit | test_catalog_query_and_dispatch PASSED

**C5** - Array validation converts to float64, rejects mismatched lengths and zero samples with DataIntegrityError (MET-04, AC 1-2)
Proof: run unit | test_array_validation_dimensions PASSED

**C6** - Array validation rejects NaN, +Inf, and -Inf with DataIntegrityError (MET-05, AC 3)
Proof: run unit | test_array_validation_non_finites PASSED

**C7** - scaled_quadratic_sum prevents intermediate overflow for large magnitudes and post-condition handles residual overflow (MET-21, AC 4-5)
Proof: run unit | test_numerical_stability_and_overflow PASSED

**C8** - Direct-scale errors mae, rmse, and mbe operate in float64 with rtol=1e-12, atol=1e-12 and zero error on identity (MET-06, AC 1, 3)
Proof: run unit | test_direct_scale_errors_accuracy PASSED

**C9** - mbe preserves positive and negative signed values (MET-06, AC 2)
Proof: run unit | test_mbe_preserves_signed_value PASSED

**C10** - Function rmse preserves scale homoscedasticity without rounding (MET-07, AC 4)
Proof: run unit | test_rmse_scale_homoscedasticity PASSED

**C11** - Dimensionless ratios r2, rmse_rel_pct, mape, pearson, and kta operate within rtol=1e-10, atol=1e-12 (MET-08, AC 1-2)
Proof: run unit | test_dimensionless_ratios_accuracy PASSED

**C12** - Functions r2 and pearson return UNDEFINED_NAN with Finding for n < 2 or zero target variance (MET-09, AC 3-4)
Proof: run unit | test_r2_and_pearson_zero_variance PASSED

**C13** - Functions rmse_rel_pct and mape return UNDEFINED_NAN with Finding for zero mean or zero target observations (MET-10, AC 5-6)
Proof: run unit | test_rmse_rel_pct_and_mape_degenerate PASSED

**C14** - Function kta computes uncentered and centered alignment and returns UNDEFINED_NAN for zero Gram norm (MET-11, AC 7)
Proof: run unit | test_kta_centered_and_uncentered PASSED

**C15** - Discrete classification metrics accuracy, balanced_accuracy, precision, recall, and f1 operate within rtol=1e-14, atol=1e-15 (MET-12, AC 1)
Proof: run unit | test_discrete_classification_accuracy PASSED

**C16** - precision returns UNDEFINED_NAN when TP + FP = 0 and valid 0.0 when TP = 0 with FP > 0 (MET-13, AC 3)
Proof: run unit | test_precision_division_by_zero_rules PASSED

**C17** - recall and balanced_accuracy return UNDEFINED_NAN for absent classes (TP + FN = 0) and valid 0.0 when TP = 0 with FN > 0 (MET-14, AC 4, 6)
Proof: run unit | test_recall_and_balanced_accuracy_rules PASSED

**C18** - f1 computes 2*TP / (2*TP + FP + FN), returning UNDEFINED_NAN only for zero denominator and valid 0.0 when denominator > 0 with TP = 0 (MET-14, AC 5)
Proof: run unit | test_f1_own_denominator_rules PASSED

**C19** - roc_auc resolves ties via mid-ranks and computes multiclass OVR macro/weighted (MET-15, AC 2-3)
Proof: run unit | test_roc_auc_ties_and_ovr PASSED

**C20** - log_loss validates distributions, applies clipping eps=1e-15, and single-class y_true returns UNDEFINED_NAN (MET-16, MET-17, AC 4-6)
Proof: run unit | test_log_loss_validation_and_clipping PASSED

**C21** - Function is_better respects compare_by_abs, coverage precedence, and UNDEFINED_NAN rules (MET-18, AC 1-3)
Proof: run unit | test_is_better_adr005_rules PASSED

**C22** - aggregate_fold_metrics and rank_configurations enforce coverage stats and strict lexicographic ordering (MET-19, MET-20, AC 4-8)
Proof: run unit | test_aggregate_and_rank_configurations PASSED

---

## Acceptance Walkthrough (ACCEPTANCE.md)

Alongside `tasks.md`, `ACCEPTANCE.md` is maintained defining:
1. Environment preparation and import verification of `experimental_ml.metrics`.
2. Public API consumer tests covering types, regression, classification, probabilities, and aggregation.
3. Integrated cross-validation scenario verifying that `VALID` strictly precedes `PARTIAL_COVERAGE`.
4. Approval matrix mapped to criteria `AC-M1.3-1` through `AC-M1.3-10`.

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
Phase 1: Types, Scopes, Validation & Regression Metrics
  T1 (types & validation) -> T2 (mae, rmse, mbe) -> T3 (r2, rmse_rel_pct, mape, pearson, kta)

Phase 2: Classification Metrics, Catalog, Aggregation & Package Export
  T4 (discrete classification) -> T5 (roc_auc, log_loss) -> T6 (catalog) -> T7 (aggregation & init)
```

