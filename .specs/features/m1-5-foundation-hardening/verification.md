# m1-5-foundation-hardening verification

**Verdict**: PASS
**Proofs**: `proofs.md` at 9d7d646
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/test_core.py` `test_hard_01_dataset_hash_column_boundary_framing_and_determinism` | yes |
| C2 | `tests/unit/test_core.py` `test_hard_02_dataset_hash_object_scalar_type_tags_and_missing` | yes |
| C3 | `tests/unit/test_core.py` `test_hard_03_dataset_hash_observation_ids_and_architecture_direction` | yes |
| C4 | `tests/unit/test_data_schemas.py` `test_hard_04_bundle_dataset_hash_delegates_observation_ids` | yes |
| C5 | `tests/unit/test_core.py` `test_hard_05_is_nan_and_missing_scalar_centralized` | yes |
| C6 | `tests/unit/test_data_schemas.py` `test_hard_06_numpy_floating_nan_counted_across_data_layer` | yes |
| C7 | `tests/unit/test_data_schemas.py` `test_hard_07_slice_bundle_preserves_observation_id_instances` | yes |
| C8 | `tests/unit/test_data_schemas.py` `test_hard_08_slice_bundle_rejects_invalid_observation_id_inputs` | yes |
| C9 | `tests/unit/test_data_schemas.py` `test_hard_09_object_column_missingness_and_semantic_preservation` | yes |
| C10 | `tests/unit/test_data_schemas.py` `test_hard_10_object_column_rejects_non_whitelisted_types` | yes |
| C11 | `tests/unit/test_data_schemas.py` `test_hard_11_int64_overflow_raises_data_integrity_error` | yes |
| C12 | `tests/integration/test_m1_foundation_integration.py` `test_hard_12_readme_python_blocks_execute_cleanly` | yes |
| C13 | `tests/integration/test_m1_foundation_integration.py` `test_hard_13_documentation_and_symbol_counts_aligned` | yes |
| C14 | `tests/integration/test_m1_foundation_integration.py` `test_hard_14_end_to_end_core_data_metrics_and_cross_process_hash` | yes |
| C15 | `tests/integration/test_m1_foundation_integration.py` `test_hard_15_audit_findings_governance_and_integrity_preservation` | yes |

## Findings

None - 0 findings identified during independent audit. All 15 criteria hold at commit 9d7d646. Full test suite (96 passed) confirms that the 6 P0 findings (AUD-F-001, AUD-F-004, AUD-F-005, AUD-F-006, AUD-F-008, AUD-F-009) and 4 selected P1 findings (AUD-F-002, AUD-F-007, AUD-F-010, AUD-F-013) are genuinely resolved in code with 0 regressions. The audit artifacts in `.specs/features/m1-integrity-review/` remain 100% untouched (0 bytes git diff), and `.specs/features/m1-1-setup-cli-smoke/verification.md` was correctly preserved as absent rather than retroactively fabricated.

| ID | Title | Severity | Status | Closed |
| --- | --- | --- | --- | --- |
