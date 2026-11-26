# m8-mvp-stabilization-contract-alignment proofs

**HEAD**: a18cb82
**Tree**: dirty - docs/referencia/api_python.md
**Shell**: /bin/sh
**Result**: 8 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run m8_unit / test_family_a_and_g_populated_from_real_artifacts PASSED` | pass |
| C2 | `run m8_unit / test_categorical_stats_ignore_none_values PASSED` | pass |
| C3 | `run m8_unit / test_nested_tuning_dynamic_selection_isolated_per_inner_fold PASSED` | pass |
| C4 | `run m8_e2e / test_run_experiment_cli_interoperability_and_seed_propagation PASSED` | pass |
| C5 | `run m8_e2e / test_cli_stats_kuncheva_and_multiobjective_pareto PASSED` | pass |
| C6 | `run m8_unit / test_resume_rejects_modified_scenarios_or_models_hash PASSED` | pass |
| C7 | `run m8_unit / test_canonical_cell_filename_without_legacy_prefix PASSED` | pass |
| Build | `.venv/bin/pytest tests/ -q` | pass |

## Output

`Run m8_unit` - exit 0

```
tests/unit/orchestration/test_matrix_resume.py::test_m52_05_03_resume_reexecutes_missing_artifacts PASSED [ 62%]
tests/unit/orchestration/test_matrix_resume.py::test_m52_05_04_resume_executes_pending_cells PASSED [ 65%]
tests/unit/orchestration/test_matrix_resume.py::test_m52_05_05_resume_retries_failed_cells PASSED [ 68%]
tests/unit/orchestration/test_matrix_resume.py::test_ach_m5_02_resume_with_mismatched_dataset_hash_raises PASSED [ 71%]
tests/unit/orchestration/test_matrix_resume.py::test_ach_m5_02_resume_with_mismatched_partition_plan_id_raises PASSED [ 75%]
tests/unit/orchestration/test_matrix_resume.py::test_ach_m5_02_resume_with_incompatible_cell_artifact_raises_before_execution PASSED [ 78%]
tests/unit/orchestration/test_matrix_resume.py::test_ach_m5_02_legacy_state_without_identity_fields_raises PASSED [ 81%]
tests/unit/orchestration/test_matrix_resume.py::test_resume_rejects_modified_scenarios_or_models_hash PASSED [ 84%]
tests/unit/tuning/test_tuning_execution.py::test_m43_05_01_fresh_model_instances_per_fold PASSED [ 87%]
tests/unit/tuning/test_tuning_execution.py::test_m43_05_02_metric_computation_and_aggregation PASSED [ 90%]
tests/unit/tuning/test_tuning_execution.py::test_m43_05_03_direction_selection_and_tie_breaking PASSED [ 93%]
tests/unit/tuning/test_tuning_execution.py::test_aud_m4_03_run_nested_tuning_with_preprocessing_anti_leakage PASSED [ 96%]
tests/unit/tuning/test_tuning_execution.py::test_nested_tuning_dynamic_selection_isolated_per_inner_fold PASSED [100%]

============================== 32 passed in 0.92s ==============================
```

`Run m8_e2e` - exit 0

```
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 9 items

tests/unit/test_usability_cli_and_facade.py::test_cli_init_and_end_to_end_workflow PASSED [ 11%]
tests/unit/test_usability_cli_and_facade.py::test_python_facade_run_experiment_end_to_end PASSED [ 22%]
tests/unit/test_usability_cli_and_facade.py::test_run_experiment_cli_interoperability_and_seed_propagation PASSED [ 33%]
tests/unit/test_usability_cli_and_facade.py::test_cli_init_classification_has_two_models_and_compares PASSED [ 44%]
tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_run_success PASSED [ 55%]
tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_status PASSED    [ 66%]
tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_verify PASSED    [ 77%]
tests/unit/cli/test_cli_stats.py::test_m64_03_cli_lazy_imports_purity PASSED [ 88%]
tests/unit/cli/test_cli_stats.py::test_cli_stats_kuncheva_and_multiobjective_pareto PASSED [100%]

============================== 9 passed in 1.94s ===============================
```
