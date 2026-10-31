# m1-1-setup-cli-smoke proofs

**HEAD**: de1860d
**Tree**: clean
**Shell**: /bin/sh
**Result**: 12 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run smoke / test_pyproject_metadata PASSED` | pass |
| C2 | `run smoke / test_package_version PASSED` | pass |
| C3 | `run smoke / test_dev_dependencies PASSED` | pass |
| C4 | `run smoke / test_cli_entrypoint_registered PASSED` | pass |
| C5 | `run smoke / test_editable_install_and_cli_on_path PASSED` | pass |
| C6 | `run smoke / test_cli_version_flag PASSED` | pass |
| C7 | `run smoke / test_cli_help_flag PASSED` | pass |
| C8 | `run smoke / test_cli_invalid_argument PASSED` | pass |
| C9 | `run smoke / test_cli_dependencies_pure_stdlib PASSED` | pass |
| C10 | `run smoke / test_smoke_discovery PASSED` | pass |
| C11 | `run smoke / test_version_non_empty PASSED` | pass |
| C12 | `run smoke / test_cli_observable_outcomes PASSED` | pass |

## Output

`Run smoke` - exit 0

```

tests/test_smoke.py::test_pyproject_metadata PASSED                      [  8%]
tests/test_smoke.py::test_package_version PASSED                         [ 16%]
tests/test_smoke.py::test_dev_dependencies PASSED                        [ 25%]
tests/test_smoke.py::test_cli_entrypoint_registered PASSED               [ 33%]
tests/test_smoke.py::test_editable_install_and_cli_on_path PASSED        [ 41%]
tests/test_smoke.py::test_cli_version_flag PASSED                        [ 50%]
tests/test_smoke.py::test_cli_help_flag PASSED                           [ 58%]
tests/test_smoke.py::test_cli_invalid_argument PASSED                    [ 66%]
tests/test_smoke.py::test_cli_dependencies_pure_stdlib PASSED            [ 75%]
tests/test_smoke.py::test_smoke_discovery PASSED                         [ 83%]
tests/test_smoke.py::test_version_non_empty PASSED                       [ 91%]
tests/test_smoke.py::test_cli_observable_outcomes PASSED                 [100%]

============================== 12 passed in 0.38s ==============================
```
