# m4-3-nested-tuning proofs

**HEAD**: 7419100
**Tree**: clean
**Shell**: /bin/sh
**Result**: 24 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/tuning/test_tuning_types.py::test_m43_01_01_search_strategy_enum PASSED` | pass |
| C2 | `run unit / tests/unit/tuning/test_tuning_types.py::test_m43_01_02_search_spec_dataclass PASSED` | pass |
| C3 | `run unit / tests/unit/tuning/test_tuning_types.py::test_m43_01_03_trial_record_dataclass PASSED` | pass |
| C4 | `run unit / tests/unit/tuning/test_tuning_types.py::test_m43_01_04_tuning_result_dataclass PASSED` | pass |
| C5 | `run unit / tests/unit/tuning/test_tuning_types.py::test_m43_01_05_tuning_error_inheritance PASSED` | pass |
| C6 | `run unit / tests/unit/tuning/test_tuning_validation.py::test_m43_02_01_validate_search_spec_valid PASSED` | pass |
| C7 | `run unit / tests/unit/tuning/test_tuning_validation.py::test_m43_02_02_validate_search_spec_invalid_folds PASS` | pass |
| C8 | `run unit / tests/unit/tuning/test_tuning_validation.py::test_m43_02_03_validate_search_spec_metric_direction P` | pass |
| C9 | `run unit / tests/unit/tuning/test_tuning_validation.py::test_m43_02_04_validate_search_spec_random_n_iter PASS` | pass |
| C10 | `run unit / tests/unit/tuning/test_tuning_candidates.py::test_m43_03_01_grid_search_cartesian_product PASSED` | pass |
| C11 | `run unit / tests/unit/tuning/test_tuning_candidates.py::test_m43_03_02_random_search_seed_determinism PASSED` | pass |
| C12 | `run unit / tests/unit/tuning/test_tuning_candidates.py::test_m43_03_03_fixed_strategy_single_candidate PASSED` | pass |
| C13 | `run unit / tests/unit/tuning/test_tuning_partitioning.py::test_m43_04_01_split_inner_folds_disjointness PASSED` | pass |
| C14 | `run unit / tests/unit/tuning/test_tuning_partitioning.py::test_m43_04_02_split_inner_folds_training_confinemen` | pass |
| C15 | `run unit / tests/unit/tuning/test_tuning_partitioning.py::test_m43_04_03_split_inner_folds_insufficient_sample` | pass |
| C16 | `run unit / tests/unit/tuning/test_tuning_execution.py::test_m43_05_01_fresh_model_instances_per_fold PASSED` | pass |
| C17 | `run unit / tests/unit/tuning/test_tuning_execution.py::test_m43_05_02_metric_computation_and_aggregation PASSE` | pass |
| C18 | `run unit / tests/unit/tuning/test_tuning_execution.py::test_m43_05_03_direction_selection_and_tie_breaking PAS` | pass |
| C19 | `run unit / tests/unit/tuning/test_tuning_failures.py::test_m43_06_01_undefined_nan_disqualification PASSED` | pass |
| C20 | `run unit / tests/unit/tuning/test_tuning_failures.py::test_m43_06_02_all_candidates_fail_raises_error PASSED` | pass |
| C21 | `run unit / tests/unit/tuning/test_tuning_failures.py::test_m43_06_03_error_preserves_trial_details PASSED` | pass |
| C22 | `run integration / tests/integration/tuning/test_tuning_integration.py::test_m43_07_01_public_api_exports PASSE` | pass |
| C23 | `run integration / tests/integration/tuning/test_tuning_integration.py::test_m43_07_02_runtime_purity_numpy_onl` | pass |
| C24 | `run integration / tests/integration/tuning/test_tuning_integration.py::test_m43_07_03_end_to_end_tuning_lifecy` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/tuning/test_tuning_failures.py::test_m43_06_03_error_preserves_trial_details PASSED [ 42%]
tests/unit/tuning/test_tuning_partitioning.py::test_m43_04_01_split_inner_folds_disjointness PASSED [ 47%]
tests/unit/tuning/test_tuning_partitioning.py::test_m43_04_02_split_inner_folds_training_confinement PASSED [ 52%]
tests/unit/tuning/test_tuning_partitioning.py::test_m43_04_03_split_inner_folds_insufficient_samples PASSED [ 57%]
tests/unit/tuning/test_tuning_types.py::test_m43_01_01_search_strategy_enum PASSED [ 61%]
tests/unit/tuning/test_tuning_types.py::test_m43_01_02_search_spec_dataclass PASSED [ 66%]
tests/unit/tuning/test_tuning_types.py::test_m43_01_03_trial_record_dataclass PASSED [ 71%]
tests/unit/tuning/test_tuning_types.py::test_m43_01_04_tuning_result_dataclass PASSED [ 76%]
tests/unit/tuning/test_tuning_types.py::test_m43_01_05_tuning_error_inheritance PASSED [ 80%]
tests/unit/tuning/test_tuning_validation.py::test_m43_02_01_validate_search_spec_valid PASSED [ 85%]
tests/unit/tuning/test_tuning_validation.py::test_m43_02_02_validate_search_spec_invalid_folds PASSED [ 90%]
tests/unit/tuning/test_tuning_validation.py::test_m43_02_03_validate_search_spec_metric_direction PASSED [ 95%]
tests/unit/tuning/test_tuning_validation.py::test_m43_02_04_validate_search_spec_random_n_iter PASSED [100%]

============================== 21 passed in 0.11s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/tuning/test_tuning_integration.py::test_m43_07_01_public_api_exports PASSED [ 33%]
tests/integration/tuning/test_tuning_integration.py::test_m43_07_02_runtime_purity_numpy_only PASSED [ 66%]
tests/integration/tuning/test_tuning_integration.py::test_m43_07_03_end_to_end_tuning_lifecycle PASSED [100%]

============================== 3 passed in 0.17s ===============================
```
