# m5-1-cell-execution-contracts proofs

**HEAD**: df82292
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
tests/unit/orchestration/test_cell_failures.py::test_m51_03_03_error_phase_recorded PASSED [ 60%]
tests/unit/orchestration/test_cell_failures.py::test_m51_03_04_error_details_recorded PASSED [ 63%]
tests/unit/orchestration/test_cell_failures.py::test_m51_03_05_no_coercion_to_zero PASSED [ 66%]
tests/unit/orchestration/test_cell_failures.py::test_m51_03_06_fail_fast_propagates PASSED [ 70%]
tests/unit/orchestration/test_cell_types.py::test_m51_01_01_execution_status_enum PASSED [ 73%]
tests/unit/orchestration/test_cell_types.py::test_m51_01_02_error_policy_enum PASSED [ 76%]
tests/unit/orchestration/test_cell_types.py::test_m51_01_03_cell_phase_enum PASSED [ 80%]
tests/unit/orchestration/test_cell_types.py::test_m51_01_04_cell_id_validation PASSED [ 83%]
tests/unit/orchestration/test_cell_types.py::test_m51_01_05_timing_breakdown_fields PASSED [ 86%]
tests/unit/orchestration/test_cell_types.py::test_m51_01_06_prediction_record_fields PASSED [ 90%]
tests/unit/orchestration/test_cell_types.py::test_m51_01_07_prediction_record_alignment PASSED [ 93%]
tests/unit/orchestration/test_cell_types.py::test_m51_01_08_cell_result_record_fields PASSED [ 96%]
tests/unit/orchestration/test_cell_types.py::test_m51_01_09_immutability PASSED [100%]

============================== 30 passed in 0.16s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/orchestration/test_cell_integration.py::test_m51_02_08_end_to_end_cell_lifecycle PASSED [ 33%]
tests/integration/orchestration/test_cell_integration.py::test_m51_02_09_anti_leakage_adversarial PASSED [ 66%]
tests/integration/orchestration/test_cell_integration.py::test_orchestration_runtime_purity_xcut_02 PASSED [100%]

============================== 3 passed in 0.30s ===============================
```
