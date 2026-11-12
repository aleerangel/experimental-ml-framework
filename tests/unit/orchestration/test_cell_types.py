"""Unit tests for orchestration types, enums, and immutable data structures (M5.1).

Covers C1 to C9 (ORCH-01, ORCH-02, ORCH-03, ORCH-04).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType
import pytest

from experimental_ml.core.enums import ExecutionStatus, MetricDirection, MetricStatus
from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.core.types import ExperimentId, ModelId, ObservationId, PartitionPlanId, ScenarioId
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue
from experimental_ml.models.types import ModelDiagnostics
from experimental_ml.orchestration.types import (
    CellId,
    CellPhase,
    CellResultRecord,
    ErrorPolicy,
    PredictionRecord,
    TimingBreakdown,
)


def test_m51_01_01_execution_status_enum() -> None:
    """C1: ExecutionStatus enum members: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED (ORCH-01, AC 1)."""
    assert ExecutionStatus.PENDING.value == "PENDING"
    assert ExecutionStatus.RUNNING.value == "RUNNING"
    assert ExecutionStatus.COMPLETED.value == "COMPLETED"
    assert ExecutionStatus.FAILED.value == "FAILED"
    assert ExecutionStatus.CANCELLED.value == "CANCELLED"
    assert len(ExecutionStatus) >= 5


def test_m51_01_02_error_policy_enum() -> None:
    """C2: ErrorPolicy enum members: FAULT_TOLERANT, FAIL_FAST (ORCH-01, AC 2)."""
    assert ErrorPolicy.FAULT_TOLERANT.value == "FAULT_TOLERANT"
    assert ErrorPolicy.FAIL_FAST.value == "FAIL_FAST"
    assert len(ErrorPolicy) == 2


def test_m51_01_03_cell_phase_enum() -> None:
    """C3: CellPhase canonical sub-phases (ORCH-01, AC 3)."""
    expected_phases = {
        "DATA_EXTRACTION",
        "FEATURE_SELECTION",
        "PREPROCESSING_L1",
        "HYPERPARAMETER_TUNING",
        "PREPROCESSING_L2",
        "MODEL_FIT",
        "PREDICTION",
        "METRIC_COMPUTATION",
    }
    actual_phases = {phase.value for phase in CellPhase}
    assert expected_phases.issubset(actual_phases)


def test_m51_01_04_cell_id_validation() -> None:
    """C4: CellId non-empty validation (ORCH-02, AC 1)."""
    cid = CellId("cell_ridge_sc_all_fold_0")
    assert str(cid) == "cell_ridge_sc_all_fold_0"

    with pytest.raises((ValueError, ConfigurationError)):
        CellId("")

    with pytest.raises((ValueError, ConfigurationError)):
        CellId("   ")

    with pytest.raises((ValueError, ConfigurationError)):
        CellId("cell\nname")


def test_m51_01_05_timing_breakdown_fields() -> None:
    """C5: TimingBreakdown non-negative float fields (ORCH-02, AC 2)."""
    tb = TimingBreakdown(
        data_extraction_time_s=0.01,
        feature_selection_time_s=0.05,
        tuning_time_s=1.20,
        preprocessing_time_s=0.03,
        fit_time_s=0.50,
        predict_time_s=0.02,
        evaluation_time_s=0.01,
        total_cell_time_s=1.82,
    )
    assert tb.data_extraction_time_s == 0.01
    assert tb.feature_selection_time_s == 0.05
    assert tb.tuning_time_s == 1.20
    assert tb.preprocessing_time_s == 0.03
    assert tb.fit_time_s == 0.50
    assert tb.predict_time_s == 0.02
    assert tb.evaluation_time_s == 0.01
    assert tb.total_cell_time_s == 1.82

    # Negative values rejected
    with pytest.raises((ValueError, ContractViolationError)):
        TimingBreakdown(data_extraction_time_s=-0.1)


def test_m51_01_06_prediction_record_fields() -> None:
    """C6: PredictionRecord fields: observation_ids, y_true, y_pred, y_std, y_proba, residuals (ORCH-03, AC 1)."""
    obs_ids = (ObservationId("obs_1"), ObservationId("obs_2"))
    pred_rec = PredictionRecord(
        cell_id=CellId("cell_01"),
        observation_ids=obs_ids,
        y_true=(10.0, 20.0),
        y_pred=(10.5, 19.5),
        y_std=(0.2, 0.3),
        y_proba=None,
        residuals=(-0.5, 0.5),
    )
    assert pred_rec.cell_id == CellId("cell_01")
    assert pred_rec.observation_ids == obs_ids
    assert pred_rec.y_true == (10.0, 20.0)
    assert pred_rec.y_pred == (10.5, 19.5)
    assert pred_rec.y_std == (0.2, 0.3)
    assert pred_rec.y_proba is None
    assert pred_rec.residuals == (-0.5, 0.5)


def test_m51_01_07_prediction_record_alignment() -> None:
    """C7: PredictionRecord length alignment and non-NaN check (ORCH-03, AC 2)."""
    obs_ids = (ObservationId("obs_1"), ObservationId("obs_2"))

    # Mismatched lengths raise ContractViolationError
    with pytest.raises(ContractViolationError):
        PredictionRecord(
            cell_id=CellId("cell_01"),
            observation_ids=obs_ids,
            y_true=(10.0,),  # len 1 vs 2
            y_pred=(10.5, 19.5),
        )

    with pytest.raises(ContractViolationError):
        PredictionRecord(
            cell_id=CellId("cell_01"),
            observation_ids=obs_ids,
            y_true=(10.0, 20.0),
            y_pred=(10.5,),  # len 1 vs 2
        )

    with pytest.raises(ContractViolationError):
        PredictionRecord(
            cell_id=CellId("cell_01"),
            observation_ids=obs_ids,
            y_true=(10.0, 20.0),
            y_pred=(10.5, 19.5),
            y_std=(0.1,),  # len 1 vs 2
        )

    # Empty observation_ids rejected
    with pytest.raises(ContractViolationError):
        PredictionRecord(
            cell_id=CellId("cell_01"),
            observation_ids=(),
            y_true=(),
            y_pred=(),
        )


def test_m51_01_08_cell_result_record_fields() -> None:
    """C8: CellResultRecord fields encapsulation (ORCH-04, AC 1)."""
    tb = TimingBreakdown(total_cell_time_s=0.5)
    metric_val = MetricValue(
        metric_id="rmse",
        value=1.5,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=10,
    )
    diag = ModelDiagnostics(
        model_id=ModelId("dummy_model"),
        phase="predict",
        diagnostics={"n_iter": 10},
        extracted_at="2026-11-12T10:00:00Z",
    )

    cr = CellResultRecord(
        cell_id=CellId("cell_01"),
        experiment_id=ExperimentId("exp_01"),
        partition_plan_id=PartitionPlanId("plan_01"),
        model_id=ModelId("model_01"),
        scenario_id=ScenarioId("sc_01"),
        fold_id="fold_0",
        phase="DEV_CV",
        status=ExecutionStatus.COMPLETED,
        selected_features=("f1", "f2"),
        effective_parameters={"alpha": 0.1},
        timing=tb,
        metrics={"rmse": metric_val},
        diagnostics=diag,
    )

    assert cr.cell_id == CellId("cell_01")
    assert cr.experiment_id == ExperimentId("exp_01")
    assert cr.partition_plan_id == PartitionPlanId("plan_01")
    assert cr.model_id == ModelId("model_01")
    assert cr.scenario_id == ScenarioId("sc_01")
    assert cr.fold_id == "fold_0"
    assert cr.phase == "DEV_CV"
    assert cr.status == ExecutionStatus.COMPLETED
    assert cr.selected_features == ("f1", "f2")
    assert isinstance(cr.effective_parameters, MappingProxyType)
    assert cr.effective_parameters["alpha"] == 0.1
    assert isinstance(cr.metrics, MappingProxyType)
    assert cr.metrics["rmse"].value == 1.5
    assert cr.diagnostics == diag
    assert cr.error_type is None


def test_m51_01_09_immutability() -> None:
    """C9: Immutability FrozenInstanceError on modification (ORCH-04, AC 2)."""
    tb = TimingBreakdown()
    with pytest.raises(FrozenInstanceError):
        tb.total_cell_time_s = 2.0  # type: ignore[misc]

    pred_rec = PredictionRecord(
        cell_id=CellId("cell_01"),
        observation_ids=(ObservationId("obs_1"),),
        y_true=(10.0,),
        y_pred=(10.5,),
    )
    with pytest.raises(FrozenInstanceError):
        pred_rec.cell_id = CellId("cell_02")  # type: ignore[misc]

    cr = CellResultRecord(
        cell_id=CellId("cell_01"),
        experiment_id=ExperimentId("exp_01"),
        partition_plan_id=PartitionPlanId("plan_01"),
        model_id=ModelId("model_01"),
        scenario_id=ScenarioId("sc_01"),
        fold_id="fold_0",
        phase="DEV_CV",
        status=ExecutionStatus.COMPLETED,
        selected_features=("f1",),
        effective_parameters={},
        timing=tb,
        metrics={},
    )
    with pytest.raises(FrozenInstanceError):
        cr.status = ExecutionStatus.FAILED  # type: ignore[misc]
