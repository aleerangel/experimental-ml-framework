"""Unit tests for pooled out-of-fold metrics and fold metric aggregations.

Covers ORCH-17, ORCH-18, ORCH-19, AC-M53-02-01 to AC-M53-02-04, and Checks C10 to C13.
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from experimental_ml.core.enums import AggregationScope, ExecutionStatus, MetricDirection, MetricStatus, TaskType
from experimental_ml.core.types import ExperimentId, ModelId, ObservationId, PartitionPlanId, ScenarioId
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue
from experimental_ml.orchestration.oof import (
    ConsolidatedOofPredictions,
    consolidate_oof_predictions,
)
from experimental_ml.orchestration.types import CellId, CellResultRecord, PredictionRecord, TimingBreakdown


def _build_cell_results_and_preds() -> tuple[list[PredictionRecord], list[CellResultRecord]]:
    """Helper creating matching prediction records and cell results across 2 folds."""
    # Fold 0: obs_1 (true=10, pred=10), obs_2 (true=20, pred=20) -> rmse=0.0
    p1 = PredictionRecord(
        cell_id=CellId("cell_m1__sc1__fold_0"),
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        y_true=(10.0, 20.0),
        y_pred=(10.0, 20.0),
    )
    c1 = CellResultRecord(
        cell_id=CellId("cell_m1__sc1__fold_0"),
        experiment_id=ExperimentId("exp_1"),
        partition_plan_id=PartitionPlanId("plan_1"),
        model_id=ModelId("m1"),
        scenario_id=ScenarioId("sc1"),
        fold_id="fold_0",
        timing=TimingBreakdown(),
        status=ExecutionStatus.COMPLETED,
        metrics={
            "rmse": MetricValue(
                metric_id="rmse",
                value=0.0,
                status=MetricStatus.VALID,
                direction=MetricDirection.MINIMIZE,
                scope=MetricEvaluationScope.PER_FOLD,
                n_samples=2,
            ),
            "mae": MetricValue(
                metric_id="mae",
                value=0.0,
                status=MetricStatus.VALID,
                direction=MetricDirection.MINIMIZE,
                scope=MetricEvaluationScope.PER_FOLD,
                n_samples=2,
            ),
        },
    )

    # Fold 1: obs_3 (true=30, pred=32), obs_4 (true=40, pred=42) -> diff=2, rmse=2.0
    p2 = PredictionRecord(
        cell_id=CellId("cell_m1__sc1__fold_1"),
        observation_ids=(ObservationId("obs_3"), ObservationId("obs_4")),
        y_true=(30.0, 40.0),
        y_pred=(32.0, 42.0),
    )
    c2 = CellResultRecord(
        cell_id=CellId("cell_m1__sc1__fold_1"),
        experiment_id=ExperimentId("exp_1"),
        partition_plan_id=PartitionPlanId("plan_1"),
        model_id=ModelId("m1"),
        scenario_id=ScenarioId("sc1"),
        fold_id="fold_1",
        timing=TimingBreakdown(),
        status=ExecutionStatus.COMPLETED,
        metrics={
            "rmse": MetricValue(
                metric_id="rmse",
                value=2.0,
                status=MetricStatus.VALID,
                direction=MetricDirection.MINIMIZE,
                scope=MetricEvaluationScope.PER_FOLD,
                n_samples=2,
            ),
            "mae": MetricValue(
                metric_id="mae",
                value=2.0,
                status=MetricStatus.VALID,
                direction=MetricDirection.MINIMIZE,
                scope=MetricEvaluationScope.PER_FOLD,
                n_samples=2,
            ),
        },
    )

    return [p1, p2], [c1, c2]


def test_m53_02_01_pooled_oof_metrics_evaluation() -> None:
    """Proof C10: POOLED_OOF evaluates metrics over the complete pooled out-of-fold vector (ORCH-17, AC 1)."""
    preds, cells = _build_cell_results_and_preds()

    oof = consolidate_oof_predictions(
        model_id="m1",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        prediction_records=preds,
        cell_results=cells,
    )

    assert "rmse" in oof.pooled_metrics
    rmse_pooled = oof.pooled_metrics["rmse"]
    assert rmse_pooled.scope == MetricEvaluationScope.POOLED_OOF
    assert rmse_pooled.status == MetricStatus.VALID
    assert rmse_pooled.n_samples == 4

    # Pooled errors: [0, 0, 2, 2] -> sum sq = 8; mean sq = 2.0; sqrt(2.0) = 1.41421356...
    assert pytest.approx(rmse_pooled.value, abs=1e-5) == math.sqrt(2.0)


def test_m53_02_02_fold_aggregation_statistics() -> None:
    """Proof C11: FOLD_AGGREGATION aggregates fold-level metrics (mean, std, median, iqr) (ORCH-18, AC 2)."""
    preds, cells = _build_cell_results_and_preds()

    oof = consolidate_oof_predictions(
        model_id="m1",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        prediction_records=preds,
        cell_results=cells,
    )

    assert "rmse" in oof.aggregated_metrics
    agg_rmse = oof.aggregated_metrics["rmse"]
    assert agg_rmse.scope == AggregationScope.FOLD_AGGREGATION
    assert agg_rmse.status == MetricStatus.VALID
    assert agg_rmse.valid_folds == 2
    assert agg_rmse.total_folds == 2
    assert agg_rmse.coverage == 1.0

    # Fold values: 0.0 and 2.0 -> mean = 1.0; std(ddof=1) = sqrt(2.0) = 1.41421356...
    assert pytest.approx(agg_rmse.mean, abs=1e-5) == 1.0
    assert pytest.approx(agg_rmse.std, abs=1e-5) == math.sqrt(2.0)
    assert pytest.approx(agg_rmse.median, abs=1e-5) == 1.0


def test_m53_02_03_undefined_nan_resilience() -> None:
    """Proof C12: Division by zero or math errors assign UNDEFINED_NAN without crashing (ORCH-19, AC 3)."""
    # MAPE with y_true = 0.0 triggers division by zero
    p = PredictionRecord(
        cell_id=CellId("cell_m1__sc1__fold_0"),
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        y_true=(0.0, 0.0),
        y_pred=(1.0, 2.0),
    )

    oof = consolidate_oof_predictions(
        model_id="m1",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        prediction_records=[p],
        metrics=["mape"],
    )

    assert "mape" in oof.pooled_metrics
    mape_val = oof.pooled_metrics["mape"]
    assert mape_val.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(mape_val.value)
    assert len(mape_val.warnings) > 0


def test_m53_02_04_metrics_scopes_distinction() -> None:
    """Proof C13: ConsolidatedOofPredictions stores pooled_metrics and aggregated_metrics separately (ORCH-17, ORCH-18, AC 4)."""
    preds, cells = _build_cell_results_and_preds()

    oof = consolidate_oof_predictions(
        model_id="m1",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        prediction_records=preds,
        cell_results=cells,
    )

    # Both scopes must exist and be distinct objects
    assert isinstance(oof.pooled_metrics, dict) or hasattr(oof.pooled_metrics, "keys")
    assert isinstance(oof.aggregated_metrics, dict) or hasattr(oof.aggregated_metrics, "keys")

    for k, v in oof.pooled_metrics.items():
        assert v.scope == MetricEvaluationScope.POOLED_OOF

    for k, v in oof.aggregated_metrics.items():
        assert v.scope == AggregationScope.FOLD_AGGREGATION

    # Pooled RMSE is sqrt(2) ≈ 1.414, whereas Fold Aggregation Mean RMSE is 1.0
    assert oof.pooled_metrics["rmse"].value != oof.aggregated_metrics["rmse"].mean
    assert pytest.approx(oof.pooled_metrics["rmse"].value, abs=1e-4) == 1.4142
    assert pytest.approx(oof.aggregated_metrics["rmse"].mean, abs=1e-4) == 1.0000
