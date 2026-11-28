# Resultados de Homologação — Submarco M11.2: KS, Dataset Shift e Resíduos OOF (`VAL-ENH-006`)

- **Submarco:** `M11.2` (`m11-2-ks-drift-residuals`)
- **Branch:** `feat/m11-2-ks-drift-residuals`
- **Status:** `VERIFICADO (PASS)` (Aguardando aceite do consumidor em `ACCEPTANCE.md` e merge em `main`)
- **Suíte de Testes:** `642 passed in 82.01s` (`.venv/bin/pytest tests/ -q`)
- **Verificador Independente:** [`verification.md`](./verification.md) — `C1`–`C3` aprovados (`PASS`)

---

## Resumo das Entregas (`T1`–`T4`)

1. **T1 (`f0ab8f8`)**: Núcleo estatístico em NumPy puro (`src/experimental_ml/statistics/distributions_diagnostics.py`, zero `scipy`): `KSTestResult`, `ResidualDistributionFit`, `ks_2samp`, `ks_normal_lilliefors` e `compare_normal_vs_student_t` (EM sobre grade de $\nu$ + AIC).
2. **T2 (`a70bef8`, fix `79b91ce`)**: Orquestração pura `compute_partition_ks_drift`, `analyze_oof_residuals_map`, serialização JSON (`partition_drift_to_dict`, `oof_residuals_to_dict`) e leitura retrocompatível em `LoadedExperimentData` / `load_experiment_artifacts_readonly`.
3. **T3 (`e29f822`)**: Painel duplo `Resíduos vs. Predito + Q-Q Plot` (`_norm_ppf_approx` e `render_residuals_diagnostic_figure` em `PNG`/`SVG`/`PDF`) e tabelas `Diagnóstico de Dataset Shift` e `Diagnóstico de Resíduos OOF` em `pt-BR` nos relatórios Markdown/HTML.
4. **T4 (`282f650`)**: Exposição opt-in (`check_ks_drift=False`, `analyze_oof_residuals=False`) em `run_experiment`, documentação em `docs/guia/03_interpretando_resultados.md` e teste E2E (`test_m11_2_ks_drift_residuals_e2e.py`).
