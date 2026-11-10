# Roteiro de Validação e Aceitação — Marco M3.3 (Seleção Dinâmica Intra-Fold de Features e Estabilidade)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M3.3 (`m3-3-intra-fold-selection`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e consumidores da biblioteca `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.features`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e o pacote instalado com suporte a desenvolvimento:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e exportações do módulo features
python -c "
import experimental_ml.features as f
assert 'SelectionResult' in f.__all__
assert 'select_features_in_fold' in f.__all__
assert 'apply_feature_selection' in f.__all__
assert 'SelectionStabilityReport' in f.__all__
assert 'compute_selection_stability' in f.__all__
print('Módulo features exportou todas as interfaces do M3.3 com sucesso!')
"
```

- **Resultado Esperado:** Mensagem confirmando importação bem-sucedida de todas as interfaces públicas da funcionalidade.
- **Critério de Falha:** `ModuleNotFoundError` ou ausência dos símbolos públicos exportados em `__all__`.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Modelo Imutável `SelectionResult` e Serialização (SEL-01)

```python
from dataclasses import FrozenInstanceError
from types import MappingProxyType
import numpy as np
from experimental_ml.features import SelectionResult

# 1. Instanciação com atributos imutáveis e proxies de mapeamento
res = SelectionResult(
    selected_features=("feat_a", "feat_b"),
    scores={"feat_a": 0.85, "feat_b": 0.60},
    fitted_params={"threshold": 0.5},
    strategy_name="VARIANCE_THRESHOLD",
)

assert res.selected_features == ("feat_a", "feat_b")
assert isinstance(res.scores, MappingProxyType)
assert isinstance(res.fitted_params, MappingProxyType)
assert res.scores["feat_a"] == 0.85

# 2. Garantia de congelamento e imutabilidade de atributos
try:
    res.strategy_name = "MUTATED"
    assert False, "Deveria ter lançado FrozenInstanceError"
except FrozenInstanceError:
    pass

# 3. Serialização e desserialização completa em dicionário
data = res.to_dict()
reconstructed = SelectionResult.from_dict(data)
assert reconstructed.selected_features == res.selected_features
assert reconstructed.scores == res.scores
assert reconstructed.strategy_name == res.strategy_name
```

- **Resultado Esperado:** Objeto `SelectionResult` imutável (`slots=True, frozen=True`), mapeamentos imutáveis com `MappingProxyType` e integridade perfeita em serialização/desserialização JSON.

---

### 2.2 Despacho Funcional Puro e Bypass em Modo `FIXED` (SEL-02)

```python
import numpy as np
from experimental_ml.features import FeatureScenario, ScenarioMode, select_features_in_fold

scenario_fixed = FeatureScenario(
    scenario_id="fixed_biometric",
    name="Biometric Baseline",
    description="Fixed features from literature",
    scientific_justification="Established baseline",
    mode=ScenarioMode.FIXED,
    selected_features=("dap", "ht"),
)

X_train = {
    "dap": np.array([15.0, 25.0, 35.0]),
    "ht": np.array([12.0, 20.0, 28.0]),
    "noise": np.array([1.0, 2.0, 3.0]),
}

# Em modo FIXED, y_train não é exigido e nenhum cálculo estatístico é realizado
res = select_features_in_fold(X_train, y_train=None, scenario=scenario_fixed)

assert res.selected_features == ("dap", "ht")
assert res.strategy_name == "FIXED"
assert len(res.scores) == 0
assert len(res.fitted_params) == 0
```

- **Resultado Esperado:** Retorno imediato dos atributos estáticos pré-declarados, sem dependência do alvo (`y_train=None`) e sem vazamento de dados.

---

### 2.3 Seleção Dinâmica Intra-Fold via Variância (`VARIANCE_THRESHOLD`) (SEL-03)

```python
import numpy as np
from experimental_ml.features import FeatureScenario, ScenarioMode, select_features_in_fold

scenario_var = FeatureScenario(
    scenario_id="dyn_variance",
    name="Variance Filter",
    description="Filter quasi-constant features",
    scientific_justification="Low variance elimination",
    mode=ScenarioMode.DYNAMIC,
    strategy_name="VARIANCE_THRESHOLD",
    strategy_params={"threshold": 0.5},
)

X_train = {
    "feat_high": np.array([1.0, 5.0, 10.0, 20.0]),  # variância elevada (~70.0)
    "feat_med": np.array([1.0, 2.0, 3.0, 4.0]),      # variância média (~1.67)
    "feat_low": np.array([1.0, 1.05, 1.0, 1.05]),    # variância quasi-constante (~0.0008)
    "feat_const": np.array([3.0, 3.0, 3.0, 3.0]),    # variância nula (0.0)
}

res = select_features_in_fold(X_train, y_train=None, scenario=scenario_var)

# Apenas as features que excedem o limiar de 0.5 devem ser selecionadas, ordenadas por variância decrescente
assert res.selected_features == ("feat_high", "feat_med")
assert res.scores["feat_high"] > res.scores["feat_med"]
assert res.strategy_name == "VARIANCE_THRESHOLD"
assert res.fitted_params["threshold"] == 0.5
```

- **Resultado Esperado:** Filtragem de atributos numéricos pela variância amostral calculada estritamente sobre `X_train`, ordenados decrescentemente.

---

### 2.4 Seleção Dinâmica Supervisionada (`TOP_K_RELEVANCE`) (SEL-04)

```python
import numpy as np
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.features import FeatureScenario, ScenarioMode, select_features_in_fold

scenario_topk = FeatureScenario(
    scenario_id="dyn_topk",
    name="Top K Relevance",
    description="Select top 2 features by association with y",
    scientific_justification="Univariate association ranking",
    mode=ScenarioMode.DYNAMIC,
    strategy_name="TOP_K_RELEVANCE",
    strategy_params={"k": 2},
)

# 1. Estratégia supervisionada exige y_train obrigatório
try:
    select_features_in_fold({"f1": np.array([1.0, 2.0])}, y_train=None, scenario=scenario_topk)
    assert False, "Deveria ter lançado ContractViolationError por ausência de y_train"
except ContractViolationError:
    pass

# 2. Execução com dados sintéticos correlacionados
np.random.seed(42)
n = 60
y_train = np.linspace(10.0, 50.0, n)
feat_strong = y_train + np.random.normal(0, 0.2, n)
feat_moderate = 0.6 * y_train + np.random.normal(0, 4.0, n)
feat_noise = np.random.normal(0, 1.0, n)

X_train = {
    "feat_strong": feat_strong,
    "feat_moderate": feat_moderate,
    "feat_noise": feat_noise,
}

res = select_features_in_fold(X_train, y_train=y_train, scenario=scenario_topk)

assert len(res.selected_features) == 2
assert res.selected_features == ("feat_strong", "feat_moderate")
assert "feat_noise" not in res.selected_features
assert res.scores["feat_strong"] > res.scores["feat_moderate"]
```

- **Resultado Esperado:** Seleção dos top-$k$ preditores ranqueados por métrica de associação com o alvo ajustada no treino.

---

### 2.5 Projeção Estrita em Dados de Avaliação (`apply_feature_selection`) (SEL-05)

```python
import numpy as np
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.features import SelectionResult, apply_feature_selection

selection_res = SelectionResult(
    selected_features=("feat_b", "feat_a"),
    scores={"feat_b": 0.9, "feat_a": 0.7},
    strategy_name="TOP_K_RELEVANCE",
)

X_eval = {
    "feat_a": np.array([10.0, 20.0]),
    "feat_b": np.array([30.0, 40.0]),
    "feat_c": np.array([50.0, 60.0]),
}

# 1. Projeção preserva ordem exata de selected_features e exclui colunas não selecionadas
filtered = apply_feature_selection(X_eval, selection_res)
assert list(filtered.keys()) == ["feat_b", "feat_a"]
assert np.array_equal(filtered["feat_b"], np.array([30.0, 40.0]))
assert "feat_c" not in filtered

# 2. Ausência de coluna selecionada em dados de avaliação levanta ContractViolationError
X_eval_missing = {"feat_a": np.array([10.0, 20.0])}
try:
    apply_feature_selection(X_eval_missing, selection_res)
    assert False, "Deveria ter lançado ContractViolationError"
except ContractViolationError:
    pass
```

- **Resultado Esperado:** Filtragem pura que projeta a seleção sobre dados de teste/validação, preservando a ordem canônica e rejeitando colunas faltantes.

---

### 2.6 Métricas de Estabilidade de Seleção Intra-Fold (SEL-06)

```python
import pytest
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.features import compute_selection_stability

# 1. Selections perfeitamente idênticas across folds
folds_identical = [
    ["f1", "f2", "f3"],
    ["f1", "f2", "f3"],
    ["f1", "f2", "f3"],
]
rep_id = compute_selection_stability(folds_identical, n_total_candidates=10)
assert rep_id.mean_jaccard == 1.0
assert rep_id.std_jaccard == 0.0
assert pytest.approx(rep_id.mean_kuncheva, abs=1e-6) == 1.0
assert rep_id.std_kuncheva == 0.0

# 2. Concordância parcial com cálculo analítico conhecido
# N = 10, k1 = 3, k2 = 3, r = 2 -> Jaccard = 2/4 = 0.5, Kuncheva = 11/21 ~ 0.5238
folds_partial = [
    ["f1", "f2", "f3"],
    ["f1", "f2", "f4"],
]
rep_part = compute_selection_stability(folds_partial, n_total_candidates=10)
assert rep_part.mean_jaccard == 0.5
assert pytest.approx(rep_part.mean_kuncheva, abs=1e-6) == (11.0 / 21.0)

# 3. Validações de entrada: recusa menos de 2 folds ou pool N menor que tamanho de seleção
try:
    compute_selection_stability([["f1"]], n_total_candidates=5)
    assert False, "Deveria ter lançado ConfigurationError por folds < 2"
except ConfigurationError:
    pass
```

- **Resultado Esperado:** Cálculo exato das matrizes par a par e agregadas de Jaccard e Kuncheva corrigido para o acaso.

---

### 2.7 Tratamento de Degenerescência e Rejeição de Seleções Vazias (SEL-07)

```python
import numpy as np
from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.features import FeatureScenario, ScenarioMode, select_features_in_fold

scenario_unreachable = FeatureScenario(
    scenario_id="dyn_unreachable",
    name="Impossible Threshold",
    description="Excessive threshold",
    scientific_justification="Test degeneracy",
    mode=ScenarioMode.DYNAMIC,
    strategy_name="VARIANCE_THRESHOLD",
    strategy_params={"threshold": 9999.0},
)

X_train = {
    "f1": np.array([1.0, 2.0, 3.0]),
    "f2": np.array([4.0, 5.0, 6.0]),
}

try:
    select_features_in_fold(X_train, y_train=None, scenario=scenario_unreachable)
    assert False, "Deveria ter lançado DataIntegrityError"
except DataIntegrityError as err:
    assert "resulted in 0 selected features" in str(err)
```

- **Resultado Esperado:** Detecção precoce de degenerescência com emissão de `DataIntegrityError`, impedindo que matrizes com 0 atributos avancem para o ajuste de estimadores.

---

## 3. Cenário Integrado de Validação Cruzada sem Vazamento de Dados (SEL-08, XCUT-02)

O script abaixo executa um pipeline de ponta a ponta simulando 5 folds de validação cruzada com seleção dinâmica no treino, projeção na validação, cálculo de estabilidade e verificação de pureza de runtime:

```python
import subprocess
import sys
import numpy as np

from experimental_ml.core.enums import TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features import (
    FeatureScenario,
    ScenarioMode,
    apply_feature_selection,
    compute_selection_stability,
    select_features_in_fold,
)
from experimental_ml.validation import (
    PartitionConfig,
    build_partition_plan,
)

# 1. Geração de dataset experimental sintético
np.random.seed(999)
n = 100
x_base = np.linspace(0.0, 20.0, n)
y = 2.5 * x_base + np.random.normal(0, 1.0, n)

data = {
    "f1": x_base + np.random.normal(0, 0.5, n),
    "f2": 2.0 * x_base + np.random.normal(0, 1.0, n),
    "f3": -1.5 * x_base + np.random.normal(0, 2.0, n),
    "f4": np.random.normal(0, 5.0, n),
    "f5": np.sin(x_base * 3.0),
    "target": y,
}

schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.REGRESSION)
bundle = load_dataset(data, schema=schema)
profile = profile_dataset(bundle)
plan = create_preparation_plan(profile, [])
view = sanitize_dataset(bundle, profile, plan)

# 2. Particionamento em 5 folds
part_config = PartitionConfig(
    strategy="KFOLD",
    regime="CV_ONLY",
    n_splits=5,
    master_seed=42,
)
part_plan = build_partition_plan(bundle, part_config)
assert len(part_plan.folds) == 5

# 3. Execução intra-fold sem vazamento de dados
scenario = FeatureScenario(
    scenario_id="dyn_top_3",
    name="Top 3 Features",
    description="Selects top 3 features within each fold",
    scientific_justification="Leakage-free feature selection baseline",
    mode=ScenarioMode.DYNAMIC,
    strategy_name="TOP_K_RELEVANCE",
    strategy_params={"k": 3},
)

fold_selections = []
obs_id_to_idx = {oid: idx for idx, oid in enumerate(view.observation_ids)}

for fold in part_plan.folds:
    train_indices = np.array([obs_id_to_idx[oid] for oid in fold.train_ids])
    val_indices = np.array([obs_id_to_idx[oid] for oid in fold.val_ids])

    X_train = {feat: view.columns[feat][train_indices] for feat in view.candidate_feature_cols}
    y_train = view.columns["target"][train_indices]
    X_val = {feat: view.columns[feat][val_indices] for feat in view.candidate_feature_cols}

    # Seleção estritamente em treino
    sel_res = select_features_in_fold(X_train, y_train, scenario)
    assert len(sel_res.selected_features) == 3
    assert "f1" in sel_res.selected_features
    assert "f2" in sel_res.selected_features

    # Projeção no fold de validação
    X_val_selected = apply_feature_selection(X_val, sel_res)
    assert list(X_val_selected.keys()) == list(sel_res.selected_features)
    assert len(X_val_selected["f1"]) == len(val_indices)

    fold_selections.append(sel_res.selected_features)

# 4. Avaliação de estabilidade
stability = compute_selection_stability(fold_selections, n_total_candidates=len(view.candidate_feature_cols))
assert stability.n_folds == 5
assert stability.mean_jaccard >= 0.70
assert stability.mean_kuncheva >= 0.50
print(f"Estabilidade validada: Jaccard={stability.mean_jaccard:.3f}, Kuncheva={stability.mean_kuncheva:.3f}")

# 5. Pureza de runtime (XCUT-02)
forbidden = {"scipy", "sklearn", "pandas", "statsmodels"} & set(sys.modules)
assert not forbidden, f"Violação XCUT-02: módulos proibidos importados: {forbidden}"
print("Pureza de tempo de execução XCUT-02 comprovada com sucesso!")
```

---

## 4. Matriz de Aceitabilidade e Critérios de Conclusão

| Requisito | Descrição | Evidência Automatizada | Critério de Aceitação |
| :--- | :--- | :--- | :--- |
| **SEL-01** | Modelo imutável `SelectionResult` | `test_sel_01_selection_result_immutability` | Dataclass congelada com slots e MappingProxyType |
| **SEL-02** | Bypass imediato para cenários `FIXED` | `test_sel_02_fixed_scenario_bypass` | Retorno direto sem acessar `y_train` ou computar estatísticas |
| **SEL-03** | Estratégia intra-fold `VARIANCE_THRESHOLD` | `test_sel_03_variance_threshold_selection` | Filtragem e ordenação decrescente por variância estritamente em treino |
| **SEL-04** | Estratégia intra-fold `TOP_K_RELEVANCE` | `test_sel_04_top_k_relevance_selection` | Ranqueamento dos top-$k$ preditores por relevância estritamente em treino |
| **SEL-05** | Projeção em avaliação `apply_feature_selection` | `test_sel_05_apply_feature_selection` | Projeção canônica preservando ordem e rejeitando ausências |
| **SEL-06** | Medição de estabilidade Jaccard e Kuncheva | `test_sel_06_selection_stability_metrics` | Cálculo de matrizes e agregação com correção para o acaso |
| **SEL-07** | Rejeição de seleção vazia via `DataIntegrityError` | `test_sel_07_empty_selection_rejection` | Diagnóstico específico impedindo 0 atributos a jusante |
| **SEL-08** | Pipeline multi-fold sem vazamento e pureza XCUT-02 | `test_sel_08_multi_fold_selection_pipeline` | Execução integrada sem data leakage e zero dependências de ML |
