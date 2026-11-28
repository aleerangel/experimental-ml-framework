# Verificação Independente TLC — M11.3 (`m11-3-dataset-characterization`)

- **Feature**: `m11-3-dataset-characterization`
- **Veredito**: **PASS**
- **Data**: 2026-11-28
- **Suite executada**: `.venv/bin/pytest tests/unit/data/test_profiling.py tests/unit/features/test_stats.py tests/unit/features/test_exploration.py tests/unit/reporting/test_reporting_report.py tests/integration/reporting/test_m11_3_dataset_characterization_e2e.py -q` → `31 passed in 3.55s`

---

## Checks

**C1** (`M113-01`, `AD-040`, `XCUT-02`) — `NumericDistributionStats` calcula momentos leves e `profile_dataset(extended_stats=True)` preenche indicadores SVD/razão/entropia
- **Veredito**: **PASS**
- **Evidência de código**:
  - `src/experimental_ml/data/profiling.py`: `NumericDistributionStats` inclui `skewness`, `kurtosis` (excesso de Fisher `- 3.0`) e `outlier_rate_iqr` em NumPy puro, com guardas para `n_valid == 0`, `n_valid == 1`, `m2 <= 1e-15`, `n_valid < 3` (`skewness`) e `n_valid < 4` (`kurtosis`).
  - `DatasetProfile` inclui `samples_to_features_ratio`, `intrinsic_dim_ratio_95` (SVD sobre matriz numérica padronizada com imputação média local temporária sem alterar `DatasetBundle`) e `target_entropy_norm`, mantidos em `None` quando `extended_stats=False` (padrão).
  - `src/experimental_ml/data/codecs.py`: round-trip JSON completo para momentos leves e indicadores estruturais em `_numeric_stats_to_dict`/`_numeric_stats_from_dict` e `dataset_profile_to_dict`/`dataset_profile_from_dict`.
- **Evidência de teste**: `tests/unit/data/test_profiling.py::test_m11_3_numeric_moments_and_extended_profile` (PASSED).

**C2** (`M113-02`, `XCUT-02`, `XCUT-01`) — `compute_vif`, `compute_distance_correlation` e `compute_linearity_score` em NumPy puro integram `explore_features(extended_stats=True)`
- **Veredito**: **PASS**
- **Evidência de código**:
  - Zero importações de `scipy` em `src/experimental_ml/data/`, `src/experimental_ml/features/`, `src/experimental_ml/reporting/` e `src/experimental_ml/pipeline.py`.
  - `src/experimental_ml/features/stats.py`: `compute_vif` via `np.linalg.pinv`, `compute_distance_correlation` (Székely et al., 2007) em NumPy puro com subamostragem determinística acima de `max_samples=2000`, e `compute_linearity_score` (OLS $R^2$ via `np.linalg.lstsq` em regressão; acurácia balanceada Ridge/LDA via `np.linalg.pinv` em classificação).
  - `src/experimental_ml/features/types.py` e `src/experimental_ml/features/exploration.py`: `explore_features(..., extended_stats: bool = False)` preenche `extended_diagnostics` apenas quando `extended_stats=True`, sob `scope="EXPLORATORY_FULL_DATA"`, sem alterar `SanitizedDatasetView` e sem seleção automática pré-split; `build_dataset_meta_features` consolida o dicionário padronizado.
- **Evidência de teste**: `tests/unit/features/test_stats.py::test_m11_3_vif_distance_corr_and_linearity` e `tests/unit/features/test_exploration.py::test_m11_3_explore_features_extended_opt_in` (PASSED).

**C3** (`M113-03`, `AD-040`) — `run_experiment(export_meta_features=True)` grava `dataset_meta_features.json` e exibe tabela `pt-BR` no relatório sem efeitos quando `False`
- **Veredito**: **PASS**
- **Evidência de código**:
  - `src/experimental_ml/pipeline.py`: `run_experiment` expõe `extended_stats: bool = False` e `export_meta_features: bool = False`; quando `export_meta_features=True`, ativa `use_extended=True` e grava `dataset_meta_features.json` via `write_json_atomic`.
  - `src/experimental_ml/reporting/types.py` e `loader.py`: `LoadedExperimentData.dataset_meta_features` e leitura opcional de `dataset_meta_features.json`.
  - `src/experimental_ml/reporting/report.py`: renderiza a tabela `Caracterização Estatística Ampliada (Meta-Features)` em `pt-BR` tanto em `markdown` quanto em `html` apenas quando `dataset_meta_features` está presente.
  - `docs/guia/03_interpretando_resultados.md`: documenta o comportamento opt-in de `extended_stats=True` e `export_meta_features=True`.
- **Evidência de teste**: `tests/unit/reporting/test_reporting_report.py::test_m11_3_report_includes_dataset_meta_features` e `tests/integration/reporting/test_m11_3_dataset_characterization_e2e.py::test_m11_3_e2e_opt_in_dataset_meta_features` (PASSED).
