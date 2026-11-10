"""Domain types and frozen data models for exploratory feature analysis.

Complies with EXP-01, EXP-07, CA-E2-01, ADR-005, ADR-007, and ADR-008.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from experimental_ml.core.enums import MetricStatus, TaskType
from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
)

SCOPE_EXPLORATORY_FULL_DATA: str = "EXPLORATORY_FULL_DATA"

METHODOLOGICAL_WARNINGS: tuple[str, ...] = (
    "Correlação não implica causalidade.",
    "Baixa correlação univariada não descarta relevância em interações multivariadas.",
    "Estatísticas calculadas sobre a base completa são estritamente exploratórias e não devem ser usadas para seleção enviesada de atributos pré-partição (prevenção de data leakage).",
)


def _safe_float_to_json(val: float) -> float | None:
    """Convert float to JSON-safe representation (RFC 8259 compliant)."""
    if math.isnan(val) or math.isinf(val):
        return None
    return float(val)


def _safe_float_from_json(val: float | None, status: MetricStatus) -> float:
    """Reconstruct float from JSON-safe representation."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return float("nan")
    return float(val)


@dataclass(frozen=True, slots=True)
class AssociationMeasure:
    """Immutable representation of an association metric between a feature and the target."""

    feature_name: str
    target_name: str
    metric_name: str
    value: float
    status: MetricStatus
    details: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.feature_name, str) or not self.feature_name.strip():
            raise ConfigurationError(
                f"feature_name must be a non-empty string, got {self.feature_name!r}"
            )
        object.__setattr__(self, "feature_name", self.feature_name.strip())

        if not isinstance(self.target_name, str) or not self.target_name.strip():
            raise ConfigurationError(
                f"target_name must be a non-empty string, got {self.target_name!r}"
            )
        object.__setattr__(self, "target_name", self.target_name.strip())

        if not isinstance(self.metric_name, str) or not self.metric_name.strip():
            raise ConfigurationError(
                f"metric_name must be a non-empty string, got {self.metric_name!r}"
            )
        object.__setattr__(self, "metric_name", self.metric_name.strip().upper())

        if not isinstance(self.status, MetricStatus):
            raise ConfigurationError(
                f"status must be an instance of MetricStatus, got {self.status!r}"
            )

        if not isinstance(self.details, MappingProxyType):
            object.__setattr__(self, "details", MappingProxyType(dict(self.details)))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compliant primitive dictionary."""
        return {
            "feature_name": self.feature_name,
            "target_name": self.target_name,
            "metric_name": self.metric_name,
            "value": _safe_float_to_json(self.value),
            "status": self.status.value,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AssociationMeasure:
        """Reconstruct from dictionary representation."""
        status = MetricStatus(data["status"])
        val = _safe_float_from_json(data.get("value"), status)
        return cls(
            feature_name=data["feature_name"],
            target_name=data["target_name"],
            metric_name=data["metric_name"],
            value=val,
            status=status,
            details=MappingProxyType(dict(data.get("details", {}))),
        )


@dataclass(frozen=True, slots=True)
class RedundancyPair:
    """Immutable representation of pairwise association between two predictor features."""

    feature_a: str
    feature_b: str
    metric_name: str
    value: float
    status: MetricStatus

    def __post_init__(self) -> None:
        if not isinstance(self.feature_a, str) or not self.feature_a.strip():
            raise ConfigurationError(
                f"feature_a must be a non-empty string, got {self.feature_a!r}"
            )
        object.__setattr__(self, "feature_a", self.feature_a.strip())

        if not isinstance(self.feature_b, str) or not self.feature_b.strip():
            raise ConfigurationError(
                f"feature_b must be a non-empty string, got {self.feature_b!r}"
            )
        object.__setattr__(self, "feature_b", self.feature_b.strip())

        if not isinstance(self.metric_name, str) or not self.metric_name.strip():
            raise ConfigurationError(
                f"metric_name must be a non-empty string, got {self.metric_name!r}"
            )
        object.__setattr__(self, "metric_name", self.metric_name.strip().upper())

        if not isinstance(self.status, MetricStatus):
            raise ConfigurationError(
                f"status must be an instance of MetricStatus, got {self.status!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compliant primitive dictionary."""
        return {
            "feature_a": self.feature_a,
            "feature_b": self.feature_b,
            "metric_name": self.metric_name,
            "value": _safe_float_to_json(self.value),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RedundancyPair:
        """Reconstruct from dictionary representation."""
        status = MetricStatus(data["status"])
        val = _safe_float_from_json(data.get("value"), status)
        return cls(
            feature_a=data["feature_a"],
            feature_b=data["feature_b"],
            metric_name=data["metric_name"],
            value=val,
            status=status,
        )


@dataclass(frozen=True, slots=True)
class ExploratoryFeatureReport:
    """Immutable report containing exploratory feature associations, redundancy, and warnings."""

    scope: str
    dataset_hash: str
    task_type: TaskType
    target_associations: tuple[AssociationMeasure, ...]
    pairwise_redundancy_matrix: Mapping[str, Mapping[str, float | None]]
    high_redundancy_pairs: tuple[RedundancyPair, ...]
    warnings: tuple[str, ...] = METHODOLOGICAL_WARNINGS
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if self.scope != SCOPE_EXPLORATORY_FULL_DATA:
            raise ConfigurationError(
                f"Invalid scope {self.scope!r}. Only {SCOPE_EXPLORATORY_FULL_DATA!r} is permitted (CA-E2-01)."
            )

        if not isinstance(self.dataset_hash, str) or not self.dataset_hash.strip():
            raise ConfigurationError("dataset_hash must be a non-empty string.")

        if not isinstance(self.task_type, TaskType):
            raise ConfigurationError(
                f"task_type must be an instance of TaskType, got {self.task_type!r}"
            )

        if not isinstance(self.target_associations, tuple):
            object.__setattr__(self, "target_associations", tuple(self.target_associations))

        if not isinstance(self.high_redundancy_pairs, tuple):
            object.__setattr__(self, "high_redundancy_pairs", tuple(self.high_redundancy_pairs))

        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(self.warnings))

        # Enforce nested immutable mapping for pairwise_redundancy_matrix
        if not isinstance(self.pairwise_redundancy_matrix, MappingProxyType):
            frozen_matrix: dict[str, MappingProxyType] = {}
            for k, sub_dict in self.pairwise_redundancy_matrix.items():
                frozen_matrix[k] = MappingProxyType(dict(sub_dict))
            object.__setattr__(self, "pairwise_redundancy_matrix", MappingProxyType(frozen_matrix))

        if not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compliant primitive dictionary."""
        # Convert nested matrix to plain dicts with safe floats
        matrix_dict: dict[str, dict[str, float | None]] = {}
        for feat_a, row in self.pairwise_redundancy_matrix.items():
            matrix_dict[feat_a] = {
                feat_b: _safe_float_to_json(val) if val is not None else None
                for feat_b, val in row.items()
            }

        return {
            "scope": self.scope,
            "dataset_hash": self.dataset_hash,
            "task_type": self.task_type.value,
            "target_associations": [assoc.to_dict() for assoc in self.target_associations],
            "pairwise_redundancy_matrix": matrix_dict,
            "high_redundancy_pairs": [pair.to_dict() for pair in self.high_redundancy_pairs],
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExploratoryFeatureReport:
        """Reconstruct from dictionary representation."""
        task_type = TaskType(data["task_type"])
        target_associations = tuple(
            AssociationMeasure.from_dict(item) for item in data.get("target_associations", [])
        )
        high_redundancy_pairs = tuple(
            RedundancyPair.from_dict(item) for item in data.get("high_redundancy_pairs", [])
        )

        matrix_raw = data.get("pairwise_redundancy_matrix", {})
        frozen_matrix: dict[str, MappingProxyType] = {}
        for feat_a, row in matrix_raw.items():
            row_dict: dict[str, float | None] = {}
            for feat_b, val in row.items():
                if val is None:
                    row_dict[feat_b] = None
                elif math.isnan(val):
                    row_dict[feat_b] = float("nan")
                else:
                    row_dict[feat_b] = float(val)
            frozen_matrix[feat_a] = MappingProxyType(row_dict)

        return cls(
            scope=data["scope"],
            dataset_hash=data["dataset_hash"],
            task_type=task_type,
            target_associations=target_associations,
            pairwise_redundancy_matrix=MappingProxyType(frozen_matrix),
            high_redundancy_pairs=high_redundancy_pairs,
            warnings=tuple(data.get("warnings", METHODOLOGICAL_WARNINGS)),
            metadata=MappingProxyType(dict(data.get("metadata", {}))),
        )


__all__ = [
    "SCOPE_EXPLORATORY_FULL_DATA",
    "METHODOLOGICAL_WARNINGS",
    "AssociationMeasure",
    "RedundancyPair",
    "ExploratoryFeatureReport",
]
