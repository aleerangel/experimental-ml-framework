# Guia Prático 7: Cenários de Features Fixos vs. Dinâmicos e Análise de Estabilidade

## Contexto Científico

Selecionar atributos manualmente com base na literatura difere fundamentalmente de aplicar seleção automática (como filtro de variância ou *Top-K* univariado). Para evitar *data leakage*, todo algoritmo de seleção dinâmica precisa ser **reajustado exclusivamente nos dados de treino de cada dobra**.

Além da acurácia preditiva, o pesquisador deve auditar a **estabilidade da seleção** entre dobras: se pequenas perturbações nas amostras mudam completamente os atributos escolhidos, a interpretabilidade científica do modelo fica comprometida.

---

## Avaliação de Estabilidade Inter-Dobras (Jaccard e Kuncheva)

```python
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
    compute_selection_stability,
    validate_scenarios,
)

# 0. Base sintética mínima para validar os cenários contra colunas reais
dados = {
    "x1": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
    "x2": [1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
    "x3": [0.5, 0.4, 0.3, 0.2, 0.1, 0.0],
    "alvo": [0, 0, 0, 1, 1, 1],
}
schema = DatasetSchemaSpec(target_col="alvo", task_type=TaskType.BINARY_CLASSIFICATION)
bundle = load_dataset(dados, schema)
profile = profile_dataset(bundle)
view = sanitize_dataset(bundle, profile, create_preparation_plan(profile, rules=[]))

# 1. Definição comparativa de cenário fixo vs. dinâmico
cenarios = validate_scenarios(
    [
        FeatureScenario(
            scenario_id="literatura_fixo",
            name="Preditores Clássicos (Fixo)",
            description="Subconjunto fixo definido previamente pela literatura",
            scientific_justification="Referência sem seleção automática",
            mode=ScenarioMode.FIXED,
            selected_features=("x1", "x2"),
        ),
        FeatureScenario(
            scenario_id="topk_dinamico",
            name="Top-K Intra-Fold (Dinâmico)",
            description="Seleção supervisionada executada estritamente no treino de cada dobra",
            scientific_justification="Avaliação de redução de dimensionalidade sem vazamento",
            mode=ScenarioMode.DYNAMIC,
            strategy_name="TOP_K_RELEVANCE",
            strategy_params={"k": 2},
        ),
    ],
    view,
)

# 2. Exemplo de conjuntos selecionados em 4 dobras (pool total de 6 atributos)
selecoes_por_dobra = [
    ["x1", "x2"],
    ["x1", "x3"],
    ["x1", "x2"],
    ["x1", "x2"],
]
estabilidade = compute_selection_stability(selecoes_por_dobra, n_total_candidates=6)

assert 0.0 <= estabilidade.mean_jaccard <= 1.0
assert -1.0 <= estabilidade.mean_kuncheva <= 1.0
assert len(cenarios.scenarios) == 2
```

---

## Interpretação Científica

- **Índice de Jaccard Médio (`mean_jaccard`):** Varia de `0.0` (conjuntos totalmente disjuntos) a `1.0` (seleção idêntica em todas as dobras). Também pode ser usado diretamente como objetivo na Fronteira de Pareto (`ObjectiveSource.FEATURE_STABILITY`).
- **Índice de Kuncheva (`mean_kuncheva`):** Corrige a sobreposição esperada por mero acaso dado o tamanho do pool total (`n_total_candidates`). Valores positivos indicam consistência acima do acaso.
