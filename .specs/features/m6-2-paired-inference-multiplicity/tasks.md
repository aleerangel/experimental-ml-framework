# m6-2-paired-inference-multiplicity Tasks (M6.2 Inferência Estatística Pareada, Tamanho de Efeito e Multiplicidade)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m6-2-paired-inference-multiplicity/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-16 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/statistics/ tests/integration/statistics/ -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `engenharia_software/ESPECIFICACAO_REQUISITOS.md`, `engenharia_software/ARQUITETURA_E_CONTRATOS.md`, `pyproject.toml`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Inference Types (`src/experimental_ml/statistics/types.py`) | unit | ComparisonScope, MultiplicityMethod, EffectSizeMagnitude, PracticalRelevanceStatus, ComparisonSpec, NadeauBengioResult, WilcoxonResult, EffectSizeResult, PairwiseComparisonResult, SkippedComparison, StatisticalComparisonBundle | `tests/unit/statistics/test_inference_types.py` | `.venv/bin/pytest tests/unit/statistics/test_inference_types.py -v` |
| Nadeau-Bengio & Student-t (`src/experimental_ml/statistics/inference.py`) | unit | Student-t CDF/quantis via betainc_reg, paired_nadeau_bengio_test, variância corrigida, variância nula (d=0 e d!=0), alerta CV > 20%, validações | `tests/unit/statistics/test_nadeau_bengio.py` | `.venv/bin/pytest tests/unit/statistics/test_nadeau_bengio.py -v` |
| Wilcoxon & Cohen's d (`src/experimental_ml/statistics/inference.py`) | unit | paired_wilcoxon_test (DP exata, wilcox vs pratt, aproximação normal, todos zeros, alerta n_eff < 6), compute_paired_cohens_d (dz, IC, magnitude, sd=0) | `tests/unit/statistics/test_wilcoxon_cohen.py` | `.venv/bin/pytest tests/unit/statistics/test_wilcoxon_cohen.py -v` |
| Multiplicity & Comparisons (`src/experimental_ml/statistics/comparisons.py`) | unit | adjust_pvalues_holm, adjust_pvalues_bh, run_statistical_comparisons (todos os 6 escopos, UNDEFINED_NAN, HOLDOUT_ONLY, relevância prática) | `tests/unit/statistics/test_multiplicity_comparisons.py` | `.venv/bin/pytest tests/unit/statistics/test_multiplicity_comparisons.py -v` |
| Integration & Purity (`tests/integration/statistics/test_m62_integration.py`) | integration | Fluxo M6.1 -> M6.2 ponta a ponta e verificação de pureza runtime XCUT-02 (zero scipy) | `tests/integration/statistics/test_m62_integration.py` | `.venv/bin/pytest tests/integration/statistics/test_m62_integration.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After tasks with unit tests in statistics | `.venv/bin/pytest tests/unit/statistics/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/unit/statistics/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Estruturas Imutáveis de Inferência e Comparação (`P1`)

Define `ComparisonScope`, `MultiplicityMethod`, `EffectSizeMagnitude`, `PracticalRelevanceStatus`, `ComparisonSpec` e os contratos de resultado congelados em `types.py`.

```
T1
```

### Phase 2: Distribuição Student-t Pura e Teste de Nadeau-Bengio (`P2`)

Implementar `betainc_reg`, `student_t_sf`, `student_t_ppf` em `_distributions.py` e `paired_nadeau_bengio_test` em `inference.py`.

```
T1 --> T2
```

### Phase 3: Teste Pareado de Wilcoxon e Tamanho de Efeito (`P3`)

Implementar `paired_wilcoxon_test` (DP exata + Pratt/Wilcox + aproximação normal) e `compute_paired_cohens_d` em `inference.py`.

```
T2 --> T3
```

### Phase 4: Multiplicidade e Orquestração de Comparações (`P4`)

Implementar `adjust_pvalues_holm` e `adjust_pvalues_bh` em `multiplicity.py` e `run_statistical_comparisons` em `comparisons.py`.

```
T3 --> T4
```

### Phase 5: API Pública e Integração Ponta a Ponta (`P5`)

Expor a API pública de M6.2 em `__init__.py` e validar o fluxo completo M6.1 -> M6.2 e pureza `XCUT-02`.

```
T4 --> T5
```

---

## Task Breakdown

### Phase 1: Estruturas Imutáveis de Inferência e Comparação

#### T1: Definir enums e dataclasses congeladas de inferência e comparação [ ]

**What**: Adicionar `ComparisonScope`, `MultiplicityMethod`, `EffectSizeMagnitude` e `PracticalRelevanceStatus` em `src/experimental_ml/statistics/types.py`. Implementar `ComparisonSpec`, `NadeauBengioResult`, `WilcoxonResult`, `EffectSizeResult`, `PairwiseComparisonResult`, `SkippedComparison` e `StatisticalComparisonBundle` com validações estruturais em `__post_init__` e imutabilidade completa (`frozen=True`). Adicionar testes unitários em `tests/unit/statistics/test_inference_types.py`.  
**Where**: `src/experimental_ml/statistics/types.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/metrics/types.py`, `src/experimental_ml/core/findings.py`  
**Requirement**: STAT-05  
**Tests**: `tests/unit/statistics/test_inference_types.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_inference_types.py -v`

---

### Phase 2: Distribuição Student-t Pura e Teste de Nadeau-Bengio

#### T2: Implementar distribuição Student-t pura e paired_nadeau_bengio_test [ ]

**What**: Criar `src/experimental_ml/statistics/_distributions.py` com `betainc_reg`, `student_t_sf` e `student_t_ppf` usando fração continuada de Lentz em Python/NumPy puro (`XCUT-02`). Criar `src/experimental_ml/statistics/inference.py` com `paired_nadeau_bengio_test(scores_a, scores_b, train_val_ratios, fold_val_sizes=None, alpha=0.05)` aplicando variância corrigida $(1/J + \bar{r}) S^2_d$, tratamento seguro de $S^2_d = 0$ ($\bar{d}=0$ vs $\bar{d}\ne 0$), alerta para CV $> 20\%$ e rejeição de entradas inválidas. Adicionar testes em `tests/unit/statistics/test_nadeau_bengio.py`.  
**Where**: `src/experimental_ml/statistics/inference.py`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/statistics/types.py`, `src/experimental_ml/core/findings.py`  
**Requirement**: STAT-06  
**Tests**: `tests/unit/statistics/test_nadeau_bengio.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_nadeau_bengio.py -v`

---

### Phase 3: Teste Pareado de Wilcoxon e Tamanho de Efeito

#### T3: Implementar paired_wilcoxon_test e compute_paired_cohens_d [ ]

**What**: Implementar `paired_wilcoxon_test` em `src/experimental_ml/statistics/inference.py` com `zero_method` (`"wilcox"` e `"pratt"` com média/variância exatas de Pratt), DP exata sobre postos dobrados para $n_{\text{eff}} \le 20$ e $J \le 25$, aproximação normal com continuidade e empates para amostras maiores, $W=0.0, p=1.0$ quando $n_{\text{eff}} = 0$ e aviso para $J < 6$ ou $n_{\text{eff}} < 6$. Implementar `compute_paired_cohens_d` com $d_z = \bar{d}/s_d$ (`ddof=1`), IC analítico com quantil $t_{\alpha/2, J-1}$ e ressalva de CV, classificação qualitativa e tratamento seguro de $s_d = 0$. Adicionar testes em `tests/unit/statistics/test_wilcoxon_cohen.py`.  
**Where**: `src/experimental_ml/statistics/inference.py`  
**Depends on**: T2  
**Reuses**: `src/experimental_ml/statistics/_distributions.py`, `src/experimental_ml/statistics/types.py`  
**Requirement**: STAT-07  
**Tests**: `tests/unit/statistics/test_wilcoxon_cohen.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_wilcoxon_cohen.py -v`

---

### Phase 4: Multiplicidade e Orquestração de Comparações

#### T4: Implementar ajuste de multiplicidade e orquestrador run_statistical_comparisons [ ]

**What**: Criar `src/experimental_ml/statistics/multiplicity.py` com `adjust_pvalues_holm` e `adjust_pvalues_bh`, preservando ordem, garantindo monotonicidade com empates e rejeitando valores fora de $[0, 1]$ ou não finitos. Criar `src/experimental_ml/statistics/comparisons.py` com `run_statistical_comparisons`, suportando os 6 escopos de `ComparisonScope`, integrando `check_pairwise_comparison_eligibility` e filtragem per-metric de `MetricStatus.VALID`, alinhando razões/tamanhos aos folds compartilhados, bloqueando `HOLDOUT_ONLY`, isolando `FINAL_HOLDOUT`, avaliando $\Delta_{\text{min}}$ e ajustando `nadeau_bengio` e `wilcoxon` por família. Adicionar testes em `tests/unit/statistics/test_multiplicity_comparisons.py`.  
**Where**: `src/experimental_ml/statistics/comparisons.py`  
**Depends on**: T3  
**Reuses**: `src/experimental_ml/statistics/suitability.py`, `src/experimental_ml/statistics/inference.py`  
**Requirement**: STAT-08  
**Tests**: `tests/unit/statistics/test_multiplicity_comparisons.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_multiplicity_comparisons.py -v`

---

### Phase 5: API Pública e Integração Ponta a Ponta

#### T5: Expor API pública de M6.2 e validar integração e pureza XCUT-02 [ ]

**What**: Atualizar `__all__` e exportações em `src/experimental_ml/statistics/__init__.py` com todos os tipos, enums e funções do M6.2. Criar testes de integração ponta a ponta M6.1 -> M6.2 e verificação de pureza runtime `XCUT-02` (bloqueando `scipy` em `sys.modules` via subprocesso isolado) em `tests/integration/statistics/test_m62_integration.py`.  
**Where**: `src/experimental_ml/statistics/__init__.py`  
**Depends on**: T4  
**Reuses**: `src/experimental_ml/statistics/types.py`, `inference.py`, `multiplicity.py`, `comparisons.py`  
**Requirement**: STAT-05, STAT-06, STAT-07, STAT-08  
**Tests**: `tests/integration/statistics/test_m62_integration.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/ tests/integration/statistics/ -v`

---

## Checks

**C1** - Enums `ComparisonScope`, `MultiplicityMethod`, `EffectSizeMagnitude` e `PracticalRelevanceStatus` contêm todos os valores canônicos. (STAT-05, AC-M62-01-01)  
Proof: run unit | tests/unit/statistics/test_inference_types.py::test_m62_01_enums_values PASSED

**C2** - `ComparisonSpec` valida escopos, direção das métricas, alpha em `(0, 1)`, baseline e pares planejados. (STAT-05, AC-M62-01-02)  
Proof: run unit | tests/unit/statistics/test_inference_types.py::test_m62_01_comparison_spec_validation PASSED

**C3** - Dataclasses de resultado (`NadeauBengioResult`, `WilcoxonResult`, `EffectSizeResult`, `PairwiseComparisonResult`, `SkippedComparison`, `StatisticalComparisonBundle`) são congeladas e lançam `FrozenInstanceError` ao tentar mutação. (STAT-05, AC-M62-01-03)  
Proof: run unit | tests/unit/statistics/test_inference_types.py::test_m62_01_frozen_immutability PASSED

**C4** - `paired_nadeau_bengio_test` computa variância corrigida, estatística t, nu=J-1, p-valor bicaudal via CDF exata e IC (1-alpha). (STAT-06, AC-M62-02-01)  
Proof: run unit | tests/unit/statistics/test_nadeau_bengio.py::test_m62_02_corrected_variance_and_pvalue PASSED

**C5** - `paired_nadeau_bengio_test` emite alerta metodológico quando CV do tamanho dos folds supera 20%. (STAT-06, AC-M62-02-02)  
Proof: run unit | tests/unit/statistics/test_nadeau_bengio.py::test_m62_02_fold_size_cv_warning PASSED

**C6** - `paired_nadeau_bengio_test` trata S^2_d = 0 sem divisão por zero distinguindo d_bar=0 de d_bar!=0. (STAT-06, AC-M62-02-03)  
Proof: run unit | tests/unit/statistics/test_nadeau_bengio.py::test_m62_02_zero_variance_handling PASSED

**C7** - `paired_nadeau_bengio_test` rejeita J < 2, alpha inválido, razões negativas, tamanhos diferentes ou NaN/Inf. (STAT-06, AC-M62-02-04)  
Proof: run unit | tests/unit/statistics/test_nadeau_bengio.py::test_m62_02_invalid_inputs_rejected PASSED

**C8** - `paired_wilcoxon_test` implementa `"wilcox"` e `"pratt"` (com média/variância exatas de Pratt), DP exata para n_eff <= 20 e aproximação normal com continuidade e empates para n_eff > 20. (STAT-07, AC-M62-03-01)  
Proof: run unit | tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_exact_pratt_and_normal PASSED

**C9** - `paired_wilcoxon_test` retorna W=0.0 e p=1.0 quando todas as diferenças são zero (n_eff = 0). (STAT-07, AC-M62-03-02)  
Proof: run unit | tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_all_zeros PASSED

**C10** - `paired_wilcoxon_test` anexa aviso explícito de amostra pequena quando J < 6 ou n_eff < 6. (STAT-07, AC-M62-03-03)  
Proof: run unit | tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_wilcoxon_small_sample_warning PASSED

**C11** - `compute_paired_cohens_d` calcula d_z, IC analítico com ressalva de CV, classificação qualitativa e trata s_d = 0 com segurança. (STAT-07, AC-M62-03-04)  
Proof: run unit | tests/unit/statistics/test_wilcoxon_cohen.py::test_m62_03_cohens_d_and_ci PASSED

**C12** - `adjust_pvalues_holm` aplica procedimento step-down de Holm-Bonferroni preservando ordem, monotonicidade e empates. (STAT-08, AC-M62-04-01)  
Proof: run unit | tests/unit/statistics/test_multiplicity_comparisons.py::test_m62_04_holm_bonferroni_adjustment PASSED

**C13** - `adjust_pvalues_bh` aplica procedimento step-up de Benjamini-Hochberg preservando ordem, monotonicidade e empates. (STAT-08, AC-M62-04-02)  
Proof: run unit | tests/unit/statistics/test_multiplicity_comparisons.py::test_m62_04_benjamini_hochberg_adjustment PASSED

**C14** - `adjust_pvalues_holm` e `adjust_pvalues_bh` rejeitam valores fora de [0, 1] ou NaN/Inf com `ContractViolationError`. (STAT-08, AC-M62-04-03)  
Proof: run unit | tests/unit/statistics/test_multiplicity_comparisons.py::test_m62_04_invalid_pvalues_raise PASSED

**C15** - `run_statistical_comparisons` executa todos os 6 escopos de `ComparisonScope`, filtra métricas `UNDEFINED_NAN`, alinha razões de folds compartilhados, avalia Delta_min e ajusta multiplicidade por família. (STAT-08, AC-M62-04-04)  
Proof: run unit | tests/unit/statistics/test_multiplicity_comparisons.py::test_m62_04_orchestrator_scopes_nan_and_practical_relevance PASSED

**C16** - `run_statistical_comparisons` bloqueia inferência multi-fold em `HOLDOUT_ONLY`, isola `FINAL_HOLDOUT` em `CV_AND_HOLDOUT` e registra pares inelegíveis em `skipped_comparisons`. (STAT-08, AC-M62-04-05)  
Proof: run unit | tests/unit/statistics/test_multiplicity_comparisons.py::test_m62_04_holdout_protection_and_skipped_pairs PASSED

**C17** - Fluxo integrado ponta a ponta M6.1 -> M6.2 via API pública de `experimental_ml.statistics`. (STAT-05)  
Proof: run unit | tests/integration/statistics/test_m62_integration.py::test_m62_end_to_end_pipeline PASSED

**C18** - Subsistema de inferência estatística opera 100% em Python/NumPy puro sem importação de `scipy`. (XCUT-02)  
Proof: run unit | tests/integration/statistics/test_m62_integration.py::test_m62_runtime_purity_xcut02 PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T1
- **Next Task:** T2
