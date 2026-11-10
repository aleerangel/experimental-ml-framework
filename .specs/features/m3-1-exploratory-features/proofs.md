# m3-1-exploratory-features proofs

**HEAD**: b757812
**Tree**: clean
**Shell**: /bin/sh
**Result**: 8 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/features/test_exploration.py::test_exp_01_mandatory_scope_and_warnings PASSED` | pass |
| C2 | `run unit / tests/unit/features/test_stats.py::test_exp_02_pearson_and_spearman_continuous PASSED` | pass |
| C3 | `run unit / tests/unit/features/test_stats.py::test_exp_03_correlation_ratio_eta PASSED` | pass |
| C4 | `run unit / tests/unit/features/test_stats.py::test_exp_04_cramers_v PASSED` | pass |
| C5 | `run unit / tests/unit/features/test_stats.py::test_exp_05_degeneracy_and_undefined_nan PASSED` | pass |
| C6 | `run unit / tests/unit/features/test_exploration.py::test_exp_06_predictor_redundancy_and_sorting PASSED` | pass |
| C7 | `run unit / tests/unit/features/test_feature_types.py::test_exp_07_roundtrip_serialization PASSED` | pass |
| C8 | `run integration / tests/integration/features/test_features_integration.py::test_exp_08_end_to_end_pipeline PAS` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/features/test_exploration.py::test_exp_01_mandatory_scope_and_warnings PASSED [  7%]
tests/unit/features/test_exploration.py::test_exp_06_predictor_redundancy_and_sorting PASSED [ 15%]
tests/unit/features/test_exploration.py::test_exp_08_input_validation PASSED [ 23%]
tests/unit/features/test_exploration.py::test_classification_feature_associations PASSED [ 30%]
tests/unit/features/test_feature_types.py::test_scope_and_warnings_constants PASSED [ 38%]
tests/unit/features/test_feature_types.py::test_association_measure_immutability_and_validation PASSED [ 46%]
tests/unit/features/test_feature_types.py::test_redundancy_pair_immutability_and_validation PASSED [ 53%]
tests/unit/features/test_feature_types.py::test_report_scope_enforcement PASSED [ 61%]
tests/unit/features/test_feature_types.py::test_exp_07_roundtrip_serialization PASSED [ 69%]
tests/unit/features/test_stats.py::test_exp_02_pearson_and_spearman_continuous PASSED [ 76%]
tests/unit/features/test_stats.py::test_exp_03_correlation_ratio_eta PASSED [ 84%]
tests/unit/features/test_stats.py::test_exp_04_cramers_v PASSED          [ 92%]
tests/unit/features/test_stats.py::test_exp_05_degeneracy_and_undefined_nan PASSED [100%]

============================== 13 passed in 0.12s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 2 items

tests/integration/features/test_features_integration.py::test_exp_08_end_to_end_pipeline PASSED [ 50%]
tests/integration/features/test_features_integration.py::test_xcut_02_runtime_purity_subprocess PASSED [100%]

============================== 2 passed in 0.24s ===============================
```
