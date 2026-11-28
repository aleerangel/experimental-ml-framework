# M11.2 — Teste Kolmogorov-Smirnov, Detecção de *Dataset Shift* e Diagnóstico de Resíduos OOF Verification

**HEAD**: 79b91ce
**Verdict**: PASS

---

## Checks

| Check | Status | Test | Verdict & Notes |
| :--- | :--- | :--- | :--- |
| C1 | PASS | `tests/unit/statistics/test_ks_diagnostics.py::test_m11_2_ks_2samp_and_lilliefors_pure_numpy` | Valida `ks_2samp`, `ks_normal_lilliefors` e `compare_normal_vs_student_t` em `src/experimental_ml/statistics/distributions_diagnostics.py` usando exclusivamente Python + NumPy puro (zero `scipy`, `XCUT-02`), exportados em `src/experimental_ml/statistics/__init__.py`. Confirma $D_{\text{KS}}$ e $p$-valor consistentes para distribuições idênticas vs. deslocadas, Lilliefors para Normal vs. Exponencial, e $\text{AIC}_{\text{Student-}t} < \text{AIC}_{\text{Normal}}$ em dados com caudas pesadas ($t$ com $\nu=3$). Sem mocks ou asserções relaxadas. |
| C2 | PASS | `tests/unit/statistics/test_ks_diagnostics.py::test_m11_2_partition_ks_drift_cv_holdout_and_temporal` | Valida `compute_partition_ks_drift` em `CV_AND_HOLDOUT` (`DEV` vs. `FINAL_HOLDOUT`) e `TEMPORAL` (`TEMPORAL_INICIAL` vs. `TEMPORAL_FINAL`), além da flag opt-in `check_ks_drift: bool = False` em `src/experimental_ml/pipeline.py` (linhas 231, 536–543) sem alterar métricas ou testes pareados de `DEV_CV`. Sem mocks ou asserções relaxadas. |
| C3 | PASS | `tests/integration/reporting/test_m11_2_ks_drift_residuals_e2e.py::test_m11_2_e2e_opt_in_ks_drift_and_oof_qq_plot` | Valida comportamento padrão (`False`, sem artefatos extras) e opt-in (`check_ks_drift=True`, `analyze_oof_residuals=True`) via `run_experiment`: gera `statistics/ks_drift_report.json`, `statistics/oof_residuals_diagnostics.json` e `reports/figures/fig_oof_residuals_qq.png` (assinatura PNG válida), além de seções em `pt-BR` em `report.md` e `report.html`. Complementado pelos testes unitários `tests/unit/reporting/test_reporting_figures.py::test_m11_2_residuals_qq_plot_formats` (painel duplo `Resíduos OOF vs. Predito` + `Q-Q Plot Normal` em `PNG`, `SVG` e `PDF`) e `tests/unit/reporting/test_reporting_report.py::test_m11_2_report_includes_ks_drift_and_residuals`. Documentação em `docs/guia/03_interpretando_resultados.md` (linhas 79–83) alinhada. |

---

## Findings

none

---

## Walk

- **Especificação e Artefatos TLC**:
  - `.specs/features/m11-2-ks-drift-residuals/spec.md` (linhas 1–68)
  - `.specs/features/m11-2-ks-drift-residuals/design.md` (linhas 1–29)
  - `.specs/features/m11-2-ks-drift-residuals/tasks.md` (linhas 1–88)
  - `.specs/features/m11-2-ks-drift-residuals/proofs.md` (linhas 1–45)
- **C1**:
  - Teste: `tests/unit/statistics/test_ks_diagnostics.py` (linhas 15–48)
  - Implementação: `src/experimental_ml/statistics/distributions_diagnostics.py` (linhas 1–207), `src/experimental_ml/statistics/__init__.py` (linhas 11–20)
- **C2**:
  - Teste: `tests/unit/statistics/test_ks_diagnostics.py` (linhas 50–110)
  - Implementação: `src/experimental_ml/statistics/distributions_diagnostics.py` (linhas 209–325), `src/experimental_ml/pipeline.py` (linhas 231, 536–543)
- **C3**:
  - Testes: `tests/integration/reporting/test_m11_2_ks_drift_residuals_e2e.py` (linhas 28–84), `tests/unit/reporting/test_reporting_figures.py` (linhas 244–266), `tests/unit/reporting/test_reporting_report.py` (linhas 171–204)
  - Implementação: `src/experimental_ml/pipeline.py` (linhas 232, 545–568, 588–596), `src/experimental_ml/reporting/types.py` (linhas 214–226), `src/experimental_ml/reporting/loader.py` (linhas 51–52, 81–82), `src/experimental_ml/reporting/figures.py` (linhas 449–514), `src/experimental_ml/reporting/report.py` (linhas 125–151, 221–240), `docs/guia/03_interpretando_resultados.md` (linhas 79–83)
