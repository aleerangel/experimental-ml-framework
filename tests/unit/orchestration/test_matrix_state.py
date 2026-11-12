"""Unit tests for global matrix execution state, codecs, and atomic persistence (M5.2).

Covers C6 to C10 (ORCH-10).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ExperimentId
from experimental_ml.orchestration.state import (
    MatrixExecutionState,
    load_execution_state,
    matrix_execution_state_from_dict,
    matrix_execution_state_to_dict,
    save_execution_state,
)
from experimental_ml.orchestration.types import CellId, ExecutionStatus


def _create_sample_state() -> MatrixExecutionState:
    c1 = CellId("cell_ridge__sc1__fold_0")
    c2 = CellId("cell_ridge__sc1__fold_1")
    c3 = CellId("cell_ridge__sc1__fold_2")

    statuses = {
        c1: ExecutionStatus.COMPLETED,
        c2: ExecutionStatus.FAILED,
        c3: ExecutionStatus.PENDING,
    }

    return MatrixExecutionState(
        experiment_id=ExperimentId("exp_001"),
        run_id="run_20261112_001",
        created_at="2026-11-12T10:00:00Z",
        updated_at="2026-11-12T10:05:00Z",
        master_seed=42,
        total_cells=3,
        cell_statuses=statuses,
    )


def test_m52_02_01_matrix_execution_state_fields():
    """C6: MatrixExecutionState immutable frozen dataclass fields (ORCH-10, AC 1)."""
    state = _create_sample_state()

    assert state.experiment_id == ExperimentId("exp_001")
    assert state.run_id == "run_20261112_001"
    assert state.created_at == "2026-11-12T10:00:00Z"
    assert state.updated_at == "2026-11-12T10:05:00Z"
    assert state.master_seed == 42
    assert state.total_cells == 3
    assert state.completed_cells == 1
    assert state.failed_cells == 1
    assert state.cancelled_cells == 0
    assert len(state.cell_statuses) == 3

    # Immutability
    with pytest.raises(Exception):
        state.completed_cells = 2  # type: ignore


def test_m52_02_02_with_cell_update_immutability():
    """C7: MatrixExecutionState.with_cell_update immutably updates status and counts (ORCH-10, AC 1)."""
    state = _create_sample_state()
    c3 = CellId("cell_ridge__sc1__fold_2")

    updated = state.with_cell_update(c3, ExecutionStatus.COMPLETED, updated_at="2026-11-12T10:10:00Z")

    # Original state remains unchanged
    assert state.completed_cells == 1
    assert state.cell_statuses[c3] == ExecutionStatus.PENDING

    # Updated state has new values
    assert updated.completed_cells == 2
    assert updated.failed_cells == 1
    assert updated.cell_statuses[c3] == ExecutionStatus.COMPLETED
    assert updated.updated_at == "2026-11-12T10:10:00Z"


def test_m52_02_03_state_to_dict_json_serializable():
    """C8: matrix_execution_state_to_dict produces JSON-serializable dictionary (ORCH-10, AC 2)."""
    state = _create_sample_state()
    d = matrix_execution_state_to_dict(state)

    assert isinstance(d, dict)
    assert d["experiment_id"] == "exp_001"
    assert d["run_id"] == "run_20261112_001"
    assert d["total_cells"] == 3
    assert d["completed_cells"] == 1
    assert d["failed_cells"] == 1
    assert d["cell_statuses"]["cell_ridge__sc1__fold_0"] == "COMPLETED"

    # Serializes to standard JSON
    json_str = json.dumps(d, allow_nan=False)
    assert "cell_ridge__sc1__fold_0" in json_str


def test_m52_02_04_state_from_dict_roundtrip():
    """C9: matrix_execution_state_from_dict round-trip fidelity (ORCH-10, AC 3)."""
    state = _create_sample_state()
    d = matrix_execution_state_to_dict(state)
    reconstructed = matrix_execution_state_from_dict(d)

    assert reconstructed.experiment_id == state.experiment_id
    assert reconstructed.run_id == state.run_id
    assert reconstructed.created_at == state.created_at
    assert reconstructed.updated_at == state.updated_at
    assert reconstructed.master_seed == state.master_seed
    assert reconstructed.total_cells == state.total_cells
    assert reconstructed.completed_cells == state.completed_cells
    assert reconstructed.failed_cells == state.failed_cells
    assert reconstructed.cancelled_cells == state.cancelled_cells
    assert reconstructed.cell_statuses == state.cell_statuses


def test_m52_02_05_save_and_load_execution_state(tmp_path: Path):
    """C10: save_execution_state and load_execution_state atomic file persistence (ORCH-10, AC 4)."""
    state = _create_sample_state()
    run_dir = tmp_path / "run_alpha"
    run_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_execution_state(state, run_dir, overwrite=True)
    assert file_path.exists()
    assert file_path.name == "execution_state.json"

    # Overwrite protection
    with pytest.raises(ConfigurationError, match="Target artifact already exists"):
        save_execution_state(state, run_dir, overwrite=False)

    # Load and verify fidelity
    loaded = load_execution_state(run_dir)
    assert loaded.experiment_id == state.experiment_id
    assert loaded.run_id == state.run_id
    assert loaded.completed_cells == 1
    assert len(loaded.cell_statuses) == 3
