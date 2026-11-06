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
from experimental_ml.core.findings import (
    ConfigurationError,
    Finding,
    make_finding,
    make_warning,
)
from experimental_ml.core import is_missing_scalar, is_nan_scalar
from experimental_ml.core.types import ObservationId
from experimental_ml.data.schema import ColumnSemanticType
from experimental_ml.data.types import DatasetBundle


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


def finding_sort_key(finding: Finding) -> tuple[int, str, str]:
    """Canonical 3-tuple sort key for findings: (severity, code, column)."""
    sev_rank = 0 if finding.severity == FindingSeverity.CONFIRMED_ISSUE else 1
    col_str = ""
    if finding.context is not None and finding.context.get("column") is not None:
        col_str = str(finding.context["column"])
    return (sev_rank, finding.code, col_str)


def evaluate_findings(
    schema_target_col: str,
    schema_group_col: str | None,
    schema_task_type: TaskType,
    n_rows: int,
    column_profiles: Mapping[str, ColumnProfile],
    target_profile: TargetProfile,
    group_profile: GroupProfile | None,
    duplicate_profile: DuplicateRowsProfile,
    config: ProfileConfig,
) -> tuple[Finding, ...]:
    """Evaluate closed findings catalog: 8 CONFIRMED_ISSUE and 7 HEURISTIC_WARNING.

    Returns:
        Canonically sorted tuple of Finding objects.
    """
    findings: list[Finding] = []

    # --- 8 CONFIRMED_ISSUE ---

    # 1. E1_TARGET_MISSING
    if schema_target_col in column_profiles:
        target_col_prof = column_profiles[schema_target_col]
        if target_col_prof.n_missing > 0:
            findings.append(
                make_finding(
                    code="E1_TARGET_MISSING",
                    message=f"Target column '{schema_target_col}' contains {target_col_prof.n_missing} missing value(s).",
                    context={
                        "column": schema_target_col,
                        "n_missing": target_col_prof.n_missing,
                        "missing_proportion": target_col_prof.missing_proportion,
                    },
                )
            )

    # 2. E1_GROUP_MISSING
    if schema_group_col and schema_group_col in column_profiles:
        group_col_prof = column_profiles[schema_group_col]
        if group_col_prof.n_missing > 0:
            findings.append(
                make_finding(
                    code="E1_GROUP_MISSING",
                    message=f"Group column '{schema_group_col}' contains {group_col_prof.n_missing} missing value(s).",
                    context={
                        "column": schema_group_col,
                        "n_missing": group_col_prof.n_missing,
                        "missing_proportion": group_col_prof.missing_proportion,
                    },
                )
            )

    # Feature-specific confirmed issues
    for col_name, col_prof in column_profiles.items():
        if col_prof.role != "feature":
            continue

        # 3. E1_FEATURE_MISSING
        if col_prof.n_missing > 0:
            findings.append(
                make_finding(
                    code="E1_FEATURE_MISSING",
                    message=f"Feature column '{col_name}' contains {col_prof.n_missing} missing value(s).",
                    context={
                        "column": col_name,
                        "n_missing": col_prof.n_missing,
                        "missing_proportion": col_prof.missing_proportion,
                    },
                )
            )

        # 4. E1_CONSTANT_COLUMN
        if col_prof.n_unique <= 1:
            findings.append(
                make_finding(
                    code="E1_CONSTANT_COLUMN",
                    message=f"Feature column '{col_name}' is constant (n_unique={col_prof.n_unique}).",
                    context={
                        "column": col_name,
                        "n_unique": col_prof.n_unique,
                    },
                )
            )

        # 5. E1_CATEGORICAL_UNENCODED
        if col_prof.physical_type == "object":
            findings.append(
                make_finding(
                    code="E1_CATEGORICAL_UNENCODED",
                    message=f"Feature column '{col_name}' has physical type 'object' and requires encoding.",
                    context={
                        "column": col_name,
                        "physical_type": "object",
                    },
                )
            )

    # 6 & 7. Binary classification target findings (mutually exclusive)
    if schema_task_type == TaskType.BINARY_CLASSIFICATION:
        classes = (
            [f.value for f in target_profile.class_frequencies]
            if target_profile.class_frequencies
            else []
        )
        n_classes = len(classes)
        if n_classes != 2:
            findings.append(
                make_finding(
                    code="E1_TARGET_CLASS_COUNT_INVALID",
                    message=f"Binary classification target '{schema_target_col}' has {n_classes} classes; expected exactly 2.",
                    context={
                        "column": schema_target_col,
                        "n_classes": n_classes,
                        "observed_classes": tuple(sorted(str(c) for c in classes)),
                    },
                )
            )
        else:
            # Check if classes are {0, 1}
            is_zero_one = False
            try:
                converted = set()
                for c in classes:
                    val = float(c)
                    if val in (0.0, 1.0) and val == int(val):
                        converted.add(int(val))
                    else:
                        converted.add(c)
                is_zero_one = (converted == {0, 1})
            except (ValueError, TypeError):
                is_zero_one = False

            if not is_zero_one:
                findings.append(
                    make_finding(
                        code="E1_TARGET_BINARY_UNMAPPED",
                        message=f"Binary classification target '{schema_target_col}' has unmapped classes; expected {{0, 1}}.",
                        context={
                            "column": schema_target_col,
                            "classes": tuple(sorted(str(c) for c in classes)),
                        },
                    )
                )

    # 8. E1_TARGET_NOT_NUMERIC
    if schema_task_type == TaskType.REGRESSION and schema_target_col in column_profiles:
        target_phys = column_profiles[schema_target_col].physical_type
        if target_phys in ("object", "bool"):
            findings.append(
                make_finding(
                    code="E1_TARGET_NOT_NUMERIC",
                    message=f"Regression target '{schema_target_col}' has non-numeric physical type '{target_phys}'.",
                    context={
                        "column": schema_target_col,
                        "physical_type": target_phys,
                    },
                )
            )

    # --- 7 HEURISTIC_WARNING ---

    # Feature-specific heuristic warnings
    eligible_medians: list[float] = []

    for col_name, col_prof in column_profiles.items():
        if col_prof.role != "feature":
            continue

        # 1. W1_POSSIBLE_IDENTIFIER
        if col_prof.physical_type in ("int64", "object") and n_rows > 0:
            unique_ratio = col_prof.n_unique / n_rows
            if unique_ratio >= config.identifier_unique_ratio:
                findings.append(
                    make_warning(
                        code="W1_POSSIBLE_IDENTIFIER",
                        message=f"Feature column '{col_name}' has high unique ratio {unique_ratio:.2f} >= {config.identifier_unique_ratio}.",
                        context={
                            "column": col_name,
                            "unique_ratio": unique_ratio,
                            "threshold": config.identifier_unique_ratio,
                        },
                    )
                )

        # 2. W1_NEAR_CONSTANT_COLUMN
        if col_prof.n_unique > 1:
            valid_count = n_rows - col_prof.n_missing
            if valid_count > 0 and col_prof.categorical_stats and col_prof.categorical_stats.frequencies:
                top_freq = col_prof.categorical_stats.frequencies[0].count
                top_ratio = top_freq / valid_count
                if top_ratio >= config.near_constant_top_frequency:
                    findings.append(
                        make_warning(
                            code="W1_NEAR_CONSTANT_COLUMN",
                            message=f"Feature column '{col_name}' is near constant with top frequency ratio {top_ratio:.2f} >= {config.near_constant_top_frequency}.",
                            context={
                                "column": col_name,
                                "top_frequency_ratio": top_ratio,
                                "top_value": col_prof.categorical_stats.frequencies[0].value,
                                "threshold": config.near_constant_top_frequency,
                            },
                        )
                    )

        # Collect eligible non-zero absolute medians for W1_SCALE_DISPARITY
        if col_prof.physical_type in ("int64", "float64") and col_prof.numeric_stats:
            med = col_prof.numeric_stats.median
            if med is not None and abs(med) > 0.0:
                eligible_medians.append(abs(med))

    # 3. W1_SCALE_DISPARITY (requires >= 2 non-zero medians among numeric features)
    if len(eligible_medians) >= 2:
        min_med = min(eligible_medians)
        max_med = max(eligible_medians)
        ratio = max_med / min_med
        if ratio >= (10.0 ** config.scale_disparity_orders):
            findings.append(
                make_warning(
                    code="W1_SCALE_DISPARITY",
                    message=f"Disparity of scales detected among numeric features (ratio {ratio:.1e} >= 10^{config.scale_disparity_orders}).",
                    context={
                        "column": None,
                        "min_median": min_med,
                        "max_median": max_med,
                        "ratio": ratio,
                        "orders": config.scale_disparity_orders,
                    },
                )
            )

    # 4. W1_CLASS_IMBALANCE
    if schema_task_type in (TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION):
        if target_profile.majority_minority_ratio is not None and target_profile.majority_minority_ratio >= config.imbalance_ratio:
            findings.append(
                make_warning(
                    code="W1_CLASS_IMBALANCE",
                    message=f"Target column '{schema_target_col}' has class imbalance ratio {target_profile.majority_minority_ratio:.2f} >= {config.imbalance_ratio}.",
                    context={
                        "column": schema_target_col,
                        "imbalance_ratio": target_profile.majority_minority_ratio,
                        "threshold": config.imbalance_ratio,
                    },
                )
            )

        # 5. W1_RARE_CLASS
        if target_profile.class_frequencies:
            rare_classes = [
                {"class": str(f.value), "proportion": f.proportion}
                for f in target_profile.class_frequencies
                if f.proportion < config.rare_class_proportion
            ]
            if rare_classes:
                findings.append(
                    make_warning(
                        code="W1_RARE_CLASS",
                        message=f"Target column '{schema_target_col}' has {len(rare_classes)} rare class(es) with proportion < {config.rare_class_proportion}.",
                        context={
                            "column": schema_target_col,
                            "rare_classes": tuple(rare_classes),
                            "threshold": config.rare_class_proportion,
                        },
                    )
                )

    # 6. W1_SMALL_GROUPS
    if group_profile and group_profile.n_groups > 0:
        if group_profile.min_group_size < config.small_group_size:
            findings.append(
                make_warning(
                    code="W1_SMALL_GROUPS",
                    message=f"Group column '{group_profile.group_col}' has groups with size {group_profile.min_group_size} < {config.small_group_size}.",
                    context={
                        "column": group_profile.group_col,
                        "min_group_size": group_profile.min_group_size,
                        "threshold": config.small_group_size,
                    },
                )
            )

    # 7. W1_DUPLICATE_ROWS
    if duplicate_profile.n_duplicate_rows > 0:
        findings.append(
            make_warning(
                code="W1_DUPLICATE_ROWS",
                message=f"Dataset contains {duplicate_profile.n_duplicate_rows} duplicate row(s) excluding observation_id.",
                context={
                    "column": None,
                    "n_duplicate_rows": duplicate_profile.n_duplicate_rows,
                    "is_truncated": duplicate_profile.is_truncated,
                },
            )
        )

    # Sort canonically
    findings.sort(key=finding_sort_key)
    return tuple(findings)


def profile_dataset(
    bundle: DatasetBundle,
    config: ProfileConfig | None = None,
) -> DatasetProfile:
    """Generate comprehensive, immutable structural profile and diagnostic findings for a DatasetBundle.

    Pure functional execution: reads bundle immutably without altering bundle.dataset_hash
    or any underlying numpy array buffers.

    Args:
        bundle: Ingested immutable DatasetBundle.
        config: Optional ProfileConfig specifying heuristic thresholds and memory limits.

    Returns:
        Immutable DatasetProfile containing column-level profiles, target/group distributions,
        duplicate rows diagnostics, and canonically sorted diagnostic findings.

    Raises:
        ConfigurationError: If any threshold in config is invalid.
    """
    if config is None:
        config = ProfileConfig()

    col_profiles: dict[str, ColumnProfile] = {}
    for col_name, col_data in bundle.columns.items():
        desc = bundle.descriptors[col_name]
        n_missing = desc.n_missing
        missing_prop = n_missing / bundle.n_rows if bundle.n_rows > 0 else 0.0

        # Numeric statistics for numeric types
        is_numeric = desc.physical_type in ("int64", "float64") or desc.semantic_type in (
            ColumnSemanticType.NUMERIC_CONTINUOUS,
            ColumnSemanticType.NUMERIC_DISCRETE,
        )
        numeric_stats = (
            compute_numeric_distribution_stats(col_data) if is_numeric else None
        )

        # Categorical statistics for categorical/boolean/object columns
        is_categorical_candidate = (
            desc.physical_type == "object"
            or desc.semantic_type in (
                ColumnSemanticType.CATEGORICAL,
                ColumnSemanticType.BOOLEAN,
            )
        )
        categorical_stats = (
            compute_categorical_distribution_stats(
                col_data, max_categories_reported=config.max_categories_reported
            )
            if is_categorical_candidate
            else None
        )

        # Determine cardinality (n_unique non-missing values)
        if categorical_stats is not None:
            n_unique = categorical_stats.cardinality
        elif is_numeric:
            # Count distinct non-missing values
            valid_set: set[float] = set()
            for x in col_data:
                if not is_missing_scalar(x):
                    valid_set.add(float(x))
            n_unique = len(valid_set)
        else:
            valid_set_any: set[Any] = set()
            for x in col_data:
                if not is_missing_scalar(x):
                    valid_set_any.add((type(x), x))
            n_unique = len(valid_set_any)

        col_profiles[col_name] = ColumnProfile(
            name=col_name,
            physical_type=desc.physical_type,
            semantic_type=desc.semantic_type,
            role=desc.role,
            n_missing=n_missing,
            missing_proportion=missing_prop,
            n_unique=n_unique,
            numeric_stats=numeric_stats,
            categorical_stats=categorical_stats,
        )

    # Target profile
    target_profile = compute_target_profile(
        target_col_name=bundle.schema.target_col,
        values=bundle.columns[bundle.schema.target_col],
        task_type=bundle.schema.task_type,
        max_categories_reported=config.max_categories_reported,
    )

    # Group profile
    group_profile: GroupProfile | None = None
    if bundle.schema.group_col and bundle.schema.group_col in bundle.columns:
        group_profile = compute_group_profile(
            group_col=bundle.schema.group_col,
            values=bundle.columns[bundle.schema.group_col],
        )

    # Duplicate rows profile
    duplicate_profile = compute_duplicate_rows_profile(
        columns=bundle.columns,
        observation_ids=bundle.observation_ids,
        observation_id_col=bundle.schema.observation_id_col,
        max_listed_ids=config.max_listed_ids,
    )

    # Closed findings catalog
    findings = evaluate_findings(
        schema_target_col=bundle.schema.target_col,
        schema_group_col=bundle.schema.group_col,
        schema_task_type=bundle.schema.task_type,
        n_rows=bundle.n_rows,
        column_profiles=col_profiles,
        target_profile=target_profile,
        group_profile=group_profile,
        duplicate_profile=duplicate_profile,
        config=config,
    )

    return DatasetProfile(
        source_dataset_hash=bundle.dataset_hash,
        n_rows=bundle.n_rows,
        n_cols=bundle.n_cols,
        memory_bytes=bundle.memory_bytes,
        columns=MappingProxyType(col_profiles),
        duplicate_rows=duplicate_profile,
        target=target_profile,
        groups=group_profile,
        findings=findings,
    )




