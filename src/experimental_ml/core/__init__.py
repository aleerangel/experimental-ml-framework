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
from experimental_ml.core.hashing import config_hash, dataset_hash
from experimental_ml.core.seeds import derive_seeds, spawn_child_seeds
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
    # Canonical Hashing
    "config_hash",
    "dataset_hash",
]

