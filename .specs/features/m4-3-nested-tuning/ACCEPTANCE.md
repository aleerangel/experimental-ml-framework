# Roteiro de Validação e Aceitação — Marco M4.3 (Otimização de Hiperparâmetros Aninhada Intra-Fold)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M4.3 (`m4-3-nested-tuning`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e integradores do subsistema de otimização de hiperparâmetros do `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.tuning`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e as exportações dos módulos estão íntegras:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de exportações dos símbolos públicos canônicos
python -c "
import experimental_ml.tuning as tuning
print('Tuning exportacoes publicas:', len(tuning.__all__))
print('Simbolos:', sorted(tuning.__all__))
"
```

- **Resultado Esperado:** Mensagem confirmando 9 símbolos exportados em `experimental_ml.tuning.__all__`.
- **Símbolos Públicos Canônicos:**
  - `HyperparameterSearchSpec`, `SearchStrategy`, `TuningOptimizationError`, `TuningResult`, `TuningTrialRecord`, `generate_candidates`, `run_nested_tuning`, `split_inner_folds`, `validate_search_spec`.
- **Critério de Falha:** `ModuleNotFoundError`, `ImportError` ou ausência de qualquer um dos 9 símbolos canônicos.

---

## 2. Roteiro de Testes de Aceitação por Capacidade

### 2.1 Tipos Declarativos, Especificações e Estruturas de Resultado (`TUN-01` / `US-M43-01`)

```python
from types import MappingProxyType
import pytest
from experimental_ml.core.enums import MetricDirection, MetricStatus
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.tuning import (
    HyperparameterSearchSpec,
    SearchStrategy,
    TuningOptimizationError,
    TuningResult,
    TuningTrialRecord,
)

# 1. Enum fechado SearchStrategy com 4 membros canônicos
assert len(SearchStrategy) == 4
assert set(SearchStrategy.__members__.keys()) == {
    "FIXED", "GRID_SEARCH", "RANDOM_SEARCH", "CUSTOM_TUNER"
}

# 2. HyperparameterSearchSpec imutável com slots e MappingProxyType
spec = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.GRID_SEARCH,
    param_grid={"alpha": [0.01, 0.1, 1.0], "max_iter": (100, 200)},
    optimization_metric="RMSE",
    direction=MetricDirection.MINIMIZE,
    n_iter=None,
    inner_cv_folds=3,
    seed=42,
    description="Grade de regularização Ridge",
)
assert spec.search_strategy == SearchStrategy.GRID_SEARCH
assert isinstance(spec.param_grid, MappingProxyType)
assert spec.param_grid["alpha"] == (0.01, 0.1, 1.0)
with pytest.raises((AttributeError, TypeError)):
    spec.inner_cv_folds = 5  # type: ignore[misc]

# 3. TuningTrialRecord imutável com histórico por fold
trial = TuningTrialRecord(
    trial_index=0,
    params={"alpha": 0.01},
    fold_scores=(0.12, 0.14, 0.11),
    mean_score=0.1233,
    status=MetricStatus.VALID,
    error_message=None,
)
assert trial.trial_index == 0
assert isinstance(trial.params, MappingProxyType)
assert isinstance(trial.fold_scores, tuple)
assert trial.status == MetricStatus.VALID
with pytest.raises((AttributeError, TypeError)):
    trial.mean_score = 0.5  # type: ignore[misc]

# 4. TuningResult imutável consolidando trials e melhor configuração
result = TuningResult(
    best_params={"alpha": 0.01},
    best_score=0.1233,
    best_trial_index=0,
    trials=[trial],
    search_strategy=SearchStrategy.GRID_SEARCH,
    optimization_metric="RMSE",
)
assert result.best_params["alpha"] == 0.01
assert result.best_trial_index == 0
assert len(result.trials) == 1
assert isinstance(result.best_params, MappingProxyType)
assert isinstance(result.trials, tuple)

# 5. TuningOptimizationError derivando de ContractViolationError
assert issubclass(TuningOptimizationError, ContractViolationError)
err = TuningOptimizationError("Falha total na otimização")
assert isinstance(err, ContractViolationError)
```

- **Resultado Esperado:** Execução limpa sem exceções não tratadas; imutabilidade estrita confirmada via `AttributeError`/`TypeError`.
- **Critério de Falha:** Mutabilidade permitida, falta de slots, tipos inconsistentes ou desacoplamento da hierarquia de erros do `core`.

---

### 2.2 Validação Declarativa de Espaço de Busca e Metadados (`TUN-02` / `US-M43-02`)

```python
import pytest
from experimental_ml.core.enums import MetricDirection
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.tuning import (
    HyperparameterSearchSpec,
    SearchStrategy,
    validate_search_spec,
)

# 1. Validação de especificação correta (identidade preservada)
spec_ok = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.GRID_SEARCH,
    param_grid={"alpha": (0.001, 0.01)},
    optimization_metric="RMSE",
    direction=MetricDirection.MINIMIZE,
    inner_cv_folds=3,
)
validated = validate_search_spec(spec_ok)
assert validated is spec_ok

# 2. Rejeição de número insuficiente de dobras internas (K < 2)
spec_bad_k = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.GRID_SEARCH,
    param_grid={"alpha": (0.001,)},
    optimization_metric="RMSE",
    direction=MetricDirection.MINIMIZE,
    inner_cv_folds=1,
)
with pytest.raises(ConfigurationError, match="inner_cv_folds must be an integer >= 2"):
    validate_search_spec(spec_bad_k)

# 3. Rejeição de métrica não registrada ou com direção divergente do catálogo
spec_bad_dir = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.GRID_SEARCH,
    param_grid={"alpha": (0.001,)},
    optimization_metric="RMSE",
    direction=MetricDirection.MAXIMIZE,  # RMSE exige MINIMIZE
    inner_cv_folds=3,
)
with pytest.raises(ConfigurationError, match="Direction mismatch for metric 'RMSE'"):
    validate_search_spec(spec_bad_dir)

# 4. Rejeição de RANDOM_SEARCH sem orçamento n_iter positivo
spec_bad_iter = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.RANDOM_SEARCH,
    param_grid={"alpha": (0.001, 0.01)},
    optimization_metric="R2",
    direction=MetricDirection.MAXIMIZE,
    n_iter=0,
    inner_cv_folds=3,
)
with pytest.raises(ConfigurationError, match="n_iter must be a positive integer"):
    validate_search_spec(spec_bad_iter)
```

- **Resultado Esperado:** `ConfigurationError` lançado de forma determinística com mensagens claras sobre a violação identificada.
- **Critério de Falha:** Aceitação silenciosa de K < 2, discrepância ignorada na direção da métrica ou `n_iter` inválido.

---

### 2.3 Geração Determinística de Candidatos de Hiperparâmetros (`TUN-03` / `US-M43-03`)

```python
from experimental_ml.core.enums import MetricDirection
from experimental_ml.tuning import (
    HyperparameterSearchSpec,
    SearchStrategy,
    generate_candidates,
)

# 1. GRID_SEARCH: Produto cartesiano completo e ordenado alfabeticamente pelas chaves
spec_grid = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.GRID_SEARCH,
    param_grid={"alpha": (0.1, 1.0), "fit_intercept": (True, False)},
    optimization_metric="RMSE",
    direction=MetricDirection.MINIMIZE,
)
cands_grid = generate_candidates(spec_grid)
assert len(cands_grid) == 4
assert [dict(c) for c in cands_grid] == [
    {"alpha": 0.1, "fit_intercept": True},
    {"alpha": 0.1, "fit_intercept": False},
    {"alpha": 1.0, "fit_intercept": True},
    {"alpha": 1.0, "fit_intercept": False},
]

# 2. RANDOM_SEARCH: Amostragem exata de n_iter candidatos com determinismo por semente
spec_rnd1 = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.RANDOM_SEARCH,
    param_grid={"alpha": (0.01, 0.05, 0.1, 0.5, 1.0), "max_iter": (100, 200, 500)},
    optimization_metric="R2",
    direction=MetricDirection.MAXIMIZE,
    n_iter=3,
    seed=123,
)
cands_rnd1 = generate_candidates(spec_rnd1)
cands_rnd2 = generate_candidates(spec_rnd1)
assert len(cands_rnd1) == 3
assert [dict(c) for c in cands_rnd1] == [dict(c) for c in cands_rnd2]

# 3. FIXED: Candidato único derivado da especificação
spec_fixed = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.FIXED,
    param_grid={"alpha": 0.5, "fit_intercept": True},
    optimization_metric="MAE",
    direction=MetricDirection.MINIMIZE,
)
cands_fixed = generate_candidates(spec_fixed)
assert len(cands_fixed) == 1
assert dict(cands_fixed[0]) == {"alpha": 0.5, "fit_intercept": True}
```

- **Resultado Esperado:** 4 candidatos no grid (2x2), 3 candidatos no random com reproduzibilidade exata de semente, 1 candidato no fixed.
- **Critério de Falha:** Combinações ausentes ou duplicadas, desordem não determinística ou quebra de semente em execuções repetidas.

---

### 2.4 Particionamento Interno Puro em NumPy e Anti-Vazamento (`TUN-04` / `US-M43-04`)

```python
import numpy as np
import pytest
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.tuning import split_inner_folds

n_train = 30
n_folds = 3
splits = split_inner_folds(n_samples=n_train, n_folds=n_folds, seed=42)
assert len(splits) == n_folds

all_val_indices = []
for tr_idx, val_idx in splits:
    # 1. Disjunção estrita: Treino interno e Validação interna não compartilham índices
    assert len(np.intersect1d(tr_idx, val_idx)) == 0
    # 2. Confinamento nos limites [0, n_train - 1]
    assert np.all(tr_idx >= 0) and np.all(tr_idx < n_train)
    assert np.all(val_idx >= 0) and np.all(val_idx < n_train)
    # 3. Imutabilidade dos arrays gerados
    assert not tr_idx.flags.writeable
    assert not val_idx.flags.writeable
    all_val_indices.extend(val_idx.tolist())

# 4. Cobertura completa sem duplicatas
assert sorted(all_val_indices) == list(range(n_train))

# 5. Rejeição quando N < K
with pytest.raises(ContractViolationError, match="Insufficient samples"):
    split_inner_folds(n_samples=2, n_folds=5)
```

- **Resultado Esperado:** Particionamento disjunto e exaustivo de $0 \dots N_{\text{train}}-1$; arrays read-only; rejeição quando $N < K$.
- **Critério de Falha:** Interseção não vazia entre treino e validação, índices fora de faixa ou mutabilidade dos arrays.

---

### 2.5 Motor de Nested Cross-Validation e Otimização Intra-Fold (`TUN-05` / `US-M43-05`)

```python
import numpy as np
from experimental_ml.core.enums import MetricDirection
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily
from experimental_ml.tuning import (
    HyperparameterSearchSpec,
    SearchStrategy,
    run_nested_tuning,
)

class RidgeSimple:
    def __init__(self, alpha: float = 1.0):
        self.alpha = float(alpha)
        self.coef_ = None
        self.__is_fitted__ = False
    def set_params(self, **p):
        if "alpha" in p: self.alpha = float(p["alpha"])
        return self
    def fit(self, X, y):
        p = X.shape[1]
        self.coef_ = np.linalg.solve(X.T @ X + self.alpha * np.eye(p), X.T @ y)
        self.__is_fitted__ = True
        return self
    def predict(self, X):
        return X @ self.coef_

model_spec = ModelSpec(
    model_id="ridge_simple",
    display_name="Ridge Simples",
    family=ModelFamily.CLASSICAL_ML,
    estimator_factory=lambda seed: RidgeSimple(),
    capabilities=ModelCapabilities(requires_fit=True),
    description="Modelo linear para validacao de aceitacao",
    scientific_justification="Teste de aceitacao M4.3",
)

rng = np.random.default_rng(42)
X_train = rng.normal(size=(50, 2))
y_train = X_train @ np.array([2.0, -1.0]) + rng.normal(scale=0.05, size=50)

spec_tune = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.GRID_SEARCH,
    param_grid={"alpha": (0.0001, 10.0)},
    optimization_metric="RMSE",
    direction=MetricDirection.MINIMIZE,
    inner_cv_folds=3,
)

res = run_nested_tuning(spec_tune, model_spec, X_train, y_train)
assert len(res.trials) == 2
# Candidato com menor erro quadrático deve vencer
assert res.best_params["alpha"] == 0.0001
assert res.best_score < 0.1
assert res.best_trial_index == 0
```

- **Resultado Esperado:** Otimização concluída selecionando $\alpha = 0.0001$ com menor RMSE médio nas dobras internas.
- **Critério de Falha:** Instâncias reutilizadas entre dobras, agregação incorreta de métricas ou seleção contrária à direção.

---

### 2.6 Desqualificação Estrita de `UNDEFINED_NAN` e Exceção de Falha Total (`TUN-06` / `US-M43-06`)

```python
import math
import numpy as np
import pytest
from experimental_ml.core.enums import MetricDirection, MetricStatus
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily
from experimental_ml.tuning import (
    HyperparameterSearchSpec,
    SearchStrategy,
    TuningOptimizationError,
    run_nested_tuning,
)

class FaultyModel:
    def __init__(self, mode="valid"):
        self.mode = mode
        self.__is_fitted__ = False
    def set_params(self, **p):
        if "mode" in p: self.mode = p["mode"]
        return self
    def fit(self, X, y):
        if self.mode == "fail_fit": raise ValueError("Falha intencional de ajuste")
        self.__is_fitted__ = True
        return self
    def predict(self, X):
        if self.mode == "nan": return np.full(X.shape[0], np.nan)
        return np.ones(X.shape[0]) * 2.0

spec_faulty = ModelSpec(
    model_id="faulty_model",
    display_name="Modelo com Falha",
    family=ModelFamily.CUSTOM,
    estimator_factory=lambda seed: FaultyModel(),
    capabilities=ModelCapabilities(requires_fit=True),
    description="Modelo com falhas intencionais",
    scientific_justification="Validacao de robustez e ADR-005",
)

X = np.ones((20, 2))
y = np.linspace(1.0, 5.0, 20)

# 1. Candidato com NaN e candidato valido: valido deve vencer
spec_mix = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.GRID_SEARCH,
    param_grid={"mode": ("nan", "valid")},
    optimization_metric="RMSE",
    direction=MetricDirection.MINIMIZE,
    inner_cv_folds=2,
)
res_mix = run_nested_tuning(spec_mix, spec_faulty, X, y)
assert res_mix.best_params["mode"] == "valid"
assert res_mix.trials[0].status == MetricStatus.UNDEFINED_NAN
assert math.isnan(res_mix.trials[0].mean_score)

# 2. Todos os candidatos falham -> TuningOptimizationError obrigatorio
spec_all_fail = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.GRID_SEARCH,
    param_grid={"mode": ("fail_fit", "nan")},
    optimization_metric="RMSE",
    direction=MetricDirection.MINIMIZE,
    inner_cv_folds=2,
)
with pytest.raises(TuningOptimizationError, match="All 2 hyperparameter candidate trials failed"):
    run_nested_tuning(spec_all_fail, spec_faulty, X, y)
```

- **Resultado Esperado:** Candidatos gerando NaN desqualificados sem propagar vitória; falha total lançando `TuningOptimizationError` com histórico.
- **Critério de Falha:** Conversão silenciosa de NaN para 0.0, seleção de trial desqualificado ou ausência de exceção na falha total.

---

### 2.7 Exportações da API Pública e Pureza de Runtime (`TUN-07` / `US-M43-07`)

```python
import subprocess
import sys

# Inspeciona em subprocesso isolado as dependencias importadas por experimental_ml.tuning
code = (
    "import sys\n"
    "import experimental_ml.tuning\n"
    "forbidden = ['optuna', 'ray', 'sklearn', 'scipy', 'torch', 'tensorflow', 'jax', 'qiskit']\n"
    "violating = [p for p in forbidden if any(m.startswith(p) for m in sys.modules)]\n"
    "if violating:\n"
    "    print(f'Violacao detectada: {violating}')\n"
    "    sys.exit(1)\n"
    "assert 'numpy' in sys.modules\n"
    "print('PURE_NUMPY_OK')\n"
)
proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
assert proc.returncode == 0
assert "PURE_NUMPY_OK" in proc.stdout
```

- **Resultado Esperado:** Código de retorno 0 e mensagem `PURE_NUMPY_OK`.
- **Critério de Falha:** Importação acidental de frameworks externos de tuning ou quebra de conformidade com `XCUT-02`.

---

## 3. Cenário Integrado de Ponta a Ponta (End-to-End Walkthrough)

O cenário a seguir simula a integração completa da Etapa 3B com a Etapa 4 de um experimento de ML:
1. Uma partição externa de treino ($X_{\text{train}}, y_{\text{train}}$) e uma partição externa de teste ($X_{\text{test}}, y_{\text{test}}$) são geradas.
2. A busca aninhada de hiperparâmetros roda estritamente sobre $X_{\text{train}}, y_{\text{train}}$ com 3 dobras internas.
3. É verificado o princípio de isolamento (*anti-leakage*, `CA-E4B-01`): alterar ou permutar $X_{\text{test}}, y_{\text{test}}$ não tem efeito nenhum no resultado do tuning.
4. O modelo final é reajustado com os parâmetros ótimos $\theta^*$ em todo $X_{\text{train}}, y_{\text{train}}$ e avaliado em $X_{\text{test}}, y_{\text{test}}$.

```python
import numpy as np
from experimental_ml.core.enums import MetricDirection
from experimental_ml.metrics.catalog import METRICS_CATALOG
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily
from experimental_ml.tuning import (
    HyperparameterSearchSpec,
    SearchStrategy,
    run_nested_tuning,
)

# 1. Definicao de modelo Ridge via contratos M4.1
class RidgeRegressor:
    def __init__(self, alpha: float = 1.0):
        self.alpha = float(alpha)
        self.coef_ = None
        self.__is_fitted__ = False
    def set_params(self, **p):
        if "alpha" in p: self.alpha = float(p["alpha"])
        return self
    def fit(self, X, y):
        p = X.shape[1]
        self.coef_ = np.linalg.solve(X.T @ X + self.alpha * np.eye(p), X.T @ y)
        self.__is_fitted__ = True
        return self
    def predict(self, X):
        return X @ self.coef_

ridge_spec = ModelSpec(
    model_id="ridge_e2e",
    display_name="Ridge E2E Integrado",
    family=ModelFamily.CLASSICAL_ML,
    estimator_factory=lambda seed: RidgeRegressor(),
    capabilities=ModelCapabilities(requires_fit=True),
    description="Modelo Ridge para demonstracao de ponta a ponta",
    scientific_justification="Homologacao do marco M4.3",
)

# 2. Dados sinteticos particionados externamente (Treino vs Teste)
rng = np.random.default_rng(2026)
W_true = np.array([4.0, -2.5, 1.2])
X_train = rng.normal(size=(60, 3))
y_train = X_train @ W_true + rng.normal(scale=0.1, size=60)

X_test = rng.normal(size=(20, 3))
y_test = X_test @ W_true + rng.normal(scale=0.1, size=20)

# 3. Especificacao de busca aninhada intra-fold (Grid Search)
search_spec = HyperparameterSearchSpec(
    search_strategy=SearchStrategy.GRID_SEARCH,
    param_grid={"alpha": (0.0001, 0.01, 1.0, 100.0)},
    optimization_metric="RMSE",
    direction=MetricDirection.MINIMIZE,
    inner_cv_folds=3,
    seed=2026,
    description="Ajuste intra-fold de regularizacao Ridge",
)

# 4. Execucao de Nested CV estritamente no conjunto de treino
tune_result = run_nested_tuning(search_spec, ridge_spec, X_train, y_train)

print(f"Melhor parametro encontrado: {dict(tune_result.best_params)}")
print(f"Melhor pontuacao media CV interna: {tune_result.best_score:.6f}")
print(f"Total de tentativas avaliadas: {len(tune_result.trials)}")

# Invariante Anti-Leakage: tuning repete identico resultado sem qualquer dado de teste
tune_result_repeat = run_nested_tuning(search_spec, ridge_spec, X_train, y_train)
assert tune_result.best_params == tune_result_repeat.best_params
assert tune_result.best_score == tune_result_repeat.best_score

# 5. Reajuste do modelo final com theta* em todo o treino externo
final_model = RidgeRegressor(**tune_result.best_params)
final_model.fit(X_train, y_train)

# 6. Avaliacao final na particao externa de teste (Holdout / Generalizacao real)
y_pred_test = final_model.predict(X_test)
test_metric = METRICS_CATALOG["rmse"].func(y_test, y_pred_test)

print(f"RMSE de generalizacao no conjunto de teste externo: {test_metric.value:.6f}")
assert test_metric.value < 0.2
```

- **Resultado Esperado:** Busca em grade identifica $\alpha$ ótimo ($0.0001$ ou $0.01$), reajusta o modelo e produz RMSE de teste $< 0.2$ com garantia de isolamento total.
- **Critério de Falha:** Vazamento de dados de teste no tuning, divergência de reprodução ou pontuação incompatível.

---

## 4. Diagnóstico e Tratamento de Falhas

| Sintoma Observado | Causa Provável | Ação de Resolução |
| :--- | :--- | :--- |
| `ConfigurationError: inner_cv_folds must be an integer >= 2` | Configuração com $K_{\text{inner}} < 2$ | Ajustar `inner_cv_folds` para no mínimo 2 na especificação. |
| `ConfigurationError: Direction mismatch for metric '...'` | Direção declarada incompatível com o catálogo | Alinhar a direção (`MAXIMIZE` ou `MINIMIZE`) com a convenção canônica do `METRICS_CATALOG`. |
| `ConfigurationError: n_iter must be a positive integer` | `RANDOM_SEARCH` sem orçamento ou com $n_{\text{iter}} \le 0$ | Definir `n_iter` como um inteiro positivo. |
| `ContractViolationError: Insufficient samples N for K inner folds` | Tamanho da amostra de treino externa menor que $K_{\text{inner}}$ | Reduzir $K_{\text{inner}}$ ou aumentar o número de observações de treino. |
| `TuningOptimizationError: All N candidate trials failed` | Todos os candidatos lançaram exceções ou geraram `UNDEFINED_NAN` | Inspecionar a mensagem detalhada da exceção que consolida o erro de cada tentativa. |
| Falha no teste de pureza (`sys.modules` com `sklearn` ou `optuna`) | Importação transitiva ou acidental de framework externo | Garantir que o pipeline utilize apenas `experimental_ml` e `numpy`. |

---

## 5. Matriz de Classificação dos Testes

| Identificador do Teste | Tipo | Requisito Rastreado | Arquivo de Teste |
| :--- | :---: | :---: | :--- |
| `test_m43_01_01_search_strategy_enum` | Unidade | `TUN-01` (AC-M43-01-01) | `tests/unit/tuning/test_tuning_types.py` |
| `test_m43_01_02_search_spec_dataclass` | Unidade | `TUN-01` (AC-M43-01-02) | `tests/unit/tuning/test_tuning_types.py` |
| `test_m43_01_03_trial_record_dataclass` | Unidade | `TUN-01` (AC-M43-01-03) | `tests/unit/tuning/test_tuning_types.py` |
| `test_m43_01_04_tuning_result_dataclass` | Unidade | `TUN-01` (AC-M43-01-04) | `tests/unit/tuning/test_tuning_types.py` |
| `test_m43_01_05_tuning_error_inheritance` | Unidade | `TUN-01` (AC-M43-01-02, 04) | `tests/unit/tuning/test_tuning_types.py` |
| `test_m43_02_01_validate_search_spec_valid` | Unidade | `TUN-02` (AC-M43-02-01) | `tests/unit/tuning/test_tuning_validation.py` |
| `test_m43_02_02_validate_search_spec_invalid_folds` | Unidade | `TUN-02` (AC-M43-02-02) | `tests/unit/tuning/test_tuning_validation.py` |
| `test_m43_02_03_validate_search_spec_metric_direction` | Unidade | `TUN-02` (AC-M43-02-03) | `tests/unit/tuning/test_tuning_validation.py` |
| `test_m43_02_04_validate_search_spec_random_n_iter` | Unidade | `TUN-02` (AC-M43-02-04) | `tests/unit/tuning/test_tuning_validation.py` |
| `test_m43_03_01_grid_search_cartesian_product` | Unidade | `TUN-03` (AC-M43-03-01) | `tests/unit/tuning/test_tuning_candidates.py` |
| `test_m43_03_02_random_search_seed_determinism` | Unidade | `TUN-03` (AC-M43-03-02) | `tests/unit/tuning/test_tuning_candidates.py` |
| `test_m43_03_03_fixed_strategy_single_candidate` | Unidade | `TUN-03` (AC-M43-03-03) | `tests/unit/tuning/test_tuning_candidates.py` |
| `test_m43_04_01_split_inner_folds_disjointness` | Unidade | `TUN-04` (AC-M43-04-01) | `tests/unit/tuning/test_tuning_partitioning.py` |
| `test_m43_04_02_split_inner_folds_training_confinement` | Unidade | `TUN-04` (AC-M43-04-02) | `tests/unit/tuning/test_tuning_partitioning.py` |
| `test_m43_04_03_split_inner_folds_insufficient_samples` | Unidade | `TUN-04` (AC-M43-04-03) | `tests/unit/tuning/test_tuning_partitioning.py` |
| `test_m43_05_01_fresh_model_instances_per_fold` | Unidade | `TUN-05` (AC-M43-05-01) | `tests/unit/tuning/test_tuning_execution.py` |
| `test_m43_05_02_metric_computation_and_aggregation` | Unidade | `TUN-05` (AC-M43-05-02) | `tests/unit/tuning/test_tuning_execution.py` |
| `test_m43_05_03_direction_selection_and_tie_breaking` | Unidade | `TUN-05` (AC-M43-05-03) | `tests/unit/tuning/test_tuning_execution.py` |
| `test_m43_06_01_undefined_nan_disqualification` | Unidade | `TUN-06` (AC-M43-06-01) | `tests/unit/tuning/test_tuning_failures.py` |
| `test_m43_06_02_all_candidates_fail_raises_error` | Unidade | `TUN-06` (AC-M43-06-02) | `tests/unit/tuning/test_tuning_failures.py` |
| `test_m43_06_03_error_preserves_trial_details` | Unidade | `TUN-06` (AC-M43-06-03) | `tests/unit/tuning/test_tuning_failures.py` |
| `test_m43_07_01_public_api_exports` | Integração | `TUN-07` (AC-M43-07-01) | `tests/integration/tuning/test_tuning_integration.py` |
| `test_m43_07_02_runtime_purity_numpy_only` | Integração | `TUN-07` (AC-M43-07-02) | `tests/integration/tuning/test_tuning_integration.py` |
| `test_m43_07_03_end_to_end_tuning_lifecycle` | Integração | `TUN-07` (AC-M43-07-01) | `tests/integration/tuning/test_tuning_integration.py` |
