"""Matrix execution orchestration module for experimental-ml-framework.

Complies with ORCH-01 through ORCH-14, XCUT-02, and ADR-008.
"""

from __future__ import annotations

from experimental_ml.orchestration.callbacks import (
    MatrixProgressCallback,
    NullProgressCallback,
)
from experimental_ml.orchestration.codecs import (
    cell_result_from_dict,
    cell_result_to_dict,
    metric_value_from_dict,
    metric_value_to_dict,
    prediction_record_from_dict,
    prediction_record_to_dict,
    timing_breakdown_from_dict,
    timing_breakdown_to_dict,
)
from experimental_ml.orchestration.engine import (
    resume_experiment_matrix,
    run_experiment_matrix,
)
from experimental_ml.orchestration.execution import execute_single_cell
from experimental_ml.orchestration.matrix import (
    CellDescriptor,
    build_cell_matrix,
    derive_cell_seed,
)
from experimental_ml.orchestration.state import (
    MatrixExecutionState,
    load_execution_state,
    matrix_execution_state_from_dict,
    matrix_execution_state_to_dict,
    save_execution_state,
)
from experimental_ml.orchestration.storage import load_cell_artifacts, save_cell_artifacts
from experimental_ml.orchestration.types import (
    CellId,
    CellPhase,
    CellResultRecord,
    ErrorPolicy,
    ExecutionStatus,
    PredictionRecord,
    TimingBreakdown,
)

__all__ = [
    # Enums
    "ExecutionStatus",
    "ErrorPolicy",
    "CellPhase",
    # Data contracts
    "CellId",
    "TimingBreakdown",
    "PredictionRecord",
    "CellResultRecord",
    # Single-cell execution
    "execute_single_cell",
    # Codecs
    "cell_result_to_dict",
    "cell_result_from_dict",
    "prediction_record_to_dict",
    "prediction_record_from_dict",
    "metric_value_to_dict",
    "metric_value_from_dict",
    "timing_breakdown_to_dict",
    "timing_breakdown_from_dict",
    # Single-cell storage
    "save_cell_artifacts",
    "load_cell_artifacts",
    # Matrix formulation
    "CellDescriptor",
    "derive_cell_seed",
    "build_cell_matrix",
    # Matrix execution state & codecs
    "MatrixExecutionState",
    "matrix_execution_state_to_dict",
    "matrix_execution_state_from_dict",
    "save_execution_state",
    "load_execution_state",
    # Matrix callbacks
    "MatrixProgressCallback",
    "NullProgressCallback",
    # Matrix engine
    "run_experiment_matrix",
    "resume_experiment_matrix",
]
