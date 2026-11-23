# sklearn-ensemble-diagnostics Acceptance Walkthrough

## Prerequisites
- Virtual environment `.venv` active with `pytest` and `numpy` installed (`XCUT-02`).

## Consumer Scenarios
1. **Ensemble estimator diagnostics (`DIAG-01`, `DIAG-02`):**
   - Fit an ensemble model (e.g., `RandomForestRegressor` or an estimator exposing `estimators_ = [DecisionTreeRegressor(), ...]`).
   - Call `extract_model_diagnostics(model, model_spec, phase="fit")`.
   - Expected: Returns `ModelDiagnostics` where `diag.diagnostics["estimators_"]` is an immutable `tuple` of `"DecisionTreeRegressor"` class names, without raising `ContractViolationError` and without mutating `model`.
2. **Arbitrary complex object rejection (`DIAG-03`, `AC-M41-06-03`):**
   - Pass a model with `self.bad_attribute_ = CustomComplexObject()` (non-estimator mutable object).
   - Expected: Raises `ContractViolationError` matching `"Unsupported mutable complex object"`.

## Approval Criteria
- `validate_spec.py sklearn-ensemble-diagnostics` exits 0.
- `.venv/bin/pytest tests/unit/models/test_model_diagnostics.py -v` passes all tests including `test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection` and new ensemble tests.
- Full test suite `.venv/bin/pytest tests/ -q` passes with zero regressions.
- Independent Verifier issues `PASS` and `validate_verification.py sklearn-ensemble-diagnostics` exits 0.
