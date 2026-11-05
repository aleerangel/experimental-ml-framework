# m1-integrity-review proofs

**HEAD**: d7e1e79
**Tree**: clean
**Shell**: /bin/sh
**Result**: 48 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run audit / test_c01_aud_01_baseline_recorded PASSED` | pass |
| C2 | `run audit / test_c02_aud_02_non_interference_diff_empty PASSED` | pass |
| C3 | `run audit / test_c03_aud_03_findings_have_reproducible_evidence PASSED` | pass |
| C4 | `run audit / test_c04_aud_04_unverifiable_criteria_marked PASSED` | pass |
| C5 | `run audit / test_c05_arch_01_import_graph_recorded PASSED` | pass |
| C6 | `run audit / test_c06_arch_02_dependency_levels_checked PASSED` | pass |
| C7 | `run audit / test_c07_arch_03_zero_import_cycles PASSED` | pass |
| C8 | `run audit / test_c08_arch_04_adr008_class_taxonomy PASSED` | pass |
| C9 | `run audit / test_c09_arch_05_duplicate_responsibilities_listed PASSED` | pass |
| C10 | `run audit / test_c10_arch_06_unreferenced_public_symbols_checked PASSED` | pass |
| C11 | `run audit / test_c11_arch_07_doc_vs_public_api_compared PASSED` | pass |
| C12 | `run audit / test_c12_int_01_e2e_flow_executed PASSED` | pass |
| C13 | `run audit / test_c13_int_02_identifier_and_enum_identity PASSED` | pass |
| C14 | `run audit / test_c14_int_03_exception_hierarchy_verified PASSED` | pass |
| C15 | `run audit / test_c15_int_04_cross_format_dataset_hash_compared PASSED` | pass |
| C16 | `run audit / test_c16_int_05_cross_process_hashseed_determinism PASSED` | pass |
| C17 | `run audit / test_c17_int_06_readonly_arrays_across_all_metrics PASSED` | pass |
| C18 | `run audit / test_c18_int_07_bundle_vs_core_dataset_hash_relation PASSED` | pass |
| C19 | `run audit / test_c19_int_08_int64_and_bool_dtype_behavior_recorded PASSED` | pass |
| C20 | `run audit / test_c20_qual_01_ast_code_quality_scan PASSED` | pass |
| C21 | `run audit / test_c21_qual_02_public_type_annotations_checked PASSED` | pass |
| C22 | `run audit / test_c22_qual_03_edge_cases_probed PASSED` | pass |
| C23 | `run audit / test_c23_qual_04_scaling_benchmark_recorded PASSED` | pass |
| C24 | `run audit / test_c24_qual_05_adversarial_immutability_verified PASSED` | pass |
| C25 | `run audit / test_c25_qual_06_interpreter_compatibility_recorded PASSED` | pass |
| C26 | `run audit / test_c26_test_01_line_coverage_measured PASSED` | pass |
| C27 | `run audit / test_c27_test_02_twelve_mutations_executed PASSED` | pass |
| C28 | `run audit / test_c28_test_03_surviving_mutations_analyzed PASSED` | pass |
| C29 | `run audit / test_c29_test_04_cross_module_integration_tests_counted PASSED` | pass |
| C30 | `run audit / test_c30_test_05_test_isolation_and_ordering_verified PASSED` | pass |
| C31 | `run audit / test_c31_test_06_tlc_validators_executed PASSED` | pass |
| C32 | `run audit / test_c32_test_07_criterion_check_proof_mapping_verified PASSED` | pass |
| C33 | `run audit / test_c33_test_08_tlc_validator_reliability_checked PASSED` | pass |
| C34 | `run audit / test_c34_doc_01_readme_python_blocks_executed PASSED` | pass |
| C35 | `run audit / test_c35_doc_02_readme_directory_tree_compared PASSED` | pass |
| C36 | `run audit / test_c36_doc_03_counts_statuses_commits_verified PASSED` | pass |
| C37 | `run audit / test_c37_doc_04_documented_symbols_importable_checked PASSED` | pass |
| C38 | `run audit / test_c38_doc_05_hash_contract_contradictions_checked PASSED` | pass |
| C39 | `run audit / test_c39_doc_06_traceability_matrix_complete PASSED` | pass |
| C40 | `run audit / test_c40_doc_07_governance_artifacts_verified PASSED` | pass |
| C41 | `run audit / test_c41_ready_01_m2_consumed_interfaces_evaluated PASSED` | pass |
| C42 | `run audit / test_c42_ready_02_open_m2_decisions_listed PASSED` | pass |
| C43 | `run audit / test_c43_ready_03_findings_register_schema_complete PASSED` | pass |
| C44 | `run audit / test_c44_ready_04_documented_limitations_cited PASSED` | pass |
| C45 | `run audit / test_c45_ready_05_remediation_plan_prioritized PASSED` | pass |
| C46 | `run audit / test_c46_ready_06_verdict_matches_decision_rule PASSED` | pass |
| C47 | `run audit / test_c47_ready_07_independent_verification_recorded PASSED` | pass |
| C48 | `run audit / test_c48_ready_08_unreproduced_findings_policy PASSED` | pass |

## Output

`Run audit` - exit 0

```
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c36_doc_03_counts_statuses_commits_verified PASSED [ 75%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c37_doc_04_documented_symbols_importable_checked PASSED [ 77%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c38_doc_05_hash_contract_contradictions_checked PASSED [ 79%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c39_doc_06_traceability_matrix_complete PASSED [ 81%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c40_doc_07_governance_artifacts_verified PASSED [ 83%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c41_ready_01_m2_consumed_interfaces_evaluated PASSED [ 85%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c42_ready_02_open_m2_decisions_listed PASSED [ 87%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c43_ready_03_findings_register_schema_complete PASSED [ 89%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c44_ready_04_documented_limitations_cited PASSED [ 91%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c45_ready_05_remediation_plan_prioritized PASSED [ 93%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c46_ready_06_verdict_matches_decision_rule PASSED [ 95%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c47_ready_07_independent_verification_recorded PASSED [ 97%]
.specs/features/m1-integrity-review/probes/test_audit_checks.py::test_c48_ready_08_unreproduced_findings_policy PASSED [100%]

============================== 48 passed in 0.12s ==============================
```
