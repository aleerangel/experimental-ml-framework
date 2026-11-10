# m3-2-feature-scenarios proofs

**HEAD**: f4b21f4
**Tree**: clean
**Shell**: /bin/sh
**Result**: 8 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/features/test_feature_scenarios.py::test_scn_01_feature_scenario_immutability PASSED` | pass |
| C2 | `run unit / tests/unit/features/test_feature_scenarios.py::test_scn_02_fixed_scenario_constraints PASSED` | pass |
| C3 | `run unit / tests/unit/features/test_feature_scenarios.py::test_scn_03_dynamic_scenario_anti_leakage PASSED` | pass |
| C4 | `run unit / tests/unit/features/test_feature_scenarios.py::test_scn_04_validate_scenarios_success PASSED` | pass |
| C5 | `run unit / tests/unit/features/test_feature_scenarios.py::test_scn_05_validate_scenarios_rejections PASSED` | pass |
| C6 | `run unit / tests/unit/features/test_feature_scenarios.py::test_scn_06_roundtrip_serialization PASSED` | pass |
| C7 | `run unit / tests/unit/features/test_scenarios_storage.py::test_scn_07_save_and_load_scenarios PASSED` | pass |
| C8 | `run integration / tests/integration/features/test_scenarios_integration.py::test_scn_08_end_to_end_scenarios_g` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/features/test_feature_scenarios.py::test_scn_05_validate_scenarios_rejections PASSED [ 42%]
tests/unit/features/test_feature_scenarios.py::test_scn_06_roundtrip_serialization PASSED [ 47%]
tests/unit/features/test_feature_types.py::test_scope_and_warnings_constants PASSED [ 52%]
tests/unit/features/test_feature_types.py::test_association_measure_immutability_and_validation PASSED [ 57%]
tests/unit/features/test_feature_types.py::test_redundancy_pair_immutability_and_validation PASSED [ 61%]
tests/unit/features/test_feature_types.py::test_report_scope_enforcement PASSED [ 66%]
tests/unit/features/test_feature_types.py::test_exp_07_roundtrip_serialization PASSED [ 71%]
tests/unit/features/test_scenarios_storage.py::test_scn_07_save_and_load_scenarios PASSED [ 76%]
tests/unit/features/test_scenarios_storage.py::test_verify_scenarios_gate_valid_and_failures PASSED [ 80%]
tests/unit/features/test_stats.py::test_exp_02_pearson_and_spearman_continuous PASSED [ 85%]
tests/unit/features/test_stats.py::test_exp_03_correlation_ratio_eta PASSED [ 90%]
tests/unit/features/test_stats.py::test_exp_04_cramers_v PASSED          [ 95%]
tests/unit/features/test_stats.py::test_exp_05_degeneracy_and_undefined_nan PASSED [100%]

============================== 21 passed in 0.12s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 2 items

tests/integration/features/test_scenarios_integration.py::test_scn_08_end_to_end_scenarios_gate PASSED [ 50%]
tests/integration/features/test_scenarios_integration.py::test_xcut_02_runtime_purity_scenarios PASSED [100%]

============================== 2 passed in 0.21s ===============================
```
