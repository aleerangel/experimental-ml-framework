"""Core module for Experimental ML Framework (Nível 0).

Provides domain identifiers, fundamental enumerations, deterministic seed derivation,
canonical configuration and tabular dataset hashing, and diagnostic finding structures
(RNF01, RNF06, RNF07, ADR-002, ADR-007, ADR-008).
"""

from __future__ import annotations

from experimental_ml.core.enums import (
    AggregationScope,
    ErrorPolicy,
    ExecutionStatus,
    FindingSeverity,
    MetricDirection,
    MetricStatus,
    TaskType,
)
from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
    ExperimentalMLError,
    Finding,
    make_finding,
    make_warning,
)
from experimental_ml.core.types import (
    ArtifactId,
    CellId,
    ComparisonId,
    ExperimentId,
    ModelId,
    ObservationId,
    PartitionPlanId,
    ScenarioId,
)

_LAZY_EXPORTS: dict[str, str] = {
    # Deterministic Seed Derivation
    "derive_seeds": "experimental_ml.core.seeds",
    "spawn_child_seeds": "experimental_ml.core.seeds",
    # Canonical Hashing & Scalar Missingness
    "config_hash": "experimental_ml.core.hashing",
    "dataset_hash": "experimental_ml.core.hashing",
    "is_nan_scalar": "experimental_ml.core.hashing",
    "is_missing_scalar": "experimental_ml.core.hashing",
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_EXPORTS:
        mod = __import__(_LAZY_EXPORTS[name], fromlist=[name])
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Domain Identifiers
    "ExperimentId",
    "PartitionPlanId",
    "ScenarioId",
    "ModelId",
    "CellId",
    "ComparisonId",
    "ArtifactId",
    "ObservationId",
    # Fundamental Enums
    "TaskType",
    "ExecutionStatus",
    "FindingSeverity",
    "MetricDirection",
    "AggregationScope",
    "MetricStatus",
    "ErrorPolicy",
    # Diagnostic Findings and Exceptions
    "Finding",
    "make_finding",
    "make_warning",
    "ExperimentalMLError",
    "ContractViolationError",
    "DataIntegrityError",
    "ConfigurationError",
    # Deterministic Seed Derivation
    "derive_seeds",
    "spawn_child_seeds",
    # Canonical Hashing & Scalar Missingness
    "config_hash",
    "dataset_hash",
    "is_nan_scalar",
    "is_missing_scalar",
]

