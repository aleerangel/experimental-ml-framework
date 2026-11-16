# m7-4-cli-report-end-to-end proofs

**HEAD**: 197fc53
**Tree**: clean
**Shell**: /bin/sh
**Result**: 6 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/cli/test_cli_report.py::test_m74_01_cli_report_generate PASSED` | pass |
| C2 | `run unit / tests/unit/cli/test_cli_report.py::test_m74_01_cli_report_export_modes PASSED` | pass |
| C3 | `run unit / tests/unit/cli/test_cli_report.py::test_m74_01_cli_force_protection PASSED` | pass |
| C4 | `run unit / tests/unit/cli/test_cli_report.py::test_m74_02_cli_report_verify_portable PASSED` | pass |
| C5 | `run unit / tests/unit/cli/test_cli_report.py::test_m74_02_cli_report_verify_tamper_fails PASSED` | pass |
| C6 | `run unit / tests/integration/reporting/test_m74_e2e.py::test_m74_e2e_stage1_to_stage6_cli PASSED` | pass |

## Output

`Run unit` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 6 items

tests/unit/cli/test_cli_report.py::test_m74_01_cli_report_generate PASSED [ 16%]
tests/unit/cli/test_cli_report.py::test_m74_01_cli_report_export_modes PASSED [ 33%]
tests/unit/cli/test_cli_report.py::test_m74_01_cli_force_protection PASSED [ 50%]
tests/unit/cli/test_cli_report.py::test_m74_02_cli_report_verify_portable PASSED [ 66%]
tests/unit/cli/test_cli_report.py::test_m74_02_cli_report_verify_tamper_fails PASSED [ 83%]
tests/integration/reporting/test_m74_e2e.py::test_m74_e2e_stage1_to_stage6_cli PASSED [100%]

============================== 6 passed in 2.77s ===============================
```
