"""Orchestration domain types, enumerations, and immutable data structures (Stage 4B).

Complies with ORCH-01, ORCH-02, ORCH-03, ORCH-04, CA-E4B-01, CA-E4B-02, and ADR-008.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from experimental_ml.core.enums import ExecutionStatus
from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.core.types import (
    ExperimentId,
    ModelId,
    ObservationId,
    PartitionPlanId,
    ScenarioId,
)
from experimental_ml.metrics.types import MetricValue
from experimental_ml.models.types import ModelDiagnostics


class ErrorPolicy(str, Enum):
    """Policies governing failure handling during matrix execution."""

    FAULT_TOLERANT = "FAULT_TOLERANT"
    FAIL_FAST = "FAIL_FAST"


class CellPhase(str, Enum):
    """Sub-phases of an individual experimental cell lifecycle."""

    DATA_EXTRACTION = "DATA_EXTRACTION"
    FEATURE_SELECTION = "FEATURE_SELECTION"
    PREPROCESSING_L1 = "PREPROCESSING_L1"
    HYPERPARAMETER_TUNING = "HYPERPARAMETER_TUNING"
    PREPROCESSING_L2 = "PREPROCESSING_L2"
    MODEL_FIT = "MODEL_FIT"
    PREDICTION = "PREDICTION"
    METRIC_COMPUTATION = "METRIC_COMPUTATION"


class CellId(str):
    """Immutable identifier for an experimental cell: cell_{model_id}_{scenario_id}_{fold_id}."""

    _PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    def __new__(cls, value: str) -> CellId:
        if not isinstance(value, str):
            raise ConfigurationError(f"CellId must be a string, got {type(value).__name__}")
        trimmed = value.strip()
        if not trimmed:
            raise ConfigurationError("CellId cannot be empty or pure whitespace")
        if not cls._PATTERN.match(trimmed):
            raise ConfigurationError(
                f"CellId contains invalid characters: '{value}' (expected regex ^[a-zA-Z0-9_-]+$)"
            )
        return super().__new__(cls, trimmed)


@dataclass(frozen=True, slots=True)
class TimingBreakdown:
    """Disaggregated timing measurements in seconds for each phase of cell execution."""

    data_extraction_time_s: float = 0.0
    feature_selection_time_s: float = 0.0
    tuning_time_s: float = 0.0
    preprocessing_time_s: float = 0.0
    fit_time_s: float = 0.0
    predict_time_s: float = 0.0
    evaluation_time_s: float = 0.0
    total_cell_time_s: float = 0.0

    def __post_init__(self) -> None:
        fields = (
            ("data_extraction_time_s", self.data_extraction_time_s),
            ("feature_selection_time_s", self.feature_selection_time_s),
            ("tuning_time_s", self.tuning_time_s),
            ("preprocessing_time_s", self.preprocessing_time_s),
            ("fit_time_s", self.fit_time_s),
            ("predict_time_s", self.predict_time_s),
            ("evaluation_time_s", self.evaluation_time_s),
            ("total_cell_time_s", self.total_cell_time_s),
        )
        for name, val in fields:
            if not isinstance(val, (int, float)) or val < 0.0:
                raise ContractViolationError(
                    f"TimingBreakdown field '{name}' must be a non-negative float, got {val}"
                )
            object.__setattr__(self, name, float(val))


@dataclass(frozen=True, slots=True)
class PredictionRecord:
    """Immutable record of out-of-fold or evaluation predictions for an individual cell."""

    cell_id: CellId
    observation_ids: tuple[ObservationId, ...]
    y_true: tuple[float, ...]
    y_pred: tuple[float, ...]
    y_std: tuple[float, ...] | None = None
    y_proba: tuple[tuple[float, ...], ...] | None = None
    residuals: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.cell_id, CellId):
            object.__setattr__(self, "cell_id", CellId(str(self.cell_id)))

        obs = tuple(ObservationId(str(o)) for o in self.observation_ids)
        y_t = tuple(float(y) for y in self.y_true)
        y_p = tuple(float(y) for y in self.y_pred)

        n = len(obs)
        if n == 0:
            raise ContractViolationError("PredictionRecord cannot be empty (n_samples must be > 0)")
        if len(y_t) != n:
            raise ContractViolationError(
                f"PredictionRecord y_true length ({len(y_t)}) does not match observation_ids ({n})"
            )
        if len(y_p) != n:
            raise ContractViolationError(
                f"PredictionRecord y_pred length ({len(y_p)}) does not match observation_ids ({n})"
            )

        object.__setattr__(self, "observation_ids", obs)
        object.__setattr__(self, "y_true", y_t)
        object.__setattr__(self, "y_pred", y_p)

        if self.y_std is not None:
            y_s = tuple(float(s) for s in self.y_std)
            if len(y_s) != n:
                raise ContractViolationError(
                    f"PredictionRecord y_std length ({len(y_s)}) does not match observation_ids ({n})"
                )
            object.__setattr__(self, "y_std", y_s)

        if self.y_proba is not None:
            proba_tuples = tuple(tuple(float(p) for p in row) for row in self.y_proba)
            if len(proba_tuples) != n:
                raise ContractViolationError(
                    f"PredictionRecord y_proba length ({len(proba_tuples)}) does not match observation_ids ({n})"
                )
            object.__setattr__(self, "y_proba", proba_tuples)

        if self.residuals is not None:
            res = tuple(float(r) for r in self.residuals)
            if len(res) != n:
                raise ContractViolationError(
                    f"PredictionRecord residuals length ({len(res)}) does not match observation_ids ({n})"
                )
            object.__setattr__(self, "residuals", res)


@dataclass(frozen=True, slots=True)
class CellResultRecord:
    """Immutable record consolidating the complete outcome of an experimental cell."""

    cell_id: CellId
    experiment_id: ExperimentId
    partition_plan_id: PartitionPlanId
    model_id: ModelId
    scenario_id: ScenarioId
    fold_id: str
    timing: TimingBreakdown
    phase: str = "DEV_CV"
    status: ExecutionStatus = ExecutionStatus.COMPLETED
    selected_features: tuple[str, ...] = field(default_factory=tuple)
    effective_parameters: Mapping[str, Any] = field(default_factory=dict)
    metrics: Mapping[str, MetricValue] = field(default_factory=dict)
    diagnostics: ModelDiagnostics | None = None
    error_type: str | None = None
    error_message: str | None = None
    error_phase: CellPhase | None = None
    error_traceback: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.cell_id, CellId):
            object.__setattr__(self, "cell_id", CellId(str(self.cell_id)))
        if not isinstance(self.experiment_id, ExperimentId):
            object.__setattr__(self, "experiment_id", ExperimentId(str(self.experiment_id)))
        if not isinstance(self.partition_plan_id, PartitionPlanId):
            object.__setattr__(self, "partition_plan_id", PartitionPlanId(str(self.partition_plan_id)))
        if not isinstance(self.model_id, ModelId):
            object.__setattr__(self, "model_id", ModelId(str(self.model_id)))
        if not isinstance(self.scenario_id, ScenarioId):
            object.__setattr__(self, "scenario_id", ScenarioId(str(self.scenario_id)))

        if not isinstance(self.selected_features, tuple):
            object.__setattr__(self, "selected_features", tuple(str(f) for f in self.selected_features))

        if not isinstance(self.effective_parameters, MappingProxyType):
            object.__setattr__(
                self,
                "effective_parameters",
                MappingProxyType(dict(self.effective_parameters)),
            )

        if not isinstance(self.metrics, MappingProxyType):
            object.__setattr__(
                self,
                "metrics",
                MappingProxyType(dict(self.metrics)),
            )

        if not isinstance(self.status, ExecutionStatus):
            object.__setattr__(self, "status", ExecutionStatus(self.status))

        if self.error_phase is not None and not isinstance(self.error_phase, CellPhase):
            object.__setattr__(self, "error_phase", CellPhase(self.error_phase))
