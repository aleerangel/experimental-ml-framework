# Guia Prático 6: Variações do Mesmo Algoritmo — LS-SVM em Prognose Florestal

> [!TIP]
> Este estudo completo — incluindo geração de relatórios, tabelas LaTeX e gráficos SVG — está disponível pronto para executar no [Notebook 04 — Variantes do LS-SVM em Prognose Florestal](../../notebooks/04_avancado_variantes_lssvm_prognose_florestal.ipynb).

## Contexto Científico

Em estudos comparativos e computação científica (como na **prognose florestal** para predição de volume de madeira a partir de variáveis dendrométricas — DAP, altura e idade), frequentemente comparamos **variações arquiteturais de um mesmo algoritmo** sob condições estritamente idênticas:
1. **LS-SVM Clássico com Kernel RBF** (`ModelFamily.CLASSICAL_ML`);
2. **LS-SVM com Kernel Quântico** (`ModelFamily.QUANTUM_KERNEL` + `supports_precomputed_kernel=True`);
3. **LS-SVM com Resolvedor de Sistema Linear Quântico** (`ModelFamily.QUANTUM_SOLVER`).

Como o `experimental-ml` é agnóstico a domínio e a estimadores, todas as variantes competem sobre **exatamente o mesmo `PartitionPlan`** e são avaliadas por métricas consagradas em inventário florestal (`rmse`, `rmse_rel_pct`, `mbe` e `r2`).

---

## Implementação Comparativa em Python

```python
import numpy as np
from experimental_ml.core.enums import TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features import FeatureScenario, ScenarioMode
from experimental_ml.models import (
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    validate_model_spec,
)
from experimental_ml.validation import (
    EvaluationRegime,
    PartitionConfig,
    PartitionStrategy,
    build_partition_plan,
)

class LSSVMVarianteRegressor:
    """Wrapper didático de LS-SVM suportando variações de kernel ou solver."""

    def __init__(self, kernel_mode: str = "rbf_classico", gamma: float = 0.5, reg: float = 1.0) -> None:
        self.kernel_mode = kernel_mode
        self.gamma = gamma
        self.reg = reg
        self.X_train_: np.ndarray | None = None
        self.alpha_: np.ndarray | None = None
        self.b_: float = 0.0

    def _gram(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:
        if self.kernel_mode == "kernel_quantico":
            # Exemplo de kernel de fidelidade em mapa de características trigonométrico
            A_norm = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-12)
            B_norm = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-12)
            return (np.cos(A_norm @ B_norm.T)) ** 2
        sq = np.sum(A ** 2, axis=1, keepdims=True) + np.sum(B ** 2, axis=1) - 2.0 * (A @ B.T)
        return np.exp(-self.gamma * np.maximum(sq, 0.0))

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LSSVMVarianteRegressor":
        n = X.shape[0]
        self.X_train_ = X.copy()
        K = self._gram(X, X) + (1.0 / self.reg) * np.eye(n)
        ones = np.ones((n, 1))
        # Sistema linear KKT do LS-SVM: [0, 1^T; 1, K + I/gamma] [b; alpha] = [0; y]
        A_mat = np.block([[np.zeros((1, 1)), ones.T], [ones, K]])
        rhs = np.concatenate([[0.0], y])
        sol = np.linalg.solve(A_mat + 1e-9 * np.eye(n + 1), rhs)
        self.b_ = float(sol[0])
        self.alpha_ = sol[1:]
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        K_eval = self._gram(X, self.X_train_)
        return K_eval @ self.alpha_ + self.b_

# 1. Base sintética de prognose florestal (DAP, altura, idade -> volume)
rng = np.random.default_rng(7)
dap = rng.uniform(10.0, 35.0, size=24)
altura = 8.0 + 0.6 * dap + rng.normal(0.0, 1.0, size=24)
idade = rng.integers(3, 12, size=24).astype(float)
volume = 0.00005 * (dap ** 2) * altura + rng.normal(0.0, 0.02, size=24)

schema = DatasetSchemaSpec(target_col="volume", task_type=TaskType.REGRESSION)
bundle = load_dataset({"dap": dap, "altura": altura, "idade": idade, "volume": volume}, schema)
profile = profile_dataset(bundle)
view = sanitize_dataset(bundle, profile, create_preparation_plan(profile, rules=[]))

# 2. Registro das 3 variantes arquiteturais do LS-SVM
specs = [
    validate_model_spec(
        ModelSpec(
            model_id="lssvm_rbf_classico",
            display_name="LS-SVM Clássico (RBF)",
            family=ModelFamily.CLASSICAL_ML,
            estimator_factory=lambda seed=None, **kw: LSSVMVarianteRegressor(**kw),
            capabilities=ModelCapabilities(requires_fit=True),
            parameters={"kernel_mode": "rbf_classico", "gamma": 0.01, "reg": 10.0},
            description="LS-SVM clássico com kernel Gaussiano RBF",
            scientific_justification="Baseline clássico de regressão não linear",
        )
    ),
    validate_model_spec(
        ModelSpec(
            model_id="lssvm_kernel_quantico",
            display_name="LS-SVM (Kernel Quântico)",
            family=ModelFamily.QUANTUM_KERNEL,
            estimator_factory=lambda seed=None, **kw: LSSVMVarianteRegressor(**kw),
            capabilities=ModelCapabilities(requires_fit=True, supports_precomputed_kernel=True),
            parameters={"kernel_mode": "kernel_quantico", "reg": 10.0},
            description="LS-SVM com matriz Gram de kernel quântico",
            scientific_justification="Avaliação do ganho de expressividade do mapa quântico",
        )
    ),
    validate_model_spec(
        ModelSpec(
            model_id="lssvm_solver_quantico",
            display_name="LS-SVM (Solver Linear Quântico)",
            family=ModelFamily.QUANTUM_SOLVER,
            estimator_factory=lambda seed=None, **kw: LSSVMVarianteRegressor(**kw),
            capabilities=ModelCapabilities(requires_fit=True),
            parameters={"kernel_mode": "solver_quantico", "gamma": 0.01, "reg": 10.0},
            description="LS-SVM com resolução do sistema KKT via solver quântico",
            scientific_justification="Avaliação do impacto numérico do solver linear",
        )
    ),
]

# 3. Plano de partição único para comparação pareada justa
plan = build_partition_plan(
    view,
    PartitionConfig(strategy=PartitionStrategy.KFOLD, regime=EvaluationRegime.CV_ONLY, n_splits=4, master_seed=42),
)
assert len(specs) == 3 and len(plan.folds) == 4
```

---

## Boas Práticas em Estudos Comparativos de Variantes

- **Controle de Variáveis:** Mantenha idênticos o `FeatureScenario`, o `PartitionPlan` e a métrica principal ao comparar variantes do mesmo algoritmo.
- **Viés em Regressão (`mbe`):** Ao utilizar `mbe` (*Mean Bias Error*) na prognose florestal, lembre-se que o catálogo do `experimental-ml` avalia `mbe` com `compare_by_abs=True` (quanto mais próximo de zero em módulo, melhor).
