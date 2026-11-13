# m5-4-cli-run-end-to-end proofs

**HEAD**: 0d46ee0
**Tree**: dirty - src/experimental_ml/cli/cmd_run.py, src/experimental_ml/orchestration/codecs.py, src/experimental_ml/orchestration/engine.py, src/experimental_ml/orchestration/oof.py, src/experimental_ml/orchestration/state.py
**Shell**: /bin/sh
**Result**: 22 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_01_01_cli_run_help_and_subparsers PASSED` | pass |
| C2 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_01_02_run_start_args_parsing PASSED` | pass |
| C3 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_01_03_run_resume_args_parsing PASSED` | pass |
| C4 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_01_04_run_status_args_parsing PASSED` | pass |
| C5 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_01_05_run_verify_args_parsing PASSED` | pass |
| C6 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_02_01_run_start_default_execution PASSED` | pass |
| C7 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_02_02_run_start_custom_run_dir PASSED` | pass |
| C8 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_02_03_run_start_parallel_dispatch PASSED` | pass |
| C9 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_02_04_run_start_fail_fast PASSED` | pass |
| C10 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_02_05_run_start_no_oof PASSED` | pass |
| C11 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_02_06_run_start_overwrite_protection PASSED` | pass |
| C12 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_03_01_run_resume_skips_completed PASSED` | pass |
| C13 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_03_02_run_resume_retry_failed PASSED` | pass |
| C14 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_03_03_run_status_read_only PASSED` | pass |
| C15 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_03_04_run_status_missing_state_returns_2 PASSED` | pass |
| C16 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_04_01_run_verify_valid_gate PASSED` | pass |
| C17 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_04_02_run_verify_corrupted_gate_returns_2 PASSED` | pass |
| C18 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_04_03_domain_errors_exit_code_2_no_traceback PASSED` | pass |
| C19 | `run unit / tests/unit/cli/test_cli_run.py::test_m54_04_04_hash_suppression_cli_11 PASSED` | pass |
| C20 | `run integration / tests/integration/cli/test_run_e2e.py::test_m54_05_01_e2e_cli_pipeline_lifecycle PASSED` | pass |
| C21 | `run integration / tests/integration/cli/test_run_e2e.py::test_m54_05_02_e2e_cli_crash_recovery PASSED` | pass |
| C22 | `run integration / tests/integration/cli/test_run_e2e.py::test_m54_05_03_cli_runtime_purity_xcut_02 PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/cli/test_cli_run.py::test_m54_02_02_run_start_custom_run_dir PASSED [ 36%]
tests/unit/cli/test_cli_run.py::test_m54_02_03_run_start_parallel_dispatch PASSED [ 42%]
tests/unit/cli/test_cli_run.py::test_m54_02_04_run_start_fail_fast PASSED [ 47%]
tests/unit/cli/test_cli_run.py::test_m54_02_05_run_start_no_oof PASSED   [ 52%]
tests/unit/cli/test_cli_run.py::test_m54_02_06_run_start_overwrite_protection PASSED [ 57%]
tests/unit/cli/test_cli_run.py::test_m54_03_01_run_resume_skips_completed PASSED [ 63%]
tests/unit/cli/test_cli_run.py::test_m54_03_02_run_resume_retry_failed PASSED [ 68%]
tests/unit/cli/test_cli_run.py::test_m54_03_03_run_status_read_only PASSED [ 73%]
tests/unit/cli/test_cli_run.py::test_m54_03_04_run_status_missing_state_returns_2 PASSED [ 78%]
tests/unit/cli/test_cli_run.py::test_m54_04_01_run_verify_valid_gate PASSED [ 84%]
tests/unit/cli/test_cli_run.py::test_m54_04_02_run_verify_corrupted_gate_returns_2 PASSED [ 89%]
tests/unit/cli/test_cli_run.py::test_m54_04_03_domain_errors_exit_code_2_no_traceback PASSED [ 94%]
tests/unit/cli/test_cli_run.py::test_m54_04_04_hash_suppression_cli_11 PASSED [100%]

============================== 19 passed in 0.58s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/cli/test_run_e2e.py::test_m54_05_01_e2e_cli_pipeline_lifecycle PASSED [ 33%]
tests/integration/cli/test_run_e2e.py::test_m54_05_02_e2e_cli_crash_recovery PASSED [ 66%]
tests/integration/cli/test_run_e2e.py::test_m54_05_03_cli_runtime_purity_xcut_02 PASSED [100%]

============================== 3 passed in 2.77s ===============================
```
