# Roteiro de Validação e Aceitação — Marco M3.1 (Exploratory Feature Relations Report)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M3.1 (`m3-1-exploratory-features`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e consumidores da biblioteca `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.features`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e o pacote instalado com suporte a desenvolvimento:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e exportações do módulo features
python -c "import experimental_ml.features as f; print('Features importado com sucesso! Exportacoes:', len(f.__all__))"
```

- **Resultado Esperado:** Mensagem confirmando importação e 10 símbolos públicos exportados em `__all__` (`explore_features`, `ExploratoryFeatureReport`, `AssociationMeasure`, `RedundancyPair`, `SCOPE_EXPLORATORY_FULL_DATA`, `METHODOLOGICAL_WARNINGS`, `compute_pearson`, `compute_spearman`, `compute_correlation_ratio`, `compute_cramers_v`).
- **Critério de Falha:** `ModuleNotFoundError` para `experimental_ml.features` ou símbolos públicos ausentes.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Análise Exploratória Preditor-Alvo e Rotulagem de Escopo Mandatória (`explore_features`)

```python
import numpy as np
from experimental_ml.core.enums import MetricStatus, TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    PreparationRule,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features import (
    METHODOLOGICAL_WARNINGS,
    SCOPE_EXPLORATORY_FULL_DATA,
    explore_features,
)

# 1. Criação de base saneada via M2.2
data = {
    "num_feature": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    "cat_feature": ["A", "A", "B", "B", "C", "C"],
    "target": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0],
}
schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.REGRESSION)
bundle = load_dataset(data, schema=schema)
profile = profile_dataset(bundle)
rules = [
    PreparationRule("E1_CATEGORICAL_UNENCODED", "cat_feature", "DEFER_INTRA_FOLD", {"encoding_strategy": "ONE_HOT"})
]
plan = create_preparation_plan(profile, rules)
view = sanitize_dataset(bundle, profile, plan)

# 2. Execução da exploração
report = explore_features(view, redundancy_threshold=0.85)

# 3. Verificação de escopo e avisos metodológicos (CA-E2-01)
assert report.scope == SCOPE_EXPLORATORY_FULL_DATA
assert report.dataset_hash == view.dataset_hash
assert report.task_type == TaskType.REGRESSION
assert report.warnings == METHODOLOGICAL_WARNINGS
assert len(report.warnings) == 3
```

- **Resultado Esperado:** O relatório emitido possui `scope = "EXPLORATORY_FULL_DATA"`, mantém o `dataset_hash` idêntico à visão saneada e traz os 3 avisos metodológicos mandatórios.

---

### 2.2 Associação Estatística por Natureza de Variável (Pearson, Spearman, $\eta$, Cramér's V)

```python
# Continuação do bloco anterior (Regressão)
assoc_map = {(a.feature_name, a.metric_name): a for a in report.target_associations}

# num_feature x target (contínua x contínua): Pearson e Spearman
assert ("num_feature", "PEARSON") in assoc_map
assert ("num_feature", "SPEARMAN") in assoc_map
assert abs(assoc_map[("num_feature", "PEARSON")].value - 1.0) < 1e-6
assert abs(assoc_map[("num_feature", "SPEARMAN")].value - 1.0) < 1e-6

# cat_feature x target (categórica x contínua): Razão de Correlação eta
assert ("cat_feature", "CORRELATION_RATIO") in assoc_map
assert abs(assoc_map[("cat_feature", "CORRELATION_RATIO")].value - 1.0) < 1e-6
```

- **Resultado Esperado:** Métricas calculadas em conformidade com as escalas de mensuração; correlações lineares e não-lineares calculadas com precisão estatística.

---

### 2.3 Matriz de Redundância e Triagem de Pares Colineares

```python
# Matriz preditor-preditor simétrica
matrix = report.pairwise_redundancy_matrix
assert matrix["num_feature"]["num_feature"] == 1.0
assert matrix["num_feature"]["cat_feature"] == matrix["cat_feature"]["num_feature"]

# Pares de alta redundância acima do limiar
for pair in report.high_redundancy_pairs:
    assert abs(pair.value) >= 0.85
    assert pair.status == MetricStatus.VALID
```

- **Resultado Esperado:** Matriz simétrica com 1.0 na diagonal e pares de alta redundância listados de forma canônica sem duplicação de espelhamento.

---

### 2.4 Serialização Lossless e Reconstrução JSON (RFC 8259)

```python
import json
from experimental_ml.features import ExploratoryFeatureReport

# Serialização determinística para JSON primitivo
serialized = report.to_dict()
json_text = json.dumps(serialized, allow_nan=False, indent=2)

# Reconstrução fiel
reconstructed = ExploratoryFeatureReport.from_dict(json.loads(json_text))
assert reconstructed.scope == report.scope
assert reconstructed.dataset_hash == report.dataset_hash
assert len(reconstructed.target_associations) == len(report.target_associations)
assert len(reconstructed.high_redundancy_pairs) == len(report.high_redundancy_pairs)
```

- **Resultado Esperado:** Serialização RFC 8259 em conformidade estrita (sem NaNs literais quebrando serializadores) e reconstrução perfeita com equivalência de metadados.

---

## 3. Resumo dos Critérios de Aceitação Verificados

| Critério | Descrição | Status |
| :--- | :--- | :---: |
| **EXP-01** | `explore_features` retorna `scope = "EXPLORATORY_FULL_DATA"` e 3 avisos metodológicos | **APROVADO** |
| **EXP-02** | Associação contínua-contínua computa Pearson $r$ e Spearman $\rho$ com postos médios para empates | **APROVADO** |
| **EXP-03** | Associação contínua-categórica computa Razão de Correlação $\eta \in [0, 1]$ (ANOVA univariada) | **APROVADO** |
| **EXP-04** | Associação categórica-categórica computa V de Cramér $V \in [0, 1]$ via tabela de contingência | **APROVADO** |
| **EXP-05** | Variância nula, colunas constantes e degenerescência retornam `NaN` e `status = UNDEFINED_NAN` | **APROVADO** |
| **EXP-06** | Matriz de redundância completa e lista de pares com alta redundância ordenada canonicamente | **APROVADO** |
| **EXP-07** | Serialização determinística bidirecional (`to_dict` / `from_dict`) compatível com JSON RFC 8259 | **APROVADO** |
| **EXP-08** | Validação de entradas, integridade da visão saneada e ausência de dependências runtime além do NumPy | **APROVADO** |
