# m3-4-cli-end-to-end Tasks (M3.4 CLI de Features e Homologação Ponta a Ponta)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m3-4-cli-end-to-end/design.md`  
**Status**: Approved  
**Approved**: 2026-11-10 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/cli/test_cmd_features.py -v  
**Run integration**: .venv/bin/pytest tests/integration/features/test_features_cli_integration.py -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001` a `AD-004`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 8 requirements (`FEAT-01` to `FEAT-08`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Features CLI Exploration (`src/experimental_ml/cli/cmd_features.py`) | unit | 1:1 AC mapping: expml features --help, expml features explore, force flag protection, stderr error formatting | `tests/unit/cli/test_cmd_features.py` | `.venv/bin/pytest tests/unit/cli/test_cmd_features.py -v` |
| Features CLI Scenarios & Gate (`src/experimental_ml/cli/cmd_features.py`) | unit | 1:1 AC mapping: expml features scenarios, invalid scenario error rejection (exit code 2), expml features verify | `tests/unit/cli/test_cmd_features.py` | `.venv/bin/pytest tests/unit/cli/test_cmd_features.py -v` |
| Runtime Purity & E2E Integration (`tests/integration/features/test_features_cli_integration.py`) | integration | Multi-stage subprocess pipeline, stage gates validation, CLI-10 sys.modules purity verification | `tests/integration/features/test_features_cli_integration.py` | `.venv/bin/pytest tests/integration/features/test_features_cli_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After tasks with unit tests in CLI handlers | `.venv/bin/pytest tests/unit/cli/test_cmd_features.py -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Features CLI Exploration Handler (`P1.1`)

Implement `expml features explore` subparser and execution handler, saving `reports/exploratory_features.json` atomically with overwrite protection.

```
T1
```

### Phase 2: Features Scenarios Handler and Verification (`P1.2`)

Implement `expml features scenarios` and `expml features verify` subcommands, validating scenarios against sanitized view and enforcing stage gates.

```
T2
```

### Phase 3: Runtime Purity and End-to-End Pipeline Integration (`P1.3`)

Verify CLI runtime purity without NumPy/hashlib in clean processes, and prove end-to-end multi-stage pipeline reproducibility via subprocess integration tests.

```
T3
```

---

## Task Breakdown

### Phase 1: Features CLI Exploration Handler (`P1.1`)

#### T1: Implement `expml features explore` and dispatcher registration

**What**: In `src/experimental_ml/cli/main.py`, register `features` subparser with `explore`, `scenarios`, and `verify` subcommands. Create `src/experimental_ml/cli/cmd_features.py` implementing `handle_features_explore(args)`. Load `SanitizedDatasetView` using `reconstruct_sanitized_view`, call `explore_features`, write `reports/exploratory_features.json` using `write_json_atomic`, enforce `--force` protection, and print summary to stdout. Add unit tests in `tests/unit/cli/test_cmd_features.py`.
**Where**: `src/experimental_ml/cli/cmd_features.py`
**Depends on**: None
**Reuses**: `experimental_ml.stages`, `experimental_ml.features`, `experimental_ml.core.storage`
**Requirement**: FEAT-01, FEAT-02, FEAT-03

**Done when**:
- [x] `expml features --help` displays help with code 0
- [x] `expml features explore` runs exploratory analysis and writes report atomically
- [x] Overwrite is prevented unless `--force` is provided (raising `ConfigurationError` and exiting code 2)
- [x] Quick gate check passes: `.venv/bin/pytest tests/unit/cli/test_cmd_features.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(cli): implementar subcomando expml features explore (FEAT-01, FEAT-02, FEAT-03)`

---

### Phase 2: Features Scenarios Handler and Verification (`P1.2`)

#### T2: Implement `expml features scenarios` and `expml features verify`

**What**: In `src/experimental_ml/cli/cmd_features.py`, implement `handle_features_scenarios(args)` and `handle_features_verify(args)`. For `scenarios`: read scenario definitions JSON, validate against sanitized view via `validate_scenarios`, persist `configuration/scenarios.json` via `save_scenarios` with `--force` protection. For `verify`: call `verify_scenarios_gate(target, view)`. Ensure all domain errors exit with code 2 and formatted stderr message without traceback. Add unit tests in `tests/unit/cli/test_cmd_features.py`.
**Where**: `src/experimental_ml/cli/cmd_features.py`
**Depends on**: T1
**Reuses**: `experimental_ml.features.scenarios`, `experimental_ml.stages.stage_gates`
**Requirement**: FEAT-04, FEAT-05, FEAT-06

**Done when**:
- [ ] `expml features scenarios` validates and saves `configuration/scenarios.json`
- [ ] Invalid scenarios (e.g. unknown column, empty features) exit with code 2 and clean stderr message
- [ ] `expml features verify` passes for valid configuration and fails with code 2 on gate violations
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/cli/test_cmd_features.py -v`

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(cli): implementar subcomandos features scenarios e features verify (FEAT-04, FEAT-05, FEAT-06)`

---

### Phase 3: Runtime Purity and End-to-End Pipeline Integration (`P1.3`)

#### T3: Implement CLI-10 runtime purity tests and end-to-end integration suite

**What**: Add subprocess tests in `tests/unit/cli/test_cmd_features.py` verifying that invoking `expml` and `expml --help` in clean python processes does not import `numpy` or `hashlib` in `sys.modules` (`CLI-10`). Create `tests/integration/features/test_features_cli_integration.py` executing a full end-to-end pipeline through CLI subprocesses in an isolated temporary directory: `expml data profile` -> `expml data sanitize` -> `expml features explore` -> `expml features scenarios` -> `expml features verify` -> `expml partition build`.
**Where**: `tests/integration/features/test_features_cli_integration.py`
**Depends on**: T2
**Reuses**: `experimental_ml.cli`
**Requirement**: FEAT-07, FEAT-08

**Done when**:
- [ ] Clean subprocess verification proves `numpy` and `hashlib` are absent from `sys.modules` on help/version calls
- [ ] Full end-to-end multi-stage pipeline passes through CLI subprocesses with exit code 0
- [ ] Full test suite passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration  
**Gate**: full  
**Commit**: `test(cli): verificar pureza CLI-10 e homologar pipeline fim a fim da etapa 2 (FEAT-07, FEAT-08)`

---

## Checks

**C1** - `expml features --help` displays help for explore, scenarios, and verify subcommands and exits with code 0 (`FEAT-01`, AC 1)  
Proof: run unit | tests/unit/cli/test_cmd_features.py::test_feat_01_features_help PASSED

**C2** - `expml features explore` generates `reports/exploratory_features.json` with `EXPLORATORY_FULL_DATA` scope and exits code 0 (`FEAT-02`, AC 2)  
Proof: run unit | tests/unit/cli/test_cmd_features.py::test_feat_02_features_explore_success PASSED

**C3** - `expml features explore` without `--force` rejects overwriting existing reports with code 2 (`FEAT-03`, AC 3)  
Proof: run unit | tests/unit/cli/test_cmd_features.py::test_feat_03_features_explore_overwrite_protection PASSED

**C4** - `expml features scenarios` validates scenarios against schema and saves `configuration/scenarios.json` (`FEAT-04`, AC 4)  
Proof: run unit | tests/unit/cli/test_cmd_features.py::test_feat_04_features_scenarios_success PASSED

**C5** - `expml features scenarios` rejects invalid scenarios with code 2 and formatted stderr without traceback (`FEAT-05`, AC 5)  
Proof: run unit | tests/unit/cli/test_cmd_features.py::test_feat_05_features_scenarios_rejection PASSED

**C6** - `expml features verify` validates stage gate, exiting code 0 for valid and code 2 for invalid catalog (`FEAT-06`, AC 6)  
Proof: run unit | tests/unit/cli/test_cmd_features.py::test_feat_06_features_verify_gate PASSED

**C7** - Clean process invocation of `expml` does not import `numpy` or `hashlib` in `sys.modules` (`FEAT-07`, AC 7)  
Proof: run unit | tests/unit/cli/test_cmd_features.py::test_feat_07_cli_purity PASSED

**C8** - Full end-to-end pipeline through CLI subprocesses in isolated directory generates valid artifacts and passes with code 0 (`FEAT-08`, AC 8)  
Proof: run integration | tests/integration/features/test_features_cli_integration.py::test_feat_08_end_to_end_cli_pipeline PASSED

---

## Handoff

**Settled mid-build**: none  
**Dispatched**: none  
**Walked**: pending  

---

## Phase Execution Map

```
Phase 1 -> Phase 2 -> Phase 3

Phase 1:  T1
Phase 2:  T2
Phase 3:  T3
```

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1: Implement `expml features explore` and dispatcher registration | Subparser registration, explore handler, report saving | ✅ Granular |
| T2: Implement `expml features scenarios` and `expml features verify` | Scenarios handler, verify handler, validation & gates | ✅ Granular |
| T3: Implement CLI-10 runtime purity tests and end-to-end integration suite | Pureza de runtime, suite de integração fim a fim por subprocesso | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | Phase 1 root (`T1`) | ✅ Match |
| T2 | T1 | Phase 2 start after Phase 1 (`T2`) | ✅ Match |
| T3 | T2 | Phase 3 start after Phase 2 (`T3`) | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1: Implement `expml features explore` and dispatcher registration | Features CLI Exploration (`src/experimental_ml/cli/cmd_features.py`) | unit | unit | ✅ OK |
| T2: Implement `expml features scenarios` and `expml features verify` | Features CLI Scenarios & Gate (`src/experimental_ml/cli/cmd_features.py`) | unit | unit | ✅ OK |
| T3: Implement CLI-10 runtime purity tests and end-to-end integration suite | Runtime Purity & E2E Integration (`tests/integration/features/test_features_cli_integration.py`) | integration | integration | ✅ OK |
