"""Domain types and immutable data structures for tabular datasets.

Defines ColumnDescriptor and DatasetBundle compliant with ADR-007 and ADR-008.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
import numpy as np

from experimental_ml.core.findings import ConfigurationError, DataIntegrityError
from experimental_ml.core.types import ObservationId
from experimental_ml.data.schema import ColumnSemanticType, DatasetSchemaSpec


VALID_ROLES: tuple[str, ...] = (
    "target",
    "group",
    "observation_id",
    "time",
    "ignored",
    "feature",
)


@dataclass(frozen=True, slots=True)
class ColumnDescriptor:
    """Metadata describing a single tabular column's physical and semantic properties.

    Complies with ADR-008:
    - Immutable frozen dataclass with slots.
    - Explicit separation between physical representation and semantic meaning.
    """

    name: str
    index: int
    role: str
    physical_type: str
    semantic_type: ColumnSemanticType
    is_semantic_declared: bool
    n_missing: int
    memory_bytes: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ConfigurationError("ColumnDescriptor name must be a non-empty string")
        if not isinstance(self.index, int) or self.index < 0:
            raise ConfigurationError(f"ColumnDescriptor index must be a non-negative int, got {self.index}")
        if self.role not in VALID_ROLES:
            raise ConfigurationError(
                f"ColumnDescriptor role '{self.role}' must be one of {VALID_ROLES}"
            )
        if not isinstance(self.semantic_type, ColumnSemanticType):
            raise ConfigurationError(
                f"ColumnDescriptor semantic_type must be ColumnSemanticType, got {self.semantic_type}"
            )
        if not isinstance(self.is_semantic_declared, bool):
            raise ConfigurationError("ColumnDescriptor is_semantic_declared must be a boolean")
        if not isinstance(self.n_missing, int) or self.n_missing < 0:
            raise ConfigurationError(f"ColumnDescriptor n_missing must be >= 0, got {self.n_missing}")
        if not isinstance(self.memory_bytes, int) or self.memory_bytes < 0:
            raise ConfigurationError(f"ColumnDescriptor memory_bytes must be >= 0, got {self.memory_bytes}")


@dataclass(frozen=True, slots=True)
class DatasetBundle:
    """Immutable tabular dataset container with deep memory isolation and data ownership.

    Complies with ADR-007, ADR-008, RF1.1 and RF1.7:
    - Immutable frozen dataclass with slots.
    - Encapsulated read-only mapping proxies for columns and descriptors.
    - Deep buffer-level array immutability for numerical and boolean columns.
    - Tripartite audit hashes (dataset_hash, raw_source_hash, schema_hash).
    - Positional or intrinsic ObservationId tracking for every observation.
    """

    schema: DatasetSchemaSpec
    n_rows: int
    n_cols: int
    column_names: tuple[str, ...]
    feature_cols: tuple[str, ...]
    columns: Mapping[str, np.ndarray]
    descriptors: Mapping[str, ColumnDescriptor]
    observation_ids: tuple[ObservationId, ...]
    dataset_hash: str
    raw_source_hash: str
    schema_hash: str
    memory_bytes: int
    source_path: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.schema, DatasetSchemaSpec):
            raise ConfigurationError(
                f"DatasetBundle schema must be DatasetSchemaSpec, got {type(self.schema).__name__}"
            )
        if not isinstance(self.n_rows, int) or self.n_rows < 0:
            raise DataIntegrityError(f"DatasetBundle n_rows must be >= 0, got {self.n_rows}")
        if not isinstance(self.n_cols, int) or self.n_cols < 0:
            raise DataIntegrityError(f"DatasetBundle n_cols must be >= 0, got {self.n_cols}")

        # Ensure tuples
        if not isinstance(self.column_names, tuple):
            object.__setattr__(self, "column_names", tuple(self.column_names))
        if not isinstance(self.feature_cols, tuple):
            object.__setattr__(self, "feature_cols", tuple(self.feature_cols))
        if not isinstance(self.observation_ids, tuple):
            object.__setattr__(self, "observation_ids", tuple(self.observation_ids))

        # Encapsulate mappings as MappingProxyType
        if not isinstance(self.columns, MappingProxyType):
            object.__setattr__(self, "columns", MappingProxyType(dict(self.columns)))
        if not isinstance(self.descriptors, MappingProxyType):
            object.__setattr__(self, "descriptors", MappingProxyType(dict(self.descriptors)))
