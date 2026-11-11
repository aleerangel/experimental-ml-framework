# m4-1-model-registry-contracts proofs

**HEAD**: 6d0aa19
**Tree**: clean
**Shell**: /bin/sh
**Result**: 35 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/models/test_model_types.py::test_m41_01_01_model_family_enum PASSED` | pass |
| C2 | `run unit / tests/unit/models/test_model_types.py::test_m41_01_02_model_capabilities_dataclass PASSED` | pass |
| C3 | `run unit / tests/unit/models/test_model_types.py::test_m41_01_03_model_diagnostics_dataclass PASSED` | pass |
| C4 | `run unit / tests/unit/models/test_model_spec.py::test_m41_02_01_model_spec_dataclass PASSED` | pass |
| C5 | `run unit / tests/unit/models/test_model_spec.py::test_m41_02_02_validate_model_spec_valid PASSED` | pass |
| C6 | `run unit / tests/unit/models/test_model_spec.py::test_m41_02_03_validate_model_spec_invalid_fields PASSED` | pass |
| C7 | `run unit / tests/unit/models/test_model_spec.py::test_m41_02_04_validate_model_spec_contradictory_capabilities` | pass |
| C8 | `run unit / tests/unit/models/test_model_instantiation.py::test_m41_03_01_instantiate_fresh_model_with_seed PAS` | pass |
| C9 | `run unit / tests/unit/models/test_model_instantiation.py::test_m41_03_02_instantiate_fresh_model_seed_none PAS` | pass |
| C10 | `run unit / tests/unit/models/test_model_instantiation.py::test_m41_03_03_instantiate_fresh_model_singleton_rej` | pass |
| C11 | `run unit / tests/unit/models/test_model_instantiation.py::test_m41_03_04_instantiate_fresh_model_factory_error` | pass |
| C12 | `run unit / tests/unit/models/test_model_instantiation.py::test_m41_03_05_instantiate_fresh_model_instance_isol` | pass |
| C13 | `run unit / tests/unit/models/test_model_fit.py::test_m41_04_01_fit_model_trainable PASSED` | pass |
| C14 | `run unit / tests/unit/models/test_model_fit.py::test_m41_04_02_fit_model_analytical_bypass PASSED` | pass |
| C15 | `run unit / tests/unit/models/test_model_fit.py::test_m41_04_03_fit_model_dimension_mismatch_and_empty PASSED` | pass |
| C16 | `run unit / tests/unit/models/test_model_predict.py::test_m41_05_01_predict_model_output_structure PASSED` | pass |
| C17 | `run unit / tests/unit/models/test_model_predict.py::test_m41_05_02_predict_model_uncertainty_valid PASSED` | pass |
| C18 | `run unit / tests/unit/models/test_model_predict.py::test_m41_05_03_predict_model_predict_proba_valid PASSED` | pass |
| C19 | `run unit / tests/unit/models/test_model_predict.py::test_m41_05_04_predict_model_uncertainty_disabled_none PAS` | pass |
| C20 | `run unit / tests/unit/models/test_model_predict.py::test_m41_05_05_predict_model_predict_proba_disabled_none P` | pass |
| C21 | `run unit / tests/unit/models/test_model_predict.py::test_m41_05_06_predict_model_unfitted_rejection PASSED` | pass |
| C22 | `run unit / tests/unit/models/test_model_predict.py::test_m41_05_07_predict_model_uncertainty_runtime_violation` | pass |
| C23 | `run unit / tests/unit/models/test_model_predict.py::test_m41_05_08_predict_model_predict_proba_runtime_violati` | pass |
| C24 | `run unit / tests/unit/models/test_model_diagnostics.py::test_m41_06_01_extract_model_diagnostics_structure PAS` | pass |
| C25 | `run unit / tests/unit/models/test_model_diagnostics.py::test_m41_06_02_extract_model_diagnostics_snapshot_inde` | pass |
| C26 | `run unit / tests/unit/models/test_model_diagnostics.py::test_m41_06_03_extract_model_diagnostics_unsupported_c` | pass |
| C27 | `run unit / tests/unit/models/test_model_diagnostics.py::test_m41_06_04_extract_model_diagnostics_model_mutatio` | pass |
| C28 | `run unit / tests/unit/models/test_model_spec.py::test_m41_07_01_validate_models_catalog_valid PASSED` | pass |
| C29 | `run unit / tests/unit/models/test_model_spec.py::test_m41_07_02_validate_models_catalog_duplicate_ids PASSED` | pass |
| C30 | `run unit / tests/unit/models/test_model_baselines.py::test_m41_08_01_dummy_baseline_regression_mean PASSED` | pass |
| C31 | `run unit / tests/unit/models/test_model_baselines.py::test_m41_08_02_dummy_baseline_regression_median PASSED` | pass |
| C32 | `run unit / tests/unit/models/test_model_baselines.py::test_m41_08_03_dummy_baseline_classification_most_freque` | pass |
| C33 | `run unit / tests/unit/models/test_model_baselines.py::test_m41_08_04_analytical_biometric_model_direct_eval PA` | pass |
| C34 | `run unit / tests/unit/models/test_model_baselines.py::test_m41_08_05_analytical_biometric_model_missing_featur` | pass |
| C35 | `run integration / tests/integration/models/test_models_integration.py::test_m41_09_01_runtime_purity_numpy_onl` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/models/test_model_predict.py::test_m41_05_05_predict_model_predict_proba_disabled_none PASSED [ 64%]
tests/unit/models/test_model_predict.py::test_m41_05_06_predict_model_unfitted_rejection PASSED [ 67%]
tests/unit/models/test_model_predict.py::test_m41_05_07_predict_model_uncertainty_runtime_violation PASSED [ 70%]
tests/unit/models/test_model_predict.py::test_m41_05_08_predict_model_predict_proba_runtime_violation PASSED [ 73%]
tests/unit/models/test_model_spec.py::test_m41_02_01_model_spec_dataclass PASSED [ 76%]
tests/unit/models/test_model_spec.py::test_m41_02_02_validate_model_spec_valid PASSED [ 79%]
tests/unit/models/test_model_spec.py::test_m41_02_03_validate_model_spec_invalid_fields PASSED [ 82%]
tests/unit/models/test_model_spec.py::test_m41_02_04_validate_model_spec_contradictory_capabilities PASSED [ 85%]
tests/unit/models/test_model_spec.py::test_m41_07_01_validate_models_catalog_valid PASSED [ 88%]
tests/unit/models/test_model_spec.py::test_m41_07_02_validate_models_catalog_duplicate_ids PASSED [ 91%]
tests/unit/models/test_model_types.py::test_m41_01_01_model_family_enum PASSED [ 94%]
tests/unit/models/test_model_types.py::test_m41_01_02_model_capabilities_dataclass PASSED [ 97%]
tests/unit/models/test_model_types.py::test_m41_01_03_model_diagnostics_dataclass PASSED [100%]

============================== 34 passed in 0.11s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 2 items

tests/integration/models/test_models_integration.py::test_m41_09_01_runtime_purity_numpy_only PASSED [ 50%]
tests/integration/models/test_models_integration.py::test_models_end_to_end_lifecycle_pipeline PASSED [100%]

============================== 2 passed in 0.18s ===============================
```
