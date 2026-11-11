# m4-1-model-registry-contracts Tasks (M4.1 Registro de Modelos, Capacidades e Contratos Funcionais)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m4-1-model-registry-contracts/design.md`  
**Status**: Approved  
**Approved**: 2026-11-11 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/models/ -v  
**Run integration**: .venv/bin/pytest tests/integration/models/ -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001` a `AD-005`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 9 requirements (`MOD-01` to `MOD-09`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Model Types & Enums (`src/experimental_ml/models/types.py`) | unit | 1:1 AC mapping: ModelFamily enum, ModelCapabilities frozen dataclass, ModelDiagnostics frozen dataclass | `tests/unit/models/test_model_types.py` | `.venv/bin/pytest tests/unit/models/test_model_types.py -v` |
| Declarative ModelSpec & Catalog (`src/experimental_ml/models/spec.py`) | unit | 1:1 AC mapping: ModelSpec frozen dataclass, validate_model_spec pure validation, validate_models_catalog uniqueness | `tests/unit/models/test_model_spec.py` | `.venv/bin/pytest tests/unit/models/test_model_spec.py -v` |
| Fresh Instantiation & Isolation (`src/experimental_ml/models/execution.py`) | unit | 1:1 AC mapping: instantiate_fresh_model seed handling, singleton rejection, unshared memory isolation | `tests/unit/models/test_model_instantiation.py` | `.venv/bin/pytest tests/unit/models/test_model_instantiation.py -v` |
| Functional Model Fitting (`src/experimental_ml/models/execution.py`) | unit | 1:1 AC mapping: fit_model trainable models, analytical bypass no-op, dimension mismatch rejection | `tests/unit/models/test_model_fit.py` | `.venv/bin/pytest tests/unit/models/test_model_fit.py -v` |
| Functional Prediction & Outputs (`src/experimental_ml/models/execution.py`) | unit | 1:1 AC mapping: predict_model tripartite dict, y_std bounds, y_proba simplex, runtime capability violations | `tests/unit/models/test_model_predict.py` | `.venv/bin/pytest tests/unit/models/test_model_predict.py -v` |
| Internal Diagnostics Snapshot (`src/experimental_ml/models/diagnostics.py`) | unit | 1:1 AC mapping: extract_model_diagnostics deep immutability, snapshot independence, complex mutables rejection | `tests/unit/models/test_model_diagnostics.py` | `.venv/bin/pytest tests/unit/models/test_model_diagnostics.py -v` |
| Canonical Baseline & Analytical Models (`src/experimental_ml/models/baselines.py`) | unit | 1:1 AC mapping: DummyBaselineModel mean/median/most_frequent, AnalyticalBiometricModel formula and feature checks | `tests/unit/models/test_model_baselines.py` | `.venv/bin/pytest tests/unit/models/test_model_baselines.py -v` |
| Models Integration & Runtime Purity (`tests/integration/models/test_models_integration.py`) | integration | Full lifecycle pipeline execution, single runtime dependency (numpy>=1.24.0, zero external ML imports) | `tests/integration/models/test_models_integration.py` | `.venv/bin/pytest tests/integration/models/test_models_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After tasks with unit tests in models | `.venv/bin/pytest tests/unit/models/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Declarative Specifications and Model Types (`P1`)

Define domain enumerations (`ModelFamily`), immutable capabilities (`ModelCapabilities`), diagnostics structure (`ModelDiagnostics`), declarative specification (`ModelSpec`), and pure in-memory validation functions (`validate_model_spec`, `validate_models_catalog`).

```
T1 --> T2
```

### Phase 2: Lifecycle Execution and Inference Contracts (`P2`)

Implement pure functional lifecycle procedures (`instantiate_fresh_model`, `fit_model`, `predict_model`), enforcing instance isolation, analytical no-op bypass, and tripartite output array verification.

```
T3 --> T4 --> T5
```

### Phase 3: Diagnostics Snapshots and Reference Implementations (`P3`)

Implement immutable diagnostics snapshot extraction (`extract_model_diagnostics`) and reference baseline/analytical model implementations (`DummyBaselineModel`, `AnalyticalBiometricModel`).

```
T6 --> T7
```

### Phase 4: Public Exports and Transversal Integration Suite (`P4`)

Expose the public module API in `src/experimental_ml/models/__init__.py`, execute end-to-end integration tests connecting lifecycle execution, and verify runtime purity without third-party ML frameworks (`XCUT-02`).

```
T8
```

---

## Task Breakdown

### Phase 1: Declarative Specifications and Model Types (`P1`)

#### T1: Define ModelFamily enum, ModelCapabilities and ModelDiagnostics dataclasses

**What**: Create `src/experimental_ml/models/types.py` defining `ModelFamily` as a closed `str, Enum` with members `CLASSICAL_ML`, `NEURAL_NETWORK`, `QUANTUM_CIRCUIT`, `QUANTUM_KERNEL`, `QUANTUM_SOLVER`, `ANALYTICAL_EQUATION`, `BIOMETRIC_MODEL`, `BASELINE`, and `CUSTOM`. Define `ModelCapabilities` as an immutable frozen dataclass with slots containing all operational capability flags and default values. Define `ModelDiagnostics` as an immutable frozen dataclass with slots containing `model_id`, `phase`, `diagnostics`, and `extracted_at`. Re-export `ModelId` from `core.types`. Add co-located unit tests in `tests/unit/models/test_model_types.py`.
**Where**: `src/experimental_ml/models/types.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/types.py`
**Requirement**: MOD-01

**Done when**:
- [x] `ModelFamily` defines all 9 canonical family members
- [x] `ModelCapabilities` defined with `frozen=True`, `slots=True`, and appropriate defaults
- [x] `ModelDiagnostics` defined with `frozen=True`, `slots=True`, and immutable mappings
- [x] Unit tests pass in `tests/unit/models/test_model_types.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_model_types.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(models): definir enums, capacidades e estruturas de tipos imutaveis (MOD-01)`

---

#### T2: Implement ModelSpec dataclass and declarative validation functions

**What**: Create `src/experimental_ml/models/spec.py` defining `ModelSpec` as an immutable frozen dataclass with slots containing `model_id`, `display_name`, `family`, `estimator_factory`, `capabilities`, `description`, `scientific_justification`, `parameters`, and `random_seed_policy`. Implement `validate_model_spec(spec)` to perform pure static validation (model_id regex `^[a-zA-Z0-9_-]+$`, non-empty strings, callable factory, `supports_predict=True`, and rejection of contradictory flags) without executing training or dummy inference. Implement `validate_models_catalog(specs)` to validate sequences of specifications and detect duplicate `model_id` values, returning `MappingProxyType[str, ModelSpec]`. Add co-located unit tests in `tests/unit/models/test_model_spec.py`.
**Where**: `src/experimental_ml/models/spec.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/models/types.py`, `src/experimental_ml/core/findings.py`
**Requirement**: MOD-02, MOD-07

**Done when**:
- [x] `ModelSpec` defined with immutability guarantees and parameters wrapped in `MappingProxyType`
- [x] `validate_model_spec` validates fields and contradictory capabilities without executing code
- [x] `validate_models_catalog` validates sequences, rejects duplicates, and returns immutable mapping
- [x] Unit tests pass in `tests/unit/models/test_model_spec.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_model_spec.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(models): implementar ModelSpec e validacao declarativa de catalogos (MOD-02, MOD-07)`

---

### Phase 2: Lifecycle Execution and Inference Contracts (`P2`)

#### T3: Implement fresh model instantiation and instance isolation audit

**What**: Create `src/experimental_ml/models/execution.py` implementing `instantiate_fresh_model(model_spec, seed=None)`. The function invokes `model_spec.estimator_factory(seed)`, intercepts factory failures raising `ConfigurationError`, and tracks active instance identities using an unshared memory registry/WeakSet to raise `ContractViolationError` if a singleton or reused instance is returned (`AC-M41-03-03`, `CA-E3-01`). Add co-located unit tests in `tests/unit/models/test_model_instantiation.py`.
**Where**: `src/experimental_ml/models/execution.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/models/types.py`, `src/experimental_ml/models/spec.py`, `src/experimental_ml/core/findings.py`
**Requirement**: MOD-03

**Done when**:
- [x] `instantiate_fresh_model` passes seed to `estimator_factory(seed)` and handles `seed=None`
- [x] Reused instances or singletons are detected and rejected with `ContractViolationError`
- [x] Factory exceptions are wrapped and raised as `ConfigurationError`
- [x] Mutating or training one instance leaves other instances untouched
- [x] Unit tests pass in `tests/unit/models/test_model_instantiation.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_model_instantiation.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(models): implementar instanciacao limpa e auditoria de isolamento (MOD-03)`

---

#### T4: Implement functional model fitting with analytical bypass

**What**: In `src/experimental_ml/models/execution.py`, implement `fit_model(model, model_spec, X_train, y_train, sample_weight=None)`. Verify that `X_train` is 2D and `y_train` is 1D with matching non-zero lengths ($N_X = N_y > 0$), raising `ContractViolationError` on mismatch or emptiness. If `model_spec.capabilities.requires_fit is True`, invoke `model.fit` with training data and sample weights (if supported). If `model_spec.capabilities.requires_fit is False`, bypass training as a transparent no-op (`RF3.2`). Extract and return `(fitted_model, fit_diagnostics)`. Add co-located unit tests in `tests/unit/models/test_model_fit.py`.
**Where**: `src/experimental_ml/models/execution.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/models/types.py`, `src/experimental_ml/models/spec.py`, `src/experimental_ml/core/findings.py`
**Requirement**: MOD-04

**Done when**:
- [x] `fit_model` executes training exclusively on training arrays when `requires_fit=True`
- [x] `fit_model` transparently bypasses training as a no-op when `requires_fit=False`
- [x] Dimension mismatches ($N_X \neq N_y$) and empty arrays ($N=0$) raise `ContractViolationError`
- [x] Unit tests pass in `tests/unit/models/test_model_fit.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_model_fit.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(models): implementar ajuste funcional de modelos com bypass analitico (MOD-04)`

---

#### T5: Implement functional model prediction and tripartite output validation

**What**: In `src/experimental_ml/models/execution.py`, implement `predict_model(model, model_spec, X_eval)`. Verify that `X_eval` is a 2D array and that trainable models (`requires_fit=True`) are properly fitted, raising `ContractViolationError` if invoked on an unfitted estimator. Produce a dictionary with keys `"y_pred"`, `"y_std"`, and `"y_proba"`. Verify that `y_pred` is a 1D `np.ndarray` of length $N$. If `supports_uncertainty=True`, verify that `y_std` is a 1D `np.ndarray` of length $N$ with finite non-negative values ($\ge 0.0$); if `False`, enforce `y_std is None`. If `supports_predict_proba=True`, verify that `y_proba` is a 2D `np.ndarray` with shape `(N, n_classes)`, finite values in $[0.0, 1.0]$, and row sums equaling $1.0$; if `False`, enforce `y_proba is None` (even if `supports_decision_function=True`). Raise `ContractViolationError` on any runtime capability breach. Add co-located unit tests in `tests/unit/models/test_model_predict.py`.
**Where**: `src/experimental_ml/models/execution.py`
**Depends on**: T4
**Reuses**: `src/experimental_ml/models/types.py`, `src/experimental_ml/models/spec.py`, `src/experimental_ml/core/findings.py`
**Requirement**: MOD-05

**Done when**:
- [x] `predict_model` returns dict with keys `"y_pred"`, `"y_std"`, `"y_proba"`
- [x] `y_pred` validated as 1D array with length matching evaluation samples
- [x] `y_std` validated for finitude, non-negativity, or enforced as `None` when disabled
- [x] `y_proba` validated for shape, $[0, 1]$ bounds, unit row sum, or enforced as `None` when disabled
- [x] Unfitted trainable models and runtime capability violations raise `ContractViolationError`
- [x] Unit tests pass in `tests/unit/models/test_model_predict.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_model_predict.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(models): implementar predicao funcional com validacao tripartite de saidas (MOD-05)`

---

### Phase 3: Diagnostics Snapshots and Reference Implementations (`P3`)

#### T6: Implement extract_model_diagnostics with deep snapshot immutability

**What**: Create `src/experimental_ml/models/diagnostics.py` implementing `extract_model_diagnostics(model, model_spec, phase="fit")`. Extract internal diagnostics (from `get_diagnostics()` or fitted attributes ending in `_`), performing a deep defensive copy and recursive conversion into native scalars, tuples, and `MappingProxyType`. Enforce snapshot independence so mutating the model after extraction does not alter diagnostics. If unsupported mutable complex objects cannot be converted to immutable primitives, raise `ContractViolationError`. Ensure extraction never mutates the model. Add co-located unit tests in `tests/unit/models/test_model_diagnostics.py`.
**Where**: `src/experimental_ml/models/diagnostics.py`
**Depends on**: T5
**Reuses**: `src/experimental_ml/models/types.py`, `src/experimental_ml/models/spec.py`, `src/experimental_ml/core/findings.py`
**Requirement**: MOD-06

**Done when**:
- [x] `extract_model_diagnostics` produces an immutable `ModelDiagnostics` record
- [x] Diagnostics operate as an independent snapshot decoupled from subsequent model mutations
- [x] Unsupported mutable complex objects raise `ContractViolationError`
- [x] Model attributes and predictions remain untouched by diagnostic extraction
- [x] Unit tests pass in `tests/unit/models/test_model_diagnostics.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_model_diagnostics.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(models): implementar extracao de diagnosticos com snapshot imutavel (MOD-06)`

---

#### T7: Implement DummyBaselineModel and AnalyticalBiometricModel reference baselines

**What**: Create `src/experimental_ml/models/baselines.py` implementing `DummyBaselineModel` and `AnalyticalBiometricModel` in pure NumPy. `DummyBaselineModel` supports regression strategies `"mean"` (target mean as `y_pred`, sample standard deviation as `y_std`) and `"median"` (target median as `y_pred`, sample MAD as `y_std`), and classification strategy `"most_frequent"` (majority class as `y_pred`, deterministic lexicographical tie-breaking, empirical class frequencies as `y_proba`). `AnalyticalBiometricModel` operates with `requires_fit=False`, no-ops on `fit`, validates presence of required features in `X_eval` (raising `ContractViolationError` if absent), and evaluates formula directly. Add co-located unit tests in `tests/unit/models/test_model_baselines.py`.
**Where**: `src/experimental_ml/models/baselines.py`
**Depends on**: T6
**Reuses**: `src/experimental_ml/models/types.py`, `src/experimental_ml/core/findings.py`
**Requirement**: MOD-08

**Done when**:
- [x] `DummyBaselineModel` implements `"mean"` regression with mean prediction and std uncertainty
- [x] `DummyBaselineModel` implements `"median"` regression with median prediction and MAD uncertainty
- [x] `DummyBaselineModel` implements `"most_frequent"` classification with lexicographical tie-break and class probabilities
- [x] `AnalyticalBiometricModel` evaluates formula directly without fitting
- [x] `AnalyticalBiometricModel` raises `ContractViolationError` when required features are missing
- [x] Unit tests pass in `tests/unit/models/test_model_baselines.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_model_baselines.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(models): implementar baselines canonicos e modelo analitico de referencia (MOD-08)`

---

### Phase 4: Public Exports and Transversal Integration Suite (`P4`)

#### T8: Expose public module API and implement transversal integration tests

**What**: Create `src/experimental_ml/models/__init__.py` exporting all public symbols via `__all__`. Implement transversal integration tests in `tests/integration/models/test_models_integration.py` exercising the full lifecycle: declarative registration, catalog validation, fresh instantiation with seed isolation, training with analytical bypass, tripartite prediction verification, and diagnostics extraction. Enforce runtime purity (`XCUT-02`) by verifying via subprocess inspection that importing `experimental_ml.models` loads only `numpy` and standard library modules, with zero mandatory imports of third-party ML frameworks (scikit-learn, PyTorch, SciPy).
**Where**: `src/experimental_ml/models/__init__.py`
**Depends on**: T7
**Reuses**: `src/experimental_ml/models/types.py`, `src/experimental_ml/models/spec.py`, `src/experimental_ml/models/execution.py`, `src/experimental_ml/models/diagnostics.py`, `src/experimental_ml/models/baselines.py`
**Requirement**: MOD-09

**Done when**:
- [ ] `src/experimental_ml/models/__init__.py` cleanly exports public API in `__all__`
- [ ] End-to-end integration tests execute full lifecycle pipeline with reference models
- [ ] Subprocess inspection asserts runtime purity without external ML framework imports
- [ ] Integration tests pass in `tests/integration/models/test_models_integration.py`
- [ ] Full gate check passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(models): expor API publica e implementar suite de integracao transversal (MOD-09)`

---

## Checks

**Run unit**: .venv/bin/pytest tests/unit/models/ -v  
**Run integration**: .venv/bin/pytest tests/integration/models/ -v  

**C1** - `ModelFamily` is defined as a closed `str, Enum` with all 9 canonical members (`MOD-01`, AC 1)  
Proof: run unit | tests/unit/models/test_model_types.py::test_m41_01_01_model_family_enum PASSED

**C2** - `ModelCapabilities` is defined as an immutable frozen dataclass with slots containing all operational capability flags (`MOD-01`, AC 2)  
Proof: run unit | tests/unit/models/test_model_types.py::test_m41_01_02_model_capabilities_dataclass PASSED

**C3** - `ModelDiagnostics` is defined as an immutable frozen dataclass with slots containing model_id, phase, diagnostics, and timestamp (`MOD-01`, AC 3)  
Proof: run unit | tests/unit/models/test_model_types.py::test_m41_01_03_model_diagnostics_dataclass PASSED

**C4** - `ModelSpec` is defined as an immutable frozen dataclass with slots containing all declarative metadata and factory fields (`MOD-02`, AC 1)  
Proof: run unit | tests/unit/models/test_model_spec.py::test_m41_02_01_model_spec_dataclass PASSED

**C5** - `validate_model_spec` validates a valid specification without mutating fields or executing dummy inference (`MOD-02`, AC 2)  
Proof: run unit | tests/unit/models/test_model_spec.py::test_m41_02_02_validate_model_spec_valid PASSED

**C6** - `validate_model_spec` raises `ConfigurationError` when model_id is invalid or mandatory string/factory fields are missing (`MOD-02`, AC 3)  
Proof: run unit | tests/unit/models/test_model_spec.py::test_m41_02_03_validate_model_spec_invalid_fields PASSED

**C7** - `validate_model_spec` raises `ConfigurationError` when capabilities contain contradictory flags (`MOD-02`, AC 4)  
Proof: run unit | tests/unit/models/test_model_spec.py::test_m41_02_04_validate_model_spec_contradictory_capabilities PASSED

**C8** - `instantiate_fresh_model` passes integer seed to `estimator_factory(seed)` and returns an uncoupled instance (`MOD-03`, AC 1)  
Proof: run unit | tests/unit/models/test_model_instantiation.py::test_m41_03_01_instantiate_fresh_model_with_seed PASSED

**C9** - `instantiate_fresh_model` handles `seed=None` by passing `None` to factory (`MOD-03`, AC 2)  
Proof: run unit | tests/unit/models/test_model_instantiation.py::test_m41_03_02_instantiate_fresh_model_seed_none PASSED

**C10** - `instantiate_fresh_model` raises `ContractViolationError` when `estimator_factory` returns a singleton or active memory instance (`MOD-03`, AC 3)  
Proof: run unit | tests/unit/models/test_model_instantiation.py::test_m41_03_03_instantiate_fresh_model_singleton_rejection PASSED

**C11** - `instantiate_fresh_model` raises `ConfigurationError` when factory rejects seed parameter or raises an exception (`MOD-03`, AC 4)  
Proof: run unit | tests/unit/models/test_model_instantiation.py::test_m41_03_04_instantiate_fresh_model_factory_error_handling PASSED

**C12** - Multiple invocations of `instantiate_fresh_model` ensure state and parameter isolation across instances (`MOD-03`, AC 5)  
Proof: run unit | tests/unit/models/test_model_instantiation.py::test_m41_03_05_instantiate_fresh_model_instance_isolation PASSED

**C13** - `fit_model` fits trainable models exclusively on provided training arrays and returns model with diagnostics (`MOD-04`, AC 1)  
Proof: run unit | tests/unit/models/test_model_fit.py::test_m41_04_01_fit_model_trainable PASSED

**C14** - `fit_model` bypasses training as a transparent no-op when `requires_fit=False` (`MOD-04`, AC 2)  
Proof: run unit | tests/unit/models/test_model_fit.py::test_m41_04_02_fit_model_analytical_bypass PASSED

**C15** - `fit_model` raises `ContractViolationError` on sample count mismatch ($N_X \neq N_y$) or empty arrays (`MOD-04`, AC 3)  
Proof: run unit | tests/unit/models/test_model_fit.py::test_m41_04_03_fit_model_dimension_mismatch_and_empty PASSED

**C16** - `predict_model` returns dictionary with keys `"y_pred"`, `"y_std"`, and `"y_proba"`, with 1D `y_pred` matching sample count (`MOD-05`, AC 1)  
Proof: run unit | tests/unit/models/test_model_predict.py::test_m41_05_01_predict_model_output_structure PASSED

**C17** - `predict_model` produces a 1D finite non-negative `y_std` when `supports_uncertainty=True` (`MOD-05`, AC 2)  
Proof: run unit | tests/unit/models/test_model_predict.py::test_m41_05_02_predict_model_uncertainty_valid PASSED

**C18** - `predict_model` produces a 2D `y_proba` in $[0.0, 1.0]$ summing to $1.0$ per row when `supports_predict_proba=True` (`MOD-05`, AC 3)  
Proof: run unit | tests/unit/models/test_model_predict.py::test_m41_05_03_predict_model_predict_proba_valid PASSED

**C19** - `predict_model` sets `y_std` to `None` when `supports_uncertainty=False` (`MOD-05`, AC 4)  
Proof: run unit | tests/unit/models/test_model_predict.py::test_m41_05_04_predict_model_uncertainty_disabled_none PASSED

**C20** - `predict_model` sets `y_proba` to `None` when `supports_predict_proba=False` without converting decision function (`MOD-05`, AC 5)  
Proof: run unit | tests/unit/models/test_model_predict.py::test_m41_05_05_predict_model_predict_proba_disabled_none PASSED

**C21** - `predict_model` raises `ContractViolationError` when invoked on an unfitted trainable estimator (`MOD-05`, AC 6)  
Proof: run unit | tests/unit/models/test_model_predict.py::test_m41_05_06_predict_model_unfitted_rejection PASSED

**C22** - `predict_model` raises `ContractViolationError` when an estimator declared with uncertainty produces invalid or negative `y_std` (`MOD-05`, AC 7)  
Proof: run unit | tests/unit/models/test_model_predict.py::test_m41_05_07_predict_model_uncertainty_runtime_violation PASSED

**C23** - `predict_model` raises `ContractViolationError` when an estimator declared with predict_proba produces invalid probabilities or non-unit row sums (`MOD-05`, AC 8)  
Proof: run unit | tests/unit/models/test_model_predict.py::test_m41_05_08_predict_model_predict_proba_runtime_violation PASSED

**C24** - `extract_model_diagnostics` returns immutable `ModelDiagnostics` record with native scalars and immutable mappings (`MOD-06`, AC 1)  
Proof: run unit | tests/unit/models/test_model_diagnostics.py::test_m41_06_01_extract_model_diagnostics_structure PASSED

**C25** - `extract_model_diagnostics` operates as an independent snapshot unaffected by subsequent model mutations (`MOD-06`, AC 2)  
Proof: run unit | tests/unit/models/test_model_diagnostics.py::test_m41_06_02_extract_model_diagnostics_snapshot_independence PASSED

**C26** - `extract_model_diagnostics` raises `ContractViolationError` when encountering unsupported mutable complex objects (`MOD-06`, AC 3)  
Proof: run unit | tests/unit/models/test_model_diagnostics.py::test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection PASSED

**C27** - `extract_model_diagnostics` never mutates the model instance or alters its future predictions (`MOD-06`, AC 4)  
Proof: run unit | tests/unit/models/test_model_diagnostics.py::test_m41_06_04_extract_model_diagnostics_model_mutation_invariance PASSED

**C28** - `validate_models_catalog` validates a sequence of `ModelSpec` objects and returns immutable mapping indexed by model_id (`MOD-07`, AC 1)  
Proof: run unit | tests/unit/models/test_model_spec.py::test_m41_07_01_validate_models_catalog_valid PASSED

**C29** - `validate_models_catalog` raises `ConfigurationError` when duplicate `model_id` values are detected (`MOD-07`, AC 2)  
Proof: run unit | tests/unit/models/test_model_spec.py::test_m41_07_02_validate_models_catalog_duplicate_ids PASSED

**C30** - `DummyBaselineModel` produces mean prediction and standard deviation uncertainty for regression (`MOD-08`, AC 1)  
Proof: run unit | tests/unit/models/test_model_baselines.py::test_m41_08_01_dummy_baseline_regression_mean PASSED

**C31** - `DummyBaselineModel` produces median prediction and MAD uncertainty for regression (`MOD-08`, AC 2)  
Proof: run unit | tests/unit/models/test_model_baselines.py::test_m41_08_02_dummy_baseline_regression_median PASSED

**C32** - `DummyBaselineModel` produces majority class with lexicographical tie-break and class probabilities for classification (`MOD-08`, AC 3)  
Proof: run unit | tests/unit/models/test_model_baselines.py::test_m41_08_03_dummy_baseline_classification_most_frequent PASSED

**C33** - `AnalyticalBiometricModel` evaluates mathematical expression directly without fitting (`MOD-08`, AC 4)  
Proof: run unit | tests/unit/models/test_model_baselines.py::test_m41_08_04_analytical_biometric_model_direct_eval PASSED

**C34** - `AnalyticalBiometricModel` raises `ContractViolationError` when required input features are missing (`MOD-08`, AC 5)  
Proof: run unit | tests/unit/models/test_model_baselines.py::test_m41_08_05_analytical_biometric_model_missing_feature_rejection PASSED

**C35** - Models module enforces single runtime dependency (`numpy>=1.24.0`) with zero mandatory external ML framework imports (`MOD-09`, AC 1)  
Proof: run integration | tests/integration/models/test_models_integration.py::test_m41_09_01_runtime_purity_numpy_only PASSED

---

## Handoff

**Settled mid-build**: none  
**Dispatched**: none  
**Walked**: pending  

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1 → T2
Phase 2:  T3 → T4 → T5
Phase 3:  T6 → T7
Phase 4:  T8
```

---

## Task Granularity Check

| Task | Scope | Status |
| :--- | :--- | :--- |
| T1: Define ModelFamily enum, ModelCapabilities and ModelDiagnostics dataclasses | Enums, capabilities dataclass, diagnostics dataclass | ✅ Granular |
| T2: Implement ModelSpec dataclass and declarative validation functions | ModelSpec model, validate_model_spec, validate_models_catalog | ✅ Granular |
| T3: Implement fresh model instantiation and instance isolation audit | instantiate_fresh_model, seed handling, memory isolation WeakSet | ✅ Granular |
| T4: Implement functional model fitting with analytical bypass | fit_model, dimension checks, requires_fit no-op bypass | ✅ Granular |
| T5: Implement functional model prediction and tripartite output validation | predict_model, y_pred, y_std, y_proba output contracts | ✅ Granular |
| T6: Implement extract_model_diagnostics with deep snapshot immutability | extract_model_diagnostics, deep snapshot, complex object rejection | ✅ Granular |
| T7: Implement DummyBaselineModel and AnalyticalBiometricModel reference baselines | DummyBaselineModel (mean/median/frequent), AnalyticalBiometricModel | ✅ Granular |
| T8: Expose public module API and implement transversal integration tests | __init__.py, public exports, runtime purity, integration pipeline | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| :--- | :--- | :--- | :--- |
| T1 | None | Phase 1 root (`T1`) | ✅ Match |
| T2 | T1 | Phase 1 continuation (`T1 --> T2`) | ✅ Match |
| T3 | T2 | Phase 2 start (`T2 --> T3`) | ✅ Match |
| T4 | T3 | Phase 2 continuation (`T3 --> T4`) | ✅ Match |
| T5 | T4 | Phase 2 continuation (`T4 --> T5`) | ✅ Match |
| T6 | T5 | Phase 3 start (`T5 --> T6`) | ✅ Match |
| T7 | T6 | Phase 3 continuation (`T6 --> T7`) | ✅ Match |
| T8 | T7 | Phase 4 start (`T7 --> T8`) | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| :--- | :--- | :--- | :--- | :--- |
| T1: Define ModelFamily enum, ModelCapabilities and ModelDiagnostics dataclasses | Model Types & Enums (`src/experimental_ml/models/types.py`) | unit | unit | ✅ OK |
| T2: Implement ModelSpec dataclass and declarative validation functions | Declarative ModelSpec & Catalog (`src/experimental_ml/models/spec.py`) | unit | unit | ✅ OK |
| T3: Implement fresh model instantiation and instance isolation audit | Fresh Instantiation & Isolation (`src/experimental_ml/models/execution.py`) | unit | unit | ✅ OK |
| T4: Implement functional model fitting with analytical bypass | Functional Model Fitting (`src/experimental_ml/models/execution.py`) | unit | unit | ✅ OK |
| T5: Implement functional model prediction and tripartite output validation | Functional Prediction & Outputs (`src/experimental_ml/models/execution.py`) | unit | unit | ✅ OK |
| T6: Implement extract_model_diagnostics with deep snapshot immutability | Internal Diagnostics Snapshot (`src/experimental_ml/models/diagnostics.py`) | unit | unit | ✅ OK |
| T7: Implement DummyBaselineModel and AnalyticalBiometricModel reference baselines | Canonical Baseline & Analytical Models (`src/experimental_ml/models/baselines.py`) | unit | unit | ✅ OK |
| T8: Expose public module API and implement transversal integration tests | Models Integration & Runtime Purity (`tests/integration/models/test_models_integration.py`) | integration | integration | ✅ OK |
