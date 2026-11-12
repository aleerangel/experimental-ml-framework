"""Global experiment matrix execution state, codecs, and atomic persistence.

Complies with ORCH-10, STORE-01, STORE-02, and ADR-008.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import read_json, write_json_atomic
from experimental_ml.core.types import ExperimentId
from experimental_ml.orchestration.types import CellId, ExecutionStatus


def _utc_now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class MatrixExecutionState:
    """Immutable representation of global experiment matrix execution progress and state."""

    experiment_id: ExperimentId
    run_id: str
    created_at: str
    updated_at: str
    master_seed: int
    total_cells: int
    cell_statuses: Mapping[CellId, ExecutionStatus]
    completed_cells: int = 0
    failed_cells: int = 0
    cancelled_cells: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.experiment_id, ExperimentId):
            object.__setattr__(self, "experiment_id", ExperimentId(str(self.experiment_id)))
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ConfigurationError(f"run_id must be a non-empty string, got {self.run_id!r}")
        if not isinstance(self.created_at, str) or not self.created_at.strip():
            raise ConfigurationError(f"created_at must be an ISO 8601 string, got {self.created_at!r}")
        if not isinstance(self.updated_at, str) or not self.updated_at.strip():
            raise ConfigurationError(f"updated_at must be an ISO 8601 string, got {self.updated_at!r}")
        if not isinstance(self.master_seed, int) or isinstance(self.master_seed, bool):
            raise ConfigurationError(f"master_seed must be an integer, got {self.master_seed!r}")
        if not isinstance(self.total_cells, int) or isinstance(self.total_cells, bool) or self.total_cells < 0:
            raise ConfigurationError(f"total_cells must be a non-negative integer, got {self.total_cells!r}")

        statuses_clean: dict[CellId, ExecutionStatus] = {}
        for k, v in self.cell_statuses.items():
            cid = CellId(str(k))
            stat = ExecutionStatus(v) if not isinstance(v, ExecutionStatus) else v
            statuses_clean[cid] = stat

        object.__setattr__(self, "cell_statuses", MappingProxyType(statuses_clean))

        n_comp = sum(1 for s in statuses_clean.values() if s == ExecutionStatus.COMPLETED)
        n_fail = sum(1 for s in statuses_clean.values() if s == ExecutionStatus.FAILED)
        n_canc = sum(1 for s in statuses_clean.values() if s == ExecutionStatus.CANCELLED)

        object.__setattr__(self, "completed_cells", n_comp)
        object.__setattr__(self, "failed_cells", n_fail)
        object.__setattr__(self, "cancelled_cells", n_canc)

    def with_cell_update(
        self,
        cell_id: CellId | str,
        status: ExecutionStatus,
        updated_at: str | None = None,
    ) -> MatrixExecutionState:
        """Return a new MatrixExecutionState with the updated status of cell_id."""
        cid = CellId(str(cell_id))
        new_statuses = dict(self.cell_statuses)
        new_statuses[cid] = status
        ts = updated_at or _utc_now_iso()

        return MatrixExecutionState(
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            created_at=self.created_at,
            updated_at=ts,
            master_seed=self.master_seed,
            total_cells=self.total_cells,
            cell_statuses=new_statuses,
        )


def matrix_execution_state_to_dict(state: MatrixExecutionState) -> dict[str, Any]:
    """Serialize MatrixExecutionState to a JSON-compatible dictionary."""
    return {
        "experiment_id": str(state.experiment_id),
        "run_id": state.run_id,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "master_seed": state.master_seed,
        "total_cells": state.total_cells,
        "completed_cells": state.completed_cells,
        "failed_cells": state.failed_cells,
        "cancelled_cells": state.cancelled_cells,
        "cell_statuses": {str(k): v.value for k, v in state.cell_statuses.items()},
    }


def matrix_execution_state_from_dict(d: dict[str, Any]) -> MatrixExecutionState:
    """Reconstruct MatrixExecutionState from a dictionary."""
    cell_statuses = {
        CellId(k): ExecutionStatus(v)
        for k, v in d.get("cell_statuses", {}).items()
    }

    return MatrixExecutionState(
        experiment_id=ExperimentId(d["experiment_id"]),
        run_id=str(d["run_id"]),
        created_at=str(d["created_at"]),
        updated_at=str(d["updated_at"]),
        master_seed=int(d["master_seed"]),
        total_cells=int(d["total_cells"]),
        cell_statuses=cell_statuses,
    )


def save_execution_state(
    state: MatrixExecutionState,
    run_dir: Path | str,
    *,
    overwrite: bool = True,
) -> Path:
    """Atomically save MatrixExecutionState to {run_dir}/execution_state.json.

    Args:
        state: The MatrixExecutionState to persist.
        run_dir: Base directory for the experiment run.
        overwrite: If False, raises ConfigurationError if destination already exists.

    Returns:
        Path to the saved execution_state.json file.
    """
    dest_path = Path(run_dir).resolve() / "execution_state.json"
    payload = matrix_execution_state_to_dict(state)
    write_json_atomic(dest_path, payload, overwrite=overwrite)
    return dest_path


def load_execution_state(run_dir: Path | str) -> MatrixExecutionState:
    """Load MatrixExecutionState from {run_dir}/execution_state.json.

    Args:
        run_dir: Base directory for the experiment run.

    Returns:
        Reconstructed MatrixExecutionState instance.

    Raises:
        ConfigurationError: If file is missing or corrupted.
    """
    state_path = Path(run_dir).resolve() / "execution_state.json"
    if not state_path.exists():
        raise ConfigurationError(f"Execution state file does not exist: '{state_path}'")

    try:
        raw_dict = read_json(state_path)
        return matrix_execution_state_from_dict(raw_dict)
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to load or parse execution state '{state_path}': {exc}"
        ) from exc
