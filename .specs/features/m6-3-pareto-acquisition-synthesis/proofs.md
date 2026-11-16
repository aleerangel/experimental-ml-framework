# m6-3-pareto-acquisition-synthesis proofs

**HEAD**: 8016f25
**Tree**: clean
**Shell**: /bin/sh
**Result**: 12 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/statistics/test_m63_types.py::test_m63_01_multiobjective_types_and_immutability PASSED` | pass |
| C2 | `run unit / tests/unit/statistics/test_pareto.py::test_m63_01_excludes_partial_and_nan_configs PASSED` | pass |
| C3 | `run unit / tests/unit/statistics/test_pareto.py::test_m63_01_exact_pareto_frontier_and_dominance PASSED` | pass |
| C4 | `run unit / tests/unit/statistics/test_m63_types.py::test_m63_02_acquisition_types_and_immutability PASSED` | pass |
| C5 | `run unit / tests/unit/statistics/test_acquisition.py::test_m63_02_acquisition_criteria_and_zero_std PASSED` | pass |
| C6 | `run unit / tests/unit/statistics/test_acquisition.py::test_m63_02_invalid_candidates_rejected PASSED` | pass |
| C7 | `run unit / tests/unit/statistics/test_m63_types.py::test_m63_03_structured_conclusion_immutability PASSED` | pass |
| C8 | `run unit / tests/unit/statistics/test_synthesis.py::test_m63_03_numeric_traceability_in_narrative PASSED` | pass |
| C9 | `run unit / tests/unit/statistics/test_synthesis.py::test_m63_03_no_equivalence_from_nonsignificance PASSED` | pass |
| C10 | `run unit / tests/unit/statistics/test_synthesis.py::test_m63_03_preserves_methodological_caveats PASSED` | pass |
| C11 | `run unit / tests/integration/statistics/test_m63_integration.py::test_m63_end_to_end_pipeline PASSED` | pass |
| C12 | `run unit / tests/integration/statistics/test_m63_integration.py::test_m63_runtime_purity_xcut02 PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/statistics/test_synthesis.py::test_m63_03_no_equivalence_from_nonsignificance PASSED [ 81%]
tests/unit/statistics/test_synthesis.py::test_m63_03_preserves_methodological_caveats PASSED [ 83%]
tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_exact_pratt_and_normal PASSED [ 84%]
tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_all_zeros PASSED [ 86%]
tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_small_sample_warning PASSED [ 87%]
tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_cohens_d_and_ci PASSED [ 89%]
tests/integration/statistics/test_m62_integration.py::test_m62_end_to_end_pipeline PASSED [ 90%]
tests/integration/statistics/test_m62_integration.py::test_m62_runtime_purity_xcut02 PASSED [ 92%]
tests/integration/statistics/test_m63_integration.py::test_m63_end_to_end_pipeline PASSED [ 93%]
tests/integration/statistics/test_m63_integration.py::test_m63_runtime_purity_xcut02 PASSED [ 95%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_public_api_exports PASSED [ 96%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_end_to_end_lifecycle PASSED [ 98%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_runtime_purity_xcut02 PASSED [100%]

============================== 65 passed in 0.78s ==============================
```
