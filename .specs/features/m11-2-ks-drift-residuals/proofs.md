# m11-2-ks-drift-residuals proofs

**HEAD**: 79b91ce
**Tree**: dirty - docs/referencia/api_python.md
**Shell**: /bin/sh
**Result**: 3 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run m11_2_unit / test_m11_2_ks_2samp_and_lilliefors_pure_numpy PASSED` | pass |
| C2 | `run m11_2_unit / test_m11_2_partition_ks_drift_cv_holdout_and_temporal PASSED` | pass |
| C3 | `run m11_2_e2e / test_m11_2_e2e_opt_in_ks_drift_and_oof_qq_plot PASSED` | pass |

## Output

`Run m11_2_unit` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 2 items

tests/unit/statistics/test_ks_diagnostics.py::test_m11_2_ks_2samp_and_lilliefors_pure_numpy PASSED [ 50%]
tests/unit/statistics/test_ks_diagnostics.py::test_m11_2_partition_ks_drift_cv_holdout_and_temporal PASSED [100%]

============================== 2 passed in 0.15s ===============================
```

`Run m11_2_e2e` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 1 item

tests/integration/reporting/test_m11_2_ks_drift_residuals_e2e.py::test_m11_2_e2e_opt_in_ks_drift_and_oof_qq_plot PASSED [100%]

============================== 1 passed in 2.61s ===============================
```
