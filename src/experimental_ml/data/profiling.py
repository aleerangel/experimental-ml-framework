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


_MISSING_SENTINEL = object()


def compute_target_profile(
    target_col_name: str,
    values: np.ndarray | Sequence[Any],
    task_type: TaskType,
    max_categories_reported: int = 50,
) -> TargetProfile:
    """Compute task-specific distribution profile for the target column.

    Args:
        target_col_name: Name of the target column.
        values: Target column data array or sequence.
        task_type: TaskType (REGRESSION, BINARY_CLASSIFICATION, etc.).
        max_categories_reported: Category truncation threshold.

    Returns:
        TargetProfile with regression metrics or classification frequencies.
    """
    if task_type == TaskType.REGRESSION:
        num_stats = compute_numeric_distribution_stats(values)

        # Extract valid values for skewness and outlier fence calculations
        valid_list: list[float] = []
        for x in values:
            if not is_missing_scalar(x):
                try:
                    valid_list.append(float(x))
                except (TypeError, ValueError):
                    pass
        valid = np.array(valid_list, dtype=np.float64)
        n_valid = len(valid)

        # Skewness calculation (Fisher-Pearson adjusted)
        skewness: float | None = None
        if n_valid >= 3 and num_stats.std is not None and num_stats.std > 0.0:
            m = num_stats.mean if num_stats.mean is not None else float(np.mean(valid))
            s = num_stats.std
            sum_cubed = float(np.sum(((valid - m) / s) ** 3))
            skewness = float((n_valid / ((n_valid - 1) * (n_valid - 2))) * sum_cubed)

        # Outliers calculation using IQR fences [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
        outliers_count: int | None = None
        if n_valid >= 4 and num_stats.q1 is not None and num_stats.q3 is not None and num_stats.iqr is not None:
            if num_stats.iqr == 0.0:
                if num_stats.min == num_stats.max:
                    outliers_count = 0
                else:
                    outliers_count = int(np.sum((valid < num_stats.q1) | (valid > num_stats.q3)))
            else:
                lower_fence = num_stats.q1 - 1.5 * num_stats.iqr
                upper_fence = num_stats.q3 + 1.5 * num_stats.iqr
                outliers_count = int(np.sum((valid < lower_fence) | (valid > upper_fence)))

        return TargetProfile(
            column_name=target_col_name,
            task_type=task_type,
            numeric_stats=num_stats,
            skewness=skewness,
            outliers_count_iqr_fences=outliers_count,
            class_frequencies=None,
            majority_minority_ratio=None,
        )

    # Classification tasks
    cat_stats = compute_categorical_distribution_stats(
        values, max_categories_reported=max_categories_reported
    )

    majority_minority_ratio: float | None = None
    if len(cat_stats.frequencies) >= 2:
        maj_count = cat_stats.frequencies[0].count
        min_count = cat_stats.frequencies[-1].count
        majority_minority_ratio = maj_count / min_count if min_count > 0 else None

    return TargetProfile(
        column_name=target_col_name,
        task_type=task_type,
        numeric_stats=None,
        skewness=None,
        outliers_count_iqr_fences=None,
        class_frequencies=cat_stats.frequencies,
        majority_minority_ratio=majority_minority_ratio,
    )


def compute_group_profile(
    group_col: str,
    values: np.ndarray | Sequence[Any],
) -> GroupProfile:
    """Compute grouping size distribution when group_col is present in schema.

    Args:
        group_col: Name of the group column.
        values: Group column data.

    Returns:
        GroupProfile with count of groups and min, median, max group sizes.
    """
    counts: dict[tuple[type, Any], int] = {}
    for x in values:
        if not is_missing_scalar(x):
            key = (type(x), x)
            counts[key] = counts.get(key, 0) + 1

    if not counts:
        return GroupProfile(
            group_col=group_col,
            n_groups=0,
            min_group_size=0,
            median_group_size=0.0,
            max_group_size=0,
        )

    sizes = list(counts.values())
    return GroupProfile(
        group_col=group_col,
        n_groups=len(sizes),
        min_group_size=int(min(sizes)),
        median_group_size=float(np.median(sizes)),
        max_group_size=int(max(sizes)),
    )


def compute_duplicate_rows_profile(
    columns: Mapping[str, np.ndarray],
    observation_ids: Sequence[ObservationId],
    observation_id_col: str | None = None,
    max_listed_ids: int = 100,
) -> DuplicateRowsProfile:
    """Detect duplicate rows comparing all columns except strictly observation_id.

    Args:
        columns: Mapping of column names to 1D arrays.
        observation_ids: Ordered sequence of observation IDs.
        observation_id_col: Name of observation ID column to exclude from comparison.
        max_listed_ids: Truncation limit for listed duplicate observation IDs.

    Returns:
        DuplicateRowsProfile with duplicate count, duplicate IDs, and truncation flag.
    """
    n_rows = len(observation_ids)
    if n_rows == 0:
        return DuplicateRowsProfile(
            n_duplicate_rows=0,
            duplicate_observation_ids=(),
            is_truncated=False,
        )

    # Exclude strictly the observation_id column; keep all other columns in sorted order
    compared_cols = sorted(
        (col_name, col_data)
        for col_name, col_data in columns.items()
        if col_name != observation_id_col
    )

    seen_signatures: set[tuple[Any, ...]] = set()
    duplicate_ids: list[ObservationId] = []
    n_duplicate_rows = 0

    for i in range(n_rows):
        row_signature = tuple(
            _MISSING_SENTINEL
            if is_missing_scalar(col_data[i])
            else (type(col_data[i]).__name__, col_data[i])
            for _, col_data in compared_cols
        )
        if row_signature in seen_signatures:
            n_duplicate_rows += 1
            if len(duplicate_ids) < max_listed_ids:
                duplicate_ids.append(observation_ids[i])
        else:
            seen_signatures.add(row_signature)

    is_truncated = n_duplicate_rows > max_listed_ids
    return DuplicateRowsProfile(
        n_duplicate_rows=n_duplicate_rows,
        duplicate_observation_ids=tuple(duplicate_ids),
        is_truncated=is_truncated,
    )


