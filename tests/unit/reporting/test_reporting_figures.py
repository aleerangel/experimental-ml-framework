"""Unit tests for deterministic pure-Python/NumPy figure builders and renderers (REP-04, XCUT-02)."""

from pathlib import Path
import struct
import pytest

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.reporting.figures import build_figure_spec, render_figure
from experimental_ml.reporting.loader import load_experiment_artifacts_readonly
from experimental_ml.reporting.types import ReportFamily
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


def _create_fig_experiment(exp_dir: Path) -> None:
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
        plan_id="pp_fig",
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
    sum_nan = ConfigurationSummary(
        model_id="m_nan",
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
                "rmse": MetricValue("rmse", float("nan"), MetricStatus.UNDEFINED_NAN, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10)
            }
            for i in range(5)
        },
        aggregated_metrics={
            "rmse": AggregatedMetricStats(0, 5, MetricStatus.UNDEFINED_NAN, None, None, None, None, None, None, None, None)
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    consol = DescriptiveConsolidation("exp_fig", plan.plan_id, 2, {("m1", "s1"): sum1, ("m_nan", "s1"): sum_nan}, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(("rmse",), {"rmse": MetricDirection.MINIMIZE}, ComparisonScope.ALL_PAIRWISE, multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI)
    comp = run_statistical_comparisons(consol, plan, spec, suit)
    pareto = compute_pareto_frontier(consol, MultiObjectiveSpec((ObjectiveSpec("rmse", MetricDirection.MINIMIZE),)))
    conc = synthesize_conclusions(consol, suit, comp, "rmse", MetricDirection.MINIMIZE, pareto)
    save_statistics_artifacts(exp_dir / "statistics", consol, suit, comp, conc, pareto=pareto)


def test_m72_01_build_figure_spec_excludes_nan_and_provenance(tmp_path: Path) -> None:
    """C1: build_figure_spec excludes UNDEFINED_NAN points, logs in notes, and uses relative provenance."""
    _create_fig_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(tmp_path)

    plot_d = build_figure_spec(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded, metric_name="rmse")
    assert all(not Path(p).is_absolute() for p in plot_d.provenance.source_relative_paths)
    assert len(plot_d.series) >= 1
    assert plot_d.series[0].x_values == ("m1/s1",)
    assert any("m_nan/s1" in n and "UNDEFINED_NAN" in n for n in plot_d.notes)


def test_m72_01_render_figure_svg_png_300dpi_pdf_deterministic(tmp_path: Path) -> None:
    """C2: render_figure outputs deterministic valid SVG, 300 DPI PNG (pHYs=11811), and PDF 1.4."""
    _create_fig_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(tmp_path)
    plot_d = build_figure_spec(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded, metric_name="rmse")

    # SVG
    svg1 = render_figure(plot_d, "svg")
    svg2 = render_figure(plot_d, "svg")
    assert svg1 == svg2
    svg_str = svg1.decode("utf-8")
    assert svg_str.startswith("<svg ") and "</svg>" in svg_str

    # PNG with 300 DPI pHYs chunk (11811 px/m)
    png1 = render_figure(plot_d, "png")
    png2 = render_figure(plot_d, "png")
    assert png1 == png2
    assert png1[:8] == b"\x89PNG\r\n\x1a\n"
    assert b"pHYs" in png1
    phys_idx = png1.index(b"pHYs")
    ppu_x, ppu_y, unit = struct.unpack(">IIB", png1[phys_idx + 4 : phys_idx + 13])
    assert ppu_x == 11811 and ppu_y == 11811 and unit == 1

    # PDF 1.4
    pdf1 = render_figure(plot_d, "pdf")
    pdf2 = render_figure(plot_d, "pdf")
    assert pdf1 == pdf2
    assert pdf1.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf1


def test_m72_01_unsupported_format_raises(tmp_path: Path) -> None:
    """C3: Unsupported figure format raises ConfigurationError."""
    _create_fig_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(tmp_path)
    plot_d = build_figure_spec(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded, metric_name="rmse")

    with pytest.raises(ConfigurationError):
        render_figure(plot_d, "bmp")
