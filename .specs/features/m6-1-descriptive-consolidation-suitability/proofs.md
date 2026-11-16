# m6-1-descriptive-consolidation-suitability proofs

**HEAD**: 4354b31
**Tree**: clean
**Shell**: /bin/sh
**Result**: 29 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/statistics/test_statistics_types.py::test_coverage_status_enum PASSED` | pass |
| C2 | `run unit / tests/unit/statistics/test_statistics_types.py::test_incomplete_comparison_policy_enum PASSED` | pass |
| C3 | `run unit / tests/unit/statistics/test_statistics_types.py::test_aggregated_metric_stats_fields PASSED` | pass |
| C4 | `run unit / tests/unit/statistics/test_statistics_types.py::test_aggregated_timing_stats_fields PASSED` | pass |
| C5 | `run unit / tests/unit/statistics/test_statistics_types.py::test_configuration_summary_fields PASSED` | pass |
| C6 | `run unit / tests/unit/statistics/test_statistics_types.py::test_descriptive_consolidation_fields PASSED` | pass |
| C7 | `run unit / tests/unit/statistics/test_statistics_types.py::test_statistics_dataclasses_frozen_immutability PAS` | pass |
| C8 | `run unit / tests/unit/statistics/test_stage5_entry.py::test_validate_stage5_entry_missing_or_corrupt_state PAS` | pass |
| C9 | `run unit / tests/unit/statistics/test_stage5_entry.py::test_validate_stage5_entry_non_terminal_cells_blocked P` | pass |
| C10 | `run unit / tests/unit/statistics/test_stage5_entry.py::test_validate_stage5_entry_zero_completed_cells_blocked` | pass |
| C11 | `run unit / tests/unit/statistics/test_stage5_entry.py::test_validate_stage5_entry_terminal_states_allowed PASS` | pass |
| C12 | `run unit / tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_groups_by_configuration P` | pass |
| C13 | `run unit / tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_coverage_status_mapping P` | pass |
| C14 | `run unit / tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_failed_and_cancelled_fold` | pass |
| C15 | `run unit / tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_multi_fold P` | pass |
| C16 | `run unit / tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_single_fold ` | pass |
| C17 | `run unit / tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_zero_valid P` | pass |
| C18 | `run unit / tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_incorporates_pooled_oof P` | pass |
| C19 | `run unit / tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_timing_aggregation PASSED` | pass |
| C20 | `run unit / tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_feature_stability PASSED` | pass |
| C21 | `run unit / tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_extracts_regime_and_rat` | pass |
| C22 | `run unit / tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_cv_applicable_methods P` | pass |
| C23 | `run unit / tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_flags_uncorrected_t_tes` | pass |
| C24 | `run unit / tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_holdout_only_rejection ` | pass |
| C25 | `run unit / tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_wilcoxon_small_sample_w` | pass |
| C26 | `run unit / tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_cv_and_holdout_isolatio` | pass |
| C27 | `run unit / tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_strict_policy PASSED` | pass |
| C28 | `run unit / tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_common_subset_policy PASS` | pass |
| C29 | `run unit / tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_insufficient_pairs PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/statistics/test_statistics_types.py::test_statistics_dataclasses_frozen_immutability PASSED [ 64%]
tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_extracts_regime_and_ratios PASSED [ 67%]
tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_cv_applicable_methods PASSED [ 70%]
tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_flags_uncorrected_t_test PASSED [ 73%]
tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_holdout_only_rejection PASSED [ 76%]
tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_wilcoxon_small_sample_warning PASSED [ 79%]
tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_cv_and_holdout_isolation PASSED [ 82%]
tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_strict_policy PASSED [ 85%]
tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_common_subset_policy PASSED [ 88%]
tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_insufficient_pairs PASSED [ 91%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_public_api_exports PASSED [ 94%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_end_to_end_lifecycle PASSED [ 97%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_runtime_purity_xcut02 PASSED [100%]

============================== 34 passed in 0.34s ==============================
```
