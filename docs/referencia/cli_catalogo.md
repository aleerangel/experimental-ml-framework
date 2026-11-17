# Catálogo Completo da CLI `expml`

A interface de linha de comando `expml` implementa *lazy imports* (`CLI-10`) para resposta instantânea e encapsula todas as 6 etapas metodológicas por meio de 7 grupos de comandos.

---

## Convenção Oficial de Códigos de Saída (*Exit Codes*)

Conforme implementado em `experimental_ml.cli.main` e nos manipuladores de subcomandos:

| Código | Significado Contratual | Causas Típicas |
| :---: | :--- | :--- |
| **`0`** | **Sucesso** | Execução concluída com êxito e todos os portões satisfeitos. |
| **`1`** | **Erro inesperado de sistema** | Exceção não tratada em tempo de execução (`Exception` genérica) ou aborto em modo `FAIL_FAST`. |
| **`2`** | **Erro semântico, contrato ou portão** | Violação de contrato/esquema (`ExperimentalMLError`, `ConfigurationError`, `DataIntegrityError`, `ValueError`), erro de uso/argumentos do `argparse`, ou reprovação em portão de estágio (`verify_*_gate`). |

---

## 1. `expml data` (Etapa 1 — Ingestão e Saneamento)

- `expml data profile`: Ingere o arquivo tabular, calcula hashes tripartites e gera o diagnóstico estrutural (`dataset_profile.json`).
- `expml data sanitize`: Aplica regras determinísticas pré-partição e gera a visão saneada (`preparation_plan.json`, `sanitized_view.json`).

---

## 2. `expml features` (Etapa 2 — Exploração e Cenários)

- `expml features explore`: Executa análise exploratória univariada rotulada como `EXPLORATORY_FULL_DATA` (`exploratory_features.json`).
- `expml features scenarios`: Valida e persiste o catálogo de cenários `FIXED` e `DYNAMIC` (`scenarios.json`).
- `expml features verify`: Verifica o portão da Etapa 2 (`verify_scenarios_gate`).

---

## 3. `expml models` (Etapa 3 — Registro e Validação de Modelos)

- `expml models validate`: Valida capacidades, pré-processamento em 2 camadas e *search specs*, persistindo `models.json` (sem imprimir hashes brutos no `stdout` — `CLI-11`).
- `expml models verify`: Verifica o portão da Etapa 3 (`verify_models_gate`).

---

## 4. `expml partition` (Etapa 4A — Particionamento Compartilhado)

- `expml partition build`: Constrói e persiste o `PartitionPlan` (`partition_plan.json` e `splits.csv.gz`) com isolamento determinístico.
- `expml partition verify`: Verifica invariantes matemáticos de partição e o portão da Etapa 4A (`verify_partition_gate`).

---

## 5. `expml run` (Etapa 4B — Execução Matricial)

- `expml run start`: Executa a matriz completa `(modelo × cenário × dobra)` com checkpointing atômico incremental e consolidação OOF.
- `expml run resume`: Retoma execução interrompida preservando células `COMPLETED`, validando compatibilidade de `dataset_hash` e `partition_plan_id`.
- `expml run status`: Exibe o progresso das células (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`).
- `expml run verify`: Verifica o portão da Etapa 4B (`verify_runs_gate`).

---

## 6. `expml stats` (Etapa 5 — Consolidação e Comparação Estatística)

- `expml stats run`: Executa consolidação descritiva, testes pareados (Nadeau-Bengio / Wilcoxon), ajustes de multiplicidade e fronteira de Pareto.
- `expml stats status`: Exibe resumo das configurações e métricas consolidadas.
- `expml stats verify`: Verifica o portão da Etapa 5 (`verify_statistics_gate`).

---

## 7. `expml report` (Etapa 6 — Relatórios e Reprodutibilidade)

- `expml report generate`: Gera relatório científico (`Markdown`, `HTML` ou ambos), 7 famílias de tabelas e figuras em modo somente-leitura.
- `expml report export`: Constrói pacote portátil de reprodutibilidade (`FULL_PACKAGE` ou `REDUCED_NO_RAW_DATA`) com `reproducibility/checksums.sha256` relativos.
- `expml report verify`: Verifica a integridade completa e o portão da Etapa 6 (`verify_report_gate`).
