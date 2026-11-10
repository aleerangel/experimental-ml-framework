# m3-4-cli-end-to-end proofs

**HEAD**: 99b5857
**Tree**: clean
**Shell**: /bin/sh
**Result**: 8 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/cli/test_cmd_features.py::test_feat_01_features_help PASSED` | pass |
| C2 | `run unit / tests/unit/cli/test_cmd_features.py::test_feat_02_features_explore_success PASSED` | pass |
| C3 | `run unit / tests/unit/cli/test_cmd_features.py::test_feat_03_features_explore_overwrite_protection PASSED` | pass |
| C4 | `run unit / tests/unit/cli/test_cmd_features.py::test_feat_04_features_scenarios_success PASSED` | pass |
| C5 | `run unit / tests/unit/cli/test_cmd_features.py::test_feat_05_features_scenarios_rejection PASSED` | pass |
| C6 | `run unit / tests/unit/cli/test_cmd_features.py::test_feat_06_features_verify_gate PASSED` | pass |
| C7 | `run unit / tests/unit/cli/test_cmd_features.py::test_feat_07_cli_purity PASSED` | pass |
| C8 | `run integration / tests/integration/features/test_features_cli_integration.py::test_feat_08_end_to_end_cli_pip` | pass |

## Output

`Run unit` - exit 0

```
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 7 items

tests/unit/cli/test_cmd_features.py::test_feat_01_features_help PASSED   [ 14%]
tests/unit/cli/test_cmd_features.py::test_feat_02_features_explore_success PASSED [ 28%]
tests/unit/cli/test_cmd_features.py::test_feat_03_features_explore_overwrite_protection PASSED [ 42%]
tests/unit/cli/test_cmd_features.py::test_feat_04_features_scenarios_success PASSED [ 57%]
tests/unit/cli/test_cmd_features.py::test_feat_05_features_scenarios_rejection PASSED [ 71%]
tests/unit/cli/test_cmd_features.py::test_feat_06_features_verify_gate PASSED [ 85%]
tests/unit/cli/test_cmd_features.py::test_feat_07_cli_purity PASSED      [100%]

============================== 7 passed in 0.40s ===============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 1 item

tests/integration/features/test_features_cli_integration.py::test_feat_08_end_to_end_cli_pipeline PASSED [100%]

============================== 1 passed in 1.72s ===============================
```
