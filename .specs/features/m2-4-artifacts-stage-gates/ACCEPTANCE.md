# Roteiro de Validação e Aceitação — Marco M2.4 (Artifacts Persistence & Stage Gates)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M2.4 (`m2-4-artifacts-stage-gates`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e consumidores da biblioteca `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através das interfaces públicas e utilitários exportados em `experimental_ml.core.storage`, `experimental_ml.data.codecs`, `experimental_ml.validation.storage` e `experimental_ml.stages`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e as exportações do módulo de persistência e *stage gates* estão disponíveis:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de exportações de persistência e stage gates
python -c "from experimental_ml.core.storage import write_json_atomic, read_json; from experimental_ml.stages import verify_preparation_gate, verify_partition_gate; print('Modulos M2.4 importados com sucesso!')"
```

- **Resultado Esperado:** Mensagem confirmando importação sem erros.
- **Critério de Falha:** `ImportError` ou `ModuleNotFoundError`.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Persistência Atômica de JSON e Proteção contra Sobrescrita (`STORE-01`, `STORE-07`)

```python
import tempfile
from pathlib import Path
import pytest
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import write_json_atomic, read_json

with tempfile.TemporaryDirectory() as td:
    target = Path(td) / "experiment" / "artifact.json"
    data = {"run_id": "exp_001", "metrics": {"acc": 0.95}}

    # 1. Escrita atômica bem sucedida
    write_json_atomic(target, data)
    assert target.exists()
    assert read_json(target) == data

    # 2. Proteção de sobrescrita (STORE-07)
    with pytest.raises(ConfigurationError):
        write_json_atomic(target, {"run_id": "tampered"}, overwrite=False)

    # 3. Sobrescrita explícita
    write_json_atomic(target, {"run_id": "updated"}, overwrite=True)
    assert read_json(target)["run_id"] == "updated"
```

- **Resultado Esperado:** Escrita atômica com diretórios intermediários criados automaticamente, recusa de sobrescrita quando `overwrite=False` disparando `ConfigurationError`, e atualização quando `overwrite=True`.

---

### 2.2 Codecs Lossless Bidirecionais (`STORE-02`)

```python
import json
import numpy as np
from experimental_ml.core.enums import TaskType
from experimental_ml.data import DatasetSchemaSpec, PreparationRule, create_preparation_plan, load_dataset, profile_dataset
from experimental_ml.data.codecs import dataset_profile_to_dict, dataset_profile_from_dict, preparation_plan_to_dict, preparation_plan_from_dict

data = {"f1": [1.0, np.nan, 3.0], "cat": ["A", "B", "A"], "target": [1, 0, 1]}
schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
bundle = load_dataset(data, schema=schema)
profile = profile_dataset(bundle)

# Serialização sem perda para DatasetProfile
prof_dict = dataset_profile_to_dict(profile)
json_str = json.dumps(prof_dict, allow_nan=False)
prof_restored = dataset_profile_from_dict(json.loads(json_str))
assert prof_restored.source_dataset_hash == profile.source_dataset_hash
assert prof_restored.columns["f1"].n_missing == 1

# Serialização sem perda para PreparationPlan
rules = [PreparationRule("E1_FEATURE_MISSING", "f1", "DROP_ROWS")]
plan = create_preparation_plan(profile, rules)
plan_dict = preparation_plan_to_dict(plan)
plan_restored = preparation_plan_from_dict(json.loads(json.dumps(plan_dict, allow_nan=False)))
assert plan_restored.status == plan.status
assert plan_restored.plan_digest == plan.plan_digest
```

- **Resultado Esperado:** Conversão bidirecional perfeita sem alteração de tipos, serialização JSON estrita sem `NaN`/`Infinity` (RFC 8259).

---

### 2.3 Serialização Determinística de Splits (`STORE-04`)

```python
import tempfile
from pathlib import Path
from types import SimpleNamespace
from experimental_ml.core.types import ObservationId
from experimental_ml.validation import EvaluationRegime, PartitionConfig, PartitionStrategy, build_partition_plan
from experimental_ml.validation.storage import write_splits_csv_gz, read_splits_csv_gz

view = SimpleNamespace(
    observation_ids=tuple(ObservationId(f"id_{i}") for i in range(10)),
    dataset_hash="hash_view",
    columns={},
    schema=None,
)
config = PartitionConfig(
    strategy=PartitionStrategy.KFOLD,
    regime=EvaluationRegime.CV_AND_HOLDOUT,
    n_splits=2,
    holdout_fraction=0.2,
    shuffle=False,
)
plan = build_partition_plan(view, config)

with tempfile.TemporaryDirectory() as td:
    file1 = Path(td) / "splits1.csv.gz"
    file2 = Path(td) / "splits2.csv.gz"
    write_splits_csv_gz(file1, plan)
    write_splits_csv_gz(file2, plan)

    # Determinismo absoluto de bytes
    assert file1.read_bytes() == file2.read_bytes()

    # Leitura e verificação de campos
    rows = read_splits_csv_gz(file1)
    assert len(rows) == 10
    assert "observation_id" in rows[0]
    assert "holdout_role" in rows[0]
```

- **Resultado Esperado:** Arquivos `.csv.gz` idênticos bit a bit e mapeamento correto de identificadores de observação.

---

### 2.4 Portões de Integridade entre Etapas (`STORE-03`, `STORE-05`, `STORE-06`)

```python
import tempfile
from pathlib import Path
import pytest
from experimental_ml.core.findings import ContractViolationError, DataIntegrityError
from experimental_ml.stages import verify_preparation_gate, verify_partition_gate

with tempfile.TemporaryDirectory() as td:
    exp_dir = Path(td)
    # Diretório vazio viola contrato do portão de preparação
    with pytest.raises(DataIntegrityError):
        verify_preparation_gate(exp_dir)
```

- **Resultado Esperado:** Bloqueio imediato quando artefatos obrigatórios estiverem ausentes, hashes divergirem ou planos estiverem incompletos.

---

## 3. Classificação dos Testes

| Camada / Tipo | Arquivo | Comando |
| :--- | :--- | :--- |
| **Unitário: Armazenamento Atômico** | `tests/unit/core/test_storage.py` | `.venv/bin/pytest tests/unit/core/test_storage.py -v` |
| **Unitário: Codecs de Dados** | `tests/unit/data/test_codecs.py` | `.venv/bin/pytest tests/unit/data/test_codecs.py -v` |
| **Unitário: Splits e Codecs de Validação** | `tests/unit/validation/test_splits_storage.py` | `.venv/bin/pytest tests/unit/validation/test_splits_storage.py -v` |
| **Unitário: Portões de Etapa** | `tests/unit/stages/test_stage_gates.py` | `.venv/bin/pytest tests/unit/stages/test_stage_gates.py -v` |
| **Integração: Layout e Isolamento** | `tests/integration/test_artifacts_stage_gates_integration.py` | `.venv/bin/pytest tests/integration/test_artifacts_stage_gates_integration.py -v` |
| **Regressão Geral** | Toda a suíte de testes | `.venv/bin/pytest tests/ -q` |
