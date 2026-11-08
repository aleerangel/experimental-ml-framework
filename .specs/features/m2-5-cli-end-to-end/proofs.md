# m2-5-cli-end-to-end proofs

**HEAD**: 5b67ef6
**Tree**: clean
**Shell**: /bin/sh
**Result**: 10 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/cli/test_cmd_data.py::test_cli_01_data_profile_success PASSED` | pass |
| C2 | `run unit / tests/unit/cli/test_cmd_data.py::test_cli_02_data_sanitize_ready_plan PASSED` | pass |
| C3 | `run unit / tests/unit/cli/test_cmd_data.py::test_cli_03_data_sanitize_incomplete_plan_rejected PASSED` | pass |
| C4 | `run unit / tests/unit/cli/test_cmd_partition.py::test_cli_04_partition_build_success PASSED` | pass |
| C5 | `run unit / tests/unit/cli/test_cmd_partition.py::test_cli_05_partition_verify_clean_and_tampered PASSED` | pass |
| C6 | `run unit / tests/unit/cli/test_cli_main.py::test_cli_06_domain_error_handling_and_exit_code_2 PASSED` | pass |
| C7 | `run unit / tests/unit/cli/test_cli_main.py::test_cli_09_base_cli_compatibility_and_help PASSED` | pass |
| C8 | `run unit / tests/unit/cli/test_cli_main.py::test_cli_10_architectural_pure_cli_no_numpy_no_hashlib PASSED` | pass |
| C9 | `run unit / tests/unit/cli/test_cli_main.py::test_cli_11_no_hash_digests_in_output PASSED` | pass |
| C10 | `run integration / tests/integration/test_cli_end_to_end_integration.py::test_cli_12_end_to_end_subprocess_acce` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/cli/test_cli_main.py::test_cli_09_base_cli_compatibility_and_help PASSED [  7%]
tests/unit/cli/test_cli_main.py::test_cli_06_domain_error_handling_and_exit_code_2 PASSED [ 15%]
tests/unit/cli/test_cli_main.py::test_cli_10_architectural_pure_cli_no_numpy_no_hashlib PASSED [ 23%]
tests/unit/cli/test_cli_main.py::test_cli_11_no_hash_digests_in_output PASSED [ 30%]
tests/unit/cli/test_cmd_data.py::test_cli_01_data_profile_success PASSED [ 38%]
tests/unit/cli/test_cmd_data.py::test_cli_03_data_sanitize_incomplete_plan_rejected PASSED [ 46%]
tests/unit/cli/test_cmd_data.py::test_cli_02_data_sanitize_ready_plan PASSED [ 53%]
tests/unit/cli/test_cmd_data.py::test_cli_08_data_profile_force_flag_behavior PASSED [ 61%]
tests/unit/cli/test_cmd_partition.py::test_cli_04_partition_build_success PASSED [ 69%]
tests/unit/cli/test_cmd_partition.py::test_cli_04_partition_build_seed_override PASSED [ 76%]
tests/unit/cli/test_cmd_partition.py::test_cli_05_partition_verify_clean_and_tampered PASSED [ 84%]
tests/unit/cli/test_cmd_partition.py::test_cli_07_upstream_gate_missing_blocked PASSED [ 92%]
tests/unit/cli/test_cmd_partition.py::test_cli_08_partition_build_force_flag_behavior PASSED [100%]

============================== 13 passed in 0.26s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 1 item

tests/integration/test_cli_end_to_end_integration.py::test_cli_12_end_to_end_subprocess_acceptance_scenario PASSED [100%]

============================== 1 passed in 1.05s ===============================
```
