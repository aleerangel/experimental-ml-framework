# m1-2-core proofs

**HEAD**: f006e56
**Tree**: clean
**Shell**: /bin/sh
**Result**: 18 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_identifier_types_immutable PASSED` | pass |
| C2 | `run unit / test_identifier_validation_non_empty PASSED` | pass |
| C3 | `run unit / test_identifier_invalid_value_error PASSED` | pass |
| C4 | `run unit / test_task_type_and_execution_status_enums PASSED` | pass |
| C5 | `run unit / test_finding_metric_aggregation_enums PASSED` | pass |
| C6 | `run unit / test_metric_status_and_error_policy_enums PASSED` | pass |
| C7 | `run unit / test_derive_seeds_returns_tuple PASSED` | pass |
| C8 | `run unit / test_derive_seeds_determinism PASSED` | pass |
| C9 | `run unit / test_spawn_child_seeds_validation PASSED` | pass |
| C10 | `run unit / test_config_hash_sha256_format PASSED` | pass |
| C11 | `run unit / test_config_hash_unicode_and_key_order PASSED` | pass |
| C12 | `run unit / test_config_hash_strict_types PASSED` | pass |
| C13 | `run unit / test_config_hash_special_floats PASSED` | pass |
| C14 | `run unit / test_dataset_hash_file_and_schema PASSED` | pass |
| C15 | `run unit / test_dataset_hash_in_memory PASSED` | pass |
| C16 | `run unit / test_dataset_hash_file_not_found PASSED` | pass |
| C17 | `run unit / test_make_finding_and_make_warning PASSED` | pass |
| C18 | `run unit / test_core_exceptions_and_finding_immutability PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/test_core.py::test_metric_status_and_error_policy_enums PASSED [ 33%]
tests/unit/test_core.py::test_derive_seeds_returns_tuple PASSED          [ 38%]
tests/unit/test_core.py::test_derive_seeds_determinism PASSED            [ 44%]
tests/unit/test_core.py::test_spawn_child_seeds_validation PASSED        [ 50%]
tests/unit/test_core.py::test_config_hash_sha256_format PASSED           [ 55%]
tests/unit/test_core.py::test_config_hash_unicode_and_key_order PASSED   [ 61%]
tests/unit/test_core.py::test_config_hash_strict_types PASSED            [ 66%]
tests/unit/test_core.py::test_config_hash_special_floats PASSED          [ 72%]
tests/unit/test_core.py::test_dataset_hash_file_and_schema PASSED        [ 77%]
tests/unit/test_core.py::test_dataset_hash_in_memory PASSED              [ 83%]
tests/unit/test_core.py::test_dataset_hash_file_not_found PASSED         [ 88%]
tests/unit/test_core.py::test_make_finding_and_make_warning PASSED       [ 94%]
tests/unit/test_core.py::test_core_exceptions_and_finding_immutability PASSED [100%]

============================== 18 passed in 0.21s ==============================
```
