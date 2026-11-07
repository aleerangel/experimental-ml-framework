"""Pure functional partition splitters.

Implements K-Fold, Stratified K-Fold, and Holdout splits compliant with ADR-002, RF4.1.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence

import numpy as np

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ObservationId


def kfold_split(
    observation_ids: Sequence[ObservationId],
    n_splits: int,
    shuffle: bool = True,
    seed: int = 42,
) -> list[tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]]:
    """Partition observation IDs into K folds for cross-validation.

    Args:
        observation_ids: Sequence of observation identifiers.
        n_splits: Number of folds (K >= 2).
        shuffle: Whether to permute indices before partitioning.
        seed: Random seed for deterministic permutation.

    Returns:
        List of K tuples: (train_ids, val_ids).
    """
    n = len(observation_ids)
    if n_splits < 2:
        raise ConfigurationError(f"n_splits must be >= 2, got {n_splits}")
    if n < n_splits:
        raise ConfigurationError(f"Cannot split {n} observations into {n_splits} folds")

    indices = np.arange(n)
    if shuffle:
        rng = np.random.default_rng(seed)
        indices = rng.permutation(n)

    # Compute fold sizes with remainder distributed across leading folds
    fold_sizes = np.full(n_splits, n // n_splits, dtype=int)
    fold_sizes[: n % n_splits] += 1

    current = 0
    splits: list[tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]] = []

    for fold_size in fold_sizes:
        start, end = current, current + fold_size
        val_idx = indices[start:end]
        train_idx = np.concatenate([indices[:start], indices[end:]])

        # Preserve relative order from original observation_ids for stability
        val_idx_sorted = np.sort(val_idx)
        train_idx_sorted = np.sort(train_idx)

        val_ids = tuple(observation_ids[i] for i in val_idx_sorted)
        train_ids = tuple(observation_ids[i] for i in train_idx_sorted)
        splits.append((train_ids, val_ids))

        current = end

    return splits


def stratified_kfold_split(
    observation_ids: Sequence[ObservationId],
    target: np.ndarray,
    n_splits: int,
    shuffle: bool = True,
    seed: int = 42,
) -> list[tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]]:
    """Partition observation IDs into K folds preserving class proportions (PART-02).

    Args:
        observation_ids: Sequence of observation identifiers.
        target: 1D array of class labels.
        n_splits: Number of folds (K >= 2).
        shuffle: Whether to permute class indices before partitioning.
        seed: Random seed for deterministic permutation.

    Returns:
        List of K tuples: (train_ids, val_ids).
    """
    n = len(observation_ids)
    if len(target) != n:
        raise ConfigurationError(
            f"target length ({len(target)}) does not match observation_ids length ({n})"
        )
    if n_splits < 2:
        raise ConfigurationError(f"n_splits must be >= 2, got {n_splits}")

    # Group indices by class label
    class_indices: dict[Any, list[int]] = defaultdict(list)
    for idx, label in enumerate(target):
        class_indices[label].append(idx)

    # Verify each class has at least 1 sample
    for label, idxs in class_indices.items():
        if len(idxs) < n_splits:
            # We still partition, but warn/allow standard rounding
            pass

    rng = np.random.default_rng(seed)
    fold_val_indices: list[list[int]] = [[] for _ in range(n_splits)]

    # Deterministic class order
    sorted_classes = sorted(class_indices.keys(), key=lambda c: (type(c).__name__, str(c)))

    for c in sorted_classes:
        c_idxs = np.array(class_indices[c], dtype=int)
        if shuffle:
            c_idxs = rng.permutation(c_idxs)

        n_c = len(c_idxs)
        c_fold_sizes = np.full(n_splits, n_c // n_splits, dtype=int)
        c_fold_sizes[: n_c % n_splits] += 1

        curr = 0
        for k, f_size in enumerate(c_fold_sizes):
            fold_val_indices[k].extend(c_idxs[curr : curr + f_size])
            curr += f_size

    # Build splits
    splits: list[tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]] = []
    all_indices_set = set(range(n))

    for k in range(n_splits):
        val_idx = np.array(sorted(fold_val_indices[k]), dtype=int)
        train_idx = np.array(sorted(all_indices_set - set(val_idx)), dtype=int)

        val_ids = tuple(observation_ids[i] for i in val_idx)
        train_ids = tuple(observation_ids[i] for i in train_idx)
        splits.append((train_ids, val_ids))

    return splits


def holdout_split(
    observation_ids: Sequence[ObservationId],
    holdout_fraction: float,
    stratify: bool = False,
    target: np.ndarray | None = None,
    seed: int = 42,
) -> tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]:
    """Partition observation IDs into development and holdout subsets (PART-06).

    Args:
        observation_ids: Sequence of observation identifiers.
        holdout_fraction: Fraction of observations to allocate to holdout (0.0 < fraction < 1.0).
        stratify: Whether to stratify holdout allocation across target classes.
        target: Optional 1D target array for stratification.
        seed: Random seed for deterministic partition.

    Returns:
        Tuple of (development_ids, holdout_ids).
    """
    n = len(observation_ids)
    if not (0.0 < holdout_fraction < 1.0):
        raise ConfigurationError(f"holdout_fraction must be in (0.0, 1.0), got {holdout_fraction}")

    rng = np.random.default_rng(seed)

    if stratify and target is not None:
        if len(target) != n:
            raise ConfigurationError("target length does not match observation_ids length")
        class_indices: dict[Any, list[int]] = defaultdict(list)
        for idx, label in enumerate(target):
            class_indices[label].append(idx)

        holdout_idx_list: list[int] = []
        for label, idxs in sorted(class_indices.items(), key=lambda x: str(x[0])):
            c_idxs = rng.permutation(np.array(idxs, dtype=int))
            n_h = int(np.round(len(c_idxs) * holdout_fraction))
            n_h = max(1, min(n_h, len(c_idxs) - 1)) if len(c_idxs) >= 2 else n_h
            holdout_idx_list.extend(c_idxs[:n_h])

        holdout_idx = np.array(sorted(holdout_idx_list), dtype=int)
    else:
        n_holdout = int(np.round(n * holdout_fraction))
        n_holdout = max(1, min(n_holdout, n - 1))
        perm = rng.permutation(n)
        holdout_idx = np.sort(perm[:n_holdout])

    holdout_set = set(holdout_idx)
    dev_idx = np.array([i for i in range(n) if i not in holdout_set], dtype=int)

    development_ids = tuple(observation_ids[i] for i in dev_idx)
    holdout_ids = tuple(observation_ids[i] for i in holdout_idx)

    return development_ids, holdout_ids


def group_kfold_split(
    observation_ids: Sequence[ObservationId],
    groups: np.ndarray,
    n_splits: int,
    shuffle: bool = True,
    seed: int = 42,
) -> list[tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]]:
    """Partition observation IDs into K folds ensuring strict group non-overlap (PART-03).

    Args:
        observation_ids: Sequence of observation identifiers.
        groups: 1D array of group identifiers.
        n_splits: Number of folds (K >= 2).
        shuffle: Whether to randomize group order before bin packing.
        seed: Random seed for deterministic allocation.

    Returns:
        List of K tuples: (train_ids, val_ids).

    Raises:
        ConfigurationError: If unique group count < n_splits.
    """
    n = len(observation_ids)
    if len(groups) != n:
        raise ConfigurationError(
            f"groups length ({len(groups)}) does not match observation_ids length ({n})"
        )
    if n_splits < 2:
        raise ConfigurationError(f"n_splits must be >= 2, got {n_splits}")

    # Map groups to indices
    group_map: dict[Any, list[int]] = defaultdict(list)
    for idx, g in enumerate(groups):
        group_map[g].append(idx)

    unique_groups = list(group_map.keys())
    if len(unique_groups) < n_splits:
        raise ConfigurationError(
            f"Number of unique groups ({len(unique_groups)}) is less than n_splits ({n_splits}) "
            "for GROUP_KFOLD strategy"
        )

    # Sort groups by count descending (greedy LPT bin-packing)
    # If shuffle, apply permutation first
    if shuffle:
        rng = np.random.default_rng(seed)
        perm = rng.permutation(len(unique_groups))
        shuffled_groups = [unique_groups[i] for i in perm]
    else:
        shuffled_groups = sorted(unique_groups, key=lambda g: (type(g).__name__, str(g)))

    # Stable sort by group size descending
    sorted_groups = sorted(shuffled_groups, key=lambda g: len(group_map[g]), reverse=True)

    # Bins tracking allocated sample counts and group indices
    bin_counts = [0] * n_splits
    bin_indices: list[list[int]] = [[] for _ in range(n_splits)]

    for g in sorted_groups:
        g_idxs = group_map[g]
        # Find bin with minimum sample count
        min_bin = int(np.argmin(bin_counts))
        bin_indices[min_bin].extend(g_idxs)
        bin_counts[min_bin] += len(g_idxs)

    splits: list[tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]] = []
    all_indices_set = set(range(n))

    for k in range(n_splits):
        val_idx = np.array(sorted(bin_indices[k]), dtype=int)
        train_idx = np.array(sorted(all_indices_set - set(val_idx)), dtype=int)

        val_ids = tuple(observation_ids[i] for i in val_idx)
        train_ids = tuple(observation_ids[i] for i in train_idx)
        splits.append((train_ids, val_ids))

    return splits


def bootstrap_split(
    observation_ids: Sequence[ObservationId],
    n_bootstraps: int = 100,
    seed: int = 42,
) -> list[tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]]:
    """Generate B bootstrap resamples with out-of-bag validation sets (PART-05).

    Args:
        observation_ids: Sequence of observation identifiers.
        n_bootstraps: Number of bootstrap repetitions (B >= 2).
        seed: Random seed for deterministic resampling.

    Returns:
        List of B tuples: (train_ids, val_ids).
    """
    n = len(observation_ids)
    if n_bootstraps < 2:
        raise ConfigurationError(f"n_bootstraps must be >= 2, got {n_bootstraps}")

    splits: list[tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]] = []
    rng_master = np.random.default_rng(seed)

    for b in range(n_bootstraps):
        b_seed = int(rng_master.integers(0, 2**31 - 1))
        rng_b = np.random.default_rng(b_seed)

        # Sample N indices with replacement
        sampled_indices = rng_b.choice(n, size=n, replace=True)
        train_ids = tuple(observation_ids[i] for i in sampled_indices)

        # Out-of-bag (OOB) indices
        oob_indices = np.sort(list(set(range(n)) - set(sampled_indices)))
        val_ids = tuple(observation_ids[i] for i in oob_indices)

        splits.append((train_ids, val_ids))

    return splits


def temporal_split(
    observation_ids: Sequence[ObservationId],
    times: np.ndarray,
    n_splits: int = 5,
) -> list[tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]]:
    """Partition observation IDs along a temporal dimension using an expanding window (PART-04).

    Ensures that max(Time(Train_k)) <= min(Time(Val_k)) for all folds, preventing future leakage.

    Args:
        observation_ids: Sequence of observation identifiers.
        times: 1D array of timestamps, dates or numeric times.
        n_splits: Number of temporal splits (K >= 2).

    Returns:
        List of K tuples: (train_ids, val_ids).
    """
    n = len(observation_ids)
    if len(times) != n:
        raise ConfigurationError(
            f"times length ({len(times)}) does not match observation_ids length ({n})"
        )
    if n_splits < 2:
        raise ConfigurationError(f"n_splits must be >= 2, got {n_splits}")
    if n < n_splits + 1:
        raise ConfigurationError(
            f"Cannot perform temporal split with {n} observations and {n_splits} splits"
        )

    # Sort indices by time, tie-breaking by original index
    sorted_indices = sorted(range(n), key=lambda i: (times[i], i))

    # Divide into n_splits + 1 segments
    n_segments = n_splits + 1
    seg_sizes = np.full(n_segments, n // n_segments, dtype=int)
    seg_sizes[: n % n_segments] += 1

    segments: list[list[int]] = []
    curr = 0
    for s_size in seg_sizes:
        segments.append(sorted_indices[curr : curr + s_size])
        curr += s_size

    splits: list[tuple[tuple[ObservationId, ...], tuple[ObservationId, ...]]] = []

    for k in range(n_splits):
        # Expanding window: train includes segments 0..k
        train_idx: list[int] = []
        for s in range(k + 1):
            train_idx.extend(segments[s])

        # Validation includes segment k+1
        val_idx = list(segments[k + 1])

        # Preserve relative order from original observation_ids
        val_ids = tuple(observation_ids[i] for i in sorted(val_idx))
        train_ids = tuple(observation_ids[i] for i in sorted(train_idx))
        splits.append((train_ids, val_ids))

    return splits
