# Feature: m5-3-oof-consolidation-stage-gate Specification

**Approved**: 2026-11-12 - user: "aprovado"

## Problem Statement

Na Etapa 4B do `experimental-ml-framework`, a execução matricial avalia os modelos em cada partição/fold individualmente gerando artefatos por célula (`cell_*.json` e `pred_*.json`). No entanto, para fins de comparação estatística rigorosa na Etapa 5 e publicação científica na Etapa 6, as predições individuais de cada fold precisam ser unificadas e estruturadas:
1. Em esquemas de validação cruzada ($K$-fold, estratificado ou agrupado), cada observação do conjunto de desenvolvimento é avaliada em exatamente um fold (ou múltiplas vezes em esquemas de bootstrap/repetição). A consolidação *out-of-fold* (OOF) deve mapear cada observação avaliada ao seu valor real, predição pontual ($\hat{\mu}_i$), desvio-padrão de comitê ($\hat{\sigma}_i$) e probabilidades/resíduos, preservando a ordenação canônica por `observation_id`.
2. A literatura experimental exige distinção explícita entre escopos de métricas (`RF4.7`): métricas calculadas em cada fold (`PER_FOLD`), resumos agregados entre folds (`FOLD_AGGREGATION`: média, desvio, mediana, IQR) e métricas globais computadas sobre o vetor concatenado out-of-fold (`POOLED_OOF`).
3. Em execuções com tolerância a falhas (`FAULT_TOLERANT`), caso um fold falhe, o framework deve consolidar as predições das dobras remanescentes com status `PARTIAL_COVERAGE`, documentando as observações ausentes sem abortar silenciosamente nem preencher com zeros artificiais.
4. Antes de autorizar a transição para a Etapa 5 (Consolidação Estatística e Comparações), o framework precisa de um portão de estágio formal (`verify_runs_gate`) que comprove a integridade completa dos artefatos persistidos (`execution_state.json`, células concluídas, predições, registros OOF) e valide os hashes cruzados em relação às etapas upstream (Etapas 1, 2, 3 e 4A).

## Goals

- [ ] Prover a estrutura imutável `ConsolidatedOofPredictions` e sua serialização/desserialização atômica (`save_oof_predictions`, `load_oof_predictions`) em `{run_dir}/oof/oof_{model_id}__{scenario_id}.json`.
- [ ] Implementar a função pura `consolidate_oof_predictions`, agregando os `PredictionRecord` das dobras de desenvolvimento, calculando estatísticas de comitê ($\hat{\mu}_i, \hat{\sigma}_i$) e probabilidades agrupadas.
- [ ] Avaliar métricas globais agrupadas (`POOLED_OOF`) e agregações inter-folds (`FOLD_AGGREGATION`) para todas as métricas aplicáveis da tarefa.
- [ ] Implementar a função `verify_runs_gate` em `experimental_ml.stages` com verificação de pré-requisitos upstream, integridade de diretório, conformidade de hashes e ausência de células incompletas.

## Out of Scope

- Interface de linha de comando `expml run` — escopo do Sub-marco M5.4.
- Testes de hipóteses estatísticas (Nadeau-Bengio, Wilcoxon pareado, Holm-Bonferroni) e Fronteira de Pareto — escopo do Marco M6.
- Geração de tabelas e relatórios gráficos — escopo do Marco M7.
- Adição de dependências de runtime além de `numpy>=1.24.0` (`XCUT-02`).

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Tratamento de falhas parciais em folds | Consolidar observações disponíveis com `MetricStatus.PARTIAL_COVERAGE` e alertas em warnings | Permite que a Etapa 5 analise cobertura parcial sem mascarar nem descartar dados válidos | y |
| Formato e localização das predições OOF | JSON atômico padronizado em `{run_dir}/oof/oof_{model_id}__{scenario_id}.json` | Conformidade estrita com `XCUT-02` e persistência transacional (`write_json_atomic`) | y |
| Cálculo de $\hat{\sigma}_i$ em fold único | $\hat{\sigma}_i$ reflete o desvio-padrão preditivo do modelo (`y_std`) se presente; caso contrário `None` (ou 0.0) | Em K-fold padrão cada observação só é avaliada uma vez; variância entre folds exige repetições | y |
| Ordenação das observações no registro OOF | Ordenação lexicográfica determinística por `observation_id` | Garante comparabilidade direta e determinismo bit a bit entre modelos e cenários | y |
| Validação de integridade no Stage Gate | Verificar existência de `execution_state.json`, ausência de status `PENDING`/`RUNNING`, e consistência de hashes | Garante que a Etapa 5 só ingira execuções finalizadas e sem corrupção | y |

**Open questions:** none - todas as decisões de produto e arquitetura foram alinhadas e confirmadas.

---

## User Stories

### US-M53-01 (Priority: P1) — Agregação e Estatísticas de Comitê Out-Of-Fold (ORCH-15, ORCH-16)

**User Story**: As an experimental ML researcher, I want to consolidate per-fold predictions into a unified out-of-fold record with committee statistics, so that each development observation has a single pooled prediction and uncertainty estimate.

**Why P1**: Necessary for evaluating pooled model performance across the development set and passing clean evaluation data to Stage 5.

#### Acceptance Criteria
- **AC-M53-01-01**: When consolidating predictions for a `(model_id, scenario_id)` configuration via `consolidate_oof_predictions`, the system SHALL aggregate all matching development fold `PredictionRecord` instances into a single `ConsolidatedOofPredictions` record.
- **AC-M53-01-02**: The system SHALL sort consolidated predictions canonically by `observation_id`.
- **AC-M53-01-03**: Where an observation is evaluated in multiple folds (e.g., bootstrap or repeated CV), the system SHALL compute committee mean $\hat{\mu}_i = \frac{1}{|F_i|} \sum_{f} \hat{y}_{i, f}$ and cross-fold sample standard deviation $\hat{\sigma}_i$.
- **AC-M53-01-04**: Where an observation is evaluated in exactly one fold, the system SHALL assign $\hat{\mu}_i = \hat{y}_i$ and retain the model predictive standard deviation $y\_std$ if present.
- **AC-M53-01-05**: Where the task is classification, the system SHALL average predicted class probabilities $\bar{P}(y=c \mid x_i) = \frac{1}{|F_i|} \sum_{f} P_f(y=c \mid x_i)$ across folds.

### US-M53-02 (Priority: P1) — Métricas Agrupadas (POOLED_OOF) e Inter-Folds (FOLD_AGGREGATION) (ORCH-17, ORCH-18, ORCH-19)

**User Story**: As an experimental ML researcher, I want to compute both pooled out-of-fold metrics and inter-fold metric aggregations, so that overall performance and fold-to-fold variability are explicitly captured and distinguished.

**Why P1**: Fulfills requirement `RF4.7` distinguishing metric evaluation scopes for rigorous statistical analysis.

#### Acceptance Criteria
- **AC-M53-02-01**: When computing pooled performance, the system SHALL evaluate applicable task metrics over the complete concatenated out-of-fold predictions with `MetricEvaluationScope.POOLED_OOF`.
- **AC-M53-02-02**: When aggregating fold results, the system SHALL compute summary statistics (mean, std, median, iqr) across individual fold metric evaluations with `AggregationScope.FOLD_AGGREGATION`.
- **AC-M53-02-03**: If any metric calculation encounters invalid values or division by zero, the system SHALL assign `MetricStatus.UNDEFINED_NAN` without raising an unhandled exception.
- **AC-M53-02-04**: The system SHALL store both `pooled_metrics` and `aggregated_metrics` in the `ConsolidatedOofPredictions` object.

### US-M53-03 (Priority: P1) — Persistência Atômica e Codecs de Predições OOF Consolidadas (ORCH-20)

**User Story**: As an experimental ML researcher, I want to serialize and load consolidated OOF predictions to and from disk atomically, so that Stage 5 can ingest consolidated results without recomputing predictions.

**Why P1**: Ensures transactional filesystem integrity and persistence parity across stages.

#### Acceptance Criteria
- **AC-M53-03-01**: The system SHALL provide `save_oof_predictions` to atomically write `{run_dir}/oof/oof_{model_id}__{scenario_id}.json` using `write_json_atomic`.
- **AC-M53-03-02**: The system SHALL provide `load_oof_predictions` to deserialize `{run_dir}/oof/oof_{model_id}__{scenario_id}.json` into a `ConsolidatedOofPredictions` instance.
- **AC-M53-03-03**: When round-tripping `ConsolidatedOofPredictions` through `oof_predictions_to_dict` and `oof_predictions_from_dict`, the system SHALL preserve all values, arrays, metrics, and metadata with exact fidelity.
- **AC-M53-03-04**: If `save_oof_predictions` is called with `overwrite=False` and the target file already exists, the system SHALL raise a `ConfigurationError`.

### US-M53-04 (Priority: P1) — Portão de Estágio da Etapa 4 (verify_runs_gate) (ORCH-21)

**User Story**: As an experimental ML researcher, I want a stage gate validator that verifies all Stage 4 execution artifacts before proceeding to Stage 5, so that incomplete, corrupted, or incompatible runs are immediately halted.

**Why P1**: Ensures rigorous stage transitions and prevents downstream statistical errors.

#### Acceptance Criteria
- **AC-M53-04-01**: When validating a run directory via `verify_runs_gate`, the system SHALL verify that upstream stage gates hold (`verify_preparation_gate`, `verify_partition_gate`, `verify_scenarios_gate`, and `verify_models_gate`).
- **AC-M53-04-02**: If `{run_dir}/execution_state.json` is missing or corrupted, the system SHALL raise a `DataIntegrityError`.
- **AC-M53-04-03**: If any cell in `execution_state.json` has a non-terminal status (`PENDING` or `RUNNING`), the system SHALL raise a `ContractViolationError`.
- **AC-M53-04-04**: If any completed cell in `execution_state.json` is missing its `cell_{cell_id}.json` or `pred_{cell_id}.json` file, the system SHALL raise a `DataIntegrityError`.
- **AC-M53-04-05**: If the `partition_plan_id` or `dataset_hash` in `execution_state.json` diverges from upstream artifacts, the system SHALL raise a `DataIntegrityError`.
- **AC-M53-04-06**: When all verification checks pass, `verify_runs_gate` SHALL return without error and return a summary of verified cells and OOF records.

### US-M53-05 (Priority: P2) — Suporte a Cobertura Parcial em FAULT_TOLERANT (ORCH-15, ORCH-21)

**User Story**: As an experimental ML researcher, I want the OOF consolidation to gracefully handle configurations with partial fold failures in fault-tolerant mode, so that surviving data can be investigated without crashing the pipeline.

**Why P2**: Enhances resilience during large exploratory matrix executions.

#### Acceptance Criteria
- **AC-M53-05-01**: Where some folds of a `(model_id, scenario_id)` configuration failed in `FAULT_TOLERANT` mode and at least one fold succeeded, the system SHALL consolidate available predictions and mark pooled metrics with `MetricStatus.PARTIAL_COVERAGE`.
- **AC-M53-05-02**: The system SHALL record the list of missing `observation_id` instances in the `ConsolidatedOofPredictions` warnings.
- **AC-M53-05-03**: If all folds of a configuration failed, the system SHALL raise a `DataIntegrityError` upon attempting OOF consolidation for that configuration.

---

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Component | Description |
| :--- | :--- | :--- | :--- |
| ORCH-15 | AC-M53-01-01, AC-M53-01-02, AC-M53-05-01, AC-M53-05-02 | `orchestration.oof` | Agregação canônica de predições OOF por configuração e tratamento de faltas |
| ORCH-16 | AC-M53-01-03, AC-M53-01-04, AC-M53-01-05 | `orchestration.oof` | Estatísticas de comitê ($\hat{\mu}_i$, $\hat{\sigma}_i$) e agregação de probabilidades |
| ORCH-17 | AC-M53-02-01, AC-M53-02-04 | `orchestration.oof` | Avaliação de métricas globais com escopo `POOLED_OOF` |
| ORCH-18 | AC-M53-02-02, AC-M53-02-04 | `orchestration.oof` | Agregação estatística inter-dobras com escopo `FOLD_AGGREGATION` |
| ORCH-19 | AC-M53-02-03 | `orchestration.oof` | Salvaguarda numérica e governança `UNDEFINED_NAN` (ADR-005) |
| ORCH-20 | AC-M53-03-01, AC-M53-03-02, AC-M53-03-03, AC-M53-03-04 | `orchestration.oof`, `orchestration.codecs` | Modelo `ConsolidatedOofPredictions`, codecs e persistência atômica |
| ORCH-21 | AC-M53-04-01, AC-M53-04-02, AC-M53-04-03, AC-M53-04-04, AC-M53-04-05, AC-M53-04-06, AC-M53-05-03 | `stages.stage_gates` | Portão de estágio `verify_runs_gate` e integridade cruzada de artefatos |
