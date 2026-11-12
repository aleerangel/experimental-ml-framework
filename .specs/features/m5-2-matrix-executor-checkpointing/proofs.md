# m5-2-matrix-executor-checkpointing proofs

**HEAD**: 9ecde37
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
tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_05_fail_fast_halts PASSED [ 78%]
tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_06_progress_callback_events PASSED [ 80%]
tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_07_cancellation_marks_cancelled PASSED [ 82%]
tests/unit/orchestration/test_matrix_resume.py::test_m52_05_01_resume_loads_and_verifies PASSED [ 83%]
tests/unit/orchestration/test_matrix_resume.py::test_m52_05_02_resume_skips_completed_cells PASSED [ 85%]
tests/unit/orchestration/test_matrix_resume.py::test_m52_05_03_resume_reexecutes_missing_artifacts PASSED [ 87%]
tests/unit/orchestration/test_matrix_resume.py::test_m52_05_04_resume_executes_pending_cells PASSED [ 89%]
tests/unit/orchestration/test_matrix_resume.py::test_m52_05_05_resume_retries_failed_cells PASSED [ 91%]
tests/unit/orchestration/test_matrix_state.py::test_m52_02_01_matrix_execution_state_fields PASSED [ 92%]
tests/unit/orchestration/test_matrix_state.py::test_m52_02_02_with_cell_update_immutability PASSED [ 94%]
tests/unit/orchestration/test_matrix_state.py::test_m52_02_03_state_to_dict_json_serializable PASSED [ 96%]
tests/unit/orchestration/test_matrix_state.py::test_m52_02_04_state_from_dict_roundtrip PASSED [ 98%]
tests/unit/orchestration/test_matrix_state.py::test_m52_02_05_save_and_load_execution_state PASSED [100%]

============================== 56 passed in 0.39s ==============================
```

`Run integration` - exit 0

```
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 7 items

tests/integration/orchestration/test_cell_integration.py::test_m51_02_08_end_to_end_cell_lifecycle PASSED [ 14%]
tests/integration/orchestration/test_cell_integration.py::test_m51_02_09_anti_leakage_adversarial PASSED [ 28%]
tests/integration/orchestration/test_cell_integration.py::test_orchestration_runtime_purity_xcut_02 PASSED [ 42%]
tests/integration/orchestration/test_matrix_integration.py::test_m52_06_01_public_api_exports PASSED [ 57%]
tests/integration/orchestration/test_matrix_integration.py::test_m52_06_02_end_to_end_matrix_lifecycle PASSED [ 71%]
tests/integration/orchestration/test_matrix_integration.py::test_m52_06_03_end_to_end_crash_recovery_resume PASSED [ 85%]
tests/integration/orchestration/test_matrix_integration.py::test_m52_06_04_runtime_purity_xcut_02 PASSED [100%]

============================== 7 passed in 0.50s ===============================
```
