# m2-2-preparation-plan-sanitization proofs

**HEAD**: e39bb1e
**Tree**: clean
**Shell**: /bin/sh
**Result**: 10 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/data/test_preparation.py::test_prep_01_ready_plan_canonical_order PASSED` | pass |
| C2 | `run unit / tests/unit/data/test_preparation.py::test_prep_02_incomplete_plan_unresolved_findings PASSED` | pass |
| C3 | `run unit / tests/unit/data/test_preparation.py::test_prep_03_invalid_rule_admissibility_and_configuration_erro` | pass |
| C4 | `run unit / tests/unit/data/test_preparation.py::test_prep_04_sanitize_dataset_structural_rules PASSED` | pass |
| C5 | `run unit / tests/unit/data/test_preparation.py::test_prep_05_binding_validation_and_status_check PASSED` | pass |
| C6 | `run unit / tests/unit/data/test_preparation.py::test_prep_06_sanitized_view_contract_and_dataset_hash PASSED` | pass |
| C7 | `run unit / tests/unit/data/test_preparation.py::test_prep_07_bit_identical_deferred_and_accepted_columns PASSE` | pass |
| C8 | `run unit / tests/unit/data/test_preparation.py::test_prep_08_binary_target_mapping_and_encoding PASSED` | pass |
| C9 | `run unit / tests/unit/data/test_preparation.py::test_prep_09_empty_dataset_or_features_raises_integrity_error ` | pass |
| C10 | `run integration / tests/integration/test_preparation_integration.py::test_prep_10_immutability_and_determinism` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/data/test_preparation.py::test_t1_sanitized_dataset_view_immutability_and_slots PASSED [ 25%]
tests/unit/data/test_preparation.py::test_t2_admissibility_valid_rules PASSED [ 31%]
tests/unit/data/test_preparation.py::test_prep_03_invalid_rule_admissibility_and_configuration_error PASSED [ 37%]
tests/unit/data/test_preparation.py::test_prep_01_ready_plan_canonical_order PASSED [ 43%]
tests/unit/data/test_preparation.py::test_prep_02_incomplete_plan_unresolved_findings PASSED [ 50%]
tests/unit/data/test_preparation.py::test_t3_duplicate_rule_and_dict_coercion PASSED [ 56%]
tests/unit/data/test_preparation.py::test_prep_05_binding_validation_and_status_check PASSED [ 62%]
tests/unit/data/test_preparation.py::test_prep_08_binary_target_mapping_and_encoding PASSED [ 68%]
tests/unit/data/test_preparation.py::test_prep_09_empty_dataset_or_features_raises_integrity_error PASSED [ 75%]
tests/unit/data/test_preparation.py::test_t4_drop_rows_and_order_preservation PASSED [ 81%]
tests/unit/data/test_preparation.py::test_prep_04_sanitize_dataset_structural_rules PASSED [ 87%]
tests/unit/data/test_preparation.py::test_prep_06_sanitized_view_contract_and_dataset_hash PASSED [ 93%]
tests/unit/data/test_preparation.py::test_prep_07_bit_identical_deferred_and_accepted_columns PASSED [100%]

============================== 16 passed in 0.11s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/test_preparation_integration.py::test_prep_10_immutability_and_determinism PASSED [ 33%]
tests/integration/test_preparation_integration.py::test_end_to_end_preparation_pipeline PASSED [ 66%]
tests/integration/test_preparation_integration.py::test_architectural_import_direction_data_preparation PASSED [100%]

============================== 3 passed in 0.09s ===============================
```
