"""Dataset profiling and diagnostic finding engine.

Implements structural profiling, distribution statistics, target/group diagnostics,
and closed findings catalog evaluation for Stage 1.
Complies with ADR-002, ADR-007, ADR-008, and RNF07.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence
import numpy as np

from experimental_ml.core.enums import FindingSeverity, TaskType
from experimental_ml.core.findings import ConfigurationError, Finding
from experimental_ml.core import is_missing_scalar, is_nan_scalar
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


def compute_numeric_distribution_stats(
    values: np.ndarray | Sequence[Any],
) -> NumericDistributionStats:
    """Compute distribution statistics for a numeric array over non-missing values.

    Args:
        values: 1D array or sequence of numbers (floats, ints, or objects containing them).

    Returns:
        NumericDistributionStats with mean, std (ddof=1), quartiles, min, max, range, IQR.
        Returns None for all metrics when no valid values exist.
    """
    if isinstance(values, np.ndarray) and values.dtype in (np.int64, np.int32, np.int16, np.int8):
        valid = values.astype(np.float64)
    elif isinstance(values, np.ndarray) and np.issubdtype(values.dtype, np.floating):
        mask = ~np.isnan(values)
        valid = values[mask].astype(np.float64)
    else:
        valid_list: list[float] = []
        for x in values:
            if not is_missing_scalar(x):
                try:
                    valid_list.append(float(x))
                except (TypeError, ValueError):
                    pass
        valid = np.array(valid_list, dtype=np.float64)

    n_valid = len(valid)
    if n_valid == 0:
        return NumericDistributionStats(
            mean=None,
            std=None,
            min=None,
            q1=None,
            median=None,
            q3=None,
            max=None,
            range=None,
            iqr=None,
        )

    if n_valid == 1:
        v = float(valid[0])
        return NumericDistributionStats(
            mean=v,
            std=None,
            min=v,
            q1=v,
            median=v,
            q3=v,
            max=v,
            range=0.0,
            iqr=0.0,
        )

    mean_val = float(np.mean(valid))
    std_val = float(np.std(valid, ddof=1))
    min_val = float(np.min(valid))
    max_val = float(np.max(valid))
    q1_val, med_val, q3_val = [float(x) for x in np.percentile(valid, [25, 50, 75], method="linear")]
    range_val = float(max_val - min_val)
    iqr_val = float(q3_val - q1_val)

    return NumericDistributionStats(
        mean=mean_val,
        std=std_val,
        min=min_val,
        q1=q1_val,
        median=med_val,
        q3=q3_val,
        max=max_val,
        range=range_val,
        iqr=iqr_val,
    )


def compute_categorical_distribution_stats(
    values: np.ndarray | Sequence[Any],
    max_categories_reported: int = 50,
) -> CategoricalDistributionStats:
    """Compute cardinality and frequency distribution for categorical, boolean or object columns.

    Args:
        values: 1D array or sequence of values.
        max_categories_reported: Maximum number of top categories to report in detail.

    Returns:
        CategoricalDistributionStats with cardinality, sorted top frequencies, and remainder.
    """
    counts: dict[tuple[type, Any], int] = {}
    total_valid = 0

    for x in values:
        if not is_missing_scalar(x):
            key = (type(x), x)
            counts[key] = counts.get(key, 0) + 1
            total_valid += 1

    cardinality = len(counts)
    if total_valid == 0:
        return CategoricalDistributionStats(
            cardinality=0,
            frequencies=(),
            remainder_count=0,
            remainder_proportion=0.0,
        )

    # Sort categories: count DESC, then (type_name, str(val)) ASC
    sorted_items = sorted(
        counts.items(),
        key=lambda item: (-item[1], item[0][0].__name__, str(item[0][1])),
    )

    top_items = sorted_items[:max_categories_reported]
    remainder_items = sorted_items[max_categories_reported:]

    frequencies = tuple(
        CategoryFrequency(
            value=key[1],
            count=count,
            proportion=count / total_valid,
        )
        for key, count in top_items
    )

    remainder_count = sum(count for _, count in remainder_items)
    remainder_prop = remainder_count / total_valid if total_valid > 0 else 0.0

    return CategoricalDistributionStats(
        cardinality=cardinality,
        frequencies=frequencies,
        remainder_count=remainder_count,
        remainder_proportion=remainder_prop,
    )

