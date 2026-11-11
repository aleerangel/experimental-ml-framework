# Roteiro de Validação e Aceitação — Marco M4.1 (Registro de Modelos, Capacidades e Contratos Funcionais)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M4.1 (`m4-1-model-registry-contracts`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e integradores do subsistema de modelos do `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.models`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e as exportações do módulo `models` estão íntegras:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e exportações do módulo models
python -c "import experimental_ml.models as m; print('Models importado com sucesso! Exportacoes:', len(m.__all__))"
```

- **Resultado Esperado:** Mensagem confirmando importação e 14 símbolos públicos exportados em `__all__`:
  `ModelId`, `ModelFamily`, `ModelCapabilities`, `ModelDiagnostics`, `ModelSpec`, `validate_model_spec`, `validate_models_catalog`, `instantiate_fresh_model`, `reset_active_instances`, `fit_model`, `predict_model`, `extract_model_diagnostics`, `DummyBaselineModel`, `AnalyticalBiometricModel`.
- **Critério de Falha:** `ModuleNotFoundError` para `experimental_ml.models` ou ausência de símbolos canônicos.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Declaração e Validação Pura de Especificações e Catálogo em Memória (`MOD-01`, `MOD-02`, `MOD-07`)

```python
from types import MappingProxyType
from experimental_ml.models import (
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    validate_model_spec,
    validate_models_catalog,
)

# 1. Especificação de modelo clássico
spec1 = ModelSpec(
    model_id="ridge_regression",
    display_name="Ridge Regressor",
    family=ModelFamily.CLASSICAL_ML,
    estimator_factory=lambda seed: object(),
    capabilities=ModelCapabilities(
        requires_fit=True,
        supports_predict=True,
        supports_uncertainty=False,
    ),
    description="Regressão Ridge com penalização L2",
    scientific_justification="Benchmark linear clássico",
    parameters={"alpha": 1.0},
)

# 2. Validação pura sem execuções colaterais
validated = validate_model_spec(spec1)
assert validated is spec1
assert isinstance(spec1.parameters, MappingProxyType)

# 3. Validação de catálogo em memória
spec2 = ModelSpec(
    model_id="clutter_equation",
    display_name="Analytical Clutter Model",
    family=ModelFamily.BIOMETRIC_MODEL,
    estimator_factory=lambda seed: object(),
    capabilities=ModelCapabilities(
        requires_fit=False,
        supports_predict=True,
    ),
    description="Equação analítica biométrica de clutter",
    scientific_justification="Equação baseada em índices espectrais",
)

catalog = validate_models_catalog([spec1, spec2])
assert isinstance(catalog, MappingProxyType)
assert len(catalog) == 2
assert "ridge_regression" in catalog
assert "clutter_equation" in catalog
```

- **Resultado Esperado:** Especificações validadas sem mutação de campos, parâmetros encapsulados em `MappingProxyType`, e catálogo retornado como mapeamento imutável indexado por `model_id`.

---

### 2.2 Instanciação Limpa e Isolamento Estrito de Memória (`MOD-03`, `CA-E3-01`)

```python
import pytest
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models import (
    DummyBaselineModel,
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    instantiate_fresh_model,
    reset_active_instances,
)

reset_active_instances()

spec = ModelSpec(
    model_id="baseline_dummy",
    display_name="Dummy Model",
    family=ModelFamily.BASELINE,
    estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
    capabilities=ModelCapabilities(),
    description="Baseline",
    scientific_justification="Benchmark",
)

# Instanciações sucessivas devem produzir instâncias desvinculadas
inst1 = instantiate_fresh_model(spec, seed=1)
inst2 = instantiate_fresh_model(spec, seed=2)
assert inst1 is not inst2

# Detecção e rejeição de singleton / instância reaproveitada
singleton_obj = DummyBaselineModel()
spec_singleton = ModelSpec(
    model_id="singleton_model",
    display_name="Singleton Model",
    family=ModelFamily.BASELINE,
    estimator_factory=lambda seed: singleton_obj,
    capabilities=ModelCapabilities(),
    description="Singleton",
    scientific_justification="Teste singleton",
)

first_inst = instantiate_fresh_model(spec_singleton)
with pytest.raises(ContractViolationError, match="Instance isolation breach"):
    instantiate_fresh_model(spec_singleton)
```

- **Resultado Esperado:** Instâncias consecutivas ocupam endereços distintos em memória; tentativas de reutilizar a mesma instância ativa disparam `ContractViolationError`.

---

### 2.3 Treinamento Funcional e Bypass Transparente de Modelos Analíticos (`MOD-04`, `RF3.2`)

```python
import numpy as np
from experimental_ml.models import (
    AnalyticalBiometricModel,
    DummyBaselineModel,
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    fit_model,
)

# 1. Treinável: ajuste executado exclusivamente nos dados fornecidos
spec_trainable = ModelSpec(
    model_id="dummy_mean",
    display_name="Mean Baseline",
    family=ModelFamily.BASELINE,
    estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
    capabilities=ModelCapabilities(requires_fit=True),
    description="Mean",
    scientific_justification="Mean",
)
model_tr = DummyBaselineModel(strategy="mean")
X_tr = np.array([[1.0], [2.0], [3.0]])
y_tr = np.array([10.0, 20.0, 30.0])

fitted_tr, diag_tr = fit_model(model_tr, spec_trainable, X_tr, y_tr)
assert fitted_tr.is_fitted is True
assert diag_tr.diagnostics["mean_"] == 20.0

# 2. Analítico: bypass transparente como no-op
spec_analytical = ModelSpec(
    model_id="bio_model",
    display_name="Analytical Bio",
    family=ModelFamily.BIOMETRIC_MODEL,
    estimator_factory=lambda seed: AnalyticalBiometricModel(),
    capabilities=ModelCapabilities(requires_fit=False),
    description="Analytical",
    scientific_justification="Bio",
)
model_an = AnalyticalBiometricModel()
fitted_an, diag_an = fit_model(model_an, spec_analytical, X_tr, y_tr)
assert fitted_an is model_an
assert diag_an.diagnostics["requires_fit"] is False
```

- **Resultado Esperado:** Modelos treináveis são ajustados e emitem diagnósticos de treinamento; modelos analíticos (`requires_fit=False`) sofrem bypass imediato sem chamadas de treino desnecessárias.

---

### 2.4 Inferência Funcional e Contrato Tripartite de Saídas (`MOD-05`, `MOD-08`)

```python
import numpy as np
from experimental_ml.models import (
    DummyBaselineModel,
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    fit_model,
    predict_model,
)

# Regressão com incerteza preditiva (média + desvio padrão)
spec_reg = ModelSpec(
    model_id="reg_baseline",
    display_name="Regression Baseline",
    family=ModelFamily.BASELINE,
    estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
    capabilities=ModelCapabilities(
        requires_fit=True,
        supports_predict=True,
        supports_uncertainty=True,
    ),
    description="Reg",
    scientific_justification="Reg",
)
model_reg = DummyBaselineModel(strategy="mean")
fit_model(model_reg, spec_reg, np.array([[1.0], [2.0], [3.0]]), np.array([10.0, 20.0, 30.0]))

out_reg = predict_model(model_reg, spec_reg, np.array([[100.0], [200.0]]))
assert isinstance(out_reg, dict)
assert set(out_reg.keys()) == {"y_pred", "y_std", "y_proba"}
assert np.allclose(out_reg["y_pred"], [20.0, 20.0])
assert out_reg["y_std"] is not None
assert np.all(out_reg["y_std"] >= 0.0)
assert out_reg["y_proba"] is None

# Classificação com probabilidades de classe
spec_clf = ModelSpec(
    model_id="clf_baseline",
    display_name="Classification Baseline",
    family=ModelFamily.BASELINE,
    estimator_factory=lambda seed: DummyBaselineModel(strategy="most_frequent"),
    capabilities=ModelCapabilities(
        requires_fit=True,
        supports_predict=True,
        supports_predict_proba=True,
    ),
    description="Clf",
    scientific_justification="Clf",
)
model_clf = DummyBaselineModel(strategy="most_frequent")
fit_model(model_clf, spec_clf, np.array([[1.0], [2.0], [3.0]]), np.array(["pos", "neg", "pos"]))

out_clf = predict_model(model_clf, spec_clf, np.array([[10.0], [20.0]]))
assert np.array_equal(out_clf["y_pred"], ["pos", "pos"])
assert out_clf["y_std"] is None
assert out_clf["y_proba"] is not None
assert out_clf["y_proba"].ndim == 2
assert np.allclose(np.sum(out_clf["y_proba"], axis=1), 1.0)
```

- **Resultado Esperado:** Dicionário tripartite padronizado com chaves `y_pred`, `y_std`, `y_proba`; validação rigorosa de finitude, não-negatividade e soma unitária em simplex.

---

### 2.5 Snapshot Imutável de Diagnósticos Internos (`MOD-06`, `RF3.6`)

```python
import numpy as np
from types import MappingProxyType
from experimental_ml.models import (
    DummyBaselineModel,
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    extract_model_diagnostics,
    fit_model,
)

spec = ModelSpec(
    model_id="diag_check",
    display_name="Diag Check",
    family=ModelFamily.BASELINE,
    estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
    capabilities=ModelCapabilities(),
    description="Diag",
    scientific_justification="Diag",
)
model = DummyBaselineModel(strategy="mean")
fit_model(model, spec, np.array([[1.0], [2.0]]), np.array([5.0, 15.0]))

diag = extract_model_diagnostics(model, spec, phase="fit")
assert isinstance(diag.diagnostics, MappingProxyType)
assert diag.diagnostics["mean_"] == 10.0

# Mutação posterior do modelo não altera o snapshot extraído
model.mean_ = 9999.0
assert diag.diagnostics["mean_"] == 10.0
```

- **Resultado Esperado:** Diagnósticos convertidos recursivamente para tipos primitivos imutáveis e `MappingProxyType`, permanecendo desacoplados de mutações subsequentes no estimador.

---

### 2.6 Pureza de Dependências de Runtime (`MOD-09`, `XCUT-02`)

```bash
python -c "
import sys
import experimental_ml.models
forbidden = ['sklearn', 'scipy', 'torch', 'tensorflow', 'jax', 'qiskit']
loaded = [p for p in forbidden if any(m.startswith(p) for m in sys.modules)]
assert not loaded, f'Dependencias proibidas carregadas: {loaded}'
assert 'numpy' in sys.modules
print('PURE_NUMPY_OK')
"
```

- **Resultado Esperado:** Impressão de `PURE_NUMPY_OK` sem que pacotes proibidos de ML sejam importados de forma mandatória.

---

## 3. Resumo dos Critérios de Aceitação Verificados

| Critério | Descrição | Status |
| :--- | :--- | :---: |
| **MOD-01** | `ModelFamily` com 9 membros canônicos, `ModelCapabilities` e `ModelDiagnostics` imutáveis com slots | **APROVADO** |
| **MOD-02** | `ModelSpec` declarativo e validação pura sem execução colateral via `validate_model_spec` | **APROVADO** |
| **MOD-03** | Instanciação limpa com controle de sementes e auditoria de isolamento de memória (`CA-E3-01`) | **APROVADO** |
| **MOD-04** | Treinamento funcional de modelos e bypass transparente para equações analíticas (`RF3.2`) | **APROVADO** |
| **MOD-05** | Inferência funcional com validação tripartite de saídas (`y_pred`, `y_std`, `y_proba`) e verificação em simplex | **APROVADO** |
| **MOD-06** | Extração de diagnósticos com snapshot imutável profundo e rejeição de complexos mutáveis (`RF3.6`) | **APROVADO** |
| **MOD-07** | Validação de catálogo de modelos em memória e detecção de duplicidade de identificadores | **APROVADO** |
| **MOD-08** | Implementação de baselines canônicos (`mean`, `median`, `most_frequent`) e modelo biométrico analítico | **APROVADO** |
| **MOD-09** | Pureza arquitetural com dependência exclusiva de `numpy>=1.24.0` e sem importações de ML de terceiros (`XCUT-02`) | **APROVADO** |
