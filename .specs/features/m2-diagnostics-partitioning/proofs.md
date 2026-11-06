# m2-diagnostics-partitioning proofs

**HEAD**: 2b6ee77
**Tree**: clean
**Shell**: /bin/sh
**Result**: 12 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/data/test_profiling.py::test_prof_01_structural_profile_and_column_profiles PASSED` | pass |
| C2 | `run unit / tests/unit/data/test_profiling.py::test_prof_02_numeric_distribution_statistics PASSED` | pass |
| C3 | `run unit / tests/unit/data/test_profiling.py::test_prof_03_categorical_distribution_and_frequencies PASSED` | pass |
| C4 | `run unit / tests/unit/data/test_profiling.py::test_prof_04_duplicate_rows_detection PASSED` | pass |
| C5 | `run unit / tests/unit/data/test_profiling.py::test_prof_05_target_profile_regression_and_classification PASSED` | pass |
| C6 | `run unit / tests/unit/data/test_profiling.py::test_prof_06_group_profile_statistics PASSED` | pass |
| C7 | `run unit / tests/unit/data/test_profiling.py::test_prof_07_catalog_findings_and_canonical_ordering PASSED` | pass |
| C8 | `run unit / tests/unit/data/test_profiling.py::test_prof_08_severity_separation_heuristics_vs_issues PASSED` | pass |
| C9 | `run unit / tests/unit/data/test_profiling.py::test_prof_09_binary_target_unmapped_and_class_count PASSED` | pass |
| C10 | `run integration / tests/integration/test_profiling_integration.py::test_prof_10_immutability_and_determinism P` | pass |
| C11 | `run unit / tests/unit/data/test_profiling.py::test_prof_11_profile_config_threshold_validation PASSED` | pass |
| C12 | `run unit / tests/unit/data/test_profiling.py::test_prof_12_fully_missing_column_handling PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/data/test_profiling.py::test_prof_11_profile_config_threshold_validation PASSED [  7%]
tests/unit/data/test_profiling.py::test_profiling_models_immutability_and_slots PASSED [ 15%]
tests/unit/data/test_profiling.py::test_prof_02_numeric_distribution_statistics PASSED [ 23%]
tests/unit/data/test_profiling.py::test_prof_03_categorical_distribution_and_frequencies PASSED [ 30%]
tests/unit/data/test_profiling.py::test_prof_12_fully_missing_column_handling PASSED [ 38%]
tests/unit/data/test_profiling.py::test_prof_04_duplicate_rows_detection PASSED [ 46%]
tests/unit/data/test_profiling.py::test_prof_05_target_profile_regression_and_classification PASSED [ 53%]
tests/unit/data/test_profiling.py::test_prof_06_group_profile_statistics PASSED [ 61%]
tests/unit/data/test_profiling.py::test_prof_07_catalog_findings_and_canonical_ordering PASSED [ 69%]
tests/unit/data/test_profiling.py::test_prof_08_severity_separation_heuristics_vs_issues PASSED [ 76%]
tests/unit/data/test_profiling.py::test_prof_09_binary_target_unmapped_and_class_count PASSED [ 84%]
tests/unit/data/test_profiling.py::test_prof_01_structural_profile_and_column_profiles PASSED [ 92%]
tests/unit/data/test_profiling.py::test_prof_10_immutability_and_determinism PASSED [100%]

============================== 13 passed in 0.14s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 5 items

tests/integration/test_profiling_integration.py::test_prof_10_immutability_and_determinism PASSED [ 20%]
tests/integration/test_profiling_integration.py::test_end_to_end_profiling_on_complex_dataset PASSED [ 40%]
tests/integration/test_profiling_integration.py::test_architectural_import_direction_xcut_01 PASSED [ 60%]
tests/integration/test_profiling_integration.py::test_single_runtime_dependency_xcut_02 PASSED [ 80%]
tests/integration/test_profiling_integration.py::test_exported_symbols_count_xcut_04 PASSED [100%]

============================== 5 passed in 0.20s ===============================
```
