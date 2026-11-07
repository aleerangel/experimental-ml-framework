# m2-4-artifacts-stage-gates proofs

**HEAD**: 01cc165
**Tree**: clean
**Shell**: /bin/sh
**Result**: 7 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/core/test_storage.py::test_store_01_atomic_write_and_failure_cleanup PASSED` | pass |
| C2 | `run unit / tests/unit/data/test_codecs.py::test_store_02_lossless_codecs_roundtrip PASSED` | pass |
| C3 | `run integration / tests/integration/test_artifacts_stage_gates_integration.py::test_store_03_experiment_direct` | pass |
| C4 | `run unit / tests/unit/validation/test_splits_storage.py::test_store_04_splits_csv_gz_deterministic PASSED` | pass |
| C5 | `run unit / tests/unit/stages/test_stage_gates.py::test_store_05_hash_divergence_and_incomplete_plan_rejection ` | pass |
| C6 | `run unit / tests/unit/stages/test_stage_gates.py::test_store_06_splits_tampering_and_mismatch_rejection PASSED` | pass |
| C7 | `run unit / tests/unit/core/test_storage.py::test_store_07_overwrite_protection_configuration_error PASSED` | pass |

## Output

`Run unit` - exit 0

```
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 9 items

tests/unit/core/test_storage.py::test_store_01_atomic_write_and_failure_cleanup PASSED [ 11%]
tests/unit/core/test_storage.py::test_store_07_overwrite_protection_configuration_error PASSED [ 22%]
tests/unit/core/test_storage.py::test_storage_converts_numpy_scalars_and_enums PASSED [ 33%]
tests/unit/data/test_codecs.py::test_store_02_lossless_codecs_roundtrip PASSED [ 44%]
tests/unit/validation/test_splits_storage.py::test_store_04_splits_csv_gz_deterministic PASSED [ 55%]
tests/unit/validation/test_splits_storage.py::test_partition_plan_codec_roundtrip PASSED [ 66%]
tests/unit/validation/test_splits_storage.py::test_splits_schema_writer PASSED [ 77%]
tests/unit/stages/test_stage_gates.py::test_store_05_hash_divergence_and_incomplete_plan_rejection PASSED [ 88%]
tests/unit/stages/test_stage_gates.py::test_store_06_splits_tampering_and_mismatch_rejection PASSED [100%]

============================== 9 passed in 0.14s ===============================
```

`Run integration` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 2 items

tests/integration/test_artifacts_stage_gates_integration.py::test_store_03_experiment_directory_layout PASSED [ 50%]
tests/integration/test_artifacts_stage_gates_integration.py::test_architectural_import_direction_artifacts_stage_gates PASSED [100%]

============================== 2 passed in 0.14s ===============================
```
