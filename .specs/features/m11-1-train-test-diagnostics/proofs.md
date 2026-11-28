# m11-1-train-test-diagnostics proofs

**HEAD**: 33ffe60
**Tree**: dirty - docs/referencia/api_python.md
**Shell**: /bin/sh
**Result**: 3 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run m11_1_unit / test_m11_1_train_metrics_opt_in_and_storage PASSED` | pass |
| C2 | `run m11_1_unit / test_m11_1_train_metrics_consolidated_isolated_from_dev_cv PASSED` | pass |
| C3 | `run m11_1_e2e / test_m11_1_e2e_train_vs_test_table_and_figure PASSED` | pass |

## Output

`Run m11_1_unit` - exit 0

```
tests/unit/orchestration/test_cell_execution.py::test_m51_02_09_anti_leakage_adversarial PASSED [ 42%]
tests/unit/orchestration/test_cell_execution.py::test_m11_1_train_metrics_opt_in_and_storage PASSED [ 47%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_groups_by_configuration PASSED [ 52%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_coverage_status_mapping PASSED [ 57%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_failed_and_cancelled_folds_recorded PASSED [ 61%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_multi_fold PASSED [ 66%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_single_fold PASSED [ 71%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_zero_valid PASSED [ 76%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_incorporates_pooled_oof PASSED [ 80%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_timing_aggregation PASSED [ 85%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_feature_stability PASSED [ 90%]
tests/unit/statistics/test_consolidation.py::test_final_holdout_isolated_from_dev_cv_consolidation PASSED [ 95%]
tests/unit/statistics/test_consolidation.py::test_m11_1_train_metrics_consolidated_isolated_from_dev_cv PASSED [100%]

============================== 21 passed in 0.40s ==============================
```

`Run m11_1_e2e` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 1 item

tests/integration/reporting/test_m11_1_train_test_e2e.py::test_m11_1_e2e_train_vs_test_table_and_figure PASSED [100%]

============================== 1 passed in 3.30s ===============================
```
