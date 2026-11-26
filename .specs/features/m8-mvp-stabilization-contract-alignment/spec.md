# M8 — Estabilização do MVP e Alinhamento Contratual (Specification — Draft)

- **Status**: Approved (Fase TLC: **Specify** concluída)
**Approved**: 2026-11-24 - user: "pode commitar e prosseguir"
- **Milestone**: `M8` (`m8-mvp-stabilization-contract-alignment`)
- **Related Validation Findings**: `VAL-BUG-002`, `VAL-BUG-003`, `VAL-BUG-004`, `VAL-BUG-005`, `VAL-BUG-007`, `VAL-BUG-009`, `VAL-BUG-010`, `VAL-BUG-011`, `VAL-QUAL-003`, `VAL-ENH-004`

---

## Problem Statement

Durante a auditoria técnica do MVP (`AUDITORIA_TECNICA_DO_MVP.md`), verificou-se que a implementação atual contém lacunas de integração e pequenos desvios contratuais em funcionalidades já especificadas na Onda 1:
1. As Tabelas A (`A_DATA_CHARACTERIZATION`) e G (`G_MODEL_SPECIFIC_ARTIFACTS`) da Etapa 6 geram 0 linhas em experimentos reais porque leem estruturas de dicionário diferentes das produzidas pelas Etapas 1 e 4B (`VAL-BUG-002`, `VAL-BUG-003`).
2. As funções `compute_correlation_ratio` e `compute_cramers_v` da Etapa 2 lançam `TypeError` quando colunas categóricas (`dtype=object`) contêm `None` (`VAL-BUG-004`).
3. A seleção dinâmica de atributos (`ScenarioMode.DYNAMIC`) é executada uma única vez no fold externo antes do loop interno do Nested CV (desviando do `ADR-003`), e `split_inner_folds` não propaga estratificação, agrupamento ou ordem temporal (`VAL-BUG-005`).
4. A fachada Python `run_experiment` grava artefatos de disco parciais (omitindo `sanitized_view.json`, `splits.csv.gz` e `pareto_summary.json`, o que quebra comandos CLI subsequentes) e ignora `seed` ao clonar instâncias prontas de estimadores (`VAL-BUG-007`).
5. A CLI `expml stats compute` e `run_experiment` não informam `n_total_candidates_per_config` (fazendo o índice de Kuncheva retornar `None`), e a CLI fixa a fronteira de Pareto em apenas 1 objetivo (`VAL-BUG-009`, `VAL-ENH-004`).
6. `MatrixExecutionState` não valida `scenarios_hash` e `models_hash` na retomada (`resume`), `_ACTIVE_INSTANCES` não usa `threading.Lock`, `expml init` para classificação cria apenas 1 modelo baseline e `validate_verification.py` verifica um caminho sem `docs/` (`VAL-BUG-010`, `VAL-QUAL-003`, `VAL-BUG-011`).

## Goals

- [ ] Povoar integralmente as Tabelas A (`tbl_family_a`) e G (`tbl_family_g`) na Etapa 6 a partir dos artefatos reais gerados em `data/dataset_profile.json` e `runs/cells/cell_*.json`.
- [ ] Garantir tratamento pairwise seguro para valores ausentes (`None`/`NaN`) em colunas categóricas nas estatísticas de associação da Etapa 2.
- [ ] Alinhar a execução de seleção dinâmica + pré-processamento + Nested CV ao `ADR-003` (ou à opção confirmada pelo desenvolvedor).
- [ ] Garantir 100% de interoperabilidade entre diretórios criados por `run_experiment` e todos os subcomandos da CLI `expml`, propagando `seed` para instâncias clonadas.
- [ ] Computar o índice de Kuncheva com `n_total_candidates` real dos cenários e permitir múltiplos objetivos de Pareto na CLI e em `run_experiment`.
- [ ] Validar `scenarios_hash` e `models_hash` no `resume`, proteger `_ACTIVE_INSTANCES` com `threading.Lock` e incluir 2 modelos iniciais nos templates de classificação de `expml init`.

## Out of Scope

- Implementação de novos transformadores `IMPUTER` ou codificadores categóricos intra-fold conectados a `DEFER_INTRA_FOLD` (alocados no Marco `M9`).
- Execução de células `FINAL_HOLDOUT` sob o regime `CV_AND_HOLDOUT` (alocada no Marco `M9`).
- Redesenho dos renderizadores gráficos das Etapas 2 e 6 ou introdução de `matplotlib`/`pandas` (alocados no Marco `M10`).

---

## User Stories

- **US-01 (Pesquisador / Relatórios):** Como pesquisador, quero que as Tabelas A e G e o índice de Kuncheva sejam preenchidos com dados reais do experimento (em vez de 0 linhas ou `N/A`), para que o relatório da Etapa 6 reflita fielmente o dataset e os modelos ajustados.
- **US-02 (Pesquisador / Exploração):** Como pesquisador, quero executar `explore_features` em datasets com valores ausentes (`None`) em colunas categóricas sem `TypeError`, para poder triar associações antes da modelagem.
- **US-03 (Pesquisador / Rigor Metodológico):** Como pesquisador, quero que a seleção dinâmica de atributos e a Camada 1 ocorram dentro de cada sub-fold interno do Nested CV (`ADR-003`) com respeito a estratificação, grupos e ordem temporal, para evitar vazamento na escolha de hiperparâmetros.
- **US-04 (Pesquisador / Python + CLI):** Como pesquisador, quero executar `run_experiment` em Python e depois inspecionar/exportar o mesmo diretório pela CLI `expml` com determinismo garantido para instâncias clonadas e retomada íntegra.

---

## Assumptions & Open Questions

Open questions: none (D1 e D2 resolvidas pelo desenvolvedor em 2026-11-24).

### Assumptions
- Todos os cálculos de núcleo permanecem em Python >= 3.11 + NumPy (`XCUT-02`), sem novas dependências externas.
- `DEFER_INTRA_FOLD` (`IMPUTER`/codificação categórica) e `FINAL_HOLDOUT` sob `CV_AND_HOLDOUT` permanecem fora de escopo do `M8` (alocados em `M9`).
- O redesign visual com `matplotlib`/`pandas` permanece fora de escopo do `M8` (alocado em `M10`).

### Decisões Registradas pelo Desenvolvedor (Open Questions Resolvidas)

1. **Decisão D1 (`VAL-BUG-005` / `ADR-003` — Opção A):**
   - A seleção dinâmica de atributos deve ocorrer dentro de cada sub-fold interno durante o tuning, incluindo a execução da Camada 1 e de `select_features_in_fold`, utilizando exclusivamente os dados de treinamento daquele sub-fold.
   - Após a escolha dos melhores hiperparâmetros, a Camada 1 e a seleção dinâmica devem ser reajustadas utilizando todo o treinamento do fold externo, antes da avaliação no respectivo fold de teste.
   - As restrições de estratificação, agrupamento e temporalidade também devem ser propagadas para `split_inner_folds`.
   - Justificativa: manter o cumprimento estrito do `ADR-003`, priorizando a integridade metodológica e a prevenção de vazamento de dados em detrimento da economia computacional.
2. **Decisão D2 (`VAL-BUG-010` — Nome dos arquivos de células: normalização sem retrocompatibilidade):**
   - Adotar `cell_<m>__<s>__<f>.json` como único padrão canônico de gravação e leitura (e padrão correspondente para predições, sem prefixo `cell_` duplicado).
   - Não implementar suporte ao padrão legado `cell_cell_<m>__<s>__<f>.json`; arquivos existentes nesse formato não precisam de migração automática nem de aceitação pelo loader.
   - Atualizar componentes de armazenamento e carregamento, documentação e testes para refletir a convenção única.
   - Justificativa: o framework ainda está em desenvolvimento e não há necessidade estabelecida de manter compatibilidade com o formato anterior.

---

## Requirements (EARS Notation)

### M8-01 — Tabela da Família A (`VAL-BUG-002`)
- **WHEN** `build_table_model(ReportFamily.A_DATA_CHARACTERIZATION, loaded_data)` é invocado sobre um `dataset_profile.json` real serializado por `dataset_profile_to_dict`, **THE SYSTEM SHALL** extrair as propriedades escalares e contagens do sub-dicionário `"summary"` (incluindo `n_rows`, `n_cols`, `memory_bytes`, contagem de colunas e contagem de achados de triagem), produzindo uma tabela com pelo menos 5 linhas válidas.

### M8-02 — Tabela da Família G (`VAL-BUG-003`)
- **WHEN** `load_reporting_data` carrega um diretório de experimento concluído e `build_table_model(ReportFamily.G_MODEL_SPECIFIC_ARTIFACTS, loaded_data)` é executado, **THE SYSTEM SHALL** ler os registros `diagnostics` persistidos nas células em `runs/cells/*.json` e consolidar por `(model_id, scenario_id)` os diagnósticos exportados pelos adaptadores (coeficientes, importâncias de atributos, `oob_score`, número de vetores de suporte e perda final).

### M8-03 — Tratamento de `None` em Estatísticas Categóricas (`VAL-BUG-004`)
- **WHEN** `compute_correlation_ratio(cat_arr, cont_arr)` ou `compute_cramers_v(x_arr, y_arr)` recebe arrays contendo valores ausentes (`None` ou `np.nan`), **THE SYSTEM SHALL** filtrar pairwise todas as posições com valores ausentes antes de chamar `np.unique`, retornando a estatística calculada sobre os pares válidos (ou `0.0` caso restem menos de 2 observações ou menos de 2 categorias distintas).

### M8-04 — Alinhamento Intra-Fold no Nested CV (`VAL-BUG-005`)
- **WHEN** `execute_single_cell` executa uma célula com `ScenarioMode.DYNAMIC` e `ModelSpec.search_spec` ativo (sob a Opção A da Decisão D1), **THE SYSTEM SHALL** aplicar a Camada 1 de pré-processamento e `select_features_in_fold` dentro de cada fold interno de `run_nested_tuning` (usando splits internos compatíveis com a estratégia externa de particionamento) e, após selecionar a melhor configuração de hiperparâmetros, reajustar Camada 1, seleção dinâmica, Camada 2 e modelo final sobre o conjunto de treino externo completo.

### M8-05 — Interoperabilidade e Determinismo na Fachada `run_experiment` (`VAL-BUG-007`)
- **WHEN** `run_experiment(..., experiment_dir=path)` é executado, **THE SYSTEM SHALL** persistir todos os artefatos canônicos das Etapas 1 a 6 (`data/dataset_descriptor.json` completo, `data/sanitized_view.json`, `partitions/splits.csv.gz`, `partitions/splits.schema.json`, `reports/exploratory_features.json`, `reports/exploratory_features.md` e `statistics/pareto_summary.json`), de modo que `expml partition verify`, `expml run verify`, `expml stats compute` e `expml report export` executem com código `0` sobre `path`.
- **WHEN** o usuário fornece uma instância de estimador em `run_experiment(models={"id": estimator_instance})` cujo atributo `random_state` existe e é `None`, **THE SYSTEM SHALL** injetar `random_state=seed` na cópia instanciada para cada célula.

### M8-06 — Índice de Kuncheva e Pareto Multiobjetivo na CLI e Fachada (`VAL-BUG-009`, `VAL-ENH-004`)
- **WHEN** `expml stats compute` ou `run_experiment` executa `consolidate_descriptive`, **THE SYSTEM SHALL** calcular `n_total_candidates_per_config` a partir de `len(scenario.candidate_features)` (ou do total de atributos preditores disponíveis na visão sanitizada quando `candidate_features` estiver vazio), garantindo que `mean_kuncheva` seja calculado sempre que $0 < k < N_{\text{total}}$.
- **WHEN** `stats_config.json` contém uma lista `"pareto_objectives"` com 2 ou mais objetivos, **THE SYSTEM SHALL** construir `MultiObjectiveSpec` com todos os objetivos declarados durante `expml stats compute`.

### M8-07 — Hashes de Retomada, Nomenclatura de Células, Thread-Safety, `expml init` e Script TLC (`VAL-BUG-010`, `VAL-QUAL-003`, `VAL-BUG-011`)
- **WHEN** `save_cell_artifacts` e os loaders de `orchestration`/`reporting` persistem ou leem registros de células em `runs/cells/` (Decisão D2), **THE SYSTEM SHALL** utilizar exclusivamente o padrão canônico `cell_<m>__<s>__<f>.json`, sem suporte ou fallback para o formato legado `cell_cell_<m>__<s>__<f>.json`.
- **WHEN** `run_execution_matrix(..., resume=True)` valida `execution_state.json`, **THE SYSTEM SHALL** verificar a igualdade de `source_dataset_hash`, `partition_plan_id`, `scenarios_hash` e `models_hash`, lançando `DataIntegrityError` se qualquer um divergir.
- **WHEN** `instantiate_fresh_model` e `execute_single_cell` registram ou removem instâncias em `_ACTIVE_INSTANCES`, **THE SYSTEM SHALL** sincronizar o acesso com um `threading.Lock`.
- **WHEN** `expml init --task binary_classification` ou `multiclass_classification` é executado, **THE SYSTEM SHALL** gerar 2 modelos no catálogo inicial (`baseline_majoritario` e um modelo comparativo), permitindo comparações pareadas imediatas no `expml quickrun`.

---

## Acceptance Criteria Summary

| ID | Criterion | Verification Method |
| :--- | :--- | :--- |
| `AC-M8-01` | `tbl_family_a` e `tbl_family_g` contêm linhas reais (> 0 linhas) em experimento E2E completo sem mocks planos. | Teste de integração E2E (`pytest`). |
| `AC-M8-02` | `compute_correlation_ratio` e `compute_cramers_v` não lançam `TypeError` quando entradas categóricas possuem `None`. | Teste unitário (`pytest`). |
| `AC-M8-03` | `select_features_in_fold` no Nested CV não acessa `y_in_val` dos folds internos durante a busca de hiperparâmetros. | Teste metodológico anti-leakage (`pytest`). |
| `AC-M8-04` | Diretório gerado por `run_experiment` passa em `expml partition verify`, `expml run verify` e `expml report export`. | Teste de integração API→CLI (`pytest`). |
| `AC-M8-05` | `mean_kuncheva` é numérico ($\neq \text{None}$) quando $k < N_{\text{candidatos}}$ mesmo que todos os folds selecionem os mesmos $k$ atributos (`mean_kuncheva == 1.0`). | Teste unitário e CLI (`pytest`). |
| `AC-M8-06` | `resume=True` rejeita alteração em `scenarios.json` ou `models.json` via `scenarios_hash`/`models_hash`. | Teste unitário de retomada (`pytest`). |
| `AC-M8-07` | Artefatos de célula gravados e lidos exclusivamente como `runs/cells/cell_<m>__<s>__<f>.json` (sem `cell_cell_` e sem fallback legado). | Teste unitário de armazenamento e carregamento (`pytest`). |

---

## Requirement Traceability

| Requirement ID | Origin / Finding | Acceptance Criteria |
| :--- | :--- | :--- |
| M8-01 | `VAL-BUG-002` | `AC-M8-01` |
| M8-02 | `VAL-BUG-003` | `AC-M8-01` |
| M8-03 | `VAL-BUG-004` | `AC-M8-02` |
| M8-04 | `VAL-BUG-005`, `AD-028` (`D1`) | `AC-M8-03` |
| M8-05 | `VAL-BUG-007` | `AC-M8-04` |
| M8-06 | `VAL-BUG-009`, `VAL-ENH-004` | `AC-M8-05` |
| M8-07 | `VAL-BUG-010`, `AD-029` (`D2`), `VAL-QUAL-003`, `VAL-BUG-011` | `AC-M8-06`, `AC-M8-07` |
