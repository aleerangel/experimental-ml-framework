# Guia de Aceite do Consumidor — Marco M6.3 (Fronteira de Pareto, Aquisição e Síntese de Conclusões)

> **Documento de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M6.3 (`m6-3-pareto-acquisition-synthesis`)  
> **Público-alvo:** Pesquisador / Usuário consumidor da API pública `experimental_ml.statistics`

---

## 1. Interfaces Públicas Validadas

A partir da API pública `experimental_ml.statistics`, o pesquisador consome:
- **Multiobjetivo (`STAT-09`)**: `ObjectiveSource`, `ObjectiveSpec`, `MultiObjectiveSpec`, `ParetoConfigurationPoint`, `ExcludedParetoConfiguration`, `MultiObjectiveSummary`, `compute_pareto_frontier`.
- **Aquisição Sequencial (`STAT-10`)**: `AcquisitionCriterion`, `CandidatePrediction`, `AcquisitionScoreRecord`, `score_candidate_acquisition`.
- **Síntese de Conclusões (`STAT-11`)**: `StructuredConclusion`, `synthesize_conclusions`.

---

## 2. Roteiro de Validação sob a Perspectiva do Consumidor

1. **Fronteira de Pareto (`compute_pareto_frontier`)**:
   ```python
   from experimental_ml.statistics import MultiObjectiveSpec, ObjectiveSpec, ObjectiveSource, compute_pareto_frontier
   from experimental_ml.metrics.types import MetricDirection

   spec = MultiObjectiveSpec((
       ObjectiveSpec("rmse", MetricDirection.MINIMIZE),
       ObjectiveSpec("fit_mean_s", MetricDirection.MINIMIZE, ObjectiveSource.TIMING_MEAN, "fit_mean_s"),
   ))
   pareto = compute_pareto_frontier(consolidation, spec)
   ```
   *Resultado esperado:* Apenas configurações `VALID` e finitas entram na fronteira não-dominada; configurações parciais/nulas ficam registradas em `excluded_configurations`.

2. **Aquisição Sequencial (`score_candidate_acquisition`)**:
   ```python
   from experimental_ml.statistics import AcquisitionCriterion, CandidatePrediction, score_candidate_acquisition

   ranked = score_candidate_acquisition(
       [CandidatePrediction("c1", 0.9, 0.2), CandidatePrediction("c2", 1.1, 0.05)],
       AcquisitionCriterion.EXPECTED_IMPROVEMENT,
   )
   ```
   *Resultado esperado:* Ordenação determinística em Python/NumPy puro (`XCUT-02`).

3. **Síntese Auditável (`synthesize_conclusions`)**:
   ```python
   from experimental_ml.statistics import synthesize_conclusions

   conclusion = synthesize_conclusions(
       consolidation, suitability_report, comparison_bundle,
       primary_metric="rmse", primary_direction=MetricDirection.MINIMIZE,
       multi_objective_summary=pareto,
   )
   ```
   *Resultado esperado:* `StructuredConclusion` com referências numéricas exatas na narrativa, todas as ressalvas metodológicas preservadas e nenhuma declaração espúria de equivalência por $p_{\text{adj}} \ge \alpha$.
