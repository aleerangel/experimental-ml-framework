# m5-3-oof-consolidation-stage-gate proofs

**HEAD**: 7850a10
**Tree**: clean
**Shell**: /bin/sh
**Result**: 25 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/orchestration/test_oof_storage.py::test_m53_03_01_save_oof_predictions_atomic PASSED` | pass |
| C2 | `run unit / tests/unit/orchestration/test_oof_storage.py::test_m53_03_02_load_oof_predictions PASSED` | pass |
| C3 | `run unit / tests/unit/orchestration/test_oof_storage.py::test_m53_03_03_codecs_roundtrip_fidelity PASSED` | pass |
| C4 | `run unit / tests/unit/orchestration/test_oof_storage.py::test_m53_03_04_save_oof_no_overwrite_protection PASSE` | pass |
| C5 | `run unit / tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_01_consolidate_aggregates_records PAS` | pass |
| C6 | `run unit / tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_02_canonical_sorting_by_obs_id PASSED` | pass |
| C7 | `run unit / tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_03_multi_fold_committee_statistics PA` | pass |
| C8 | `run unit / tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_04_single_fold_prediction_preservatio` | pass |
| C9 | `run unit / tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_05_classification_probability_pooling` | pass |
| C10 | `run unit / tests/unit/orchestration/test_oof_metrics.py::test_m53_02_01_pooled_oof_metrics_evaluation PASSED` | pass |
| C11 | `run unit / tests/unit/orchestration/test_oof_metrics.py::test_m53_02_02_fold_aggregation_statistics PASSED` | pass |
| C12 | `run unit / tests/unit/orchestration/test_oof_metrics.py::test_m53_02_03_undefined_nan_resilience PASSED` | pass |
| C13 | `run unit / tests/unit/orchestration/test_oof_metrics.py::test_m53_02_04_metrics_scopes_distinction PASSED` | pass |
| C14 | `run unit / tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_01_partial_coverage_on_fold_failu` | pass |
| C15 | `run unit / tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_02_missing_observations_warning P` | pass |
| C16 | `run unit / tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_03_total_failure_raises_integrity` | pass |
| C17 | `run unit / tests/unit/stages/test_stage_runs_gate.py::test_m53_04_01_upstream_gates_verification PASSED` | pass |
| C18 | `run unit / tests/unit/stages/test_stage_runs_gate.py::test_m53_04_02_missing_or_corrupt_state_raises PASSED` | pass |
| C19 | `run unit / tests/unit/stages/test_stage_runs_gate.py::test_m53_04_03_non_terminal_cell_status_raises PASSED` | pass |
| C20 | `run unit / tests/unit/stages/test_stage_runs_gate.py::test_m53_04_04_missing_cell_artifact_raises PASSED` | pass |
| C21 | `run unit / tests/unit/stages/test_stage_runs_gate.py::test_m53_04_05_cross_hashes_mismatch_raises PASSED` | pass |
| C22 | `run unit / tests/unit/stages/test_stage_runs_gate.py::test_m53_04_06_valid_runs_gate_returns_summary PASSED` | pass |
| C23 | `run integration / tests/integration/orchestration/test_oof_integration.py::test_m53_06_01_public_api_exports P` | pass |
| C24 | `run integration / tests/integration/orchestration/test_oof_integration.py::test_m53_06_02_end_to_end_matrix_to` | pass |
| C25 | `run integration / tests/integration/orchestration/test_oof_integration.py::test_m53_06_03_runtime_purity_xcut_` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/stages/test_models_stage_gate.py::test_m44_04_02_verify_models_gate_missing_or_empty PASSED [ 87%]
tests/unit/stages/test_models_stage_gate.py::test_m44_04_03_verify_models_gate_unmet_precondition PASSED [ 88%]
tests/unit/stages/test_stage_gates.py::test_store_05_hash_divergence_and_incomplete_plan_rejection PASSED [ 89%]
tests/unit/stages/test_stage_gates.py::test_store_06_splits_tampering_and_mismatch_rejection PASSED [ 90%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_01_upstream_gates_verification PASSED [ 91%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_02_missing_or_corrupt_state_raises PASSED [ 92%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_03_non_terminal_cell_status_raises PASSED [ 93%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_04_missing_cell_artifact_raises PASSED [ 94%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_05_cross_hashes_mismatch_raises PASSED [ 95%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_06_valid_runs_gate_returns_summary PASSED [ 96%]
tests/unit/stages/test_stage_runs_gate.py::test_ach_m5_03_stage_gate_with_failed_cell_returns_partial_ready PASSED [ 97%]
tests/unit/stages/test_stage_runs_gate.py::test_ach_m5_03_stage_gate_with_cancelled_cell_returns_partial_ready PASSED [ 98%]
tests/unit/stages/test_stage_runs_gate.py::test_ach_m5_03_subsequent_cell_divergent_partition_plan_id_raises PASSED [100%]

============================== 96 passed in 0.41s ==============================
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

============================== 10 passed in 0.55s ==============================
```
