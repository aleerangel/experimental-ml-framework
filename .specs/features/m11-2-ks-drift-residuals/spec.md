# M11.2 — Teste Kolmogorov-Smirnov, Detecção de *Dataset Shift* e Diagnóstico de Resíduos OOF

- **Status**: Approved (`AD-039`, `XCUT-02`) — Fase TLC: **Specify**
**Approved**: 2026-11-28 - user: "aprovado"
- **Milestone**: `M11.2` (`m11-2-ks-drift-residuals`)
- **Branch**: `feat/m11-2-ks-drift-residuals`
- **Related Validation Finding**: `VAL-ENH-006`

---

## Problem Statement

O framework não possui testes de aderência distribucional nem verificação de *dataset shift* entre partições (`development_ids` vs. `holdout_ids` em `CV_AND_HOLDOUT` ou entre folds em `TEMPORAL`), nem diagnóstico estatístico e visual dos resíduos *out-of-fold* (OOF) em regressão (normalidade via Lilliefors, caudas pesadas Normal vs. Student-$t$ e gráfico `Resíduos vs. Predito + Q-Q Plot`).

---

## Architectural Decision (`AD-039`, `XCUT-02`)

- **Núcleo em NumPy puro (`XCUT-02`):** Todas as rotinas de KS (`ks_2samp`, `ks_normal_lilliefors`, log-verossimilhança/AIC Normal vs. Student-$t$) são implementadas em Python + NumPy puro sem dependência de `scipy`.
- **Transparência e opt-in explícito (`AD-039`):** Nenhum cálculo adicional ocorre de forma oculta; as análises são acionadas explicitamente pelo pesquisador via parâmetros (`check_ks_drift: bool = False`, `analyze_oof_residuals: bool = False`) em `run_experiment` / CLI (`--check-ks-drift`, `--analyze-oof-residuals`), documentadas como recomendadas conforme o regime/tarefa.

---

## Requirements (EARS Notation)

### M112-01 — Testes Kolmogorov-Smirnov em NumPy Puro (`statistics`)
- **THE SYSTEM SHALL** disponibilizar `ks_2samp(a, b)` retornando estatística $D_{\text{KS}} \in [0, 1]$ e $p$-valor assintótico (Kolmogorov 1933; Smirnov 1948), e `ks_normal_lilliefors(x)` para aderência à Normal com média e desvio estimados da amostra (Lilliefors 1967; Stephens 1974), utilizando exclusivamente Python + NumPy puro.

### M112-02 — Detecção Opt-In de *Dataset Shift* entre Partições (`validation`, `statistics`, `pipeline`)
- **WHEN** `check_ks_drift=True` (padrão `False`) é solicitado em `CV_AND_HOLDOUT` ou `TEMPORAL`, **THE SYSTEM SHALL** aplicar `ks_2samp` por atributo numérico e alvo entre `development_ids` e `holdout_ids` (ou primeiro vs. último fold temporal), reportando $D_{\text{KS}}$, $p$-valor e sinalização de *shift* quando $D_{\text{KS}}$ e $p$-valor indicarem divergência relevante, sem alterar métricas ou testes pareados de `DEV_CV`.

### M112-03 — Diagnóstico Opt-In de Resíduos OOF e Q-Q Plot (`statistics`, `reporting`)
- **WHEN** `analyze_oof_residuals=True` (padrão `False`) é solicitado em tarefa de regressão com predições OOF disponíveis, **THE SYSTEM SHALL** avaliar os resíduos OOF ($y - \hat{y}$) com `ks_normal_lilliefors` e comparação AIC Normal vs. Student-$t$, além de gerar gráfico diagnóstico `Resíduos vs. Predito` e `Q-Q Plot` na Etapa 6 (`PNG`, `SVG`, `PDF`).

---

## Out of Scope
- Caracterização estatística ampliada de atributos (`skewness`, `kurtosis`, VIF, *Distance Correlation*, SVD, `dataset_meta_features`) — escopo de `M11.3` (`VAL-ENH-007`).
- Múltiplos objetivos de Pareto e `planned_pairs` via CLI — escopo de `M11.4` (`VAL-ENH-004`).
- Ajuste MLE iterativo multi-distribuição (Gamma, Weibull, Beta) — escopo de `Onda 2`.

---

## User Stories

1. **Como pesquisador**, quero poder ativar explicitamente a checagem de *dataset shift* (`--check-ks-drift`) em regimes `CV_AND_HOLDOUT` e `TEMPORAL` para saber se o conjunto de teste/holdout diverge estatisticamente do desenvolvimento.
2. **Como pesquisador**, quero poder ativar a análise de resíduos OOF (`--analyze-oof-residuals`) em regressão para inspecionar normalidade (Lilliefors), caudas pesadas (Normal vs. Student-$t$) e Q-Q Plot na Etapa 6.

---

## Assumptions & Open Questions

### Assumptions
- `ks_2samp` e `ks_normal_lilliefors` exigem amostra mínima finita (ex.: $n \ge 5$) e ignoram valores `NaN`/não-finitos com reporte claro de status quando insuficientes.
- Gráficos de resíduos + Q-Q Plot utilizam o backend Matplotlib (`Agg`) já autorizado em `reporting/figures.py` (`AD-033`).

### Open Questions
Open questions: none (`AD-039` aprovada pelo desenvolvedor em 2026-11-28).

---

## Requirement Traceability

| Requisito | Origem | Critério de Verificação |
| :--- | :--- | :--- |
| M112-01 | `VAL-ENH-006`, `XCUT-02` | `C1`: `ks_2samp` e `ks_normal_lilliefors` em NumPy puro calculam $D_{\text{KS}}$ e $p$-valor consistentes |
| M112-02 | `VAL-ENH-006`, `AD-039` | `C2`: `check_ks_drift` (opt-in `False` por padrão) detecta *shift* em `CV_AND_HOLDOUT` e `TEMPORAL` sem alterar `DEV_CV` |
| M112-03 | `VAL-ENH-006`, `AD-039` | `C3`: `analyze_oof_residuals` (opt-in `False` por padrão) computa Lilliefors + AIC Normal vs. Student-$t$ e gera Q-Q Plot em `PNG`/`SVG`/`PDF` |
