"""End-to-end integration tests for M7.2 figures, full report, and runtime purity XCUT-02."""

from pathlib import Path
import subprocess
import sys

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.reporting import (
    ReportFamily,
    ResearcherDeclarations,
    build_figure_spec,
    load_experiment_artifacts_readonly,
    render_figure,
    render_full_report,
)
from experimental_ml.statistics.comparisons import run_statistical_comparisons
from experimental_ml.statistics.multiobjective import compute_pareto_frontier
from experimental_ml.statistics.storage import save_statistics_artifacts
from experimental_ml.statistics.suitability import evaluate_method_suitability
from experimental_ml.statistics.synthesis import synthesize_conclusions
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    ComparisonScope,
    ComparisonSpec,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    MultiObjectiveSpec,
    MultiplicityMethod,
    ObjectiveSpec,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def test_m72_end_to_end_figures_and_report(tmp_path: Path) -> None:
    """C7: End-to-end M7.1 + M7.2 pipeline generating figures (SVG/PNG/PDF) and full reports (MD/HTML)."""
    n_folds = 5
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"tr_{i}_{k}") for k in range(40)),
            val_ids=tuple(ObservationId(f"va_{i}_{k}") for k in range(10)),
        )
        for i in range(n_folds)
    )
    plan = PartitionPlan(
        plan_id="pp_int_m72",
        source_dataset_hash="a" * 64,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=tuple(ObservationId(f"d_{k}") for k in range(50)),
        holdout_ids=(),
        folds=folds,
        config=PartitionConfig(PartitionStrategy.KFOLD, EvaluationRegime.CV_ONLY, n_splits=n_folds),
    )
    sum1 = ConfigurationSummary(
        model_id="m1",
        scenario_id="s1",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(5)),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics={
            f"fold_{i}": {
                "rmse": MetricValue("rmse", 1.0 + 0.01 * i, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10)
            }
            for i in range(5)
        },
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.02, 0.0158, 1.02, 0.02, 1.01, 1.03, 1.00, 1.04)
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    sum2 = ConfigurationSummary(
        model_id="m2",
        scenario_id="s1",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(5)),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics={
            f"fold_{i}": {
                "rmse": MetricValue("rmse", 1.5 + 0.01 * i, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10)
            }
            for i in range(5)
        },
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.52, 0.0158, 1.52, 0.02, 1.51, 1.53, 1.50, 1.54)
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    consol = DescriptiveConsolidation("exp_int_m72", plan.plan_id, 2, {("m1", "s1"): sum1, ("m2", "s1"): sum2}, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(("rmse",), {"rmse": MetricDirection.MINIMIZE}, ComparisonScope.ALL_PAIRWISE, multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI)
    comp = run_statistical_comparisons(consol, plan, spec, suit)
    pareto = compute_pareto_frontier(consol, MultiObjectiveSpec((ObjectiveSpec("rmse", MetricDirection.MINIMIZE),)))
    conc = synthesize_conclusions(consol, suit, comp, "rmse", MetricDirection.MINIMIZE, pareto)
    save_statistics_artifacts(tmp_path / "statistics", consol, suit, comp, conc, pareto=pareto)

    loaded = load_experiment_artifacts_readonly(tmp_path)
    fig_spec = build_figure_spec(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded, metric_name="rmse")
    assert render_figure(fig_spec, "svg").startswith(b"<svg ")
    assert render_figure(fig_spec, "png")[:8] == b"\x89PNG\r\n\x1a\n"
    assert render_figure(fig_spec, "pdf").startswith(b"%PDF-1.4")

    decl = ResearcherDeclarations(scientific_objective="Benchmark generalization.")
    md = render_full_report(loaded, "markdown", declarations=decl, figure_paths=("figures/fig_d.svg",))
    html_doc = render_full_report(loaded, "html", declarations=decl, figure_paths=("figures/fig_d.svg",))
    assert "Benchmark generalization." in md
    assert "<!DOCTYPE html>" in html_doc


def test_m72_runtime_purity_xcut02() -> None:
    """C8: Figure and report rendering run 100% without matplotlib/pillow/scipy."""
    code = (
        "import sys; "
        "sys.modules['matplotlib'] = None; "
        "sys.modules['PIL'] = None; "
        "sys.modules['scipy'] = None; "
        "from experimental_ml.reporting import render_figure, PlotSpecification, PlotSeries, PlotType, ReportFamily, ArtifactProvenance; "
        "prov = ArtifactProvenance('p1', 'figure', ReportFamily.D_PREDICTIVE_PERFORMANCE, 'e1', 'pp1', ('m1',), ('s1',), ('rmse',), ('statistics/descriptive_consolidation.json',), '2026-11-16T00:00:00Z'); "
        "ps = PlotSpecification('p1', ReportFamily.D_PREDICTIVE_PERFORMANCE, PlotType.BAR_COMPARISON, 'T', 'X', 'Y', (PlotSeries('s', ('a',), (1.0,)),), (), prov); "
        "assert render_figure(ps, 'png')[:4] == b'\\x89PNG'"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, f"Purity check failed: {proc.stderr}"
