# Design — Submarco M11.3 (`m11-3-dataset-characterization`)

## Arquitetura e Fluxo de Dados

1. **`src/experimental_ml/data/profiling.py` e `data/codecs.py` / `data/storage.py`**
   - `NumericDistributionStats`: adiciona `skewness: float | None = None`, `kurtosis: float | None = None`, `outlier_rate_iqr: float | None = None`.
   - `DatasetProfile`: adiciona campos opcionais `samples_to_features_ratio: float | None = None`, `intrinsic_dim_ratio_95: float | None = None`, `target_entropy_norm: float | None = None`.
   - `profile_dataset(..., extended_stats: bool = False)`: quando `False`, preserva custo zero de SVD/entropia; quando `True`, calcula os três indicadores estruturais em NumPy puro (usando imputação média temporária local apenas para SVD quando houver `NaN`, sem alterar dados).

2. **`src/experimental_ml/features/stats.py` e `features/exploration.py`**
   - `compute_vif(X: np.ndarray) -> tuple[np.ndarray, MetricStatus]`: calcula VIF por coluna usando `np.linalg.pinv` da matriz de correlação padronizada (com guarda para variância zero / colinearidade extrema).
   - `compute_distance_correlation(x: np.ndarray, y: np.ndarray) -> tuple[float, MetricStatus]`: *Distance Correlation* em NumPy puro (matrizes de distância centradas duplamente, Székely et al., 2007), com amostragem determinística opcional se $n > 2000$ ou cálculo direto para $n \le 2000$.
   - `compute_linearity_score(X: np.ndarray, y: np.ndarray, task_type: TaskType) -> tuple[float, MetricStatus]`: OLS $R^2$ (`np.linalg.lstsq` com intercepto) para regressão; acurácia balanceada de classificador linear Ridge/LDA (`np.linalg.pinv` sobre alvos one-hot centrados) para classificação.
   - `explore_features(view, ..., extended_stats: bool = False)`: preenche `extended_diagnostics: dict[str, Any] | None = None` no `ExploratoryFeatureReport` apenas quando `extended_stats=True`, mantendo `scope="EXPLORATORY_FULL_DATA"`.

3. **Meta-Features & Reporting (`features/exploration.py`, `reporting/{types,loader,report}.py`, `pipeline.py`)**
   - Função pura `build_dataset_meta_features(profile: DatasetProfile, report: ExploratoryFeatureReport) -> dict[str, Any]` agregando dimensões (`n_rows`, `n_features`, `samples_to_features_ratio`, `intrinsic_dim_ratio_95`, `target_entropy_norm`), sumários de distribuição (`mean_abs_skewness`, `mean_excess_kurtosis`, `mean_outlier_rate_iqr`) e estrutura (`max_vif`, `mean_vif`, `mean_distance_correlation_target`, `linearity_score`).
   - `run_experiment(..., extended_stats: bool = False, export_meta_features: bool = False)`: se `export_meta_features=True`, ativa `extended_stats=True` para o perfil/exploração e grava `dataset_meta_features.json` no diretório do experimento.
   - `LoadedExperimentData.dataset_meta_features: dict[str, Any] | None = None` carregado em `loader.py` e renderizado em `report.py` como tabela `Caracterização Estatística Ampliada (Meta-Features)` quando presente.
