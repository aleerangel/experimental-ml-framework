# m6-2-paired-inference-multiplicity proofs

**HEAD**: e07c5e2
**Tree**: clean
**Shell**: /bin/sh
**Result**: 18 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/statistics/test_inference_types.py::test_m62_01_enums_values PASSED` | pass |
| C2 | `run unit / tests/unit/statistics/test_inference_types.py::test_m62_01_comparison_spec_validation PASSED` | pass |
| C3 | `run unit / tests/unit/statistics/test_inference_types.py::test_m62_01_frozen_immutability PASSED` | pass |
| C4 | `run unit / tests/unit/statistics/test_nadeau_bengio.py::test_m62_02_corrected_variance_and_pvalue PASSED` | pass |
| C5 | `run unit / tests/unit/statistics/test_nadeau_bengio.py::test_m62_02_fold_size_cv_warning PASSED` | pass |
| C6 | `run unit / tests/unit/statistics/test_nadeau_bengio.py::test_m62_02_zero_variance_handling PASSED` | pass |
| C7 | `run unit / tests/unit/statistics/test_nadeau_bengio.py::test_m62_02_invalid_inputs_rejected PASSED` | pass |
| C8 | `run unit / tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_exact_pratt_and_normal PASSED` | pass |
| C9 | `run unit / tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_all_zeros PASSED` | pass |
| C10 | `run unit / tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_small_sample_warning PASSED` | pass |
| C11 | `run unit / tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_cohens_d_and_ci PASSED` | pass |
| C12 | `run unit / tests/unit/statistics/test_multiplicity_comparisons.py::test_m62_04_holm_bonferroni_adjustment PASS` | pass |
| C13 | `run unit / tests/unit/statistics/test_multiplicity_comparisons.py::test_m62_04_benjamini_hochberg_adjustment P` | pass |
| C14 | `run unit / tests/unit/statistics/test_multiplicity_comparisons.py::test_m62_04_invalid_pvalues_raise PASSED` | pass |
| C15 | `run unit / tests/unit/statistics/test_multiplicity_comparisons.py::test_m62_04_orchestrator_scopes_nan_and_pra` | pass |
| C16 | `run unit / tests/unit/statistics/test_multiplicity_comparisons.py::test_m62_04_holdout_protection_and_skipped_` | pass |
| C17 | `run unit / tests/integration/statistics/test_m62_integration.py::test_m62_end_to_end_pipeline PASSED` | pass |
| C18 | `run unit / tests/integration/statistics/test_m62_integration.py::test_m62_runtime_purity_xcut02 PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/statistics/test_suitability.py::test_evaluate_method_suitability_cv_and_holdout_isolation PASSED [ 77%]
tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_strict_policy PASSED [ 79%]
tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_common_subset_policy PASSED [ 81%]
tests/unit/statistics/test_suitability.py::test_check_pairwise_comparison_insufficient_pairs PASSED [ 83%]
tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_exact_pratt_and_normal PASSED [ 84%]
tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_all_zeros PASSED [ 86%]
tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_small_sample_warning PASSED [ 88%]
tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_cohens_d_and_ci PASSED [ 90%]
tests/integration/statistics/test_m62_integration.py::test_m62_end_to_end_pipeline PASSED [ 92%]
tests/integration/statistics/test_m62_integration.py::test_m62_runtime_purity_xcut02 PASSED [ 94%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_public_api_exports PASSED [ 96%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_end_to_end_lifecycle PASSED [ 98%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_runtime_purity_xcut02 PASSED [100%]

============================== 53 passed in 0.50s ==============================
```
