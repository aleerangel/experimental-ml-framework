"""Pure NumPy inner cross-validation index partitioning for hyperparameter tuning."""

from __future__ import annotations

import numpy as np

from experimental_ml.core.findings import ContractViolationError

__all__ = ["split_inner_folds"]


def split_inner_folds(
    n_samples: int,
    n_folds: int,
    seed: int | None = None,
    shuffle: bool = False,
) -> tuple[tuple[np.ndarray, np.ndarray], ...]:
    """Partition sample indices [0, n_samples - 1] into n_folds disjoint inner train/val pairs.

    Parameters
    ----------
    n_samples:
        Total number of training observations in the outer fold.
    n_folds:
        Number of inner cross-validation folds (must be >= 2).
    seed:
        Random seed for shuffling.
    shuffle:
        Whether to shuffle indices before partitioning.

    Returns
    -------
    tuple[tuple[np.ndarray, np.ndarray], ...]
        Sequence of (train_indices, val_indices) arrays.

    Raises
    ------
    ContractViolationError
        If n_samples < n_folds or n_folds < 2.
    """
    if not isinstance(n_samples, int) or not isinstance(n_folds, int):
        raise ContractViolationError("n_samples and n_folds must be integers")

    if n_folds < 2:
        raise ContractViolationError(
            f"Inner cross-validation requires at least 2 folds, got {n_folds!r}"
        )

    if n_samples < n_folds:
        raise ContractViolationError(
            f"Insufficient samples {n_samples} for {n_folds} inner cross-validation folds"
        )

    indices = np.arange(n_samples, dtype=np.int64)
    if shuffle:
        rng = np.random.default_rng(seed)
        rng.shuffle(indices)

    # Standard K-Fold partition distributing remainder across first folds
    fold_sizes = np.full(n_folds, n_samples // n_folds, dtype=np.int64)
    fold_sizes[: n_samples % n_folds] += 1

    current = 0
    splits = []
    for fold_size in fold_sizes:
        start, stop = current, current + fold_size
        val_idx = indices[start:stop]
        # Train indices are all indices except val_idx
        train_mask = np.ones(n_samples, dtype=bool)
        train_mask[start:stop] = False
        train_idx = indices[train_mask]

        # Defensive assertions
        train_idx.setflags(write=False)
        val_idx.setflags(write=False)
        splits.append((train_idx, val_idx))
        current = stop

    return tuple(splits)
