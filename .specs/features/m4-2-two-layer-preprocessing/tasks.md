# m4-2-two-layer-preprocessing Tasks (M4.2 Pipeline de Pré-processamento em Duas Camadas)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m4-2-two-layer-preprocessing/design.md`  
**Status**: Approved  
**Approved**: 2026-11-11 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/models/ -v  
**Run integration**: .venv/bin/pytest tests/integration/models/ -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001` a `AD-005`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 7 requirements (`PRE-01` to `PRE-07`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Preprocessing Types & Enums (`src/experimental_ml/models/preprocessing/types.py`) | unit | 1:1 AC mapping: ScalerType enum, PreprocessingStepSpec, TwoLayerPreprocessingSpec, TwoLayerPreprocessingState | `tests/unit/models/test_preprocessing_types.py` | `.venv/bin/pytest tests/unit/models/test_preprocessing_types.py -v` |
| Preprocessing Validation & Duplication Check (`src/experimental_ml/models/preprocessing/pipeline.py`) | unit | 1:1 AC mapping: validate_two_layer_preprocessing duplication rejection (CA-E3-02), pass-through | `tests/unit/models/test_preprocessing_validation.py` | `.venv/bin/pytest tests/unit/models/test_preprocessing_validation.py -v` |
| Pure NumPy Scalers (`src/experimental_ml/models/preprocessing/scalers.py`) | unit | 1:1 AC mapping: StandardScaler, MinMaxScaler, MaxAbsScaler, RobustScaler, AngularScaler zero-variance handling | `tests/unit/models/test_preprocessing_scalers.py` | `.venv/bin/pytest tests/unit/models/test_preprocessing_scalers.py -v` |
| Precomputed Kernel Adapter (`src/experimental_ml/models/preprocessing/kernel.py`) | unit | 1:1 AC mapping: partition passing (X_train, X_train) in fit, (X_eval, X_train) in transform, validation | `tests/unit/models/test_preprocessing_kernel.py` | `.venv/bin/pytest tests/unit/models/test_preprocessing_kernel.py -v` |
| Intra-Fold Fitting (`src/experimental_ml/models/preprocessing/pipeline.py`) | unit | 1:1 AC mapping: fit_two_layer_preprocessing strict dependence on X_train, intermediate projection | `tests/unit/models/test_preprocessing_fit.py` | `.venv/bin/pytest tests/unit/models/test_preprocessing_fit.py -v` |
| Stateless Evaluation Projection (`src/experimental_ml/models/preprocessing/pipeline.py`) | unit | 1:1 AC mapping: apply_two_layer_preprocessing projection, state immutability, column validation | `tests/unit/models/test_preprocessing_apply.py` | `.venv/bin/pytest tests/unit/models/test_preprocessing_apply.py -v` |
| Preprocessing Integration & Runtime Purity (`tests/integration/models/test_preprocessing_integration.py`) | integration | Full two-layer pipeline execution, single runtime dependency (numpy>=1.24.0, zero external ML imports) | `tests/integration/models/test_preprocessing_integration.py` | `.venv/bin/pytest tests/integration/models/test_preprocessing_integration.py -v` |

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

### Phase 1: Declarative Specifications and Duplication Validation (`P1`)

Define domain enumerations (`ScalerType`), immutable specifications (`PreprocessingStepSpec`, `TwoLayerPreprocessingSpec`, `TwoLayerPreprocessingState`), and pure validation logic rejecting accidental duplication across layers (`CA-E3-02`).

```
T1 --> T2
```

### Phase 2: Numerical Scalers and Precomputed Kernel Adapter (`P2`)

Implement pure NumPy scalers with numerical safeguards against zero-variance and constant columns, and the external precomputed kernel partition adapter (`RF3.4`).

```
T3 --> T4
```

### Phase 3: Intra-Fold Fitting and Stateless Projection (`P3`)

Implement `fit_two_layer_preprocessing` with anti-leakage guarantees (`CA-E4B-01`) and `apply_two_layer_preprocessing` for stateless evaluation projection.

```
T5 --> T6
```

### Phase 4: Public API Exports and Transversal Integration Suite (`P4`)

Expose the public module API in `src/experimental_ml/models/preprocessing/__init__.py`, re-export primary functions in `models`, execute end-to-end integration tests, and verify runtime purity without external ML frameworks (`XCUT-02`).

```
T7
```

---

## Task Breakdown

### Phase 1: Declarative Specifications and Duplication Validation (`P1`)

#### T1: Define ScalerType enum, PreprocessingStepSpec, TwoLayerPreprocessingSpec and State dataclasses

**What**: Create `src/experimental_ml/models/preprocessing/types.py` defining `ScalerType` as a closed `str, Enum` with members `STANDARD`, `MINMAX`, `MAXABS`, `ROBUST`, `ANGULAR`, and `NONE`. Define `PreprocessingStepSpec` as an immutable frozen dataclass with slots containing `step_id`, `transformer_type`, `parameters`, and `description`. Define `TwoLayerPreprocessingSpec` as an immutable frozen dataclass with slots containing `layer1_steps`, `layer2_steps`, and `description`. Define `TwoLayerPreprocessingState` as an immutable frozen dataclass with slots containing `spec`, `layer1_fitted_state`, and `layer2_fitted_state`. Add co-located unit tests in `tests/unit/models/test_preprocessing_types.py`.
**Where**: `src/experimental_ml/models/preprocessing/types.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/findings.py`
**Requirement**: PRE-01

**Done when**:
- [x] `ScalerType` defines all 6 canonical members
- [x] `PreprocessingStepSpec` defined with `frozen=True`, `slots=True`, and `MappingProxyType` parameters
- [x] `TwoLayerPreprocessingSpec` defined with `layer1_steps` and `layer2_steps` as immutable tuples
- [x] `TwoLayerPreprocessingState` defined with immutability guarantees
- [x] Unit tests pass in `tests/unit/models/test_preprocessing_types.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_preprocessing_types.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(preprocessing): definir enums, especificacoes declarativas e estado imutavel (PRE-01)`

---

#### T2: Implement validate_two_layer_preprocessing with accidental duplication detection

**What**: Create `src/experimental_ml/models/preprocessing/pipeline.py` implementing `validate_two_layer_preprocessing(spec: TwoLayerPreprocessingSpec) -> TwoLayerPreprocessingSpec`. Validate that `spec` is a valid specification, each step has a valid `step_id` matching alphanumeric format, recognized transformer type, and that no scaler or identical transformation is declared in both Layer 1 and Layer 2 (`CA-E3-02`), raising `ConfigurationError` on conflict. Allow empty specifications as valid pass-through pipelines. Add co-located unit tests in `tests/unit/models/test_preprocessing_validation.py`.
**Where**: `src/experimental_ml/models/preprocessing/pipeline.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/models/preprocessing/types.py`, `src/experimental_ml/core/findings.py`
**Requirement**: PRE-02

**Done when**:
- [x] `validate_two_layer_preprocessing` validates specifications without mutating fields
- [x] Accidental duplication of scalers or transformations across Layer 1 and Layer 2 raises `ConfigurationError`
- [x] Invalid step IDs, unknown transformer types, or bad parameters raise `ConfigurationError`
- [x] Empty specifications are accepted as pass-through
- [x] Unit tests pass in `tests/unit/models/test_preprocessing_validation.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_preprocessing_validation.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(preprocessing): implementar validacao declarativa e deteccao de duplicacao (PRE-02)`

---

### Phase 2: Numerical Scalers and Precomputed Kernel Adapter (`P2`)

#### T3: Implement pure NumPy scalers with zero-variance safeguards

**What**: Create `src/experimental_ml/models/preprocessing/scalers.py` implementing `StandardScaler`, `MinMaxScaler`, `MaxAbsScaler`, `RobustScaler`, and `AngularScaler` in pure NumPy. Ensure numerical stability under degenerate cases: constant columns (zero variance) produce $0.0$ in `StandardScaler`, lower bound in `MinMaxScaler`, $0.0$ in `MaxAbsScaler`, $0.0$ in `RobustScaler`, without zero-division errors. Implement `AngularScaler` mapping features to $[0.0, \pi]$ for parameterized quantum gates. Add co-located unit tests in `tests/unit/models/test_preprocessing_scalers.py`.
**Where**: `src/experimental_ml/models/preprocessing/scalers.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/models/preprocessing/types.py`, `src/experimental_ml/core/findings.py`
**Requirement**: PRE-05

**Done when**:
- [ ] `StandardScaler` centers to $0.0$ and unit variance, handling constant columns cleanly
- [ ] `MinMaxScaler` scales to target range, handling constant columns
- [ ] `MaxAbsScaler` scales to $[-1.0, 1.0]$, handling all-zero columns
- [ ] `RobustScaler` scales by median and IQR, handling zero IQR
- [ ] `AngularScaler` scales features to $[0.0, \pi]$ for quantum gates
- [ ] Unit tests pass in `tests/unit/models/test_preprocessing_scalers.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_preprocessing_scalers.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(preprocessing): implementar escalonadores puros em numpy com salvaguardas (PRE-05)`

---

#### T4: Implement PrecomputedKernelAdapter with non-leakage partition passing

**What**: Create `src/experimental_ml/models/preprocessing/kernel.py` implementing `PrecomputedKernelAdapter(kernel_func: Callable[[np.ndarray, np.ndarray], np.ndarray])`. In `fit(X_train)`, call `kernel_func(X_train, X_train)`, validate that the result is a 2D finite square matrix $(N_{\text{train}}, N_{\text{train}})$, and store an immutable defensive copy of `X_train`. In `transform(X_eval)`, call `kernel_func(X_eval, self.X_train_)` producing a Gram matrix of shape $(N_{\text{eval}}, N_{\text{train}})$. Validate dimensions, finitude, and raise `ContractViolationError` on non-square training matrices or dimension mismatches (`RF3.4`). Add co-located unit tests in `tests/unit/models/test_preprocessing_kernel.py`.
**Where**: `src/experimental_ml/models/preprocessing/kernel.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/core/findings.py`
**Requirement**: PRE-06

**Done when**:
- [ ] `PrecomputedKernelAdapter` passes $(X_{\text{train}}, X_{\text{train}})$ during fit and saves reference
- [ ] `PrecomputedKernelAdapter` passes $(X_{\text{eval}}, X_{\text{train}})$ during transform
- [ ] Non-square training outputs, non-finite values, and dimension mismatches raise `ContractViolationError`
- [ ] Unit tests pass in `tests/unit/models/test_preprocessing_kernel.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_preprocessing_kernel.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(preprocessing): implementar adaptador de kernel precomputado sem vazamento (PRE-06)`

---

### Phase 3: Intra-Fold Fitting and Stateless Projection (`P3`)

#### T5: Implement fit_two_layer_preprocessing with intermediate projection

**What**: In `src/experimental_ml/models/preprocessing/pipeline.py`, implement `fit_two_layer_preprocessing(spec: TwoLayerPreprocessingSpec, X_train: np.ndarray) -> TwoLayerPreprocessingState`. Validate that `X_train` is a non-empty 2D array. Fit Layer 1 steps sequentially on `X_train`, projecting after each step to compute intermediate array `X_inter`. Fit Layer 2 steps sequentially on `X_inter`. Guarantee that all estimated parameters depend strictly on `X_train` (`CA-E4B-01`). Return immutable `TwoLayerPreprocessingState`. Add co-located unit tests in `tests/unit/models/test_preprocessing_fit.py`.
**Where**: `src/experimental_ml/models/preprocessing/pipeline.py`
**Depends on**: T4
**Reuses**: `src/experimental_ml/models/preprocessing/types.py`, `src/experimental_ml/models/preprocessing/scalers.py`, `src/experimental_ml/models/preprocessing/kernel.py`
**Requirement**: PRE-03

**Done when**:
- [ ] `fit_two_layer_preprocessing` fits Layer 1 and Layer 2 sequentially with intermediate projection
- [ ] Parameters depend strictly on `X_train` without reference to evaluation data
- [ ] 1D arrays, empty arrays, or non-finite inputs raise `ContractViolationError`
- [ ] Unit tests pass in `tests/unit/models/test_preprocessing_fit.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_preprocessing_fit.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(preprocessing): implementar ajuste intra-fold com projecao intermediaria (PRE-03)`

---

#### T6: Implement apply_two_layer_preprocessing for stateless evaluation projection

**What**: In `src/experimental_ml/models/preprocessing/pipeline.py`, implement `apply_two_layer_preprocessing(state: TwoLayerPreprocessingState, X_eval: np.ndarray) -> np.ndarray`. Validate that `X_eval` is a non-empty 2D array and its column count matches the feature count expected by the fitted state, raising `ContractViolationError` on mismatch. Apply Layer 1 transformations followed by Layer 2 transformations using exclusively the parameters stored in `state` without re-estimating any statistic or mutating the state. Return the transformed 2D `np.ndarray`. Add co-located unit tests in `tests/unit/models/test_preprocessing_apply.py`.
**Where**: `src/experimental_ml/models/preprocessing/pipeline.py`
**Depends on**: T5
**Reuses**: `src/experimental_ml/models/preprocessing/types.py`, `src/experimental_ml/core/findings.py`
**Requirement**: PRE-04

**Done when**:
- [ ] `apply_two_layer_preprocessing` projects `X_eval` through Layer 1 and Layer 2 using stored state
- [ ] State parameters and attributes are never re-estimated or mutated during projection
- [ ] Feature count mismatches and invalid inputs raise `ContractViolationError`
- [ ] Unit tests pass in `tests/unit/models/test_preprocessing_apply.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/models/test_preprocessing_apply.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(preprocessing): implementar projecao funcional sem estado em avaliacao (PRE-04)`

---

### Phase 4: Public API Exports and Transversal Integration Suite (`P4`)

#### T7: Expose public module API and implement transversal integration tests

**What**: Create `src/experimental_ml/models/preprocessing/__init__.py` exporting all preprocessing public symbols via `__all__`, and re-export `fit_two_layer_preprocessing`, `apply_two_layer_preprocessing`, `validate_two_layer_preprocessing`, `TwoLayerPreprocessingSpec`, and `TwoLayerPreprocessingState` in `src/experimental_ml/models/__init__.py`. Implement transversal integration tests in `tests/integration/models/test_preprocessing_integration.py` exercising the full pipeline: declarative validation, intra-fold fitting, anti-leakage invariance, evaluation projection, and precomputed kernel Gram matrices. Verify runtime purity (`XCUT-02`) via subprocess inspection asserting zero mandatory imports of third-party ML frameworks (scikit-learn, PyTorch, SciPy).
**Where**: `src/experimental_ml/models/preprocessing/__init__.py`
**Depends on**: T6
**Reuses**: `src/experimental_ml/models/preprocessing/types.py`, `src/experimental_ml/models/preprocessing/scalers.py`, `src/experimental_ml/models/preprocessing/kernel.py`, `src/experimental_ml/models/preprocessing/pipeline.py`
**Requirement**: PRE-07

**Done when**:
- [ ] `preprocessing/__init__.py` and `models/__init__.py` cleanly export public API in `__all__`
- [ ] End-to-end integration tests execute full two-layer preprocessing lifecycle
- [ ] Subprocess inspection asserts runtime purity without external ML framework imports
- [ ] Integration tests pass in `tests/integration/models/test_preprocessing_integration.py`
- [ ] Full gate check passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(preprocessing): expor API publica e implementar suite de integracao transversal (PRE-07)`

---

## Checks

**Run unit**: .venv/bin/pytest tests/unit/models/ -v  
**Run integration**: .venv/bin/pytest tests/integration/models/ -v  

**C1** - `ScalerType` is defined as a closed `str, Enum` with all 6 canonical members (`PRE-01`, AC 1)  
Proof: run unit | tests/unit/models/test_preprocessing_types.py::test_m42_01_01_scaler_type_enum PASSED

**C2** - `PreprocessingStepSpec` is defined as an immutable frozen dataclass with slots containing step metadata (`PRE-01`, AC 2)  
Proof: run unit | tests/unit/models/test_preprocessing_types.py::test_m42_01_02_preprocessing_step_spec PASSED

**C3** - `TwoLayerPreprocessingSpec` is defined as an immutable frozen dataclass with slots containing layer steps tuples (`PRE-01`, AC 3)  
Proof: run unit | tests/unit/models/test_preprocessing_types.py::test_m42_01_03_two_layer_preprocessing_spec PASSED

**C4** - `TwoLayerPreprocessingState` is defined as an immutable frozen dataclass with slots containing fitted states (`PRE-01`, AC 4)  
Proof: run unit | tests/unit/models/test_preprocessing_types.py::test_m42_01_04_two_layer_preprocessing_state PASSED

**C5** - `validate_two_layer_preprocessing` validates a valid specification without mutating fields (`PRE-02`, AC 1)  
Proof: run unit | tests/unit/models/test_preprocessing_validation.py::test_m42_02_01_validate_two_layer_valid PASSED

**C6** - `validate_two_layer_preprocessing` raises `ConfigurationError` when the same scaler is declared in both layers (`PRE-02`, AC 2)  
Proof: run unit | tests/unit/models/test_preprocessing_validation.py::test_m42_02_02_validate_two_layer_duplication_rejection PASSED

**C7** - `validate_two_layer_preprocessing` raises `ConfigurationError` on invalid step_id or unrecognized transformer_type (`PRE-02`, AC 3)  
Proof: run unit | tests/unit/models/test_preprocessing_validation.py::test_m42_02_03_validate_two_layer_invalid_step PASSED

**C8** - `validate_two_layer_preprocessing` accepts an empty specification as a valid pass-through pipeline (`PRE-02`, AC 4)  
Proof: run unit | tests/unit/models/test_preprocessing_validation.py::test_m42_02_04_validate_two_layer_empty_passthrough PASSED

**C9** - `fit_two_layer_preprocessing` fits Layer 1 and Layer 2 sequentially with intermediate projection (`PRE-03`, AC 1)  
Proof: run unit | tests/unit/models/test_preprocessing_fit.py::test_m42_03_01_fit_two_layer_preprocessing_execution PASSED

**C10** - `fit_two_layer_preprocessing` ensures fitted statistics depend strictly on training data (`PRE-03`, AC 2)  
Proof: run unit | tests/unit/models/test_preprocessing_fit.py::test_m42_03_02_fit_two_layer_preprocessing_anti_leakage PASSED

**C11** - `fit_two_layer_preprocessing` raises `ContractViolationError` on 1D arrays, empty inputs, or non-finite values (`PRE-03`, AC 3)  
Proof: run unit | tests/unit/models/test_preprocessing_fit.py::test_m42_03_03_fit_two_layer_preprocessing_invalid_inputs PASSED

**C12** - `apply_two_layer_preprocessing` projects evaluation data using strictly stored parameters (`PRE-04`, AC 1)  
Proof: run unit | tests/unit/models/test_preprocessing_apply.py::test_m42_04_01_apply_two_layer_preprocessing_projection PASSED

**C13** - `apply_two_layer_preprocessing` never re-estimates or alters any parameter in fitted state (`PRE-04`, AC 2)  
Proof: run unit | tests/unit/models/test_preprocessing_apply.py::test_m42_04_02_apply_two_layer_preprocessing_state_immutability PASSED

**C14** - `apply_two_layer_preprocessing` raises `ContractViolationError` on feature count mismatch (`PRE-04`, AC 3)  
Proof: run unit | tests/unit/models/test_preprocessing_apply.py::test_m42_04_03_apply_two_layer_preprocessing_feature_count_mismatch PASSED

**C15** - `StandardScaler` centers to 0.0 and unit variance, handling constant columns cleanly (`PRE-05`, AC 1)  
Proof: run unit | tests/unit/models/test_preprocessing_scalers.py::test_m42_05_01_standard_scaler_zero_variance PASSED

**C16** - `MinMaxScaler` scales features into target range, handling constant columns (`PRE-05`, AC 2)  
Proof: run unit | tests/unit/models/test_preprocessing_scalers.py::test_m42_05_02_minmax_scaler_constant_columns PASSED

**C17** - `MaxAbsScaler` scales features into [-1.0, 1.0], handling all-zero columns (`PRE-05`, AC 3)  
Proof: run unit | tests/unit/models/test_preprocessing_scalers.py::test_m42_05_03_maxabs_scaler_zero_columns PASSED

**C18** - `RobustScaler` centers by median and scales by IQR, handling zero IQR columns (`PRE-05`, AC 4)  
Proof: run unit | tests/unit/models/test_preprocessing_scalers.py::test_m42_05_04_robust_scaler_zero_iqr PASSED

**C19** - `AngularScaler` scales features linearly into quantum gate range [0.0, pi] (`PRE-05`, AC 5)  
Proof: run unit | tests/unit/models/test_preprocessing_scalers.py::test_m42_05_05_angular_scaler_quantum_gates PASSED

**C20** - `PrecomputedKernelAdapter` passes (X_train, X_train) in fit and stores copy (`PRE-06`, AC 1)  
Proof: run unit | tests/unit/models/test_preprocessing_kernel.py::test_m42_06_01_kernel_adapter_fit_partition_passing PASSED

**C21** - `PrecomputedKernelAdapter` passes (X_eval, X_train) in transform to compute Gram matrix (`PRE-06`, AC 2)  
Proof: run unit | tests/unit/models/test_preprocessing_kernel.py::test_m42_06_02_kernel_adapter_transform_partition_passing PASSED

**C22** - `PrecomputedKernelAdapter` raises `ContractViolationError` on non-square training outputs or dimension mismatches (`PRE-06`, AC 3)  
Proof: run unit | tests/unit/models/test_preprocessing_kernel.py::test_m42_06_03_kernel_adapter_invalid_matrix_rejection PASSED

**C23** - Preprocessing subsystem exports public API cleanly (`PRE-07`, AC 1)  
Proof: run integration | tests/integration/models/test_preprocessing_integration.py::test_m42_07_01_public_api_exports PASSED

**C24** - Preprocessing subsystem maintains single runtime dependency (numpy>=1.24.0) with zero external ML imports (`PRE-07`, AC 2)  
Proof: run integration | tests/integration/models/test_preprocessing_integration.py::test_m42_07_02_runtime_purity_numpy_only PASSED

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
Phase 2:  T3 → T4
Phase 3:  T5 → T6
Phase 4:  T7
```

---

## Task Granularity Check

| Task | Scope | Status |
| :--- | :--- | :--- |
| T1: Define ScalerType enum, PreprocessingStepSpec, TwoLayerPreprocessingSpec and State dataclasses | Preprocessing types, enums and specs | ✅ Granular |
| T2: Implement validate_two_layer_preprocessing with accidental duplication detection | Declarative validation and duplication checks | ✅ Granular |
| T3: Implement pure NumPy scalers with zero-variance safeguards | Pure NumPy numerical scalers | ✅ Granular |
| T4: Implement PrecomputedKernelAdapter with non-leakage partition passing | Precomputed kernel partition adapter | ✅ Granular |
| T5: Implement fit_two_layer_preprocessing with intermediate projection | Intra-fold fitting and anti-leakage | ✅ Granular |
| T6: Implement apply_two_layer_preprocessing for stateless evaluation projection | Stateless projection and column validation | ✅ Granular |
| T7: Expose public module API and implement transversal integration tests | __init__.py, public exports, runtime purity, integration pipeline | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| :--- | :--- | :--- | :--- |
| T1 | None | Phase 1 root (`T1`) | ✅ Match |
| T2 | T1 | Phase 1 continuation (`T1 --> T2`) | ✅ Match |
| T3 | T2 | Phase 2 start (`T2 --> T3`) | ✅ Match |
| T4 | T3 | Phase 2 continuation (`T3 --> T4`) | ✅ Match |
| T5 | T4 | Phase 3 start (`T4 --> T5`) | ✅ Match |
| T6 | T5 | Phase 3 continuation (`T5 --> T6`) | ✅ Match |
| T7 | T6 | Phase 4 start (`T6 --> T7`) | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| :--- | :--- | :--- | :--- | :--- |
| T1: Define ScalerType enum, PreprocessingStepSpec, TwoLayerPreprocessingSpec and State dataclasses | Preprocessing Types & Enums (`src/experimental_ml/models/preprocessing/types.py`) | unit | unit | ✅ OK |
| T2: Implement validate_two_layer_preprocessing with accidental duplication detection | Preprocessing Validation & Duplication Check (`src/experimental_ml/models/preprocessing/pipeline.py`) | unit | unit | ✅ OK |
| T3: Implement pure NumPy scalers with zero-variance safeguards | Pure NumPy Scalers (`src/experimental_ml/models/preprocessing/scalers.py`) | unit | unit | ✅ OK |
| T4: Implement PrecomputedKernelAdapter with non-leakage partition passing | Precomputed Kernel Adapter (`src/experimental_ml/models/preprocessing/kernel.py`) | unit | unit | ✅ OK |
| T5: Implement fit_two_layer_preprocessing with intermediate projection | Intra-Fold Fitting (`src/experimental_ml/models/preprocessing/pipeline.py`) | unit | unit | ✅ OK |
| T6: Implement apply_two_layer_preprocessing for stateless evaluation projection | Stateless Evaluation Projection (`src/experimental_ml/models/preprocessing/pipeline.py`) | unit | unit | ✅ OK |
| T7: Expose public module API and implement transversal integration tests | Preprocessing Integration & Runtime Purity (`tests/integration/models/test_preprocessing_integration.py`) | integration | integration | ✅ OK |
