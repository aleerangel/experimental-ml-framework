"""Unit tests for partial coverage and fault tolerance in out-of-fold consolidation.

Covers ORCH-15, ORCH-21, AC-M53-05-01 to AC-M53-05-03, and Checks C14 to C16.
"""

from __future__ import annotations

import pytest

from experimental_ml.core.enums import ExecutionStatus, MetricDirection, MetricStatus, TaskType
from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.core.types import ExperimentId, ModelId, ObservationId, PartitionPlanId, ScenarioId
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue
from experimental_ml.orchestration.oof import (
    ConsolidatedOofPredictions,
    consolidate_oof_predictions,
)
from experimental_ml.orchestration.types import CellId, CellResultRecord, PredictionRecord, TimingBreakdown


def test_m53_05_01_partial_coverage_on_fold_failure() -> None:
    """Proof C14: Survived folds in FAULT_TOLERANT mark PARTIAL_COVERAGE on pooled metrics (ORCH-15, AC 1)."""
    # 2 folds expected: fold_0 completed (obs_1, obs_2), fold_1 failed (obs_3, obs_4 missing)
    p0 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_0"),
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        y_true=(10.0, 20.0),
        y_pred=(10.2, 19.8),
    )
    c0 = CellResultRecord(
        cell_id=CellId("cell_ridge__sc1__fold_0"),
        experiment_id=ExperimentId("exp_1"),
        partition_plan_id=PartitionPlanId("plan_1"),
        model_id=ModelId("ridge"),
        scenario_id=ScenarioId("sc1"),
        fold_id="fold_0",
        timing=TimingBreakdown(),
        status=ExecutionStatus.COMPLETED,
        metrics={
            "rmse": MetricValue(
                metric_id="rmse",
                value=0.2,
                status=MetricStatus.VALID,
                direction=MetricDirection.MINIMIZE,
                scope=MetricEvaluationScope.PER_FOLD,
                n_samples=2,
            ),
        },
    )
    c1_failed = CellResultRecord(
        cell_id=CellId("cell_ridge__sc1__fold_1"),
        experiment_id=ExperimentId("exp_1"),
        partition_plan_id=PartitionPlanId("plan_1"),
        model_id=ModelId("ridge"),
        scenario_id=ScenarioId("sc1"),
        fold_id="fold_1",
        timing=TimingBreakdown(),
        status=ExecutionStatus.FAILED,
        error_type="RuntimeError",
        error_message="Matrix singular",
    )

    all_target_obs = ["obs_1", "obs_2", "obs_3", "obs_4"]

    oof = consolidate_oof_predictions(
        model_id="ridge",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        prediction_records=[p0],
        cell_results=[c0, c1_failed],
        target_observation_ids=all_target_obs,
    )

    assert oof.status == MetricStatus.PARTIAL_COVERAGE
    assert oof.coverage == 0.5  # 2 of 4 observations
    assert "rmse" in oof.pooled_metrics
    assert oof.pooled_metrics["rmse"].status == MetricStatus.PARTIAL_COVERAGE


def test_m53_05_02_missing_observations_warning() -> None:
    """Proof C15: Missing observation_ids are recorded in ConsolidatedOofPredictions warnings (ORCH-15, AC 2)."""
    p0 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_0"),
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        y_true=(10.0, 20.0),
        y_pred=(10.0, 20.0),
    )

    all_target_obs = [
        ObservationId("obs_1"),
        ObservationId("obs_2"),
        ObservationId("obs_3"),
        ObservationId("obs_4"),
    ]

    oof = consolidate_oof_predictions(
        model_id="ridge",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        prediction_records=[p0],
        target_observation_ids=all_target_obs,
    )

    assert len(oof.warnings) > 0
    warning_text = " ".join(oof.warnings)
    assert "obs_3" in warning_text
    assert "obs_4" in warning_text
    assert "Missing 2 observation(s)" in warning_text


def test_m53_05_03_total_failure_raises_integrity_error() -> None:
    """Proof C16: 100% fold failure raises DataIntegrityError on OOF consolidation attempt (ORCH-15, AC 3)."""
    c0_failed = CellResultRecord(
        cell_id=CellId("cell_ridge__sc1__fold_0"),
        experiment_id=ExperimentId("exp_1"),
        partition_plan_id=PartitionPlanId("plan_1"),
        model_id=ModelId("ridge"),
        scenario_id=ScenarioId("sc1"),
        fold_id="fold_0",
        timing=TimingBreakdown(),
        status=ExecutionStatus.FAILED,
        error_type="ValueError",
    )
    c1_failed = CellResultRecord(
        cell_id=CellId("cell_ridge__sc1__fold_1"),
        experiment_id=ExperimentId("exp_1"),
        partition_plan_id=PartitionPlanId("plan_1"),
        model_id=ModelId("ridge"),
        scenario_id=ScenarioId("sc1"),
        fold_id="fold_1",
        timing=TimingBreakdown(),
        status=ExecutionStatus.FAILED,
        error_type="ValueError",
    )

    # Empty prediction records
    with pytest.raises(DataIntegrityError, match="zero prediction records"):
        consolidate_oof_predictions(
            model_id="ridge",
            scenario_id="sc1",
            task_type=TaskType.REGRESSION,
            prediction_records=[],
            cell_results=[c0_failed, c1_failed],
        )

    # Prediction record empty or all cell results failed
    p_dummy = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_0"),
        observation_ids=(ObservationId("obs_1"),),
        y_true=(1.0,),
        y_pred=(1.0,),
    )
    with pytest.raises(DataIntegrityError, match="All folds failed"):
        consolidate_oof_predictions(
            model_id="ridge",
            scenario_id="sc1",
            task_type=TaskType.REGRESSION,
            prediction_records=[p_dummy],
            cell_results=[c0_failed, c1_failed],
        )
