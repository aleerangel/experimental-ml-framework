# m1-3-metrics proofs

**HEAD**: 002fa9a
**Tree**: clean
**Shell**: /bin/sh
**Result**: 22 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_metric_structures_immutable PASSED` | pass |
| C2 | `run unit / test_metric_evaluation_scope_validation PASSED` | pass |
| C3 | `run unit / test_metrics_catalog_registration PASSED` | pass |
| C4 | `run unit / test_catalog_query_and_dispatch PASSED` | pass |
| C5 | `run unit / test_array_validation_dimensions PASSED` | pass |
| C6 | `run unit / test_array_validation_non_finites PASSED` | pass |
| C7 | `run unit / test_numerical_stability_and_overflow PASSED` | pass |
| C8 | `run unit / test_direct_scale_errors_accuracy PASSED` | pass |
| C9 | `run unit / test_mbe_preserves_signed_value PASSED` | pass |
| C10 | `run unit / test_rmse_scale_homoscedasticity PASSED` | pass |
| C11 | `run unit / test_dimensionless_ratios_accuracy PASSED` | pass |
| C12 | `run unit / test_r2_and_pearson_zero_variance PASSED` | pass |
| C13 | `run unit / test_rmse_rel_pct_and_mape_degenerate PASSED` | pass |
| C14 | `run unit / test_kta_centered_and_uncentered PASSED` | pass |
| C15 | `run unit / test_discrete_classification_accuracy PASSED` | pass |
| C16 | `run unit / test_precision_division_by_zero_rules PASSED` | pass |
| C17 | `run unit / test_recall_and_balanced_accuracy_rules PASSED` | pass |
| C18 | `run unit / test_f1_own_denominator_rules PASSED` | pass |
| C19 | `run unit / test_roc_auc_ties_and_ovr PASSED` | pass |
| C20 | `run unit / test_log_loss_validation_and_clipping PASSED` | pass |
| C21 | `run unit / test_is_better_adr005_rules PASSED` | pass |
| C22 | `run unit / test_aggregate_and_rank_configurations PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/test_metrics.py::test_r2_and_pearson_zero_variance PASSED     [ 45%]
tests/unit/test_metrics.py::test_rmse_rel_pct_and_mape_degenerate PASSED [ 50%]
tests/unit/test_metrics.py::test_kta_centered_and_uncentered PASSED      [ 54%]
tests/unit/test_metrics.py::test_discrete_classification_accuracy PASSED [ 59%]
tests/unit/test_metrics.py::test_precision_division_by_zero_rules PASSED [ 63%]
tests/unit/test_metrics.py::test_recall_and_balanced_accuracy_rules PASSED [ 68%]
tests/unit/test_metrics.py::test_f1_own_denominator_rules PASSED         [ 72%]
tests/unit/test_metrics.py::test_roc_auc_ties_and_ovr PASSED             [ 77%]
tests/unit/test_metrics.py::test_log_loss_validation_and_clipping PASSED [ 81%]
tests/unit/test_metrics.py::test_metrics_catalog_registration PASSED     [ 86%]
tests/unit/test_metrics.py::test_catalog_query_and_dispatch PASSED       [ 90%]
tests/unit/test_metrics.py::test_is_better_adr005_rules PASSED           [ 95%]
tests/unit/test_metrics.py::test_aggregate_and_rank_configurations PASSED [100%]

============================== 22 passed in 0.08s ==============================
```
