# Roteiro de Validação e Aceitação — Marco M4.2 (Pipeline de Pré-processamento em Duas Camadas)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M4.2 (`m4-2-two-layer-preprocessing`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e integradores do subsistema de pré-processamento e modelos do `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.models` e `experimental_ml.models.preprocessing`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e as exportações dos módulos estão íntegras:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e exportações dos módulos públicos
python -c "
import experimental_ml.models as m
import experimental_ml.models.preprocessing as prep
print('Models exportacoes:', len(m.__all__))
print('Preprocessing exportacoes:', len(prep.__all__))
"
```

- **Resultado Esperado:** Mensagem confirmando 20 símbolos em `experimental_ml.models` e 13 símbolos em `experimental_ml.models.preprocessing`.
- **Símbolos Públicos Canônicos:**
  - Em `experimental_ml.models`: `ScalerType`, `TwoLayerPreprocessingSpec`, `TwoLayerPreprocessingState`, `validate_two_layer_preprocessing`, `fit_two_layer_preprocessing`, `apply_two_layer_preprocessing` (além dos contratos M4.1).
  - Em `experimental_ml.models.preprocessing`: `ScalerType`, `PreprocessingStepSpec`, `TwoLayerPreprocessingSpec`, `TwoLayerPreprocessingState`, `StandardScaler`, `MinMaxScaler`, `MaxAbsScaler`, `RobustScaler`, `AngularScaler`, `PrecomputedKernelAdapter`, `validate_two_layer_preprocessing`, `fit_two_layer_preprocessing`, `apply_two_layer_preprocessing`.
- **Critério de Falha:** `ModuleNotFoundError`, `ImportError` ou ausência dos símbolos canônicos.

---

## 2. Roteiro de Testes de Aceitação por Capacidade

### 2.1 Tipos Declarativos, Especificações e Estado Imutável (`PRE-01`)

```python
from types import MappingProxyType
import pytest
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models.preprocessing import (
    ScalerType,
    PreprocessingStepSpec,
    TwoLayerPreprocessingSpec,
    TwoLayerPreprocessingState,
)

# 1. ScalerType Enum fechado com 6 membros canônicos
assert len(ScalerType) == 6
assert set(ScalerType.__members__.keys()) == {
    "STANDARD", "MINMAX", "MAXABS", "ROBUST", "ANGULAR", "NONE"
}

# 2. PreprocessingStepSpec imutável com slots e MappingProxyType
step1 = PreprocessingStepSpec(
    step_id="imputer_num",
    transformer_type="PASSTHROUGH",
    parameters={"strategy": "median"},
    description="Imputador de cenário",
)
assert step1.step_id == "imputer_num"
assert isinstance(step1.parameters, MappingProxyType)
with pytest.raises((AttributeError, TypeError)):
    step1.step_id = "mutated"  # type: ignore[misc]

# 3. TwoLayerPreprocessingSpec imutável com tuplas em slots
step2 = PreprocessingStepSpec(step_id="std_scale", transformer_type="STANDARD")
spec = TwoLayerPreprocessingSpec(
    layer1_steps=[step1],
    layer2_steps=[step2],
    description="Pipeline bidimensional de teste",
)
assert isinstance(spec.layer1_steps, tuple)
assert isinstance(spec.layer2_steps, tuple)
assert spec.layer1_steps[0] is step1
assert spec.layer2_steps[0] is step2

# 4. TwoLayerPreprocessingState imutável
state = TwoLayerPreprocessingState(
    spec=spec,
    layer1_fitted_state=("fitted_imputer",),
    layer2_fitted_state=("fitted_scaler",),
)
assert state.spec is spec
with pytest.raises((AttributeError, TypeError)):
    state.layer1_fitted_state = ()  # type: ignore[misc]
```

- **Resultado Esperado:** Asserções aprovadas sem exceções; tentativas de mutação bloqueadas.
- **Critério de Falha:** Erro de tipo ou mutabilidade permitida.

---

### 2.2 Detecção de Duplicação Acidental e Validação Declarativa (`PRE-02`, `CA-E3-02`)

```python
import pytest
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models.preprocessing import (
    PreprocessingStepSpec,
    TwoLayerPreprocessingSpec,
    validate_two_layer_preprocessing,
)

# 1. Validação de especificação válida sem mutação
s_l1 = PreprocessingStepSpec(step_id="imputer", transformer_type="PASSTHROUGH")
s_l2 = PreprocessingStepSpec(step_id="scaler", transformer_type="STANDARD")
valid_spec = TwoLayerPreprocessingSpec(layer1_steps=(s_l1,), layer2_steps=(s_l2,))
assert validate_two_layer_preprocessing(valid_spec) is valid_spec

# 2. Bloqueio de duplicação exata de transformação entre Camada 1 e Camada 2 (CA-E3-02)
dup_spec = TwoLayerPreprocessingSpec(
    layer1_steps=(PreprocessingStepSpec(step_id="scale_l1", transformer_type="STANDARD"),),
    layer2_steps=(PreprocessingStepSpec(step_id="scale_l2", transformer_type="STANDARD"),),
)
with pytest.raises(ConfigurationError, match="Accidental duplication detected"):
    validate_two_layer_preprocessing(dup_spec)

# 3. Bloqueio de escalonadores redundantes/conflitantes entre camadas (ex.: MINMAX na L1 e STANDARD na L2)
conflict_spec = TwoLayerPreprocessingSpec(
    layer1_steps=(PreprocessingStepSpec(step_id="minmax_l1", transformer_type="MINMAX"),),
    layer2_steps=(PreprocessingStepSpec(step_id="std_l2", transformer_type="STANDARD"),),
)
with pytest.raises(ConfigurationError, match="redundant scalers declared"):
    validate_two_layer_preprocessing(conflict_spec)

# 4. Pipeline pass-through vazio é válido
empty_spec = TwoLayerPreprocessingSpec()
assert validate_two_layer_preprocessing(empty_spec) is empty_spec
```

- **Resultado Esperado:** Validações funcionais aprovadas e conflitos rejeitados com `ConfigurationError`.
- **Critério de Falha:** Conflitos aceitos sem erro ou rejeição indevida do pipeline vazio.

---

### 2.3 Ajuste Intra-Fold com Projeção Intermediária e Garantia Anti-Leakage (`PRE-03`, `CA-E4B-01`)

```python
import numpy as np
import pytest
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.preprocessing import (
    PreprocessingStepSpec,
    TwoLayerPreprocessingSpec,
    TwoLayerPreprocessingState,
    fit_two_layer_preprocessing,
)

# 1. Ajuste sequencial: Camada 1 -> projeção X_inter -> Camada 2
s1 = PreprocessingStepSpec(step_id="pass_l1", transformer_type="PASSTHROUGH")
s2 = PreprocessingStepSpec(step_id="std_l2", transformer_type="STANDARD")
spec = TwoLayerPreprocessingSpec(layer1_steps=(s1,), layer2_steps=(s2,))

X_train = np.array([
    [10.0, 100.0],
    [20.0, 200.0],
    [30.0, 300.0],
])
state = fit_two_layer_preprocessing(spec, X_train)
assert isinstance(state, TwoLayerPreprocessingState)
assert len(state.layer1_fitted_state) == 1
assert len(state.layer2_fitted_state) == 1

scaler_l2 = state.layer2_fitted_state[0]
assert np.allclose(scaler_l2.mean_, [20.0, 200.0])

# 2. Rejeição de entradas inválidas
with pytest.raises(ContractViolationError, match="must be a 2D array"):
    fit_two_layer_preprocessing(spec, np.array([1.0, 2.0]))

with pytest.raises(ContractViolationError, match="must not be empty"):
    fit_two_layer_preprocessing(spec, np.empty((0, 2)))

with pytest.raises(ContractViolationError, match="non-finite values"):
    fit_two_layer_preprocessing(spec, np.array([[np.nan, 1.0], [2.0, 3.0]]))
```

- **Resultado Esperado:** Estatísticas ajustadas estritamente a partir de `X_train` e violações dimensionais rejeitadas.
- **Critério de Falha:** Cálculo com contaminação externa ou aceitação de `NaN`/dimensões inválidas.

---

### 2.4 Projeção Funcional sem Estado em Avaliação (`PRE-04`)

```python
import numpy as np
import pytest
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.preprocessing import (
    PreprocessingStepSpec,
    TwoLayerPreprocessingSpec,
    apply_two_layer_preprocessing,
    fit_two_layer_preprocessing,
)

s1 = PreprocessingStepSpec(step_id="pass_l1", transformer_type="PASSTHROUGH")
s2 = PreprocessingStepSpec(step_id="std_l2", transformer_type="STANDARD")
spec = TwoLayerPreprocessingSpec(layer1_steps=(s1,), layer2_steps=(s2,))

# Treino: média = 20.0
X_train = np.array([[10.0], [20.0], [30.0]])
state = fit_two_layer_preprocessing(spec, X_train)

# Avaliação com o valor da média de treino: deve projetar estritamente para 0.0
X_eval = np.array([[20.0]])
X_eval_proj = apply_two_layer_preprocessing(state, X_eval)
assert np.allclose(X_eval_proj[0, 0], 0.0)

# Verificação de imutabilidade do estado
scaler_before_mean = float(state.layer2_fitted_state[0].mean_[0])
X_extreme = np.array([[10000.0], [-5000.0]])
apply_two_layer_preprocessing(state, X_extreme)
assert float(state.layer2_fitted_state[0].mean_[0]) == scaler_before_mean

# Rejeição de incompatibilidade no número de features
with pytest.raises(ContractViolationError, match="Feature count mismatch"):
    apply_two_layer_preprocessing(state, np.array([[1.0, 2.0]]))
```

- **Resultado Esperado:** Projeção determinística sem alteração do estado pré-ajustado.
- **Critério de Falha:** Modificação de parâmetros pré-ajustados ou tolerância a contagem incorreta de colunas.

---

### 2.5 Escalonadores Numéricos Puros em NumPy com Salvaguardas (`PRE-05`, `XCUT-02`)

```python
import numpy as np
from experimental_ml.models.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    MaxAbsScaler,
    RobustScaler,
    AngularScaler,
)

# 1. StandardScaler com coluna constante (variância zero)
X_std = np.array([[10.0, 5.0], [20.0, 5.0], [30.0, 5.0]])
std = StandardScaler().fit(X_std)
Xt_std = std.transform(X_std)
assert np.allclose(np.mean(Xt_std[:, 0]), 0.0)
assert np.allclose(np.var(Xt_std[:, 0]), 1.0)
assert np.allclose(Xt_std[:, 1], [0.0, 0.0, 0.0])  # Coluna constante -> 0.0

# 2. MinMaxScaler com coluna constante
X_mm = np.array([[1.0, 7.0], [5.0, 7.0], [9.0, 7.0]])
mm = MinMaxScaler(feature_range=(-1.0, 1.0)).fit(X_mm)
Xt_mm = mm.transform(X_mm)
assert np.allclose(Xt_mm[:, 0], [-1.0, 0.0, 1.0])
assert np.allclose(Xt_mm[:, 1], [-1.0, -1.0, -1.0])  # Coluna constante -> limite inferior -1.0

# 3. MaxAbsScaler com coluna nula
X_ma = np.array([[2.0, 0.0], [-10.0, 0.0], [5.0, 0.0]])
ma = MaxAbsScaler().fit(X_ma)
Xt_ma = ma.transform(X_ma)
assert np.allclose(Xt_ma[:, 0], [0.2, -1.0, 0.5])
assert np.allclose(Xt_ma[:, 1], [0.0, 0.0, 0.0])  # Coluna zero -> 0.0

# 4. RobustScaler com mediana e IQR
X_rob = np.array([[10.0, 4.0], [20.0, 4.0], [30.0, 4.0], [100.0, 4.0]])
rob = RobustScaler().fit(X_rob)
Xt_rob = rob.transform(X_rob)
assert np.allclose(np.median(Xt_rob[:, 0]), 0.0)
assert np.allclose(Xt_rob[:, 1], [0.0, 0.0, 0.0, 0.0])  # Coluna IQR zero -> 0.0

# 5. AngularScaler para portas quânticas [0, pi]
X_ang = np.array([[0.0], [50.0], [100.0]])
ang = AngularScaler(target_range=(0.0, np.pi)).fit(X_ang)
Xt_ang = ang.transform(X_ang)
assert np.allclose(Xt_ang[:, 0], [0.0, np.pi / 2.0, np.pi])
```

- **Resultado Esperado:** Todas as transformações produzem escalas matematicamente corretas, sem `ZeroDivisionError`, `NaN` ou `Inf`.
- **Critério de Falha:** Divisão por zero em colunas constantes ou distorção de escala.

---

### 2.6 Adaptador de Kernel Pré-computado e Passagem de Partição (`PRE-06`, `RF3.4`)

```python
import numpy as np
import pytest
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.preprocessing import PrecomputedKernelAdapter

# 1. Função de kernel linear simples
def linear_kernel(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.dot(A, B.T)

adapter = PrecomputedKernelAdapter(kernel_func=linear_kernel)
X_train = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])  # 3 amostras
adapter.fit(X_train)

assert adapter.n_train_samples_ == 3
assert adapter.X_train_ is not None

# 2. Avaliação de inferência passando (X_eval, X_train)
X_eval = np.array([[2.0, 3.0], [4.0, 5.0]])  # 2 amostras
K_eval = adapter.transform(X_eval)

assert K_eval.shape == (2, 3)
assert np.allclose(K_eval, [[2.0, 3.0, 5.0], [4.0, 5.0, 9.0]])

# 3. Rejeição de matriz não quadrada no treino
def bad_kernel(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.ones((A.shape[0], A.shape[0] + 1))

bad_adapter = PrecomputedKernelAdapter(kernel_func=bad_kernel)
with pytest.raises(ContractViolationError, match="must be square"):
    bad_adapter.fit(X_train)
```

- **Resultado Esperado:** Passagem correta de partição $(X_{\text{train}}, X_{\text{train}})$ no ajuste e $(X_{\text{eval}}, X_{\text{train}})$ na transformação; validação dimensional estrita.
- **Critério de Falha:** Avaliação $(X_{\text{eval}}, X_{\text{eval}})$ em inferência (vazamento/erro de contrato de Gram) ou tolerância a matrizes não quadradas no treino.

---

### 2.7 API Pública e Pureza de Runtime (`PRE-07`, `XCUT-01`, `XCUT-02`)

```bash
# Execução de subprocesso puro verificando dependência única do runtime
python -c "
import sys
import experimental_ml.models.preprocessing
forbidden = ['sklearn', 'scipy', 'torch', 'tensorflow', 'jax', 'qiskit']
loaded = [p for p in forbidden if any(m.startswith(p) for m in sys.modules)]
if loaded:
    print(f'VIOLACAO: pacotes proibidos importados: {loaded}')
    sys.exit(1)
assert 'numpy' in sys.modules, 'numpy deve estar carregado'
print('PUREZA_RUNTIME_OK: apenas numpy carregado!')
"
```

- **Resultado Esperado:** `PUREZA_RUNTIME_OK: apenas numpy carregado!` com código de saída 0.
- **Critério de Falha:** Importação acidental de `scikit-learn`, `scipy`, ou qualquer biblioteca de ML externa.

---

## 3. Cenário Integrado de Ponta a Ponta: Fold Experimental com Modelo Clássico

O exemplo a seguir simula uma iteração completa de validação cruzada (*fold*), combinando:
1. Pré-processamento em duas camadas (Camada 1: limpeza/passthrough, Camada 2: `StandardScaler`).
2. Ajuste do pré-processamento estritamente sobre `X_train`.
3. Projeção de treino e ajuste de modelo (M4.1).
4. Projeção funcional sem estado sobre `X_eval` e inferência.

```python
import numpy as np
from experimental_ml.models import (
    ModelFamily,
    ModelSpec,
    ModelCapabilities,
    DummyBaselineModel,
    fit_model,
    predict_model,
    TwoLayerPreprocessingSpec,
    validate_two_layer_preprocessing,
    fit_two_layer_preprocessing,
    apply_two_layer_preprocessing,
)
from experimental_ml.models.preprocessing import PreprocessingStepSpec

# 1. Definir especificação do pré-processamento em duas camadas
prep_spec = TwoLayerPreprocessingSpec(
    layer1_steps=(
        PreprocessingStepSpec(step_id="l1_clean", transformer_type="PASSTHROUGH"),
    ),
    layer2_steps=(
        PreprocessingStepSpec(step_id="l2_scale", transformer_type="STANDARD"),
    ),
    description="Preprocessamento do fold experimental",
)
validated_prep_spec = validate_two_layer_preprocessing(prep_spec)

# 2. Dados do fold
X_train = np.array([
    [10.0, 100.0],
    [20.0, 200.0],
    [30.0, 300.0],
    [40.0, 400.0],
])
y_train = np.array([1.0, 2.0, 3.0, 4.0])

X_eval = np.array([
    [25.0, 250.0],
    [15.0, 150.0],
])

# 3. Ajustar pré-processamento intra-fold (anti-leakage)
prep_state = fit_two_layer_preprocessing(validated_prep_spec, X_train)

# 4. Projetar treino
X_train_transformed = apply_two_layer_preprocessing(prep_state, X_train)
assert np.allclose(np.mean(X_train_transformed, axis=0), [0.0, 0.0])

# 5. Ajustar modelo sobre dados transformados
model_spec = ModelSpec(
    model_id="baseline_fold_model",
    display_name="Fold Baseline Regressor",
    family=ModelFamily.BASELINE_MODEL,
    estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
    capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
)
fitted_estimator = fit_model(model_spec, X_train_transformed, y_train)

# 6. Projetar conjunto de avaliação sem vazamento
X_eval_transformed = apply_two_layer_preprocessing(prep_state, X_eval)
assert np.allclose(X_eval_transformed[0], [0.0, 0.0])  # Média de treino projeta para 0.0

# 7. Previsão sobre conjunto de avaliação
predictions = predict_model(fitted_estimator, X_eval_transformed)
assert len(predictions) == 2
assert np.allclose(predictions, [2.5, 2.5])  # Média de y_train é 2.5

print("CENARIO_INTEGRADO_PONTUAL_SUCESSO")
```

- **Resultado Esperado:** Mensagem `CENARIO_INTEGRADO_PONTUAL_SUCESSO` sem advertências ou falhas numéricas.

---

## 4. Classificação e Diagnóstico de Falhas

| Sintoma / Erro | Causa Provável | Ação Recomendada |
| :--- | :--- | :--- |
| `ConfigurationError: Accidental duplication detected (CA-E3-02)` | O mesmo escalonador ou tipo de transformação foi declarado tanto na Camada 1 quanto na Camada 2. | Remover a etapa redundante de uma das camadas ou utilizar transformadores complementares (ex.: imputador na L1, escalonador na L2). |
| `ContractViolationError: Feature count mismatch` | `X_eval` possui dimensionalidade diferente daquela observada no `fit_two_layer_preprocessing`. | Verificar se as partições de treino e teste originam-se do mesmo conjunto de atributos e sanitização. |
| `ContractViolationError: X_train contains non-finite values` | Dados contêm `NaN` ou `Inf` que não foram previamente imputados. | Incluir etapa de imputação na Camada 1 ou sanitizar os dados na Etapa 2. |
| `ContractViolationError: Kernel matrix must be square` | A função de kernel fornecida ao `PrecomputedKernelAdapter` retornou formato inválido. | Ajustar a função de kernel para retornar matriz quadrada $(N, N)$ ao receber $(X, X)$. |

---

## 5. Taxonomia dos Testes Automatizados

| Nível | Arquivos de Teste | Quantidade de Testes | Objetivo |
| :--- | :--- | :---: | :--- |
| **Unidade** | `tests/unit/models/test_preprocessing_types.py` | 4 | Validação de tipos, dataclasses imutáveis, slots e `ScalerType`. |
| **Unidade** | `tests/unit/models/test_preprocessing_validation.py` | 4 | Validação declarativa e bloqueio de duplicações acidentais (`CA-E3-02`). |
| **Unidade** | `tests/unit/models/test_preprocessing_fit.py` | 3 | Ajuste intra-fold estrito sobre `X_train` e anti-leakage (`CA-E4B-01`). |
| **Unidade** | `tests/unit/models/test_preprocessing_apply.py` | 3 | Projeção funcional sem estado e validação de dimensionalidade. |
| **Unidade** | `tests/unit/models/test_preprocessing_scalers.py` | 5 | Escalonadores puros em NumPy com salvaguardas de variância zero. |
| **Unidade** | `tests/unit/models/test_preprocessing_kernel.py` | 3 | Adaptador de kernel e passagem $(X_{\text{train}}, X_{\text{train}})$ / $(X_{\text{eval}}, X_{\text{train}})$. |
| **Integração**| `tests/integration/models/test_preprocessing_integration.py` | 3 | Exportações públicas, pureza de runtime e pipeline ponta a ponta. |
| **Total M4.2**| **7 suítes** | **25 testes** | **100% aprovados** |
