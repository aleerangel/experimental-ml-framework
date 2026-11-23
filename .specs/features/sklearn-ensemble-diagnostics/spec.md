# sklearn-ensemble-diagnostics Spec

**Status**: Completed  
**Approved**: 2026-11-23 - user: "aprovado"  
**Build**: .venv/bin/python -c "import experimental_ml.models.diagnostics"  
**Run diag_unit**: .venv/bin/pytest tests/unit/models/test_model_diagnostics.py -v  

## Problem Statement

Scikit-learn ensemble estimators (such as `RandomForestRegressor`) populate fitted attributes like `estimators_` containing lists of sub-estimator instances (`DecisionTreeRegressor`). Currently, `extract_model_diagnostics` in `src/experimental_ml/models/diagnostics.py` passes every fitted `*_` attribute through `_to_immutable_primitive`, which raises `ContractViolationError` on sub-estimators and aborts `expml run start` during `MODEL_FIT`. We must safely summarize sub-estimators into immutable metadata while preserving `AC-M41-06-03` rejection for arbitrary unsupported mutable objects.

## User Stories

- As a researcher running `expml run start` with scikit-learn ensemble models (e.g. `RandomForestRegressor`), I want `extract_model_diagnostics` to summarize sub-estimators into safe immutable metadata so training completes without `ContractViolationError`.
- As a framework maintainer, I want `extract_model_diagnostics` to keep rejecting arbitrary unsupported mutable objects (`AC-M41-06-03`) so contract violations are still caught.

## Scope

- `src/experimental_ml/models/diagnostics.py`: Detect sub-estimator instances (objects exposing callable `fit` and `predict`/`transform` methods, or belonging to `sklearn.*` modules) inside `_to_immutable_primitive` / `extract_model_diagnostics` and convert them to immutable string descriptors (`type(val).__name__`), preserving deep immutability and model invariance.
- `tests/unit/models/test_model_diagnostics.py`: Add unit tests simulating ensemble sub-estimators (`estimators_`, `estimator_`, nested structures) and verify `AC-M41-06-03` remains enforced for `CustomComplexObject`.

## Requirements

- **DIAG-01 (Sub-estimator safe summarization):** WHEN `extract_model_diagnostics` converts fitted model attributes (or `get_diagnostics()` mappings) containing sub-estimator objects (objects with callable `fit` and `predict`/`transform`, or from `sklearn.*`), THE SYSTEM SHALL convert each sub-estimator into an immutable string summary (`type(val).__name__`) instead of raising `ContractViolationError`.
- **DIAG-02 (Deep immutability and model invariance):** WHEN sub-estimator attributes are summarized inside lists, tuples, or mappings, THE SYSTEM SHALL preserve deep snapshot immutability (`tuple` / `MappingProxyType`) and SHALL NOT mutate the fitted model or its sub-estimators (`AC-M41-06-02`, `AC-M41-06-04`).
- **DIAG-03 (Preservation of `AC-M41-06-03`):** IF a fitted attribute or `get_diagnostics()` value contains an unsupported mutable complex object that is NOT a primitive, collection, NumPy scalar/array, or sub-estimator (e.g., `CustomComplexObject`, socket, function, generator), THEN THE SYSTEM SHALL still raise `ContractViolationError`.

## Assumptions & Open Questions

### Assumptions
- Scikit-learn is an optional external dependency (`XCUT-02`); unit tests simulate scikit-learn-style ensemble estimators without requiring `scikit-learn` in `.venv`.
- Summarizing a sub-estimator as `type(val).__name__` (e.g. `"DecisionTreeRegressor"`) provides sufficient diagnostic visibility (identifying ensemble composition and count via `len(diag.diagnostics["estimators_"])`) while remaining deeply immutable.

### Open Questions
- None (resolved with user: preserve `AC-M41-06-03` for arbitrary objects and replace sub-estimators with safe immutable metadata).

## Out of Scope

- Adding `scikit-learn` to runtime dependencies (`XCUT-02`).
- Extracting deep recursive hyperparameters of every individual tree inside an ensemble.

## Completion Criteria

- `extract_model_diagnostics` succeeds on ensemble models with `estimators_` / `estimator_` sub-estimators.
- `test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection` continues to pass unchanged.
- All unit and integration tests pass via `.venv/bin/pytest tests/ -q`.

## Requirement Traceability

| Requirement ID | Acceptance Criterion | Test / Verification |
| --- | --- | --- |
| DIAG-01 | Sub-estimators summarized as immutable class name strings | `test_diag_ensemble_subestimators_summarized_immutably` |
| DIAG-02 | Deep immutability & model invariance preserved with sub-estimators | `test_diag_ensemble_subestimators_summarized_immutably` |
| DIAG-03 | Arbitrary mutable complex objects still raise `ContractViolationError` | `test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection` |

## Checks

**C1** - `extract_model_diagnostics` summarizes sub-estimators in `estimators_` and `estimator_` into immutable string descriptors (`DIAG-01`, `DIAG-02`).
  Proof: run diag_unit | test_diag_ensemble_subestimators_summarized_immutably PASSED

**C2** - `extract_model_diagnostics` still raises `ContractViolationError` for arbitrary unsupported mutable objects (`DIAG-03`, `AC-M41-06-03`).
  Proof: run diag_unit | test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection PASSED
