"""Unit tests for statistics types, enumerations, and frozen dataclasses (STAT-01)."""

from dataclasses import FrozenInstanceError
from types import MappingProxyType
import pytest

from experimental_ml.core.enums import MetricDirection, MetricStatus
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue
from experimental_ml.features.stability import SelectionStabilityReport
from experimental_ml.validation.types import EvaluationRegime
from experimental_ml.statistics.types import (
    ApplicabilityStatus,
    ApplicableMethod,
    AggregatedMetricStats,
    AggregatedTimingStats,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    IncompleteComparisonPolicy,
    MethodSuitabilityReport,
)


def test_coverage_status_enum() -> None:
    """C1: CoverageStatus enum has VALID, PARTIAL_COVERAGE, and NO_COVERAGE (STAT-01, AC-M61-01-01)."""
    assert CoverageStatus.VALID == "VALID"
    assert CoverageStatus.PARTIAL_COVERAGE == "PARTIAL_COVERAGE"
    assert CoverageStatus.NO_COVERAGE == "NO_COVERAGE"
    assert len(CoverageStatus) == 3


def test_incomplete_comparison_policy_enum() -> None:
    """C2: IncompleteComparisonPolicy enum has STRICT_COMPLETE_ONLY and ALLOW_COMMON_SUBSET (STAT-01, AC-M61-01-02)."""
    assert IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY == "STRICT_COMPLETE_ONLY"
    assert IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET == "ALLOW_COMMON_SUBSET"
    assert len(IncompleteComparisonPolicy) == 2


def test_applicability_status_enum() -> None:
    """ApplicabilityStatus enum contains expected members."""
    assert ApplicabilityStatus.APPLICABLE == "APPLICABLE"
    assert ApplicabilityStatus.CONDITIONALLY_APPLICABLE == "CONDITIONALLY_APPLICABLE"
    assert ApplicabilityStatus.NOT_SUITABLE == "NOT_SUITABLE"
    assert ApplicabilityStatus.NOT_APPLICABLE == "NOT_APPLICABLE"
    assert len(ApplicabilityStatus) == 4


def test_aggregated_metric_stats_fields() -> None:
    """C3: AggregatedMetricStats contains n_valid, n_total, status, and nullable float summary fields (STAT-01, AC-M61-01-03)."""
    stats_full = AggregatedMetricStats(
        n_valid=5,
        n_total=5,
        status=MetricStatus.VALID,
        mean=0.25,
        std=0.05,
        median=0.24,
        iqr=0.03,
        q25=0.23,
        q75=0.26,
        min_value=0.20,
        max_value=0.31,
    )
    assert stats_full.n_valid == 5
    assert stats_full.n_total == 5
    assert stats_full.status == MetricStatus.VALID
    assert stats_full.mean == 0.25
    assert stats_full.std == 0.05
    assert stats_full.median == 0.24
    assert stats_full.iqr == 0.03
    assert stats_full.q25 == 0.23
    assert stats_full.q75 == 0.26
    assert stats_full.min_value == 0.20
    assert stats_full.max_value == 0.31

    # Case with n_valid == 0 (all None)
    stats_empty = AggregatedMetricStats(
        n_valid=0,
        n_total=5,
        status=MetricStatus.UNDEFINED_NAN,
        mean=None,
        std=None,
        median=None,
        iqr=None,
        q25=None,
        q75=None,
        min_value=None,
        max_value=None,
    )
    assert stats_empty.n_valid == 0
    assert stats_empty.status == MetricStatus.UNDEFINED_NAN
    assert stats_empty.mean is None
    assert stats_empty.std is None


def test_aggregated_timing_stats_fields() -> None:
    """C4: AggregatedTimingStats contains mean and total durations in seconds for all cell sub-phases (STAT-01, AC-M61-01-04)."""
    timing = AggregatedTimingStats(
        data_extraction_mean_s=0.01,
        data_extraction_total_s=0.05,
        preprocessing_mean_s=0.02,
        preprocessing_total_s=0.10,
        feature_selection_mean_s=0.03,
        feature_selection_total_s=0.15,
        tuning_mean_s=0.04,
        tuning_total_s=0.20,
        fit_mean_s=0.10,
        fit_total_s=0.50,
        predict_mean_s=0.02,
        predict_total_s=0.10,
        evaluation_mean_s=0.01,
        evaluation_total_s=0.05,
        total_cell_mean_s=0.23,
        total_cell_sum_s=1.15,
    )
    assert timing.data_extraction_mean_s == 0.01
    assert timing.fit_total_s == 0.50
    assert timing.total_cell_sum_s == 1.15


def test_configuration_summary_fields() -> None:
    """C5: ConfigurationSummary contains model_id, scenario_id, fold counters, coverage status, fold id tuples, and metric/timing summaries (STAT-01, AC-M61-01-05)."""
    mv = MetricValue(
        metric_id="rmse",
        value=0.25,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=20,
    )
    agg_stat = AggregatedMetricStats(
        n_valid=3,
        n_total=5,
        status=MetricStatus.PARTIAL_COVERAGE,
        mean=0.25,
        std=0.02,
        median=0.25,
        iqr=0.01,
        q25=0.24,
        q75=0.25,
        min_value=0.23,
        max_value=0.27,
    )
    timing = AggregatedTimingStats(
        data_extraction_mean_s=0.01,
        data_extraction_total_s=0.03,
        preprocessing_mean_s=0.02,
        preprocessing_total_s=0.06,
        feature_selection_mean_s=0.0,
        feature_selection_total_s=0.0,
        tuning_mean_s=0.0,
        tuning_total_s=0.0,
        fit_mean_s=0.1,
        fit_total_s=0.3,
        predict_mean_s=0.01,
        predict_total_s=0.03,
        evaluation_mean_s=0.01,
        evaluation_total_s=0.03,
        total_cell_mean_s=0.15,
        total_cell_sum_s=0.45,
    )
    summary = ConfigurationSummary(
        model_id="ridge",
        scenario_id="sc1",
        total_folds=5,
        completed_folds=3,
        failed_folds=1,
        cancelled_folds=1,
        coverage=0.6,
        coverage_status=CoverageStatus.PARTIAL_COVERAGE,
        completed_fold_ids=("fold_0", "fold_1", "fold_2"),
        failed_fold_ids=("fold_3",),
        cancelled_fold_ids=("fold_4",),
        fold_metrics={"fold_0": {"rmse": mv}},
        aggregated_metrics={"rmse": agg_stat},
        pooled_oof_metrics={"rmse": mv},
        aggregated_timing=timing,
        feature_stability=None,
    )
    assert summary.model_id == "ridge"
    assert summary.scenario_id == "sc1"
    assert summary.total_folds == 5
    assert summary.completed_folds == 3
    assert summary.failed_folds == 1
    assert summary.cancelled_folds == 1
    assert summary.coverage == 0.6
    assert summary.coverage_status == CoverageStatus.PARTIAL_COVERAGE
    assert summary.completed_fold_ids == ("fold_0", "fold_1", "fold_2")
    assert summary.failed_fold_ids == ("fold_3",)
    assert summary.cancelled_fold_ids == ("fold_4",)
    assert isinstance(summary.fold_metrics, MappingProxyType)
    assert isinstance(summary.aggregated_metrics, MappingProxyType)
    assert isinstance(summary.pooled_oof_metrics, MappingProxyType)


def test_descriptive_consolidation_fields() -> None:
    """C6: DescriptiveConsolidation contains experiment_id, partition_plan_id, total_configurations, configurations mapping, and timestamp (STAT-01, AC-M61-01-06)."""
    cfg_summary = ConfigurationSummary(
        model_id="ridge",
        scenario_id="sc1",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=("fold_0", "fold_1", "fold_2", "fold_3", "fold_4"),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics={},
        aggregated_metrics={},
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    consol = DescriptiveConsolidation(
        experiment_id="exp_01",
        partition_plan_id="plan_01",
        total_configurations=1,
        configurations={("ridge", "sc1"): cfg_summary},
        timestamp_utc="2026-11-16T16:00:00Z",
    )
    assert consol.experiment_id == "exp_01"
    assert consol.partition_plan_id == "plan_01"
    assert consol.total_configurations == 1
    assert ("ridge", "sc1") in consol.configurations
    assert isinstance(consol.configurations, MappingProxyType)
    assert consol.timestamp_utc == "2026-11-16T16:00:00Z"


def test_method_suitability_report_fields() -> None:
    """MethodSuitabilityReport holds evaluation regime, partition count, overlap ratios and applicable methods."""
    method = ApplicableMethod(
        method_name="nadeau_bengio_paired_t",
        status=ApplicabilityStatus.APPLICABLE,
        rationale="Corrects for cross-validation overlap.",
        assumptions_tested=("paired_folds",),
        assumptions_untested=("approximate_normality",),
        warnings=(),
    )
    report = MethodSuitabilityReport(
        evaluation_regime=EvaluationRegime.CV_ONLY,
        total_development_partitions=5,
        fold_ratios=(0.25, 0.25, 0.25, 0.25, 0.25),
        mean_train_overlap_ratio=0.25,
        is_cross_validation=True,
        applicable_methods={"nadeau_bengio_paired_t": method},
        warnings=(),
    )
    assert report.evaluation_regime == EvaluationRegime.CV_ONLY
    assert report.total_development_partitions == 5
    assert report.mean_train_overlap_ratio == 0.25
    assert report.is_cross_validation is True
    assert "nadeau_bengio_paired_t" in report.applicable_methods
    assert isinstance(report.applicable_methods, MappingProxyType)


def test_statistics_dataclasses_frozen_immutability() -> None:
    """C7: Modifying any attribute of statistics dataclasses raises FrozenInstanceError (STAT-01, AC-M61-01-07)."""
    stats = AggregatedMetricStats(
        n_valid=1,
        n_total=1,
        status=MetricStatus.VALID,
        mean=1.0,
        std=None,
        median=1.0,
        iqr=0.0,
        q25=1.0,
        q75=1.0,
        min_value=1.0,
        max_value=1.0,
    )
    with pytest.raises(FrozenInstanceError):
        stats.mean = 2.0  # type: ignore[misc]

    timing = AggregatedTimingStats(
        data_extraction_mean_s=0.0,
        data_extraction_total_s=0.0,
        preprocessing_mean_s=0.0,
        preprocessing_total_s=0.0,
        feature_selection_mean_s=0.0,
        feature_selection_total_s=0.0,
        tuning_mean_s=0.0,
        tuning_total_s=0.0,
        fit_mean_s=0.0,
        fit_total_s=0.0,
        predict_mean_s=0.0,
        predict_total_s=0.0,
        evaluation_mean_s=0.0,
        evaluation_total_s=0.0,
        total_cell_mean_s=0.0,
        total_cell_sum_s=0.0,
    )
    with pytest.raises(FrozenInstanceError):
        timing.fit_mean_s = 1.0  # type: ignore[misc]

    summary = ConfigurationSummary(
        model_id="ridge",
        scenario_id="sc1",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=("fold_0",),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics={},
        aggregated_metrics={},
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    with pytest.raises(FrozenInstanceError):
        summary.coverage = 0.5  # type: ignore[misc]

    consol = DescriptiveConsolidation(
        experiment_id="exp_01",
        partition_plan_id="plan_01",
        total_configurations=1,
        configurations={},
        timestamp_utc="2026-11-16T16:00:00Z",
    )
    with pytest.raises(FrozenInstanceError):
        consol.total_configurations = 2  # type: ignore[misc]
