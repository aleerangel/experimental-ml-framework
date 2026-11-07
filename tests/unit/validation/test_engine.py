"""Unit tests for PartitionPlan builder engine (validation/engine.py).

Verifies PART-01, PART-06, PART-08, PART-09, PART-10 and Checks C1, C6.
"""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ObservationId
from experimental_ml.validation.engine import _compute_plan_id, build_partition_plan
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


class MockSchema:
    def __init__(
        self,
        target_col: str | None = "target",
        group_col: str | None = "group",
        time_col: str | None = "timestamp",
    ):
        self.target_col = target_col
        self.group_col = group_col
        self.time_col = time_col


class MockDatasetView:
    def __init__(
        self,
        observation_ids: list[ObservationId] | tuple[ObservationId, ...],
        columns: dict[str, np.ndarray] | None = None,
        schema: MockSchema | None = None,
        dataset_hash: str = "mock_hash_abc123",
    ):
        self.observation_ids = tuple(observation_ids)
        self.columns = columns or {}
        self.schema = schema or MockSchema()
        self.dataset_hash = dataset_hash


def test_part_01_kfold_cv_only() -> None:
    """PART-01 (Check C1): build_partition_plan with CV_ONLY and KFOLD partitions into K folds."""
    obs_ids = [ObservationId(f"id_{i}") for i in range(30)]
    view = MockDatasetView(observation_ids=obs_ids)

    config = PartitionConfig(
        strategy=PartitionStrategy.KFOLD,
        regime=EvaluationRegime.CV_ONLY,
        n_splits=5,
        shuffle=False,
    )

    plan = build_partition_plan(view, config)

    assert plan.regime == EvaluationRegime.CV_ONLY
    assert plan.strategy == PartitionStrategy.KFOLD
    assert plan.development_ids == tuple(obs_ids)
    assert plan.holdout_ids == ()
    assert len(plan.folds) == 5

    all_val_ids: list[ObservationId] = []
    for k, fold in enumerate(plan.folds):
        assert fold.fold_index == k
        assert len(fold.val_ids) == 6
        assert len(fold.train_ids) == 24
        # Train and val are strictly disjoint
        assert set(fold.train_ids).isdisjoint(set(fold.val_ids))
        # Union is exactly development_ids
        assert set(fold.train_ids) | set(fold.val_ids) == set(obs_ids)
        all_val_ids.extend(fold.val_ids)

    # All validation sets form a partition of development_ids
    assert set(all_val_ids) == set(obs_ids)
    assert len(all_val_ids) == len(obs_ids)


def test_part_06_holdout_separation() -> None:
    """PART-06 (Check C6): build_partition_plan with CV_AND_HOLDOUT partitions holdout and dev."""
    obs_ids = [ObservationId(f"obs_{i}") for i in range(50)]
    target = np.array([0, 1] * 25)
    view = MockDatasetView(
        observation_ids=obs_ids,
        columns={"target": target},
        schema=MockSchema(target_col="target"),
    )

    config = PartitionConfig(
        strategy=PartitionStrategy.KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=3,
        holdout_fraction=0.2,
        shuffle=False,
        master_seed=42,
    )

    plan = build_partition_plan(view, config)

    assert plan.regime == EvaluationRegime.CV_AND_HOLDOUT
    assert len(plan.holdout_ids) == 10
    assert len(plan.development_ids) == 40
    # Disjointness between holdout and development
    assert set(plan.holdout_ids).isdisjoint(set(plan.development_ids))
    assert set(plan.holdout_ids) | set(plan.development_ids) == set(obs_ids)

    # CV folds partition ONLY development_ids
    dev_set = set(plan.development_ids)
    holdout_set = set(plan.holdout_ids)

    assert len(plan.folds) == 3
    for fold in plan.folds:
        assert set(fold.train_ids).issubset(dev_set)
        assert set(fold.val_ids).issubset(dev_set)
        assert set(fold.train_ids).isdisjoint(holdout_set)
        assert set(fold.val_ids).isdisjoint(holdout_set)
        assert set(fold.train_ids).isdisjoint(set(fold.val_ids))


def test_holdout_only_regime() -> None:
    """Verify HOLDOUT_ONLY creates exactly 1 fold where train is dev and val is holdout."""
    obs_ids = [ObservationId(f"obs_{i}") for i in range(20)]
    view = MockDatasetView(observation_ids=obs_ids)

    config = PartitionConfig(
        strategy=PartitionStrategy.HOLDOUT,
        regime=EvaluationRegime.HOLDOUT_ONLY,
        holdout_fraction=0.25,
        shuffle=False,
        master_seed=42,
    )

    plan = build_partition_plan(view, config)

    assert plan.regime == EvaluationRegime.HOLDOUT_ONLY
    assert len(plan.holdout_ids) == 5
    assert len(plan.development_ids) == 15
    assert len(plan.folds) == 1
    assert plan.folds[0].train_ids == plan.development_ids
    assert plan.folds[0].val_ids == plan.holdout_ids


def test_missing_column_raises_configuration_error() -> None:
    """Missing target or group column in data view raises ConfigurationError."""
    obs_ids = [ObservationId(f"obs_{i}") for i in range(10)]
    view = MockDatasetView(observation_ids=obs_ids, columns={})

    # Stratified kfold without target column
    config_strat = PartitionConfig(
        strategy=PartitionStrategy.STRATIFIED_KFOLD,
        regime=EvaluationRegime.CV_ONLY,
        n_splits=2,
    )
    with pytest.raises(ConfigurationError, match="target column"):
        build_partition_plan(view, config_strat)

    # Group kfold without group column
    config_group = PartitionConfig(
        strategy=PartitionStrategy.GROUP_KFOLD,
        regime=EvaluationRegime.CV_ONLY,
        group_col="non_existent_group",
        n_splits=2,
    )
    with pytest.raises(ConfigurationError, match="group column"):
        build_partition_plan(view, config_group)

    # Temporal without time column
    config_temp = PartitionConfig(
        strategy=PartitionStrategy.TEMPORAL,
        regime=EvaluationRegime.CV_ONLY,
        time_col="non_existent_time",
        n_splits=2,
    )
    with pytest.raises(ConfigurationError, match="time column"):
        build_partition_plan(view, config_temp)
