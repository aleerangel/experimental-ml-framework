# m5-4-cli-run-end-to-end Tasks (M5.4 CLI Run End-to-End)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m5-4-cli-run-end-to-end/design.md`  
**Status**: approved  
**Approved**: 2026-11-12 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/cli/test_cli_run.py -v  
**Run integration**: .venv/bin/pytest tests/integration/cli/test_run_e2e.py -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| CLI Parser & Subcommands (`src/experimental_ml/cli/main.py`) | unit | 1:1 AC mapping: subparser `run` com `start`, `resume`, `status`, `verify`, `--help` e parsing de flags | `tests/unit/cli/test_cli_run.py` | `.venv/bin/pytest tests/unit/cli/test_cli_run.py -v -k "parsing or help"` |
| Subcomando Run Start (`src/experimental_ml/cli/cmd_run.py`) | unit | 1:1 AC mapping: reconstituição de insumos, execução matricial, `-j`, `--error-policy`, `--no-oof`, `--force` | `tests/unit/cli/test_cli_run.py` | `.venv/bin/pytest tests/unit/cli/test_cli_run.py -v -k "run_start"` |
| Subcomandos Resume & Status (`src/experimental_ml/cli/cmd_run.py`) | unit | 1:1 AC mapping: retomada incremental, `--retry-failed`, leitura somente-leitura de status e percentual | `tests/unit/cli/test_cli_run.py` | `.venv/bin/pytest tests/unit/cli/test_cli_run.py -v -k "run_resume or run_status"` |
| Subcomando Verify & Error Handling (`src/experimental_ml/cli/cmd_run.py`) | unit | 1:1 AC mapping: auditoria via verify_runs_gate, código 2 sem traceback em erros de domínio, supressão de hash | `tests/unit/cli/test_cli_run.py` | `.venv/bin/pytest tests/unit/cli/test_cli_run.py -v -k "run_verify or domain_errors or hash"` |
| Transversal Integration (`tests/integration/cli/test_run_e2e.py`) | integration | Ciclo ponta a ponta da CLI (etapas 1 a 4B), recuperação após crash, pureza de runtime (XCUT-02, CLI-10) | `tests/integration/cli/test_run_e2e.py` | `.venv/bin/pytest tests/integration/cli/test_run_e2e.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After tasks with unit tests in cli | `.venv/bin/pytest tests/unit/cli/test_cli_run.py -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Registro Modular e Estrutura da CLI (`P1`)

Registrar o subparser `run` em `src/experimental_ml/cli/main.py` com `start`, `resume`, `status` e `verify`, e inicializar `cmd_run.py`.

```
T1
```

### Phase 2: Execução de Matriz Experimental via CLI (`P2`)

Implementar o manipulador `handle_run_start` em `src/experimental_ml/cli/cmd_run.py` com validação de portões upstream, reconstituição de insumos e execução matricial.

```
T1 --> T2
```

### Phase 3: Retomada Incremental e Inspeção Somente-Leitura (`P3`)

Implementar `handle_run_resume` e `handle_run_status` em `src/experimental_ml/cli/cmd_run.py`.

```
T2 --> T3
```

### Phase 4: Portão de Estágio e Tratamento de Erros da CLI (`P4`)

Implementar `handle_run_verify` em `src/experimental_ml/cli/cmd_run.py`, padronização de códigos de saída (0, 1, 2) e supressão de hashes.

```
T3 --> T4
```

### Phase 5: Integração Transversal e Pureza de Runtime (`P5`)

Implementar a suíte de integração transversal `tests/integration/cli/test_run_e2e.py` com ciclo ponta a ponta e teste em subprocesso isolado (`XCUT-02`).

```
T4 --> T5
```

---

## Task Breakdown

### Phase 1: Registro Modular e Estrutura da CLI

#### T1: Registrar Subparsers de expml run em cli/main.py

**What**: Adicionar o subparser `run` em `src/experimental_ml/cli/main.py` com os subcomandos `start`, `resume`, `status` e `verify`. Configurar todos os argumentos requeridos e opcionais (`--experiment-dir`, `--run-dir`, `-j`/`--jobs`/`--parallel`, `--error-policy`, `--no-oof`, `--retry-failed` e `--force`). Implementar o roteamento lazy para `experimental_ml.cli.cmd_run` preservando estritamente a diretriz `CLI-10` (zero importações pesadas no escopo do módulo `main.py`). Criar `tests/unit/cli/test_cli_run.py` validando parsing, telas de ajuda e argumentos inválidos.  
**Where**: `src/experimental_ml/cli/main.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/cli/main.py`  
**Requirement**: ORCH-22  

**Done when**:
- [x] Subparser `run` registrado com subcomandos `start`, `resume`, `status` e `verify`
- [x] Argumentos configurados conforme especificação
- [x] Módulo `cmd_run.py` criado com stubs dos manipuladores
- [x] `expml run --help` exibe a ajuda dos subcomandos com código de saída 0
- [x] Testes unitários de parser passam em `tests/unit/cli/test_cli_run.py`
- [x] Gate rápido aprovado

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(cli): registrar subparsers modulares para expml run (ORCH-22)`

---

### Phase 2: Execução de Matriz Experimental via CLI

#### T2: Implementar Subcomando expml run start

**What**: Implementar `handle_run_start` em `src/experimental_ml/cli/cmd_run.py`. Validar a existência de `experiment_dir`, verificar os portões upstream (`verify_preparation_gate`, `verify_partition_gate`, `verify_scenarios_gate`, `verify_models_gate`), reconstituir os insumos (`reconstruct_sanitized_view`, partições, cenários, modelos), verificar a proteção contra sobrescrita indevida com `--force`, despachar a execução matricial (`run_experiment_matrix`) com controle de workers (`-j`/`--parallel`), política de erro (`--error-policy`) e consolidação OOF automática (respeitando `--no-oof`). Formatar e emitir resumo descritivo sem hashes para `sys.stdout`. Adicionar testes unitários em `tests/unit/cli/test_cli_run.py`.  
**Where**: `src/experimental_ml/cli/cmd_run.py`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/orchestration/engine.py`, `src/experimental_ml/stages/stage_gates.py`  
**Requirement**: ORCH-23  

**Done when**:
- [ ] `handle_run_start` valida pré-requisitos upstream das etapas 1 a 4A
- [ ] Reconstitui insumos e executa matriz experimental
- [ ] Grava em `<experiment-dir>/runs` ou `--run-dir` customizado
- [ ] Suporta `-j` / `--parallel` e `--error-policy`
- [ ] Consolidada OOF por padrão e omite com `--no-oof`
- [ ] Protege contra sobrescrita sem `--force` retornando código 2
- [ ] Testes unitários passam em `tests/unit/cli/test_cli_run.py`
- [ ] Gate rápido aprovado

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(cli): implementar subcomando expml run start com matriz e OOF (ORCH-23)`

---

### Phase 3: Retomada Incremental e Inspeção Somente-Leitura

#### T3: Implementar Subcomandos expml run resume e expml run status

**What**: Implementar `handle_run_resume` e `handle_run_status` em `src/experimental_ml/cli/cmd_run.py`. Em `resume`, validar a existência de `execution_state.json` em `run_dir`, reconstituir insumos e invocar `resume_experiment_matrix` pulando células concluídas e reexecutando pendentes/ausentes, com suporte a reexecução opcional de células que falharam via `--retry-failed`. Em `status`, realizar leitura puramente não-destrutiva de `execution_state.json`, computar percentuais de progresso e imprimir resumo claro sem modificar o disco. Adicionar testes unitários em `tests/unit/cli/test_cli_run.py`.  
**Where**: `src/experimental_ml/cli/cmd_run.py`  
**Depends on**: T2  
**Reuses**: `src/experimental_ml/orchestration/engine.py`, `src/experimental_ml/orchestration/state.py`  
**Requirement**: ORCH-24, ORCH-25  

**Done when**:
- [ ] `handle_run_resume` retoma execução incremental ignorando células prontas
- [ ] Flag `--retry-failed` reexecuta células falhas
- [ ] `handle_run_status` é puramente somente-leitura e exibe progresso percentual
- [ ] Falta de `execution_state.json` retorna código de saída 2 sem traceback
- [ ] Testes unitários passam em `tests/unit/cli/test_cli_run.py`
- [ ] Gate rápido aprovado

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(cli): implementar subcomandos expml run resume e status (ORCH-24, ORCH-25)`

---

### Phase 4: Portão de Estágio e Tratamento de Erros da CLI

#### T4: Implementar Subcomando expml run verify e Padronização de Erros

**What**: Implementar `handle_run_verify` em `src/experimental_ml/cli/cmd_run.py`. Invocar `verify_runs_gate(run_dir)` para validar a integridade física de células, OOF e coerência de hashes da etapa 4, emitindo resumo de conformidade com status `READY`. Assegurar que todas as exceções de domínio (`ExperimentalMLError` e subclasses) e `ValueError` sejam impressas no formato `Error: <msg>` em `sys.stderr` sem traceback, encerrando com código 2 (`CLI-06`), e garantir supressão total de hashes criptográficos na saída (`CLI-11`). Adicionar testes unitários em `tests/unit/cli/test_cli_run.py`.  
**Where**: `src/experimental_ml/cli/cmd_run.py`  
**Depends on**: T3  
**Reuses**: `src/experimental_ml/stages/stage_gates.py`  
**Requirement**: ORCH-26, ORCH-27  

**Done when**:
- [ ] `handle_run_verify` audita execução via `verify_runs_gate` e confirma status `READY`
- [ ] Falhas de portão retornam código de saída 2 sem traceback
- [ ] Hashes criptográficos suprimidos da saída padrão do terminal
- [ ] Testes unitários passam em `tests/unit/cli/test_cli_run.py`
- [ ] Gate rápido aprovado

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(cli): implementar expml run verify e padronizacao de erros (ORCH-26, ORCH-27)`

---

### Phase 5: Integração Transversal e Pureza de Runtime

#### T5: Implementar Suite de Integracao Transversal e Validacao XCUT-02

**What**: Criar a suíte de testes de integração transversal em `tests/integration/cli/test_run_e2e.py`. Executar o ciclo operacional completo via CLI (`data profile` -> `data sanitize` -> `partition build` -> `features scenarios` -> `models validate` -> `expml run start` -> `expml run status` -> `expml run resume` -> `expml run verify`). Testar retomada após interrupção/falha simulada. Testar a pureza estrita de runtime em subprocesso isolado, garantindo que nenhum framework proibido (`scipy`, `pandas`, `sklearn`, `torch`, etc.) seja importado (`XCUT-02`) e que `main.py` e `cmd_run.py` tenham zero importações pesadas no escopo do módulo (`CLI-10`).  
**Where**: `tests/integration/cli/test_run_e2e.py`  
**Depends on**: T4  
**Reuses**: `src/experimental_ml/cli/`  
**Requirement**: ORCH-28  

**Done when**:
- [ ] Ciclo ponta a ponta da CLI (etapas 1 a 4B) executa e conclui com sucesso
- [ ] Teste de retomada e checkpoint via CLI valida recuperação transparente
- [ ] Teste de pureza comprova conformidade total com `XCUT-02` e `CLI-10`
- [ ] Todos os testes passam na suíte global
- [ ] Gate rápido aprovado

**Tests**: integration  
**Gate**: quick  
**Commit**: `test(cli): implementar suite de integracao transversal ponta a ponta expml run (ORCH-28)`

---

## Checks

**C1** - Ponto de entrada da CLI expoe comando run e subcomandos com --help (ORCH-22, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_01_01_cli_run_help_and_subparsers PASSED

**C2** - Subparser run start valida argumentos obrigatorios e opcionais (ORCH-22, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_01_02_run_start_args_parsing PASSED

**C3** - Subparser run resume valida argumentos obrigatorios e opcionais (ORCH-22, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_01_03_run_resume_args_parsing PASSED

**C4** - Subparser run status valida argumentos obrigatorios (ORCH-22, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_01_04_run_status_args_parsing PASSED

**C5** - Subparser run verify valida argumentos obrigatorios (ORCH-22, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_01_05_run_verify_args_parsing PASSED

**C6** - expml run start executa matriz completa e consolida OOF em runs (ORCH-23, AC 1, AC 5)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_02_01_run_start_default_execution PASSED

**C7** - expml run start com --run-dir customizado grava artefatos no diretorio indicado (ORCH-23, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_02_02_run_start_custom_run_dir PASSED

**C8** - expml run start com -j N despacha execucao em paralelo (ORCH-23, AC 3)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_02_03_run_start_parallel_dispatch PASSED

**C9** - expml run start com --error-policy fail_fast interrompe apos primeira falha (ORCH-23, AC 4)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_02_04_run_start_fail_fast PASSED

**C10** - expml run start com --no-oof desativa consolidacao out-of-fold (ORCH-23, AC 6)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_02_05_run_start_no_oof PASSED

**C11** - expml run start recusa sobrescrita de execucao existente sem --force (ORCH-23, AC 7)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_02_06_run_start_overwrite_protection PASSED

**C12** - expml run resume pula celulas concluidas e reexecuta pendentes (ORCH-24, AC 1)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_03_01_run_resume_skips_completed PASSED

**C13** - expml run resume com --retry-failed reexecuta celulas falhas (ORCH-24, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_03_02_run_resume_retry_failed PASSED

**C14** - expml run status realiza leitura puramente somente-leitura e exibe progresso (ORCH-25, AC 1)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_03_03_run_status_read_only PASSED

**C15** - expml run status com diretorio invalido ou sem estado retorna codigo 2 (ORCH-25, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_03_04_run_status_missing_state_returns_2 PASSED

**C16** - expml run verify audita execucao e retorna status READY com codigo 0 (ORCH-26, AC 1)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_04_01_run_verify_valid_gate PASSED

**C17** - expml run verify com execucao incompleta ou corrompida retorna codigo 2 (ORCH-26, AC 2)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_04_02_run_verify_corrupted_gate_returns_2 PASSED

**C18** - Erros de dominio e precondicoes sao emitidos sem traceback com codigo 2 (ORCH-27, AC 1)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_04_03_domain_errors_exit_code_2_no_traceback PASSED

**C19** - Resumos da CLI emitem textos limpos com supressao de hashes criptograficos (ORCH-27, AC 4)  
Proof: run unit | tests/unit/cli/test_cli_run.py::test_m54_04_04_hash_suppression_cli_11 PASSED

**C20** - Ciclo ponta a ponta da CLI executa etapas 1 a 4B com sucesso (ORCH-28, AC 5)  
Proof: run integration | tests/integration/cli/test_run_e2e.py::test_m54_05_01_e2e_cli_pipeline_lifecycle PASSED

**C21** - Ciclo de recuperacao via expml run resume recupera execucao interrompida (ORCH-28, AC 5)  
Proof: run integration | tests/integration/cli/test_run_e2e.py::test_m54_05_02_e2e_cli_crash_recovery PASSED

**C22** - Pureza estrita de runtime: apenas biblioteca padrao e numpy>=1.24.0 (XCUT-02, CLI-10)  
Proof: run integration | tests/integration/cli/test_run_e2e.py::test_m54_05_03_cli_runtime_purity_xcut_02 PASSED

---

## Handoff

- **Dispatched:** none
- **Completed:** none
- **In-progress:** T1
- **Next step:** Implement T1 (subparsers in main.py, stub in cmd_run.py)
- **Blockers:** none
