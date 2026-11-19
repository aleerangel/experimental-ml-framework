# Referência da API Python Pública

Esta referência cataloga a **API pública oficial** do `experimental-ml`, delimitada estritamente pelos símbolos, classes declarativas (*dataclasses*), enumerações e funções exportadas no nível superior (`__init__.py` e `__all__`) do **pacote raiz** (`experimental_ml`) e dos **11 subpacotes públicos** do framework.

> [!NOTE]
> **Fronteira de Estabilidade:** Módulos auxiliares internos (como `orchestration.codecs`, formatadores internos de SVG/tabelas, parsers auxiliares e funções iniciadas por `_`) não compõem a API pública e não devem ser importados diretamente por código de pesquisa.

---

## 0. `experimental_ml` (Fachada de Alto Nível)

- **Ponto de Entrada Unificado:** `run_experiment(data, models, output_dir, *, target=None, task=None, schema=None, scenarios=None, partition_config=None, cv_folds=5, group_col=None, metrics=None, rules=(), alpha=0.05, master_seed=42, force=True, delimiter=None, decimal=".", encoding="utf-8-sig", has_header=True, column_names=None, quotechar='"', csv_format=None) -> ExperimentRunSummary` — executa ponta a ponta as Etapas 1 a 6 aceitando entradas simples ou contratos formais completos (incluindo formatação regional de CSV).
- **Resumo Imutável:** `ExperimentRunSummary` (atributos: `experiment_dir`, `dataset_hash`, `partition_plan_id`, `completed_cells`, `failed_cells`, `observed_leader`, `statistical_evidence_status`, `report_md_path`, `report_html_path`, `consolidation`, `conclusion`; método `summary() -> str`).
- **Metadados:** `__version__` (`str`).

---

## 1. `experimental_ml.core` (Nível 0 — Fundamentos e Determinismo)

- **Identificadores e Tipos:** `ExperimentId`, `ModelId`, `ScenarioId`, `PartitionPlanId`, `CellId`, `ComparisonId`, `ArtifactId`, `ObservationId`.
- **Enumerações:** `TaskType`, `MetricDirection`, `MetricStatus`, `ExecutionStatus`, `ErrorPolicy`, `AggregationScope`, `FindingSeverity`.
- **Exceções Contratuais:** `ExperimentalMLError` (base), `ConfigurationError`, `ContractViolationError`, `DataIntegrityError`.
- **Diagnóstico e Utilitários:** `Finding`, `make_finding`, `make_warning`, `config_hash`, `dataset_hash`, `derive_seeds`, `spawn_child_seeds`, `is_missing_scalar`, `is_nan_scalar`.

---

## 2. `experimental_ml.data` (Etapa 1 — Ingestão, Diagnóstico e Saneamento)

- **Ingestão Imutável:** `load_dataset(source, schema, *, delimiter=None, has_header=True, column_names=None, encoding="utf-8-sig", decimal=".", quotechar='"', csv_format=None) -> DatasetBundle`
- **Formatação CSV e Detecção:** `CsvFormatSpec`, `validate_csv_format_spec`, `detect_delimiter`, `detect_decimal`.
- **Esquema e Descritores:** `DatasetSchemaSpec`, `DatasetBundle`, `ColumnDescriptor`, `ColumnSemanticType`, `validate_schema_spec`, `validate_dataset_schema`, `assign_or_validate_observation_ids`.
- **Triagem e Perfilamento:** `profile_dataset(bundle, config=None) -> DatasetProfile`, `DatasetProfile`, `ColumnProfile`, `ProfileConfig`.
- **Saneamento Determinístico:** `create_preparation_plan(profile, rules) -> PreparationPlan`, `sanitize_dataset(bundle, profile, plan) -> SanitizedDatasetView`, `PreparationPlan`, `PreparationRule`, `SanitizedDatasetView`, `UnresolvedFinding`.
- **Fatiamento Seguro:** `get_column_array`, `slice_bundle_by_observation_ids`, `slice_view_by_observation_ids`.

---

## 3. `experimental_ml.metrics` (Nível 1 — Métricas e Agregação)

- **Catálogo e Despacho:** `METRICS_CATALOG`, `MetricSpec`, `MetricValue`, `MetricEvaluationScope`, `compute_metric(metric_id, y_true, y_pred_or_score, **kwargs) -> MetricValue`, `get_metric_spec`, `list_metrics`.
- **Agregação e Ranking (`ADR-005`):** `AggregatedMetricValue`, `RankedCandidate`, `aggregate_fold_metrics`, `is_better`, `rank_configurations`.
- **Classificação:** `accuracy`, `balanced_accuracy`, `precision`, `recall`, `f1`, `roc_auc` (`requires_probabilities=True`), `log_loss` (`requires_probabilities=True`).
- **Regressão e Kernel:** `mae`, `rmse`, `rmse_rel_pct`, `r2`, `mape`, `mbe` (`compare_by_abs=True`), `pearson`, `kta` (`requires_kernel_matrix=True`).

---

## 4. `experimental_ml.features` (Etapa 2 — Exploração e Cenários)

- **Análise Exploratória e Visualização:** `explore_features`, `ExploratoryFeatureReport` (métodos `.ranked_target_features()` e `.summary(top_n=15)`), `RedundancyPair`, `AssociationMeasure`, `SCOPE_EXPLORATORY_FULL_DATA`, `METHODOLOGICAL_WARNINGS`, `compute_pearson`, `compute_spearman`, `compute_correlation_ratio`, `compute_cramers_v`, `render_exploratory_report`, `render_exploratory_target_chart`, `render_exploratory_redundancy_heatmap`, `render_exploratory_target_csv`, `render_exploratory_redundancy_csv`.
- **Cenários de Features:** `FeatureScenario`, `ScenarioMode` (`FIXED`, `DYNAMIC`), `ScenariosCatalog`, `validate_scenarios`, `save_scenarios`, `load_scenarios`.
- **Seleção Intra-Fold e Estabilidade:** `select_features_in_fold`, `apply_feature_selection`, `SelectionResult`, `compute_selection_stability`, `SelectionStabilityReport` (Jaccard e Kuncheva corrigido).

---

## 5. `experimental_ml.models` (Etapa 3A — Especificação e Execução Isolada)

- **Especificação e Capacidades:** `ModelSpec`, `ModelCapabilities`, `ModelFamily`, `ModelsCatalog`, `validate_model_spec`, `validate_models_catalog`, `save_models_catalog`, `load_models_catalog`.
- **Execução e Isolamento:** `instantiate_fresh_model(spec, seed=None)`, `fit_model`, `predict_model`, `extract_model_diagnostics`, `ModelDiagnostics`, `reset_active_instances`.
- **Pré-processamento em 2 Camadas (`experimental_ml.models.preprocessing`):** `TwoLayerPreprocessingSpec`, `TwoLayerPreprocessingState`, `ScalerType`, `PrecomputedKernelAdapter`, `validate_two_layer_preprocessing`, `fit_two_layer_preprocessing`, `apply_two_layer_preprocessing`.
- **Baselines Embutidos:** `DummyBaselineModel`, `AnalyticalBiometricModel` (`requires_fit=False`).

---

## 6. `experimental_ml.tuning` (Etapa 3B — Busca Aninhada / Nested CV)

- **Especificação:** `HyperparameterSearchSpec`, `SearchStrategy` (`GRID_SEARCH`, `RANDOM_SEARCH`), `validate_search_spec`.
- **Execução Aninhada:** `run_nested_tuning`, `split_inner_folds`, `generate_candidates`, `TuningResult`, `TuningTrialRecord`, `TuningOptimizationError`.

---

## 7. `experimental_ml.validation` (Etapa 4A — Particionamento Compartilhado)

- **Configuração e Plano:** `PartitionConfig`, `PartitionPlan`, `FoldPartition`, `PartitionStrategy` (`KFOLD`, `STRATIFIED_KFOLD`, `GROUP_KFOLD`, `TEMPORAL`, `HOLDOUT`), `EvaluationRegime` (`CV_ONLY`, `HOLDOUT_ONLY`, `CV_AND_HOLDOUT`).
- **Geração e Auditoria:** `build_partition_plan(view, config) -> PartitionPlan`, `validate_partition_plan(plan, view)`.

---

## 8. `experimental_ml.orchestration` (Etapa 4B — Execução Matricial)

- **Execução e Retomada:** `run_experiment_matrix`, `resume_experiment_matrix`, `execute_single_cell`, `build_cell_matrix`, `derive_cell_seed`.
- **Estado e Predições:** `MatrixExecutionState`, `CellDescriptor`, `CellPhase`, `CellResultRecord`, `TimingBreakdown`, `PredictionRecord`, `ConsolidatedOofPredictions`, `consolidate_matrix_oof`, `consolidate_oof_predictions`.
- **Persistência e Callbacks:** `save_cell_artifacts`, `load_cell_artifacts`, `save_execution_state`, `load_execution_state`, `save_oof_predictions`, `load_oof_predictions`, `MatrixProgressCallback`, `NullProgressCallback`.

---

## 9. `experimental_ml.statistics` (Etapa 5 — Consolidação e Estatística)

- **Entrada e Consolidação (5A):** `validate_stage5_entry`, `consolidate_descriptive`, `DescriptiveConsolidation`, `ConfigurationSummary`, `CoverageStatus`, `AggregatedMetricStats`, `AggregatedTimingStats`.
- **Adequação e Inferência (5B):** `evaluate_method_suitability`, `MethodSuitabilityReport`, `ApplicableMethod`, `ApplicabilityStatus`, `paired_nadeau_bengio_test`, `NadeauBengioResult`, `paired_wilcoxon_test`, `WilcoxonResult`, `compute_paired_cohens_d`, `EffectSizeResult`, `adjust_pvalues_holm`, `adjust_pvalues_bh`, `run_statistical_comparisons`, `ComparisonSpec`, `StatisticalComparisonBundle`.
- **Multiobjetivo e Síntese (5C):** `compute_pareto_frontier`, `MultiObjectiveSpec`, `ObjectiveSpec`, `ObjectiveSource`, `MultiObjectiveSummary`, `score_candidate_acquisition`, `synthesize_conclusions`, `StructuredConclusion`.

---

## 10. `experimental_ml.reporting` (Etapa 6 — Relatórios e Reprodutibilidade)

- **Acesso Somente-Leitura:** `load_experiment_artifacts_readonly`, `select_report_content`, `LoadedExperimentData`, `ReportContentSelection`, `ReportAudience`, `ReportFamily`, `ResearcherDeclarations`.
- **Tabelas e Figuras:** `build_table_model`, `render_table_csv`, `render_table_markdown`, `render_table_latex`, `TableModel`, `build_figure_spec`, `render_figure`, `PlotSpecification`, `PlotType`, `render_full_report`.
- **Empacotamento:** `build_reproducibility_package`, `PackageMode` (`FULL_PACKAGE`, `REDUCED_NO_RAW_DATA`), `ReproducibilityPackageManifest`, `ArtifactProvenance`.

---

## 11. `experimental_ml.stages` (Portões de Estágio)

- **Verificadores de Portão (*Stage Gates*):**
  - `verify_preparation_gate` (Etapa 1)
  - `verify_scenarios_gate` (Etapa 2)
  - `verify_models_gate` (Etapa 3)
  - `verify_partition_gate` (Etapa 4A)
  - `verify_runs_gate` (Etapa 4B)
  - `verify_statistics_gate` (Etapa 5)
  - `verify_report_gate` (Etapa 6)
- **Utilitários:** `reconstruct_sanitized_view` e constantes canônicas de caminhos relativos (`*_REL_PATH`).
