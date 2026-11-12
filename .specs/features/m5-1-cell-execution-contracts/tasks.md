# m5-1-cell-execution-contracts Tasks (M5.1 Contratos da Célula e Execução Unitária)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m5-1-cell-execution-contracts/design.md`  
**Status**: Approved  
**Approved**: 2026-11-12 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/orchestration/ -v  
**Run integration**: .venv/bin/pytest tests/integration/orchestration/ -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Orchestration Types & Enums (`src/experimental_ml/orchestration/types.py`) | unit | 1:1 AC mapping: ExecutionStatus, ErrorPolicy, CellPhase enums, CellId, TimingBreakdown, PredictionRecord, CellResultRecord | `tests/unit/orchestration/test_cell_types.py` | `.venv/bin/pytest tests/unit/orchestration/test_cell_types.py -v` |
| Pure Cell Execution (`src/experimental_ml/orchestration/execution.py`) | unit | 1:1 AC mapping: execute_single_cell, fold slicing, feature selection, nested tuning, two-layer preprocessing, fresh model instantiation, fit/predict/eval | `tests/unit/orchestration/test_cell_execution.py` | `.venv/bin/pytest tests/unit/orchestration/test_cell_execution.py -v` |
| Failure Policies & Resilience (`src/experimental_ml/orchestration/execution.py`) | unit | 1:1 AC mapping: FAULT_TOLERANT phase recording, traceback, uncoerced empty metrics, FAIL_FAST immediate re-raising | `tests/unit/orchestration/test_cell_failures.py` | `.venv/bin/pytest tests/unit/orchestration/test_cell_failures.py -v` |
| Codecs & Storage (`src/experimental_ml/orchestration/codecs.py`, `src/experimental_ml/orchestration/storage.py`) | unit | 1:1 AC mapping: cell_result to/from dict, prediction_record to/from dict, atomic file persistence, overwrite protection | `tests/unit/orchestration/test_cell_codecs.py` | `.venv/bin/pytest tests/unit/orchestration/test_cell_codecs.py -v` |
| Orchestration Integration & Purity (`tests/integration/orchestration/test_cell_integration.py`) | integration | Full cell lifecycle pipeline execution, anti-leakage invariance check, runtime purity (numpy>=1.24.0, zero external imports) | `tests/integration/orchestration/test_cell_integration.py` | `.venv/bin/pytest tests/integration/orchestration/test_cell_integration.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After tasks with unit tests in orchestration | `.venv/bin/pytest tests/unit/orchestration/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Domain Types, Enumerations, and Immutable Structures (`P1`)

Define domain enumerations (`ExecutionStatus`, `ErrorPolicy`, `CellPhase`), validated identifier (`CellId`), and frozen data structures (`TimingBreakdown`, `PredictionRecord`, `CellResultRecord`).

```
T1
```

### Phase 2: Functional Cell Execution and Anti-Leakage Isolation (`P2`)

Implement pure functional single-cell executor (`execute_single_cell`), coordinating sequential fold slicing, feature selection, nested tuning, two-layer preprocessing, fresh model fitting, inference, and metric computation.

```
T1 --> T2
```

### Phase 3: Resilient Failure Handling and Error Policies (`P3`)

Implement error handling policies in `execute_single_cell`, capturing exceptions in `FAULT_TOLERANT` mode, recording error phase and traceback without metric coercion, and propagating immediately in `FAIL_FAST` mode.

```
T2 --> T3
```

### Phase 4: Codecs and Atomic File Persistence (`P4`)

Implement lossless dictionary codecs (`to_dict` / `from_dict`) for cell results and prediction records, along with atomic file storage (`save_cell_artifacts`, `load_cell_artifacts`) using `write_json_atomic`.

```
T1 --> T4
```

### Phase 5: Public API Exposure and Integration Suite (`P5`)

Expose public module API in `src/experimental_ml/orchestration/__init__.py`, execute transversal integration pipeline, and verify runtime purity without third-party frameworks (`XCUT-02`).

```
T3 --> T5
T4 --> T5
```

---

## Task Breakdown

### Phase 1: Domain Types, Enumerations, and Immutable Structures

#### T1: Define orchestration enums, CellId, TimingBreakdown, PredictionRecord, and CellResultRecord

**What**: Create `src/experimental_ml/orchestration/types.py` defining `ExecutionStatus`, `ErrorPolicy`, and `CellPhase` as closed string enums. Define `CellId` as a validated string wrapper enforcing non-empty string and format pattern. Define `TimingBreakdown` as an immutable frozen dataclass with slots containing all sub-phase durations and total time. Define `PredictionRecord` as an immutable frozen dataclass validating matching lengths of arrays and encapsulating validation predictions. Define `CellResultRecord` as an immutable frozen dataclass encapsulating cell identifiers, status, parameters, timing, metrics, diagnostics, and error fields. Add unit tests in `tests/unit/orchestration/test_cell_types.py`.
**Where**: `src/experimental_ml/orchestration/types.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/types.py`, `src/experimental_ml/metrics/types.py`, `src/experimental_ml/models/types.py`
**Requirement**: ORCH-01, ORCH-02, ORCH-03, ORCH-04

**Done when**:
- [x] `ExecutionStatus`, `ErrorPolicy`, `CellPhase` defined with all canonical members
- [x] `CellId` validates non-empty string
- [x] `TimingBreakdown` defined with slots and frozen dataclass
- [x] `PredictionRecord` validates length alignment and non-NaN identifiers
- [x] `CellResultRecord` defined with frozen immutability and slots
- [x] Unit tests pass in `tests/unit/orchestration/test_cell_types.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/orchestration/test_cell_types.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): definir enums, CellId e estruturas de dados de celula (ORCH-01 a ORCH-04)`

---

### Phase 2: Functional Cell Execution and Anti-Leakage Isolation

#### T2: Implement pure functional single-cell executor and sequential pipeline

**What**: Create `src/experimental_ml/orchestration/execution.py` implementing `execute_single_cell`. The function slices training and validation subsets from `SanitizedDatasetView` using `fold.train_ids` and `fold.val_ids`, executes feature selection on train and projects validation, executes nested tuning on train when applicable, fits two-layer preprocessing on train and projects validation, instantiates a fresh model with deterministic cell seed, fits the model, predicts on validation data, extracts diagnostics, evaluates all requested metrics preserving `UNDEFINED_NAN`, and populates `CellResultRecord` and `PredictionRecord`. Add unit tests in `tests/unit/orchestration/test_cell_execution.py`.
**Where**: `src/experimental_ml/orchestration/execution.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/data/query.py`, `src/experimental_ml/features/selection.py`, `src/experimental_ml/tuning/engine.py`, `src/experimental_ml/models/preprocessing/pipeline.py`, `src/experimental_ml/models/execution.py`, `src/experimental_ml/metrics/catalog.py`
**Requirement**: ORCH-05, ORCH-06

**Done when**:
- [x] `execute_single_cell` slices train and val sets by fold IDs
- [x] Feature selection operates strictly on train data
- [x] Nested tuning executes confined to train data
- [x] Two-layer preprocessing fits on train and projects val
- [x] Model instantiated cleanly with deterministic seed and unshared state
- [x] Metrics computed preserving `UNDEFINED_NAN`
- [x] Adversarial test proves perturbed `y_val` leaves fitted parameters unchanged
- [x] Unit tests pass in `tests/unit/orchestration/test_cell_execution.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/orchestration/test_cell_execution.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar executor funcional de celula com isolamento anti-leakage (ORCH-05, ORCH-06)`

---

### Phase 3: Resilient Failure Handling and Error Policies

#### T3: Implement error policy handling and failure phase recording

**What**: Extend `src/experimental_ml/orchestration/execution.py` with structured error handling policies. In `ErrorPolicy.FAULT_TOLERANT` mode, catch all exceptions occurring in any sub-phase of cell execution, record the exact `CellPhase`, exception type, message, and traceback, set `status = ExecutionStatus.FAILED`, and return empty metrics (`metrics = {}`) and `prediction_record = None` without process termination or zero coercion. In `ErrorPolicy.FAIL_FAST` mode, immediately re-raise the exception. Add unit tests in `tests/unit/orchestration/test_cell_failures.py`.
**Where**: `src/experimental_ml/orchestration/execution.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/orchestration/types.py`
**Requirement**: ORCH-07

**Done when**:
- [x] `FAULT_TOLERANT` catches exceptions without aborting process
- [x] `CellResultRecord` has `status = ExecutionStatus.FAILED`
- [x] Exact `error_phase`, `error_type`, `error_message`, and `error_traceback` populated
- [x] Metrics dictionary is empty and prediction record is `None` (no coercion to 0.0)
- [x] `FAIL_FAST` propagates exception immediately
- [x] Unit tests pass in `tests/unit/orchestration/test_cell_failures.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/orchestration/test_cell_failures.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar politicas de erro e registro estruturado de falhas (ORCH-07)`

---

### Phase 4: Codecs and Atomic File Persistence

#### T4: Implement lossless codecs and atomic cell persistence

**What**: Create `src/experimental_ml/orchestration/codecs.py` and `src/experimental_ml/orchestration/storage.py` implementing bidirectional dictionary serialization (`cell_result_to_dict`, `cell_result_from_dict`, `prediction_record_to_dict`, `prediction_record_from_dict`) and atomic file persistence (`save_cell_artifacts`, `load_cell_artifacts`). Use `write_json_atomic` to save `runs/cells/cell_<cell_id>.json` and `runs/predictions/pred_<cell_id>.json` with overwrite protection raising `ConfigurationError`. Add unit tests in `tests/unit/orchestration/test_cell_codecs.py`.
**Where**: `src/experimental_ml/orchestration/codecs.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/core/storage.py`, `src/experimental_ml/metrics/codecs.py`
**Requirement**: ORCH-08

**Done when**:
- [ ] `cell_result_to_dict` and `cell_result_from_dict` achieve round-trip fidelity
- [ ] `prediction_record_to_dict` and `prediction_record_from_dict` achieve round-trip fidelity
- [ ] `save_cell_artifacts` atomically writes cell and prediction JSON files
- [ ] `load_cell_artifacts` reconstructs identical instances from disk
- [ ] Existing files trigger `ConfigurationError` when `overwrite=False`
- [ ] Unit tests pass in `tests/unit/orchestration/test_cell_codecs.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/orchestration/test_cell_codecs.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar codecs e persistencia atomica de celulas (ORCH-08)`

---

### Phase 5: Public API Exposure and Integration Suite

#### T5: Expose orchestration public API and verify end-to-end integration and purity

**What**: Create `src/experimental_ml/orchestration/__init__.py` re-exporting all public classes and functions with an explicit `__all__` list. Implement end-to-end integration tests in `tests/integration/orchestration/test_cell_integration.py` executing a full cell across SanitizedDatasetView, PartitionPlan, FeatureScenario, and ModelSpec with Nested CV and TwoLayerPreprocessing. Verify single runtime dependency `numpy>=1.24.0` without third-party ML frameworks via subprocess import inspection (`XCUT-02`).
**Where**: `src/experimental_ml/orchestration/__init__.py`
**Depends on**: T3, T4
**Reuses**: `src/experimental_ml/orchestration/types.py`, `src/experimental_ml/orchestration/execution.py`, `src/experimental_ml/orchestration/codecs.py`, `src/experimental_ml/orchestration/storage.py`
**Requirement**: ORCH-05, ORCH-06, ORCH-08

**Done when**:
- [ ] Public API cleanly exported in `src/experimental_ml/orchestration/__init__.py`
- [ ] End-to-end integration test passes executing complete cell lifecycle
- [ ] Subprocess runtime purity check passes asserting zero external ML imports
- [ ] Integration gate check passes: `.venv/bin/pytest tests/integration/orchestration/test_cell_integration.py -v`
- [ ] Full test suite passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(orchestration): expor API publica e implementar suite de integracao transversal (ORCH-05 a ORCH-08)`

---

## Checks

**C1** - ExecutionStatus enum members: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED (ORCH-01, AC 1)  
Proof: run unit | tests/unit/orchestration/test_cell_types.py::test_m51_01_01_execution_status_enum PASSED

**C2** - ErrorPolicy enum members: FAULT_TOLERANT, FAIL_FAST (ORCH-01, AC 2)  
Proof: run unit | tests/unit/orchestration/test_cell_types.py::test_m51_01_02_error_policy_enum PASSED

**C3** - CellPhase canonical sub-phases (ORCH-01, AC 3)  
Proof: run unit | tests/unit/orchestration/test_cell_types.py::test_m51_01_03_cell_phase_enum PASSED

**C4** - CellId non-empty validation (ORCH-02, AC 1)  
Proof: run unit | tests/unit/orchestration/test_cell_types.py::test_m51_01_04_cell_id_validation PASSED

**C5** - TimingBreakdown non-negative float fields (ORCH-02, AC 2)  
Proof: run unit | tests/unit/orchestration/test_cell_types.py::test_m51_01_05_timing_breakdown_fields PASSED

**C6** - PredictionRecord fields: observation_ids, y_true, y_pred, y_std, y_proba, residuals (ORCH-03, AC 1)  
Proof: run unit | tests/unit/orchestration/test_cell_types.py::test_m51_01_06_prediction_record_fields PASSED

**C7** - PredictionRecord length alignment and non-NaN check (ORCH-03, AC 2)  
Proof: run unit | tests/unit/orchestration/test_cell_types.py::test_m51_01_07_prediction_record_alignment PASSED

**C8** - CellResultRecord fields encapsulation (ORCH-04, AC 1)  
Proof: run unit | tests/unit/orchestration/test_cell_types.py::test_m51_01_08_cell_result_record_fields PASSED

**C9** - Immutability FrozenInstanceError on modification (ORCH-04, AC 2)  
Proof: run unit | tests/unit/orchestration/test_cell_types.py::test_m51_01_09_immutability PASSED

**C10** - execute_single_cell slices train and val sets by fold IDs (ORCH-05, AC 1)  
Proof: run unit | tests/unit/orchestration/test_cell_execution.py::test_m51_02_01_fold_slicing PASSED

**C11** - select_features_in_fold on train and project val without y_val (ORCH-05, AC 2)  
Proof: run unit | tests/unit/orchestration/test_cell_execution.py::test_m51_02_02_feature_selection_isolation PASSED

**C12** - run_nested_tuning on train data and apply theta* (ORCH-05, AC 3)  
Proof: run unit | tests/unit/orchestration/test_cell_execution.py::test_m51_02_03_nested_tuning_integration PASSED

**C13** - fit_two_layer_preprocessing on train and project val (ORCH-05, AC 4)  
Proof: run unit | tests/unit/orchestration/test_cell_execution.py::test_m51_02_04_two_layer_preprocessing_isolation PASSED

**C14** - instantiate_fresh_model with deterministic cell seed (ORCH-06, AC 1)  
Proof: run unit | tests/unit/orchestration/test_cell_execution.py::test_m51_02_05_fresh_model_seed PASSED

**C15** - fit_model on train, predict_model on val, extract diagnostics (ORCH-06, AC 2)  
Proof: run unit | tests/unit/orchestration/test_cell_execution.py::test_m51_02_06_fit_predict_diagnostics PASSED

**C16** - compute_metric evaluates all metrics preserving UNDEFINED_NAN (ORCH-06, AC 3)  
Proof: run unit | tests/unit/orchestration/test_cell_execution.py::test_m51_02_07_metric_evaluation_nan PASSED

**C17** - execute_single_cell returns CellResultRecord COMPLETED and PredictionRecord (ORCH-06, AC 4)  
Proof: run integration | tests/integration/orchestration/test_cell_integration.py::test_m51_02_08_end_to_end_cell_lifecycle PASSED

**C18** - Perturbed y_val leaves fitted parameters bit-for-bit unchanged (ORCH-06, AC 5)  
Proof: run integration | tests/integration/orchestration/test_cell_integration.py::test_m51_02_09_anti_leakage_adversarial PASSED

**C19** - FAULT_TOLERANT catches exceptions without aborting process (ORCH-07, AC 1)  
Proof: run unit | tests/unit/orchestration/test_cell_failures.py::test_m51_03_01_fault_tolerant_catches_exception PASSED

**C20** - FAULT_TOLERANT sets status = FAILED (ORCH-07, AC 2)  
Proof: run unit | tests/unit/orchestration/test_cell_failures.py::test_m51_03_02_status_failed PASSED

**C21** - FAULT_TOLERANT populates exact error_phase (ORCH-07, AC 3)  
Proof: run unit | tests/unit/orchestration/test_cell_failures.py::test_m51_03_03_error_phase_recorded PASSED

**C22** - FAULT_TOLERANT populates error_type, message, and traceback (ORCH-07, AC 4)  
Proof: run unit | tests/unit/orchestration/test_cell_failures.py::test_m51_03_04_error_details_recorded PASSED

**C23** - FAULT_TOLERANT returns empty metrics and prediction_record = None (ORCH-07, AC 5)  
Proof: run unit | tests/unit/orchestration/test_cell_failures.py::test_m51_03_05_no_coercion_to_zero PASSED

**C24** - FAIL_FAST propagates exception immediately (ORCH-07, AC 6)  
Proof: run unit | tests/unit/orchestration/test_cell_failures.py::test_m51_03_06_fail_fast_propagates PASSED

**C25** - cell_result_to_dict produces JSON-serializable dictionary (ORCH-08, AC 1)  
Proof: run unit | tests/unit/orchestration/test_cell_codecs.py::test_m51_04_01_cell_result_to_dict PASSED

**C26** - cell_result_from_dict round-trip fidelity (ORCH-08, AC 2)  
Proof: run unit | tests/unit/orchestration/test_cell_codecs.py::test_m51_04_02_cell_result_from_dict PASSED

**C27** - prediction_record_to_dict produces JSON-serializable dictionary (ORCH-08, AC 3)  
Proof: run unit | tests/unit/orchestration/test_cell_codecs.py::test_m51_04_03_prediction_record_to_dict PASSED

**C28** - prediction_record_from_dict round-trip fidelity (ORCH-08, AC 4)  
Proof: run unit | tests/unit/orchestration/test_cell_codecs.py::test_m51_04_04_prediction_record_from_dict PASSED

**C29** - save_cell_artifacts atomically writes cell_<id>.json and pred_<id>.json (ORCH-08, AC 5)  
Proof: run unit | tests/unit/orchestration/test_cell_codecs.py::test_m51_04_05_atomic_save_artifacts PASSED

**C30** - save_cell_artifacts raises ConfigurationError if files exist and overwrite=False (ORCH-08, AC 6)  
Proof: run unit | tests/unit/orchestration/test_cell_codecs.py::test_m51_04_06_overwrite_protection PASSED
