"""Unit tests for dataset profiling data structures, configuration, and engines.

Tests compliance with PROF-01 through PROF-12, ADR-007, and ADR-008.
"""

from __future__ import annotations

import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.data.profiling import (
    CategoricalDistributionStats,
    CategoryFrequency,
    ColumnProfile,
    DatasetProfile,
    DuplicateRowsProfile,
    GroupProfile,
    NumericDistributionStats,
    ProfileConfig,
    TargetProfile,
)


def test_prof_11_profile_config_threshold_validation() -> None:
    """PROF-11: ProfileConfig validates thresholds and raises ConfigurationError on invalid bounds."""
    # Default config is valid
    cfg = ProfileConfig()
    assert cfg.near_constant_top_frequency == 0.99
    assert cfg.identifier_unique_ratio == 0.95
    assert cfg.scale_disparity_orders == 3.0
    assert cfg.imbalance_ratio == 3.0
    assert cfg.rare_class_proportion == 0.05
    assert cfg.small_group_size == 5
    assert cfg.max_categories_reported == 50
    assert cfg.max_listed_ids == 100

    # near_constant_top_frequency out of (0.5, 1.0]
    with pytest.raises(ConfigurationError, match="near_constant_top_frequency"):
        ProfileConfig(near_constant_top_frequency=0.5)
    with pytest.raises(ConfigurationError, match="near_constant_top_frequency"):
        ProfileConfig(near_constant_top_frequency=1.01)

    # identifier_unique_ratio out of (0.0, 1.0]
    with pytest.raises(ConfigurationError, match="identifier_unique_ratio"):
        ProfileConfig(identifier_unique_ratio=0.0)
    with pytest.raises(ConfigurationError, match="identifier_unique_ratio"):
        ProfileConfig(identifier_unique_ratio=1.05)

    # scale_disparity_orders < 1.0
    with pytest.raises(ConfigurationError, match="scale_disparity_orders"):
        ProfileConfig(scale_disparity_orders=0.9)

    # imbalance_ratio < 1.0
    with pytest.raises(ConfigurationError, match="imbalance_ratio"):
        ProfileConfig(imbalance_ratio=0.99)

    # rare_class_proportion out of (0.0, 0.5]
    with pytest.raises(ConfigurationError, match="rare_class_proportion"):
        ProfileConfig(rare_class_proportion=0.0)
    with pytest.raises(ConfigurationError, match="rare_class_proportion"):
        ProfileConfig(rare_class_proportion=0.51)

    # small_group_size < 1
    with pytest.raises(ConfigurationError, match="small_group_size"):
        ProfileConfig(small_group_size=0)

    # max_categories_reported < 1
    with pytest.raises(ConfigurationError, match="max_categories_reported"):
        ProfileConfig(max_categories_reported=0)

    # max_listed_ids < 1
    with pytest.raises(ConfigurationError, match="max_listed_ids"):
        ProfileConfig(max_listed_ids=0)


def test_profiling_models_immutability_and_slots() -> None:
    """Verify that all profiling models are frozen and use slots per ADR-008."""
    cfg = ProfileConfig()
    with pytest.raises(Exception):
        cfg.near_constant_top_frequency = 0.8  # type: ignore[misc]

    num_stats = NumericDistributionStats(
        mean=1.0, std=0.5, min=0.0, q1=0.25, median=0.5, q3=0.75, max=1.0, range=1.0, iqr=0.5
    )
    with pytest.raises(Exception):
        num_stats.mean = 2.0  # type: ignore[misc]
    assert not hasattr(num_stats, "__dict__")

    cat_freq = CategoryFrequency(value="A", count=10, proportion=1.0)
    with pytest.raises(Exception):
        cat_freq.count = 20  # type: ignore[misc]
    assert not hasattr(cat_freq, "__dict__")


def test_prof_02_numeric_distribution_statistics() -> None:
    """PROF-02: Numeric columns calculate mean, std (ddof=1), min, max, quartiles, range, IQR."""
    import numpy as np
    from experimental_ml.data.profiling import compute_numeric_distribution_stats

    # Standard distribution with missing values
    data = np.array([10.0, 20.0, 30.0, 40.0, np.nan], dtype=object)
    stats = compute_numeric_distribution_stats(data)

    assert stats.mean == 25.0
    assert stats.min == 10.0
    assert stats.max == 40.0
    assert stats.median == 25.0
    assert stats.q1 == 17.5
    assert stats.q3 == 32.5
    assert stats.range == 30.0
    assert stats.iqr == 15.0
    assert stats.std is not None
    assert np.isclose(stats.std, np.std([10.0, 20.0, 30.0, 40.0], ddof=1))

    # Single non-missing observation (sample std is undefined None)
    single = np.array([42.0, np.nan], dtype=object)
    s_stats = compute_numeric_distribution_stats(single)
    assert s_stats.mean == 42.0
    assert s_stats.std is None
    assert s_stats.min == 42.0
    assert s_stats.max == 42.0
    assert s_stats.range == 0.0
    assert s_stats.iqr == 0.0

    # Zero variance sample (std = 0.0)
    zero_var = np.array([7.0, 7.0, 7.0], dtype=np.float64)
    zv_stats = compute_numeric_distribution_stats(zero_var)
    assert zv_stats.mean == 7.0
    assert zv_stats.std == 0.0
    assert zv_stats.range == 0.0
    assert zv_stats.iqr == 0.0


def test_prof_03_categorical_distribution_and_frequencies() -> None:
    """PROF-03: Categorical/object columns report cardinality, deterministic sorted frequencies, truncation."""
    import numpy as np
    from experimental_ml.data.profiling import compute_categorical_distribution_stats

    # Categories with frequency tie: A=2, B=2, C=1, D=1, missing=2
    data = np.array(["B", "A", "B", "C", "A", "D", None, np.nan], dtype=object)
    stats = compute_categorical_distribution_stats(data, max_categories_reported=2)

    assert stats.cardinality == 4
    assert len(stats.frequencies) == 2
    # Tie broken alphabetically: A before B
    assert stats.frequencies[0].value == "A"
    assert stats.frequencies[0].count == 2
    assert np.isclose(stats.frequencies[0].proportion, 2 / 6)
    assert stats.frequencies[1].value == "B"
    assert stats.frequencies[1].count == 2
    assert np.isclose(stats.frequencies[1].proportion, 2 / 6)

    # Remainder captures C and D
    assert stats.remainder_count == 2
    assert np.isclose(stats.remainder_proportion, 2 / 6)

    # Heterogeneous scalar types in object column
    het = np.array([1, "1", True, False, None], dtype=object)
    het_stats = compute_categorical_distribution_stats(het, max_categories_reported=10)
    assert het_stats.cardinality == 4
    # All 4 valid values present without type comparison error
    values = [f.value for f in het_stats.frequencies]
    assert 1 in values
    assert "1" in values
    assert True in values
    assert False in values


def test_prof_12_fully_missing_column_handling() -> None:
    """PROF-12: Columns with 100% missing values return None for all statistics without raising."""
    import numpy as np
    from experimental_ml.data.profiling import (
        compute_categorical_distribution_stats,
        compute_numeric_distribution_stats,
    )

    data = np.array([None, np.nan, float("nan")], dtype=object)

    num_stats = compute_numeric_distribution_stats(data)
    assert num_stats.mean is None
    assert num_stats.std is None
    assert num_stats.min is None
    assert num_stats.q1 is None
    assert num_stats.median is None
    assert num_stats.q3 is None
    assert num_stats.max is None
    assert num_stats.range is None
    assert num_stats.iqr is None

    cat_stats = compute_categorical_distribution_stats(data)
    assert cat_stats.cardinality == 0
    assert cat_stats.frequencies == ()
    assert cat_stats.remainder_count == 0
    assert cat_stats.remainder_proportion == 0.0

