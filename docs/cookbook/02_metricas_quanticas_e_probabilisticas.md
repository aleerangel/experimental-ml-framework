# Receita 2: Métricas Quânticas (`KTA`) e Métricas Probabilísticas (`ROC-AUC`, `Log-Loss`)

## Contexto Científico

Avaliações envolvendo kernels pré-computados (como *Quantum Kernels*) e classificadores probabilísticos exigem contratos rígidos para evitar vazamento de informação e erros silenciosos de escala:
- **`PrecomputedKernelAdapter`:** Garante que a matriz de Gram de treino receba apenas $(X_{\text{train}}, X_{\text{train}})$ e a matriz de avaliação receba $(X_{\text{eval}}, X_{\text{train}})$, sem jamais misturar amostras de validação no cálculo do kernel de treino.
- **`requires_kernel_matrix=True` (`kta`):** A métrica *Kernel Target Alignment* (`kta`) no `METRICS_CATALOG` compara matrizes Gram quadradas $(n, n)$ ou vetores 1D convertidos em produtos externos $v v^T$.
- **`requires_probabilities=True` (`roc_auc`, `log_loss`):** O executor celular (`execute_single_cell`) exige que o modelo retorne `y_proba` (não `None`), lançando `ConfigurationError` caso contrário. `roc_auc` aceita probabilidades ou scores contínuos, enquanto `log_loss` exige probabilidades válidas no intervalo $[0, 1]$ somando $1$ por amostra.

---

## 1. Uso de Kernel Pré-computado sem Vazamento

```python
import numpy as np
from experimental_ml.models.preprocessing import PrecomputedKernelAdapter

def rbf_kernel(X_a: np.ndarray, X_b: np.ndarray, gamma: float = 0.5) -> np.ndarray:
    """Kernel Gaussiano puro em NumPy."""
    sq_dists = (
        np.sum(X_a ** 2, axis=1, keepdims=True)
        + np.sum(X_b ** 2, axis=1)
        - 2.0 * (X_a @ X_b.T)
    )
    return np.exp(-gamma * np.maximum(sq_dists, 0.0))

adapter = PrecomputedKernelAdapter(kernel_func=rbf_kernel)

X_train = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]])
X_val = np.array([[0.2, 0.8]])

# No ajuste: computa K(X_train, X_train)
K_train = adapter.fit_transform(X_train)
# Na validação: computa K(X_val, X_train) usando apenas o X_train memorizado
K_val = adapter.transform(X_val)
assert K_train.shape == (3, 3) and K_val.shape == (1, 3)
```

---

## 2. Avaliação de Alinhamento de Kernel (`KTA`) e Probabilidades

```python
import numpy as np
from experimental_ml.metrics import METRICS_CATALOG, compute_metric

# Inspecionando contratos no catálogo oficial
assert METRICS_CATALOG["kta"].requires_kernel_matrix is True
assert METRICS_CATALOG["roc_auc"].requires_probabilities is True
assert METRICS_CATALOG["log_loss"].requires_probabilities is True

# Exemplo KTA com matriz Gram pré-computada
y_bin = np.array([1.0, -1.0, 1.0])
K_ideal = np.outer(y_bin, y_bin)
K_pred = np.array([
    [1.0, -0.8, 0.9],
    [-0.8, 1.0, -0.7],
    [0.9, -0.7, 1.0],
])
res_kta = compute_metric("kta", K_ideal, K_pred, centered=True)

# Exemplo probabilístico (classificação binária: probabilidade da classe positiva)
y_true = np.array([0, 1, 1, 0])
y_proba_pos = np.array([0.1, 0.9, 0.8, 0.2])
res_auc = compute_metric("roc_auc", y_true, y_proba_pos)
res_logloss = compute_metric("log_loss", y_true, y_proba_pos)
```

---

## Cuidados na Execução Matricial

- Ao incluir `"roc_auc"` ou `"log_loss"` na lista `metrics` de `run_experiment_matrix`, todos os modelos avaliados devem retornar `"y_proba"` em sua saída de predição e declarar `supports_predict_proba=True` em `ModelCapabilities`.
- Para `kta`, certifique-se de que não haja valores `NaN` ou `+Inf`/`-Inf` nas matrizes Gram; caso contrário, `DataIntegrityError` será lançado imediatamente.
