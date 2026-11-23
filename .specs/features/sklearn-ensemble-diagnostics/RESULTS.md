# sklearn-ensemble-diagnostics Results

**Status**: Implemented

## Summary of Changes
- **`src/experimental_ml/models/diagnostics.py`**: Added `_is_subestimator(val)` and updated `_to_immutable_primitive(val)` to convert sub-estimator instances (objects with callable `fit` and `predict`/`transform`, or from `sklearn.*`, including inside lists/tuples/dicts/`np.ndarray`) to immutable class name strings (`type(val).__name__`), while preserving `ContractViolationError` (`AC-M41-06-03`) for arbitrary unsupported mutable complex objects.
- **`tests/unit/models/test_model_diagnostics.py`**: Added `test_diag_ensemble_subestimators_summarized_immutably` covering `estimator_`, `estimators_` list, 2D object `np.ndarray`, snapshot immutability, and `AC-M41-06-03` preservation.
- **`.specs/STATE.md`**: Recorded `AD-027` and updated Handoff.

## Verification Gates Executed
- `.venv/bin/pytest tests/unit/models/test_model_diagnostics.py -v`: `5 passed in 0.17s`
