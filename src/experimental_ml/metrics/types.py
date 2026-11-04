"""Domain types, frozen evaluation records, and evaluation scopes for experimental_ml.metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from experimental_ml.core.enums import (
    AggregationScope,
    MetricDirection,
    MetricStatus,
    StrEnum,
    TaskType,
)
from experimental_ml.core.findings import ConfigurationError, Finding


class MetricEvaluationScope(StrEnum):
    """Evaluation scope levels for metrics computation."""

    PER_FOLD = "PER_FOLD"
    FOLD_AGGREGATION = "FOLD_AGGREGATION"
    POOLED_OOF = "POOLED_OOF"
    FINAL_HOLDOUT = "FINAL_HOLDOUT"


def _validate_scope_value(
    scope: Any,
    allowed_types: tuple[type, ...],
    allowed_values: tuple[str, ...],
    error_context: str,
) -> Any:
    """Validate and coerce a scope object or canonical string."""
    if isinstance(scope, allowed_types):
        return scope
    if isinstance(scope, str):
        val = scope.strip()
        for cls in allowed_types:
            for member in cls:
                if member.value == val or member.name == val:
                    return member
    raise ConfigurationError(
        f"Invalid scope for {error_context}: {scope!r}. Allowed scopes: {list(allowed_values)}"
    )


@dataclass(frozen=True, slots=True)
class MetricValue:
    """Immutable evaluation record for an atomic metric computation."""

    metric_id: str
    value: float
    status: MetricStatus
    direction: MetricDirection
    scope: MetricEvaluationScope | AggregationScope
    n_samples: int
    warnings: tuple[Finding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.metric_id, str) or not self.metric_id.strip():
            raise ConfigurationError(f"metric_id must be a non-empty string, got {self.metric_id!r}")
        object.__setattr__(self, "metric_id", self.metric_id.strip().lower())

        validated_scope = _validate_scope_value(
            self.scope,
            (MetricEvaluationScope, AggregationScope),
            tuple(m.value for m in MetricEvaluationScope) + tuple(m.value for m in AggregationScope),
            "MetricValue",
        )
        object.__setattr__(self, "scope", validated_scope)

        if not isinstance(self.status, MetricStatus):
            raise ConfigurationError(f"status must be an instance of MetricStatus, got {self.status!r}")

        if not isinstance(self.direction, MetricDirection):
            raise ConfigurationError(f"direction must be an instance of MetricDirection, got {self.direction!r}")

        if not isinstance(self.n_samples, int) or isinstance(self.n_samples, bool) or self.n_samples < 0:
            raise ConfigurationError(f"n_samples must be a non-negative integer, got {self.n_samples!r}")

        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True, slots=True)
class AggregatedMetricValue:
    """Immutable summary record for metrics aggregated across multiple folds/partitions."""

    metric_id: str
    mean: float
    std: float
    median: float
    iqr: float
    status: MetricStatus
    direction: MetricDirection
    scope: AggregationScope | MetricEvaluationScope
    valid_folds: int
    total_folds: int
    coverage: float
    fold_values: tuple[MetricValue, ...] = ()
    warnings: tuple[Finding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.metric_id, str) or not self.metric_id.strip():
            raise ConfigurationError(f"metric_id must be a non-empty string, got {self.metric_id!r}")
        object.__setattr__(self, "metric_id", self.metric_id.strip().lower())

        allowed_scopes = (
            AggregationScope.FOLD_AGGREGATION,
            AggregationScope.REPETITION_AGGREGATION,
            AggregationScope.OVERALL_AGGREGATION,
            MetricEvaluationScope.FOLD_AGGREGATION,
        )
        validated_scope = _validate_scope_value(
            self.scope,
            (AggregationScope,),
            tuple(m.value for m in AggregationScope),
            "AggregatedMetricValue",
        )
        object.__setattr__(self, "scope", validated_scope)

        if not isinstance(self.status, MetricStatus):
            raise ConfigurationError(f"status must be an instance of MetricStatus, got {self.status!r}")

        if not isinstance(self.direction, MetricDirection):
            raise ConfigurationError(f"direction must be an instance of MetricDirection, got {self.direction!r}")

        if not isinstance(self.fold_values, tuple):
            object.__setattr__(self, "fold_values", tuple(self.fold_values))

        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True, slots=True)
class MetricSpec:
    """Formal specification and metadata descriptor for a registered metric in METRICS_CATALOG."""

    metric_id: str
    name: str
    family: str
    direction: MetricDirection
    compare_by_abs: bool
    supported_tasks: tuple[TaskType, ...]
    func: Callable[..., MetricValue]
    rtol: float
    atol: float
    requires_probabilities: bool = False
    requires_kernel_matrix: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.metric_id, str) or not self.metric_id.strip():
            raise ConfigurationError(f"metric_id must be a non-empty string, got {self.metric_id!r}")
        object.__setattr__(self, "metric_id", self.metric_id.strip().lower())

        if not isinstance(self.supported_tasks, tuple):
            object.__setattr__(self, "supported_tasks", tuple(self.supported_tasks))


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    """Ordered candidate representation resulting from metric ranking."""

    candidate_id: str
    metric: MetricValue | AggregatedMetricValue
    rank: int | None
    status: MetricStatus


__all__ = [
    "MetricEvaluationScope",
    "MetricValue",
    "AggregatedMetricValue",
    "MetricSpec",
    "RankedCandidate",
]
