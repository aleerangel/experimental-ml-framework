# m5-2-matrix-executor-checkpointing Tasks (M5.2 Motor de Execucao Matricial e Checkpointing)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m5-2-matrix-executor-checkpointing/design.md`  
**Status**: Approved  
**Approved**: 2026-11-12 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/orchestration/ -v  
**Run integration**: .venv/bin/pytest tests/integration/orchestration/ -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Matrix Formulation (`src/experimental_ml/orchestration/matrix.py`) | unit | 1:1 AC mapping: build_cell_matrix Cartesian product, canonical sorting, CellDescriptor, derive_cell_seed determinism & dispersion | `tests/unit/orchestration/test_matrix_builder.py` | `.venv/bin/pytest tests/unit/orchestration/test_matrix_builder.py -v` |
| Execution State & Persistence (`src/experimental_ml/orchestration/state.py`) | unit | 1:1 AC mapping: MatrixExecutionState, with_cell_update immutability, to/from dict codecs, atomic save/load execution_state.json | `tests/unit/orchestration/test_matrix_state.py` | `.venv/bin/pytest tests/unit/orchestration/test_matrix_state.py -v` |
| Sequential Engine & Callbacks (`src/experimental_ml/orchestration/engine.py`) | unit | 1:1 AC mapping: sequential execution order, immediate artifact writes, incremental state flushing, error policy handling, callbacks, cancellation | `tests/unit/orchestration/test_matrix_engine_sequential.py` | `.venv/bin/pytest tests/unit/orchestration/test_matrix_engine_sequential.py -v` |
| Parallel Engine (`src/experimental_ml/orchestration/engine.py`) | unit | 1:1 AC mapping: outer_n_jobs > 1 concurrent dispatch, thread-safe state updating, parity with sequential execution, parallel error handling | `tests/unit/orchestration/test_matrix_engine_parallel.py` | `.venv/bin/pytest tests/unit/orchestration/test_matrix_engine_parallel.py -v` |
| Checkpoint & Resume (`src/experimental_ml/orchestration/engine.py`) | unit | 1:1 AC mapping: resume_experiment_matrix loading/verifying, skipping completed cells, re-executing missing artifacts, pending & retry_failed | `tests/unit/orchestration/test_matrix_resume.py` | `.venv/bin/pytest tests/unit/orchestration/test_matrix_resume.py -v` |
| Transversal Integration (`tests/integration/orchestration/test_matrix_integration.py`) | integration | Public API exports, full 2x2x2 lifecycle execution, simulated crash and resume recovery, runtime purity (XCUT-02) | `tests/integration/orchestration/test_matrix_integration.py` | `.venv/bin/pytest tests/integration/orchestration/test_matrix_integration.py -v` |

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

### Phase 1: Cartesian Matrix Formulation and Seed Derivation (`P1`)

Formulate the Cartesian product $\mathcal{M} \times \mathcal{C} \times \mathcal{F}$ into canonically ordered `CellDescriptor` instances with deterministic 31-bit derived random seeds via SHA-256.

```
T1
```

### Phase 2: Global Execution State, Codecs, and Atomic Storage (`P2`)

Implement immutable `MatrixExecutionState` to track status transitions and aggregate counters for all cells, with lossless JSON codecs and atomic filesystem persistence.

```
T2
```

### Phase 3: Observability Callbacks and Sequential Matrix Engine (`P3`)

Implement `MatrixProgressCallback` protocol and sequential `run_experiment_matrix` with immediate atomic cell persistence, incremental state flushing, and fault tolerance.

```
T1 --> T3
T2 --> T3
```

### Phase 4: Concurrent Multi-Worker Execution (`P4`)

Implement concurrent cell execution when `outer_n_jobs > 1` using a worker pool, ensuring thread-safe state updating, deterministic output parity, and error handling.

```
T3 --> T4
```

### Phase 5: Resilient Checkpoint and Resume Engine (`P5`)

Implement `resume_experiment_matrix` with physical artifact integrity verification, skipped completed cells, and re-execution of pending or failed cells.

```
T3 --> T5
```

### Phase 6: Public API Exposure and Integration Suite (`P6`)

Export all public matrix orchestration symbols in `src/experimental_ml/orchestration/__init__.py`, execute end-to-end integration lifecycle tests, and verify runtime dependency purity (`XCUT-02`).

```
T4 --> T6
T5 --> T6
```

---

## Task Breakdown

### Phase 1: Cartesian Matrix Formulation and Seed Derivation

#### T1: Implement CellDescriptor, derive_cell_seed, and build_cell_matrix

**What**: Create `src/experimental_ml/orchestration/matrix.py` defining `CellDescriptor` as an immutable frozen dataclass with slots (`cell_id: CellId`, `model_spec: ModelSpec`, `scenario: FeatureScenario`, `fold: FoldPartition`, `cell_seed: int`). Implement `derive_cell_seed` using SHA-256 on `master_seed:model_id:scenario_id:fold_id` returning an integer in $[0, 2^{31} - 2]$. Implement `build_cell_matrix` to generate all $|M| \times |C| \times |F|$ descriptors canonically sorted by `(model_spec.model_id, scenario.scenario_id, fold_id)`. Add unit tests in `tests/unit/orchestration/test_matrix_builder.py`.
**Where**: `src/experimental_ml/orchestration/matrix.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/orchestration/types.py`, `src/experimental_ml/models/spec.py`, `src/experimental_ml/features/scenarios.py`, `src/experimental_ml/validation/types.py`
**Requirement**: ORCH-09

**Done when**:
- [x] `CellDescriptor` defined with frozen dataclass and slots
- [x] `derive_cell_seed` generates deterministic 31-bit integers
- [x] `build_cell_matrix` produces Cartesian product sorted canonically
- [x] Unit tests pass in `tests/unit/orchestration/test_matrix_builder.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/orchestration/test_matrix_builder.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar formulacao da grade matricial e derivacao de sementes (ORCH-09)`

---

### Phase 2: Global Execution State, Codecs, and Atomic Storage

#### T2: Implement MatrixExecutionState, codecs, and atomic persistence

**What**: Create `src/experimental_ml/orchestration/state.py` defining `MatrixExecutionState` as an immutable frozen dataclass with slots (`experiment_id`, `run_id`, `created_at`, `updated_at`, `master_seed`, `total_cells`, `cell_statuses`, `completed_cells`, `failed_cells`, `cancelled_cells`). Implement `with_cell_update` returning a new instance with updated status and recalculated counters. Implement `matrix_execution_state_to_dict` and `matrix_execution_state_from_dict`. Implement `save_execution_state` and `load_execution_state` using `write_json_atomic` and `read_json` targeting `{run_dir}/execution_state.json`. Add unit tests in `tests/unit/orchestration/test_matrix_state.py`.
**Where**: `src/experimental_ml/orchestration/state.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/orchestration/types.py`, `src/experimental_ml/core/storage.py`
**Requirement**: ORCH-10

**Done when**:
- [x] `MatrixExecutionState` defined with frozen immutability and slots
- [x] `with_cell_update` updates cell status and counts immutably
- [x] `matrix_execution_state_to_dict` and `from_dict` achieve round-trip fidelity
- [x] `save_execution_state` atomically writes `execution_state.json`
- [x] `load_execution_state` reconstructs exact instance from disk
- [x] Unit tests pass in `tests/unit/orchestration/test_matrix_state.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/orchestration/test_matrix_state.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar estado global da matriz, codecs e persistencia (ORCH-10)`

---

### Phase 3: Observability Callbacks and Sequential Matrix Engine

#### T3: Implement MatrixProgressCallback and sequential matrix execution

**What**: Create `src/experimental_ml/orchestration/callbacks.py` defining `MatrixProgressCallback` protocol and `NullProgressCallback`. Create `src/experimental_ml/orchestration/engine.py` implementing `run_experiment_matrix` for `outer_n_jobs = 1`. The engine builds the matrix, initializes `MatrixExecutionState`, iterates through cells in canonical order, calls `execute_single_cell`, saves artifacts immediately via `save_cell_artifacts`, flushes updated `execution_state.json`, and triggers callback events. Implement cancellation check support marking unstarted cells as `CANCELLED`. Add unit tests in `tests/unit/orchestration/test_matrix_engine_sequential.py`.
**Where**: `src/experimental_ml/orchestration/engine.py`
**Depends on**: T1, T2
**Reuses**: `src/experimental_ml/orchestration/execution.py`, `src/experimental_ml/orchestration/storage.py`, `src/experimental_ml/orchestration/matrix.py`, `src/experimental_ml/orchestration/state.py`, `src/experimental_ml/orchestration/callbacks.py`
**Requirement**: ORCH-11, ORCH-14

**Done when**:
- [x] `MatrixProgressCallback` protocol and `NullProgressCallback` defined
- [x] `run_experiment_matrix` executes cells sequentially when `outer_n_jobs = 1`
- [x] Cell artifacts and `execution_state.json` saved atomically after every cell
- [x] `FAULT_TOLERANT` mode logs cell failure and proceeds with remaining cells
- [x] `FAIL_FAST` mode halts execution and re-raises exception
- [x] Cancellation marks remaining pending cells as `CANCELLED`
- [x] Unit tests pass in `tests/unit/orchestration/test_matrix_engine_sequential.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/orchestration/test_matrix_engine_sequential.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar motor sequencial da matriz com checkpointing incremental (ORCH-11, ORCH-14)`

---

### Phase 4: Concurrent Multi-Worker Execution

#### T4: Implement multi-worker matrix execution with thread safety

**What**: Extend `src/experimental_ml/orchestration/engine.py` to support `outer_n_jobs > 1`. Dispatch cell executions concurrently using `ThreadPoolExecutor`. Protect `MatrixExecutionState` updates and file flushes with a reentrant lock to eliminate race conditions. Ensure that deterministic cell seeds and isolated data views guarantee identical numerical results to sequential execution regardless of task completion order. Add unit tests in `tests/unit/orchestration/test_matrix_engine_parallel.py`.
**Where**: `src/experimental_ml/orchestration/engine.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/orchestration/engine.py`, `src/experimental_ml/orchestration/state.py`
**Requirement**: ORCH-12

**Done when**:
- [ ] `run_experiment_matrix` with `outer_n_jobs > 1` executes cells concurrently
- [ ] Concurrent state updates are thread-safe without corrupted JSON writes
- [ ] Parallel execution metrics and artifacts match sequential execution
- [ ] Individual cell exceptions in worker threads handled according to error policy
- [ ] Unit tests pass in `tests/unit/orchestration/test_matrix_engine_parallel.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/orchestration/test_matrix_engine_parallel.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar execucao paralela configuravel da matriz (ORCH-12)`

---

### Phase 5: Resilient Checkpoint and Resume Engine

#### T5: Implement resume_experiment_matrix with artifact integrity verification

**What**: Extend `src/experimental_ml/orchestration/engine.py` implementing `resume_experiment_matrix`. Load `{run_dir}/execution_state.json`, rebuild cell descriptors, and inspect physical artifact presence for each cell. If `cell_{id}.json` and `pred_{id}.json` exist and are valid, skip the cell; if missing or corrupted, reset status to `PENDING`. Re-execute `PENDING` cells, and re-execute `FAILED` cells when `retry_failed = True`. Flush state incrementally and return consolidated state. Add unit tests in `tests/unit/orchestration/test_matrix_resume.py`.
**Where**: `src/experimental_ml/orchestration/engine.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/orchestration/engine.py`, `src/experimental_ml/orchestration/storage.py`, `src/experimental_ml/orchestration/state.py`
**Requirement**: ORCH-13

**Done when**:
- [ ] `resume_experiment_matrix` loads state and verifies disk artifacts
- [ ] Verified `COMPLETED` cells are skipped without re-computation
- [ ] Missing or corrupt artifacts trigger re-execution of cell
- [ ] `retry_failed = True` re-executes previously failed cells
- [ ] Final `execution_state.json` reflects all completed and resolved cells
- [ ] Unit tests pass in `tests/unit/orchestration/test_matrix_resume.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/orchestration/test_matrix_resume.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar mecanismo de retomada e checkpoint da matriz (ORCH-13)`

---

### Phase 6: Public API Exposure and Integration Suite

#### T6: Expose public matrix API and verify end-to-end integration and purity

**What**: Update `src/experimental_ml/orchestration/__init__.py` exporting all public matrix types and functions (`CellDescriptor`, `derive_cell_seed`, `build_cell_matrix`, `MatrixExecutionState`, `save_execution_state`, `load_execution_state`, `MatrixProgressCallback`, `NullProgressCallback`, `run_experiment_matrix`, `resume_experiment_matrix`). Implement end-to-end integration tests in `tests/integration/orchestration/test_matrix_integration.py` running a multi-model, multi-scenario, multi-fold matrix, simulating an interrupted run followed by successful resume, and verifying single runtime dependency `numpy>=1.24.0` via subprocess (`XCUT-02`).
**Where**: `src/experimental_ml/orchestration/__init__.py`
**Depends on**: T4, T5
**Reuses**: `src/experimental_ml/orchestration/__init__.py`
**Requirement**: ORCH-09, ORCH-10, ORCH-11, ORCH-12, ORCH-13, ORCH-14

**Done when**:
- [ ] Public matrix API cleanly exported in `src/experimental_ml/orchestration/__init__.py`
- [ ] End-to-end integration test passes executing full matrix lifecycle
- [ ] End-to-end resume test passes verifying crash recovery
- [ ] Subprocess runtime purity check passes asserting zero forbidden ML frameworks
- [ ] Integration gate check passes: `.venv/bin/pytest tests/integration/orchestration/test_matrix_integration.py -v`
- [ ] Full test suite passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(orchestration): expor API publica da matriz e implementar suite de integracao transversal (ORCH-09 a ORCH-14)`

---

## Checks

**C1** - build_cell_matrix produces Cartesian product M x C x F (ORCH-09, AC 1)  
Proof: run unit | tests/unit/orchestration/test_matrix_builder.py::test_m52_01_01_build_cell_matrix_cartesian PASSED

**C2** - build_cell_matrix canonically sorts by model_id, scenario_id, fold_id (ORCH-09, AC 2)  
Proof: run unit | tests/unit/orchestration/test_matrix_builder.py::test_m52_01_02_build_cell_matrix_canonical_sorting PASSED

**C3** - CellDescriptor contains canonical cell_id structure (ORCH-09, AC 3)  
Proof: run unit | tests/unit/orchestration/test_matrix_builder.py::test_m52_01_03_cell_descriptor_canonical_id PASSED

**C4** - derive_cell_seed produces deterministic 31-bit integer (ORCH-09, AC 4)  
Proof: run unit | tests/unit/orchestration/test_matrix_builder.py::test_m52_01_04_derive_cell_seed_determinism PASSED

**C5** - derive_cell_seed produces distinct seeds for differing inputs (ORCH-09, AC 4)  
Proof: run unit | tests/unit/orchestration/test_matrix_builder.py::test_m52_01_05_derive_cell_seed_dispersion PASSED

**C6** - MatrixExecutionState immutable frozen dataclass fields (ORCH-10, AC 1)  
Proof: run unit | tests/unit/orchestration/test_matrix_state.py::test_m52_02_01_matrix_execution_state_fields PASSED

**C7** - MatrixExecutionState.with_cell_update immutably updates status and counts (ORCH-10, AC 1)  
Proof: run unit | tests/unit/orchestration/test_matrix_state.py::test_m52_02_02_with_cell_update_immutability PASSED

**C8** - matrix_execution_state_to_dict produces JSON-serializable dictionary (ORCH-10, AC 2)  
Proof: run unit | tests/unit/orchestration/test_matrix_state.py::test_m52_02_03_state_to_dict_json_serializable PASSED

**C9** - matrix_execution_state_from_dict round-trip fidelity (ORCH-10, AC 3)  
Proof: run unit | tests/unit/orchestration/test_matrix_state.py::test_m52_02_04_state_from_dict_roundtrip PASSED

**C10** - save_execution_state and load_execution_state atomic file persistence (ORCH-10, AC 4)  
Proof: run unit | tests/unit/orchestration/test_matrix_state.py::test_m52_02_05_save_and_load_execution_state PASSED

**C11** - run_experiment_matrix executes all cells in sequential canonical order (ORCH-11, AC 1)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_01_sequential_execution_order PASSED

**C12** - run_experiment_matrix atomically writes cell and pred artifacts immediately (ORCH-11, AC 2)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_02_atomic_artifacts_written PASSED

**C13** - run_experiment_matrix incrementally updates execution_state.json per cell (ORCH-11, AC 3)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_03_incremental_state_flushed PASSED

**C14** - run_experiment_matrix FAULT_TOLERANT records FAILED and continues matrix (ORCH-11, AC 4)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_04_fault_tolerant_continues PASSED

**C15** - run_experiment_matrix FAIL_FAST halts execution and re-raises exception (ORCH-11, AC 5)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_05_fail_fast_halts PASSED

**C16** - MatrixProgressCallback receives cell lifecycle events (ORCH-14, AC 1)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_06_progress_callback_events PASSED

**C17** - run_experiment_matrix cancellation marks pending cells CANCELLED and flushes state (ORCH-14, AC 2)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_sequential.py::test_m52_03_07_cancellation_marks_cancelled PASSED

**C18** - run_experiment_matrix outer_n_jobs > 1 dispatches cells concurrently (ORCH-12, AC 1)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_parallel.py::test_m52_04_01_parallel_dispatch PASSED

**C19** - Concurrent updates to execution_state.json are thread-safe without race conditions (ORCH-12, AC 2)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_parallel.py::test_m52_04_02_thread_safe_state_updates PASSED

**C20** - Parallel execution produces identical cell artifacts and metrics as sequential (ORCH-12, AC 3)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_parallel.py::test_m52_04_03_parallel_sequential_parity PASSED

**C21** - Parallel execution handles individual cell failures cleanly (ORCH-12, AC 1)  
Proof: run unit | tests/unit/orchestration/test_matrix_engine_parallel.py::test_m52_04_04_parallel_cell_failure_handling PASSED

**C22** - resume_experiment_matrix loads existing execution_state.json and verifies artifacts (ORCH-13, AC 1)  
Proof: run unit | tests/unit/orchestration/test_matrix_resume.py::test_m52_05_01_resume_loads_and_verifies PASSED

**C23** - resume_experiment_matrix skips verified COMPLETED cells without re-computation (ORCH-13, AC 2)  
Proof: run unit | tests/unit/orchestration/test_matrix_resume.py::test_m52_05_02_resume_skips_completed_cells PASSED

**C24** - resume_experiment_matrix re-executes corrupted or missing COMPLETED cells (ORCH-13, AC 1)  
Proof: run unit | tests/unit/orchestration/test_matrix_resume.py::test_m52_05_03_resume_reexecutes_missing_artifacts PASSED

**C25** - resume_experiment_matrix executes PENDING cells to completion (ORCH-13, AC 3)  
Proof: run unit | tests/unit/orchestration/test_matrix_resume.py::test_m52_05_04_resume_executes_pending_cells PASSED

**C26** - resume_experiment_matrix retries FAILED cells when retry_failed=True (ORCH-13, AC 3)  
Proof: run unit | tests/unit/orchestration/test_matrix_resume.py::test_m52_05_05_resume_retries_failed_cells PASSED

**C27** - Public API cleanly exported in experimental_ml.orchestration (ORCH-09 a ORCH-14)  
Proof: run integration | tests/integration/orchestration/test_matrix_integration.py::test_m52_06_01_public_api_exports PASSED

**C28** - End-to-end matrix lifecycle executes 2x2x2 grid with metrics and predictions (ORCH-11)  
Proof: run integration | tests/integration/orchestration/test_matrix_integration.py::test_m52_06_02_end_to_end_matrix_lifecycle PASSED

**C29** - End-to-end crash-recovery simulation verifies idempotent resume (ORCH-13)  
Proof: run integration | tests/integration/orchestration/test_matrix_integration.py::test_m52_06_03_end_to_end_crash_recovery_resume PASSED

**C30** - Subprocess runtime dependency purity check asserts only numpy and standard library (XCUT-02)  
Proof: run integration | tests/integration/orchestration/test_matrix_integration.py::test_m52_06_04_runtime_purity_xcut_02 PASSED
