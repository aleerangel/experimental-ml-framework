# m5-1-cell-execution-contracts proofs

**HEAD**: 7850a10
**Tree**: clean
**Shell**: /bin/sh
**Result**: 30 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/orchestration/test_cell_types.py::test_m51_01_01_execution_status_enum PASSED` | pass |
| C2 | `run unit / tests/unit/orchestration/test_cell_types.py::test_m51_01_02_error_policy_enum PASSED` | pass |
| C3 | `run unit / tests/unit/orchestration/test_cell_types.py::test_m51_01_03_cell_phase_enum PASSED` | pass |
| C4 | `run unit / tests/unit/orchestration/test_cell_types.py::test_m51_01_04_cell_id_validation PASSED` | pass |
| C5 | `run unit / tests/unit/orchestration/test_cell_types.py::test_m51_01_05_timing_breakdown_fields PASSED` | pass |
| C6 | `run unit / tests/unit/orchestration/test_cell_types.py::test_m51_01_06_prediction_record_fields PASSED` | pass |
| C7 | `run unit / tests/unit/orchestration/test_cell_types.py::test_m51_01_07_prediction_record_alignment PASSED` | pass |
| C8 | `run unit / tests/unit/orchestration/test_cell_types.py::test_m51_01_08_cell_result_record_fields PASSED` | pass |
| C9 | `run unit / tests/unit/orchestration/test_cell_types.py::test_m51_01_09_immutability PASSED` | pass |
| C10 | `run unit / tests/unit/orchestration/test_cell_execution.py::test_m51_02_01_fold_slicing PASSED` | pass |
| C11 | `run unit / tests/unit/orchestration/test_cell_execution.py::test_m51_02_02_feature_selection_isolation PASSED` | pass |
| C12 | `run unit / tests/unit/orchestration/test_cell_execution.py::test_m51_02_03_nested_tuning_integration PASSED` | pass |
| C13 | `run unit / tests/unit/orchestration/test_cell_execution.py::test_m51_02_04_two_layer_preprocessing_isolation P` | pass |
| C14 | `run unit / tests/unit/orchestration/test_cell_execution.py::test_m51_02_05_fresh_model_seed PASSED` | pass |
| C15 | `run unit / tests/unit/orchestration/test_cell_execution.py::test_m51_02_06_fit_predict_diagnostics PASSED` | pass |
| C16 | `run unit / tests/unit/orchestration/test_cell_execution.py::test_m51_02_07_metric_evaluation_nan PASSED` | pass |
| C17 | `run integration / tests/integration/orchestration/test_cell_integration.py::test_m51_02_08_end_to_end_cell_lif` | pass |
| C18 | `run integration / tests/integration/orchestration/test_cell_integration.py::test_m51_02_09_anti_leakage_advers` | pass |
| C19 | `run unit / tests/unit/orchestration/test_cell_failures.py::test_m51_03_01_fault_tolerant_catches_exception PAS` | pass |
| C20 | `run unit / tests/unit/orchestration/test_cell_failures.py::test_m51_03_02_status_failed PASSED` | pass |
| C21 | `run unit / tests/unit/orchestration/test_cell_failures.py::test_m51_03_03_error_phase_recorded PASSED` | pass |
| C22 | `run unit / tests/unit/orchestration/test_cell_failures.py::test_m51_03_04_error_details_recorded PASSED` | pass |
| C23 | `run unit / tests/unit/orchestration/test_cell_failures.py::test_m51_03_05_no_coercion_to_zero PASSED` | pass |
| C24 | `run unit / tests/unit/orchestration/test_cell_failures.py::test_m51_03_06_fail_fast_propagates PASSED` | pass |
| C25 | `run unit / tests/unit/orchestration/test_cell_codecs.py::test_m51_04_01_cell_result_to_dict PASSED` | pass |
| C26 | `run unit / tests/unit/orchestration/test_cell_codecs.py::test_m51_04_02_cell_result_from_dict PASSED` | pass |
| C27 | `run unit / tests/unit/orchestration/test_cell_codecs.py::test_m51_04_03_prediction_record_to_dict PASSED` | pass |
| C28 | `run unit / tests/unit/orchestration/test_cell_codecs.py::test_m51_04_04_prediction_record_from_dict PASSED` | pass |
| C29 | `run unit / tests/unit/orchestration/test_cell_codecs.py::test_m51_04_05_atomic_save_artifacts PASSED` | pass |
| C30 | `run unit / tests/unit/orchestration/test_cell_codecs.py::test_m51_04_06_overwrite_protection PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/orchestration/test_oof_aggregation.py::test_ach_m5_01_serialization_roundtrip_preserves_none_std PASSED [ 85%]
tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_01_partial_coverage_on_fold_failure PASSED [ 86%]
tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_02_missing_observations_warning PASSED [ 87%]
tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_03_total_failure_raises_integrity_error PASSED [ 89%]
tests/unit/orchestration/test_oof_metrics.py::test_m53_02_01_pooled_oof_metrics_evaluation PASSED [ 90%]
tests/unit/orchestration/test_oof_metrics.py::test_m53_02_02_fold_aggregation_statistics PASSED [ 91%]
tests/unit/orchestration/test_oof_metrics.py::test_m53_02_03_undefined_nan_resilience PASSED [ 92%]
tests/unit/orchestration/test_oof_metrics.py::test_m53_02_04_metrics_scopes_distinction PASSED [ 93%]
tests/unit/orchestration/test_oof_storage.py::test_m53_03_01_save_oof_predictions_atomic PASSED [ 95%]
tests/unit/orchestration/test_oof_storage.py::test_m53_03_02_load_oof_predictions PASSED [ 96%]
tests/unit/orchestration/test_oof_storage.py::test_m53_03_03_codecs_roundtrip_fidelity PASSED [ 97%]
tests/unit/orchestration/test_oof_storage.py::test_m53_03_04_save_oof_no_overwrite_protection PASSED [ 98%]
tests/unit/orchestration/test_oof_storage.py::test_oof_invariants_validation PASSED [100%]

============================== 82 passed in 0.32s ==============================
```

`Run integration` - exit 0

```
configfile: pyproject.toml
collecting ... collected 10 items

tests/integration/orchestration/test_cell_integration.py::test_m51_02_08_end_to_end_cell_lifecycle PASSED [ 10%]
tests/integration/orchestration/test_cell_integration.py::test_m51_02_09_anti_leakage_adversarial PASSED [ 20%]
tests/integration/orchestration/test_cell_integration.py::test_orchestration_runtime_purity_xcut_02 PASSED [ 30%]
tests/integration/orchestration/test_matrix_integration.py::test_m52_06_01_public_api_exports PASSED [ 40%]
tests/integration/orchestration/test_matrix_integration.py::test_m52_06_02_end_to_end_matrix_lifecycle PASSED [ 50%]
tests/integration/orchestration/test_matrix_integration.py::test_m52_06_03_end_to_end_crash_recovery_resume PASSED [ 60%]
tests/integration/orchestration/test_matrix_integration.py::test_m52_06_04_runtime_purity_xcut_02 PASSED [ 70%]
tests/integration/orchestration/test_oof_integration.py::test_m53_06_01_public_api_exports PASSED [ 80%]
tests/integration/orchestration/test_oof_integration.py::test_m53_06_02_end_to_end_matrix_to_oof_gate PASSED [ 90%]
tests/integration/orchestration/test_oof_integration.py::test_m53_06_03_runtime_purity_xcut_02 PASSED [100%]

============================== 10 passed in 0.67s ==============================
```
