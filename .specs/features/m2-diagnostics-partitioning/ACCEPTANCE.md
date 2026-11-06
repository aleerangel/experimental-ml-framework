# Roteiro de Validação e Aceitação — Marco M2.1 (Stage 1 Dataset Profiling)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M2.1 (`m2-diagnostics-partitioning`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e consumidores da biblioteca `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.data`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e o pacote instalado com suporte a desenvolvimento:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e exportações do módulo data
python -c "import experimental_ml.data as d; print('Data importado com sucesso! Exportacoes:', len(d.__all__))"
```

- **Resultado Esperado:** Mensagem confirmando importação e 17 símbolos públicos exportados em `__all__` (`profile_dataset`, `ProfileConfig`, `DatasetProfile`, `ColumnProfile`, etc.).
- **Critério de Falha:** `ModuleNotFoundError` para `experimental_ml.data` ou símbolos de perfilamento ausentes.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Configuração Imutável e Validação de Limiares (`ProfileConfig`)

```python
import pytest
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.data import ProfileConfig

# 1. Instanciação padrão válida com slots e imutabilidade
cfg = ProfileConfig()
assert cfg.near_constant_top_frequency == 0.99
assert cfg.identifier_unique_ratio == 0.95
assert cfg.scale_disparity_orders == 3.0
assert cfg.imbalance_ratio == 3.0
assert cfg.rare_class_proportion == 0.05
assert cfg.small_group_size == 5
assert cfg.max_categories_reported == 50
assert cfg.max_listed_ids == 100

# 2. Rejeição de valores fora dos limites válidos
try:
    ProfileConfig(near_constant_top_frequency=1.05)
    raise AssertionError("Deveria ter lançado ConfigurationError")
except ConfigurationError:
    pass

try:
    ProfileConfig(imbalance_ratio=0.8)
    raise AssertionError("Deveria ter lançado ConfigurationError")
except ConfigurationError:
    pass

print("2.1 ProfileConfig: APROVADO")
```

---

### 2.2 Perfilamento Estrutural e Estatísticas por Coluna (`profile_dataset`)

```python
import numpy as np
from experimental_ml.core.enums import TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    load_dataset,
    profile_dataset,
    DatasetProfile,
)

data = {
    "num_feat": [10.0, 20.0, 30.0, 40.0, np.nan],
    "cat_feat": ["cat", "dog", "cat", "bird", "cat"],
    "target": [1.0, 2.0, 3.0, 4.0, 5.0],
}
schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.REGRESSION)
bundle = load_dataset(data, schema=schema)

profile = profile_dataset(bundle)

assert isinstance(profile, DatasetProfile)
assert profile.source_dataset_hash == bundle.dataset_hash
assert profile.n_rows == 5
assert profile.n_cols == 3

# Estatísticas numéricas com ddof=1 e exclusão de ausentes
num_stats = profile.columns["num_feat"].numeric_stats
assert num_stats is not None
assert num_stats.mean == 25.0
assert num_stats.min == 10.0
assert num_stats.max == 40.0
assert profile.columns["num_feat"].n_missing == 1
assert profile.columns["num_feat"].missing_proportion == 0.2

# Estatísticas categóricas com frequências ordenadas
cat_stats = profile.columns["cat_feat"].categorical_stats
assert cat_stats is not None
assert cat_stats.cardinality == 3
assert cat_stats.frequencies[0].value == "cat"
assert cat_stats.frequencies[0].count == 3

print("2.2 Perfilamento Estrutural: APROVADO")
```

---

### 2.3 Diagnósticos de Alvo, Grupos e Detecção de Linhas Duplicadas

```python
import numpy as np
from experimental_ml.core.enums import TaskType
from experimental_ml.data import DatasetSchemaSpec, load_dataset, profile_dataset

# Dataset com grupo e linhas duplicadas (ignorando observation_id)
data = {
    "id": ["row_1", "row_2", "row_3", "row_4"],
    "x": [1.0, 1.0, 2.0, 3.0],
    "grp": ["g1", "g1", "g2", "g2"],
    "y": [0, 0, 1, 1],
}
schema = DatasetSchemaSpec(
    target_col="y",
    task_type=TaskType.BINARY_CLASSIFICATION,
    observation_id_col="id",
    group_col="grp",
)
bundle = load_dataset(data, schema=schema)
profile = profile_dataset(bundle)

# Verificação de grupos
assert profile.groups is not None
assert profile.groups.n_groups == 2
assert profile.groups.min_group_size == 2
assert profile.groups.max_group_size == 2

# Verificação de duplicatas
assert profile.duplicate_rows.n_duplicate_rows == 1
assert len(profile.duplicate_rows.duplicate_observation_ids) == 1

print("2.3 Diagnósticos de Alvo, Grupos e Duplicatas: APROVADO")
```

---

### 2.4 Avaliação de Achados Fechados e Separação de Severidade

```python
from experimental_ml.core.enums import FindingSeverity, TaskType
from experimental_ml.data import DatasetSchemaSpec, load_dataset, profile_dataset

# Dataset com classe desbalanceada e alvo binário não mapeado
data = {
    "feature_const": [1.0] * 100,
    "target": ["negativo"] * 95 + ["positivo"] * 5,
}
schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
bundle = load_dataset(data, schema=schema)
profile = profile_dataset(bundle)

# Achados canônicos: CONFIRMED_ISSUE antes de HEURISTIC_WARNING
codes = [f.code for f in profile.findings]
assert "E1_CONSTANT_COLUMN" in codes
assert "E1_TARGET_BINARY_UNMAPPED" in codes
assert "W1_CLASS_IMBALANCE" in codes

seen_warning = False
for f in profile.findings:
    if f.severity == FindingSeverity.HEURISTIC_WARNING:
        seen_warning = True
    elif f.severity == FindingSeverity.CONFIRMED_ISSUE:
        assert not seen_warning, f"CONFIRMED_ISSUE {f.code} encontrado após HEURISTIC_WARNING"

print("2.4 Catálogo de Achados e Ordenação Canônica: APROVADO")
```

---

### 2.5 Imutabilidade Absoluta e Determinismo

```python
from experimental_ml.core.enums import TaskType
from experimental_ml.data import DatasetSchemaSpec, load_dataset, profile_dataset

data = {"x": [10.0, 20.0, 30.0], "y": [1, 0, 1]}
schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.BINARY_CLASSIFICATION)
bundle = load_dataset(data, schema=schema)

h_before = bundle.dataset_hash
p1 = profile_dataset(bundle)
h_after = bundle.dataset_hash

assert h_before == h_after
p2 = profile_dataset(bundle)
assert p1 == p2
assert p1.findings == p2.findings

print("2.5 Imutabilidade e Determinismo: APROVADO")
```

---

## 3. Cenário Integrado de Ponta a Ponta

Executar a validação fim a fim via suíte de integração:

```bash
.venv/bin/pytest tests/integration/test_profiling_integration.py -v
```

- **Critério de Aceite:** 5 testes aprovados (`test_prof_10_immutability_and_determinism`, `test_end_to_end_profiling_on_complex_dataset`, `test_architectural_import_direction_xcut_01`, `test_single_runtime_dependency_xcut_02`, `test_exported_symbols_count_xcut_04`).
