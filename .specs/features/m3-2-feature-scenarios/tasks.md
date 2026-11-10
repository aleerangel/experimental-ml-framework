# m3-2-feature-scenarios Tasks (M3.2 Definição e Validação de Cenários de Features)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m3-2-feature-scenarios/design.md`  
**Status**: Approved  
**Approved**: 2026-11-10 - user: "podemos"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/features/ -v  
**Run integration**: .venv/bin/pytest tests/integration/features/test_scenarios_integration.py -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001` a `AD-004`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 8 requirements (`SCN-01` to `SCN-08`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Scenario Models & Constraints (`src/experimental_ml/features/scenarios.py`) | unit | 1:1 AC mapping: FeatureScenario frozen slots, mode constraints (FIXED vs DYNAMIC), anti-leakage guards, MappingProxy wrapping | `tests/unit/features/test_feature_scenarios.py` | `.venv/bin/pytest tests/unit/features/test_feature_scenarios.py -v` |
| Catalog & View Validation (`src/experimental_ml/features/scenarios.py`) | unit | 1:1 AC mapping: scenario_id uniqueness, candidate features membership, protected columns disjunction, ScenariosCatalog immutability | `tests/unit/features/test_feature_scenarios.py` | `.venv/bin/pytest tests/unit/features/test_feature_scenarios.py -v` |
| Persistence & Stage Gate (`src/experimental_ml/features/scenarios.py`, `src/experimental_ml/stages/stage_gates.py`) | unit | 1:1 AC mapping: write_json_atomic roundtrip, overwrite protection, verify_scenarios_gate hash matching and validation | `tests/unit/features/test_scenarios_storage.py` | `.venv/bin/pytest tests/unit/features/test_scenarios_storage.py -v` |
| Scenarios Integration & Invariants (`tests/integration/features/test_scenarios_integration.py`) | integration | Full end-to-end pipeline from SanitizedDatasetView to scenarios.json and gate verification, runtime purity (XCUT-02) | `tests/integration/features/test_scenarios_integration.py` | `.venv/bin/pytest tests/integration/features/test_scenarios_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After tasks with unit tests in features | `.venv/bin/pytest tests/unit/features/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Scenario Models and Mode Constraints (`P1.1`)

Define immutable data models for `FeatureScenario` and `ScenarioMode`, enforcing strict constraints for `FIXED` and `DYNAMIC` modes and anti-leakage invariants.

```
T1
```

### Phase 2: Catalog Assembly and View Validation Engine (`P1.2`)

Implement `ScenariosCatalog` and `validate_scenarios` against `SanitizedDatasetView`, verifying candidate column membership and protected column disjunction.

```
T2
```

### Phase 3: Atomic Persistence and Stage Gate (`P1.3`)

Implement `save_scenarios`, `load_scenarios`, and the Stage 2 gate `verify_scenarios_gate` in `stages/stage_gates.py`.

```
T3
```

### Phase 4: Public Module Exports and Integration Suite (`P1.4`)

Expose public interfaces in `features/__init__.py` and `stages/__init__.py`, execute end-to-end integration tests, and assert zero runtime dependencies outside NumPy.

```
T4
```

---

## Task Breakdown

### Phase 1: Scenario Models and Mode Constraints (`P1.1`)

#### T1: Implement `FeatureScenario` and mode constraints

**What**: Create `src/experimental_ml/features/scenarios.py` defining `ScenarioMode(StrEnum)` and `FeatureScenario(frozen=True, slots=True)`. In `__post_init__`, validate `scenario_id` (non-empty slug), `name`, `description`, `scientific_justification`, and mode in `{"FIXED", "DYNAMIC"}`. For `FIXED`, require non-empty `selected_features` without duplicates, and forbid `strategy_name` or non-empty `strategy_params`. For `DYNAMIC`, require non-empty `strategy_name`, allow `strategy_params`, and strictly forbid `selected_features` (`selected_features == ()`). Wrap dictionaries in `MappingProxyType`. Implement deterministic `.to_dict()` and `.from_dict()`. Add co-located unit tests in `tests/unit/features/test_feature_scenarios.py`.
**Where**: `src/experimental_ml/features/scenarios.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/enums.py`, `src/experimental_ml/core/findings.py`
**Requirement**: SCN-01, SCN-02, SCN-03

**Done when**:
- [x] `ScenarioMode` and `FeatureScenario` defined with immutability guarantees (`frozen=True, slots=True`)
- [x] `FIXED` mode enforces non-empty unique `selected_features` and forbids dynamic parameters
- [x] `DYNAMIC` mode enforces `strategy_name` and forbids pre-calculated `selected_features`
- [x] `.to_dict()` and `.from_dict()` perform lossless roundtrip conversion
- [x] Unit tests pass in `tests/unit/features/test_feature_scenarios.py`
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/features/test_feature_scenarios.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(features): implementar modelo FeatureScenario e restricoes de modo (SCN-01, SCN-02, SCN-03)`

---

### Phase 2: Catalog Assembly and View Validation Engine (`P1.2`)

#### T2: Implement `ScenariosCatalog` and `validate_scenarios` against view

**What**: In `src/experimental_ml/features/scenarios.py`, define `ScenariosCatalog(frozen=True, slots=True)` with `scenarios: tuple[FeatureScenario, ...]`, `dataset_hash: str`, and `metadata`. Implement `validate_scenarios(scenarios, view)`. Check that `scenarios` is non-empty, all `scenario_id`s are unique, each `FIXED` scenario's `selected_features` belong to `view.candidate_feature_cols`, and have zero intersection with protected columns (`target_col`, `group_col`, `observation_id_col`, `time_col`, `ignore_cols`). Raise `ConfigurationError` or `ContractViolationError` on any mismatch. Return `ScenariosCatalog` bound to `view.dataset_hash`. Implement `.to_dict()` and `.from_dict()` for `ScenariosCatalog`. Add co-located unit tests in `tests/unit/features/test_feature_scenarios.py`.
**Where**: `src/experimental_ml/features/scenarios.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/data/types.py`, `src/experimental_ml/core/findings.py`
**Requirement**: SCN-04, SCN-05, SCN-06

**Done when**:
- [ ] `ScenariosCatalog` defined with immutability and roundtrip serialization
- [ ] `validate_scenarios` verifies unique IDs, candidate feature membership, and protected column disjunction
- [ ] Rejects duplicate IDs, missing features, or protected column inclusions with typed domain errors
- [ ] Returns `ScenariosCatalog` bound to `view.dataset_hash`
- [ ] Unit tests pass in `tests/unit/features/test_feature_scenarios.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/features/test_feature_scenarios.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(features): implementar catalogo e validador de cenarios contra view saneada (SCN-04, SCN-05, SCN-06)`

---

### Phase 3: Atomic Persistence and Stage Gate (`P1.3`)

#### T3: Implement `save_scenarios`, `load_scenarios` and `verify_scenarios_gate`

**What**: In `src/experimental_ml/features/scenarios.py`, implement `save_scenarios(catalog, path, overwrite=False)` using `write_json_atomic` and `load_scenarios(path)` using `read_json`. In `src/experimental_ml/stages/stage_gates.py`, implement `verify_scenarios_gate(catalog_path, view)`: verify physical file existence, load catalog, assert `catalog.dataset_hash == view.dataset_hash` (raise `DataIntegrityError` if mismatch), re-validate scenarios against the view, and return the validated catalog. Add co-located unit tests in `tests/unit/features/test_scenarios_storage.py`.
**Where**: `src/experimental_ml/stages/stage_gates.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/core/storage.py`, `src/experimental_ml/core/findings.py`, `src/experimental_ml/data/preparation.py`
**Requirement**: SCN-07, SCN-08

**Done when**:
- [ ] `save_scenarios` writes `scenarios.json` atomically and respects `overwrite=False`
- [ ] `load_scenarios` restores validated `ScenariosCatalog`
- [ ] `verify_scenarios_gate` checks file existence, dataset hash equality, and structural re-validation
- [ ] Unit tests pass in `tests/unit/features/test_scenarios_storage.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/features/ -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(features): implementar persistencia atomica e portao de cenarios (SCN-07, SCN-08)`

---

### Phase 4: Public Module Exports and Integration Suite (`P1.4`)

#### T4: Expose public API and implement scenarios integration test suite

**What**: In `src/experimental_ml/features/__init__.py`, export `FeatureScenario`, `ScenarioMode`, `ScenariosCatalog`, `validate_scenarios`, `save_scenarios`, `load_scenarios` in `__all__`. In `src/experimental_ml/stages/__init__.py`, export `verify_scenarios_gate`. Create `tests/integration/features/test_scenarios_integration.py` exercising the full pipeline: dataset loading -> profiling -> preparation -> sanitization -> feature exploration -> scenario definition and validation -> atomic save -> stage gate verification, with zero runtime dependencies outside NumPy (`XCUT-02`).
**Where**: `src/experimental_ml/features/__init__.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/data/`, `src/experimental_ml/features/`, `src/experimental_ml/stages/`
**Requirement**: SCN-01, SCN-02, SCN-03, SCN-04, SCN-05, SCN-06, SCN-07, SCN-08

**Done when**:
- [ ] Public symbols exported in `features/__init__.py` and `stages/__init__.py`
- [ ] Integration suite verifies end-to-end flow from raw data ingestion to verified scenarios gate
- [ ] Subprocess test proves absence of external ML libraries in `sys.modules` (`XCUT-02`)
- [ ] Full test suite passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(features): exportar api publica e consolidar suite de integracao do m3-2 (SCN-01 a SCN-08)`

---

## Checks

**C1** - `FeatureScenario` enforces immutability, validated string fields and MappingProxy parameters (`SCN-01`, AC 1)  
Proof: run unit | tests/unit/features/test_feature_scenarios.py::test_scn_01_feature_scenario_immutability PASSED

**C2** - Fixed scenarios enforce non-empty sequence of unique `selected_features` and forbid dynamic strategy parameters (`SCN-02`, AC 2)  
Proof: run unit | tests/unit/features/test_feature_scenarios.py::test_scn_02_fixed_scenario_constraints PASSED

**C3** - Dynamic scenarios enforce `strategy_name` and strictly forbid pre-calculated `selected_features` as an anti-leakage invariant (`SCN-03`, AC 3)  
Proof: run unit | tests/unit/features/test_feature_scenarios.py::test_scn_03_dynamic_scenario_anti_leakage PASSED

**C4** - `validate_scenarios` confirms unique scenario IDs, candidate feature membership, and returns `ScenariosCatalog` bound to `view.dataset_hash` (`SCN-04`, AC 4)  
Proof: run unit | tests/unit/features/test_feature_scenarios.py::test_scn_04_validate_scenarios_success PASSED

**C5** - `validate_scenarios` rejects duplicate IDs, unknown features, or features intersecting with protected roles (`SCN-05`, AC 5)  
Proof: run unit | tests/unit/features/test_feature_scenarios.py::test_scn_05_validate_scenarios_rejections PASSED

**C6** - `ScenariosCatalog.to_dict()` and `ScenariosCatalog.from_dict()` perform lossless roundtrip serialization conforming to JSON standards (`SCN-06`, AC 6)  
Proof: run unit | tests/unit/features/test_feature_scenarios.py::test_scn_06_roundtrip_serialization PASSED

**C7** - `save_scenarios` writes atomically and respects `overwrite=False`, and `load_scenarios` restores the validated catalog (`SCN-07`, AC 7)  
Proof: run unit | tests/unit/features/test_scenarios_storage.py::test_scn_07_save_and_load_scenarios PASSED

**C8** - Full pipeline from dataset ingestion to sanitized view, scenario validation, atomic persistence, and stage gate passes with hash integrity and runtime purity (`SCN-08`, AC 8)  
Proof: run integration | tests/integration/features/test_scenarios_integration.py::test_scn_08_end_to_end_scenarios_gate PASSED

---

## Handoff

**Settled mid-build**: none  
**Dispatched**: none  
**Walked**: pending  

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1
Phase 2:  T2
Phase 3:  T3
Phase 4:  T4
```

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1: Implement `FeatureScenario` and mode constraints | Scenario model, immutability, FIXED/DYNAMIC validation | ✅ Granular |
| T2: Implement `ScenariosCatalog` and `validate_scenarios` against view | Catalog model, candidate membership, role disjunction | ✅ Granular |
| T3: Implement `save_scenarios`, `load_scenarios` and `verify_scenarios_gate` | Storage utilities, JSON roundtrip, Stage 2 gate | ✅ Granular |
| T4: Expose public API and implement scenarios integration test suite | Public exports, end-to-end pipeline, runtime purity | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | Phase 1 root (`T1`) | ✅ Match |
| T2 | T1 | Phase 2 start after Phase 1 (`T2`) | ✅ Match |
| T3 | T2 | Phase 3 start after Phase 2 (`T3`) | ✅ Match |
| T4 | T3 | Phase 4 start after Phase 3 (`T4`) | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1: Implement `FeatureScenario` and mode constraints | Scenario Models & Constraints (`src/experimental_ml/features/scenarios.py`) | unit | unit | ✅ OK |
| T2: Implement `ScenariosCatalog` and `validate_scenarios` against view | Catalog & View Validation (`src/experimental_ml/features/scenarios.py`) | unit | unit | ✅ OK |
| T3: Implement `save_scenarios`, `load_scenarios` and `verify_scenarios_gate` | Persistence & Stage Gate (`src/experimental_ml/stages/stage_gates.py`) | unit | unit | ✅ OK |
| T4: Expose public API and implement scenarios integration test suite | Scenarios Integration & Invariants (`tests/integration/features/test_scenarios_integration.py`) | integration | integration | ✅ OK |
