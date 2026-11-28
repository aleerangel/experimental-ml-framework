# m11-4-wave1-polish proofs

**HEAD**: 5ebc6ec
**Tree**: clean
**Shell**: /bin/sh
**Result**: 3 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run m11_4_e2e / test_m11_4_run_experiment_planned_pairs_and_pareto PASSED` | pass |
| C2 | `run m11_4_perf / test_m11_4_nested_cv_caches_inner_fold_preprocessing PASSED` | pass |
| C3 | `run m11_4_e2e / test_m11_4_docs_symbols_synced PASSED` | pass |

## Output

`Run m11_4_e2e` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 2 items

tests/integration/reporting/test_m11_4_wave1_polish_e2e.py::test_m11_4_run_experiment_planned_pairs_and_pareto PASSED [ 50%]
tests/integration/reporting/test_m11_4_wave1_polish_e2e.py::test_m11_4_docs_symbols_synced PASSED [100%]

============================== 2 passed in 2.05s ===============================
```

`Run m11_4_perf` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 11 items / 9 deselected / 2 selected

tests/unit/tuning/test_tuning_execution.py::test_m11_4_nested_cv_caches_inner_fold_preprocessing PASSED [ 50%]
tests/unit/orchestration/test_matrix_engine_parallel.py::test_m11_4_process_pool_backend PASSED [100%]

======================= 2 passed, 9 deselected in 0.18s ========================
```
