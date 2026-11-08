# m2-5-cli-end-to-end Tasks (M2.5 CLI data & partition and End-to-End Acceptance)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m2-5-cli-end-to-end/design.md`
**Status**: Approved
**Approved**: 2026-11-07 - user: "aprovado"
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates
**Run unit**: .venv/bin/pytest tests/unit/cli/ -v
**Run integration**: .venv/bin/pytest tests/integration/test_cli_end_to_end_integration.py -v

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specs/STATE.md` (`AD-001`, `AD-002`, `AD-003`), `ARQUITETURA_E_CONTRATOS.md`; strong defaults applied across all 12 requirements (`CLI-01` to `CLI-12`) and transversal invariants.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| CLI Main Dispatcher & Error Infrastructure (`src/experimental_ml/cli/main.py`) | unit | 1:1 AC mapping: exit codes 0/1/2, traceback suppression, M1.1 base compatibility, no numpy/hashlib imports, no hashes printed | `tests/unit/cli/test_cli_main.py` | `.venv/bin/pytest tests/unit/cli/test_cli_main.py -v` |
| Data CLI Commands (`src/experimental_ml/cli/cmd_data.py`) | unit | 1:1 AC mapping: data profile output, data sanitize READY vs INCOMPLETE plan rejection, overwrite protection | `tests/unit/cli/test_cmd_data.py` | `.venv/bin/pytest tests/unit/cli/test_cmd_data.py -v` |
| Partition CLI Commands (`src/experimental_ml/cli/cmd_partition.py`) | unit | 1:1 AC mapping: partition build output, seed override, partition verify clean & tampered detection, upstream blockers | `tests/unit/cli/test_cmd_partition.py` | `.venv/bin/pytest tests/unit/cli/test_cmd_partition.py -v` |
| End-to-End Subprocess Integration (`tests/integration/test_cli_end_to_end_integration.py`) | integration | Full subprocess lifecycle via installed `expml`, bit-identical byte equivalence across independent directories | `tests/integration/test_cli_end_to_end_integration.py` | `.venv/bin/pytest tests/integration/test_cli_end_to_end_integration.py -v` |

---

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After tasks with unit tests | `.venv/bin/pytest tests/unit/cli/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: CLI Dispatcher & Error Infrastructure (`P1.1`)

Implement hierarchical argument parsing, error trapping with traceback suppression, and M1.1 baseline compatibility.

```
T1
```

### Phase 2: Data & Partition Subcommands (`P1.2`)

Implement `data profile`, `data sanitize`, `partition build`, and `partition verify` with diagnostic summaries, seed override, and stage gate validation.

```
T2 → T3
```

### Phase 3: End-to-End Subprocess Integration Suite (`P1.3`)

Implement the formal acceptance scenario executing the complete pipeline via installed `expml` entrypoint in separate directories.

```
T4
```

---

## Task Breakdown

### Phase 1: CLI Dispatcher & Error Infrastructure (`P1.1`)

#### T1: Implement hierarchical parser, error trapping, and base compatibility in `cli/main.py`

**What**: Update `src/experimental_ml/cli/main.py` defining subparsers for `data` (`profile`, `sanitize`) and `partition` (`build`, `verify`). Implement exception handling in `main`: catch `argparse.ArgumentError`, `ExperimentalMLError` (and subclasses) and print instructive error message `Error: {msg}` to stderr without traceback, exiting with code 2 (CLI-06). Catch unexpected exceptions and exit with code 1. Preserve M1.1 behavior: `--version` and no arguments exit with code 0 (CLI-09). Ensure `cli/main.py` imports neither `numpy` nor `hashlib` (CLI-10) and prints no hashes (CLI-11). Add co-located unit tests in `tests/unit/cli/test_cli_main.py`.
**Where**: `src/experimental_ml/cli/main.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/core/findings.py`
**Requirement**: CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11

**Done when**:
- [ ] Base `expml` commands (`--version`, `--help`, empty arguments) exit with code 0
- [ ] Subcommand parsers for `data` and `partition` configured with `--help`
- [ ] Domain errors print message without traceback and exit with code 2
- [ ] No `numpy` or `hashlib` imported in `cli/main.py`
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/cli/test_cli_main.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(cli): despachante hierarquico e tratamento robusto de erros`

---

### Phase 2: Data & Partition Subcommands (`P1.2`)

#### T2: Implement `data profile` and `data sanitize` handlers in `cli/cmd_data.py`

**What**: Create `src/experimental_ml/cli/cmd_data.py` implementing `handle_data_profile` and `handle_data_sanitize`. `handle_data_profile` loads dataset with schema, runs `profile_dataset`, saves `data/dataset_descriptor.json` and `data/dataset_profile.json` with `overwrite=args.force`, prints dimensions and findings without hashes, and exits with code 0 (CLI-01). `handle_data_sanitize` loads profile and rules JSON, runs `create_preparation_plan`; if `INCOMPLETE`, prints unresolved confirmed issues with code and column, does NOT save plan, and exits with code 2 (CLI-03); if `READY`, runs `sanitize_dataset`, saves `configuration/preparation_plan.json` and `data/sanitized_view.json`, prints summary, and exits with code 0 (CLI-02). Add unit tests in `tests/unit/cli/test_cmd_data.py`.
**Where**: `src/experimental_ml/cli/cmd_data.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/core/storage.py`, `src/experimental_ml/data/`
**Requirement**: CLI-01, CLI-02, CLI-03, CLI-08, CLI-10, CLI-11

**Done when**:
- [ ] `data profile` writes descriptor and profile, printing readable summary
- [ ] `data sanitize` writes preparation plan and sanitized view when plan is READY
- [ ] `data sanitize` rejects INCOMPLETE plans with exit code 2 and prints pending findings
- [ ] Existing output artifacts without `--force` raise ConfigurationError and exit with code 2
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/cli/test_cmd_data.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(cli): subcomandos de perfilamento e saneamento de dados`

---

#### T3: Implement `partition build` and `partition verify` handlers in `cli/cmd_partition.py`

**What**: Create `src/experimental_ml/cli/cmd_partition.py` implementing `handle_partition_build` and `handle_partition_verify`. `handle_partition_build` validates upstream preparation gate via `verify_preparation_gate` (CLI-07), applies optional `--seed` override, reconstructs sanitized view, builds partition plan, and writes `partitions/partition_plan.json`, `partitions/splits.csv.gz`, and `partitions/splits.schema.json` with `overwrite=args.force`, printing fold summary and exiting with code 0 (CLI-04). `handle_partition_verify` executes `verify_partition_gate` and `validate_partition_plan`, exiting with code 0 when all invariants hold or code 2 when tampered (CLI-05). Add unit tests in `tests/unit/cli/test_cmd_partition.py`.
**Where**: `src/experimental_ml/cli/cmd_partition.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/validation/`, `src/experimental_ml/stages/stage_gates.py`
**Requirement**: CLI-04, CLI-05, CLI-07, CLI-08, CLI-10, CLI-11

**Done when**:
- [ ] `partition build` validates upstream gate, writes partition artifacts, and prints fold sizes
- [ ] `--seed` CLI argument overrides `master_seed` in partition config
- [ ] `partition verify` exits with code 0 on valid artifacts and code 2 on tampered artifacts
- [ ] Upstream missing artifacts block execution with code 2
- [ ] Quick gate check passes: `.venv/bin/pytest tests/unit/cli/test_cmd_partition.py -v`

**Tests**: unit
**Gate**: quick
**Commit**: `feat(cli): subcomandos de construcao e verificacao de particoes`

---

### Phase 3: End-to-End Subprocess Integration Suite (`P1.3`)

#### T4: Implement end-to-end acceptance integration suite via `expml` subprocess

**What**: Create `tests/integration/test_cli_end_to_end_integration.py` executing the complete sequence (`data profile` -> `data sanitize` -> `partition build` -> `partition verify`) through the installed `expml` CLI executable in two separate independent directories. Verify exit code 0 at every step, bit-identical bytes for `partitions/partition_plan.json`, identical decompressed content for `partitions/splits.csv.gz` (CLI-12), and verify architectural import isolation (CLI-10).
**Where**: `tests/integration/test_cli_end_to_end_integration.py`
**Depends on**: T3
**Reuses**: CLI entrypoint, all modules
**Requirement**: CLI-10, CLI-11, CLI-12

**Done when**:
- [ ] Subprocess execution of the full sequence completes with exit code 0 at each step
- [ ] Identical `partition_plan.json` bytes produced across the two independent directories
- [ ] Identical decompressed `splits.csv.gz` content verified across the two independent directories
- [ ] AST check verifies zero imports of `numpy` or `hashlib` in `experimental_ml.cli`
- [ ] Full gate check passes: `.venv/bin/pytest tests/ -v`

**Tests**: integration
**Gate**: full
**Commit**: `feat(cli): suite de aceite ponta a ponta e homologacao da CLI`

---

## Checks

The checks below verify every acceptance criterion (`CLI-01` to `CLI-12`). Each check settles an observable claim against its exact proof.

**C1** - `expml data profile --data PATH --schema SCHEMA.json --output-dir DIR` writes `dataset_descriptor.json` and `dataset_profile.json`, prints dimensions and findings, exits code 0 (`CLI-01`, AC 1)
Proof: run unit | tests/unit/cli/test_cmd_data.py::test_cli_01_data_profile_success PASSED

**C2** - `expml data sanitize --experiment-dir DIR --rules RULES.json` writes `preparation_plan.json` and `data/sanitized_view.json`, prints summary, exits code 0 when plan is READY (`CLI-02`, AC 2)
Proof: run unit | tests/unit/cli/test_cmd_data.py::test_cli_02_data_sanitize_ready_plan PASSED

**C3** - `expml data sanitize` prints unresolved confirmed findings and exits code 2 without writing preparation_plan.json when plan is INCOMPLETE (`CLI-03`, AC 3)
Proof: run unit | tests/unit/cli/test_cmd_data.py::test_cli_03_data_sanitize_incomplete_plan_rejected PASSED

**C4** - `expml partition build --experiment-dir DIR --config CONFIG.json [--seed N]` writes `partition_plan.json`, `splits.csv.gz` and `splits.schema.json`, prints regime, strategy, per-fold sizes, exits code 0 (`CLI-04`, AC 4)
Proof: run unit | tests/unit/cli/test_cmd_partition.py::test_cli_04_partition_build_success PASSED

**C5** - `expml partition verify --experiment-dir DIR` validates stage gates and invariants, exits code 0 on valid artifacts and code 2 on tampered artifacts (`CLI-05`, AC 5)
Proof: run unit | tests/unit/cli/test_cmd_partition.py::test_cli_05_partition_verify_clean_and_tampered PASSED

**C6** - CLI catches domain errors, missing upstream artifacts, or existing files without `--force`, printing an instructive message without traceback and exiting code 2 (`CLI-06`, `CLI-07`, `CLI-08`, AC 6, AC 7, AC 8)
Proof: run unit | tests/unit/cli/test_cli_main.py::test_cli_06_domain_error_handling_and_exit_code_2 PASSED

**C7** - CLI preserves M1.1 base behaviors: `--version` and no arguments exit code 0, invalid options exit code 2, every subcommand exposes `--help` (`CLI-09`, AC 9)
Proof: run unit | tests/unit/cli/test_cli_main.py::test_cli_09_base_cli_compatibility_and_help PASSED

**C8** - Modules under `experimental_ml.cli` contain no numerical or business logic, importing neither `numpy` nor `hashlib` (`CLI-10`, AC 10)
Proof: run unit | tests/unit/cli/test_cli_main.py::test_cli_10_architectural_pure_cli_no_numpy_no_hashlib PASSED

**C9** - Subcommands never print a hash digest in stdout or stderr (`CLI-11`, AC 11)
Proof: run unit | tests/unit/cli/test_cli_main.py::test_cli_11_no_hash_digests_in_output PASSED

**C10** - Complete sequence (`profile` -> `sanitize` -> `partition build` -> `partition verify`) run via subprocess on installed `expml` in two independent directories produces identical `partition_plan.json` bytes and identical `splits.csv.gz` content (`CLI-12`, AC 12)
Proof: run integration | tests/integration/test_cli_end_to_end_integration.py::test_cli_12_end_to_end_subprocess_acceptance_scenario PASSED

---

## Handoff

**Settled mid-build**: none
**Dispatched**: none
**Walked**: pending Execute phase
