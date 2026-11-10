"""Unit tests for exploratory feature analysis engine (EXP-01, EXP-06, EXP-08)."""

from types import MappingProxyType
import numpy as np
import pytest

from experimental_ml.core.enums import MetricStatus, TaskType
from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.data.preparation import SanitizedDatasetView
from experimental_ml.data.schema import DatasetSchemaSpec
from experimental_ml.data.types import ObservationId
from experimental_ml.features.exploration import explore_features
from experimental_ml.features.types import (
    METHODOLOGICAL_WARNINGS,
    SCOPE_EXPLORATORY_FULL_DATA,
)


def _make_dummy_sanitized_view(
    columns: dict[str, np.ndarray],
    target_col: str = "target",
    task_type: TaskType = TaskType.REGRESSION,
    candidate_features: tuple[str, ...] | None = None,
    dataset_hash: str = "sha256_dummy_hash_for_testing",
) -> SanitizedDatasetView:
    """Helper to assemble a valid immutable SanitizedDatasetView for unit tests."""
    n_rows = len(next(iter(columns.values())))
    obs_ids = tuple(ObservationId(f"obs_{i:04d}") for i in range(n_rows))
    if candidate_features is None:
        candidate_features = tuple(col for col in columns if col != target_col)

    schema = DatasetSchemaSpec(
        target_col=target_col,
        task_type=task_type,
    )

    return SanitizedDatasetView(
        columns=MappingProxyType(columns),
        schema=schema,
        observation_ids=obs_ids,
        candidate_feature_cols=candidate_features,
        dropped_observation_ids=(),
        target_label_mapping=None,
        deferred_rules=(),
        source_dataset_hash=dataset_hash,
        source_plan_digest="plan_digest_abc",
        dataset_hash=dataset_hash,
    )


def test_exp_01_mandatory_scope_and_warnings() -> None:
    """Proof C1: Verify explore_features returns report with mandatory scope, hash, and warnings (EXP-01)."""
    np.random.seed(42)
    n = 100
    x1 = np.random.randn(n)
    x2 = np.random.randn(n)
    y = 2.0 * x1 + 0.5 * x2 + np.random.randn(n) * 0.1

    view = _make_dummy_sanitized_view(
        columns={"feat_1": x1, "feat_2": x2, "target": y},
        target_col="target",
        task_type=TaskType.REGRESSION,
        dataset_hash="dataset_hash_12345",
    )

    report = explore_features(view)

    # Invariants mandated by CA-E2-01
    assert report.scope == SCOPE_EXPLORATORY_FULL_DATA
    assert report.dataset_hash == "dataset_hash_12345"
    assert report.task_type == TaskType.REGRESSION
    assert report.warnings == METHODOLOGICAL_WARNINGS
    assert len(report.warnings) == 3

    # Check associations exist
    feature_names = {a.feature_name for a in report.target_associations}
    assert feature_names == {"feat_1", "feat_2"}


def test_exp_06_predictor_redundancy_and_sorting() -> None:
    """Proof C6: Verify predictor redundancy matrix and canonical sorting of high redundancy pairs (EXP-06)."""
    n = 100
    base = np.linspace(0.0, 10.0, n)
    # feat_a and feat_b have correlation ~ 0.99
    feat_a = base + np.sin(base) * 0.1
    feat_b = base + np.sin(base) * 0.2
    # feat_c has correlation ~ 0.88 with feat_a
    feat_c = base + np.cos(base) * 2.0
    # feat_d has low correlation
    feat_d = np.sin(base * 5.0)
    target = base * 2.0

    view = _make_dummy_sanitized_view(
        columns={
            "feat_a": feat_a,
            "feat_b": feat_b,
            "feat_c": feat_c,
            "feat_d": feat_d,
            "target": target,
        },
        target_col="target",
        task_type=TaskType.REGRESSION,
    )

    report = explore_features(view, redundancy_threshold=0.85)

    # 1. Check pairwise matrix symmetry and diagonal
    matrix = report.pairwise_redundancy_matrix
    for f in ["feat_a", "feat_b", "feat_c", "feat_d"]:
        assert matrix[f][f] == 1.0
        for f2 in ["feat_a", "feat_b", "feat_c", "feat_d"]:
            assert matrix[f][f2] == matrix[f2][f]

    # 2. Check high redundancy pairs: only pairs with |val| >= 0.85
    pairs = report.high_redundancy_pairs
    assert len(pairs) >= 1
    for p in pairs:
        assert abs(p.value) >= 0.85
        assert p.status == MetricStatus.VALID

    # 3. Check canonical ordering: sorted by descending magnitude
    values = [abs(p.value) for p in pairs]
    assert values == sorted(values, reverse=True)


def test_exp_08_input_validation() -> None:
    """Proof C8: Verify validation of view, parameters, and empty features (EXP-08)."""
    # 1. Invalid view type
    with pytest.raises(ContractViolationError, match="requires a SanitizedDatasetView"):
        explore_features("not_a_view")  # type: ignore

    # 2. Invalid redundancy_threshold
    view = _make_dummy_sanitized_view(
        columns={"feat_1": np.array([1.0, 2.0]), "target": np.array([1.0, 2.0])}
    )
    with pytest.raises(ConfigurationError, match="redundancy_threshold"):
        explore_features(view, redundancy_threshold=-0.1)

    with pytest.raises(ConfigurationError, match="redundancy_threshold"):
        explore_features(view, redundancy_threshold=1.5)

    with pytest.raises(ConfigurationError, match="redundancy_threshold"):
        explore_features(view, redundancy_threshold=float("nan"))

    # 3. Empty candidate features
    empty_features_view = _make_dummy_sanitized_view(
        columns={"target": np.array([1.0, 2.0])},
        candidate_features=(),
    )
    with pytest.raises(ContractViolationError, match="no candidate feature columns"):
        explore_features(empty_features_view)


def test_classification_feature_associations() -> None:
    """Verify that classification tasks dispatch Correlation Ratio and Cramér's V appropriately."""
    n = 60
    # Discrete target
    target = np.array(["class_0"] * 30 + ["class_1"] * 30, dtype=object)
    # Numeric feature
    num_feat = np.array([1.0] * 30 + [10.0] * 30, dtype=np.float64)
    # Categorical feature
    cat_feat = np.array(["cat_A"] * 25 + ["cat_B"] * 5 + ["cat_A"] * 5 + ["cat_B"] * 25, dtype=object)

    view = _make_dummy_sanitized_view(
        columns={"num_feat": num_feat, "cat_feat": cat_feat, "target": target},
        target_col="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
    )

    report = explore_features(view)

    metrics_by_feat = {a.feature_name: a for a in report.target_associations}
    assert metrics_by_feat["num_feat"].metric_name == "CORRELATION_RATIO"
    assert pytest.approx(metrics_by_feat["num_feat"].value, abs=1e-5) == 1.0

    assert metrics_by_feat["cat_feat"].metric_name == "CRAMERS_V"
    assert metrics_by_feat["cat_feat"].value > 0.0
