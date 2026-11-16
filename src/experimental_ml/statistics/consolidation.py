"""Consolidation and descriptive statistics module (STAT-02, STAT-03, CA-E5-01).

Implements Stage 4B -> Stage 5 gate validation (validate_stage5_entry) and
descriptive consolidation (consolidate_descriptive).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experimental_ml.core.enums import ExecutionStatus
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.orchestration.state import (
    MatrixExecutionState,
    load_execution_state,
    matrix_execution_state_from_dict,
)


def validate_stage5_entry(
    execution_state_or_target: MatrixExecutionState | Path | str | dict[str, Any],
) -> None:
    """Validate prerequisites before entering Stage 5 (STAT-02, CA-E5-01).

    Args:
        execution_state_or_target: A MatrixExecutionState instance, run directory/file path,
            or dictionary.

    Raises:
        ContractViolationError: If execution_state.json is missing or corrupted,
            if any cell has non-terminal status (PENDING or RUNNING),
            or if completed_cells == 0.
    """
    state: MatrixExecutionState
    if isinstance(execution_state_or_target, MatrixExecutionState):
        state = execution_state_or_target
    elif isinstance(execution_state_or_target, (str, Path)):
        target_path = Path(execution_state_or_target).resolve()
        state_file: Path
        if target_path.is_file() and target_path.name == "execution_state.json":
            state_file = target_path
            run_dir = target_path.parent
        elif (target_path / "execution_state.json").exists():
            state_file = target_path / "execution_state.json"
            run_dir = target_path
        elif (target_path / "runs" / "execution_state.json").exists():
            state_file = target_path / "runs" / "execution_state.json"
            run_dir = target_path / "runs"
        else:
            raise ContractViolationError(
                f"execution_state.json missing or unreadable at '{target_path}'"
            )

        try:
            state = load_execution_state(run_dir)
        except Exception as exc:
            raise ContractViolationError(
                f"Failed to parse execution state from '{state_file}': {exc}"
            ) from exc
    elif isinstance(execution_state_or_target, dict):
        try:
            state = matrix_execution_state_from_dict(execution_state_or_target)
        except Exception as exc:
            raise ContractViolationError(
                f"Failed to parse execution state dictionary: {exc}"
            ) from exc
    else:
        raise ContractViolationError(
            f"Unsupported execution state target type: {type(execution_state_or_target).__name__}"
        )

    # 1. Non-terminal cells check (PENDING or RUNNING)
    non_terminal = [
        cid
        for cid, status in state.cell_statuses.items()
        if status in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING)
    ]
    if non_terminal:
        raise ContractViolationError(
            f"Execution contains {len(non_terminal)} non-terminal cell(s) (PENDING or RUNNING): {non_terminal}. "
            "Execution is in progress and must be completed or resumed before Stage 5."
        )

    # 2. At least one completed cell required
    if state.completed_cells == 0:
        raise ContractViolationError(
            f"Matrix execution contains zero completed cells ({state.completed_cells}/{state.total_cells}). "
            "At least one completed cell is required for Stage 5 consolidation."
        )
