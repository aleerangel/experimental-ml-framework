"""Dataset profiling and diagnostic finding engine.

Implements structural profiling, distribution statistics, target/group diagnostics,
and closed findings catalog evaluation for Stage 1.
Complies with ADR-002, ADR-007, ADR-008, and RNF07.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from experimental_ml.core.enums import FindingSeverity, TaskType
from experimental_ml.core.findings import ConfigurationError, Finding
from experimental_ml.core.types import ObservationId
from experimental_ml.data.schema import ColumnSemanticType


@dataclass(frozen=True, slots=True)
class ProfileConfig:
    """Immutable configuration of heuristic thresholds and memory limits for profiling."""

    near_constant_top_frequency: float = 0.99
    identifier_unique_ratio: float = 0.95
    scale_disparity_orders: float = 3.0
    imbalance_ratio: float = 3.0
    rare_class_proportion: float = 0.05
    small_group_size: int = 5
    max_categories_reported: int = 50
    max_listed_ids: int = 100

    def __post_init__(self) -> None:
        if not (0.5 < self.near_constant_top_frequency <= 1.0):
            raise ConfigurationError(
                f"near_constant_top_frequency must be in (0.5, 1.0], got {self.near_constant_top_frequency}"
            )
        if not (0.0 < self.identifier_unique_ratio <= 1.0):
            raise ConfigurationError(
                f"identifier_unique_ratio must be in (0.0, 1.0], got {self.identifier_unique_ratio}"
            )
        if self.scale_disparity_orders < 1.0:
            raise ConfigurationError(
                f"scale_disparity_orders must be >= 1.0, got {self.scale_disparity_orders}"
            )
        if self.imbalance_ratio < 1.0:
            raise ConfigurationError(
                f"imbalance_ratio must be >= 1.0, got {self.imbalance_ratio}"
            )
        if not (0.0 < self.rare_class_proportion <= 0.5):
            raise ConfigurationError(
                f"rare_class_proportion must be in (0.0, 0.5], got {self.rare_class_proportion}"
            )
        if self.small_group_size < 1:
            raise ConfigurationError(
                f"small_group_size must be >= 1, got {self.small_group_size}"
            )
        if self.max_categories_reported < 1:
            raise ConfigurationError(
                f"max_categories_reported must be >= 1, got {self.max_categories_reported}"
            )
        if self.max_listed_ids < 1:
            raise ConfigurationError(
                f"max_listed_ids must be >= 1, got {self.max_listed_ids}"
            )


@dataclass(frozen=True, slots=True)
class NumericDistributionStats:
    """Distribution statistics for numeric columns computed over valid non-missing values."""

    mean: float | None
    std: float | None
    min: float | None
    q1: float | None
    median: float | None
    q3: float | None
    max: float | None
    range: float | None
    iqr: float | None


@dataclass(frozen=True, slots=True)
class CategoryFrequency:
    """Absolute and relative frequency of an individual category value."""

    value: Any
    count: int
    proportion: float


@dataclass(frozen=True, slots=True)
class CategoricalDistributionStats:
    """Distribution statistics for categorical, boolean or object columns."""

    cardinality: int
    frequencies: tuple[CategoryFrequency, ...]
    remainder_count: int
    remainder_proportion: float


@dataclass(frozen=True, slots=True)
class ColumnProfile:
    """Detailed structural and distribution profile for an individual column."""

    name: str
    physical_type: str
    semantic_type: ColumnSemanticType
    role: str
    n_missing: int
    missing_proportion: float
    n_unique: int
    numeric_stats: NumericDistributionStats | None
    categorical_stats: CategoricalDistributionStats | None


@dataclass(frozen=True, slots=True)
class TargetProfile:
    """Target column profile including task-specific distribution statistics."""

    column_name: str
    task_type: TaskType
    numeric_stats: NumericDistributionStats | None
    skewness: float | None
    outliers_count_iqr_fences: int | None
    class_frequencies: tuple[CategoryFrequency, ...] | None
    majority_minority_ratio: float | None


@dataclass(frozen=True, slots=True)
class GroupProfile:
    """Grouping profile when group_col is declared in schema."""

    group_col: str
    n_groups: int
    min_group_size: int
    median_group_size: float
    max_group_size: int


@dataclass(frozen=True, slots=True)
class DuplicateRowsProfile:
    """Duplicate rows analysis excluding strictly the observation_id column."""

    n_duplicate_rows: int
    duplicate_observation_ids: tuple[ObservationId, ...]
    is_truncated: bool


@dataclass(frozen=True, slots=True)
class DatasetProfile:
    """Immutable aggregate dataset profile and diagnostic findings."""

    source_dataset_hash: str
    n_rows: int
    n_cols: int
    memory_bytes: int
    columns: MappingProxyType[str, ColumnProfile]
    duplicate_rows: DuplicateRowsProfile
    target: TargetProfile
    groups: GroupProfile | None
    findings: tuple[Finding, ...]
