# m1-2-core verification

**Verdict**: PASS
**Proofs**: `proofs.md` at 479ee8d
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/test_core.py` `test_identifier_types_immutable` | yes |
| C2 | `tests/unit/test_core.py` `test_identifier_validation_non_empty` | yes |
| C3 | `tests/unit/test_core.py` `test_identifier_invalid_value_error` | yes |
| C4 | `tests/unit/test_core.py` `test_task_type_and_execution_status_enums` | yes |
| C5 | `tests/unit/test_core.py` `test_finding_metric_aggregation_enums` | yes |
| C6 | `tests/unit/test_core.py` `test_metric_status_and_error_policy_enums` | yes |
| C7 | `tests/unit/test_core.py` `test_derive_seeds_returns_tuple` | yes |
| C8 | `tests/unit/test_core.py` `test_derive_seeds_determinism` | yes |
| C9 | `tests/unit/test_core.py` `test_spawn_child_seeds_validation` | yes |
| C10 | `tests/unit/test_core.py` `test_config_hash_sha256_format` | yes |
| C11 | `tests/unit/test_core.py` `test_config_hash_unicode_and_key_order` | yes |
| C12 | `tests/unit/test_core.py` `test_config_hash_strict_types` | yes |
| C13 | `tests/unit/test_core.py` `test_config_hash_special_floats` | yes |
| C14 | `tests/unit/test_core.py` `test_dataset_hash_file_and_schema` | yes |
| C15 | `tests/unit/test_core.py` `test_dataset_hash_in_memory` | yes |
| C16 | `tests/unit/test_core.py` `test_dataset_hash_file_not_found` | yes |
| C17 | `tests/unit/test_core.py` `test_make_finding_and_make_warning` | yes |
| C18 | `tests/unit/test_core.py` `test_core_exceptions_and_finding_immutability` | yes |

## Findings

None - probed deeply nested canonical hash invariance, 10k seed derivation determinism, and dataset_hash record variations.
