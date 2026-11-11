# m4-4-model-persistence-cli proofs

**HEAD**: 7dd8556
**Tree**: clean
**Shell**: /bin/sh
**Result**: 21 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/models/test_models_codecs.py::test_m44_01_01_models_catalog_dataclass PASSED` | pass |
| C2 | `run unit / tests/unit/models/test_models_codecs.py::test_m44_01_02_models_catalog_to_dict PASSED` | pass |
| C3 | `run unit / tests/unit/models/test_models_codecs.py::test_m44_01_03_models_catalog_from_dict PASSED` | pass |
| C4 | `run unit / tests/unit/models/test_models_resolution.py::test_m44_02_01_resolve_builtin_baselines PASSED` | pass |
| C5 | `run unit / tests/unit/models/test_models_resolution.py::test_m44_02_02_resolve_dotted_import_path PASSED` | pass |
| C6 | `run unit / tests/unit/models/test_models_resolution.py::test_m44_02_03_resolve_invalid_reference_raises PASSED` | pass |
| C7 | `run unit / tests/unit/models/test_models_storage.py::test_m44_03_01_save_and_load_roundtrip PASSED` | pass |
| C8 | `run unit / tests/unit/models/test_models_storage.py::test_m44_03_02_save_overwrite_guard PASSED` | pass |
| C9 | `run unit / tests/unit/models/test_models_storage.py::test_m44_03_03_load_missing_or_corrupt PASSED` | pass |
| C10 | `run unit / tests/unit/stages/test_models_stage_gate.py::test_m44_04_01_verify_models_gate_valid PASSED` | pass |
| C11 | `run unit / tests/unit/stages/test_models_stage_gate.py::test_m44_04_02_verify_models_gate_missing_or_empty PAS` | pass |
| C12 | `run unit / tests/unit/stages/test_models_stage_gate.py::test_m44_04_03_verify_models_gate_unmet_precondition P` | pass |
| C13 | `run unit / tests/unit/cli/test_cli_models_validate.py::test_m44_05_01_models_validate_success PASSED` | pass |
| C14 | `run unit / tests/unit/cli/test_cli_models_validate.py::test_m44_05_02_models_validate_overwrite_error PASSED` | pass |
| C15 | `run unit / tests/unit/cli/test_cli_models_validate.py::test_m44_05_03_models_validate_invalid_input PASSED` | pass |
| C16 | `run unit / tests/unit/cli/test_cli_models_verify.py::test_m44_06_01_models_verify_success PASSED` | pass |
| C17 | `run unit / tests/unit/cli/test_cli_models_verify.py::test_m44_06_02_models_verify_gate_failure PASSED` | pass |
| C18 | `run unit / tests/unit/cli/test_cli_models_verify.py::test_m44_06_03_models_verify_missing_dir PASSED` | pass |
| C19 | `run integration / tests/integration/models/test_models_cli_integration.py::test_m44_07_01_cli_parser_registrat` | pass |
| C20 | `run integration / tests/integration/models/test_models_cli_integration.py::test_m44_07_02_cli_import_purity PA` | pass |
| C21 | `run integration / tests/integration/models/test_models_cli_integration.py::test_m44_07_03_e2e_cli_subprocess P` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/cli/test_cmd_data.py::test_cli_08_data_profile_force_flag_behavior PASSED [ 87%]
tests/unit/cli/test_cmd_features.py::test_feat_01_features_help PASSED   [ 88%]
tests/unit/cli/test_cmd_features.py::test_feat_02_features_explore_success PASSED [ 89%]
tests/unit/cli/test_cmd_features.py::test_feat_03_features_explore_overwrite_protection PASSED [ 90%]
tests/unit/cli/test_cmd_features.py::test_feat_04_features_scenarios_success PASSED [ 91%]
tests/unit/cli/test_cmd_features.py::test_feat_05_features_scenarios_rejection PASSED [ 92%]
tests/unit/cli/test_cmd_features.py::test_feat_06_features_verify_gate PASSED [ 93%]
tests/unit/cli/test_cmd_features.py::test_feat_07_cli_purity PASSED      [ 94%]
tests/unit/cli/test_cmd_partition.py::test_cli_04_partition_build_success PASSED [ 95%]
tests/unit/cli/test_cmd_partition.py::test_cli_04_partition_build_seed_override PASSED [ 96%]
tests/unit/cli/test_cmd_partition.py::test_cli_05_partition_verify_clean_and_tampered PASSED [ 97%]
tests/unit/cli/test_cmd_partition.py::test_cli_07_upstream_gate_missing_blocked PASSED [ 98%]
tests/unit/cli/test_cmd_partition.py::test_cli_08_partition_build_force_flag_behavior PASSED [100%]

============================== 96 passed in 0.41s ==============================
```

`Run integration` - exit 0

```
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 8 items

tests/integration/models/test_models_cli_integration.py::test_m44_07_01_cli_parser_registration PASSED [ 12%]
tests/integration/models/test_models_cli_integration.py::test_m44_07_02_cli_import_purity PASSED [ 25%]
tests/integration/models/test_models_cli_integration.py::test_m44_07_03_e2e_cli_subprocess PASSED [ 37%]
tests/integration/models/test_models_integration.py::test_m41_09_01_runtime_purity_numpy_only PASSED [ 50%]
tests/integration/models/test_models_integration.py::test_models_end_to_end_lifecycle_pipeline PASSED [ 62%]
tests/integration/models/test_preprocessing_integration.py::test_m42_07_01_public_api_exports PASSED [ 75%]
tests/integration/models/test_preprocessing_integration.py::test_m42_07_02_runtime_purity_numpy_only PASSED [ 87%]
tests/integration/models/test_preprocessing_integration.py::test_preprocessing_end_to_end_two_layer_pipeline PASSED [100%]

============================== 8 passed in 0.99s ===============================
```
