# m1-3-metrics verification

**Verdict**: PASS
**Proofs**: `proofs.md` at 002fa9a
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/test_metrics.py` `test_metric_structures_immutable` | yes |
| C2 | `tests/unit/test_metrics.py` `test_metric_evaluation_scope_validation` | yes |
| C3 | `tests/unit/test_metrics.py` `test_metrics_catalog_registration` | yes |
| C4 | `tests/unit/test_metrics.py` `test_catalog_query_and_dispatch` | yes |
| C5 | `tests/unit/test_metrics.py` `test_array_validation_dimensions` | yes |
| C6 | `tests/unit/test_metrics.py` `test_array_validation_non_finites` | yes |
| C7 | `tests/unit/test_metrics.py` `test_numerical_stability_and_overflow` | yes |
| C8 | `tests/unit/test_metrics.py` `test_direct_scale_errors_accuracy` | yes |
| C9 | `tests/unit/test_metrics.py` `test_mbe_preserves_signed_value` | yes |
| C10 | `tests/unit/test_metrics.py` `test_rmse_scale_homoscedasticity` | yes |
| C11 | `tests/unit/test_metrics.py` `test_dimensionless_ratios_accuracy` | yes |
| C12 | `tests/unit/test_metrics.py` `test_r2_and_pearson_zero_variance` | yes |
| C13 | `tests/unit/test_metrics.py` `test_rmse_rel_pct_and_mape_degenerate` | yes |
| C14 | `tests/unit/test_metrics.py` `test_kta_centered_and_uncentered` | yes |
| C15 | `tests/unit/test_metrics.py` `test_discrete_classification_accuracy` | yes |
| C16 | `tests/unit/test_metrics.py` `test_precision_division_by_zero_rules` | yes |
| C17 | `tests/unit/test_metrics.py` `test_recall_and_balanced_accuracy_rules` | yes |
| C18 | `tests/unit/test_metrics.py` `test_f1_own_denominator_rules` | yes |
| C19 | `tests/unit/test_metrics.py` `test_roc_auc_ties_and_ovr` | yes |
| C20 | `tests/unit/test_metrics.py` `test_log_loss_validation_and_clipping` | yes |
| C21 | `tests/unit/test_metrics.py` `test_is_better_adr005_rules` | yes |
| C22 | `tests/unit/test_metrics.py` `test_aggregate_and_rank_configurations` | yes |

## Findings

None - independent audit confirmed analytical accuracy across float64 precision, signed bias preservation in MBE, division-by-zero rules, F1 direct denominator evaluation, Mann-Whitney U mid-ranks tie breaking, probability distributions validation and clipping, and ADR-005 lexicographic ranking.
