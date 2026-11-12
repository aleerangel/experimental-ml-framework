# Roteiro de Validação e Aceitação — Marco M5.2 (Motor de Execução Matricial e Checkpointing)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M5.2 (`m5-2-matrix-executor-checkpointing`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e integradores do subsistema de orquestração matricial do `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.orchestration`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e as exportações do módulo de orquestração matricial estão íntegras:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de exportações dos símbolos públicos canônicos da matriz
python -c "
import experimental_ml.orchestration as orch
print('Orchestration exportações públicas:', len(orch.__all__))
for sym in [
    'CellDescriptor', 'derive_cell_seed', 'build_cell_matrix',
    'MatrixExecutionState', 'save_execution_state', 'load_execution_state',
    'matrix_execution_state_to_dict', 'matrix_execution_state_from_dict',
    'MatrixProgressCallback', 'NullProgressCallback',
    'run_experiment_matrix', 'resume_experiment_matrix',
]:
    assert sym in orch.__all__, f'Símbolo ausente: {sym}'
print('Símbolos canônicos de orquestração matricial validados com sucesso!')
"

# 3. Verificação de pureza de runtime (XCUT-02: zero dependências externas além de numpy)
python -c "
import sys
import experimental_ml.orchestration
forbidden = ['scipy', 'pandas', 'sklearn', 'torch', 'qiskit', 'pyarrow']
loaded = [p for p in forbidden if p in sys.modules]
assert not loaded, f'Dependências externas proibidas carregadas: {loaded}'
print('Pureza de runtime validada com sucesso (XCUT-02)!')
"
```

- **Resultado Esperado:** Mensagens confirmando a disponibilidade de todos os símbolos exportados e pureza de runtime.
- **Critério de Falha:** `ModuleNotFoundError`, `ImportError`, ausência de símbolos ou carregamento de bibliotecas externas pesadas.

---

## 2. Roteiro de Testes de Aceitação por Capacidade

### 2.1 Formulação da Grade Cartesiana e Derivação de Sementes (`ORCH-09`)

```python
from experimental_ml.core.types import ModelId, ScenarioId, PartitionPlanId
from experimental_ml.features.scenarios import FeatureScenario, ScenarioMode
from experimental_ml.models import ModelCapabilities, ModelFamily, ModelSpec, resolve_estimator_factory
from experimental_ml.orchestration import build_cell_matrix, derive_cell_seed
from experimental_ml.validation.types import EvaluationRegime, FoldPartition, PartitionConfig, PartitionPlan, PartitionStrategy

# 1. Derivação de sementes unívocas
s1 = derive_cell_seed(42, "ridge", "sc_baseline", "fold_0")
s2 = derive_cell_seed(42, "ridge", "sc_baseline", "fold_0")
s3 = derive_cell_seed(42, "ridge", "sc_baseline", "fold_1")
assert s1 == s2
assert s1 != s3
assert 0 <= s1 < 2147483647

# 2. Construção da grade cartesiana
# (2 modelos x 1 cenário x 2 folds = 4 células ordenadas deterministicamente)
```

---

### 2.2 Estado Global da Matriz, Codecs e Persistência Atômica (`ORCH-10`)

```python
from pathlib import Path
from experimental_ml.core.types import ExperimentId
from experimental_ml.orchestration import (
    CellId,
    ExecutionStatus,
    MatrixExecutionState,
    load_execution_state,
    matrix_execution_state_from_dict,
    matrix_execution_state_to_dict,
    save_execution_state,
)

state = MatrixExecutionState(
    experiment_id=ExperimentId("exp_test"),
    run_id="run_001",
    created_at="2026-11-12T10:00:00Z",
    updated_at="2026-11-12T10:00:00Z",
    master_seed=42,
    total_cells=2,
    cell_statuses={
        CellId("cell_1"): ExecutionStatus.COMPLETED,
        CellId("cell_2"): ExecutionStatus.PENDING,
    },
)
assert state.completed_cells == 1

# Serialização
d = matrix_execution_state_to_dict(state)
reconstructed = matrix_execution_state_from_dict(d)
assert reconstructed.completed_cells == state.completed_cells

# Persistência atômica
run_dir = Path("/tmp/test_expml_matrix_state")
run_dir.mkdir(parents=True, exist_ok=True)
save_execution_state(state, run_dir, overwrite=True)
loaded = load_execution_state(run_dir)
assert loaded.run_id == "run_001"
```

---

### 2.3 Execução Sequencial e Paralela da Matriz (`ORCH-11`, `ORCH-12`, `ORCH-14`)

```python
from experimental_ml.orchestration import run_experiment_matrix

# Execução paralela com 2 workers
state_parallel = run_experiment_matrix(
    model_specs=[m1, m2],
    scenarios=[s1, s2],
    partition_plan=partition_plan,
    sanitized_view=view,
    run_dir=Path("/tmp/test_run_parallel"),
    metrics=("rmse",),
    outer_n_jobs=2,
    master_seed=42,
    overwrite=True,
)
assert state_parallel.completed_cells == 8
assert state_parallel.failed_cells == 0
```

---

### 2.4 Mecanismo de Retomada e Checkpointing Idempotente (`ORCH-13`)

```python
from experimental_ml.orchestration import resume_experiment_matrix

# Retomada sobre diretório existente: células já concluídas são puladas sem recomputação
resumed_state = resume_experiment_matrix(
    run_dir=Path("/tmp/test_run_parallel"),
    model_specs=[m1, m2],
    scenarios=[s1, s2],
    partition_plan=partition_plan,
    sanitized_view=view,
    metrics=("rmse",),
)
assert resumed_state.completed_cells == 8
```
