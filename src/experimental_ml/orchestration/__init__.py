"""Matrix execution orchestration module for experimental-ml-framework.

Complies with ORCH-01 through ORCH-08, XCUT-02, and ADR-008.
"""

from __future__ import annotations

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
from experimental_ml.orchestration.execution import execute_single_cell
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
    # Execution
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
    # Storage
    "save_cell_artifacts",
    "load_cell_artifacts",
]
