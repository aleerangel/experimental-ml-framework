"""Unit tests for Stage 4B to Stage 5 transition validation (STAT-02, CA-E5-01)."""

import json
from pathlib import Path
import pytest

from experimental_ml.core.enums import ExecutionStatus
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.core.types import CellId, ExperimentId
from experimental_ml.orchestration.state import MatrixExecutionState, save_execution_state
from experimental_ml.statistics.consolidation import validate_stage5_entry


def test_validate_stage5_entry_missing_or_corrupt_state(tmp_path: Path) -> None:
    """C8: Missing or corrupted execution_state.json raises ContractViolationError (STAT-02, AC-M61-02-01)."""
    # 1. Missing file in directory
    with pytest.raises(ContractViolationError, match="execution_state.json missing or unreadable"):
        validate_stage5_entry(tmp_path)

    # 2. Corrupt/malformed JSON
    corrupt_file = tmp_path / "execution_state.json"
    corrupt_file.write_text("{corrupt: json}", encoding="utf-8")
    with pytest.raises(ContractViolationError, match="Failed to parse execution state"):
        validate_stage5_entry(tmp_path)


def test_validate_stage5_entry_non_terminal_cells_blocked(tmp_path: Path) -> None:
    """C9: Active non-terminal cells (PENDING or RUNNING) raise ContractViolationError with resume message (STAT-02, AC-M61-02-02)."""
    # Case with PENDING
    state_pending = MatrixExecutionState(
        experiment_id=ExperimentId("exp_test"),
        run_id="run_01",
        created_at="2026-11-16T12:00:00Z",
        updated_at="2026-11-16T12:01:00Z",
        master_seed=42,
        total_cells=2,
        cell_statuses={
            CellId("cell_ridge_sc1_fold0"): ExecutionStatus.COMPLETED,
            CellId("cell_ridge_sc1_fold1"): ExecutionStatus.PENDING,
        },
    )
    with pytest.raises(ContractViolationError, match="Execution contains 1 non-terminal cell.*resume"):
        validate_stage5_entry(state_pending)

    # Also test via directory load
    save_execution_state(state_pending, tmp_path, overwrite=True)
    with pytest.raises(ContractViolationError, match="Execution contains 1 non-terminal cell.*resume"):
        validate_stage5_entry(tmp_path)

    # Case with RUNNING
    state_running = MatrixExecutionState(
        experiment_id=ExperimentId("exp_test"),
        run_id="run_01",
        created_at="2026-11-16T12:00:00Z",
        updated_at="2026-11-16T12:01:00Z",
        master_seed=42,
        total_cells=2,
        cell_statuses={
            CellId("cell_ridge_sc1_fold0"): ExecutionStatus.COMPLETED,
            CellId("cell_ridge_sc1_fold1"): ExecutionStatus.RUNNING,
        },
    )
    with pytest.raises(ContractViolationError, match="Execution contains 1 non-terminal cell.*resume"):
        validate_stage5_entry(state_running)


def test_validate_stage5_entry_zero_completed_cells_blocked(tmp_path: Path) -> None:
    """C10: Execution state with completed_cells == 0 raises ContractViolationError (STAT-02, AC-M61-02-03)."""
    # All failed
    state_all_failed = MatrixExecutionState(
        experiment_id=ExperimentId("exp_test"),
        run_id="run_01",
        created_at="2026-11-16T12:00:00Z",
        updated_at="2026-11-16T12:01:00Z",
        master_seed=42,
        total_cells=2,
        cell_statuses={
            CellId("cell_ridge_sc1_fold0"): ExecutionStatus.FAILED,
            CellId("cell_ridge_sc1_fold1"): ExecutionStatus.FAILED,
        },
    )
    with pytest.raises(ContractViolationError, match="zero completed cells"):
        validate_stage5_entry(state_all_failed)

    # All cancelled
    state_all_cancelled = MatrixExecutionState(
        experiment_id=ExperimentId("exp_test"),
        run_id="run_01",
        created_at="2026-11-16T12:00:00Z",
        updated_at="2026-11-16T12:01:00Z",
        master_seed=42,
        total_cells=2,
        cell_statuses={
            CellId("cell_ridge_sc1_fold0"): ExecutionStatus.CANCELLED,
            CellId("cell_ridge_sc1_fold1"): ExecutionStatus.CANCELLED,
        },
    )
    with pytest.raises(ContractViolationError, match="zero completed cells"):
        validate_stage5_entry(state_all_cancelled)


def test_validate_stage5_entry_terminal_states_allowed(tmp_path: Path) -> None:
    """C11: All cells terminal (COMPLETED, FAILED, CANCELLED) with completed_cells >= 1 allows Stage 5 entry (STAT-02, AC-M61-02-04)."""
    # 1. Fully completed
    state_full = MatrixExecutionState(
        experiment_id=ExperimentId("exp_test"),
        run_id="run_01",
        created_at="2026-11-16T12:00:00Z",
        updated_at="2026-11-16T12:01:00Z",
        master_seed=42,
        total_cells=2,
        cell_statuses={
            CellId("cell_ridge_sc1_fold0"): ExecutionStatus.COMPLETED,
            CellId("cell_ridge_sc1_fold1"): ExecutionStatus.COMPLETED,
        },
    )
    # Returns None without raising
    assert validate_stage5_entry(state_full) is None

    # 2. Partially completed with FAILED and CANCELLED
    state_mixed = MatrixExecutionState(
        experiment_id=ExperimentId("exp_test"),
        run_id="run_01",
        created_at="2026-11-16T12:00:00Z",
        updated_at="2026-11-16T12:01:00Z",
        master_seed=42,
        total_cells=3,
        cell_statuses={
            CellId("cell_ridge_sc1_fold0"): ExecutionStatus.COMPLETED,
            CellId("cell_ridge_sc1_fold1"): ExecutionStatus.FAILED,
            CellId("cell_ridge_sc1_fold2"): ExecutionStatus.CANCELLED,
        },
    )
    assert validate_stage5_entry(state_mixed) is None

    # Test via dictionary and path
    save_execution_state(state_mixed, tmp_path, overwrite=True)
    assert validate_stage5_entry(tmp_path) is None

    # Dict directly
    raw_dict = {
        "experiment_id": "exp_test",
        "run_id": "run_01",
        "created_at": "2026-11-16T12:00:00Z",
        "updated_at": "2026-11-16T12:01:00Z",
        "master_seed": 42,
        "total_cells": 3,
        "completed_cells": 1,
        "failed_cells": 1,
        "cancelled_cells": 1,
        "cell_statuses": {
            "cell_0": "COMPLETED",
            "cell_1": "FAILED",
            "cell_2": "CANCELLED",
        },
    }
    assert validate_stage5_entry(raw_dict) is None
