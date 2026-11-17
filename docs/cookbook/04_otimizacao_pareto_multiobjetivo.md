# Receita 4: Otimização Multiobjetivo na Fronteira de Pareto

## Contexto Científico

Em pesquisa aplicada, a acurácia isolada raramente basta: é preciso equilibrar desempenho preditivo, custo computacional (latência de inferência) e estabilidade da seleção de atributos.

A função `compute_pareto_frontier` (Etapa 5 — `experimental_ml.statistics`) calcula exatamente a fronteira de configurações **não dominadas** segundo a especificação `MultiObjectiveSpec`, operando com as seguintes garantias:
- **Elegibilidade Estrita (`CoverageStatus.VALID`):** Configurações com falhas de execução (`PARTIAL_COVERAGE`, `NO_COVERAGE`) ou com métrica `UNDEFINED_NAN` são excluídas da fronteira e listadas explicitamente em `excluded` com o motivo detalhado;
- **Três Fontes Nativas de Objetivos (`ObjectiveSource`):**
  1. `AGGREGATED_METRIC`: qualquer métrica agregada consolidada (ex.: `accuracy`, `f1`, `rmse`);
  2. `TIMING_MEAN`: tempos médios registrados no `TimingBreakdown` (ex.: `predict_time_s`, `fit_time_s`, `total_time_s`);
  3. `FEATURE_STABILITY`: estabilidade inter-dobras de seleção de atributos (`mean_jaccard`).

---

## Implementação da Fronteira de Pareto

```python
# conceptual
from experimental_ml.core.enums import MetricDirection
from experimental_ml.statistics import (
    MultiObjectiveSpec,
    ObjectiveSource,
    ObjectiveSpec,
    compute_pareto_frontier,
    consolidate_descriptive,
)

# Supondo `consolidation` obtido de `consolidate_descriptive(...)`
spec = MultiObjectiveSpec(
    objectives=(
        ObjectiveSpec(
            name="accuracy",
            source=ObjectiveSource.AGGREGATED_METRIC,
            direction=MetricDirection.MAXIMIZE,
            field_name="accuracy",
        ),
        ObjectiveSpec(
            name="latencia_inferencia",
            source=ObjectiveSource.TIMING_MEAN,
            direction=MetricDirection.MINIMIZE,
            field_name="predict_time_s",
        ),
        ObjectiveSpec(
            name="estabilidade_features",
            source=ObjectiveSource.FEATURE_STABILITY,
            direction=MetricDirection.MAXIMIZE,
            field_name="mean_jaccard",
        ),
    )
)

pareto_summary = compute_pareto_frontier(consolidation, spec)

# Pontos ótimos (não dominados) e pontos excluídos por cobertura/NaN
otimos = [pt.config_id for pt in pareto_summary.frontier]
excluidos = [(ex.config_id, ex.reason) for ex in pareto_summary.excluded]
```

---

## Interpretação dos Resultados

- Um ponto $A$ domina $B$ se e somente se $A$ é pelo menos tão bom quanto $B$ em todos os objetivos e estritamente superior em pelo menos um.
- Na Etapa 6 (`reporting`), a família de tabelas `F_STABILITY_COST_PARETO` exporta automaticamente a fronteira de Pareto e os pontos dominados/excluídos em formato `CSV`, `Markdown` e `LaTeX booktabs`.
