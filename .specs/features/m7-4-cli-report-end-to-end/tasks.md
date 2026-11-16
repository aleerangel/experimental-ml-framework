# m7-4-cli-report-end-to-end Tasks (M7.4 CLI `expml report` e Integração E2E)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m7-4-cli-report-end-to-end/design.md`  
**Status**: Completed  
**Approved**: 2026-11-16 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/cli/test_cli_report.py tests/integration/reporting/test_m74_e2e.py -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| CLI Handlers (`src/experimental_ml/cli/cmd_report.py`, `main.py`) | unit | `expml report generate`, `export`, `verify`, seleção de audiência/formato, proteção `--force`, códigos de saída `0`/`2` e detecção de 1 byte | `tests/unit/cli/test_cli_report.py` | `.venv/bin/pytest tests/unit/cli/test_cli_report.py -v` |
| End-to-End Stage 1–6 (`tests/integration/reporting/test_m74_e2e.py`) | integration | Fluxo CLI/API completo Estágio 1 (`data`) → Estágio 6 (`report export` + movimentação + `report verify`) e pureza `XCUT-02` | `tests/integration/reporting/test_m74_e2e.py` | `.venv/bin/pytest tests/integration/reporting/test_m74_e2e.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After unit task | `.venv/bin/pytest tests/unit/cli/test_cli_report.py -v` |
| Full | After integration task | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/unit/cli/test_cli_report.py tests/integration/reporting/test_m74_e2e.py -v` |

---

## Execution Plan

### Phase 1: Subcomandos CLI `expml report` (`P1`)

```
T1
```

### Phase 2: Integração Ponta a Ponta Estágio 1–6 (`P2`)

```
T1 --> T2
```

---

## Task Breakdown

### Phase 1: Subcomandos CLI `expml report`

#### T1: Implementar `cmd_report.py` e registrar `expml report {generate, export, verify}` em `cli/main.py` [x]

**What**: Criar `src/experimental_ml/cli/cmd_report.py` com `handle_report_generate`, `handle_report_export` e `handle_report_verify`, e registrar o grupo `report` (`generate`, `export`, `verify`) em `src/experimental_ml/cli/main.py` seguindo `CLI-10` (imports lazy), `CLI-11` (sem hashes brutos no stdout), proteção `--force` (`STORE-05`) e códigos de saída `0`/`2`. Adicionar testes em `tests/unit/cli/test_cli_report.py`.  
**Where**: `src/experimental_ml/cli/cmd_report.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/reporting/`, `src/experimental_ml/stages/stage_gates.py` (`verify_report_gate`)  
**Requirement**: REP-08, REP-09  
**Tests**: `tests/unit/cli/test_cli_report.py`  
**Gate**: `.venv/bin/pytest tests/unit/cli/test_cli_report.py -v`

---

### Phase 2: Integração Ponta a Ponta Estágio 1–6

#### T2: Validar fluxo completo Estágio 1 -> Estágio 6 e pureza XCUT-02 [x]

**What**: Criar `tests/integration/reporting/test_m74_e2e.py` executando um experimento sintético completo desde a Etapa 1 (dados) até a Etapa 6 (`expml report export`, movimentação do diretório do pacote, `expml report verify` e detecção de adulteração de 1 byte), validando conformidade `XCUT-02` e `CA-E6-01`/`CA-E6-02`.  
**Where**: `tests/integration/reporting/test_m74_e2e.py`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/cli/main.py`, `src/experimental_ml/reporting/`  
**Requirement**: REP-08, REP-09  
**Tests**: `tests/integration/reporting/test_m74_e2e.py`  
**Gate**: `.venv/bin/pytest tests/unit/cli/test_cli_report.py tests/integration/reporting/test_m74_e2e.py -v`

---

## Checks

**C1** - `expml report generate` gera `report.md` e/ou `report.html` em modo somente-leitura com código `0` e resumo JSON. (REP-08, AC-M74-01-01)  
Proof: run unit | tests/unit/cli/test_cli_report.py::test_m74_01_cli_report_generate PASSED

**C2** - `expml report export` exporta pacote completo nos modos `full_package` e `reduced_no_raw_data` com código `0` e manifesto JSON. (REP-08, AC-M74-01-02)  
Proof: run unit | tests/unit/cli/test_cli_report.py::test_m74_01_cli_report_export_modes PASSED

**C3** - `expml report generate` e `export` sem `--force` retornam código `2` (`ContractViolationError`) sem sobrescrever arquivos existentes. (REP-08, AC-M74-01-03)  
Proof: run unit | tests/unit/cli/test_cli_report.py::test_m74_01_cli_force_protection PASSED

**C4** - `expml report verify` retorna código `0` e `"status": "VERIFIED"` mesmo após mover o diretório do pacote. (REP-09, AC-M74-02-01)  
Proof: run unit | tests/unit/cli/test_cli_report.py::test_m74_02_cli_report_verify_portable PASSED

**C5** - `expml report verify` retorna código `2` (`DataIntegrityError`) em adulteração de 1 byte, arquivo ausente ou caminho não relativo. (REP-09, AC-M74-02-02)  
Proof: run unit | tests/unit/cli/test_cli_report.py::test_m74_02_cli_report_verify_tamper_fails PASSED

**C6** - Fluxo E2E completo Estágio 1 → Estágio 6 via CLI/API aprovado com pureza `XCUT-02`. (REP-09, AC-M74-02-03)  
Proof: run unit | tests/integration/reporting/test_m74_e2e.py::test_m74_e2e_stage1_to_stage6_cli PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T1
- **Next Task:** T2
