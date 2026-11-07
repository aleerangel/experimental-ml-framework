# Roteiro de Validação e Aceitação — Marco M2.2 (Preparation Plan & Sanitized Dataset View)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M2.2 (`m2-2-preparation-plan-sanitization`)  
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

- **Resultado Esperado:** Mensagem confirmando importação e 23 símbolos públicos exportados em `__all__` (`create_preparation_plan`, `sanitize_dataset`, `PreparationRule`, `PreparationPlan`, `SanitizedDatasetView`, etc.).
- **Critério de Falha:** `ModuleNotFoundError` para `experimental_ml.data` ou símbolos de preparação ausentes.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Construção de Plano de Preparação e Auditoria de Cobertura (`create_preparation_plan`)

```python
import numpy as np
from experimental_ml.core.enums import TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    PreparationRule,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
)

data = {
    "num_feature": [10.0, 20.0, np.nan, 40.0],
    "cat_feature": ["A", "B", "A", "C"],
    "const_feature": [1.0, 1.0, 1.0, 1.0],
    "target": ["pos", "neg", "pos", "neg"],
}
schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
bundle = load_dataset(data, schema=schema)
profile = profile_dataset(bundle)

# 1. Plano incompleto (sem regras para os problemas detectados)
plan_incomplete = create_preparation_plan(profile, [])
assert plan_incomplete.status == "INCOMPLETE"
assert len(plan_incomplete.unresolved_findings) > 0
assert plan_incomplete.plan_digest == ""

# 2. Plano completo e ordenado canonicamente
rules = [
    PreparationRule("E1_FEATURE_MISSING", "num_feature", "DROP_ROWS"),
    PreparationRule("E1_CATEGORICAL_UNENCODED", "cat_feature", "DEFER_INTRA_FOLD", {"encoding_strategy": "ONE_HOT"}),
    PreparationRule("E1_CONSTANT_COLUMN", "const_feature", "EXCLUDE_COLUMN"),
    PreparationRule("E1_TARGET_BINARY_UNMAPPED", "target", "MAP_BINARY_TARGET", {"positive_label": "pos"}),
]
plan_ready = create_preparation_plan(profile, rules)
assert plan_ready.status == "READY"
assert len(plan_ready.plan_digest) == 64
assert len(plan_ready.rules) == 4
```

- **Resultado Esperado:** Plano sem regras suficientes recebe status `"INCOMPLETE"`. Plano com cobertura total de `CONFIRMED_ISSUE` recebe status `"READY"` com digest determinístico de 64 caracteres.

---

### 2.2 Saneamento Estrutural Pré-Partição e Visão Saneada (`sanitize_dataset`)

```python
from experimental_ml.core.hashing import dataset_hash
from experimental_ml.data import sanitize_dataset

view = sanitize_dataset(bundle, profile, plan_ready)

# 1. Verificação de regras estruturais aplicadas
assert len(view.observation_ids) == 3  # Linha com nan em num_feature foi descartada
assert len(view.dropped_observation_ids) == 1
assert "const_feature" not in view.columns
assert "const_feature" not in view.candidate_feature_cols
assert "num_feature" in view.candidate_feature_cols
assert "cat_feature" in view.candidate_feature_cols

# 2. Mapeamento binário do alvo codificado em int64 {0, 1}
assert view.columns["target"].dtype == np.int64
assert set(view.columns["target"]) == {0, 1}
assert view.target_label_mapping == {"pos": 1, "neg": 0}

# 3. Integridade do hash e imutabilidade dos arrays
expected_hash = dataset_hash(view.columns, view.schema, observation_ids=view.observation_ids)
assert view.dataset_hash == expected_hash
for col_name, arr in view.columns.items():
    assert not arr.flags.writeable
```

- **Resultado Esperado:** Linha com nulo descartada, coluna constante excluída, alvo codificado em `{0, 1}`, arrays somente-leitura e hash da visão canônico.

---

### 2.3 Preservação Bit a Bit e Prevenção de Vazamento de Dados (ADR-002)

```python
# Coluna deferida (cat_feature) preservada bit a bit sem codificacao prematura
orig_cat_kept = bundle.columns["cat_feature"][[0, 1, 3]]  # indices mantidos
assert view.columns["cat_feature"].tobytes() == orig_cat_kept.tobytes()

# Bundle original permanece intocado e integro
assert not bundle.columns["num_feature"].flags.writeable
assert bundle.dataset_hash == profile.source_dataset_hash
```

- **Resultado Esperado:** Transformações que aprendem parâmetros (como encoding e imputação) não são aplicadas globalmente antes da partição (ADR-002); colunas permanecem 100% bit a bit idênticas ao bundle original.

---

## 3. Resumo dos Critérios de Aceitação Verificados

| Critério | Descrição | Status |
| :--- | :--- | :---: |
| **PREP-01** | `create_preparation_plan` com cobertura total retorna `status = "READY"` e digest canônico | **APROVADO** |
| **PREP-02** | Plano com achados pendentes ou irresolúveis retorna `status = "INCOMPLETE"` | **APROVADO** |
| **PREP-03** | Validação de regras e rejeição de regras órfãs/inadmissíveis via `ConfigurationError` | **APROVADO** |
| **PREP-04** | Aplicação estrita de regras estruturais (`DROP_ROWS`, `EXCLUDE_COLUMN`, `MAP_BINARY_TARGET`) | **APROVADO** |
| **PREP-05** | Bloqueio de saneamento sob status não-READY ou hashes divergentes | **APROVADO** |
| **PREP-06** | Contrato de `SanitizedDatasetView` com equivalência de `dataset_hash` | **APROVADO** |
| **PREP-07** | Preservação bit a bit de colunas sob `DEFER_INTRA_FOLD` ou `ACCEPT_AS_IS` | **APROVADO** |
| **PREP-08** | Codificação de alvo binário textual em `{0, 1}` com rastreabilidade | **APROVADO** |
| **PREP-09** | Validação de não-vacuidade pós-saneamento (linhas > 0 e atributos candidatos > 0) | **APROVADO** |
| **PREP-10** | Imutabilidade do `DatasetBundle` e determinismo estrito na geração da visão | **APROVADO** |
