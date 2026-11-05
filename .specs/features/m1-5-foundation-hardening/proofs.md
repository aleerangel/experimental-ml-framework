# m1-5-foundation-hardening proofs

**HEAD**: e90797f
**Tree**: clean
**Shell**: /bin/sh
**Result**: 15 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/test_core.py::test_hard_01_dataset_hash_column_boundary_framing_and_determinism PASSED` | pass |
| C2 | `run unit / tests/unit/test_core.py::test_hard_02_dataset_hash_object_scalar_type_tags_and_missing PASSED` | pass |
| C3 | `run unit / tests/unit/test_core.py::test_hard_03_dataset_hash_observation_ids_and_architecture_direction PASSE` | pass |
| C4 | `run unit / tests/unit/test_data_schemas.py::test_hard_04_bundle_dataset_hash_delegates_observation_ids PASSED` | pass |
| C5 | `run unit / tests/unit/test_core.py::test_hard_05_is_nan_and_missing_scalar_centralized PASSED` | pass |
| C6 | `run unit / tests/unit/test_data_schemas.py::test_hard_06_numpy_floating_nan_counted_across_data_layer PASSED` | pass |
| C7 | `run unit / tests/unit/test_data_schemas.py::test_hard_07_slice_bundle_preserves_observation_id_instances PASSE` | pass |
| C8 | `run unit / tests/unit/test_data_schemas.py::test_hard_08_slice_bundle_rejects_invalid_observation_id_inputs PA` | pass |
| C9 | `run unit / tests/unit/test_data_schemas.py::test_hard_09_object_column_missingness_and_semantic_preservation P` | pass |
| C10 | `run unit / tests/unit/test_data_schemas.py::test_hard_10_object_column_rejects_non_whitelisted_types PASSED` | pass |
| C11 | `run unit / tests/unit/test_data_schemas.py::test_hard_11_int64_overflow_raises_data_integrity_error PASSED` | pass |
| C12 | `run unit / tests/integration/test_m1_foundation_integration.py::test_hard_12_readme_python_blocks_execute_clea` | pass |
| C13 | `run unit / tests/integration/test_m1_foundation_integration.py::test_hard_13_documentation_and_symbol_counts_a` | pass |
| C14 | `run unit / tests/integration/test_m1_foundation_integration.py::test_hard_14_end_to_end_core_data_metrics_and_` | pass |
| C15 | `run unit / tests/integration/test_m1_foundation_integration.py::test_hard_15_audit_findings_governance_and_int` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/test_metrics.py::test_r2_and_pearson_zero_variance PASSED     [ 87%]
tests/unit/test_metrics.py::test_rmse_rel_pct_and_mape_degenerate PASSED [ 88%]
tests/unit/test_metrics.py::test_kta_centered_and_uncentered PASSED      [ 89%]
tests/unit/test_metrics.py::test_discrete_classification_accuracy PASSED [ 90%]
tests/unit/test_metrics.py::test_precision_division_by_zero_rules PASSED [ 91%]
tests/unit/test_metrics.py::test_recall_and_balanced_accuracy_rules PASSED [ 92%]
tests/unit/test_metrics.py::test_f1_own_denominator_rules PASSED         [ 93%]
tests/unit/test_metrics.py::test_roc_auc_ties_and_ovr PASSED             [ 94%]
tests/unit/test_metrics.py::test_log_loss_validation_and_clipping PASSED [ 95%]
tests/unit/test_metrics.py::test_metrics_catalog_registration PASSED     [ 96%]
tests/unit/test_metrics.py::test_catalog_query_and_dispatch PASSED       [ 97%]
tests/unit/test_metrics.py::test_is_better_adr005_rules PASSED           [ 98%]
tests/unit/test_metrics.py::test_aggregate_and_rank_configurations PASSED [100%]

============================== 96 passed in 0.70s ==============================
```
