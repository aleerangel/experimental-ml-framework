"""Unit tests for partition splitters (K-Fold, Stratified K-Fold, Holdout)."""

import numpy as np
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ObservationId
from experimental_ml.validation.splitters import (
    holdout_split,
    kfold_split,
    stratified_kfold_split,
)


def test_kfold_split_disjointness_and_coverage() -> None:
    obs_ids = tuple(ObservationId(f"obs_{i}") for i in range(23))
    splits = kfold_split(obs_ids, n_splits=5, shuffle=True, seed=123)

    assert len(splits) == 5
    all_val_ids: list[ObservationId] = []

    for train_ids, val_ids in splits:
        # Disjointness
        assert set(train_ids).isdisjoint(set(val_ids))
        # Completeness
        assert set(train_ids) | set(val_ids) == set(obs_ids)
        all_val_ids.extend(val_ids)

    # Every observation validated exactly once
    assert len(all_val_ids) == 23
    assert set(all_val_ids) == set(obs_ids)

    # Fold sizes: 23 // 5 = 4, remainder 3 -> sizes: 5, 5, 5, 4, 4
    sizes = [len(s[1]) for s in splits]
    assert sorted(sizes, reverse=True) == [5, 5, 5, 4, 4]


def test_part_02_stratified_kfold_proportions() -> None:
    # 60 positive samples (60%), 40 negative samples (40%) = 100 total
    obs_ids = tuple(ObservationId(f"id_{i:03d}") for i in range(100))
    target = np.array([1] * 60 + [0] * 40, dtype=np.int64)

    splits = stratified_kfold_split(obs_ids, target, n_splits=5, shuffle=True, seed=42)

    assert len(splits) == 5
    all_val_ids: list[ObservationId] = []

    for train_ids, val_ids in splits:
        # Disjointness
        assert set(train_ids).isdisjoint(set(val_ids))
        # Total size per fold: 100 // 5 = 20
        assert len(val_ids) == 20
        assert len(train_ids) == 80

        # Check stratification in validation fold: 60% of 20 = 12, 40% of 20 = 8
        val_indices = [int(str(v).split("_")[1]) for v in val_ids]
        val_targets = target[val_indices]
        pos_count = np.sum(val_targets == 1)
        neg_count = np.sum(val_targets == 0)

        assert pos_count == 12  # exactly 60%
        assert neg_count == 8   # exactly 40%

        all_val_ids.extend(val_ids)

    assert len(all_val_ids) == 100
    assert set(all_val_ids) == set(obs_ids)


def test_holdout_split_proportions_and_disjointness() -> None:
    obs_ids = tuple(ObservationId(f"obs_{i}") for i in range(50))
    dev_ids, holdout_ids = holdout_split(obs_ids, holdout_fraction=0.2, seed=42)

    assert len(holdout_ids) == 10  # 20% of 50
    assert len(dev_ids) == 40      # 80% of 50
    assert set(dev_ids).isdisjoint(set(holdout_ids))
    assert set(dev_ids) | set(holdout_ids) == set(obs_ids)
