# Roteiro de Validação e Aceitação — Marco M5.1 (Contratos e Execução Funcional de Célula)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M5.1 (`m5-1-cell-execution-contracts`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e integradores do subsistema de orquestração matricial do `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.orchestration`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e as exportações do módulo de orquestração estão íntegras:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de exportações dos símbolos públicos canônicos de orquestração
python -c "
import experimental_ml.orchestration as orch
print('Orchestration exportacoes publicas:', len(orch.__all__))
for sym in [
    'ExecutionStatus', 'ErrorPolicy', 'CellPhase',
    'CellId', 'TimingBreakdown', 'PredictionRecord', 'CellResultRecord',
    'execute_single_cell',
    'cell_result_to_dict', 'cell_result_from_dict',
    'prediction_record_to_dict', 'prediction_record_from_dict',
    'save_cell_artifacts', 'load_cell_artifacts',
]:
    assert sym in orch.__all__, f'Simbolo ausente: {sym}'
print('Simbolos canônicos de orquestracao validados com sucesso!')
"

# 3. Verificação de pureza de runtime (XCUT-02: zero dependências externas alem de numpy)
python -c "
import sys
import experimental_ml.orchestration
forbidden = ['scipy', 'pandas', 'sklearn', 'torch', 'qiskit']
loaded = [p for p in forbidden if p in sys.modules]
assert not loaded, f'Dependencias externas proibidas carregadas: {loaded}'
print('Pureza de runtime validada com sucesso (XCUT-02)!')
"
```

- **Resultado Esperado:** Mensagens confirmando a disponibilidade de todos os símbolos exportados e pureza de runtime.
- **Critério de Falha:** `ModuleNotFoundError`, `ImportError`, ausência de símbolos ou carregamento de bibliotecas externas pesadas.

---

## 2. Roteiro de Testes de Aceitação por Capacidade

### 2.1 Enums e Tipos Imutáveis (`ORCH-01`, `ORCH-02`, `ORCH-03`, `ORCH-04`)

```python
from experimental_ml.orchestration import (
    ExecutionStatus,
    ErrorPolicy,
    CellPhase,
    CellId,
    TimingBreakdown,
    PredictionRecord,
    CellResultRecord,
)
from experimental_ml.core.types import ModelId, ObservationId, PartitionPlanId, ScenarioId
import pytest

# 1. Enums canônicas
assert ExecutionStatus.COMPLETED.value == "COMPLETED"
assert ErrorPolicy.FAULT_TOLERANT.value == "FAULT_TOLERANT"
assert CellPhase.FIT.value == "FIT"

# 2. CellId com validação
cell_id = CellId("cell_001")
assert str(cell_id) == "cell_001"

# 3. TimingBreakdown imutável
timing = TimingBreakdown(
    data_extraction_time_s=0.01,
    fit_time_s=0.05,
    predict_time_s=0.02,
    total_cell_time_s=0.08,
)
assert timing.total_cell_time_s == 0.08

# 4. Imutabilidade comprovada
with pytest.raises(Exception):
    timing.total_cell_time_s = 1.0  # FrozenInstanceError
```

---

### 2.2 Execução Funcional de Célula e Isolamento Anti-Leakage (`ORCH-05`, `ORCH-06`)

```python
import numpy as np
from experimental_ml.core.enums import TaskType
from experimental_ml.core.types import ModelId, ScenarioId, PartitionPlanId
from experimental_ml.data import (
    ColumnSemanticType,
    DatasetSchemaSpec,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features.scenarios import FeatureScenario, ScenarioMode
from experimental_ml.models import (
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    resolve_estimator_factory,
)
from experimental_ml.orchestration import execute_single_cell, ExecutionStatus
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)

# 1. Dataset sintético
raw_data = {
    "f1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    "target": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
}
schema = DatasetSchemaSpec(
    target_col="target",
    task_type=TaskType.REGRESSION,
    column_semantic_types={
        "f1": ColumnSemanticType.NUMERIC_CONTINUOUS,
        "target": ColumnSemanticType.NUMERIC_CONTINUOUS,
    },
)
bundle = load_dataset(raw_data, schema)
profile = profile_dataset(bundle)
prep_plan = create_preparation_plan(profile, rules=[])
view = sanitize_dataset(bundle, profile, prep_plan)

# 2. Fold partition
fold = FoldPartition(
    fold_index=0,
    train_ids=view.observation_ids[:4],
    val_ids=view.observation_ids[4:],
)
partition_plan = PartitionPlan(
    plan_id=PartitionPlanId("plan_test"),
    source_dataset_hash=view.dataset_hash,
    regime=EvaluationRegime.CV_ONLY,
    strategy=PartitionStrategy.KFOLD,
    development_ids=view.observation_ids,
    holdout_ids=(),
    folds=(fold,),
    config=PartitionConfig(
        strategy=PartitionStrategy.KFOLD,
        regime=EvaluationRegime.CV_ONLY,
        n_splits=2,
        master_seed=42,
    ),
)

# 3. Cenário e Modelo
scenario = FeatureScenario(
    scenario_id=ScenarioId("sc_fixed"),
    name="Fixed Scenario",
    description="All features fixed",
    scientific_justification="Baseline set",
    mode=ScenarioMode.FIXED,
    selected_features=("f1",),
)
model_spec = ModelSpec(
    model_id=ModelId("dummy_mean"),
    display_name="Dummy Mean Baseline",
    family=ModelFamily.BASELINE,
    capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
    estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
    description="Baseline estimator",
    scientific_justification="Reference",
)

# 4. Execução da célula
cell_result, pred_record = execute_single_cell(
    model_spec=model_spec,
    scenario=scenario,
    fold=fold,
    sanitized_view=view,
    partition_plan=partition_plan,
    metrics=("rmse",),
)

assert cell_result.status == ExecutionStatus.COMPLETED
assert pred_record is not None
assert len(pred_record.y_pred) == 2
```

---

### 2.3 Resiliência e Políticas de Falha (`ORCH-07`)

```python
from experimental_ml.orchestration import execute_single_cell, ErrorPolicy, ExecutionStatus

# Modelo que falha intencionalmente na fase de predição
failing_spec = ModelSpec(
    model_id=ModelId("failing_model"),
    display_name="Failing Model",
    family=ModelFamily.BASELINE,
    capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
    estimator_factory=lambda seed: FailingEstimator(),
    description="Model that raises RuntimeError in predict",
    scientific_justification="Failure policy testing",
)

# Modo FAULT_TOLERANT: captura o erro e marca FAILED sem abortar o processo
res, pred = execute_single_cell(
    model_spec=failing_spec,
    scenario=scenario,
    fold=fold,
    sanitized_view=view,
    partition_plan=partition_plan,
    error_policy=ErrorPolicy.FAULT_TOLERANT,
)
assert res.status == ExecutionStatus.FAILED
assert res.error_phase == CellPhase.PREDICT
assert res.error_type == "RuntimeError"
assert pred is None
assert res.metrics == {}  # Sem coerção para 0.0

# Modo FAIL_FAST: propaga a exceção imediatamente
with pytest.raises(RuntimeError):
    execute_single_cell(
        model_spec=failing_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=partition_plan,
        error_policy=ErrorPolicy.FAIL_FAST,
    )
```

---

### 2.4 Codecs e Persistência Atômica de Artefatos (`ORCH-08`)

```python
from pathlib import Path
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.orchestration import (
    save_cell_artifacts,
    load_cell_artifacts,
    cell_result_to_dict,
    cell_result_from_dict,
)

# Serialização em dicionário e round-trip
d = cell_result_to_dict(cell_result)
reconstructed = cell_result_from_dict(d)
assert reconstructed.cell_id == cell_result.cell_id

# Persistência atômica
run_dir = Path("/tmp/test_expml_run")
cell_path, pred_path = save_cell_artifacts(cell_result, pred_record, run_dir, overwrite=True)
assert cell_path.exists()
assert pred_path.exists()

# Tentativa de sobrescrita com overwrite=False deve falhar
with pytest.raises(ConfigurationError):
    save_cell_artifacts(cell_result, pred_record, run_dir, overwrite=False)

# Carga de artefatos
loaded_result, loaded_pred = load_cell_artifacts(cell_result.cell_id, run_dir)
assert loaded_result.cell_id == cell_result.cell_id
assert loaded_pred.observation_ids == pred_record.observation_ids
```
