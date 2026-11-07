# m2-3-partitioning-engine proofs

**HEAD**: d7f5595
**Tree**: clean
**Shell**: /bin/sh
**Result**: 10 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/validation/test_engine.py::test_part_01_kfold_cv_only PASSED` | pass |
| C2 | `run unit / tests/unit/validation/test_splitters.py::test_part_02_stratified_kfold_proportions PASSED` | pass |
| C3 | `run unit / tests/unit/validation/test_splitters.py::test_part_03_group_kfold_disjointness PASSED` | pass |
| C4 | `run unit / tests/unit/validation/test_splitters.py::test_part_04_temporal_monotonicity PASSED` | pass |
| C5 | `run unit / tests/unit/validation/test_splitters.py::test_part_05_bootstrap_oob PASSED` | pass |
| C6 | `run unit / tests/unit/validation/test_engine.py::test_part_06_holdout_separation PASSED` | pass |
| C7 | `run unit / tests/unit/validation/test_validators.py::test_part_07_validate_partition_plan_invariants PASSED` | pass |
| C8 | `run unit / tests/unit/validation/test_types.py::test_part_08_partition_plan_plan_id PASSED` | pass |
| C9 | `run integration / tests/integration/test_validation_integration.py::test_part_09_immutability_and_determinism ` | pass |
| C10 | `run unit / tests/unit/validation/test_types.py::test_part_10_config_boundary_validation PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/validation/test_engine.py::test_holdout_only_regime PASSED    [ 20%]
tests/unit/validation/test_engine.py::test_missing_column_raises_configuration_error PASSED [ 26%]
tests/unit/validation/test_splitters.py::test_kfold_split_disjointness_and_coverage PASSED [ 33%]
tests/unit/validation/test_splitters.py::test_part_02_stratified_kfold_proportions PASSED [ 40%]
tests/unit/validation/test_splitters.py::test_holdout_split_proportions_and_disjointness PASSED [ 46%]
tests/unit/validation/test_splitters.py::test_part_03_group_kfold_disjointness PASSED [ 53%]
tests/unit/validation/test_splitters.py::test_part_04_temporal_monotonicity PASSED [ 60%]
tests/unit/validation/test_splitters.py::test_part_05_bootstrap_oob PASSED [ 66%]
tests/unit/validation/test_types.py::test_t1_enums_and_coercion PASSED   [ 73%]
tests/unit/validation/test_types.py::test_part_10_config_boundary_validation PASSED [ 80%]
tests/unit/validation/test_types.py::test_part_08_partition_plan_plan_id PASSED [ 86%]
tests/unit/validation/test_validators.py::test_part_07_validate_partition_plan_invariants PASSED [ 93%]
tests/unit/validation/test_validators.py::test_validator_group_and_temporal_invariants PASSED [100%]

============================== 15 passed in 0.11s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/test_validation_integration.py::test_part_09_immutability_and_determinism PASSED [ 33%]
tests/integration/test_validation_integration.py::test_validation_end_to_end_with_sanitized_dataset_view PASSED [ 66%]
tests/integration/test_validation_integration.py::test_architectural_import_direction_validation PASSED [100%]

============================== 3 passed in 0.12s ===============================
```
