# m5-2-matrix-executor-checkpointing proofs

**HEAD**: 7850a10
**Tree**: clean
**Shell**: /bin/sh
**Result**: 30 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/orchestration/test_matrix_builder.py::test_m52_01_01_build_cell_matrix_cartesian PASSED` | pass |
| C2 | `run unit / tests/unit/orchestration/test_matrix_builder.py::test_m52_01_02_build_cell_matrix_canonical_sorting` | pass |
| C3 | `run unit / tests/unit/orchestration/test_matrix_builder.py::test_m52_01_03_cell_descriptor_canonical_id PASSED` | pass |
| C4 | `run unit / tests/unit/orchestration/test_matrix_builder.py::test_m52_01_04_derive_cell_seed_determinism PASSED` | pass |
| C5 | `run unit / tests/unit/orchestration/test_matrix_builder.py::test_m52_01_05_derive_cell_seed_dispersion PASSED` | pass |
| C6 | `run unit / tests/unit/orchestration/test_matrix_state.py::test_m52_02_01_matrix_execution_state_fields PASSED` | pass |
| C7 | `run unit / tests/unit/orchestration/test_matrix_state.py::test_m52_02_02_with_cell_update_immutability PASSED` | pass |
| C8 | `run unit / tests/unit/orchestration/test_matrix_state.py::test_m52_02_03_state_to_dict_json_serializable PASSE` | pass |
| C9 | `run unit / tests/unit/orchestration/test_matrix_state.py::test_m52_02_04_state_from_dict_roundtrip PASSED` | pass |
| C10 | `run unit / tests/unit/orchestration/test_matrix_state.py::test_m52_02_05_save_and_load_execution_state PASSED` | pass |
| C11 | `run unit / tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_01_sequential_execution_orde` | pass |
| C12 | `run unit / tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_02_atomic_artifacts_written ` | pass |
| C13 | `run unit / tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_03_incremental_state_flushed` | pass |
| C14 | `run unit / tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_04_fault_tolerant_continues ` | pass |
| C15 | `run unit / tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_05_fail_fast_halts PASSED` | pass |
| C16 | `run unit / tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_06_progress_callback_events ` | pass |
| C17 | `run unit / tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_07_cancellation_marks_cancel` | pass |
| C18 | `run unit / tests/unit/orchestration/test_matrix_engine_parallel.py::test_m52_04_01_parallel_dispatch PASSED` | pass |
| C19 | `run unit / tests/unit/orchestration/test_matrix_engine_parallel.py::test_m52_04_02_thread_safe_state_updates P` | pass |
| C20 | `run unit / tests/unit/orchestration/test_matrix_engine_parallel.py::test_m52_04_03_parallel_sequential_parity ` | pass |
| C21 | `run unit / tests/unit/orchestration/test_matrix_engine_parallel.py::test_m52_04_04_parallel_cell_failure_handl` | pass |
| C22 | `run unit / tests/unit/orchestration/test_matrix_resume.py::test_m52_05_01_resume_loads_and_verifies PASSED` | pass |
| C23 | `run unit / tests/unit/orchestration/test_matrix_resume.py::test_m52_05_02_resume_skips_completed_cells PASSED` | pass |
| C24 | `run unit / tests/unit/orchestration/test_matrix_resume.py::test_m52_05_03_resume_reexecutes_missing_artifacts ` | pass |
| C25 | `run unit / tests/unit/orchestration/test_matrix_resume.py::test_m52_05_04_resume_executes_pending_cells PASSED` | pass |
| C26 | `run unit / tests/unit/orchestration/test_matrix_resume.py::test_m52_05_05_resume_retries_failed_cells PASSED` | pass |
| C27 | `run integration / tests/integration/orchestration/test_matrix_integration.py::test_m52_06_01_public_api_export` | pass |
| C28 | `run integration / tests/integration/orchestration/test_matrix_integration.py::test_m52_06_02_end_to_end_matrix` | pass |
| C29 | `run integration / tests/integration/orchestration/test_matrix_integration.py::test_m52_06_03_end_to_end_crash_` | pass |
| C30 | `run integration / tests/integration/orchestration/test_matrix_integration.py::test_m52_06_04_runtime_purity_xc` | pass |

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

============================== 82 passed in 0.35s ==============================
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

============================== 10 passed in 0.63s ==============================
```
