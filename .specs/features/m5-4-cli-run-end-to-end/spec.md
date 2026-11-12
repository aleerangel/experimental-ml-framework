# m5-4-cli-run-end-to-end Specification

**Status**: approved  
**Approved**: 2026-11-12 - user: "aprovado"  
**Coverage**: 100%  
**Requirements**: ORCH-22 to ORCH-28  
**Scope**: Subcomandos da CLI `expml run` (`start`, `resume`, `status`, `verify`), integração com o motor matricial e consolidação OOF, tratamento padronizado de erros e códigos de saída, supressão de hashes criptográficos na saída e testes de ciclo de vida transversal ponta a ponta.

---

## Problem Statement

O Marco M5 desenvolveu os contratos unitários de célula (M5.1), o motor matricial de grande porte com paralelismo e retomada (M5.2) e a consolidação out-of-fold com estatísticas de comitê e portão da Etapa 4 (M5.3). No entanto, o usuário e os scripts de automação ainda não dispõem de uma interface de linha de comando (`expml run`) para disparar execuções completas, inspecionar estados sem alterar o disco, retomar execuções de forma transparente e auditar portões de estágio pelo terminal. Sem essa interface, a Etapa 4 não pode ser acionada como parte do pipeline operacional agnóstico definido na arquitetura.

---

## Goals

1. Implementar o módulo `src/experimental_ml/cli/cmd_run.py` fornecendo os manipuladores para `start`, `resume`, `status` e `verify`.
2. Registrar modularmente os subparsers de `run` em `src/experimental_ml/cli/main.py`.
3. Permitir que `expml run start` carregue os artefatos das etapas 1 a 4A (`SanitizedDatasetView`, `PartitionPlan`, `ScenariosCatalog`, `ModelsCatalog`), valide os portões upstream e execute a matriz com consolidação OOF automática.
4. Suportar opções completas de execução: `-j`/`--parallel`, `--error-policy`, `--no-oof`, `--retry-failed` e `--force`.
5. Fornecer `expml run resume` para retomada incremental transparente e `expml run status` para inspeção puramente somente-leitura.
6. Fornecer `expml run verify` para validação formal de integridade via `verify_runs_gate`.
7. Assegurar conformidade com todas as diretrizes de CLI: `CLI-06` (códigos de saída 0, 1, 2 e sem traceback em erros de domínio), `CLI-07` (subparsers modulares), `CLI-08` (proteção de sobrescrita), `CLI-09` (ajuda e versão), `CLI-10` (zero imports pesados em nível de módulo), `CLI-11` (supressão de hashes brutos na saída) e `XCUT-02` (pureza de runtime com `numpy>=1.24.0` e standard library apenas).

---

## Out of Scope

- Subcomandos de análise estatística e ranqueamento (`expml stats`) — escopo do Marco M6.
- Subcomandos de publicação e geração de relatórios (`expml report`) — escopo do Marco M7.
- Dependência de frameworks pesados de linha de comando (`click`, `typer`) — mantido em `argparse` puro da biblioteca padrão.

---

## Assumptions & Open Questions

- **Diretório Padrão de Execução**: O destino padrão de `expml run start` é `<experiment-dir>/runs` (onde ficam `execution_state.json`, `cells/`, `predictions/`, `oof/`), permitindo customização com `--run-dir`.
- **Validação Upstream**: `expml run start` exige que as Etapas 1, 2, 3 e 4A estejam concluídas e válidas no experimento (`verify_preparation_gate`, `verify_partition_gate`, `verify_scenarios_gate`, `verify_models_gate`).
- **Política de Erro Padrão**: O padrão é `fault_tolerant` para coletar o maior volume de dados experimentais, com opção `--error-policy fail_fast`.
- **Auto-consolidação OOF**: Habilitada por padrão (`auto_consolidate_oof=True`), podendo ser desativada com `--no-oof`.
- Open questions: None. Todas as decisões de arquitetura e interface foram alinhadas e registradas em context.md.

---

## User Stories

### US-M54-01: Execução de Matriz Experimental via Terminal (`expml run start`)
Como pesquisador, quero disparar a execução de uma matriz experimental completa a partir do diretório do experimento pelo terminal, para que os modelos sejam treinados e avaliados em todos os cenários e dobras de forma automatizada e com consolidação OOF.

- **AC-M54-01-01**: WHEN `expml run start --experiment-dir <dir>` é executado em um experimento com etapas 1 a 4A concluídas, THEN o sistema SHALL validar os portões upstream (`verify_preparation_gate`, `verify_partition_gate`, `verify_scenarios_gate`, `verify_models_gate`), executar a matriz de células, gerar artefatos em `<experiment-dir>/runs` e retornar código de saída 0.
- **AC-M54-01-02**: WHEN `expml run start` é executado com `--run-dir <custom_dir>`, THEN o sistema SHALL gravar os artefatos da execução no diretório especificado.
- **AC-M54-01-03**: WHEN `expml run start` é executado com `-j <N>` ou `--parallel <N>` com $N \ge 2$, THEN o sistema SHALL despachar a execução em paralelo com até $N$ workers concorrentes.
- **AC-M54-01-04**: WHEN `expml run start` é executado com `--error-policy fail_fast`, THEN o sistema SHALL interromper a execução na primeira falha de célula e registrar as demais como canceladas.
- **AC-M54-01-05**: WHEN `expml run start` é executado sem a flag `--no-oof`, THEN o sistema SHALL consolidar automaticamente as predições out-of-fold sob `{run_dir}/oof/` para todas as configurações que tiverem dobras concluídas.
- **AC-M54-01-06**: WHEN `expml run start` é executado com a flag `--no-oof`, THEN o sistema SHALL omitir a geração do diretório `oof/`.
- **AC-M54-01-07**: WHEN o diretório de destino já contém uma execução anterior e a flag `--force` não for informada, THEN o sistema SHALL recusar a execução, imprimir mensagem instrutiva e encerrar com código de saída 2.

### US-M54-02: Retomada Resiliente de Execução Interrompida (`expml run resume`)
Como operador de experimentos computacionais caros, quero poder retomar uma execução abortada ou parcialmente concluída pelo terminal sem refazer cálculos de células já finalizadas.

- **AC-M54-02-01**: WHEN `expml run resume --run-dir <run_dir>` é executado em uma pasta de execução interrompida, THEN o sistema SHALL validar a consistência do estado anterior, pular células com artefatos válidos e reexecutar apenas células pendentes ou com artefatos ausentes, retornando código de saída 0.
- **AC-M54-02-02**: WHEN `expml run resume` é executado com a flag `--retry-failed`, THEN o sistema SHALL reexecutar adicionalmente as células marcadas anteriormente com status `FAILED`.
- **AC-M54-02-03**: WHEN `expml run resume` é executado e `execution_state.json` estiver corrompido ou ausente, THEN o sistema SHALL imprimir mensagem instrutiva sem traceback e encerrar com código de saída 2.

### US-M54-03: Inspeção do Progresso da Execução (`expml run status`)
Como usuário, quero verificar o estado atual e o percentual de conclusão de uma execução de matriz a qualquer momento sem acionar recálculos nem modificar o disco.

- **AC-M54-03-01**: WHEN `expml run status --run-dir <run_dir>` é executado, THEN o sistema SHALL carregar `execution_state.json` de forma puramente somente-leitura e imprimir o total de células, o total concluído, falhado, cancelado e pendente, com porcentagem de progresso, retornando código de saída 0.
- **AC-M54-03-02**: WHEN `expml run status` é executado apontando para um diretório inexistente ou sem arquivo de estado, THEN o sistema SHALL imprimir mensagem instrutiva sem traceback e encerrar com código de saída 2.

### US-M54-04: Auditoria de Portão de Estágio da Etapa 4 (`expml run verify`)
Como auditor de reprodutibilidade, quero verificar formalmente se uma execução concluiu todos os requisitos de integridade da Etapa 4 antes de avançar para a consolidação estatística.

- **AC-M54-04-01**: WHEN `expml run verify --run-dir <run_dir>` é executado em uma execução válida com células concluídas e OOF consolidados, THEN o sistema SHALL invocar `verify_runs_gate`, imprimir resumo de conformidade com status `READY` e encerrar com código de saída 0.
- **AC-M54-04-02**: WHEN `expml run verify` é executado sobre uma execução com células incompletas (`PENDING`/`RUNNING`), artefatos faltantes ou divergência de hashes, THEN o sistema SHALL imprimir mensagem instrutiva sem traceback e encerrar com código de saída 2.

### US-M54-05: Tratamento de Erros, Ergonomia e Pureza de Runtime (`CLI-06` a `CLI-11`, `XCUT-02`)
Como desenvolvedor e integrador, quero que a interface de linha de comando cumpra estritamente todas as diretrizes de código de saída, ergonomia de terminal, ausência de vazamento de tracebacks e pureza de dependências.

- **AC-M54-05-01**: WHEN qualquer subcomando de `run` encontra uma exceção do framework (`ExperimentalMLError` ou `ValueError`), THEN o sistema SHALL imprimir `Error: <mensagem>` no `sys.stderr` sem traceback e retornar código de saída 2.
- **AC-M54-05-02**: WHEN `expml run` é executado sem subcomando ou com `--help`, THEN o sistema SHALL imprimir a mensagem de ajuda no `sys.stdout` e retornar código de saída 0.
- **AC-M54-05-03**: WHEN `main.py` ou `cmd_run.py` são importados, THEN o sistema SHALL carregar zero dependências pesadas (`numpy`, `scipy`, etc.) no nível de módulo (`CLI-10`).
- **AC-M54-05-04**: WHEN os subcomandos de `run` emitem resumos para o terminal, THEN o sistema SHALL suprimir strings de hash criptográfico (`dataset_hash`, `config_hash`), exibindo apenas identificadores legíveis (`CLI-11`).
- **AC-M54-05-05**: WHEN a suíte de testes de `run` é executada em subprocesso isolado, THEN o sistema SHALL confirmar conformidade estrita com `XCUT-02` (apenas standard library e `numpy>=1.24.0`).

---

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Component | Description |
| :--- | :--- | :--- | :--- |
| ORCH-22 | AC-M54-05-02, AC-M54-05-03 | `src/experimental_ml/cli/main.py` | Ponto de entrada modular e registro dos subparsers de `run` |
| ORCH-23 | AC-M54-01-01, AC-M54-01-02, AC-M54-01-03, AC-M54-01-04, AC-M54-01-05, AC-M54-01-06, AC-M54-01-07 | `src/experimental_ml/cli/cmd_run.py` | Subcomando `expml run start` com execução matricial e consolidação OOF |
| ORCH-24 | AC-M54-02-01, AC-M54-02-02, AC-M54-02-03 | `src/experimental_ml/cli/cmd_run.py` | Subcomando `expml run resume` com retomada incremental e `--retry-failed` |
| ORCH-25 | AC-M54-03-01, AC-M54-03-02 | `src/experimental_ml/cli/cmd_run.py` | Subcomando `expml run status` somente-leitura e progresso percentual |
| ORCH-26 | AC-M54-04-01, AC-M54-04-02 | `src/experimental_ml/cli/cmd_run.py` | Subcomando `expml run verify` com auditoria formal via `verify_runs_gate` |
| ORCH-27 | AC-M54-05-01, AC-M54-05-04 | `src/experimental_ml/cli/main.py`, `src/experimental_ml/cli/cmd_run.py` | Códigos de saída padronizados (0, 1, 2) e supressão de tracebacks e hashes |
| ORCH-28 | AC-M54-05-05 | `tests/integration/cli/test_run_e2e.py` | Ciclo transversal ponta a ponta e pureza estrita de runtime (`XCUT-02`) |
