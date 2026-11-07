# Roteiro de Validação e Aceitação — Marco M2.3 (Partitioning Engine)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M2.3 (`m2-3-partitioning-engine`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e consumidores da biblioteca `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.validation`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e o pacote instalado com suporte a desenvolvimento:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e exportações do módulo validation
python -c "import experimental_ml.validation as v; print('Validation importado com sucesso! Exportacoes:', len(v.__all__))"
```

- **Resultado Esperado:** Mensagem confirmando importação e 7 símbolos públicos exportados em `__all__` (`build_partition_plan`, `validate_partition_plan`, `PartitionStrategy`, `EvaluationRegime`, `FoldPartition`, `PartitionConfig`, `PartitionPlan`).
- **Critério de Falha:** `ModuleNotFoundError` para `experimental_ml.validation` ou símbolos públicos ausentes.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Construção de Plano K-Fold com Validação Cruzada Pura (`CV_ONLY` e `KFOLD`)

```python
import numpy as np
from experimental_ml.core.types import ObservationId
from experimental_ml.validation import (
    EvaluationRegime,
    PartitionConfig,
    PartitionStrategy,
    build_partition_plan,
    validate_partition_plan,
)

class MockView:
    def __init__(self, n=30):
        self.observation_ids = tuple(ObservationId(f"id_{i:02d}") for i in range(n))
        self.columns = {}
        self.schema = None
        self.dataset_hash = "mock_hash_kfold"

view = MockView(30)
cfg = PartitionConfig(
    strategy=PartitionStrategy.KFOLD,
    regime=EvaluationRegime.CV_ONLY,
    n_splits=5,
    shuffle=False,
)

plan = build_partition_plan(view, cfg)

# Verificações de contrato
assert plan.regime == EvaluationRegime.CV_ONLY
assert plan.strategy == PartitionStrategy.KFOLD
assert len(plan.folds) == 5
assert plan.holdout_ids == ()
assert len(plan.development_ids) == 30
assert len(plan.plan_id) == 64

# Disjunção e cobertura em cada fold
all_val = []
for fold in plan.folds:
    assert set(fold.train_ids).isdisjoint(set(fold.val_ids))
    assert set(fold.train_ids) | set(fold.val_ids) == set(view.observation_ids)
    all_val.extend(fold.val_ids)

assert set(all_val) == set(view.observation_ids)
assert len(all_val) == 30

# Validador matemático não levanta erros
validate_partition_plan(plan, view)
```

- **Resultado Esperado:** Divisão uniforme em 5 folds com disjunção estrita entre treino e validação, cobertura total de `development_ids` e aprovação pelo `validate_partition_plan`.

---

### 2.2 Preservação de Classes sob Stratified K-Fold e Separação de Holdout (`CV_AND_HOLDOUT`)

```python
from types import SimpleNamespace

# 50 observações com proporção 60% classe 1 e 40% classe 0
n = 50
target_arr = np.array([1] * 30 + [0] * 20, dtype=np.int64)
obs = tuple(ObservationId(f"obs_{i:02d}") for i in range(n))

class MockStratView:
    def __init__(self):
        self.observation_ids = obs
        self.columns = {"target": target_arr}
        self.schema = SimpleNamespace(target_col="target")
        self.dataset_hash = "mock_hash_strat"

strat_view = MockStratView()

cfg_strat = PartitionConfig(
    strategy=PartitionStrategy.STRATIFIED_KFOLD,
    regime=EvaluationRegime.CV_AND_HOLDOUT,
    n_splits=4,
    holdout_fraction=0.2,
    stratify=True,
    master_seed=42,
)

plan_strat = build_partition_plan(strat_view, cfg_strat)

# Holdout isolado de 20% (10 amostras) e desenvolvimento de 80% (40 amostras)
assert len(plan_strat.holdout_ids) == 10
assert len(plan_strat.development_ids) == 40
assert set(plan_strat.holdout_ids).isdisjoint(set(plan_strat.development_ids))

# CV ocorre exclusivamente sobre development_ids
for fold in plan_strat.folds:
    assert set(fold.train_ids).isdisjoint(set(plan_strat.holdout_ids))
    assert set(fold.val_ids).isdisjoint(set(plan_strat.holdout_ids))
    assert set(fold.train_ids).isdisjoint(set(fold.val_ids))

# Validação matemática
validate_partition_plan(plan_strat, strat_view)
```

- **Resultado Esperado:** 10 amostras isoladas para holdout final e 40 amostras alocadas para CV estratificado sem vazamento de dados.

---

### 2.3 Particionamento Agrupado (`GROUP_KFOLD`) e Prevenção de Vazamento por Grupo

```python
# 20 observações distribuídas em 4 grupos (5 observações por grupo)
grp_arr = np.array(["A"] * 5 + ["B"] * 5 + ["C"] * 5 + ["D"] * 5, dtype=object)

class MockGroupView:
    def __init__(self):
        self.observation_ids = tuple(ObservationId(f"g_{i:02d}") for i in range(20))
        self.columns = {"group": grp_arr}
        self.schema = SimpleNamespace(group_col="group")
        self.dataset_hash = "mock_hash_group"

grp_view = MockGroupView()

cfg_grp = PartitionConfig(
    strategy=PartitionStrategy.GROUP_KFOLD,
    regime=EvaluationRegime.CV_ONLY,
    group_col="group",
    n_splits=4,
    master_seed=123,
)

plan_grp = build_partition_plan(grp_view, cfg_grp)
grp_lookup = {oid: grp_arr[i] for i, oid in enumerate(grp_view.observation_ids)}

for fold in plan_grp.folds:
    tr_grps = {grp_lookup[oid] for oid in fold.train_ids}
    va_grps = {grp_lookup[oid] for oid in fold.val_ids}
    assert tr_grps.isdisjoint(va_grps)

validate_partition_plan(plan_grp, grp_view)
```

- **Resultado Esperado:** 100% de disjunção de grupos entre treino e validação em cada fold, impedindo contaminação intergrupo.

---

### 2.4 Determinismo Estrito de `plan_id` e Imutabilidade do Plano (D8, ADR-007)

```python
from dataclasses import FrozenInstanceError

# Execuções repetidas com mesma semente produzem exatamente o mesmo plan_id
plan_a = build_partition_plan(strat_view, cfg_strat)
plan_b = build_partition_plan(strat_view, cfg_strat)

assert plan_a.plan_id == plan_b.plan_id
assert plan_a.development_ids == plan_b.development_ids
assert plan_a.holdout_ids == plan_b.holdout_ids

# Imutabilidade via frozen dataclass
try:
    plan_a.plan_id = "modified"
    assert False, "Deveria ter lançado FrozenInstanceError"
except FrozenInstanceError:
    pass
```

- **Resultado Esperado:** Identificador SHA-256 de 64 caracteres idêntico em execuções repetidas e bloqueio de modificações in-place.

---

## 3. Resumo dos Critérios de Aceitação Verificados

| Critério | Descrição | Status |
| :--- | :--- | :---: |
| **PART-01** | Divisão K-Fold pura com disjunção estrita e cobertura total de development | **APROVADO** |
| **PART-02** | Divisão Estratificada preservando distribuição de classes ($\pm 1$ amostra) | **APROVADO** |
| **PART-03** | Divisão Agrupada com disjunção estrita de grupos ($\text{Groups}(Train) \cap \text{Groups}(Val) = \emptyset$) | **APROVADO** |
| **PART-04** | Divisão Temporal com ordenação cronológica e prevenção de vazamento temporal | **APROVADO** |
| **PART-05** | Reamostragem Bootstrap com conjunto de validação Out-of-Bag (OOB) | **APROVADO** |
| **PART-06** | Separação de Holdout e confinamento de CV a `development_ids` | **APROVADO** |
| **PART-07** | Validador matemático `validate_partition_plan` com checagem de invariantes | **APROVADO** |
| **PART-08** | Contrato imutável de `PartitionPlan` com `plan_id` SHA-256 determinístico | **APROVADO** |
| **PART-09** | Determinismo e reprodutibilidade de partições a partir de semente mestre | **APROVADO** |
| **PART-10** | Validação de limites e configurações de particionamento via `ConfigurationError` | **APROVADO** |
