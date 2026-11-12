# Design: m5-3-oof-consolidation-stage-gate

## 1. Visão Geral da Arquitetura

O sub-marco M5.3 implementa a consolidação das predições *out-of-fold* (OOF) do conjunto de desenvolvimento e o portão formal de estágio da Etapa 4 (`verify_runs_gate`). Ele fecha a lacuna entre a execução atômica matricial de células (Etapa 4B) e a consolidação/comparação estatística rigorosa (Etapa 5).

A arquitetura organiza-se em dois módulos principais:
1. `src/experimental_ml/orchestration/oof.py`: estrutura declarativa `ConsolidatedOofPredictions`, consolidação funcional pura (`consolidate_oof_predictions`), cálculo de comitês ($\hat{\mu}_i, \hat{\sigma}_i$), avaliação de métricas com separação explícita de escopos (`POOLED_OOF` vs `FOLD_AGGREGATION`), codecs e persistência atômica sob `{run_dir}/oof/`.
2. `src/experimental_ml/stages/stage_gates.py`: portão de integridade `verify_runs_gate`, validando pré-requisitos upstream (Etapas 1 a 4A), integridade de `execution_state.json`, presença e correspondência de todos os artefatos de células e OOF, e alinhamento de hashes criptográficos.

```
+-----------------------------------------------------------------------------------------+
|                                    orchestration.oof                                    |
|                                                                                         |
|   +--------------------+     +--------------------+                                     |
|   | PredictionRecord 1 | ... | PredictionRecord K |  (de cada fold de desenvolvimento)  |
|   +---------+----------+     +---------+----------+                                     |
|             |                          |                                                |
|             +------------+-------------+                                                |
|                          v                                                              |
|        +-----------------------------------+                                            |
|        |    consolidate_oof_predictions    |                                            |
|        |  - Ordenação por observation_id   |                                            |
|        |  - Comitê: \hat{\mu}_i, \hat{\sigma}_i |                                       |
|        |  - Probabilidades Médias (classif)|                                            |
|        |  - POOLED_OOF & FOLD_AGGREGATION  |                                            |
|        +-----------------+-----------------+                                            |
|                          |                                                              |
|                          v                                                              |
|          +-------------------------------+                                              |
|          |  ConsolidatedOofPredictions   |                                              |
|          +---------------+---------------+                                              |
|                          |                                                              |
|                          v                                                              |
|          +-------------------------------+                                              |
|          | save_oof_predictions (atomic) |                                              |
|          | {run_dir}/oof/oof_<m>__<c>.json|                                             |
|          +-------------------------------+                                              |
+-----------------------------------------------------------------------------------------+
                               |
                               v
+-----------------------------------------------------------------------------------------+
|                                  stages.stage_gates                                     |
|                                                                                         |
|          +-------------------------------+                                              |
|          |       verify_runs_gate        |                                              |
|          |  - Upstream Gates (1, 2, 3, 4)|                                              |
|          |  - execution_state.json válido|                                              |
|          |  - Nenhum PENDING / RUNNING   |                                              |
|          |  - Células e Predições em disco|                                             |
|          |  - Arquivos OOF em disco      |                                              |
|          |  - Hashes alinhados (SHA-256) |                                              |
|          +-------------------------------+                                              |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Modelagem de Dados e Tipos (`oof.py`)

### 2.1 Modelo Declarativo `ConsolidatedOofPredictions`

```python
@dataclass(frozen=True, slots=True)
class ConsolidatedOofPredictions:
    """Predições consolidadas out-of-fold para uma configuração (modelo, cenário)."""
    model_id: ModelId
    scenario_id: ScenarioId
    task_type: TaskType
    observation_ids: tuple[ObservationId, ...]
    y_true: tuple[float, ...]
    y_pred: tuple[float, ...]
    y_std: tuple[float, ...] | None = None
    y_proba: tuple[tuple[float, ...], ...] | None = None
    residuals: tuple[float, ...] | None = None
    pooled_metrics: Mapping[str, MetricValue] = field(default_factory=dict)
    aggregated_metrics: Mapping[str, AggregatedMetricValue] = field(default_factory=dict)
    fold_ids: tuple[str, ...] = field(default_factory=tuple)
    coverage: float = 1.0
    status: MetricStatus = MetricStatus.VALID
    warnings: tuple[str, ...] = field(default_factory=tuple)
```

Invariantes e Validações:
- `observation_ids`, `y_true`, `y_pred` possuem o mesmo comprimento $N \ge 1$.
- Ordenação canônica compulsória por `observation_id` (ordenação lexicográfica).
- Se `y_std` estiver presente, seu comprimento é $N$.
- Se `y_proba` estiver presente, seu comprimento é $N$ e cada linha é uma tupla de probabilidades.
- Se `residuals` estiver presente, seu comprimento é $N$.
- `pooled_metrics` e `aggregated_metrics` são convertidos para `MappingProxyType`.

---

## 3. Algoritmo de Consolidação (`consolidate_oof_predictions`)

1. **Agrupamento por Observação**:
   - Para cada `PredictionRecord` fornecido, iterar sobre `(obs_id, y_t, y_p, y_s, y_prob)` associando ao `obs_id`.
   - Se uma observação aparecer em mais de um fold (ex: bootstrap, repetições de CV):
     $$\hat{\mu}_i = \frac{1}{|F_i|} \sum_{f \in F_i} \hat{y}_{i, f}$$
     $$\hat{\sigma}_i = \sqrt{\frac{1}{|F_i| - 1} \sum_{f \in F_i} (\hat{y}_{i, f} - \hat{\mu}_i)^2} \quad (|F_i| > 1)$$
   - Se aparecer em apenas um fold ($|F_i| = 1$):
     $$\hat{\mu}_i = \hat{y}_{i}, \quad \hat{\sigma}_i = y\_std_i \text{ (se fornecido, senão None)}$$
   - Probabilidades (para classificação):
     $$\bar{P}(y = c \mid x_i) = \frac{1}{|F_i|} \sum_{f \in F_i} P_f(y = c \mid x_i)$$
   - Resíduo:
     $$e_i = y_i - \hat{\mu}_i$$

2. **Ordenação Canônica**:
   - Ordenar todas as observações pelo identificador `observation_id`.

3. **Cálculo de Métricas Agrupadas (`MetricEvaluationScope.POOLED_OOF`)**:
   - Extrair vetores agrupados $\mathbf{y}_{\text{true}}$ e $\hat{\mathbf{y}}_{\text{pred}}$.
   - Avaliar todas as métricas aplicáveis ao `task_type` (ex: RMSE, MAE, R2 para regressão; Accuracy, F1, LogLoss para classificação).
   - Rotular cada métrica com `scope = MetricEvaluationScope.POOLED_OOF`.

4. **Agregação Inter-Dobra (`AggregationScope.FOLD_AGGREGATION`)**:
   - A partir dos `CellResultRecord` dos folds concluídos, agrupar as métricas de mesmo `metric_id`.
   - Executar `aggregate_fold_metrics` de `experimental_ml.metrics.aggregation` para calcular média, desvio, mediana e IQR inter-dobras.

5. **Tratamento de Folds com Falha (`PARTIAL_COVERAGE`)**:
   - Se `target_observation_ids` for fornecido e algumas observações estiverem ausentes:
     $$\text{coverage} = \frac{N_{\text{observadas}}}{N_{\text{esperadas}}} < 1.0$$
     $$\text{status} = \text{MetricStatus.PARTIAL_COVERAGE}$$
     Emitir aviso com lista de observações faltantes.

---

## 4. Persistência Atômica e Codecs

- Caminho canônico: `{run_dir}/oof/oof_{model_id}__{scenario_id}.json`.
- `save_oof_predictions(oof_record, run_dir, *, overwrite=False)`:
  - Cria diretório `{run_dir}/oof` se não existir.
  - Verifica se arquivo já existe (lança `ConfigurationError` se `overwrite=False`).
  - Grava via `write_json_atomic`.
- `load_oof_predictions(model_id, scenario_id, run_dir)`:
  - Lê e desserializa o arquivo JSON via `oof_predictions_from_dict`.
- Codecs:
  - `oof_predictions_to_dict`: serializa `ConsolidatedOofPredictions` para dicionário compatível com JSON.
  - `oof_predictions_from_dict`: desserializa dicionário restaurando tipos e tuplas imutáveis.

---

## 5. Portão de Estágio da Etapa 4 (`verify_runs_gate`)

A função `verify_runs_gate(target: Path | str)` valida:
1. **Pré-requisitos Upstream (Portões 1, 2, 3 e 4A)**:
   - Invoca `verify_preparation_gate`, `verify_partition_gate`, `verify_scenarios_gate` e `verify_models_gate`.
2. **Existência do Estado de Execução**:
   - `{run_dir}/execution_state.json` deve existir e ser desserializável via `load_execution_state`.
3. **Ausência de Células Não-Terminais**:
   - Nenhuma célula pode estar em estado `PENDING` ou `RUNNING`. Todas devem ser `COMPLETED`, `FAILED` ou `CANCELLED`.
4. **Verificação Física de Artefatos**:
   - Para cada célula `COMPLETED`: `{run_dir}/cells/cell_{cell_id}.json` e `{run_dir}/predictions/pred_{cell_id}.json` devem existir.
   - Para cada célula `FAILED`: `{run_dir}/cells/cell_{cell_id}.json` deve existir e conter campos de erro.
5. **Verificação de Registros OOF**:
   - Para cada configuração `(model_id, scenario_id)` com ao menos uma célula `COMPLETED`, o arquivo `{run_dir}/oof/oof_{model_id}__{scenario_id}.json` deve existir e ser válido.
6. **Alinhamento Transversal de Hashes**:
   - `dataset_hash` do estado deve coincidir com o hash da visão saneada / profile.
   - `partition_plan_id` do estado deve coincidir com `partition_plan.json`.

---

## 6. Riscos, Preocupações e Mitigações

1. **Divisão por Zero / Variância Nula**:
   - *Risco*: Em amostra única ($|F_i| = 1$), cálculo ingênuo de desvio com $N - 1$ divide por zero.
   - *Mitigação*: Algoritmo detecta $|F_i| = 1$ e define desvio amostral como 0.0 ou herda `y_std` do modelo.
2. **Memória em Bases Extensas**:
   - *Risco*: Vetores grandes de predições podem ocupar memória excessiva se duplicados.
   - *Mitigação*: Utiliza tuplas imutáveis de primitivos nativos e NumPy vetorizado para cálculo de métricas.
3. **Pureza de Runtime (`XCUT-02`)**:
   - *Risco*: Dependência acidental de `pandas` ou `scipy`.
   - *Mitigação*: Uso estrito da biblioteca padrão Python e `numpy>=1.24.0`.
