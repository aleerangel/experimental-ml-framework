"""Unit tests for compute_pareto_frontier (STAT-09, CA-E5-02)."""

import pytest

from experimental_ml.core.enums import MetricStatus
from experimental_ml.metrics.types import MetricDirection
from experimental_ml.statistics.multiobjective import compute_pareto_frontier
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    AggregatedTimingStats,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    MultiObjectiveSpec,
    ObjectiveSource,
    ObjectiveSpec,
)


def _make_cfg(
    model_id: str,
    rmse: float | None,
    fit_mean_s: float,
    coverage_status: CoverageStatus = CoverageStatus.VALID,
    rmse_status: MetricStatus = MetricStatus.VALID,
) -> ConfigurationSummary:
    agg_metrics = {
        "rmse": AggregatedMetricStats(
            n_valid=5 if rmse is not None else 0,
            n_total=5,
            status=rmse_status,
            mean=rmse,
            std=0.05 if rmse is not None else None,
            median=rmse,
            iqr=0.02 if rmse is not None else None,
            q25=rmse,
            q75=rmse,
            min_value=rmse,
            max_value=rmse,
        )
    }
    timing = AggregatedTimingStats(
        data_extraction_mean_s=0.01,
        data_extraction_total_s=0.05,
        preprocessing_mean_s=0.01,
        preprocessing_total_s=0.05,
        feature_selection_mean_s=0.0,
        feature_selection_total_s=0.0,
        tuning_mean_s=0.0,
        tuning_total_s=0.0,
        fit_mean_s=fit_mean_s,
        fit_total_s=fit_mean_s * 5,
        predict_mean_s=0.01,
        predict_total_s=0.05,
        evaluation_mean_s=0.01,
        evaluation_total_s=0.05,
        total_cell_mean_s=fit_mean_s + 0.04,
        total_cell_sum_s=(fit_mean_s + 0.04) * 5,
    )
    return ConfigurationSummary(
        model_id=model_id,
        scenario_id="s1",
        total_folds=5,
        completed_folds=5 if coverage_status == CoverageStatus.VALID else 3,
        failed_folds=0 if coverage_status == CoverageStatus.VALID else 2,
        cancelled_folds=0,
        coverage=1.0 if coverage_status == CoverageStatus.VALID else 0.6,
        coverage_status=coverage_status,
        completed_fold_ids=("f0", "f1", "f2", "f3", "f4") if coverage_status == CoverageStatus.VALID else ("f0", "f1", "f2"),
        failed_fold_ids=() if coverage_status == CoverageStatus.VALID else ("f3", "f4"),
        cancelled_fold_ids=(),
        fold_metrics={},
        aggregated_metrics=agg_metrics,
        pooled_oof_metrics={},
        aggregated_timing=timing,
        feature_stability=None,
    )


def test_m63_01_excludes_partial_and_nan_configs() -> None:
    """C2: Excludes PARTIAL_COVERAGE, NO_COVERAGE, and UNDEFINED_NAN configs from Pareto frontier."""
    configs = {
        ("m_valid", "s1"): _make_cfg("m_valid", rmse=1.0, fit_mean_s=0.5),
        ("m_partial", "s1"): _make_cfg("m_partial", rmse=0.1, fit_mean_s=0.01, coverage_status=CoverageStatus.PARTIAL_COVERAGE),
        ("m_nan", "s1"): _make_cfg("m_nan", rmse=None, fit_mean_s=0.01, rmse_status=MetricStatus.UNDEFINED_NAN),
    }
    consol = DescriptiveConsolidation("exp", "pp", 3, configs, "2026-11-16T00:00:00Z")
    spec = MultiObjectiveSpec(
        objectives=(
            ObjectiveSpec("rmse", MetricDirection.MINIMIZE),
            ObjectiveSpec("fit_mean_s", MetricDirection.MINIMIZE, ObjectiveSource.TIMING_MEAN, "fit_mean_s"),
        )
    )
    summary = compute_pareto_frontier(consol, spec)
    assert [p.config_id for p in summary.pareto_frontier] == [("m_valid", "s1")]
    assert len(summary.excluded_configurations) == 2
    excluded_ids = {e.config_id for e in summary.excluded_configurations}
    assert excluded_ids == {("m_partial", "s1"), ("m_nan", "s1")}


def test_m63_01_exact_pareto_frontier_and_dominance() -> None:
    """C3: Identifies exact non-dominated set and records dominated_by relationships."""
    # Minimizing rmse and fit_mean_s:
    # A (1.0, 1.0) -> Pareto optimal (best rmse)
    # B (1.5, 0.2) -> Pareto optimal (best speed)
    # C (1.2, 0.5) -> Pareto optimal (middle trade-off)
    # D (1.3, 0.6) -> Dominated by C (1.2 < 1.3 and 0.5 < 0.6)
    # E (1.5, 0.5) -> Dominated by C (1.2 < 1.5 and 0.5 <= 0.5) and B (1.5 <= 1.5 and 0.2 < 0.5)
    configs = {
        ("A", "s1"): _make_cfg("A", 1.0, 1.0),
        ("B", "s1"): _make_cfg("B", 1.5, 0.2),
        ("C", "s1"): _make_cfg("C", 1.2, 0.5),
        ("D", "s1"): _make_cfg("D", 1.3, 0.6),
        ("E", "s1"): _make_cfg("E", 1.5, 0.5),
    }
    consol = DescriptiveConsolidation("exp", "pp", 5, configs, "2026-11-16T00:00:00Z")
    spec = MultiObjectiveSpec(
        objectives=(
            ObjectiveSpec("rmse", MetricDirection.MINIMIZE),
            ObjectiveSpec("fit_mean_s", MetricDirection.MINIMIZE, ObjectiveSource.TIMING_MEAN, "fit_mean_s"),
        )
    )
    summary = compute_pareto_frontier(consol, spec)
    frontier_ids = [p.config_id for p in summary.pareto_frontier]
    assert frontier_ids == [("A", "s1"), ("B", "s1"), ("C", "s1")]

    dom_map = {p.config_id: p for p in summary.dominated_configurations}
    assert set(dom_map.keys()) == {("D", "s1"), ("E", "s1")}
    assert ("C", "s1") in dom_map[("D", "s1")].dominated_by
    assert set(dom_map[("E", "s1")].dominated_by) == {("B", "s1"), ("C", "s1")}
