"""Unit tests for partition splitters (K-Fold, Stratified K-Fold, Holdout)."""

import numpy as np
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ObservationId
from experimental_ml.validation.splitters import (
    bootstrap_split,
    group_kfold_split,
    holdout_split,
    kfold_split,
    stratified_kfold_split,
    temporal_split,
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


def test_part_03_group_kfold_disjointness() -> None:
    # 8 unique groups, 30 samples total
    obs_ids = tuple(ObservationId(f"id_{i:02d}") for i in range(30))
    # Groups: g0 (5), g1 (5), g2 (4), g3 (4), g4 (3), g5 (3), g6 (3), g7 (3)
    groups = np.array(
        ["g0"] * 5 + ["g1"] * 5 + ["g2"] * 4 + ["g3"] * 4 + ["g4"] * 3 + ["g5"] * 3 + ["g6"] * 3 + ["g7"] * 3,
        dtype=object,
    )

    splits = group_kfold_split(obs_ids, groups, n_splits=4, shuffle=True, seed=42)
    assert len(splits) == 4

    all_val_ids: list[ObservationId] = []
    group_lookup = {obs: grp for obs, grp in zip(obs_ids, groups)}

    for train_ids, val_ids in splits:
        train_groups = {group_lookup[oid] for oid in train_ids}
        val_groups = {group_lookup[oid] for oid in val_ids}

        # Strict group non-overlap: Groups(Train) ∩ Groups(Val) == ∅
        assert train_groups.isdisjoint(val_groups)
        all_val_ids.extend(val_ids)

    # Every sample validated exactly once
    assert len(all_val_ids) == 30
    assert set(all_val_ids) == set(obs_ids)

    # Error when unique groups < n_splits
    few_groups = np.array(["g1"] * 10 + ["g2"] * 10, dtype=object)
    with pytest.raises(ConfigurationError, match="Number of unique groups"):
        group_kfold_split(obs_ids[:20], few_groups, n_splits=3)


def test_part_04_temporal_monotonicity() -> None:
    obs_ids = tuple(ObservationId(f"id_{i}") for i in range(30))
    # Dates or integer timestamps
    times = np.array([2020 + i for i in range(30)], dtype=np.int64)

    splits = temporal_split(obs_ids, times, n_splits=4)
    assert len(splits) == 4

    time_lookup = {obs: t for obs, t in zip(obs_ids, times)}

    for train_ids, val_ids in splits:
        train_times = [time_lookup[oid] for oid in train_ids]
        val_times = [time_lookup[oid] for oid in val_ids]

        # max(Time(Train_k)) <= min(Time(Val_k))
        assert max(train_times) <= min(val_times)


def test_part_05_bootstrap_oob() -> None:
    obs_ids = tuple(ObservationId(f"id_{i}") for i in range(50))
    splits = bootstrap_split(obs_ids, n_bootstraps=10, seed=42)

    assert len(splits) == 10

    for train_ids, val_ids in splits:
        # Train has size N (sampled with replacement)
        assert len(train_ids) == 50
        # Val contains only out-of-bag observations: Train ∩ Val == ∅
        assert set(train_ids).isdisjoint(set(val_ids))
        # Union of unique train + val is all observations
        assert set(train_ids) | set(val_ids) == set(obs_ids)
        # OOB fraction is roughly ~36.8% (typically between 10 and 28 for N=50)
        assert 5 <= len(val_ids) <= 35
