# Guia de Aceite do Consumidor — Marco M6.2 (Inferência Estatística Pareada, Tamanho de Efeito e Multiplicidade)

> **Documento de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M6.2 (`m6-2-paired-inference-multiplicity`)  
> **Público-alvo:** Pesquisador / Usuário consumidor da API pública `experimental_ml.statistics`

---

## 1. Interfaces Públicas Validadas

A partir da API pública `experimental_ml.statistics`, o pesquisador tem acesso direto e tipado aos seguintes recursos:

- **Especificação e Estruturas Imutáveis (`STAT-05`)**:
  - `ComparisonScope`, `MultiplicityMethod`, `EffectSizeMagnitude`, `PracticalRelevanceStatus`
  - `ComparisonSpec`, `NadeauBengioResult`, `WilcoxonResult`, `EffectSizeResult`, `PairwiseComparisonResult`, `SkippedComparison`, `StatisticalComparisonBundle`
- **Funções Inferenciais Puras em NumPy (`STAT-06`, `STAT-07`, `XCUT-02`)**:
  - `paired_nadeau_bengio_test(scores_a, scores_b, train_val_ratios, fold_val_sizes=None, alpha=0.05)`
  - `paired_wilcoxon_test(scores_a, scores_b, zero_method="wilcox", alpha=0.05)`
  - `compute_paired_cohens_d(scores_a, scores_b, alpha=0.05)`
- **Ajuste de Multiplicidade e Orquestração (`STAT-08`)**:
  - `adjust_pvalues_holm(p_values)` (FWER)
  - `adjust_pvalues_bh(p_values)` (FDR)
  - `run_statistical_comparisons(consolidation, partition_plan, comparison_spec, suitability_report, policy=...)`

---

## 2. Roteiro de Validação sob a Perspectiva do Consumidor

1. **Executar Teste $t$ Corrigido de Nadeau-Bengio**:
   ```python
   from experimental_ml.statistics import paired_nadeau_bengio_test

   res = paired_nadeau_bengio_test(
       scores_a=[0.80, 0.82, 0.78, 0.85, 0.81],
       scores_b=[0.75, 0.76, 0.75, 0.79, 0.77],
       train_val_ratios=0.25,
       alpha=0.05,
   )
   ```
   *Resultado esperado:* Variância corrigida $(1/J + \bar{r}) S^2_d$, $p$-valor bicaudal exato e intervalo de confiança sem dependência de `scipy`.

2. **Executar Teste de Wilcoxon Pareado & Tamanho de Efeito**:
   ```python
   from experimental_ml.statistics import paired_wilcoxon_test, compute_paired_cohens_d

   wx = paired_wilcoxon_test([1.0, 2.0, 3.0, 4.0, 5.0], [0.0] * 5, zero_method="pratt")
   es = compute_paired_cohens_d([1.0, 2.0, 3.0, 4.0, 5.0], [0.0] * 5)
   ```
   *Resultado esperado:* Cálculo exato via DP para $n_{\text{eff}} \le 20$, alerta para $n_{\text{eff}} < 6$, e estimativa de $d_z$ com magnitude qualitativa e ressalva de sobreposição de CV.

3. **Orquestrar Comparações Completas da Etapa 5B**:
   ```python
   from experimental_ml.statistics import (
       ComparisonScope,
       ComparisonSpec,
       MultiplicityMethod,
       run_statistical_comparisons,
   )

   spec = ComparisonSpec(
       metrics_of_interest=("rmse",),
       metric_directions={"rmse": MetricDirection.MINIMIZE},
       comparison_scope=ComparisonScope.AGAINST_BASELINE,
       baseline_config=("m_baseline", "sc1"),
       multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI,
       practical_relevance_thresholds={"rmse": 0.2},
   )
   bundle = run_statistical_comparisons(consolidation, partition_plan, spec, suitability_report)
   ```
   *Resultado esperado:* Bloqueio automático em `HOLDOUT_ONLY`, filtragem por `MetricStatus.VALID`, ajuste por família de hipóteses e classificação de relevância prática sem equacionar $p \ge \alpha$ à equivalência.
