# m4-2-two-layer-preprocessing proofs

**HEAD**: bece29c
**Tree**: clean
**Shell**: /bin/sh
**Result**: 24 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/models/test_preprocessing_types.py::test_m42_01_01_scaler_type_enum PASSED` | pass |
| C2 | `run unit / tests/unit/models/test_preprocessing_types.py::test_m42_01_02_preprocessing_step_spec PASSED` | pass |
| C3 | `run unit / tests/unit/models/test_preprocessing_types.py::test_m42_01_03_two_layer_preprocessing_spec PASSED` | pass |
| C4 | `run unit / tests/unit/models/test_preprocessing_types.py::test_m42_01_04_two_layer_preprocessing_state PASSED` | pass |
| C5 | `run unit / tests/unit/models/test_preprocessing_validation.py::test_m42_02_01_validate_two_layer_valid PASSED` | pass |
| C6 | `run unit / tests/unit/models/test_preprocessing_validation.py::test_m42_02_02_validate_two_layer_duplication_r` | pass |
| C7 | `run unit / tests/unit/models/test_preprocessing_validation.py::test_m42_02_03_validate_two_layer_invalid_step ` | pass |
| C8 | `run unit / tests/unit/models/test_preprocessing_validation.py::test_m42_02_04_validate_two_layer_empty_passthr` | pass |
| C9 | `run unit / tests/unit/models/test_preprocessing_fit.py::test_m42_03_01_fit_two_layer_preprocessing_execution P` | pass |
| C10 | `run unit / tests/unit/models/test_preprocessing_fit.py::test_m42_03_02_fit_two_layer_preprocessing_anti_leakag` | pass |
| C11 | `run unit / tests/unit/models/test_preprocessing_fit.py::test_m42_03_03_fit_two_layer_preprocessing_invalid_inp` | pass |
| C12 | `run unit / tests/unit/models/test_preprocessing_apply.py::test_m42_04_01_apply_two_layer_preprocessing_project` | pass |
| C13 | `run unit / tests/unit/models/test_preprocessing_apply.py::test_m42_04_02_apply_two_layer_preprocessing_state_i` | pass |
| C14 | `run unit / tests/unit/models/test_preprocessing_apply.py::test_m42_04_03_apply_two_layer_preprocessing_feature` | pass |
| C15 | `run unit / tests/unit/models/test_preprocessing_scalers.py::test_m42_05_01_standard_scaler_zero_variance PASSE` | pass |
| C16 | `run unit / tests/unit/models/test_preprocessing_scalers.py::test_m42_05_02_minmax_scaler_constant_columns PASS` | pass |
| C17 | `run unit / tests/unit/models/test_preprocessing_scalers.py::test_m42_05_03_maxabs_scaler_zero_columns PASSED` | pass |
| C18 | `run unit / tests/unit/models/test_preprocessing_scalers.py::test_m42_05_04_robust_scaler_zero_iqr PASSED` | pass |
| C19 | `run unit / tests/unit/models/test_preprocessing_scalers.py::test_m42_05_05_angular_scaler_quantum_gates PASSED` | pass |
| C20 | `run unit / tests/unit/models/test_preprocessing_kernel.py::test_m42_06_01_kernel_adapter_fit_partition_passing` | pass |
| C21 | `run unit / tests/unit/models/test_preprocessing_kernel.py::test_m42_06_02_kernel_adapter_transform_partition_p` | pass |
| C22 | `run unit / tests/unit/models/test_preprocessing_kernel.py::test_m42_06_03_kernel_adapter_invalid_matrix_reject` | pass |
| C23 | `run integration / tests/integration/models/test_preprocessing_integration.py::test_m42_07_01_public_api_export` | pass |
| C24 | `run integration / tests/integration/models/test_preprocessing_integration.py::test_m42_07_02_runtime_purity_nu` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/models/test_preprocessing_scalers.py::test_m42_05_01_standard_scaler_zero_variance PASSED [ 78%]
tests/unit/models/test_preprocessing_scalers.py::test_m42_05_02_minmax_scaler_constant_columns PASSED [ 80%]
tests/unit/models/test_preprocessing_scalers.py::test_m42_05_03_maxabs_scaler_zero_columns PASSED [ 82%]
tests/unit/models/test_preprocessing_scalers.py::test_m42_05_04_robust_scaler_zero_iqr PASSED [ 83%]
tests/unit/models/test_preprocessing_scalers.py::test_m42_05_05_angular_scaler_quantum_gates PASSED [ 85%]
tests/unit/models/test_preprocessing_types.py::test_m42_01_01_scaler_type_enum PASSED [ 87%]
tests/unit/models/test_preprocessing_types.py::test_m42_01_02_preprocessing_step_spec PASSED [ 89%]
tests/unit/models/test_preprocessing_types.py::test_m42_01_03_two_layer_preprocessing_spec PASSED [ 91%]
tests/unit/models/test_preprocessing_types.py::test_m42_01_04_two_layer_preprocessing_state PASSED [ 92%]
tests/unit/models/test_preprocessing_validation.py::test_m42_02_01_validate_two_layer_valid PASSED [ 94%]
tests/unit/models/test_preprocessing_validation.py::test_m42_02_02_validate_two_layer_duplication_rejection PASSED [ 96%]
tests/unit/models/test_preprocessing_validation.py::test_m42_02_03_validate_two_layer_invalid_step PASSED [ 98%]
tests/unit/models/test_preprocessing_validation.py::test_m42_02_04_validate_two_layer_empty_passthrough PASSED [100%]

============================== 56 passed in 0.13s ==============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 5 items

tests/integration/models/test_models_integration.py::test_m41_09_01_runtime_purity_numpy_only PASSED [ 20%]
tests/integration/models/test_models_integration.py::test_models_end_to_end_lifecycle_pipeline PASSED [ 40%]
tests/integration/models/test_preprocessing_integration.py::test_m42_07_01_public_api_exports PASSED [ 60%]
tests/integration/models/test_preprocessing_integration.py::test_m42_07_02_runtime_purity_numpy_only PASSED [ 80%]
tests/integration/models/test_preprocessing_integration.py::test_preprocessing_end_to_end_two_layer_pipeline PASSED [100%]

============================== 5 passed in 0.31s ===============================
```
