# Contexto e Decisões de Projeto — Marco M5.4 (CLI Run End-to-End)

## Decisões Registradas com o Usuário

1. **Subcomandos de `expml run`**:
   - `start`: Inicia uma nova execução da matriz de experimentos ($M \times C \times F$) a partir de um `experiment-dir`, carregando dataset saneado, partição, cenários e modelos, executando as células e gerando artefatos e predições OOF.
   - `resume`: Retoma uma execução interrompida a partir de `run-dir`, ignorando células já concluídas com artefatos válidos e reexecutando células pendentes/ausentes (com suporte a reexecução opcional de células falhas via `--retry-failed`).
   - `status`: Inspeciona o estado atual da execução matricial a partir de `execution_state.json` sem executar nada e sem modificar o disco, exibindo métricas de progresso e contagens por status.
   - `verify`: Audita o portão de estágio Stage 4 (`verify_runs_gate`), validando pré-requisitos upstream, ausência de estados não-terminais, existência física dos artefatos em disco e alinhamento de hashes.

2. **Diretório de Destino Padrão para `start`**:
   - Diretório canônico `<experiment-dir>/runs` por padrão (conforme convenções da ARQUITETURA §5 e `verify_runs_gate`), permitindo sobrescrita via `--output-dir` ou `--run-dir`.

3. **Controle de Paralelismo**:
   - Argumento `-j` / `--jobs` / `--parallel` (inteiro $\ge 1$, default `1`), determinando o número de workers em paralelo.

4. **Política de Tratamento de Erro**:
   - Argumento `--error-policy` com opções `fault_tolerant` (default) e `fail_fast`.

5. **Consolidação Out-Of-Fold (OOF)**:
   - Habilitada por padrão (`auto_consolidate_oof=True`), com opção de desativação explícita via `--no-oof`.

6. **Invariantes Arquiteturais de CLI (`CLI-06` a `CLI-11`, `XCUT-02`)**:
   - `CLI-06`: Códigos de saída padronizados (0 para sucesso, 2 para erros de domínio/precondições sem traceback, 1 para falhas sistêmicas inesperadas).
   - `CLI-07`: Subparsers compostos hierarquicamente de forma modular.
   - `CLI-08`: Proteção contra sobrescrita com `--force`.
   - `CLI-09`: Suporte a `--version`, `--help` e ausência de argumentos com saída 0.
   - `CLI-10`: Zero importações pesadas no nível de módulo de `cli/main.py` e `cli/cmd_run.py`.
   - `CLI-11`: Supressão de hashes criptográficos na saída padrão do terminal.
   - `XCUT-02`: Apenas biblioteca padrão e `numpy>=1.24.0` no runtime.
