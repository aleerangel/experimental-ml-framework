# m9-intra-fold-imputation-encoding-holdout proofs

**HEAD**: 31fefba
**Tree**: dirty - docs/referencia/api_python.md
**Shell**: /bin/sh
**Result**: 5 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run m9_unit / test_simple_imputer_mean_median_mode_and_all_missing PASSED` | pass |
| C2 | `run m9_unit / test_categorical_encoders_1to1_and_unseen_categories PASSED` | pass |
| C3 | `run m9_e2e / test_deferred_missing_and_categorical_e2e_no_leakage PASSED` | pass |
| C4 | `run m9_unit / test_final_holdout_isolated_from_dev_cv_consolidation PASSED` | pass |
| Build | `.venv/bin/pytest tests/ -q` | pass |

## Output

`Run m9_unit` - exit 0

```
tests/unit/orchestration/test_matrix_builder.py::test_m52_01_04_derive_cell_seed_determinism PASSED [ 40%]
tests/unit/orchestration/test_matrix_builder.py::test_m52_01_05_derive_cell_seed_dispersion PASSED [ 45%]
tests/unit/orchestration/test_matrix_builder.py::test_build_cell_matrix_cv_and_holdout_adds_final_holdout PASSED [ 50%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_groups_by_configuration PASSED [ 55%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_coverage_status_mapping PASSED [ 60%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_failed_and_cancelled_folds_recorded PASSED [ 65%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_multi_fold PASSED [ 70%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_single_fold PASSED [ 75%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_metric_stats_zero_valid PASSED [ 80%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_incorporates_pooled_oof PASSED [ 85%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_timing_aggregation PASSED [ 90%]
tests/unit/statistics/test_consolidation.py::test_consolidate_descriptive_feature_stability PASSED [ 95%]
tests/unit/statistics/test_consolidation.py::test_final_holdout_isolated_from_dev_cv_consolidation PASSED [100%]

============================== 20 passed in 0.16s ==============================
```

`Run m9_e2e` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 1 item

tests/integration/test_m9_deferred_preprocessing_e2e.py::test_deferred_missing_and_categorical_e2e_no_leakage PASSED [100%]

============================== 1 passed in 0.32s ===============================
```
