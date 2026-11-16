# pos-1-mega-auditoria-mvp proofs

**HEAD**: 65cb86c
**Tree**: clean
**Shell**: /bin/sh
**Result**: 3 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/integration/test_mvp_audit_invariants.py::test_audit_xcut02_runtime_purity_ast PASSED` | pass |
| C2 | `run unit / tests/integration/test_mvp_audit_invariants.py::test_audit_stage_gates_cli_and_domain_neutrality PA` | pass |
| C3 | `run unit / tests/integration/test_mvp_audit_invariants.py::test_audit_report_zero_open_p0_p1 PASSED` | pass |

## Output

`Run unit` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/test_mvp_audit_invariants.py::test_audit_xcut02_runtime_purity_ast PASSED [ 33%]
tests/integration/test_mvp_audit_invariants.py::test_audit_stage_gates_cli_and_domain_neutrality PASSED [ 66%]
tests/integration/test_mvp_audit_invariants.py::test_audit_report_zero_open_p0_p1 PASSED [100%]

============================== 3 passed in 0.37s ===============================
```
