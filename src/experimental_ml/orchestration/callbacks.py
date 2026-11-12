"""Observability callbacks for experiment matrix execution.

Complies with ORCH-14 and XCUT-02.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from experimental_ml.orchestration.state import MatrixExecutionState
from experimental_ml.orchestration.types import CellId, CellResultRecord


@runtime_checkable
class MatrixProgressCallback(Protocol):
    """Protocol for decoupled progress notification during matrix execution."""

    def on_matrix_start(self, total_cells: int) -> None:
        """Called once before starting the matrix execution."""
        ...

    def on_cell_start(self, cell_id: CellId) -> None:
        """Called when a cell execution begins."""
        ...

    def on_cell_completed(self, cell_result: CellResultRecord) -> None:
        """Called when a cell completes successfully."""
        ...

    def on_cell_failed(self, cell_result: CellResultRecord) -> None:
        """Called when a cell execution fails."""
        ...

    def on_cell_skipped(self, cell_id: CellId) -> None:
        """Called when a cell is skipped during resume."""
        ...

    def on_matrix_completed(self, state: MatrixExecutionState) -> None:
        """Called once when the entire matrix or remaining cells finish."""
        ...


class NullProgressCallback:
    """Default no-op implementation of MatrixProgressCallback."""

    def on_matrix_start(self, total_cells: int) -> None:
        pass

    def on_cell_start(self, cell_id: CellId) -> None:
        pass

    def on_cell_completed(self, cell_result: CellResultRecord) -> None:
        pass

    def on_cell_failed(self, cell_result: CellResultRecord) -> None:
        pass

    def on_cell_skipped(self, cell_id: CellId) -> None:
        pass

    def on_matrix_completed(self, state: MatrixExecutionState) -> None:
        pass
