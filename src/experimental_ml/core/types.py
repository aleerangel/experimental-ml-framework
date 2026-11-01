"""Immutable domain identifiers and types for experimental-ml-framework."""

from __future__ import annotations


class DomainIdentifier(str):
    """Base immutable domain identifier ensuring non-empty stripped strings."""

    def __new__(cls, value: str) -> DomainIdentifier:
        if not isinstance(value, str):
            raise ValueError(f"{cls.__name__} must be a string, got {type(value).__name__}")
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"{cls.__name__} cannot be empty or purely whitespace")
        if any(c in stripped for c in ("\n", "\r", "\t")):
            raise ValueError(f"{cls.__name__} cannot contain newline or tab characters: {value!r}")
        return super().__new__(cls, stripped)


class ExperimentId(DomainIdentifier):
    """Unique identifier for an overall experiment."""


class PartitionPlanId(DomainIdentifier):
    """Unique identifier for a partition plan."""


class ScenarioId(DomainIdentifier):
    """Unique identifier for a feature scenario."""


class ModelId(DomainIdentifier):
    """Unique identifier for a model specification."""


class CellId(DomainIdentifier):
    """Unique identifier for an execution matrix cell."""


class ComparisonId(DomainIdentifier):
    """Unique identifier for a statistical comparison."""


class ArtifactId(DomainIdentifier):
    """Unique identifier for an exported artifact."""


class ObservationId(DomainIdentifier):
    """Unique identifier for a dataset observation row."""


__all__ = [
    "DomainIdentifier",
    "ExperimentId",
    "PartitionPlanId",
    "ScenarioId",
    "ModelId",
    "CellId",
    "ComparisonId",
    "ArtifactId",
    "ObservationId",
]

