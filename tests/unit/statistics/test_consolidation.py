"""Unit tests for descriptive consolidation engine (STAT-03, CA-E5-01)."""

import numpy as np
import pytest

from experimental_ml.core.enums import ExecutionStatus, MetricDirection, MetricStatus, TaskType
from experimental_ml.core.types import CellId, ExperimentId, PartitionPlanId
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue
from experimental_ml.orchestration.oof import ConsolidatedOofPredictions
from experimental_ml.orchestration.types import CellResultRecord, TimingBreakdown
from experimental_ml.statistics.consolidation import consolidate_descriptive
from experimental_ml.statistics.types import CoverageStatus


def _make_cell(
    model_id: str,
    scenario_id: str,
    fold_id: str,
    status: ExecutionStatus = ExecutionStatus.COMPLETED,
    metrics: dict[str, MetricValue] | None = None,
    timing: TimingBreakdown | None = None,
    selected_features: tuple[str, ...] = ("feat_a", "feat_b"),
) -> CellResultRecord:
    cid = CellId(f"cell_{model_id}_{scenario_id}_{fold_id}")
    return CellResultRecord(
        cell_id=cid,
        experiment_id=ExperimentId("exp_test"),
        partition_plan_id=PartitionPlanId("plan_test"),
        model_id=model_id,
        scenario_id=scenario_id,
        fold_id=fold_id,
        timing=timing or TimingBreakdown(total_cell_time_s=1.0, fit_time_s=0.5),
        status=status,
        selected_features=selected_features,
        metrics=metrics or {},
    )


def _make_metric(val: float, status: MetricStatus = MetricStatus.VALID) -> MetricValue:
    return MetricValue(
        metric_id="rmse",
        value=val,
        status=status,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=20,
    )


def test_consolidate_descriptive_groups_by_configuration() -> None:
    """C12: consolidate_descriptive groups cell results by unique (model_id, scenario_id) configuration (STAT-03, AC-M61-03-01)."""
    cells = [
        _make_cell("ridge", "sc1", "fold_0"),
        _make_cell("ridge", "sc1", "fold_1"),
        _make_cell("lasso", "sc1", "fold_0"),
        _make_cell("lasso", "sc2", "fold_0"),
    ]
    consol = consolidate_descriptive(
        cell_results=cells,
        total_folds_per_config={
            ("ridge", "sc1"): 2,
            ("lasso", "sc1"): 2,
            ("lasso", "sc2"): 2,
        },
        experiment_id="exp_test",
        partition_plan_id="plan_test",
    )
    assert consol.total_configurations == 3
    assert ("ridge", "sc1") in consol.configurations
    assert ("lasso", "sc1") in consol.configurations
    assert ("lasso", "sc2") in consol.configurations


def test_consolidate_descriptive_coverage_status_mapping() -> None:
    """C13: Configuration coverage C is computed correctly, assigning VALID, PARTIAL_COVERAGE, or NO_COVERAGE (STAT-03, AC-M61-03-02)."""
    cells = [
        # Config 1: 2/2 completed -> VALID
        _make_cell("m1", "sc1", "fold_0", ExecutionStatus.COMPLETED),
        _make_cell("m1", "sc1", "fold_1", ExecutionStatus.COMPLETED),
        # Config 2: 1/2 completed -> PARTIAL_COVERAGE
        _make_cell("m2", "sc1", "fold_0", ExecutionStatus.COMPLETED),
        _make_cell("m2", "sc1", "fold_1", ExecutionStatus.FAILED),
        # Config 3: 0/2 completed -> NO_COVERAGE
        _make_cell("m3", "sc1", "fold_0", ExecutionStatus.FAILED),
        _make_cell("m3", "sc1", "fold_1", ExecutionStatus.CANCELLED),
    ]
    consol = consolidate_descriptive(
        cell_results=cells,
        total_folds_per_config={
            ("m1", "sc1"): 2,
            ("m2", "sc1"): 2,
            ("m3", "sc1"): 2,
        },
        experiment_id="exp_test",
        partition_plan_id="plan_test",
    )
    c1 = consol.configurations[("m1", "sc1")]
    assert c1.coverage == 1.0
    assert c1.coverage_status == CoverageStatus.VALID

    c2 = consol.configurations[("m2", "sc1")]
    assert c2.coverage == 0.5
    assert c2.coverage_status == CoverageStatus.PARTIAL_COVERAGE

    c3 = consol.configurations[("m3", "sc1")]
    assert c3.coverage == 0.0
    assert c3.coverage_status == CoverageStatus.NO_COVERAGE


def test_consolidate_descriptive_failed_and_cancelled_folds_recorded() -> None:
    """C14: FAILED and CANCELLED folds are recorded in failed_fold_ids and cancelled_fold_ids without metric coercion (STAT-03, AC-M61-03-03)."""
    cells = [
        _make_cell("ridge", "sc1", "fold_0", ExecutionStatus.COMPLETED, {"rmse": _make_metric(0.20)}),
        _make_cell("ridge", "sc1", "fold_1", ExecutionStatus.FAILED),
        _make_cell("ridge", "sc1", "fold_2", ExecutionStatus.CANCELLED),
    ]
    consol = consolidate_descriptive(
        cell_results=cells,
        total_folds_per_config={("ridge", "sc1"): 3},
        experiment_id="exp_test",
        partition_plan_id="plan_test",
    )
    summary = consol.configurations[("ridge", "sc1")]
    assert summary.completed_fold_ids == ("fold_0",)
    assert summary.failed_fold_ids == ("fold_1",)
    assert summary.cancelled_fold_ids == ("fold_2",)
    assert summary.completed_folds == 1
    assert summary.failed_folds == 1
    assert summary.cancelled_folds == 1
    # Check that failed/cancelled folds did not coerce metrics to 0.0
    assert "fold_1" not in summary.fold_metrics or summary.fold_metrics["fold_1"] == {}


def test_consolidate_descriptive_metric_stats_multi_fold() -> None:
    """C15: AggregatedMetricStats computes mean, sample std (ddof=1), median, IQR, min, max when n_valid >= 2 (STAT-03, AC-M61-03-04)."""
    vals = [0.10, 0.20, 0.30, 0.40, 0.50]
    cells = [
        _make_cell("ridge", "sc1", f"fold_{i}", ExecutionStatus.COMPLETED, {"rmse": _make_metric(v)})
        for i, v in enumerate(vals)
    ]
    consol = consolidate_descriptive(
        cell_results=cells,
        total_folds_per_config={("ridge", "sc1"): 5},
        experiment_id="exp_test",
        partition_plan_id="plan_test",
    )
    summary = consol.configurations[("ridge", "sc1")]
    rmse_stats = summary.aggregated_metrics["rmse"]

    assert rmse_stats.n_valid == 5
    assert rmse_stats.n_total == 5
    assert rmse_stats.status == MetricStatus.VALID
    assert rmse_stats.mean == pytest.approx(float(np.mean(vals)))
    assert rmse_stats.std == pytest.approx(float(np.std(vals, ddof=1)))
    assert rmse_stats.median == pytest.approx(float(np.median(vals)))
    q75, q25 = np.percentile(vals, [75, 25])
    assert rmse_stats.iqr == pytest.approx(float(q75 - q25))
    assert rmse_stats.min_value == pytest.approx(0.10)
    assert rmse_stats.max_value == pytest.approx(0.50)


def test_consolidate_descriptive_metric_stats_single_fold() -> None:
    """C16: AggregatedMetricStats computes mean, median, min, max, but sets std = None when n_valid == 1 (STAT-03, AC-M61-03-05)."""
    cells = [
        _make_cell("ridge", "sc1", "fold_0", ExecutionStatus.COMPLETED, {"rmse": _make_metric(0.25)}),
        _make_cell("ridge", "sc1", "fold_1", ExecutionStatus.FAILED),
    ]
    consol = consolidate_descriptive(
        cell_results=cells,
        total_folds_per_config={("ridge", "sc1"): 2},
        experiment_id="exp_test",
        partition_plan_id="plan_test",
    )
    summary = consol.configurations[("ridge", "sc1")]
    rmse_stats = summary.aggregated_metrics["rmse"]

    assert rmse_stats.n_valid == 1
    assert rmse_stats.n_total == 2
    assert rmse_stats.status == MetricStatus.PARTIAL_COVERAGE
    assert rmse_stats.mean == pytest.approx(0.25)
    assert rmse_stats.std is None
    assert rmse_stats.median == pytest.approx(0.25)
    assert rmse_stats.iqr == pytest.approx(0.0)
    assert rmse_stats.min_value == pytest.approx(0.25)
    assert rmse_stats.max_value == pytest.approx(0.25)


def test_consolidate_descriptive_metric_stats_zero_valid() -> None:
    """C17: AggregatedMetricStats sets all summary fields to None and status to UNDEFINED_NAN when n_valid == 0 (STAT-03, AC-M61-03-06)."""
    cells = [
        _make_cell(
            "ridge",
            "sc1",
            "fold_0",
            ExecutionStatus.COMPLETED,
            {"rmse": _make_metric(float("nan"), MetricStatus.UNDEFINED_NAN)},
        ),
        _make_cell(
            "ridge",
            "sc1",
            "fold_1",
            ExecutionStatus.COMPLETED,
            {"rmse": _make_metric(float("nan"), MetricStatus.UNDEFINED_NAN)},
        ),
    ]
    consol = consolidate_descriptive(
        cell_results=cells,
        total_folds_per_config={("ridge", "sc1"): 2},
        experiment_id="exp_test",
        partition_plan_id="plan_test",
    )
    summary = consol.configurations[("ridge", "sc1")]
    rmse_stats = summary.aggregated_metrics["rmse"]

    assert rmse_stats.n_valid == 0
    assert rmse_stats.n_total == 2
    assert rmse_stats.status == MetricStatus.UNDEFINED_NAN
    assert rmse_stats.mean is None
    assert rmse_stats.std is None
    assert rmse_stats.median is None
    assert rmse_stats.iqr is None
    assert rmse_stats.min_value is None
    assert rmse_stats.max_value is None


def test_consolidate_descriptive_incorporates_pooled_oof() -> None:
    """C18: Consolidated OOF prediction records are incorporated into pooled_oof_metrics of ConfigurationSummary (STAT-03, AC-M61-03-07)."""
    cells = [
        _make_cell("ridge", "sc1", "fold_0", ExecutionStatus.COMPLETED, {"rmse": _make_metric(0.20)}),
        _make_cell("ridge", "sc1", "fold_1", ExecutionStatus.COMPLETED, {"rmse": _make_metric(0.30)}),
    ]
    oof_rec = ConsolidatedOofPredictions(
        model_id="ridge",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        observation_ids=("obs_1", "obs_2"),
        y_true=(1.0, 2.0),
        y_pred=(1.1, 1.9),
        coverage=1.0,
        pooled_metrics={"rmse": _make_metric(0.15)},
    )
    consol = consolidate_descriptive(
        cell_results=cells,
        total_folds_per_config={("ridge", "sc1"): 2},
        oof_predictions=[oof_rec],
        experiment_id="exp_test",
        partition_plan_id="plan_test",
    )
    summary = consol.configurations[("ridge", "sc1")]
    assert "rmse" in summary.pooled_oof_metrics
    assert summary.pooled_oof_metrics["rmse"].value == pytest.approx(0.15)


def test_consolidate_descriptive_timing_aggregation() -> None:
    """C19: Timing breakdown across completed folds is aggregated into mean and sum durations (STAT-03, AC-M61-03-08)."""
    t1 = TimingBreakdown(fit_time_s=1.0, predict_time_s=0.2, total_cell_time_s=1.5)
    t2 = TimingBreakdown(fit_time_s=3.0, predict_time_s=0.4, total_cell_time_s=4.5)
    cells = [
        _make_cell("ridge", "sc1", "fold_0", ExecutionStatus.COMPLETED, timing=t1),
        _make_cell("ridge", "sc1", "fold_1", ExecutionStatus.COMPLETED, timing=t2),
    ]
    consol = consolidate_descriptive(
        cell_results=cells,
        total_folds_per_config={("ridge", "sc1"): 2},
        experiment_id="exp_test",
        partition_plan_id="plan_test",
    )
    summary = consol.configurations[("ridge", "sc1")]
    timing = summary.aggregated_timing
    assert timing is not None
    assert timing.fit_mean_s == pytest.approx(2.0)
    assert timing.fit_total_s == pytest.approx(4.0)
    assert timing.predict_mean_s == pytest.approx(0.3)
    assert timing.predict_total_s == pytest.approx(0.6)
    assert timing.total_cell_mean_s == pytest.approx(3.0)
    assert timing.total_cell_sum_s == pytest.approx(6.0)


def test_consolidate_descriptive_feature_stability() -> None:
    """C20: Pairwise feature selection stability across folds uses compute_selection_stability with Jaccard empty set conventions (STAT-03, AC-M61-03-09)."""
    # 2 folds with dynamic selections
    cells = [
        _make_cell(
            "ridge",
            "dyn_sc",
            "fold_0",
            ExecutionStatus.COMPLETED,
            selected_features=("f1", "f2"),
        ),
        _make_cell(
            "ridge",
            "dyn_sc",
            "fold_1",
            ExecutionStatus.COMPLETED,
            selected_features=("f2", "f3"),
        ),
    ]
    consol = consolidate_descriptive(
        cell_results=cells,
        total_folds_per_config={("ridge", "dyn_sc"): 2},
        n_total_candidates_per_config={("ridge", "dyn_sc"): 4},
        experiment_id="exp_test",
        partition_plan_id="plan_test",
    )
    summary = consol.configurations[("ridge", "dyn_sc")]
    stab = summary.feature_stability
    assert stab is not None
    # Jaccard between {f1, f2} and {f2, f3}: |{f2}| / |{f1, f2, f3}| = 1/3
    assert stab.mean_jaccard == pytest.approx(1.0 / 3.0)

    # Empty sets convention: both empty -> 1.0
    cells_empty = [
        _make_cell("ridge", "empty_sc", "fold_0", ExecutionStatus.COMPLETED, selected_features=()),
        _make_cell("ridge", "empty_sc", "fold_1", ExecutionStatus.COMPLETED, selected_features=()),
    ]
    consol_empty = consolidate_descriptive(
        cell_results=cells_empty,
        total_folds_per_config={("ridge", "empty_sc"): 2},
        n_total_candidates_per_config={("ridge", "empty_sc"): 4},
        experiment_id="exp_test",
        partition_plan_id="plan_test",
    )
    stab_empty = consol_empty.configurations[("ridge", "empty_sc")].feature_stability
    assert stab_empty is not None
    assert stab_empty.mean_jaccard == pytest.approx(1.0)
