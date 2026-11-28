# Resultados de Homologação — Submarco M11.3: Caracterização Estatística Ampliada (`VAL-ENH-007`)

- **Submarco:** `M11.3` (`m11-3-dataset-characterization`)
- **Branch:** `feat/m11-3-dataset-characterization`
- **Status:** `VERIFICADO (PASS)` (Aguardando aceite do consumidor em `ACCEPTANCE.md` e merge em `main`)
- **Suíte de Testes:** `647 passed in 98.11s` (`.venv/bin/pytest tests/ -q`)
- **Verificador Independente:** [`verification.md`](./verification.md) — `C1`–`C3` aprovados (`PASS`, `31 passed in 3.55s`)

---

## Resumo das Entregas (`T1`–`T4`)

1. **T1 (`cafd596`)**: `NumericDistributionStats` com `skewness`, excesso de `kurtosis` (Fisher) e `outlier_rate_iqr` em NumPy puro; `profile_dataset(..., extended_stats=False)` opt-in preenchendo `samples_to_features_ratio`, `intrinsic_dim_ratio_95` (SVD $\ge 95\%$) e `target_entropy_norm` com round-trip JSON em `data/codecs.py`.
2. **T2 (`52e8974`)**: `compute_vif` (`np.linalg.pinv`), `compute_distance_correlation` (Székely et al., 2007) e `compute_linearity_score` (OLS $R^2$ / Ridge-LDA NumPy) em `features/stats.py` (`XCUT-02`), integrados a `explore_features(..., extended_stats=False)` sob `EXPLORATORY_FULL_DATA`.
3. **T3 (`871811d`)**: `build_dataset_meta_features`, carregamento opcional em `LoadedExperimentData` / `loader.py` e tabela `Caracterização Estatística Ampliada (Meta-Features)` em `pt-BR` nos relatórios Markdown/HTML.
4. **T4 (`bc994e5`)**: Exposição opt-in (`extended_stats=False`, `export_meta_features=False`) em `run_experiment`, documentação em `docs/guia/03_interpretando_resultados.md` e teste E2E (`test_m11_3_dataset_characterization_e2e.py`).
