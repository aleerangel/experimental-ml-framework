# Receita 1: Modelos Analíticos/Biométricos (`requires_fit=False`) vs. Modelos Treinados

## Contexto Científico

Em áreas como biometria, fisiologia, engenharia biomédica e física aplicada, modelos baseados em equações analíticas fechadas (sem parâmetros ajustados por otimização empírica) competem frequentemente contra modelos treinados de Aprendizado de Máquina sobre exatamente as mesmas dobras de validação.

No `experimental-ml`, modelos analíticos declaram `requires_fit=False` em `ModelCapabilities`, o que instrui o executor de células a:
1. Dispensar o método `fit()` sem exigir ajuste artificial;
2. Garantir coerência contratual (ex.: bloquear `supports_sample_weight=True` quando `requires_fit=False`);
3. Aplicar os parâmetros declarados em `ModelSpec.parameters` via `instantiate_fresh_model` de forma isolada a cada dobra.

---

## Implementação Comparativa em Python

```python
from experimental_ml.models import (
    AnalyticalBiometricModel,
    DummyBaselineModel,
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    instantiate_fresh_model,
    validate_model_spec,
)

# 1. Modelo Analítico / Biométrico (sem ajuste em dados de treino)
analytical_spec = validate_model_spec(
    ModelSpec(
        model_id="analitico_clutter",
        display_name="Modelo Analítico Biométrico",
        family=ModelFamily.BIOMETRIC_MODEL,
        estimator_factory=lambda seed=None, **params: AnalyticalBiometricModel(**params),
        capabilities=ModelCapabilities(
            requires_fit=False,
            supports_predict_proba=False,
            supports_sample_weight=False,
        ),
        parameters={"formula_name": "clutter_relative"},
        description="Equação analítica fechada sem treinamento iterativo",
        scientific_justification="Baseline físico-matemático de referência",
    )
)

# 2. Modelo Treinado Paramétrico (com ajuste estrito por dobra)
trained_spec = validate_model_spec(
    ModelSpec(
        model_id="baseline_treinado",
        display_name="Baseline Treinado",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed=None, **params: DummyBaselineModel(**params),
        capabilities=ModelCapabilities(
            requires_fit=True,
            supports_predict_proba=True,
            supports_sample_weight=True,
        ),
        parameters={"strategy": "most_frequent"},
        description="Modelo treinado no conjunto de treino de cada dobra",
        scientific_justification="Comparação justa sobre o mesmo PartitionPlan",
    )
)

# 3. Garantia de instanciação isolada por dobra (zero contaminação de estado)
instancia_fold_0 = instantiate_fresh_model(analytical_spec, seed=42)
instancia_fold_1 = instantiate_fresh_model(analytical_spec, seed=43)
assert instancia_fold_0 is not instancia_fold_1
```

---

## Pontos de Atenção Metodológica

- **Coerência de Capacidades:** Se `requires_fit=False` for combinado com `supports_sample_weight=True`, `validate_model_spec` rejeitará a especificação com `ConfigurationError`.
- **Competição Justa:** Ambos os modelos devem ser passados juntos para `run_experiment_matrix` sob o mesmo `PartitionPlan` para viabilizar testes pareados (Etapa 5).
