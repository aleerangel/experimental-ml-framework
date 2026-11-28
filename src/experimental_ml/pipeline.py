"""Fachada de alto nível para condução integrada de experimentos (USAB-02).

Permite executar as Etapas 1 a 6 a partir de entradas simples de ML (CSV, alvo,
dicionário de estimadores) ou especificações formais completas (`ModelSpec`,
`DatasetSchemaSpec`, `FeatureScenario`, `PartitionConfig`), preservando todos
os portões anti-vazamento, determinismo e pureza `XCUT-02`.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from experimental_ml.core.enums import MetricDirection, TaskType
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.data import (
    CsvFormatSpec,
    DatasetSchemaSpec,
    PreparationRule,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features import FeatureScenario, ScenarioMode, validate_scenarios
from experimental_ml.metrics.catalog import get_metric_spec
from experimental_ml.models import (
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    validate_model_spec,
)
from experimental_ml.orchestration import load_cell_artifacts, run_experiment_matrix
from experimental_ml.reporting import (
    ReportAudience,
    ReportContentSelection,
    ReportFamily,
    build_figure_spec,
    load_experiment_artifacts_readonly,
    render_figure,
    render_full_report,
    select_report_content,
)
from experimental_ml.stages.stage_gates import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    MODELS_CATALOG_REL_PATH,
    PARTITION_PLAN_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    SCENARIOS_CATALOG_REL_PATH,
)
from experimental_ml.statistics import (
    ComparisonScope,
    ComparisonSpec,
    DescriptiveConsolidation,
    MultiObjectiveSpec,
    ObjectiveSource,
    ObjectiveSpec,
    StructuredConclusion,
    compute_pareto_frontier,
    consolidate_descriptive,
    evaluate_method_suitability,
    run_statistical_comparisons,
    save_statistics_artifacts,
    synthesize_conclusions,
)
from experimental_ml.validation import (
    EvaluationRegime,
    PartitionConfig,
    PartitionStrategy,
    build_partition_plan,
)


@dataclass(frozen=True, slots=True)
class ExperimentRunSummary:
    """Resumo imutável de um experimento completo executado via `run_experiment`."""

    experiment_dir: Path
    dataset_hash: str
    partition_plan_id: str
    completed_cells: int
    failed_cells: int
    observed_leader: tuple[str, str] | None
    statistical_evidence_status: str
    report_md_path: Path
    report_html_path: Path
    consolidation: DescriptiveConsolidation
    conclusion: StructuredConclusion

    def summary(self) -> str:
        """Retorna resumo legível em português com métricas, conclusão e caminhos."""
        lines = [
            "=== Resumo do Experimento ===",
            f"Diretório: {self.experiment_dir}",
            f"Células concluídas: {self.completed_cells} (falhas: {self.failed_cells})",
            f"Líder observado ({self.conclusion.primary_metric}): {self.observed_leader}",
            f"Status estatístico: {self.statistical_evidence_status}",
            "",
            "Desempenho por configuração:",
        ]
        for cfg_id, cfg_sum in self.consolidation.configurations.items():
            metrics_str = ", ".join(
                f"{m}={st.mean:.4f}±{st.std:.4f}"
                for m, st in cfg_sum.aggregated_metrics.items()
                if st.mean is not None
            )
            lines.append(f"  - {cfg_id}: [{cfg_sum.coverage_status.value}] {metrics_str}")
        lines.extend(
            [
                "",
                f"Conclusão: {self.conclusion.narrative_text}",
                f"Relatório Markdown: {self.report_md_path}",
                f"Relatório HTML: {self.report_html_path}",
            ]
        )
        return "\n".join(lines)


def _slugify_id(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip().lower()).strip("_")
    return slug or "modelo"


def _coerce_model_specs(
    models: Mapping[str, Any] | Sequence[ModelSpec],
    task_type: TaskType,
) -> list[ModelSpec]:
    is_clf = task_type in {TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION}
    if isinstance(models, Mapping):
        if not models:
            raise ConfigurationError("Provide at least one model in 'models'.")
        specs: list[ModelSpec] = []
        for display_name, item in models.items():
            if isinstance(item, ModelSpec):
                specs.append(validate_model_spec(item))
                continue
            model_id = _slugify_id(display_name)
            if isinstance(item, type):
                def _make_cls_factory(_cls: type) -> Any:
                    def _factory(seed: int | None = None) -> Any:
                        return _cls()
                    _factory._factory_ref = f"{_cls.__module__}:{_cls.__qualname__}"  # type: ignore[attr-defined]
                    return _factory
                factory = _make_cls_factory(item)
                has_fit = hasattr(item, "fit")
                has_proba = is_clf and hasattr(item, "predict_proba")
            elif callable(item) and not hasattr(item, "predict"):
                factory = item
                has_fit = True
                has_proba = False
            elif hasattr(item, "predict"):
                def _make_inst_factory(_inst: Any, _mid: str) -> Any:
                    def _factory(seed: int | None = None) -> Any:
                        cloned = copy.deepcopy(_inst)
                        if seed is not None and hasattr(cloned, "random_state") and getattr(cloned, "random_state") is None:
                            try:
                                cloned.random_state = seed
                            except Exception:
                                if hasattr(cloned, "set_params"):
                                    cloned.set_params(random_state=seed)
                        return cloned
                    cls = type(_inst)
                    mod = getattr(cls, "__module__", "")
                    qn = getattr(cls, "__qualname__", "")
                    if mod and qn and mod != "__main__" and "<locals>" not in qn:
                        _factory._factory_ref = f"{mod}:{qn}"  # type: ignore[attr-defined]
                    else:
                        _factory._factory_ref = f"inline:{_mid}"  # type: ignore[attr-defined]
                    return _factory
                factory = _make_inst_factory(item, model_id)
                has_fit = hasattr(item, "fit")
                has_proba = is_clf and hasattr(item, "predict_proba")
            else:
                raise ConfigurationError(
                    f"Unsupported model entry '{display_name}': pass a ModelSpec, estimator instance, class, or factory."
                )
            specs.append(
                validate_model_spec(
                    ModelSpec(
                        model_id=model_id,
                        display_name=str(display_name),
                        family=ModelFamily.CUSTOM,
                        estimator_factory=factory,
                        capabilities=ModelCapabilities(
                            requires_fit=has_fit,
                            supports_predict_proba=has_proba,
                        ),
                        description=f"Modelo '{display_name}' registrado via fachada run_experiment",
                        scientific_justification="Comparação experimental controlada",
                    )
                )
            )
        return specs

    specs = [validate_model_spec(m) for m in models]
    if not specs:
        raise ConfigurationError("Provide at least one ModelSpec in 'models'.")
    return specs


def run_experiment(
    data: Any,
    models: Mapping[str, Any] | Sequence[ModelSpec],
    output_dir: Path | str,
    *,
    target: str | None = None,
    task: str | TaskType | None = None,
    schema: DatasetSchemaSpec | None = None,
    scenarios: Sequence[FeatureScenario] | None = None,
    partition_config: PartitionConfig | None = None,
    cv_folds: int = 5,
    group_col: str | None = None,
    metrics: Sequence[str] | None = None,
    rules: Sequence[PreparationRule] = (),
    alpha: float = 0.05,
    master_seed: int = 42,
    force: bool = True,
    delimiter: str | None = None,
    decimal: str | None = ".",
    encoding: str = "utf-8-sig",
    has_header: bool = True,
    column_names: Sequence[str] | None = None,
    quotechar: str = '"',
    csv_format: CsvFormatSpec | None = None,
    collect_train_metrics: bool = False,
    check_ks_drift: bool = False,
    analyze_oof_residuals: bool = False,
    extended_stats: bool = False,
    export_meta_features: bool = False,
    comparison_scope: ComparisonScope = ComparisonScope.ALL_PAIRWISE,
    planned_pairs: Sequence[tuple[tuple[str, str], tuple[str, str]]] = (),
    pareto_objectives: Sequence[ObjectiveSpec] | None = None,
) -> ExperimentRunSummary:
    """Executa ponta a ponta as Etapas 1 a 6 de forma segura e reproduzível.

    Aceita tanto entradas simples (`data="dados.csv"`, `target="alvo"`,
    `task="regression"`, `models={"A": reg_a, "B": reg_b}`) quanto contratos
    formais completos (`schema`, `ModelSpec`, `FeatureScenario`, `PartitionConfig`).
    """
    exp_dir = Path(output_dir).resolve()
    exp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Resolver esquema e carregar dados (Etapa 1)
    if schema is None:
        if not target or not task:
            raise ConfigurationError(
                "Provide either 'schema=DatasetSchemaSpec(...)' or both 'target' and 'task'."
            )
        task_enum = task if isinstance(task, TaskType) else TaskType(str(task).upper())
        resolved_schema = DatasetSchemaSpec(
            target_col=target,
            task_type=task_enum,
            group_col=group_col,
        )
    else:
        resolved_schema = schema

    bundle = load_dataset(
        data,
        resolved_schema,
        delimiter=delimiter,
        decimal=decimal,
        encoding=encoding,
        has_header=has_header,
        column_names=column_names,
        quotechar=quotechar,
        csv_format=csv_format,
    )
    use_extended = bool(extended_stats or export_meta_features)
    profile = profile_dataset(bundle, extended_stats=use_extended)
    prep_plan = create_preparation_plan(profile, list(rules))
    if prep_plan.status != "READY":
        issues = "; ".join(f"{u.finding_code} ({u.column or 'dataset'})" for u in prep_plan.unresolved_findings)
        raise ConfigurationError(f"Dataset has unresolved confirmed issues: {issues}")
    view = sanitize_dataset(bundle, profile, prep_plan)

    # 2. Cenários de features (Etapa 2)
    if scenarios is None:
        feature_cols = tuple(view.candidate_feature_cols)
        raw_scenarios = [
            FeatureScenario(
                scenario_id="todas_features",
                name="Todas as Features",
                description="Conjunto completo de variáveis preditoras",
                scientific_justification="Cenário padrão explícito sem seleção",
                mode=ScenarioMode.FIXED,
                selected_features=feature_cols,
            )
        ]
    else:
        raw_scenarios = list(scenarios)
    scenarios_cat = validate_scenarios(raw_scenarios, view)

    # 3. Modelos (Etapa 3)
    model_specs = _coerce_model_specs(models, resolved_schema.task_type)

    # 4. Particionamento (4A) e Execução Matricial (4B)
    if partition_config is None:
        if resolved_schema.group_col:
            strategy = PartitionStrategy.GROUP_KFOLD
        elif resolved_schema.task_type in {TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION}:
            strategy = PartitionStrategy.STRATIFIED_KFOLD
        else:
            strategy = PartitionStrategy.KFOLD
        resolved_part_cfg = PartitionConfig(
            strategy=strategy,
            regime=EvaluationRegime.CV_ONLY,
            n_splits=cv_folds,
            group_col=resolved_schema.group_col,
            master_seed=master_seed,
        )
    else:
        resolved_part_cfg = partition_config

    part_plan = build_partition_plan(view, resolved_part_cfg)

    if metrics is None:
        selected_metrics = (
            ("rmse", "mae", "r2")
            if resolved_schema.task_type == TaskType.REGRESSION
            else ("accuracy", "balanced_accuracy", "f1")
        )
    else:
        for m_id in metrics:
            get_metric_spec(m_id)
        selected_metrics = tuple(metrics)

    run_dir = exp_dir / "runs"
    run_state = run_experiment_matrix(
        model_specs=model_specs,
        scenarios=scenarios_cat.scenarios,
        partition_plan=part_plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=selected_metrics,
        master_seed=master_seed,
        overwrite=force,
        collect_train_metrics=collect_train_metrics,
    )

    # 5. Estatística (Etapa 5)
    from experimental_ml.orchestration import consolidate_matrix_oof

    oof_target_ids = (
        part_plan.development_ids
        if getattr(part_plan, "regime", None) == EvaluationRegime.CV_AND_HOLDOUT and part_plan.development_ids
        else view.observation_ids
    )
    oof_map = consolidate_matrix_oof(
        run_dir,
        task_type=resolved_schema.task_type,
        target_observation_ids=oof_target_ids,
        overwrite=force,
    )
    oof_records = list(oof_map.values())
    cells = [load_cell_artifacts(cid, run_dir)[0] for cid in run_state.cell_statuses]

    n_total_candidates_per_config = {
        (str(m.model_id), str(s.scenario_id)): len(view.candidate_feature_cols)
        for m in model_specs
        for s in scenarios_cat.scenarios
    }
    cons = consolidate_descriptive(
        cells,
        total_folds_per_config=len(part_plan.folds),
        n_total_candidates_per_config=n_total_candidates_per_config,
        oof_predictions=oof_records or None,
        experiment_id=run_state.experiment_id,
        partition_plan_id=part_plan.plan_id,
    )
    suit = evaluate_method_suitability(part_plan, cons)
    metric_dirs = {m_id: get_metric_spec(m_id).direction for m_id in selected_metrics}
    primary_metric = selected_metrics[0]
    comp = run_statistical_comparisons(
        cons,
        part_plan,
        ComparisonSpec(
            metrics_of_interest=selected_metrics,
            metric_directions=metric_dirs,
            comparison_scope=comparison_scope,
            planned_pairs=tuple(planned_pairs),
            alpha=alpha,
        ),
        suit,
    )
    resolved_pareto_objs = (
        tuple(pareto_objectives)
        if pareto_objectives
        else (
            ObjectiveSpec(primary_metric, metric_dirs[primary_metric]),
            ObjectiveSpec("fit_mean_s", MetricDirection.MINIMIZE, ObjectiveSource.TIMING_MEAN, "fit_mean_s"),
        )
    )
    pareto = compute_pareto_frontier(
        cons,
        MultiObjectiveSpec(objectives=resolved_pareto_objs),
    )
    conc = synthesize_conclusions(
        cons,
        suit,
        comp,
        primary_metric=primary_metric,
        primary_direction=metric_dirs[primary_metric],
        multi_objective_summary=pareto,
    )

    # Persistir artefatos canônicos completos para interoperabilidade com CLI (M8-05)
    from experimental_ml.data.codecs import (
        dataset_descriptor_to_dict,
        dataset_profile_to_dict,
        preparation_plan_to_dict,
        sanitized_view_descriptor_to_dict,
    )
    from experimental_ml.data.descriptors import DatasetDescriptor, SanitizedViewDescriptor
    from experimental_ml.features.exploration import explore_features
    from experimental_ml.features.visualization import render_exploratory_report
    from experimental_ml.models.catalog import models_catalog_to_dict, ModelsCatalog
    from experimental_ml.features.scenarios import save_scenarios
    from experimental_ml.stages.stage_gates import (
        EXPLORATORY_FEATURES_REL_PATH,
        SANITIZED_VIEW_REL_PATH,
        SPLITS_CSV_GZ_REL_PATH,
        SPLITS_SCHEMA_REL_PATH,
    )
    from experimental_ml.validation.codecs import partition_plan_to_dict
    from experimental_ml.validation.storage import write_splits_csv_gz, write_splits_schema

    schema_file = exp_dir / "configuration" / "schema.json"
    schema_payload = {
        "target_col": resolved_schema.target_col,
        "task_type": resolved_schema.task_type.value,
        "observation_id_col": resolved_schema.observation_id_col,
        "group_col": resolved_schema.group_col,
        "time_col": resolved_schema.time_col,
        "column_semantic_types": {k: v.value for k, v in resolved_schema.column_semantic_types.items()},
    }
    write_json_atomic(schema_file, schema_payload, overwrite=force)
    schema_out_path = str(schema_file)

    if isinstance(data, (str, Path)):
        raw_source_out_path = str(Path(data).resolve())
        effective_csv_format = csv_format or CsvFormatSpec(
            delimiter=delimiter,
            decimal=decimal or ".",
            encoding=encoding,
            has_header=has_header,
            column_names=tuple(column_names) if column_names is not None else None,
            quotechar=quotechar,
        )
    else:
        import csv as _csv

        snapshot_csv = exp_dir / "data" / "source_snapshot.csv"
        snapshot_csv.parent.mkdir(parents=True, exist_ok=True)
        col_names = list(bundle.columns.keys())
        include_obs_col = (
            resolved_schema.observation_id_col is not None
            and resolved_schema.observation_id_col not in bundle.columns
        )
        headers = ([resolved_schema.observation_id_col] if include_obs_col else []) + col_names
        with snapshot_csv.open("w", encoding="utf-8", newline="") as fh:
            writer = _csv.writer(fh)
            writer.writerow(headers)
            for idx in range(len(bundle.observation_ids)):
                row_vals = ([str(bundle.observation_ids[idx])] if include_obs_col else []) + [
                    bundle.columns[c][idx].item() if hasattr(bundle.columns[c][idx], "item") else bundle.columns[c][idx]
                    for c in col_names
                ]
                writer.writerow(row_vals)
        raw_source_out_path = str(snapshot_csv)
        effective_csv_format = CsvFormatSpec(delimiter=",", decimal=".", encoding="utf-8")

    desc_obj = DatasetDescriptor(
        dataset_hash=bundle.dataset_hash,
        raw_source_hash=getattr(bundle, "raw_source_hash", None),
        raw_source_path=raw_source_out_path,
        n_observations=len(bundle.observation_ids),
        n_columns=len(bundle.columns),
        column_names=tuple(bundle.columns.keys()),
        column_types={col: str(bundle.columns[col].dtype) for col in bundle.columns},
        target_col=resolved_schema.target_col,
        task_type=resolved_schema.task_type.value,
        group_col=resolved_schema.group_col,
        time_col=resolved_schema.time_col,
        schema_path=schema_out_path,
        csv_format=effective_csv_format,
    )
    view_desc = SanitizedViewDescriptor(
        dataset_hash=view.dataset_hash,
        source_dataset_hash=view.source_dataset_hash,
        source_plan_digest=view.source_plan_digest,
        n_observations=len(view.observation_ids),
        candidate_feature_cols=tuple(view.candidate_feature_cols),
        dropped_observation_ids=tuple(view.dropped_observation_ids),
        target_label_mapping=view.target_label_mapping,
        deferred_rules=tuple(view.deferred_rules),
    )

    write_json_atomic(exp_dir / DATASET_PROFILE_REL_PATH, dataset_profile_to_dict(profile), overwrite=force)
    write_json_atomic(exp_dir / PREPARATION_PLAN_REL_PATH, preparation_plan_to_dict(prep_plan), overwrite=force)
    write_json_atomic(exp_dir / DATASET_DESCRIPTOR_REL_PATH, dataset_descriptor_to_dict(desc_obj), overwrite=force)
    write_json_atomic(exp_dir / SANITIZED_VIEW_REL_PATH, sanitized_view_descriptor_to_dict(view_desc), overwrite=force)
    save_scenarios(scenarios_cat, exp_dir / SCENARIOS_CATALOG_REL_PATH, overwrite=force)
    all_importable = all(
        not getattr(m.estimator_factory, "_factory_ref", "").startswith(("inline:", "__main__:"))
        for m in model_specs
    )
    if all_importable:
        write_json_atomic(
            exp_dir / MODELS_CATALOG_REL_PATH,
            models_catalog_to_dict(ModelsCatalog(models=tuple(model_specs))),
            overwrite=force,
        )
    write_json_atomic(exp_dir / PARTITION_PLAN_REL_PATH, partition_plan_to_dict(part_plan), overwrite=force)
    write_splits_csv_gz(exp_dir / SPLITS_CSV_GZ_REL_PATH, part_plan, overwrite=force)
    write_splits_schema(exp_dir / SPLITS_SCHEMA_REL_PATH, part_plan, overwrite=force)

    from experimental_ml.features.exploration import build_dataset_meta_features, explore_features
    exp_report = explore_features(view, extended_stats=use_extended)
    write_json_atomic(exp_dir / EXPLORATORY_FEATURES_REL_PATH, exp_report.to_dict(), overwrite=force)
    if export_meta_features:
        meta_features = build_dataset_meta_features(profile, exp_report)
        write_json_atomic(exp_dir / "dataset_meta_features.json", meta_features, overwrite=force)
    reports_dir = exp_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    from experimental_ml.features.visualization import (
        render_exploratory_redundancy_heatmap,
        render_exploratory_target_chart,
    )

    (reports_dir / "exploratory_target.png").write_bytes(render_exploratory_target_chart(exp_report, fmt="png"))
    (reports_dir / "exploratory_redundancy.png").write_bytes(render_exploratory_redundancy_heatmap(exp_report, fmt="png"))
    exp_fig_paths = ("exploratory_target.png", "exploratory_redundancy.png")
    (reports_dir / "exploratory_features.md").write_text(
        render_exploratory_report(exp_report, fmt="markdown", figure_paths=exp_fig_paths),
        encoding="utf-8",
    )
    (reports_dir / "exploratory_features.html").write_text(
        render_exploratory_report(exp_report, fmt="html", figure_paths=exp_fig_paths),
        encoding="utf-8",
    )

    save_statistics_artifacts(exp_dir / "statistics", cons, suit, comp, conc, pareto=pareto, force=force)

    if check_ks_drift:
        from experimental_ml.statistics.distributions_diagnostics import (
            compute_partition_ks_drift,
            partition_drift_to_dict,
        )

        drift_rep = compute_partition_ks_drift(view, part_plan, alpha=alpha)
        write_json_atomic(exp_dir / "statistics" / "ks_drift_report.json", partition_drift_to_dict(drift_rep), overwrite=force)

    if analyze_oof_residuals and resolved_schema.task_type == TaskType.REGRESSION and oof_map:
        from experimental_ml.statistics.distributions_diagnostics import (
            analyze_oof_residuals_map,
            oof_residuals_to_dict,
        )

        res_entries = analyze_oof_residuals_map(oof_map)
        if res_entries:
            oof_samples = {}
            for key, oof_rec in oof_map.items():
                m_id = str(getattr(oof_rec, "model_id", key[0] if isinstance(key, tuple) else key))
                sc_id = str(getattr(oof_rec, "scenario_id", key[1] if isinstance(key, tuple) else ""))
                yp_seq = oof_rec.y_pred_mean if hasattr(oof_rec, "y_pred_mean") else oof_rec.y_pred
                yp_list = [float(v) for v in yp_seq]
                if getattr(oof_rec, "residuals", None) is not None:
                    res_list = [float(v) for v in oof_rec.residuals]
                else:
                    res_list = [float(yt - yp) for yt, yp in zip(oof_rec.y_true, yp_list)]
                oof_samples[(m_id, sc_id)] = (yp_list, res_list)
            write_json_atomic(
                exp_dir / "statistics" / "oof_residuals_diagnostics.json",
                oof_residuals_to_dict(res_entries, oof_samples=oof_samples),
                overwrite=force,
            )

    # 6. Relatórios e Figuras (Etapa 6)
    loaded = load_experiment_artifacts_readonly(exp_dir)
    sel = select_report_content(loaded, ReportContentSelection(audience=ReportAudience.FULL_LAB))
    figures_dir = reports_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    fig_rel_paths: list[str] = []
    for fam in (
        ReportFamily.D_PREDICTIVE_PERFORMANCE,
        ReportFamily.E_STATISTICAL_COMPARISONS,
        ReportFamily.F_STABILITY_COST_PARETO,
        ReportFamily.G_MODEL_SPECIFIC_ARTIFACTS,
    ):
        if fam in sel.families:
            fig_spec = build_figure_spec(fam, loaded, sel)
            fig_file = figures_dir / f"{fig_spec.plot_id}.png"
            fig_file.write_bytes(render_figure(fig_spec, "png"))
            fig_rel_paths.append(f"figures/{fig_file.name}")

    if loaded.oof_residuals_diagnostics and any(
        c.get("residuals") and c.get("y_pred")
        for c in loaded.oof_residuals_diagnostics.get("configurations", ())
    ):
        from experimental_ml.reporting.figures import render_residuals_diagnostic_figure

        qq_file = figures_dir / "fig_oof_residuals_qq.png"
        qq_file.write_bytes(render_residuals_diagnostic_figure(dict(loaded.oof_residuals_diagnostics), "png"))
        fig_rel_paths.append(f"figures/{qq_file.name}")

    md_path = reports_dir / "report.md"
    html_path = reports_dir / "report.html"
    md_path.write_text(
        render_full_report(loaded, fmt="markdown", selection=sel, figure_paths=tuple(fig_rel_paths)),
        encoding="utf-8",
    )
    html_path.write_text(
        render_full_report(loaded, fmt="html", selection=sel, figure_paths=tuple(fig_rel_paths)),
        encoding="utf-8",
    )

    return ExperimentRunSummary(
        experiment_dir=exp_dir,
        dataset_hash=view.dataset_hash,
        partition_plan_id=part_plan.plan_id,
        completed_cells=run_state.completed_cells,
        failed_cells=run_state.failed_cells,
        observed_leader=conc.observed_leader,
        statistical_evidence_status=conc.statistical_evidence_status,
        report_md_path=md_path,
        report_html_path=html_path,
        consolidation=cons,
        conclusion=conc,
    )
