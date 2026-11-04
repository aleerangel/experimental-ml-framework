# m1-4-datasets-schemas proofs

**HEAD**: 18e1c88
**Tree**: clean
**Shell**: /bin/sh
**Result**: 29 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_domain_structures_and_enum_immutable PASSED` | pass |
| C2 | `run unit / test_schema_spec_nfc_normalization_and_encapsulation PASSED` | pass |
| C3 | `run unit / test_schema_spec_rejects_empty_and_control_chars PASSED` | pass |
| C4 | `run unit / test_schema_spec_blocks_wave2_features PASSED` | pass |
| C5 | `run unit / test_schema_spec_enforces_disjoint_roles PASSED` | pass |
| C6 | `run unit / test_schema_spec_config_hash_invariance PASSED` | pass |
| C7 | `run unit / test_load_dataset_sources_and_bundle_ownership PASSED` | pass |
| C8 | `run unit / test_load_dataset_defensive_copies_isolation PASSED` | pass |
| C9 | `run unit / test_bundle_numeric_columns_buffer_immutability PASSED` | pass |
| C10 | `run unit / test_bundle_object_columns_scalar_immutability PASSED` | pass |
| C11 | `run unit / test_load_dataset_preserves_missing_values PASSED` | pass |
| C12 | `run unit / test_bundle_structural_metadata_completeness PASSED` | pass |
| C13 | `run unit / test_dataset_hash_canonical_in_memory_digest PASSED` | pass |
| C14 | `run unit / test_raw_source_hash_file_and_memory PASSED` | pass |
| C15 | `run unit / test_tabular_parsing_supported_delimiters_and_quotes PASSED` | pass |
| C16 | `run unit / test_delimiter_sniffer_automatic_detection PASSED` | pass |
| C17 | `run unit / test_delimiter_sniffer_ambiguity_raises_error PASSED` | pass |
| C18 | `run unit / test_explicit_delimiter_overrides_detection PASSED` | pass |
| C19 | `run unit / test_ragged_rows_raise_data_integrity_error PASSED` | pass |
| C20 | `run unit / test_empty_or_zero_rows_file_raises_error PASSED` | pass |
| C21 | `run unit / test_parsing_has_header_false_and_column_names PASSED` | pass |
| C22 | `run unit / test_header_validation_empty_or_duplicate_names PASSED` | pass |
| C23 | `run unit / test_column_descriptor_fields_and_roles PASSED` | pass |
| C24 | `run unit / test_semantic_types_declared_vs_default_fallbacks PASSED` | pass |
| C25 | `run unit / test_observation_ids_positional_generation PASSED` | pass |
| C26 | `run unit / test_observation_ids_source_column_validation PASSED` | pass |
| C27 | `run unit / test_dataset_schema_validation_structural_errors PASSED` | pass |
| C28 | `run unit / test_get_column_array_view_and_copy PASSED` | pass |
| C29 | `run unit / test_slice_bundle_by_observation_ids_ordering_and_hash PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/test_data_schemas.py::test_observation_ids_positional_generation PASSED [ 58%]
tests/unit/test_data_schemas.py::test_observation_ids_source_column_validation PASSED [ 62%]
tests/unit/test_data_schemas.py::test_dataset_schema_validation_structural_errors PASSED [ 65%]
tests/unit/test_data_schemas.py::test_load_dataset_sources_and_bundle_ownership PASSED [ 68%]
tests/unit/test_data_schemas.py::test_load_dataset_defensive_copies_isolation PASSED [ 72%]
tests/unit/test_data_schemas.py::test_bundle_numeric_columns_buffer_immutability PASSED [ 75%]
tests/unit/test_data_schemas.py::test_bundle_object_columns_scalar_immutability PASSED [ 79%]
tests/unit/test_data_schemas.py::test_load_dataset_preserves_missing_values PASSED [ 82%]
tests/unit/test_data_schemas.py::test_bundle_structural_metadata_completeness PASSED [ 86%]
tests/unit/test_data_schemas.py::test_dataset_hash_canonical_in_memory_digest PASSED [ 89%]
tests/unit/test_data_schemas.py::test_raw_source_hash_file_and_memory PASSED [ 93%]
tests/unit/test_data_schemas.py::test_get_column_array_view_and_copy PASSED [ 96%]
tests/unit/test_data_schemas.py::test_slice_bundle_by_observation_ids_ordering_and_hash PASSED [100%]

============================== 29 passed in 0.10s ==============================
```
