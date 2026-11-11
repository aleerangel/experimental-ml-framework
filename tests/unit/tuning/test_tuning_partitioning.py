"""Unit tests for inner fold index partitioning (TUN-04)."""

import numpy as np
import pytest
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.tuning.partitioning import split_inner_folds


def test_m43_04_01_split_inner_folds_disjointness() -> None:
    """C13: split_inner_folds partitions indices into disjoint inner folds."""
    n_samples = 25
    n_folds = 5
    splits = split_inner_folds(n_samples=n_samples, n_folds=n_folds)
    assert len(splits) == n_folds

    all_val_indices = []
    for train_idx, val_idx in splits:
        # Disjointness: Train_inner \cap Val_inner = \emptyset
        overlap = np.intersect1d(train_idx, val_idx)
        assert len(overlap) == 0

        # Coverage: train + val = all indices
        combined = np.union1d(train_idx, val_idx)
        assert len(combined) == n_samples
        all_val_indices.extend(val_idx.tolist())

    # Union of all validation folds covers exact index range 0..N-1 with no duplicates
    assert sorted(all_val_indices) == list(range(n_samples))


def test_m43_04_02_split_inner_folds_training_confinement() -> None:
    """C14: split_inner_folds operates strictly on training indices without external leakage."""
    n_train = 50
    splits = split_inner_folds(n_samples=n_train, n_folds=3, seed=42, shuffle=True)
    assert len(splits) == 3

    for train_idx, val_idx in splits:
        # All indices are strictly within [0, n_train - 1]
        assert np.all(train_idx >= 0) and np.all(train_idx < n_train)
        assert np.all(val_idx >= 0) and np.all(val_idx < n_train)
        # Arrays are read-only
        assert not train_idx.flags.writeable
        assert not val_idx.flags.writeable


def test_m43_04_03_split_inner_folds_insufficient_samples() -> None:
    """C15: split_inner_folds raises ContractViolationError when N < K_inner."""
    # N = 2, K = 3
    with pytest.raises(ContractViolationError, match="Insufficient samples 2 for 3 inner cross-validation folds"):
        split_inner_folds(n_samples=2, n_folds=3)

    # N = 0
    with pytest.raises(ContractViolationError, match="Insufficient samples 0 for 5 inner cross-validation folds"):
        split_inner_folds(n_samples=0, n_folds=5)

    # K < 2
    with pytest.raises(ContractViolationError, match="requires at least 2 folds"):
        split_inner_folds(n_samples=10, n_folds=1)
