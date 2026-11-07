# m2-2-preparation-plan-sanitization verification

**Verdict**: PASS
**Proofs**: `proofs.md` at e39bb1e
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/data/test_preparation.py` `test_prep_01_ready_plan_canonical_order` | yes |
| C2 | `tests/unit/data/test_preparation.py` `test_prep_02_incomplete_plan_unresolved_findings` | yes |
| C3 | `tests/unit/data/test_preparation.py` `test_prep_03_invalid_rule_admissibility_and_configuration_error` | yes |
| C4 | `tests/unit/data/test_preparation.py` `test_prep_04_sanitize_dataset_structural_rules` | yes |
| C5 | `tests/unit/data/test_preparation.py` `test_prep_05_binding_validation_and_status_check` | yes |
| C6 | `tests/unit/data/test_preparation.py` `test_prep_06_sanitized_view_contract_and_dataset_hash` | yes |
| C7 | `tests/unit/data/test_preparation.py` `test_prep_07_bit_identical_deferred_and_accepted_columns` | yes |
| C8 | `tests/unit/data/test_preparation.py` `test_prep_08_binary_target_mapping_and_encoding` | yes |
| C9 | `tests/unit/data/test_preparation.py` `test_prep_09_empty_dataset_or_features_raises_integrity_error` | yes |
| C10 | `tests/integration/test_preparation_integration.py` `test_prep_10_immutability_and_determinism` | yes |

## Own examples

Three boundary / edge case behaviors were tested independently against the codebase at `HEAD`:

1. **Simultaneous `DROP_ROWS` across `group_col` and `target` with custom `ObservationId` values**:
   - Dataset configured with custom non-sequential string observation IDs (`"id_alpha"` to `"id_epsilon"`).
   - Rules applied `DROP_ROWS` to both `group_col` (`E1_GROUP_MISSING`) and `target` (`E1_TARGET_MISSING`), plus `MAP_BINARY_TARGET`.
   - Verified that `SanitizedDatasetView.observation_ids` and `dropped_observation_ids` accurately preserved exact custom `ObservationId` values in original relative order (`id_alpha`, `id_delta`, `id_epsilon` kept; `id_beta`, `id_gamma` dropped).

2. **Class collapse guard post row-filtering**:
   - Dataset configured where all instances of the positive class coincided with missing values in a feature column targeted by `DROP_ROWS`.
   - Verified that `sanitize_dataset` detects that positive class is no longer present in sliced target classes and raises `DataIntegrityError` (`MAP_BINARY_TARGET positive_label 'pos' not in sliced target classes`), preventing downstream pipeline execution on collapsed single-class targets.

3. **Preservation of non-feature columns (`time_col`, `ignore_cols`)**:
   - Dataset configured with `time_col` and `ignore_cols`.
   - Verified that `candidate_feature_cols` strictly excludes target, group, observation ID, time, and ignore columns, while `columns` buffer and schema properly preserve `time_col` and `ignore_cols`.

## Findings

None - all checks genuinely prove their acceptance criteria, error conditions raise appropriate typed exceptions, and immutability invariants are strictly enforced across models and dataset views.
