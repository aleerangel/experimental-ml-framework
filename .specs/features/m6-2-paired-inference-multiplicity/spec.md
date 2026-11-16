# Feature: m6-2-paired-inference-multiplicity

**Approved**: 2026-11-16 - user: "aprovado"

## Problem Statement

Com a consolidação descritiva e a avaliação de adequação metodológica implementadas no Sub-marco M6.1 (`consolidate_descriptive`, `evaluate_method_suitability`), a Etapa 5 do `experimental-ml-framework` necessita agora do **Submódulo 5B de Inferência Estatística Pareada, Tamanho de Efeito e Ajuste de Multiplicidade** para executar comparações rigorosas entre configurações `(model_id, scenario_id)` sem violar a dependência entre partições de validação cruzada nem depender de bibliotecas externas em tempo de execução (`XCUT-02`).

Atualmente, o subsistema `src/experimental_ml/statistics/` ainda não dispõe de:
1. Implementação pura em NumPy/Python da distribuição $t$ de Student (CDF e quantis via função Beta incompleta regularizada $I_x(a, b)$ por fração continuada), necessária para calcular $p$-valores bicaudais e intervalos de confiança sem dependência de `scipy` (`XCUT-02`).
2. O **teste $t$ pareado corrigido de Nadeau-Bengio (2003)** (`paired_nadeau_bengio_test`), considerando a variância corrigida $\sigma_{\text{corr}}^2 = \left(\frac{1}{J} + \bar{r}\right) S^2_d$ com $\nu = J - 1$ graus de liberdade, tratando explicitamente variância nula das diferenças ($s^2_d = 0$) sem divisão por zero e emitindo alerta metodológico caso o coeficiente de variação dos tamanhos dos *folds* ultrapasse 20% (`ADR-004`).
3. O **teste pareado dos postos com sinais de Wilcoxon** (`paired_wilcoxon_test`), com cálculo exato por programação dinâmica sobre postos dobrados para amostras pequenas ($n_{\text{eff}} \le 20$ e $J \le 25$) e aproximação normal com correção de continuidade e fator de empates para amostras maiores, tratando explicitamente diferenças nulas ($d_j = 0$) tanto pelo método `"wilcox"` quanto pelo método `"pratt"` (com média e variância exatas de Pratt), e emitindo alerta estrutural quando $J < 6$ ou $n_{\text{eff}} < 6$ (`ADR-004`, `CA-E5-01`).
4. Cálculo de **tamanho de efeito padronizado** ($d_z = \bar{d} / s_d$ de Cohen pareado, com `ddof=1`) com intervalo de confiança analítico aproximado ($t_{\alpha/2, J-1} \sqrt{1/J + d_z^2/(2J)}$) acompanhado de ressalva explícita de não-correção para sobreposição de CV, classificação qualitativa separada da significância estatística (`NEGLIGIBLE`, `SMALL`, `MEDIUM`, `LARGE`), e avaliação de **relevância prática** frente a limiares configuráveis ($\Delta_{\text{min}}$) (`RF5.4`).
5. Procedimentos de **correção para múltiplas comparações** por família de hipóteses (`adjust_pvalues_holm` para controle de FWER via Holm-Bonferroni e `adjust_pvalues_bh` para controle de FDR via Benjamini-Hochberg), aplicados de forma independente aos $p$-valores de Nadeau-Bengio e Wilcoxon (`CA-E5-02`).
6. Orquestrador de comparações estatísticas (`run_statistical_comparisons`) capaz de executar os escopos de `ComparisonSpec` (`MODELS_WITHIN_SCENARIO`, `SCENARIOS_WITHIN_MODEL`, `FULL_CONFIGURATIONS`, `AGAINST_BASELINE`, `ALL_PAIRWISE`, `PLANNED_HYPOTHESES`), respeitando `evaluate_method_suitability`, `check_pairwise_comparison_eligibility`, a semântica de `MetricStatus.UNDEFINED_NAN` (`ADR-005`), o isolamento estrito de `HOLDOUT_ONLY` e `FINAL_HOLDOUT`, e registrando comparações não aplicáveis sem descarte silencioso.

## Out of Scope

- Análise multiobjetivo, cálculo da Fronteira de Pareto (`compute_pareto_frontier`), critérios de aquisição sequencial e síntese narrativa de conclusões (`synthesize_conclusions`, `StructuredConclusion`) — escopo do Sub-marco M6.3.
- Persistência em disco de `statistics/` (`save_statistics_bundle`, `load_statistics_bundle`), portão de estágio `verify_statistics_gate` e CLI `expml stats` — escopo do Sub-marco M6.4.
- Inclusão de `scipy` ou qualquer outra biblioteca de terceiros além de `numpy>=1.24.0` em tempo de execução (`XCUT-02`).
- Acoplamento a qualquer domínio aplicado ou dados reais específicos (`RNF02`, `CA02`).

## Assumptions & Open Questions

**Open questions:** none - todos os contratos matemáticos, limiares de alerta, escopos de comparação e restrições de runtime estão formalmente estabelecidos em `ARQUITETURA_E_CONTRATOS.md` (Seção 3.5, ADR-004 e ADR-005) e `ESPECIFICACAO_REQUISITOS.md` (RF5.1–RF5.4, CA-E5-01, CA-E5-02).

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Dependência de runtime | Apenas `numpy>=1.24.0` e biblioteca padrão Python (`math.erfc`, etc.) | Cumpre `XCUT-02` e `RNF03` mantendo precisão de máquina ($\le 10^{-12}$) via função Beta incompleta $I_x(a,b)$ |
| Convenção de sinal da diferença $\Delta$ | $\bar{d} = \text{mean}(x_A - x_B)$; `observed_better` determinado por `MetricDirection` (`MINIMIZE` vs `MAXIMIZE`) | Preserva sinal aritmético transparente enquanto atribui superioridade observada conforme a direção da métrica |
| Variância nula ($S^2_d = 0$) no Nadeau-Bengio | Se $\bar{d} = 0$: `t = 0.0`, `p = 1.0`, `CI = (0.0, 0.0)`. Se $\bar{d} \ne 0$: `t = sign(d)*inf`, `p = 0.0`, `CI = (d, d)`, com aviso `zero_difference_variance` | Evita `ZeroDivisionError` (`ADR-004`) e distingue empate perfeito de diferença constante em todas as partições |
| Coeficiente de variação de tamanho dos *folds* ($> 20\%$) | `paired_nadeau_bengio_test` aceita `fold_val_sizes` opcional; calcula $\text{CV} = \text{std}(\text{sizes}, \text{ddof}=1) / \text{mean}(\text{sizes})$ (ou sobre `train_val_ratios` se `fold_val_sizes` omitido) | Alinha a assinatura da função ao requisito de `ADR-004` tanto em chamadas diretas quanto orquestradas via `PartitionPlan` |
| Tratamento de zeros no Wilcoxon (`zero_method`) | `"wilcox"` (padrão: descarta $d_j = 0$) e `"pratt"` (ranqueia todos os $J$ valores, descarta zeros após ranquear, usando média $\mu_{W^+}$ e variância $\sigma^2_{W^+}$ exatas de Pratt 1959) | Corrige erro comum de aplicar fórmulas padrão de Wilcoxon a postos de Pratt; $n_{\text{eff}} = J - n_0$ controla o poder mínimo em ambos |
| Exatidão vs. aproximação no Wilcoxon | Programação dinâmica exata sobre postos inteiros dobrados ($2 r_i$) quando $n_{\text{eff}} \le 20$ e $J \le 25$; aproximação normal com correção de continuidade e empates caso contrário | Exatidão combinatória inclusive com empates para $K \le 20$ e estabilidade assintótica para $K > 20$ |
| Intervalo de confiança de Cohen's $d_z$ | $\text{SE}(d_z) = \sqrt{1/J + d_z^2/(2J)}$ com quantil $t_{\alpha/2, J-1}$; para $s_d = 0$ e $\bar{d} \ne 0$, IC é `(None, None)`. Acompanhado de aviso de não-correção por sobreposição de CV | Explicita fórmula para pequenas amostras, evita conflito interpretativo com Nadeau-Bengio e previne divisão por zero |
| Famílias de hipóteses padrão e ajuste | Agrupamento por `hypothesis_family_spec` (padrão: por `metric_name`); ajustes separados para `nadeau_bengio` e `wilcoxon` | Garante controle rigoroso de FWER/FDR sem misturar métricas distintas nem deixar um dos testes sem correção |
| Métricas `UNDEFINED_NAN` em *folds* `COMPLETED` | Filtragem específica por métrica: sob `STRICT_COMPLETE_ONLY` torna o par não aplicável; sob `ALLOW_COMMON_SUBSET` restringe aos *folds* com métrica `VALID` em ambas as configurações | Impede propagação de `NaN` para os testes (`ADR-005`) quando a célula concluiu mas a métrica é matematicamente indefinida |

## User Stories

### US-M62-01 (Priority: P1) — Estruturas Imutáveis de Inferência e Comparação
As an experimental ML researcher,  
I want typed, immutable data structures for comparison specifications, pairwise statistical test results, effect sizes, and multiplicity-adjusted families,  
So that all inferential outputs are strongly typed, serializable, and auditable.

#### Acceptance Criteria
- **AC-M62-01-01**: The system SHALL provide enumerations `ComparisonScope` (`MODELS_WITHIN_SCENARIO`, `SCENARIOS_WITHIN_MODEL`, `FULL_CONFIGURATIONS`, `AGAINST_BASELINE`, `ALL_PAIRWISE`, `PLANNED_HYPOTHESES`), `MultiplicityMethod` (`NONE`, `HOLM_BONFERRONI`, `BENJAMINI_HOCHBERG`), `EffectSizeMagnitude` (`NEGLIGIBLE`, `SMALL`, `MEDIUM`, `LARGE`), and `PracticalRelevanceStatus` (`NOT_CONFIGURED`, `STATISTICALLY_SIGNIFICANT_AND_PRACTICAL`, `STATISTICALLY_SIGNIFICANT_NOT_PRACTICAL`, `PRACTICAL_NOT_STATISTICALLY_SIGNIFICANT`, `INCONCLUSIVE`, `EVIDENCE_OF_EQUIVALENCE`).
- **AC-M62-01-02**: The system SHALL provide a frozen dataclass `ComparisonSpec` validating `metrics_of_interest`, `metric_directions: Mapping[str, MetricDirection]`, `comparison_scope`, optional `baseline_config`, optional `planned_pairs`, `alpha` in $(0.0, 1.0)$, `multiplicity_method`, optional `hypothesis_family_spec`, and optional `practical_relevance_thresholds`.
- **AC-M62-01-03**: The system SHALL provide frozen dataclasses `NadeauBengioResult`, `WilcoxonResult`, `EffectSizeResult`, `PairwiseComparisonResult`, `SkippedComparison`, and `StatisticalComparisonBundle` with strict structural validations and immutability (`FrozenInstanceError` on mutation).

---

### US-M62-02 (Priority: P1) — Teste t Pareado Corrigido de Nadeau-Bengio
As an experimental ML researcher,  
I want a pure-NumPy implementation of the Nadeau-Bengio corrected paired t-test,  
So that model comparisons across cross-validation folds account for training set overlap correlation without external runtime dependencies.

#### Acceptance Criteria
- **AC-M62-02-01**: WHEN invoking `paired_nadeau_bengio_test` with paired fold arrays of length $J \ge 2$ and train/val overlap ratio(s) $r$, the system SHALL compute mean difference $\bar{d}$, sample variance $S^2_d$ (`ddof=1`), corrected variance $\sigma_{\text{corr}}^2 = \left(\frac{1}{J} + \bar{r}\right) S^2_d$, $t$-statistic, degrees of freedom $\nu = J - 1$, two-sided $p$-value via exact Student-t CDF, and $(1-\alpha)$ confidence interval.
- **AC-M62-02-02**: IF `fold_val_sizes` are provided (or inferred from `train_val_ratios`) and their coefficient of variation ($\text{std}_{\text{ddof}=1} / \text{mean}$) exceeds $20\%$, THEN the system SHALL attach an explicit methodological warning to `NadeauBengioResult.warnings`.
- **AC-M62-02-03**: IF the sample variance of differences is zero ($S^2_d = 0$), THEN the system SHALL avoid division by zero, returning $t = 0.0$, $p = 1.0$, and $\text{CI} = (0.0, 0.0)$ when $\bar{d} = 0$, or $t = \text{sign}(\bar{d}) \cdot \infty$, $p = 0.0$, and $\text{CI} = (\bar{d}, \bar{d})$ when $\bar{d} \ne 0$, with an explicit `zero_difference_variance` warning.
- **AC-M62-02-04**: IF $J < 2$, `alpha` is not in $(0.0, 1.0)$, ratios are negative, arrays have mismatched lengths, or arrays contain `NaN`/`Inf`, THEN the system SHALL raise `ContractViolationError` or `ConfigurationError`.

---

### US-M62-03 (Priority: P1) — Teste Pareado de Wilcoxon e Tamanho de Efeito (Cohen's d)
As an experimental ML researcher,  
I want a pure-NumPy Wilcoxon signed-rank test and paired Cohen's d effect size estimator,  
So that non-parametric robustness and standardized effect magnitudes are reported alongside parametric tests.

#### Acceptance Criteria
- **AC-M62-03-01**: WHEN invoking `paired_wilcoxon_test` with paired arrays of length $J \ge 2$, the system SHALL handle zero differences according to `zero_method` (`"wilcox"` dropping zeros, or `"pratt"` ranking all $J$ absolute values and dropping zero ranks using Pratt's exact null mean $\mu_{W^+}$ and tie/zero-corrected variance $\sigma^2_{W^+}$), compute $W = \min(W^+, W^-)$ and $n_{\text{effective}} = J - n_0$, and compute exact two-sided $p$-values via dynamic programming on doubled ranks for $n_{\text{effective}} \le 20$ (and $J \le 25$) or normal approximation with continuity and tie corrections otherwise.
- **AC-M62-03-02**: IF all paired differences are zero ($n_{\text{effective}} = 0$), THEN the system SHALL return $W = 0.0$ and $p = 1.0$ without division by zero.
- **AC-M62-03-03**: IF $J < 6$ or $n_{\text{effective}} < 6$, THEN the system SHALL attach an explicit low-sample-size warning stating that two-sided significance at $\alpha = 0.05$ cannot be reached mathematically for $n_{\text{effective}} \le 5$.
- **AC-M62-03-04**: WHEN invoking `compute_paired_cohens_d`, the system SHALL compute $d_z = \bar{d} / s_d$ (`ddof=1`), analytical confidence interval $\bar{d}/s_d \pm t_{\alpha/2, J-1}\sqrt{1/J + d_z^2/(2J)}$ (with explicit CV non-correction caveat), and qualitative magnitude (`NEGLIGIBLE` for $|d_z| < 0.2$, `SMALL` for $0.2 \le |d_z| < 0.5$, `MEDIUM` for $0.5 \le |d_z| < 0.8$, `LARGE` for $|d_z| \ge 0.8$), handling $s_d = 0$ safely without `ZeroDivisionError`.

---

### US-M62-04 (Priority: P1) — Ajuste de Multiplicidade e Orquestração de Comparações
As an experimental ML researcher,  
I want multiplicity correction procedures (Holm-Bonferroni and Benjamini-Hochberg) and a unified comparison orchestrator,  
So that hypothesis families are properly controlled for false discoveries and incomplete or unsuitable comparisons are never silently fabricated.

#### Acceptance Criteria
- **AC-M62-04-01**: WHEN invoking `adjust_pvalues_holm`, the system SHALL apply the Holm-Bonferroni step-down procedure preserving original index order, enforcing monotonicity across sorted steps, handling ties identically, and clamping values to $[0.0, 1.0]$.
- **AC-M62-04-02**: WHEN invoking `adjust_pvalues_bh`, the system SHALL apply the Benjamini-Hochberg step-up procedure preserving original index order, enforcing step-up monotonicity, handling ties identically, and clamping values to $[0.0, 1.0]$.
- **AC-M62-04-03**: WHEN invoking `adjust_pvalues_holm` or `adjust_pvalues_bh` with out-of-range values ($p < 0$ or $p > 1$) or non-finite values (`NaN`/`Inf`), THEN the system SHALL raise `ContractViolationError`.
- **AC-M62-04-04**: WHEN invoking `run_statistical_comparisons`, the system SHALL generate candidate pairs according to `ComparisonSpec.comparison_scope`, verify fold eligibility via `check_pairwise_comparison_eligibility` and per-metric `MetricStatus.VALID` availability, align fold-level `train_val_ratios` and `fold_val_sizes` strictly to shared valid development folds, execute Nadeau-Bengio, Wilcoxon, and Cohen's $d$, evaluate practical relevance against $\Delta_{\text{min}}$ (when configured) without equating $p \ge \alpha$ to equivalence, and apply multiplicity correction independently for Nadeau-Bengio and Wilcoxon within each hypothesis family.
- **AC-M62-04-05**: IF the partition regime is `HOLDOUT_ONLY` ($J = 1$), fewer than 2 comparable configurations exist, or a candidate pair is ineligible/has `< 2` valid shared folds for the metric, THEN `run_statistical_comparisons` SHALL emit no multi-fold inferential test for that scope/pair and record explicit reasons in `StatisticalComparisonBundle.skipped_comparisons` or `non_applicable_reasons` without pseudoreplication or mixing `FINAL_HOLDOUT` metrics.

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| STAT-05 | AC-M62-01-01, AC-M62-01-02, AC-M62-01-03 | `experimental_ml.statistics.types` | pending |
| STAT-06 | AC-M62-02-01, AC-M62-02-02, AC-M62-02-03, AC-M62-02-04 | `experimental_ml.statistics.inference` | pending |
| STAT-07 | AC-M62-03-01, AC-M62-03-02, AC-M62-03-03, AC-M62-03-04 | `experimental_ml.statistics.inference` | pending |
| STAT-08 | AC-M62-04-01, AC-M62-04-02, AC-M62-04-03, AC-M62-04-04, AC-M62-04-05 | `experimental_ml.statistics.multiplicity`, `experimental_ml.statistics.comparisons` | pending |
