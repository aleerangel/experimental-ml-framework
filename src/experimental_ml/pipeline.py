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
    load_experiment_artifacts_readonly,
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
    StructuredConclusion,
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
                        return copy.deepcopy(_inst)
                    cls = type(_inst)
                    mod = getattr(cls, "__module__", "")
                    qn = getattr(cls, "__qualname__", "")
                    _factory._factory_ref = f"{mod}:{qn}" if mod and qn and "<locals>" not in qn else f"inline:{_mid}"  # type: ignore[attr-defined]
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

    bundle = load_dataset(data, resolved_schema)
    profile = profile_dataset(bundle)
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
    )

    # 5. Estatística (Etapa 5)
    cells = [load_cell_artifacts(cid, run_dir)[0] for cid in run_state.cell_statuses]
    cons = consolidate_descriptive(
        cells,
        total_folds_per_config=len(part_plan.folds),
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
            comparison_scope=ComparisonScope.ALL_PAIRWISE,
            alpha=alpha,
        ),
        suit,
    )
    conc = synthesize_conclusions(
        cons,
        suit,
        comp,
        primary_metric=primary_metric,
        primary_direction=metric_dirs[primary_metric],
    )

    # Persistir metadados mínimos esperados por load_experiment_artifacts_readonly
    from experimental_ml.data.codecs import dataset_profile_to_dict, preparation_plan_to_dict
    from experimental_ml.models.catalog import models_catalog_to_dict, ModelsCatalog
    from experimental_ml.features.scenarios import save_scenarios
    from experimental_ml.validation.codecs import partition_plan_to_dict

    write_json_atomic(exp_dir / DATASET_PROFILE_REL_PATH, dataset_profile_to_dict(profile), overwrite=force)
    write_json_atomic(exp_dir / PREPARATION_PLAN_REL_PATH, preparation_plan_to_dict(prep_plan), overwrite=force)
    write_json_atomic(exp_dir / DATASET_DESCRIPTOR_REL_PATH, {"dataset_hash": bundle.dataset_hash}, overwrite=force)
    save_scenarios(scenarios_cat, exp_dir / SCENARIOS_CATALOG_REL_PATH, overwrite=force)
    write_json_atomic(
        exp_dir / MODELS_CATALOG_REL_PATH,
        models_catalog_to_dict(ModelsCatalog(models=tuple(model_specs))),
        overwrite=force,
    )
    write_json_atomic(exp_dir / PARTITION_PLAN_REL_PATH, partition_plan_to_dict(part_plan), overwrite=force)
    save_statistics_artifacts(exp_dir / "statistics", cons, suit, comp, conc, force=force)

    # 6. Relatórios (Etapa 6)
    loaded = load_experiment_artifacts_readonly(exp_dir)
    sel = select_report_content(loaded, ReportContentSelection(audience=ReportAudience.FULL_LAB))
    reports_dir = exp_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    md_path = reports_dir / "report.md"
    html_path = reports_dir / "report.html"
    md_path.write_text(render_full_report(loaded, fmt="markdown", selection=sel), encoding="utf-8")
    html_path.write_text(render_full_report(loaded, fmt="html", selection=sel), encoding="utf-8")

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
