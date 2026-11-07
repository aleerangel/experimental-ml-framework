# m2-3-partitioning-engine Tasks (M2.3 Partitioning Engine)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m2-3-partitioning-engine/design.md`
**Status**: Approved
**Approved**: 2026-11-07 - user: "aprovado"
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates
**Run unit**: .venv/bin/pytest tests/unit/validation/ -v
**Run integration**: .venv/bin/pytest tests/integration/test_validation_integration.py -v

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001`, `AD-002`, `AD-003`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 10 requirements (`PART-01` to `PART-10`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Validation Data Models & Configuration (`src/experimental_ml/validation/types.py`) | unit | 1:1 AC mapping: dataclass immutability, frozen slots, enum coercion, boundary checks, SHA-256 plan_id | `tests/unit/validation/test_types.py` | `.venv/bin/pytest tests/unit/validation/test_types.py -v` |
| Partition Splitter Engines (`src/experimental_ml/validation/splitters.py`) | unit | 1:1 AC mapping: K-Fold disjunction, stratified class ratios, group non-overlap, temporal monotonicity, bootstrap OOB, holdout extraction | `tests/unit/validation/test_splitters.py` | `.venv/bin/pytest tests/unit/validation/test_splitters.py -v` |
| Mathematical Invariants Validator (`src/experimental_ml/validation/validators.py`) | unit | 1:1 AC mapping: train/val disjointness, holdout isolation, group boundary enforcement, temporal monotonicity, error raising | `tests/unit/validation/test_validators.py` | `.venv/bin/pytest tests/unit/validation/test_validators.py -v` |
| Partition Plan Builder Engine (`src/experimental_ml/validation/engine.py`) | unit | 1:1 AC mapping: holdout/development separation, cross-validation dispatch, plan_id canonical calculation | `tests/unit/validation/test_engine.py` | `.venv/bin/pytest tests/unit/validation/test_engine.py -v` |
| Validation Integration & Architecture Invariants (`tests/integration/test_validation_integration.py`) | integration | End-to-end partitioning on sanitized views and bundles, determinism across runs, layer import direction | `tests/integration/test_validation_integration.py` | `.venv/bin/pytest tests/integration/test_validation_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After tasks with unit tests in validation | `.venv/bin/pytest tests/unit/validation/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Validation Types & Configuration Validation (`P1.1`)

Define immutable data structures for partitions, configuration with threshold validation, and canonical plan identification.

```
T1
```

### Phase 2: Pure Partitioning Splitter Algorithms (`P1.2`)

Implement pure splitting algorithms for K-Fold, Stratified K-Fold, Holdout, Group K-Fold, Bootstrap (OOB), and Temporal divisions.

```
T2 → T3
```

### Phase 3: Mathematical Validator & Plan Builder Engine (`P1.3`)

Implement mathematical verification of partition disjointness and the main `build_partition_plan` builder engine.

```
T4 → T5
```

### Phase 4: Integration, Invariants & Public Package Exports (`P1.4`)

Expose public API in `experimental_ml.validation` and verify end-to-end integration, determinism, and layer import isolation.

```
T6
```

---

## Task Breakdown

### Phase 1: Validation Types & Configuration Validation (`P1.1`)

#### T1: Implement validation data models and configuration in `validation/types.py`

**What**: Create `src/experimental_ml/validation/types.py` defining `PartitionStrategy` (StrEnum: `KFOLD`, `STRATIFIED_KFOLD`, `GROUP_KFOLD`, `BOOTSTRAP`, `TEMPORAL`, `HOLDOUT`), `EvaluationRegime` (StrEnum: `CV_ONLY`, `HOLDOUT_ONLY`, `CV_AND_HOLDOUT`), `FoldPartition` (frozen dataclass, slots=True), `PartitionConfig` (frozen dataclass, slots=True with validation in `__post_init__` raising `ConfigurationError` on invalid bounds), and `PartitionPlan` (frozen dataclass, slots=True). Add co-located unit tests in `tests/unit/validation/test_types.py`.
**Where**: `src/experimental_ml/validation/types.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/types.py`, `src/experimental_ml/core/findings.py`, `src/experimental_ml/core/enums.py`
**Requirement**: PART-08, PART-10

**Done when**:
- [x] `PartitionStrategy` and `EvaluationRegime` enums defined
- [x] `FoldPartition`, `PartitionConfig`, `PartitionPlan` defined with `frozen=True, slots=True`
- [x] `PartitionConfig.__post_init__` raises `ConfigurationError` on invalid bounds (`n_splits < 2` for CV, invalid `holdout_fraction`, missing columns)
- [x] Unit tests verify immutability, slots, and parameter validation
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/validation/test_types.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(validation): definir modelos e configuracao de particionamento`

---

### Phase 2: Pure Partitioning Splitter Algorithms (`P1.2`)

#### T2: Implement K-Fold, Stratified K-Fold, and Holdout splitters in `validation/splitters.py`

**What**: Create `src/experimental_ml/validation/splitters.py` implementing `kfold_split` (uniform division with deterministic permutation when `shuffle=True`), `stratified_kfold_split` (balanced class allocation across folds within $\pm 1$ sample of nominal proportion), and `holdout_split` (deterministic split into development and holdout subsets with optional stratification). Add co-located unit tests in `tests/unit/validation/test_splitters.py`.
**Where**: `src/experimental_ml/validation/splitters.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/core/seeds.py`, `src/experimental_ml/core/types.py`
**Requirement**: PART-01, PART-02, PART-06

**Done when**:
- [x] `kfold_split` divides observations into $K$ disjoint validation folds with complete coverage
- [x] `stratified_kfold_split` preserves class distribution within $\pm 1$ sample per fold
- [x] `holdout_split` extracts disjoint development and holdout partitions according to fraction
- [x] Unit tests verify deterministic split behavior and fold disjointness
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/validation/test_splitters.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(validation): implementar splitters kfold estratificado e holdout`

---

#### T3: Implement Group K-Fold, Bootstrap, and Temporal splitters in `validation/splitters.py`

**What**: Implement in `src/experimental_ml/validation/splitters.py` the `group_kfold_split` (greedy LPT bin-packing ensuring $\text{Groups}(Train) \cap \text{Groups}(Val) = \emptyset$ and raising `ConfigurationError` if unique groups $< K$), `bootstrap_split` (sampling with replacement of size $N$ for training and strictly out-of-bag observations for validation), and `temporal_split` (chronological sorting by `time_col` with expanding window ensuring $\max(Time(Train)) \le \min(Time(Val))$). Add co-located unit tests in `tests/unit/validation/test_splitters.py`.
**Where**: `src/experimental_ml/validation/splitters.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/core/seeds.py`, `src/experimental_ml/core/findings.py`
**Requirement**: PART-03, PART-04, PART-05

**Done when**:
- [x] `group_kfold_split` guarantees 100% group non-overlap and raises `ConfigurationError` if groups $< K$
- [x] `bootstrap_split` produces resamples with size $N$ in train and disjoint out-of-bag in validation
- [x] `temporal_split` guarantees monotonic chronological ordering without future leakage
- [x] Unit tests for group, bootstrap, and temporal splits pass
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/validation/test_splitters.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(validation): implementar splitters agrupado bootstrap e temporal`

---

### Phase 3: Mathematical Validator & Plan Builder Engine (`P1.3`)

#### T4: Implement `validate_partition_plan` in `validation/validators.py`

**What**: Create `src/experimental_ml/validation/validators.py` implementing `validate_partition_plan(plan, data_or_view)`. Validate mathematical disjointness: $\text{Train}_k \cap \text{Val}_k = \emptyset$ for all folds, $(\text{Train}_k \cup \text{Val}_k) \cap \text{Holdout} = \emptyset$, all IDs belong to source dataset, group non-overlap for `GROUP_KFOLD`, and temporal monotonicity for `TEMPORAL`. Raise `DataIntegrityError` on any violation. Add co-located unit tests in `tests/unit/validation/test_validators.py`.
**Where**: `src/experimental_ml/validation/validators.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/core/findings.py`, `src/experimental_ml/validation/types.py`
**Requirement**: PART-07

**Done when**:
- [ ] Proves mathematical disjointness $\text{Train}_k \cap \text{Val}_k = \emptyset$
- [ ] Proves holdout disjointness with training and validation sets
- [ ] Checks group disjointness and temporal monotonicity when applicable
- [ ] Raises `DataIntegrityError` on any detected overlap or ordering violation
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/validation/test_validators.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(validation): implementar validador matematico de planos de particao`

---

#### T5: Implement `build_partition_plan` and `plan_id` calculation in `validation/engine.py`

**What**: Create `src/experimental_ml/validation/engine.py` implementing `build_partition_plan(data_or_view, config)`. Extract observations and columns adhering strictly to public contracts (`SanitizedDatasetView` or `DatasetBundle`). Execute holdout separation if required (D7: `development_ids`), dispatch to appropriate splitter on `development_ids`, compute canonical deterministic `plan_id` via SHA-256 over configuration, dataset hash, development IDs, holdout IDs, and fold partitions. Run `validate_partition_plan` before returning immutable `PartitionPlan`. Add co-located unit tests in `tests/unit/validation/test_engine.py`.
**Where**: `src/experimental_ml/validation/engine.py`
**Depends on**: T4
**Reuses**: `src/experimental_ml/core/hashing.py`, `src/experimental_ml/validation/splitters.py`, `src/experimental_ml/validation/validators.py`
**Requirement**: PART-01, PART-06, PART-08, PART-09

**Done when**:
- [ ] `build_partition_plan` coordinates holdout separation and CV splitting on `development_ids`
- [ ] Canonical `plan_id` computed via SHA-256 ignoring volatile timestamps
- [ ] Validates partition plan mathematically before returning
- [ ] Unit tests for CV, Holdout, and CV+Holdout regimes pass
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/validation/test_engine.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(validation): implementar motor de construcao de PartitionPlan`

---

### Phase 4: Integration, Invariants & Public Package Exports (`P1.4`)

#### T6: Expose public symbols in `validation/__init__.py` and add integration test suite

**What**: Create `src/experimental_ml/validation/__init__.py` exporting `PartitionStrategy`, `EvaluationRegime`, `FoldPartition`, `PartitionConfig`, `PartitionPlan`, `build_partition_plan`, and `validate_partition_plan`. Implement integration test suite in `tests/integration/test_validation_integration.py` verifying end-to-end partitioning on realistic datasets, determinism across repeated executions with identical seeds, and architectural import direction isolation (`validation` does not import `models` or internal `data.preparation`).
**Where**: `src/experimental_ml/validation/__init__.py`
**Depends on**: T5
**Reuses**: `src/experimental_ml/validation/types.py`, `src/experimental_ml/validation/engine.py`, `src/experimental_ml/validation/validators.py`
**Requirement**: PART-09

**Done when**:
- [ ] Public symbols exported from `experimental_ml.validation`
- [ ] Integration tests verify strict determinism (identical `plan_id` and partitions across runs)
- [ ] Architectural import isolation confirmed (zero imports from `models`, `cli`, or private `data` modules)
- [ ] Full gate check passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration
**Gate**: full
**Commit**: `feat(validation): exportar simbolos publicos de validacao e suite de integracao`

---

## Checks

The checks below verify every acceptance criterion (`PART-01` to `PART-10`). Each check settles an observable claim against its exact proof.

**C1** - `build_partition_plan` with `regime = "CV_ONLY"` and `strategy = "KFOLD"` partitions `observation_ids` into $K$ disjoint validation folds whose union equals `development_ids`, with `holdout_ids = ()`, and $\text{Train}_k \cap \text{Val}_k = \emptyset$ (`PART-01`, AC 1)
Proof: run unit | tests/unit/validation/test_engine.py::test_part_01_kfold_cv_only PASSED

**C2** - `build_partition_plan` with `strategy = "STRATIFIED_KFOLD"` preserves class frequency proportions in each validation fold within 1 sample (`PART-02`, AC 2)
Proof: run unit | tests/unit/validation/test_splitters.py::test_part_02_stratified_kfold_proportions PASSED

**C3** - `build_partition_plan` with `strategy = "GROUP_KFOLD"` guarantees $\text{Groups}(\text{Train}_k) \cap \text{Groups}(\text{Val}_k) = \emptyset$ for every fold (`PART-03`, AC 3)
Proof: run unit | tests/unit/validation/test_splitters.py::test_part_03_group_kfold_disjointness PASSED

**C4** - `build_partition_plan` with `strategy = "TEMPORAL"` sorts observations by time ensuring $\max(\text{Time}(\text{Train}_k)) \le \min(\text{Time}(\text{Val}_k))$ (`PART-04`, AC 4)
Proof: run unit | tests/unit/validation/test_splitters.py::test_part_04_temporal_monotonicity PASSED

**C5** - `build_partition_plan` with `strategy = "BOOTSTRAP"` generates $B$ resamples where each training set is sampled with replacement and validation set contains strictly out-of-bag observations (`PART-05`, AC 5)
Proof: run unit | tests/unit/validation/test_splitters.py::test_part_05_bootstrap_oob PASSED

**C6** - `build_partition_plan` with `regime = "CV_AND_HOLDOUT"` or `"HOLDOUT_ONLY"` partitions into `holdout_ids` and `development_ids` disjointly, confining CV folds to `development_ids` (`PART-06`, AC 6)
Proof: run unit | tests/unit/validation/test_engine.py::test_part_06_holdout_separation PASSED

**C7** - `validate_partition_plan` verifies mathematical disjointness, holdout disjointness, group non-overlap, and temporal monotonicity, raising `DataIntegrityError` if violated (`PART-07`, AC 7)
Proof: run unit | tests/unit/validation/test_validators.py::test_part_07_validate_partition_plan_invariants PASSED

**C8** - `PartitionPlan` exposes `plan_id` as deterministic 64-char SHA-256 digest computed from dataset hash, config, development, holdout, and folds (`PART-08`, AC 8)
Proof: run unit | tests/unit/validation/test_types.py::test_part_08_partition_plan_plan_id PASSED

**C9** - Repeated calls to `build_partition_plan` with identical data, config, and `master_seed` produce identical `plan_id` and partitions (`PART-09`, AC 9)
Proof: run integration | tests/integration/test_validation_integration.py::test_part_09_immutability_and_determinism PASSED

**C10** - Rejection of invalid configurations (`n_splits < 2`, invalid `holdout_fraction`, missing `group_col`/`time_col`, groups $< K$) raises `ConfigurationError` (`PART-10`, AC 10)
Proof: run unit | tests/unit/validation/test_types.py::test_part_10_config_boundary_validation PASSED

---

## Handoff

**Settled mid-build**: none
**Dispatched**: none
**Walked**: pending Execute phase

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1
Phase 2:  T2 ------→ T3
Phase 3:  T4 ------→ T5
Phase 4:  T6
```

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1: Validation models and config validation (`validation/types.py`) | Data models + boundary validation unit tests | ✅ Granular |
| T2: K-Fold, Stratified K-Fold, Holdout splitters (`validation/splitters.py`) | Splitter algorithms + unit tests | ✅ Granular |
| T3: Group K-Fold, Bootstrap, Temporal splitters (`validation/splitters.py`) | Specialized splitters + unit tests | ✅ Granular |
| T4: Mathematical validator (`validation/validators.py`) | Validator + disjointness unit tests | ✅ Granular |
| T5: Plan engine and canonical plan_id (`validation/engine.py`) | Builder engine + canonical digest + unit tests | ✅ Granular |
| T6: Package exports and integration suite (`validation/__init__.py`) | Public exports + end-to-end integration suite | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | Phase 1 root (`T1`) | ✅ Match |
| T2 | T1 | Phase 2 start after Phase 1 (`T2`) | ✅ Match |
| T3 | T2 | `T2 → T3` | ✅ Match |
| T4 | T3 | Phase 3 start after Phase 2 (`T4`) | ✅ Match |
| T5 | T4 | `T4 → T5` | ✅ Match |
| T6 | T5 | Phase 4 start after Phase 3 (`T6`) | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1: Validation models and config | Validation Data Models & Config (`src/experimental_ml/validation/types.py`) | unit | unit | ✅ OK |
| T2: KFold, Stratified, Holdout splitters | Partition Splitter Engines (`src/experimental_ml/validation/splitters.py`) | unit | unit | ✅ OK |
| T3: Group, Bootstrap, Temporal splitters | Partition Splitter Engines (`src/experimental_ml/validation/splitters.py`) | unit | unit | ✅ OK |
| T4: Mathematical validator | Mathematical Invariants Validator (`src/experimental_ml/validation/validators.py`) | unit | unit | ✅ OK |
| T5: Plan builder engine | Partition Plan Builder Engine (`src/experimental_ml/validation/engine.py`) | unit | unit | ✅ OK |
| T6: Package exports and integration | Validation Integration (`tests/integration/test_validation_integration.py`) | integration | integration | ✅ OK |
