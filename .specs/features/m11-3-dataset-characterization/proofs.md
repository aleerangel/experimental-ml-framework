# m11-3-dataset-characterization proofs

**HEAD**: bc994e5
**Tree**: dirty - docs/referencia/api_python.md
**Shell**: /bin/sh
**Result**: 3 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run m11_3_prof / test_m11_3_numeric_moments_and_extended_profile PASSED` | pass |
| C2 | `run m11_3_feat / test_m11_3_vif_distance_corr_and_linearity PASSED` | pass |
| C3 | `run m11_3_e2e / test_m11_3_e2e_opt_in_dataset_meta_features PASSED` | pass |

## Output

`Run m11_3_prof` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 14 items / 13 deselected / 1 selected

tests/unit/data/test_profiling.py::test_m11_3_numeric_moments_and_extended_profile PASSED [100%]

======================= 1 passed, 13 deselected in 0.12s =======================
```

`Run m11_3_feat` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 11 items / 9 deselected / 2 selected

tests/unit/features/test_stats.py::test_m11_3_vif_distance_corr_and_linearity PASSED [ 50%]
tests/unit/features/test_exploration.py::test_m11_3_explore_features_extended_opt_in PASSED [100%]

======================= 2 passed, 9 deselected in 0.11s ========================
```

`Run m11_3_e2e` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 1 item

tests/integration/reporting/test_m11_3_dataset_characterization_e2e.py::test_m11_3_e2e_opt_in_dataset_meta_features PASSED [100%]

============================== 1 passed in 3.47s ===============================
```
