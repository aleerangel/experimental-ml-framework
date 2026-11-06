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


def test_prof_04_duplicate_rows_detection() -> None:
    """PROF-04: Duplicate rows detection compares all columns except observation_id, truncates at max_listed_ids."""
    import numpy as np
    from experimental_ml.core.types import ObservationId
    from experimental_ml.data.profiling import compute_duplicate_rows_profile

    # Rows 0, 1, 3 have identical content ("A", 1.0, None)
    # Row 2 is distinct ("B", 2.0, 10)
    # Row 4 is distinct ("A", 1.0, 5)
    cols = {
        "id": np.array(["id_0", "id_1", "id_2", "id_3", "id_4"], dtype=object),
        "feat1": np.array(["A", "A", "B", "A", "A"], dtype=object),
        "feat2": np.array([1.0, 1.0, 2.0, 1.0, 1.0], dtype=object),
        "feat3": np.array([None, np.nan, 10, None, 5], dtype=object),
    }
    obs_ids = [ObservationId(x) for x in cols["id"]]

    # With max_listed_ids = 1
    dup_profile = compute_duplicate_rows_profile(
        columns=cols,
        observation_ids=obs_ids,
        observation_id_col="id",
        max_listed_ids=1,
    )

    # Rows 1 and 3 are duplicates (total 2 duplicates)
    assert dup_profile.n_duplicate_rows == 2
    # Only 1 listed because max_listed_ids = 1
    assert len(dup_profile.duplicate_observation_ids) == 1
    assert dup_profile.duplicate_observation_ids[0] == ObservationId("id_1")
    assert dup_profile.is_truncated is True

    # With max_listed_ids = 5
    dup_profile_full = compute_duplicate_rows_profile(
        columns=cols,
        observation_ids=obs_ids,
        observation_id_col="id",
        max_listed_ids=5,
    )
    assert dup_profile_full.n_duplicate_rows == 2
    assert len(dup_profile_full.duplicate_observation_ids) == 2
    assert dup_profile_full.duplicate_observation_ids == (ObservationId("id_1"), ObservationId("id_3"))
    assert dup_profile_full.is_truncated is False


def test_prof_05_target_profile_regression_and_classification() -> None:
    """PROF-05: Target profile reports distribution, skewness, outliers for regression, and class frequencies for classification."""
    import numpy as np
    from experimental_ml.core.enums import TaskType
    from experimental_ml.data.profiling import compute_target_profile

    # Regression target with right skew and outliers
    reg_vals = np.array([1.0, 2.0, 2.0, 3.0, 3.0, 4.0, 5.0, 100.0], dtype=np.float64)
    reg_prof = compute_target_profile("target", reg_vals, TaskType.REGRESSION)
    assert reg_prof.task_type == TaskType.REGRESSION
    assert reg_prof.numeric_stats is not None
    assert reg_prof.numeric_stats.mean is not None
    assert reg_prof.skewness is not None
    assert reg_prof.skewness > 1.0  # heavily right-skewed
    assert reg_prof.outliers_count_iqr_fences == 1  # 100.0 is an outlier
    assert reg_prof.class_frequencies is None
    assert reg_prof.majority_minority_ratio is None

    # Classification target with imbalance: class 0 has 80, class 1 has 20
    clf_vals = np.array([0] * 80 + [1] * 20, dtype=object)
    clf_prof = compute_target_profile("label", clf_vals, TaskType.BINARY_CLASSIFICATION)
    assert clf_prof.task_type == TaskType.BINARY_CLASSIFICATION
    assert clf_prof.numeric_stats is None
    assert clf_prof.skewness is None
    assert clf_prof.class_frequencies is not None
    assert len(clf_prof.class_frequencies) == 2
    assert clf_prof.class_frequencies[0].value == 0
    assert clf_prof.class_frequencies[0].count == 80
    assert clf_prof.majority_minority_ratio == 4.0


def test_prof_06_group_profile_statistics() -> None:
    """PROF-06: Group profile reports group count, min, median, max group sizes."""
    import numpy as np
    from experimental_ml.data.profiling import compute_group_profile

    # Groups: g1 (2), g2 (5), g3 (10)
    groups_data = np.array(["g1"] * 2 + ["g2"] * 5 + ["g3"] * 10, dtype=object)
    g_prof = compute_group_profile("site_id", groups_data)

    assert g_prof.group_col == "site_id"
    assert g_prof.n_groups == 3
    assert g_prof.min_group_size == 2
    assert g_prof.median_group_size == 5.0
    assert g_prof.max_group_size == 10


def test_prof_07_catalog_findings_and_canonical_ordering() -> None:
    """PROF-07: Catalog findings are emitted with column context and canonically ordered by severity, code, column."""
    from experimental_ml.core.enums import FindingSeverity, TaskType
    from experimental_ml.data.schema import ColumnSemanticType
    from experimental_ml.data.profiling import (
        ColumnProfile,
        DuplicateRowsProfile,
        NumericDistributionStats,
        ProfileConfig,
        TargetProfile,
        evaluate_findings,
    )

    col_profs = {
        "feat_const": ColumnProfile(
            name="feat_const",
            physical_type="float64",
            semantic_type=ColumnSemanticType.NUMERIC_CONTINUOUS,
            role="feature",
            n_missing=0,
            missing_proportion=0.0,
            n_unique=1,
            numeric_stats=NumericDistributionStats(1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0),
            categorical_stats=None,
        ),
        "feat_obj": ColumnProfile(
            name="feat_obj",
            physical_type="object",
            semantic_type=ColumnSemanticType.CATEGORICAL,
            role="feature",
            n_missing=0,
            missing_proportion=0.0,
            n_unique=2,
            numeric_stats=None,
            categorical_stats=None,
        ),
        "target": ColumnProfile(
            name="target",
            physical_type="int64",
            semantic_type=ColumnSemanticType.CATEGORICAL,
            role="target",
            n_missing=2,
            missing_proportion=0.2,
            n_unique=2,
            numeric_stats=None,
            categorical_stats=None,
        ),
    }

    target_prof = TargetProfile(
        column_name="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        numeric_stats=None,
        skewness=None,
        outliers_count_iqr_fences=None,
        class_frequencies=None,
        majority_minority_ratio=None,
    )
    dup_prof = DuplicateRowsProfile(n_duplicate_rows=1, duplicate_observation_ids=(), is_truncated=False)
    config = ProfileConfig()

    findings = evaluate_findings(
        schema_target_col="target",
        schema_group_col=None,
        schema_task_type=TaskType.BINARY_CLASSIFICATION,
        n_rows=10,
        column_profiles=col_profs,
        target_profile=target_prof,
        group_profile=None,
        duplicate_profile=dup_prof,
        config=config,
    )

    # Verify severity ordering: all CONFIRMED_ISSUE appear before HEURISTIC_WARNING
    severities = [f.severity for f in findings]
    first_warning_idx = next((i for i, s in enumerate(severities) if s == FindingSeverity.HEURISTIC_WARNING), len(severities))
    for s in severities[:first_warning_idx]:
        assert s == FindingSeverity.CONFIRMED_ISSUE
    for s in severities[first_warning_idx:]:
        assert s == FindingSeverity.HEURISTIC_WARNING

    # Context contains 'column'
    for f in findings:
        assert f.context is not None
        assert "column" in f.context


def test_prof_08_severity_separation_heuristics_vs_issues() -> None:
    """PROF-08: Heuristic conditions emit only HEURISTIC_WARNING and never CONFIRMED_ISSUE."""
    from experimental_ml.core.enums import FindingSeverity, TaskType
    from experimental_ml.data.schema import ColumnSemanticType
    from experimental_ml.data.profiling import (
        CategoricalDistributionStats,
        CategoryFrequency,
        ColumnProfile,
        DuplicateRowsProfile,
        GroupProfile,
        NumericDistributionStats,
        ProfileConfig,
        TargetProfile,
        evaluate_findings,
    )

    # Dataset with heuristic triggers only
    cat_stats = CategoricalDistributionStats(
        cardinality=2,
        frequencies=(
            CategoryFrequency(value=0, count=99, proportion=0.99),
            CategoryFrequency(value=1, count=1, proportion=0.01),
        ),
        remainder_count=0,
        remainder_proportion=0.0,
    )
    col_profs = {
        "num1": ColumnProfile(
            name="num1",
            physical_type="float64",
            semantic_type=ColumnSemanticType.NUMERIC_CONTINUOUS,
            role="feature",
            n_missing=0,
            missing_proportion=0.0,
            n_unique=10,
            numeric_stats=NumericDistributionStats(1.0, 0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.0, 1.0),
            categorical_stats=None,
        ),
        "num2": ColumnProfile(
            name="num2",
            physical_type="float64",
            semantic_type=ColumnSemanticType.NUMERIC_CONTINUOUS,
            role="feature",
            n_missing=0,
            missing_proportion=0.0,
            n_unique=10,
            numeric_stats=NumericDistributionStats(10000.0, 500.0, 9000.0, 9500.0, 10000.0, 10500.0, 11000.0, 2000.0, 1000.0),
            categorical_stats=None,
        ),
        "target": ColumnProfile(
            name="target",
            physical_type="int64",
            semantic_type=ColumnSemanticType.CATEGORICAL,
            role="target",
            n_missing=0,
            missing_proportion=0.0,
            n_unique=2,
            numeric_stats=None,
            categorical_stats=cat_stats,
        ),
    }

    target_prof = TargetProfile(
        column_name="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        numeric_stats=None,
        skewness=None,
        outliers_count_iqr_fences=None,
        class_frequencies=cat_stats.frequencies,
        majority_minority_ratio=99.0,
    )
    g_prof = GroupProfile(group_col="g", n_groups=1, min_group_size=2, median_group_size=2.0, max_group_size=2)
    dup_prof = DuplicateRowsProfile(n_duplicate_rows=1, duplicate_observation_ids=(), is_truncated=False)
    config = ProfileConfig()

    findings = evaluate_findings(
        schema_target_col="target",
        schema_group_col="g",
        schema_task_type=TaskType.BINARY_CLASSIFICATION,
        n_rows=100,
        column_profiles=col_profs,
        target_profile=target_prof,
        group_profile=g_prof,
        duplicate_profile=dup_prof,
        config=config,
    )

    heuristic_codes = {
        "W1_POSSIBLE_IDENTIFIER",
        "W1_NEAR_CONSTANT_COLUMN",
        "W1_SCALE_DISPARITY",
        "W1_CLASS_IMBALANCE",
        "W1_RARE_CLASS",
        "W1_SMALL_GROUPS",
        "W1_DUPLICATE_ROWS",
    }
    for f in findings:
        if f.code in heuristic_codes:
            assert f.severity == FindingSeverity.HEURISTIC_WARNING
        else:
            assert f.severity == FindingSeverity.CONFIRMED_ISSUE


def test_prof_09_binary_target_unmapped_and_class_count() -> None:
    """PROF-09: Binary classification target findings are mutually exclusive."""
    from experimental_ml.core.enums import FindingSeverity, TaskType
    from experimental_ml.data.schema import ColumnSemanticType
    from experimental_ml.data.profiling import (
        CategoryFrequency,
        ColumnProfile,
        DuplicateRowsProfile,
        ProfileConfig,
        TargetProfile,
        evaluate_findings,
    )

    col_prof = ColumnProfile(
        name="target",
        physical_type="object",
        semantic_type=ColumnSemanticType.CATEGORICAL,
        role="target",
        n_missing=0,
        missing_proportion=0.0,
        n_unique=2,
        numeric_stats=None,
        categorical_stats=None,
    )
    dup_prof = DuplicateRowsProfile(n_duplicate_rows=0, duplicate_observation_ids=(), is_truncated=False)
    config = ProfileConfig()

    # Case 1: Exactly 2 classes, not {0, 1} -> E1_TARGET_BINARY_UNMAPPED only
    t_prof_unmapped = TargetProfile(
        column_name="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        numeric_stats=None,
        skewness=None,
        outliers_count_iqr_fences=None,
        class_frequencies=(
            CategoryFrequency(value="sim", count=50, proportion=0.5),
            CategoryFrequency(value="nao", count=50, proportion=0.5),
        ),
        majority_minority_ratio=1.0,
    )
    f_unmapped = evaluate_findings(
        schema_target_col="target",
        schema_group_col=None,
        schema_task_type=TaskType.BINARY_CLASSIFICATION,
        n_rows=100,
        column_profiles={"target": col_prof},
        target_profile=t_prof_unmapped,
        group_profile=None,
        duplicate_profile=dup_prof,
        config=config,
    )
    codes_unmapped = [f.code for f in f_unmapped]
    assert "E1_TARGET_BINARY_UNMAPPED" in codes_unmapped
    assert "E1_TARGET_CLASS_COUNT_INVALID" not in codes_unmapped

    # Case 2: 3 classes -> E1_TARGET_CLASS_COUNT_INVALID only
    t_prof_3classes = TargetProfile(
        column_name="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        numeric_stats=None,
        skewness=None,
        outliers_count_iqr_fences=None,
        class_frequencies=(
            CategoryFrequency(value="A", count=40, proportion=0.4),
            CategoryFrequency(value="B", count=30, proportion=0.3),
            CategoryFrequency(value="C", count=30, proportion=0.3),
        ),
        majority_minority_ratio=40 / 30,
    )
    f_3classes = evaluate_findings(
        schema_target_col="target",
        schema_group_col=None,
        schema_task_type=TaskType.BINARY_CLASSIFICATION,
        n_rows=100,
        column_profiles={"target": col_prof},
        target_profile=t_prof_3classes,
        group_profile=None,
        duplicate_profile=dup_prof,
        config=config,
    )
    codes_3classes = [f.code for f in f_3classes]
    assert "E1_TARGET_CLASS_COUNT_INVALID" in codes_3classes
    assert "E1_TARGET_BINARY_UNMAPPED" not in codes_3classes

    # Case 3: Exactly {0, 1} classes -> neither is emitted
    t_prof_mapped = TargetProfile(
        column_name="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        numeric_stats=None,
        skewness=None,
        outliers_count_iqr_fences=None,
        class_frequencies=(
            CategoryFrequency(value=0, count=50, proportion=0.5),
            CategoryFrequency(value=1, count=50, proportion=0.5),
        ),
        majority_minority_ratio=1.0,
    )
    f_mapped = evaluate_findings(
        schema_target_col="target",
        schema_group_col=None,
        schema_task_type=TaskType.BINARY_CLASSIFICATION,
        n_rows=100,
        column_profiles={"target": col_prof},
        target_profile=t_prof_mapped,
        group_profile=None,
        duplicate_profile=dup_prof,
        config=config,
    )
    codes_mapped = [f.code for f in f_mapped]
    assert "E1_TARGET_CLASS_COUNT_INVALID" not in codes_mapped
    assert "E1_TARGET_BINARY_UNMAPPED" not in codes_mapped


def test_prof_01_structural_profile_and_column_profiles() -> None:
    """PROF-01: profile_dataset returns immutable DatasetProfile matching bundle metadata and ColumnProfile per column."""
    import numpy as np
    from experimental_ml.core.enums import TaskType
    from experimental_ml.data import (
        DatasetProfile,
        DatasetSchemaSpec,
        load_dataset,
        profile_dataset,
    )

    data = {
        "x1": [1.0, 2.0, np.nan, 4.0],
        "x2": ["cat", "dog", "cat", "bird"],
        "target": [10.0, 20.0, 30.0, 40.0],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.REGRESSION)
    bundle = load_dataset(data, schema=schema)

    profile = profile_dataset(bundle)

    assert isinstance(profile, DatasetProfile)
    assert profile.source_dataset_hash == bundle.dataset_hash
    assert profile.n_rows == bundle.n_rows == 4
    assert profile.n_cols == bundle.n_cols == 3
    assert profile.memory_bytes == bundle.memory_bytes

    # Every column present in profile.columns
    for col_name in bundle.columns:
        assert col_name in profile.columns
        cp = profile.columns[col_name]
        desc = bundle.descriptors[col_name]
        assert cp.name == col_name
        assert cp.physical_type == desc.physical_type
        assert cp.semantic_type == desc.semantic_type
        assert cp.role == desc.role
        assert cp.n_missing == desc.n_missing

    # x1 missing proportion is 1/4 = 0.25
    assert profile.columns["x1"].n_missing == 1
    assert profile.columns["x1"].missing_proportion == 0.25


def test_prof_10_immutability_and_determinism() -> None:
    """PROF-10: profile_dataset leaves bundle untouched and repeated calls produce identical profiles."""
    import numpy as np
    from experimental_ml.core.enums import TaskType
    from experimental_ml.data import DatasetSchemaSpec, load_dataset, profile_dataset

    data = {
        "feat_a": [10, 20, 30, 40],
        "feat_b": ["yes", "no", "yes", "no"],
        "label": [1, 0, 1, 0],
    }
    schema = DatasetSchemaSpec(target_col="label", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)

    initial_hash = bundle.dataset_hash
    initial_arrays = {col: arr.copy() for col, arr in bundle.columns.items()}

    profile_1 = profile_dataset(bundle)

    # Immutability check
    assert bundle.dataset_hash == initial_hash
    for col, orig_arr in initial_arrays.items():
        assert len(bundle.columns[col]) == len(orig_arr)
        for v1, v2 in zip(bundle.columns[col], orig_arr):
            assert (v1 == v2) or (v1 != v1 and v2 != v2)

    profile_2 = profile_dataset(bundle)

    # Determinism check
    assert profile_1 == profile_2
    assert profile_1.findings == profile_2.findings




