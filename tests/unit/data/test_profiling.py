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
