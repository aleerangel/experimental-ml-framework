# Feature: m5-1-cell-execution-contracts

**Approved**: 2026-11-12 - user: "Aprovado"

## Problem Statement

Na arquitetura do `experimental-ml-framework`, a Etapa 4B (Execução Matricial e Persistência) é responsável por coordenar a avaliação de cada célula da grade experimental tridimensional $\text{Célula}(m, c, f) = \text{Modelo } m \in \mathcal{M} \times \text{Cenário } c \in \mathcal{C} \times \text{Fold } f \in \mathcal{F}$.

Atualmente, o framework consolidou as Fundações Transversais (M1), os Dados e Particionamento Compartilhado (M2), os Cenários de Atributos e Seleção Intra-fold (M3) e os Contratos de Modelos, Pré-processamento em 2 Camadas e Tuning Aninhado (M4). No entanto, não há ainda no subsistema `src/experimental_ml/orchestration/` contratos e funções unificadas para:
1. Modelar a identidade e o ciclo de vida de uma célula de execução unitária (`CellId`, `ExecutionStatus`, `CellPhase`, `ErrorPolicy`).
2. Medir e segregar de forma auditável e desagregada os tempos de execução por subetapa (`TimingBreakdown`), diferenciando extração de dados, pré-processamento, seleção de atributos, tuning aninhado, ajuste do modelo, inferência e cálculo de métricas.
3. Coletar e estruturar predições individuais da partição de validação indexadas por `ObservationId` (`PredictionRecord`), incluindo predição pontual (`y_pred`), incerteza individual (`y_std`), probabilidades de classe (`y_proba`) e resíduos.
4. Consolidar os resultados completos de uma célula (`CellResultRecord`), registrando status, atributos efetivamente selecionados, parâmetros finais $\theta^*$, tempos, diagnósticos internos e dicionário tipado de métricas avaliadas.
5. Executar de forma puramente funcional uma célula experimental (`execute_single_cell`), orquestrando em sequência rigorosa a extração dos dados do fold, seleção de atributos, tuning aninhado se dinâmico, ajuste do pré-processamento em duas camadas, instanciação fresca e treino do modelo, inferência e avaliação, garantindo total isolamento anti-leakage (`CA-E4B-01`).
6. Implementar políticas de tratamento de falhas por célula (`FAULT_TOLERANT` vs `FAIL_FAST`), capturando exceções, registrando a fase exata do erro, mensagem e traceback, sem derrubar a execução e sem converter métricas para zero (`CA-E4B-02`).
7. Serializar e persistir atomicamente os artefatos de célula em formato JSON determinístico sem dependências adicionais de runtime (`XCUT-02`).

Este sub-marco M5.1 estabelece as estruturas de dados, os contratos e o motor de execução unitário de célula, viabilizando o orquestrador matricial e checkpoint/resume (M5.2), a consolidação out-of-fold e portão de estágio (M5.3) e a CLI `expml run` (M5.4).

## Out of Scope

- Orquestração de loops de múltiplos modelos, cenários e folds em matriz global — escopo do Sub-marco M5.2 (`run_experiment_matrix`).
- Controle de paralelismo em dois níveis (`outer_n_jobs`, `inner_model_threads`) — escopo do Sub-marco M5.2.
- Gerenciamento de estado global da matriz (`execution_state.json`) e retomada (*Checkpoint & Resume*) — escopo do Sub-marco M5.2 (`resume_experiment_matrix`).
- Consolidação global out-of-fold (`consolidate_oof_predictions`) e estatísticas de comitê ($\hat{\mu}_i, \hat{\sigma}_i$) — escopo do Sub-marco M5.3.
- Portão de estágio `verify_runs_gate` em `experimental_ml.stages` — escopo do Sub-marco M5.3.
- Interface de linha de comando `expml run ...` — escopo do Sub-marco M5.4.
- Inclusão de novas dependências obrigatórias de runtime além de `numpy>=1.24.0` (`XCUT-02`).

## Assumptions & Open Questions

**Open questions:** none - os contratos de execução de células e modelo de dados de resultados já foram formalmente especificados na SRS (RF4.1 a RF4.4) e na Arquitetura (Seção 3.4).

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Dependência de runtime do subsistema de orquestração | `numpy>=1.24.0` e biblioteca padrão Python exclusivamente | Atende a `XCUT-02` e `RNF07`, garantindo que a execução e persistência de células opere sem dependência mandatória de pandas ou pyarrow |
| Formato de persistência das predições por célula | JSON determinístico lossless via `write_json_atomic` (`pred_<cell_id>.json`) | Mantém determinismo binário, interoperabilidade e independência de bibliotecas colunares adicionais na Onda 1 |
| Nomenclatura canônica do identificador de célula (`CellId`) | Formato determinístico estruturado `cell_{model_id}_{scenario_id}_{fold_id}` | Facilita a auditoria humana, ordenação lexicográfica estável e indexação unívoca no sistema de arquivos |
| Isolamento estrito de vazamento de dados (`CA-E4B-01`) | O conjunto `X_val, y_val` só é consultado nas etapas de transformação pré-ajustada, predição e cálculo de métricas | Garante que seleção de atributos, tuning aninhado e pré-processamento em duas camadas ajustem estatísticas exclusivamente sobre `X_train, y_train` |
| Tratamento de falhas em modo `FAULT_TOLERANT` | Grava `CellResultRecord` com `status = FAILED`, `error_phase`, `error_type`, `error_message`, `error_traceback` e `metrics = {}` | Evita coerção para zero de métricas e preserva informações detalhadas para diagnóstico e auditoria pós-execução |
| Desagregação de tempos em `TimingBreakdown` | Medição em segundos via `time.perf_counter()` para cada fase da célula | Permite análise posterior de custo computacional e identificação precisa de gargalos na Fronteira de Pareto (Etapa 5) |

## User Stories

### US-M51-01 (Priority: P1) — Estruturas Imutáveis e Identificadores da Célula
As an experimental ML researcher,  
I want immutable domain types, enumerations, and data structures for experimental execution cells,  
So that cell execution, timing breakdowns, prediction records, and execution states are typed, deterministic, and auditable.

#### Acceptance Criteria
- **AC-M51-01-01**: When creating an `ExecutionStatus`, the system SHALL support the members `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, and `CANCELLED`.
- **AC-M51-01-02**: When creating an `ErrorPolicy`, the system SHALL support the members `FAULT_TOLERANT` and `FAIL_FAST`.
- **AC-M51-01-03**: When creating a `CellPhase`, the system SHALL support canonical sub-phases `DATA_EXTRACTION`, `FEATURE_SELECTION`, `PREPROCESSING_L1`, `HYPERPARAMETER_TUNING`, `PREPROCESSING_L2`, `MODEL_FIT`, `PREDICTION`, and `METRIC_COMPUTATION`.
- **AC-M51-01-04**: When instantiating `CellId`, the system SHALL enforce non-empty string validation and reject whitespace or control characters.
- **AC-M51-01-05**: When creating a `TimingBreakdown`, the system SHALL store non-negative float durations in seconds for `data_extraction_time_s`, `preprocessing_time_s`, `feature_selection_time_s`, `tuning_time_s`, `fit_time_s`, `predict_time_s`, `evaluation_time_s`, and `total_cell_time_s`.
- **AC-M51-01-06**: When creating a `PredictionRecord`, the system SHALL store `observation_ids: tuple[ObservationId, ...]`, `y_true: tuple[float, ...]`, `y_pred: tuple[float, ...]`, optional `y_std: tuple[float, ...] | None`, optional `y_proba: tuple[tuple[float, ...], ...] | None`, and optional `residuals: tuple[float, ...] | None`.
- **AC-M51-01-07**: When instantiating `PredictionRecord`, the system SHALL validate that `observation_ids`, `y_true`, and `y_pred` have matching lengths and contain no unmapped NaN values in `observation_ids`.
- **AC-M51-01-08**: When creating a `CellResultRecord`, the system SHALL encapsulate `cell_id`, `experiment_id`, `partition_plan_id`, `model_id`, `scenario_id`, `fold_id`, `status: ExecutionStatus`, `selected_features: tuple[str, ...]`, `effective_parameters: Mapping[str, Any]`, `timing: TimingBreakdown`, `metrics: Mapping[str, MetricValue]`, optional `diagnostics`, and optional error fields (`error_type`, `error_message`, `error_phase`, `error_traceback`).
- **AC-M51-01-09**: When modifying any attribute of `TimingBreakdown`, `PredictionRecord`, or `CellResultRecord`, the system SHALL raise `FrozenInstanceError` preserving immutability.

---

### US-M51-02 (Priority: P1) — Execução Funcional de Célula Unitária e Isolamento Científico
As an experimental ML researcher,  
I want a pure functional executor for a single experimental cell,  
So that feature selection, tuning, preprocessing, model fitting, prediction, and evaluation occur in strict sequence without data leakage.

#### Acceptance Criteria
- **AC-M51-02-01**: When invoking `execute_single_cell`, the system SHALL slice `X_train, y_train` and `X_val, y_val` from `SanitizedDatasetView` using exclusively the `train_ids` and `val_ids` declared in the target fold of `PartitionPlan`.
- **AC-M51-02-02**: When the target scenario declares `mode = "DYNAMIC"`, the system SHALL execute `select_features_in_fold` strictly on `X_train, y_train` and project `X_val` using `apply_feature_selection` without consulting `y_val`.
- **AC-M51-02-03**: When the target model declares a `HyperparameterSearchSpec` with strategy other than `FIXED`, the system SHALL execute `run_nested_tuning` confined strictly to `X_train, y_train` and apply the selected best parameters $\theta^*$ to the model specification.
- **AC-M51-02-04**: When the target model declares a `TwoLayerPreprocessingSpec`, the system SHALL fit `fit_two_layer_preprocessing` strictly on `X_train` and project `X_val` using `apply_two_layer_preprocessing` without leakage from evaluation data.
- **AC-M51-02-05**: When instantiating the estimator for the cell, the system SHALL call `instantiate_fresh_model` passing a deterministic seed derived from the cell context, ensuring no state contamination from prior folds or cells.
- **AC-M51-02-06**: When executing model fitting and prediction, the system SHALL invoke `fit_model` on transformed `X_train, y_train` and `predict_model` on transformed `X_val`, extracting internal diagnostics via `extract_model_diagnostics`.
- **AC-M51-02-07**: When computing cell metrics, the system SHALL evaluate all requested metrics from `METRICS_CATALOG` comparing `y_val` with the outputs of `predict_model` and preserving `MetricStatus.UNDEFINED_NAN` where degenerate.
- **AC-M51-02-08**: When all cell phases complete successfully, the system SHALL return a `CellResultRecord` with `status = ExecutionStatus.COMPLETED` and a populated `PredictionRecord`.
- **AC-M51-02-09**: When tested with synthetic perturbed `y_val`, the parameters fitted during feature selection, preprocessing, nested tuning, and model training SHALL remain bit-for-bit identical, demonstrating anti-leakage compliance (`CA-E4B-01`).

---

### US-M51-03 (Priority: P1) — Tratamento Resiliente de Falhas por Célula
As an experimental ML researcher,  
I want cell execution to capture exceptions and classify failure phases according to the configured error policy,  
So that matrix runs are resilient to isolated convergence or numeric failures without masking errors or corrupting metrics.

#### Acceptance Criteria
- **AC-M51-03-01**: When an unhandled exception occurs in any phase of `execute_single_cell` under `error_policy = ErrorPolicy.FAULT_TOLERANT`, the system SHALL catch the exception without aborting process execution.
- **AC-M51-03-02**: When an exception is caught under `ErrorPolicy.FAULT_TOLERANT`, the system SHALL set `status = ExecutionStatus.FAILED` in `CellResultRecord`.
- **AC-M51-03-03**: When an exception is caught under `ErrorPolicy.FAULT_TOLERANT`, the system SHALL populate `error_phase` with the exact `CellPhase` during which the failure occurred.
- **AC-M51-03-04**: When an exception is caught under `ErrorPolicy.FAULT_TOLERANT`, the system SHALL populate `error_type`, `error_message`, and `error_traceback` with the exception details.
- **AC-M51-03-05**: When an exception is caught under `ErrorPolicy.FAULT_TOLERANT`, the system SHALL return `metrics = {}` and `prediction_record = None`, never coercing failed metrics to `0.0`.
- **AC-M51-03-06**: When an unhandled exception occurs in `execute_single_cell` under `error_policy = ErrorPolicy.FAIL_FAST`, the system SHALL propagate the exception immediately.

---

### US-M51-04 (Priority: P2) — Codecs de Serialização e Persistência Atômica de Célula
As an experimental ML researcher,  
I want deterministic codecs and atomic file persistence for cell results and predictions,  
So that individual cell outcomes can be stored, verified, and reloaded incrementally without data corruption.

#### Acceptance Criteria
- **AC-M51-04-01**: When converting a `CellResultRecord` to dictionary via `cell_result_to_dict`, the system SHALL produce a JSON-serializable dictionary preserving all identifiers, status, timing, parameters, metrics, and error fields.
- **AC-M51-04-02**: When reconstructing a `CellResultRecord` from dictionary via `cell_result_from_dict`, the system SHALL restore an equivalent record with identical values and types (round-trip fidelity).
- **AC-M51-04-03**: When converting a `PredictionRecord` to dictionary via `prediction_record_to_dict`, the system SHALL produce a JSON-serializable dictionary preserving `observation_ids`, `y_true`, `y_pred`, `y_std`, `y_proba`, and `residuals`.
- **AC-M51-04-04**: When reconstructing a `PredictionRecord` from dictionary via `prediction_record_from_dict`, the system SHALL restore an equivalent record with identical values and types.
- **AC-M51-04-05**: When saving cell artifacts via `save_cell_artifacts`, the system SHALL atomically write `runs/cells/cell_<cell_id>.json` and `runs/predictions/pred_<cell_id>.json` using temporary files and atomic replace (`write_json_atomic`).
- **AC-M51-04-06**: When target files already exist and `overwrite = False`, `save_cell_artifacts` SHALL raise `ConfigurationError` preventing accidental data destruction.

---

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Component | Description |
| :--- | :--- | :--- | :--- |
| ORCH-01 | AC-M51-01-01, AC-M51-01-02, AC-M51-01-03 | `orchestration.types` | Enums canônicas de execução (`ExecutionStatus`, `ErrorPolicy`, `CellPhase`) |
| ORCH-02 | AC-M51-01-04, AC-M51-01-05 | `orchestration.types` | Identificador `CellId` e estrutura de medição desagregada `TimingBreakdown` |
| ORCH-03 | AC-M51-01-06, AC-M51-01-07 | `orchestration.types` | Estrutura imutável de predições indexadas `PredictionRecord` |
| ORCH-04 | AC-M51-01-08, AC-M51-01-09 | `orchestration.types` | Estrutura imutável de resultado consolidado `CellResultRecord` |
| ORCH-05 | AC-M51-02-01, AC-M51-02-02, AC-M51-02-03, AC-M51-02-04 | `orchestration.execution` | Execução puramente funcional de célula com isolamento intra-fold anti-leakage |
| ORCH-06 | AC-M51-02-05, AC-M51-02-06, AC-M51-02-07, AC-M51-02-08, AC-M51-02-09 | `orchestration.execution` | Instanciação fresca, ajuste, inferência, diagnósticos e avaliação métrica |
| ORCH-07 | AC-M51-03-01, AC-M51-03-02, AC-M51-03-03, AC-M51-03-04, AC-M51-03-05, AC-M51-03-06 | `orchestration.execution` | Políticas de erro `FAULT_TOLERANT` e `FAIL_FAST` com registro detalhado de falhas |
| ORCH-08 | AC-M51-04-01, AC-M51-04-02, AC-M51-04-03, AC-M51-04-04, AC-M51-04-05, AC-M51-04-06 | `orchestration.codecs`, `orchestration.storage` | Codecs determinísticos e persistência atômica de artefatos de célula |
