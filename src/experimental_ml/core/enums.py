"""Fundamental domain enumerations for experimental-ml-framework."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """String-compatible enumeration base class."""

    def __str__(self) -> str:
        return str(self.value)


class TaskType(StrEnum):
    """Supported predictive task types."""

    REGRESSION = "REGRESSION"
    MULTI_TARGET_REGRESSION = "MULTI_TARGET_REGRESSION"
    BINARY_CLASSIFICATION = "BINARY_CLASSIFICATION"
    MULTICLASS_CLASSIFICATION = "MULTICLASS_CLASSIFICATION"


class ExecutionStatus(StrEnum):
    """Lifecycle execution status of cells and experiments."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FindingSeverity(StrEnum):
    """Severity classification for diagnostics and findings."""

    CONFIRMED_ISSUE = "CONFIRMED_ISSUE"
    HEURISTIC_WARNING = "HEURISTIC_WARNING"


class MetricDirection(StrEnum):
    """Optimization direction for metric evaluation."""

    MAXIMIZE = "MAXIMIZE"
    MINIMIZE = "MINIMIZE"


class AggregationScope(StrEnum):
    """Scope level for metric aggregation."""

    FOLD_AGGREGATION = "FOLD_AGGREGATION"
    REPETITION_AGGREGATION = "REPETITION_AGGREGATION"
    OVERALL_AGGREGATION = "OVERALL_AGGREGATION"


class MetricStatus(StrEnum):
    """Status classification for computed metric values."""

    VALID = "VALID"
    UNDEFINED_NAN = "UNDEFINED_NAN"
    PARTIAL_COVERAGE = "PARTIAL_COVERAGE"
    UNRANKABLE = "UNRANKABLE"


class ErrorPolicy(StrEnum):
    """Fault tolerance policy for experiment matrix execution."""

    FAULT_TOLERANT = "FAULT_TOLERANT"
    FAIL_FAST = "FAIL_FAST"


__all__ = [
    "StrEnum",
    "TaskType",
    "ExecutionStatus",
    "FindingSeverity",
    "MetricDirection",
    "AggregationScope",
    "MetricStatus",
    "ErrorPolicy",
]

