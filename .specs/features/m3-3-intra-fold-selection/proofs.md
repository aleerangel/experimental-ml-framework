# m3-3-intra-fold-selection proofs

**HEAD**: 044bc2c
**Tree**: clean
**Shell**: /bin/sh
**Result**: 8 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/features/test_selection.py::test_sel_01_selection_result_immutability PASSED` | pass |
| C2 | `run unit / tests/unit/features/test_selection.py::test_sel_02_fixed_scenario_bypass PASSED` | pass |
| C3 | `run unit / tests/unit/features/test_selection.py::test_sel_03_variance_threshold_selection PASSED` | pass |
| C4 | `run unit / tests/unit/features/test_selection.py::test_sel_04_top_k_relevance_selection PASSED` | pass |
| C5 | `run unit / tests/unit/features/test_selection.py::test_sel_05_apply_feature_selection PASSED` | pass |
| C6 | `run unit / tests/unit/features/test_stability.py::test_sel_06_selection_stability_metrics PASSED` | pass |
| C7 | `run unit / tests/unit/features/test_selection.py::test_sel_07_empty_selection_rejection PASSED` | pass |
| C8 | `run integration / tests/integration/features/test_selection_integration.py::test_sel_08_multi_fold_selection_p` | pass |

## Output

`Run unit` - exit 0

```
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 8 items

tests/unit/features/test_selection.py::test_sel_01_selection_result_immutability PASSED [ 12%]
tests/unit/features/test_selection.py::test_sel_02_fixed_scenario_bypass PASSED [ 25%]
tests/unit/features/test_selection.py::test_sel_03_variance_threshold_selection PASSED [ 37%]
tests/unit/features/test_selection.py::test_sel_04_top_k_relevance_selection PASSED [ 50%]
tests/unit/features/test_selection.py::test_sel_07_empty_selection_rejection PASSED [ 62%]
tests/unit/features/test_selection.py::test_sel_05_apply_feature_selection PASSED [ 75%]
tests/unit/features/test_stability.py::test_sel_06_selection_stability_metrics PASSED [ 87%]
tests/unit/features/test_stability.py::test_stability_input_validations PASSED [100%]

============================== 8 passed in 0.10s ===============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 2 items

tests/integration/features/test_selection_integration.py::test_sel_08_multi_fold_selection_pipeline PASSED [ 50%]
tests/integration/features/test_selection_integration.py::test_xcut_02_runtime_purity_selection PASSED [100%]

============================== 2 passed in 0.19s ===============================
```
