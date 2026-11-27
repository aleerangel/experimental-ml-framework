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
    y: np.ndarray | None = None,
    groups: np.ndarray | None = None,
    strategy: str | None = None,
) -> tuple[tuple[np.ndarray, np.ndarray], ...]:
    """Partition sample indices [0, n_samples - 1] into n_folds disjoint inner train/val pairs.

    Supports KFOLD (default), STRATIFIED_KFOLD, GROUP_KFOLD / STRATIFIED_GROUP_KFOLD, and TEMPORAL.
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

    strat = strategy.strip().upper() if isinstance(strategy, str) and strategy.strip() else "KFOLD"

    if strat == "TEMPORAL":
        if n_samples < n_folds + 1:
            raise ContractViolationError(
                f"Insufficient samples {n_samples} for {n_folds} temporal inner folds"
            )
        block_sizes = np.full(n_folds + 1, n_samples // (n_folds + 1), dtype=np.int64)
        block_sizes[: n_samples % (n_folds + 1)] += 1
        bounds: list[tuple[int, int]] = []
        pos = 0
        for sz in block_sizes:
            bounds.append((pos, pos + int(sz)))
            pos += int(sz)
        splits = []
        for k in range(n_folds):
            val_start, val_stop = bounds[k + 1]
            train_idx = np.arange(0, val_start, dtype=np.int64)
            val_idx = np.arange(val_start, val_stop, dtype=np.int64)
            train_idx.setflags(write=False)
            val_idx.setflags(write=False)
            splits.append((train_idx, val_idx))
        return tuple(splits)

    if strat in ("GROUP_KFOLD", "STRATIFIED_GROUP_KFOLD") and groups is not None:
        grp_arr = np.asarray(groups).ravel()
        if len(grp_arr) != n_samples:
            raise ContractViolationError(
                f"groups length ({len(grp_arr)}) must match n_samples ({n_samples})"
            )
        unique_groups = sorted(set(grp_arr.tolist()), key=str)
        if len(unique_groups) < n_folds:
            raise ContractViolationError(
                f"Insufficient unique groups ({len(unique_groups)}) for {n_folds} inner folds"
            )
        if shuffle:
            rng = np.random.default_rng(seed)
            perm = rng.permutation(len(unique_groups))
            unique_groups = [unique_groups[int(i)] for i in perm]
        fold_bins: list[list[int]] = [[] for _ in range(n_folds)]
        for g_idx, g_val in enumerate(unique_groups):
            target_fold = min(range(n_folds), key=lambda f: (len(fold_bins[f]), f))
            indices_for_g = np.where(grp_arr == g_val)[0].tolist()
            fold_bins[target_fold].extend(indices_for_g)
        splits = []
        for f_idx in range(n_folds):
            val_idx = np.array(sorted(fold_bins[f_idx]), dtype=np.int64)
            train_mask = np.ones(n_samples, dtype=bool)
            train_mask[val_idx] = False
            train_idx = np.arange(n_samples, dtype=np.int64)[train_mask]
            train_idx.setflags(write=False)
            val_idx.setflags(write=False)
            splits.append((train_idx, val_idx))
        return tuple(splits)

    if strat == "STRATIFIED_KFOLD" and y is not None:
        y_arr = np.asarray(y).ravel()
        if len(y_arr) != n_samples:
            raise ContractViolationError(
                f"y length ({len(y_arr)}) must match n_samples ({n_samples})"
            )
        fold_bins = [[] for _ in range(n_folds)]
        rng = np.random.default_rng(seed) if shuffle else None
        unique_classes = sorted(set(y_arr.tolist()), key=str)
        for cls_val in unique_classes:
            cls_indices = np.where(y_arr == cls_val)[0]
            if rng is not None:
                rng.shuffle(cls_indices)
            for pos, idx_val in enumerate(cls_indices):
                fold_bins[pos % n_folds].append(int(idx_val))
        splits = []
        for f_idx in range(n_folds):
            val_idx = np.array(sorted(fold_bins[f_idx]), dtype=np.int64)
            train_mask = np.ones(n_samples, dtype=bool)
            train_mask[val_idx] = False
            train_idx = np.arange(n_samples, dtype=np.int64)[train_mask]
            train_idx.setflags(write=False)
            val_idx.setflags(write=False)
            splits.append((train_idx, val_idx))
        return tuple(splits)

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
