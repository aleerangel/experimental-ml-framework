# Catálogo Completo da CLI `expml`

A interface de linha de comando `expml` implementa *lazy imports* para resposta instantânea e encapsula todas as 6 etapas metodológicas por meio de **2 comandos diretos** (`init`, `quickrun`), **7 grupos de comandos** e **19 subcomandos**.

---

## Opções Globais e Atalhos de Entrada Rápida

- `expml -h` / `expml --help`: Exibe a ajuda geral e lista os comandos e grupos.
- `expml --version`: Exibe a versão instalada do pacote e encerra com código `0`.

### `expml init`
Cria um projeto inicial pronto com `dados_exemplo.csv` e todos os arquivos JSON válidos (`schema.json`, `rules.json`, `scenarios.json`, `models.json`, `partition.json`, `stats_config.json`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--output-dir DIR` | Sim | Diretório de destino para o projeto inicializado. |
| `--task TASK` | Não | Tipo de tarefa (`regression`, `binary_classification`, `multiclass_classification`; padrão: `regression`). |
| `--force` | Não | Sobrescreve arquivos existentes no diretório de destino. |

### `expml quickrun`
Executa sequencialmente todas as 6 etapas a partir de uma pasta inicializada.

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir DIR` / `--exp-dir DIR` | Sim | Diretório do experimento inicializado. |
| `--data CSV` | Não | Caminho alternativo para o arquivo CSV de entrada. |
| `--metrics M1 [M2 ...]` | Não | Lista explícita de métricas a calcular e consolidar. |
| `--delimiter DELIM` | Não | Delimitador de colunas (`,`, `;`, `\t`, `|`, `whitespace`). Sobrescreve `schema.json`. |
| `--decimal {., ,, auto}` | Não | Separador decimal (`.`, `,` ou `auto`). Sobrescreve `schema.json`. |
| `--encoding CODEC` | Não | Codificação do arquivo (`utf-8-sig`, `latin-1`, `cp1252` ou `auto`). |
| `--no-header` | Não | Trata a primeira linha como dados em vez de cabeçalho. |
| `--column-names COL ...` | Não | Nomes explícitos de colunas (útil com `--no-header`). |
| `--quotechar CHAR` | Não | Caractere de aspas (padrão: `"`). |
| `--force` | Não | Sobrescreve artefatos de execuções anteriores (habilitado por padrão: `default=True`). |

---

## Convenção Oficial de Códigos de Saída (*Exit Codes*)

Conforme implementado em `experimental_ml.cli.main` e nos manipuladores de subcomandos:

| Código | Significado Contratual | Causas Típicas |
| :---: | :--- | :--- |
| **`0`** | **Sucesso** | Execução concluída com êxito e todos os portões satisfeitos. |
| **`1`** | **Erro inesperado de sistema** | Exceção não tratada em tempo de execução (`Exception` genérica) ou falha fatal de sistema. |
| **`2`** | **Erro semântico, contrato ou portão** | Violação de contrato/esquema (`ExperimentalMLError`, `ConfigurationError`, `DataIntegrityError`, `ValueError`), erro de uso/argumentos do `argparse`, ou reprovação em portão de estágio (`verify_*_gate`). |

---

## 1. `expml data` (Etapa 1 — Ingestão, Perfilamento e Saneamento)

### `expml data profile`
Ingere a base tabular bruta, calcula os hashes tripartites (`raw_source_hash`, `schema_hash`, `dataset_hash`) e gera o diagnóstico estrutural (`dataset_profile.json`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--data DATA` | Sim | Caminho para o arquivo tabular de entrada (`.csv`, `.tsv`, `.txt`). |
| `--schema SCHEMA` | Sim | Caminho para o arquivo JSON com o esquema (`DatasetSchemaSpec`). |
| `--output-dir OUTPUT_DIR` | Sim | Diretório de saída onde os artefatos do experimento serão criados. |
| `--delimiter DELIM` | Não | Delimitador de colunas (`,`, `;`, `\t`, `|`, `whitespace`). Sobrescreve `"csv_format"` do `schema.json`. |
| `--decimal {., ,, auto}` | Não | Separador decimal (`.`, `,` ou `auto`). Sobrescreve `"csv_format"` do `schema.json`. |
| `--encoding CODEC` | Não | Codificação do arquivo (`utf-8-sig`, `latin-1`, `cp1252` ou `auto`). Sobrescreve `schema.json`. |
| `--no-header` | Não | Trata a primeira linha como dados em vez de cabeçalho. |
| `--column-names COL ...` | Não | Nomes explícitos de colunas (útil com `--no-header`). |
| `--quotechar CHAR` | Não | Caractere de aspas (padrão: `"`). |
| `--force` | Não | Sobrescreve artefatos existentes no diretório de saída (padrão: bloqueado). |

### `expml data sanitize`
Aplica regras determinísticas pré-partição e materializa a visão saneada (`preparation_plan.json` e `sanitized_view.json`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Caminho do diretório do experimento criado em `data profile`. |
| `--rules RULES` | Não | Caminho para o arquivo JSON com a lista de regras (`PreparationRule`). Se omitido e não houver achados confirmados, usa `[]`. |
| `--force` | Não | Sobrescreve o plano e a visão saneada caso já existam. |

---

## 2. `expml features` (Etapa 2 — Exploração e Cenários de Features)

### `expml features explore`
Executa análise exploratória univariada rotulada compulsoriamente como `EXPLORATORY_FULL_DATA`, imprime no terminal o ranking único por atributo (ordenado por `mean(|valor|)`) e os pares redundantes e gera `reports/exploratory_features.{json,md,html}` (HTML formatado para impressão A4/PDF), tabelas `reports/exploratory_{target_associations,redundancy_matrix}.csv` e gráficos PNG rotulados `figures/exploratory_{target_associations,redundancy_heatmap}.png`.

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento contendo os artefatos da Etapa 1. |
| `--force` | Não | Sobrescreve o relatório exploratório anterior. |

### `expml features scenarios`
Valida e persiste o catálogo de cenários `FIXED` e `DYNAMIC` (`scenarios.json`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento. |
| `--scenarios SCENARIOS` | Sim | Caminho para o arquivo JSON com as definições de `FeatureScenario`. |
| `--force` | Não | Sobrescreve o catálogo de cenários existente. |

### `expml features verify`
Verifica o portão de integridade da Etapa 2 (`verify_scenarios_gate`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento a auditar. |

---

## 3. `expml models` (Etapa 3 — Registro e Validação de Modelos)

### `expml models validate`
Valida capacidades, pré-processamento em 2 camadas e *search specs*, persistindo `models.json` sem imprimir hashes brutos no `stdout` (`CLI-11`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento. |
| `--models MODELS` | Sim | Caminho para o arquivo JSON com o catálogo de `ModelSpec`. |
| `--force` | Não | Sobrescreve o catálogo de modelos existente. |

### `expml models verify`
Verifica o portão da Etapa 3 (`verify_models_gate`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento a auditar. |

---

## 4. `expml partition` (Etapa 4A — Particionamento Compartilhado)

### `expml partition build`
Constrói e persiste o `PartitionPlan` (`partition_plan.json` e `splits.csv.gz`) com isolamento determinístico.

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento. |
| `--config CONFIG` | Sim | Caminho para o JSON de configuração de partição (`PartitionConfig`: `strategy`, `regime`, `n_splits`, `group_col`, `time_col`, `holdout_fraction`, `master_seed`). |
| `--seed SEED` | Não | Sobrescreve a semente mestre (`master_seed`) declarada no JSON de configuração. |
| `--force` | Não | Sobrescreve um plano de partição existente. |

### `expml partition verify`
Verifica os invariantes matemáticos de partição (disjunção, ausência de dobras vazias, grupos/ordem temporal) e o portão da Etapa 4A (`verify_partition_gate`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento a auditar. |

---

## 5. `expml run` (Etapa 4B — Execução Matricial e Retomada)

### `expml run start`
Executa a matriz completa `(modelo × cenário × dobra)` com checkpointing atômico incremental e consolidação OOF automática.

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento contendo as Etapas 1 a 4A validadas. |
| `--run-dir RUN_DIR` | Não | Diretório customizado de saída da execução (padrão: `<experiment-dir>/runs`). |
| `-j`, `--jobs`, `--parallel PARALLEL` | Não | Número de trabalhadores paralelos externos (padrão: `1`, sequencial). |
| `--error-policy` | Não | Política de tratamento de erro por célula: `fault_tolerant` (padrão — isola células falhas como `FAILED` sem interromper as demais) ou `fail_fast` (aborta na primeira falha). |
| `--no-oof` | Não | Desativa a consolidação automática de predições *out-of-fold* (OOF) ao final. |
| `--metrics M1 [M2 ...]` | Não | Lista opcional de métricas de `METRICS_CATALOG` (se omitida, usa padrões seguros por tarefa). |
| `--force` | Não | Sobrescreve o diretório de execução caso já exista. |

### `expml run resume`
Retoma uma execução interrompida preservando células `COMPLETED` e validando compatibilidade de `dataset_hash` e `partition_plan_id`.

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--run-dir RUN_DIR` | Sim | Diretório da execução contendo `execution_state.json`. |
| `--experiment-dir EXPERIMENT_DIR` | Não | Diretório do experimento (inferido automaticamente a partir de `--run-dir` se omitido). |
| `-j`, `--jobs`, `--parallel PARALLEL` | Não | Número de trabalhadores paralelos na retomada (padrão: `1`). |
| `--retry-failed` | Não | Reexecuta também células marcadas anteriormente como `FAILED` (padrão: executa apenas `PENDING`/`RUNNING`). |
| `--no-oof` | Não | Desativa a consolidação OOF automática após a retomada. |

### `expml run status`
Exibe o progresso atual das células (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--run-dir RUN_DIR` | Condicional | Diretório da execução contendo `execution_state.json` (opcional se `--experiment-dir` for informado). |
| `--experiment-dir`, `--exp-dir` | Condicional | Diretório do experimento (infere `<experiment-dir>/runs`). |

### `expml run verify`
Verifica o portão da Etapa 4B e integridade dos artefatos OOF (`verify_runs_gate`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--run-dir RUN_DIR` | Condicional | Diretório da execução a auditar (opcional se `--experiment-dir` for informado). |
| `--experiment-dir`, `--exp-dir` | Condicional | Diretório do experimento (infere `<experiment-dir>/runs`). |

---

## 6. `expml stats` (Etapa 5 — Consolidação e Comparação Estatística)

### `expml stats run`
Executa consolidação descritiva, verificação de adequação metodológica, testes pareados (Nadeau-Bengio / Wilcoxon), ajustes de multiplicidade e fronteira de Pareto.

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento com execuções concluídas na Etapa 4. |
| `--config CONFIG` | Não | Caminho opcional para JSON de configuração de comparações (`ComparisonSpec`, `MultiObjectiveSpec`, `alpha`). |
| `--force` | Não | Sobrescreve artefatos estatísticos existentes. |

### `expml stats status`
Exibe resumo consolidado das configurações e cobertura (`VALID`, `PARTIAL_COVERAGE`, `NO_COVERAGE`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento. |

### `expml stats verify`
Verifica o portão da Etapa 5 (`verify_statistics_gate`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir EXPERIMENT_DIR` | Sim | Diretório do experimento a auditar. |

---

## 7. `expml report` (Etapa 6 — Relatórios e Reprodutibilidade)

### `expml report generate`
Gera relatório científico completo, 7 famílias de tabelas e figuras determinísticas em modo estritamente somente-leitura.

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir`, `--exp-dir` | Sim | Diretório do experimento. |
| `--output-dir OUTPUT_DIR` | Não | Diretório de saída dos relatórios (padrão: `<exp-dir>/reports`). |
| `--format` | Não | Formato do relatório principal: `markdown`, `html` ou `both`. |
| `--audience` | Não | Perfil de seleção de conteúdo: `FULL_LAB` (todas as 7 famílias), `ARTICLE_COMPACT` (resumo para artigo) ou `CUSTOM` (personalizado). |
| `--families FAMILIES` | Condicional | Lista separada por vírgulas de valores de `ReportFamily` (obrigatória quando `--audience CUSTOM`). |
| `--objective OBJECTIVE` | Não | Declaração textual opcional do objetivo científico do pesquisador. |
| `--force` | Não | Sobrescreve relatórios existentes no destino. |

### `expml report export`
Constrói o pacote portátil de reprodutibilidade com linhagem (`artifact_provenance.json`) e hashes relativos POSIX (`reproducibility/checksums.sha256`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir`, `--exp-dir` | Sim | Diretório do experimento de origem. |
| `--output-dir OUTPUT_DIR` | Não | Diretório do pacote exportado (padrão: `<exp-dir>`). |
| `--mode` | Não | Modalidade do pacote: `full_package` (inclui dados em `data/`) ou `reduced_no_raw_data` (exclui `data/` para revisão cega/NDA). |
| `--audience` | Não | Perfil de seleção: `FULL_LAB`, `ARTICLE_COMPACT` ou `CUSTOM`. |
| `--families FAMILIES` | Condicional | Lista separada por vírgulas de `ReportFamily` (obrigatória se `--audience CUSTOM`). |
| `--objective OBJECTIVE` | Não | Declaração textual opcional do objetivo científico. |
| `--force` | Não | Sobrescreve artefatos existentes no diretório de destino. |

### `expml report verify`
Verifica a integridade completa do pacote exportado, checksums SHA-256 e o portão da Etapa 6 (`verify_report_gate`).

| Argumento / Opção | Obrigatório | Descrição e Variações |
| :--- | :---: | :--- |
| `--experiment-dir`, `--exp-dir` | Sim | Diretório do pacote ou experimento a verificar. |
