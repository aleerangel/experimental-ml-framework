# Roteiro de Validação e Aceitação — Marco M5.3 (Consolidação OOF e Portão da Etapa 4)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M5.3 (`m5-3-oof-consolidation-stage-gate`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e integradores do subsistema de consolidação out-of-fold e portões de estágio do `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.orchestration` e `experimental_ml.stages`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e as exportações públicas estão íntegras:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de exportações dos símbolos públicos de OOF e portão da etapa 4
python -c "
import experimental_ml.orchestration as orch
import experimental_ml.stages as stages

oof_symbols = [
    'ConsolidatedOofPredictions', 'save_oof_predictions', 'load_oof_predictions',
    'oof_predictions_to_dict', 'oof_predictions_from_dict',
    'aggregated_metric_value_to_dict', 'aggregated_metric_value_from_dict',
    'consolidate_oof_predictions', 'consolidate_matrix_oof'
]
for sym in oof_symbols:
    assert sym in orch.__all__, f'Símbolo OOF ausente em orchestration: {sym}'

assert 'verify_runs_gate' in stages.__all__, 'verify_runs_gate ausente em stages'
print('Símbolos públicos M5.3 validados com sucesso!')
"

# 3. Verificação de pureza de runtime (XCUT-02: zero dependências externas além de numpy)
python -c "
import sys
import experimental_ml.orchestration
import experimental_ml.stages

forbidden = ['scipy', 'pandas', 'sklearn', 'torch', 'qiskit', 'pyarrow']
loaded = [p for p in forbidden if p in sys.modules]
assert not loaded, f'Dependências externas proibidas carregadas: {loaded}'
print('Pureza de runtime validada com sucesso (XCUT-02)!')
"
```

---

## 2. Roteiro de Testes de Aceitação por Capacidade

### 2.1 Agregação Canônica OOF e Estatísticas de Comitê (`ORCH-15`, `ORCH-16`)

Valida a consolidação de predições de dobras de desenvolvimento, ordenação canônica por `observation_id`, estatísticas de comitê ($\hat{\mu}_i, \hat{\sigma}_i$) em múltiplas avaliações e probabilidades médias em classificação:

```python
import numpy as np
from experimental_ml.core.types import ModelId, ScenarioId
from experimental_ml.orchestration import (
    PredictionRecord,
    consolidate_oof_predictions,
)

# 1. Criação de registros de predições de teste
pred_fold0 = PredictionRecord(
    model_id=ModelId("ridge"),
    scenario_id=ScenarioId("sc1"),
    fold_id="fold_0",
    observation_ids=("obs_2", "obs_1"),
    y_true=(20.0, 10.0),
    y_pred=(21.0, 10.5),
    y_std=(0.5, 0.4),
)
pred_fold1 = PredictionRecord(
    model_id=ModelId("ridge"),
    scenario_id=ScenarioId("sc1"),
    fold_id="fold_1",
    observation_ids=("obs_1", "obs_3"),
    y_true=(10.0, 30.0),
    y_pred=(11.5, 29.0),
    y_std=(0.3, 0.6),
)

# 2. Consolidação
oof = consolidate_oof_predictions(
    model_id=ModelId("ridge"),
    scenario_id=ScenarioId("sc1"),
    prediction_records=[pred_fold0, pred_fold1],
    target_observation_ids={"obs_1", "obs_2", "obs_3"},
)

# 3. Asserções
assert oof.observation_ids == ("obs_1", "obs_2", "obs_3"), "Ordenação lexicográfica canônica violada"
assert oof.y_true == (10.0, 20.0, 30.0)
# obs_1: média entre 10.5 e 11.5 -> 11.0
assert oof.y_pred[0] == 11.0
assert oof.y_pred_std[0] is not None
assert oof.evaluation_counts == (2, 1, 1)
```

---

### 2.2 Métricas Globais (`POOLED_OOF`) e Inter-Folds (`FOLD_AGGREGATION`) (`ORCH-17`, `ORCH-18`, `ORCH-19`)

Valida a separação estrita de escopos entre métricas sobre o vetor concatenado out-of-fold e resumos estatísticos entre folds:

```python
from experimental_ml.metrics.types import MetricEvaluationScope, AggregationScope

# 1. Verificação de escopo de métricas
assert all(m.scope == MetricEvaluationScope.POOLED_OOF for m in oof.pooled_metrics.values())
assert all(a.scope == AggregationScope.FOLD_AGGREGATION for a in oof.aggregated_metrics.values())

# 2. Resiliência numérica
# Em caso de indefinição matemática (ex: divisão por zero), o status deve ser UNDEFINED_NAN
# e o fluxo continua sem exceções não tratadas.
```

---

### 2.3 Persistência Atômica e Codecs de OOF (`ORCH-20`)

Valida a persistência atômica sob `{run_dir}/oof/oof_{model_id}__{scenario_id}.json` e proteção contra sobrescrita indevida:

```python
from pathlib import Path
from experimental_ml.orchestration import (
    save_oof_predictions,
    load_oof_predictions,
    oof_predictions_to_dict,
    oof_predictions_from_dict,
)

run_dir = Path("/tmp/test_run_oof")
run_dir.mkdir(parents=True, exist_ok=True)

# 1. Salvar OOF atomicamente
file_path = save_oof_predictions(oof, run_dir, overwrite=True)
assert file_path.exists()
assert file_path.name == "oof_ridge__sc1.json"

# 2. Carregar OOF
loaded_oof = load_oof_predictions(file_path)
assert loaded_oof.model_id == oof.model_id
assert loaded_oof.observation_ids == oof.observation_ids
assert loaded_oof.y_pred == oof.y_pred
```

---

### 2.4 Governança de Cobertura Parcial (`ORCH-15`)

Valida que execuções parciais sob `FAULT_TOLERANT` marcam cobertura fracionária e emitem alertas detalhados com as observações faltantes:

```python
from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.exceptions import DataIntegrityError

# 1. Cobertura parcial
oof_partial = consolidate_oof_predictions(
    model_id=ModelId("ridge"),
    scenario_id=ScenarioId("sc1"),
    prediction_records=[pred_fold0],
    target_observation_ids={"obs_1", "obs_2", "obs_3"},
)
assert oof_partial.coverage < 1.0
assert len(oof_partial.warnings) > 0

# 2. Falha em 100% dos folds deve lançar DataIntegrityError
try:
    consolidate_oof_predictions(
        model_id=ModelId("ridge"),
        scenario_id=ScenarioId("sc1"),
        prediction_records=[],
        target_observation_ids={"obs_1"},
    )
    assert False, "Deveria ter lançado DataIntegrityError"
except DataIntegrityError:
    pass
```

---

### 2.5 Portão de Estágio da Etapa 4 (`verify_runs_gate`) (`ORCH-21`)

Valida a integridade transversal da etapa de execução matricial, garantindo verificação upstream, ausência de estados não-terminais, presença física dos artefatos em disco e consistência de hashes:

```python
from experimental_ml.stages import verify_runs_gate

# Invocação do portão da etapa 4
summary = verify_runs_gate(run_dir)
assert summary["status"] == "READY"
assert summary["verified_cells"] > 0
assert summary["verified_oof_models"] > 0
```

---

## 3. Critérios Formais de Aceite (DoD)

Para homologação do Marco M5.3, os seguintes critérios são mandatórios:
- [x] Todas as 25 verificações (C1 a C25) aprovadas sem regressão.
- [x] Suíte de testes automatizados com 438/438 testes aprovados.
- [x] Relatório do Verificador Independente com veredito `PASS` e zero `findings` abertos.
- [x] Conformidade total com `XCUT-02` (runtime livre de bibliotecas pesadas de terceiros).
- [x] Persistência atômica (`write_json_atomic`) conforme `STORE-01` e `ADR-008`.
