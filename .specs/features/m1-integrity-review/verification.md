# m1-integrity-review verification

**Verdict**: PASS
**Proofs**: `proofs.md` at d7e1e79
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c01_aud_01_baseline_recorded` | yes |
| C2 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c02_aud_02_non_interference_diff_empty` | yes |
| C3 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c03_aud_03_findings_have_reproducible_evidence` | yes |
| C4 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c04_aud_04_unverifiable_criteria_marked` | yes |
| C5 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c05_arch_01_import_graph_recorded` | yes |
| C6 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c06_arch_02_dependency_levels_checked` | yes |
| C7 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c07_arch_03_zero_import_cycles` | yes |
| C8 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c08_arch_04_adr008_class_taxonomy` | yes |
| C9 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c09_arch_05_duplicate_responsibilities_listed` | yes |
| C10 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c10_arch_06_unreferenced_public_symbols_checked` | yes |
| C11 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c11_arch_07_doc_vs_public_api_compared` | yes |
| C12 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c12_int_01_e2e_flow_executed` | yes |
| C13 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c13_int_02_identifier_and_enum_identity` | yes |
| C14 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c14_int_03_exception_hierarchy_verified` | yes |
| C15 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c15_int_04_cross_format_dataset_hash_compared` | yes |
| C16 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c16_int_05_cross_process_hashseed_determinism` | yes |
| C17 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c17_int_06_readonly_arrays_across_all_metrics` | yes |
| C18 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c18_int_07_bundle_vs_core_dataset_hash_relation` | yes |
| C19 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c19_int_08_int64_and_bool_dtype_behavior_recorded` | yes |
| C20 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c20_qual_01_ast_code_quality_scan` | yes |
| C21 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c21_qual_02_public_type_annotations_checked` | yes |
| C22 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c22_qual_03_edge_cases_probed` | yes |
| C23 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c23_qual_04_scaling_benchmark_recorded` | yes |
| C24 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c24_qual_05_adversarial_immutability_verified` | yes |
| C25 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c25_qual_06_interpreter_compatibility_recorded` | yes |
| C26 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c26_test_01_line_coverage_measured` | yes |
| C27 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c27_test_02_twelve_mutations_executed` | yes |
| C28 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c28_test_03_surviving_mutations_analyzed` | yes |
| C29 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c29_test_04_cross_module_integration_tests_counted` | yes |
| C30 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c30_test_05_test_isolation_and_ordering_verified` | yes |
| C31 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c31_test_06_tlc_validators_executed` | yes |
| C32 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c32_test_07_criterion_check_proof_mapping_verified` | yes |
| C33 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c33_test_08_tlc_validator_reliability_checked` | yes |
| C34 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c34_doc_01_readme_python_blocks_executed` | yes |
| C35 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c35_doc_02_readme_directory_tree_compared` | yes |
| C36 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c36_doc_03_counts_statuses_commits_verified` | yes |
| C37 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c37_doc_04_documented_symbols_importable_checked` | yes |
| C38 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c38_doc_05_hash_contract_contradictions_checked` | yes |
| C39 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c39_doc_06_traceability_matrix_complete` | yes |
| C40 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c40_doc_07_governance_artifacts_verified` | yes |
| C41 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c41_ready_01_m2_consumed_interfaces_evaluated` | yes |
| C42 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c42_ready_02_open_m2_decisions_listed` | yes |
| C43 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c43_ready_03_findings_register_schema_complete` | yes |
| C44 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c44_ready_04_documented_limitations_cited` | yes |
| C45 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c45_ready_05_remediation_plan_prioritized` | yes |
| C46 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c46_ready_06_verdict_matches_decision_rule` | yes |
| C47 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c47_ready_07_independent_verification_recorded` | yes |
| C48 | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` `test_c48_ready_08_unreproduced_findings_policy` | yes |

## Findings

None - independent audit verification confirmed 100% of all 48 acceptance criteria (`C1`..`C48`), verified `proofs.md` at `d7e1e79` (`48 pass, 0 fail`), confirmed that the non-interference diff against baseline `6acf6f8` across `src/`, `tests/`, `pyproject.toml`, `README.md`, `engenharia_software/`, `.agent/`, and `.specs/features/m1-{1,2,3,4}-*/` is empty, and independently re-executed the reproduction evidence for 100% of the `ALTO` findings (`6/6`) and 40% (`4/10`, exceeding the $\ge 20\%$ requirement of `READY-07`) of the remaining findings with `0` `NÃO REPRODUZIDO` results (`READY-08`):

- **`AUD-F-001` (`DEFEITO` / `ALTO`) — `CONFIRMADO`**: Re-executing `.venv/bin/python .specs/features/m1-integrity-review/probes/docs_and_traceability_probe.py` confirmed that `README.md` Block 3 (`L262-L289`) fails with `ConfigurationError: Unsupported candidate type <class 'NoneType'>` and Block 4 (`L292-L323`) fails with `TypeError: DatasetSchemaSpec.__init__() got an unexpected keyword argument 'semantic_types'`.
- **`AUD-F-004` (`DEFEITO` / `ALTO`) — `CONFIRMADO`**: Re-executing `dataset_hash({'ab': [1.0], 'c': [2.0]}) == dataset_hash({'a': [1.0], 'bc': [2.0]})` returned `True`, confirming the column-name concatenation collision in `_hash_in_memory_tabular`.
- **`AUD-F-005` (`RISCO` / `ALTO`) — `CONFIRMADO`**: Re-executing `slice_bundle_by_observation_ids(b, [ObservationId('obs_000001')])` vs a fresh bundle with identical values confirmed `observation_ids` differ (`('obs_000001',)` vs `('obs_000000',)`) while `bundle.dataset_hash` is identical (`True`).
- **`AUD-F-006` (`DEFEITO` / `ALTO`) — `CONFIRMADO`**: Re-executing `slice_bundle_by_observation_ids(b, ['obs_000001'])` confirmed `sub.observation_ids[0]` has type `str` and `isinstance(sub.observation_ids[0], ObservationId)` is `False`.
- **`AUD-F-008` (`DEFEITO` / `ALTO`) — `CONFIRMADO`**: Re-executing `load_dataset` on a 2D `np.float32` array containing `np.float32(np.nan)` confirmed `b.descriptors['col_0'].n_missing == 0` while `int(np.isnan(b.columns['col_0']).sum()) == 1`.
- **`AUD-F-009` (`RISCO` / `ALTO`) — `CONFIRMADO`**: Re-executing `load_dataset` with `types.SimpleNamespace(v='a')` in an `object` column and mutating `ns.v = 'mutated'` confirmed `b.columns['cat'][0].v == 'mutated'`.
- **`AUD-F-002` (`DEFEITO` / `MODERADO`, sampled) — `CONFIRMADO`**: Confirmed `src/experimental_ml/core/exceptions.py` and `identifiers.py` do not exist on disk while `len(experimental_ml.data.__all__) == 13` (vs 7 stated in `ETAPA_ATUAL_ENGENHARIA.md:87`).
- **`AUD-F-003` (`RISCO` / `MODERADO`, sampled) — `CONFIRMADO`**: Confirmed `ObservationId('obs_\x00_1')` accepts ASCII NUL, carries a mutable `__dict__`, and `ObservationId('obs_e\u0301') != ObservationId('obs_\u00e9')`.
- **`AUD-F-007` (`DEFEITO` / `MODERADO`, sampled) — `CONFIRMADO`**: Confirmed `load_dataset({'x': [2**63], 'y': [1.0]}, s)` raises raw `OverflowError` instead of `DataIntegrityError`.
- **`AUD-F-012` (`RISCO` / `MODERADO`, sampled) — `CONFIRMADO`**: Confirmed `.specs/features/m1-1-setup-cli-smoke/verification.md` is absent on disk.
