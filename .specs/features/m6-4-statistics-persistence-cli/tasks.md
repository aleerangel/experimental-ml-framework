# m6-4-statistics-persistence-cli Tasks (M6.4 Persistência, Portão de Estágio e CLI)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m6-4-statistics-persistence-cli/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-16 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/statistics/ tests/unit/stages/test_stage_statistics_gate.py tests/unit/cli/test_cli_stats.py tests/integration/statistics/ -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Statistics Persistence (`src/experimental_ml/statistics/storage.py`) | unit | save_statistics_artifacts, load_statistics_artifacts, escrita atômica, no-overwrite, roundtrip NaN/Inf | `tests/unit/statistics/test_statistics_storage.py` | `.venv/bin/pytest tests/unit/statistics/test_statistics_storage.py -v` |
| Stage 5 Gate (`src/experimental_ml/stages/stage_gates.py`) | unit | verify_statistics_gate, bloqueio de arquivos ausentes/corrompidos, divergência partition_plan_id | `tests/unit/stages/test_stage_statistics_gate.py` | `.venv/bin/pytest tests/unit/stages/test_stage_statistics_gate.py -v` |
| CLI `expml stats` (`src/experimental_ml/cli/cmd_stats.py`) | unit | expml stats run/status/verify, exit codes 0/2, supressão de hashes, lazy imports CLI-10 | `tests/unit/cli/test_cli_stats.py` | `.venv/bin/pytest tests/unit/cli/test_cli_stats.py -v` |
| Integration & Purity (`tests/integration/statistics/test_m64_integration.py`) | integration | Fluxo CLI ponta a ponta Stage 4 -> Stage 5 -> verify_statistics_gate e pureza XCUT-02 | `tests/integration/statistics/test_m64_integration.py` | `.venv/bin/pytest tests/integration/statistics/test_m64_integration.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After unit tasks | `.venv/bin/pytest tests/unit/statistics/ tests/unit/stages/test_stage_statistics_gate.py tests/unit/cli/test_cli_stats.py -v` |
| Full | After integration task | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/unit/statistics/ -v` |

---

## Execution Plan

### Phase 1: Persistência Atômica (`P1`)

```
T1
```

### Phase 2: Portão de Estágio Stage 5 (`P2`)

```
T1 --> T2
```

### Phase 3: CLI `expml stats` (`P3`)

```
T2 --> T3
```

### Phase 4: API Pública e Integração Ponta a Ponta (`P4`)

```
T3 --> T4
```

---

## Task Breakdown

### Phase 1: Persistência Atômica

#### T1: Implementar save_statistics_artifacts e load_statistics_artifacts [x]

**What**: Criar `src/experimental_ml/statistics/storage.py` com codecs JSON tipados (preservando `NaN`/`Inf`/`-Inf` via marcadores RFC 8259, enums, chaves compostas e dataclasses congeladas), escrita atômica (`write_json_atomic`) e proteção `force=False`. Adicionar testes em `tests/unit/statistics/test_statistics_storage.py`.  
**Where**: `src/experimental_ml/statistics/storage.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/core/storage.py`, `src/experimental_ml/statistics/types.py`  
**Requirement**: STAT-12  
**Tests**: `tests/unit/statistics/test_statistics_storage.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_statistics_storage.py -v`

---

### Phase 2: Portão de Estágio Stage 5

#### T2: Implementar verify_statistics_gate [x]

**What**: Adicionar `verify_statistics_gate` em `src/experimental_ml/stages/stage_gates.py`, verificando portão upstream (`verify_runs_gate` quando `runs/` existe), existência/parseabilidade dos arquivos obrigatórios em `statistics/` e consistência de `partition_plan_id`. Adicionar testes em `tests/unit/stages/test_stage_statistics_gate.py`.  
**Where**: `src/experimental_ml/stages/stage_gates.py`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/statistics/storage.py`  
**Requirement**: STAT-13  
**Tests**: `tests/unit/stages/test_stage_statistics_gate.py`  
**Gate**: `.venv/bin/pytest tests/unit/stages/test_stage_statistics_gate.py -v`

---

### Phase 3: CLI `expml stats`

#### T3: Implementar cmd_stats e registrar subcomandos em cli/main.py [x]

**What**: Criar `src/experimental_ml/cli/cmd_stats.py` e registrar `expml stats run`, `status` e `verify` em `src/experimental_ml/cli/main.py` com lazy imports (`CLI-10`), códigos de saída `0`/`2` (`CLI-06`) e supressão de hashes brutos na saída (`CLI-11`). Adicionar testes em `tests/unit/cli/test_cli_stats.py`.  
**Where**: `src/experimental_ml/cli/cmd_stats.py`  
**Depends on**: T2  
**Reuses**: `src/experimental_ml/statistics/storage.py`, `src/experimental_ml/stages/stage_gates.py`  
**Requirement**: STAT-14  
**Tests**: `tests/unit/cli/test_cli_stats.py`  
**Gate**: `.venv/bin/pytest tests/unit/cli/test_cli_stats.py -v`

---

### Phase 4: API Pública e Integração Ponta a Ponta

#### T4: Expor persistência em __init__.py e validar integração ponta a ponta [x]

**What**: Exportar `LoadedStatisticsArtifacts`, `save_statistics_artifacts` e `load_statistics_artifacts` em `src/experimental_ml/statistics/__init__.py`. Criar `tests/integration/statistics/test_m64_integration.py` validando fluxo CLI completo Stage 4 -> `expml stats run` -> `expml stats verify` e pureza de runtime `XCUT-02`.  
**Where**: `src/experimental_ml/statistics/__init__.py`  
**Depends on**: T3  
**Reuses**: `src/experimental_ml/statistics/storage.py`, `src/experimental_ml/cli/main.py`  
**Requirement**: STAT-12, STAT-13, STAT-14  
**Tests**: `tests/integration/statistics/test_m64_integration.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/ tests/unit/stages/test_stage_statistics_gate.py tests/unit/cli/test_cli_stats.py tests/integration/statistics/ -v`

---

## Checks

**C1** - `save_statistics_artifacts` persiste atomicamente os arquivos obrigatórios e `pareto_summary.json` opcional em `statistics/`. (STAT-12, AC-M64-01-01)  
Proof: run unit | tests/unit/statistics/test_statistics_storage.py::test_m64_01_atomic_save_creates_all_files PASSED

**C2** - `save_statistics_artifacts` rejeita sobrescrita quando `force=False`. (STAT-12, AC-M64-01-02)  
Proof: run unit | tests/unit/statistics/test_statistics_storage.py::test_m64_01_no_overwrite_protection PASSED

**C3** - `load_statistics_artifacts` reconstrói todas as estruturas congeladas com fidelidade integral inclusive `NaN`/`Inf`. (STAT-12, AC-M64-01-03)  
Proof: run unit | tests/unit/statistics/test_statistics_storage.py::test_m64_01_roundtrip_fidelity_with_nonfinite PASSED

**C4** - `verify_statistics_gate` lança `DataIntegrityError` quando qualquer arquivo obrigatório está ausente ou corrompido. (STAT-13, AC-M64-02-01)  
Proof: run unit | tests/unit/stages/test_stage_statistics_gate.py::test_m64_02_missing_or_corrupt_raises PASSED

**C5** - `verify_statistics_gate` lança `DataIntegrityError` quando `partition_plan_id` diverge do upstream. (STAT-13, AC-M64-02-02)  
Proof: run unit | tests/unit/stages/test_stage_statistics_gate.py::test_m64_02_partition_plan_mismatch_raises PASSED

**C6** - `verify_statistics_gate` retorna dicionário resumo quando todos os portões upstream e Stage 5 estão íntegros. (STAT-13, AC-M64-02-03)  
Proof: run unit | tests/unit/stages/test_stage_statistics_gate.py::test_m64_02_valid_gate_returns_summary PASSED

**C7** - `expml stats run` executa Etapa 5 completa, persiste `statistics/` e retorna código 0 sem imprimir hashes brutos. (STAT-14, AC-M64-03-01)  
Proof: run unit | tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_run_success PASSED

**C8** - `expml stats status` exibe resumo somente-leitura e retorna 0 (ou 2 se ausente). (STAT-14, AC-M64-03-02)  
Proof: run unit | tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_status PASSED

**C9** - `expml stats verify` executa `verify_statistics_gate` retornando 0 ou 2 sem traceback em erro. (STAT-14, AC-M64-03-03)  
Proof: run unit | tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_verify PASSED

**C10** - `cli.main` e `cli.cmd_stats` mantêm imports pesados isolados no nível de módulo (`CLI-10`). (STAT-14, AC-M64-03-04)  
Proof: run unit | tests/unit/cli/test_cli_stats.py::test_m64_03_cli_lazy_imports_purity PASSED

**C11** - Fluxo integrado CLI Stage 4 -> `expml stats run` -> `expml stats verify`. (STAT-12)  
Proof: run unit | tests/integration/statistics/test_m64_integration.py::test_m64_cli_end_to_end_pipeline PASSED

**C12** - Persistência e CLI Stage 5 operam 100% sem `scipy` (`XCUT-02`). (XCUT-02)  
Proof: run unit | tests/integration/statistics/test_m64_integration.py::test_m64_runtime_purity_xcut02 PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T1
- **Next Task:** T2
