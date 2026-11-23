# sklearn-ensemble-diagnostics Independent Verification

**Verdict:** `PASS`

## Requirements Verification

- **DIAG-01 (Sub-estimator safe summarization):** Verified in `src/experimental_ml/models/diagnostics.py` (`_is_subestimator`, `_to_immutable_primitive`) and `tests/unit/models/test_model_diagnostics.py::test_diag_ensemble_subestimators_summarized_immutably`. Objects with callable `fit` + `predict`/`transform` or `sklearn`/`sklearn.*` `__module__` are converted to `type(val).__name__` (including inside `list`, `np.ndarray`, and `get_diagnostics()` mappings).
- **DIAG-02 (Deep immutability and model invariance):** Verified in `test_diag_ensemble_subestimators_summarized_immutably`, `test_m41_06_02_extract_model_diagnostics_snapshot_independence`, and `test_m41_06_04_extract_model_diagnostics_model_mutation_invariance`. Collections are converted to `tuple` and `MappingProxyType`, and post-extraction mutations to the model do not affect the snapshot.
- **DIAG-03 / AC-M41-06-03 (Unsupported mutable complex object rejection):** Verified in `test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection` and edge-case check (e.g., `lambda` function) — `ContractViolationError` is raised.
- **XCUT-02 (No sklearn runtime dependency):** Verified in `pyproject.toml` (`dependencies = ["numpy>=1.24.0"]`).

## Checks

| Check | Criterion | Test | Holds |
| --- | --- | --- | --- |
| C1 | `extract_model_diagnostics` summarizes sub-estimators in `estimators_` and `estimator_` into immutable string descriptors (`DIAG-01`, `DIAG-02`). | `tests/unit/models/test_model_diagnostics.py::test_diag_ensemble_subestimators_summarized_immutably` | PASS |
| C2 | `extract_model_diagnostics` still raises `ContractViolationError` for arbitrary unsupported mutable objects (`DIAG-03`, `AC-M41-06-03`). | `tests/unit/models/test_model_diagnostics.py::test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection` | PASS |

## Observed Test Outputs

### `.venv/bin/pytest tests/unit/models/test_model_diagnostics.py -v` (exit code 0)

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... 
collected 5 items                                                              

tests/unit/models/test_model_diagnostics.py::test_m41_06_01_extract_model_diagnostics_structure PASSED [ 20%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_02_extract_model_diagnostics_snapshot_independence PASSED [ 40%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection PASSED [ 60%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_04_extract_model_diagnostics_model_mutation_invariance PASSED [ 80%]
tests/unit/models/test_model_diagnostics.py::test_diag_ensemble_subestimators_summarized_immutably PASSED [100%]

============================== 5 passed in 0.11s ===============================
```

### `.venv/bin/pytest tests/ -q` (exit code 0)

```
........................................................................ [ 11%]
........................................................................ [ 23%]
........................................................................ [ 35%]
........................................................................ [ 47%]
........................................................................ [ 58%]
........................................................................ [ 70%]
........................................................................ [ 82%]
........................................................................ [ 94%]
...................................                                      [100%]
611 passed in 20.78s
```
