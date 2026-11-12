"""Unit tests for Stage 4 execution verification gate (verify_runs_gate).

Covers ORCH-21, AC-M53-04-01 to AC-M53-04-06, and Checks C17 to C22.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from experimental_ml.core.enums import ExecutionStatus, TaskType
from experimental_ml.core.findings import ContractViolationError, DataIntegrityError
from experimental_ml.core.types import ExperimentId, ModelId, ObservationId, PartitionPlanId, ScenarioId
from experimental_ml.orchestration.oof import ConsolidatedOofPredictions, save_oof_predictions
from experimental_ml.orchestration.state import MatrixExecutionState, save_execution_state
from experimental_ml.orchestration.storage import save_cell_artifacts
from experimental_ml.orchestration.types import CellId, CellResultRecord, PredictionRecord, TimingBreakdown
from experimental_ml.stages.stage_gates import verify_runs_gate


def _setup_valid_run(run_dir: Path) -> tuple[MatrixExecutionState, CellId]:
    """Helper creating a minimal valid completed run directory."""
    cid = CellId("cell_ridge__sc1__fold_0")
    state = MatrixExecutionState(
        experiment_id=ExperimentId("exp_test"),
        run_id="run_test",
        created_at="2026-11-12T00:00:00Z",
        updated_at="2026-11-12T00:01:00Z",
        master_seed=42,
        total_cells=1,
        cell_statuses={cid: ExecutionStatus.COMPLETED},
        completed_cells=1,
        failed_cells=0,
        cancelled_cells=0,
    )
    save_execution_state(state, run_dir)

    cell_res = CellResultRecord(
        cell_id=cid,
        experiment_id=ExperimentId("exp_test"),
        partition_plan_id=PartitionPlanId("plan_test"),
        model_id=ModelId("ridge"),
        scenario_id=ScenarioId("sc1"),
        fold_id="fold_0",
        timing=TimingBreakdown(),
        status=ExecutionStatus.COMPLETED,
    )
    pred_rec = PredictionRecord(
        cell_id=cid,
        observation_ids=(ObservationId("obs_1"),),
        y_true=(1.0,),
        y_pred=(1.1,),
    )
    save_cell_artifacts(cell_res, pred_rec, run_dir)

    oof_rec = ConsolidatedOofPredictions(
        model_id=ModelId("ridge"),
        scenario_id=ScenarioId("sc1"),
        task_type=TaskType.REGRESSION,
        observation_ids=(ObservationId("obs_1"),),
        y_true=(1.0,),
        y_pred=(1.1,),
    )
    save_oof_predictions(oof_rec, run_dir)

    return state, cid


def test_m53_04_01_upstream_gates_verification(tmp_path: Path) -> None:
    """Proof C17: verify_runs_gate validates upstream stage gates when present (ORCH-21, AC 1)."""
    run_dir = tmp_path / "runs"
    run_dir.mkdir(parents=True)
    _setup_valid_run(run_dir)

    # Valid descriptor
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "dataset_descriptor.json").write_text(
        json.dumps({"dataset_hash": "hash123"}),
        encoding="utf-8",
    )

    # Corrupt preparation plan in upstream config
    prep_dir = tmp_path / "configuration"
    prep_dir.mkdir(parents=True)
    (prep_dir / "preparation_plan.json").write_text("invalid json", encoding="utf-8")

    with pytest.raises(DataIntegrityError):
        verify_runs_gate(tmp_path)


def test_m53_04_02_missing_or_corrupt_state_raises(tmp_path: Path) -> None:
    """Proof C18: verify_runs_gate raises DataIntegrityError on missing/corrupt execution_state (ORCH-21, AC 2)."""
    # 1. Missing execution_state.json
    with pytest.raises(DataIntegrityError, match="Execution state missing"):
        verify_runs_gate(tmp_path)

    # 2. Corrupted execution_state.json
    (tmp_path / "execution_state.json").write_text("{corrupt json", encoding="utf-8")
    with pytest.raises(DataIntegrityError, match="Failed to load execution state"):
        verify_runs_gate(tmp_path)


def test_m53_04_03_non_terminal_cell_status_raises(tmp_path: Path) -> None:
    """Proof C19: verify_runs_gate raises ContractViolationError on non-terminal cell statuses (ORCH-21, AC 3)."""
    cid = CellId("cell_ridge__sc1__fold_0")
    state = MatrixExecutionState(
        experiment_id=ExperimentId("exp_test"),
        run_id="run_test",
        created_at="2026-11-12T00:00:00Z",
        updated_at="2026-11-12T00:01:00Z",
        master_seed=42,
        total_cells=1,
        cell_statuses={cid: ExecutionStatus.RUNNING},  # Non-terminal!
        completed_cells=0,
        failed_cells=0,
        cancelled_cells=0,
    )
    save_execution_state(state, tmp_path)

    with pytest.raises(ContractViolationError, match="non-terminal cell"):
        verify_runs_gate(tmp_path)


def test_m53_04_04_missing_cell_artifact_raises(tmp_path: Path) -> None:
    """Proof C20: Missing cell or pred file for completed cell raises DataIntegrityError (ORCH-21, AC 4)."""
    _setup_valid_run(tmp_path)

    # Delete prediction file
    cid = "cell_ridge__sc1__fold_0"
    pred_file = tmp_path / "predictions" / f"pred_{cid}.json"
    pred_file.unlink()

    with pytest.raises(DataIntegrityError, match="Missing prediction artifact"):
        verify_runs_gate(tmp_path)


def test_m53_04_05_cross_hashes_mismatch_raises(tmp_path: Path) -> None:
    """Proof C21: Divergent partition_plan_id raises DataIntegrityError (ORCH-21, AC 5)."""
    run_dir = tmp_path / "runs"
    run_dir.mkdir(parents=True)
    _setup_valid_run(run_dir)

    # Upstream partition plan with different plan_id
    parts_dir = tmp_path / "partitions"
    parts_dir.mkdir(parents=True)
    (parts_dir / "partition_plan.json").write_text(
        json.dumps({"plan_id": "different_plan_hash_123"}),
        encoding="utf-8",
    )

    with pytest.raises(DataIntegrityError, match="partition_plan_id mismatch"):
        verify_runs_gate(tmp_path)


def test_m53_04_06_valid_runs_gate_returns_summary(tmp_path: Path) -> None:
    """Proof C22: Valid execution passes gate and returns structured summary (ORCH-21, AC 6)."""
    _setup_valid_run(tmp_path)

    summary = verify_runs_gate(tmp_path)
    assert isinstance(summary, dict)
    assert summary["status"] == "READY"
    assert summary["experiment_id"] == "exp_test"
    assert summary["total_cells"] == 1
    assert summary["completed_cells"] == 1
    assert summary["failed_cells"] == 0
    assert summary["cancelled_cells"] == 0
    assert summary["verified_configurations"] == ["ridge__sc1"]
