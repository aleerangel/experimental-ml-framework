"""Pure NumPy statistical association metrics with strict degeneracy handling.

Complies with EXP-02, EXP-03, EXP-04, EXP-05, RF2.1, ADR-005, CA-GER-03, and XCUT-02.
Zero runtime dependencies outside numpy.
"""

from __future__ import annotations

import math
from typing import Any, Tuple

import numpy as np

from experimental_ml.core.enums import MetricStatus


def _rank_data(a: np.ndarray) -> np.ndarray:
    """Compute average fractional ranks for 1D numeric array handling ties deterministically."""
    n = len(a)
    if n == 0:
        return np.empty(0, dtype=np.float64)

    order = np.argsort(a, kind="mergesort")
    inv = np.empty(n, dtype=np.int64)
    inv[order] = np.arange(n, dtype=np.int64)

    sorted_a = a[order]
    # Identify run boundaries where values change
    diffs = np.concatenate(([True], sorted_a[1:] != sorted_a[:-1]))
    idx = np.where(diffs)[0]
    counts = np.diff(np.append(idx, n))

    # Mean rank for tie run starting at idx with length count
    mean_ranks = idx + (counts + 1) / 2.0
    ranks_sorted = np.repeat(mean_ranks, counts)
    return ranks_sorted[inv]


def compute_pearson(x: np.ndarray, y: np.ndarray) -> tuple[float, MetricStatus]:
    """Compute Pearson linear correlation coefficient between two numeric vectors.

    Args:
        x: 1D numeric array.
        y: 1D numeric array.

    Returns:
        (correlation, MetricStatus.VALID) or (NaN, MetricStatus.UNDEFINED_NAN)
    """
    x_arr = np.asarray(x, dtype=np.float64).ravel()
    y_arr = np.asarray(y, dtype=np.float64).ravel()

    if len(x_arr) != len(y_arr) or len(x_arr) < 2:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    # Filter out NaNs pairwise
    valid_mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
    if np.count_nonzero(valid_mask) < 2:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    x_clean = x_arr[valid_mask]
    y_clean = y_arr[valid_mask]

    x_mean = np.mean(x_clean)
    y_mean = np.mean(y_clean)

    x_c = x_clean - x_mean
    y_c = y_clean - y_mean

    ss_xx = float(np.sum(x_c * x_c))
    ss_yy = float(np.sum(y_c * y_c))

    # Strict check for zero variance or non-finite sums
    if ss_xx <= 1e-15 or ss_yy <= 1e-15 or not math.isfinite(ss_xx) or not math.isfinite(ss_yy):
        return float("nan"), MetricStatus.UNDEFINED_NAN

    cov_xy = float(np.sum(x_c * y_c))
    r = cov_xy / math.sqrt(ss_xx * ss_yy)

    # Defensively clamp numeric inaccuracies to [-1.0, 1.0]
    r_clamped = max(-1.0, min(1.0, r))
    return float(r_clamped), MetricStatus.VALID


def compute_spearman(x: np.ndarray, y: np.ndarray) -> tuple[float, MetricStatus]:
    """Compute Spearman rank correlation using average fractional ranks for ties.

    Args:
        x: 1D numeric array.
        y: 1D numeric array.

    Returns:
        (rho, MetricStatus.VALID) or (NaN, MetricStatus.UNDEFINED_NAN)
    """
    x_arr = np.asarray(x, dtype=np.float64).ravel()
    y_arr = np.asarray(y, dtype=np.float64).ravel()

    if len(x_arr) != len(y_arr) or len(x_arr) < 2:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    valid_mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
    if np.count_nonzero(valid_mask) < 2:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    x_clean = x_arr[valid_mask]
    y_clean = y_arr[valid_mask]

    # Convert to fractional ranks
    rx = _rank_data(x_clean)
    ry = _rank_data(y_clean)

    return compute_pearson(rx, ry)


def compute_correlation_ratio(
    categories: np.ndarray, continuous: np.ndarray
) -> tuple[float, MetricStatus]:
    """Compute Correlation Ratio (eta) between a categorical and a continuous variable.

    eta = sqrt(SS_between / SS_total) in [0.0, 1.0].

    Args:
        categories: 1D array of categorical labels (strings, integers, or objects).
        continuous: 1D numeric array.

    Returns:
        (eta, MetricStatus.VALID) or (NaN, MetricStatus.UNDEFINED_NAN)
    """
    cat_arr = np.asarray(categories).ravel()
    cont_arr = np.asarray(continuous, dtype=np.float64).ravel()

    if len(cat_arr) != len(cont_arr) or len(cont_arr) < 2:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    valid_mask = ~np.isnan(cont_arr)
    if np.count_nonzero(valid_mask) < 2:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    cat_clean = cat_arr[valid_mask]
    cont_clean = cont_arr[valid_mask]

    grand_mean = np.mean(cont_clean)
    ss_total = float(np.sum((cont_clean - grand_mean) ** 2))

    # If continuous variable has zero variance, eta is undefined
    if ss_total <= 1e-15 or not math.isfinite(ss_total):
        return float("nan"), MetricStatus.UNDEFINED_NAN

    unique_cats = np.unique(cat_clean)
    if len(unique_cats) < 2:
        # Only 1 category present: between-group variation is degenerate
        return float("nan"), MetricStatus.UNDEFINED_NAN

    ss_between = 0.0
    for cat in unique_cats:
        group_mask = (cat_clean == cat)
        group_size = np.count_nonzero(group_mask)
        if group_size > 0:
            group_mean = float(np.mean(cont_clean[group_mask]))
            ss_between += group_size * ((group_mean - grand_mean) ** 2)

    ratio = ss_between / ss_total
    ratio_clamped = max(0.0, min(1.0, ratio))
    eta = math.sqrt(ratio_clamped)
    return float(eta), MetricStatus.VALID


def compute_cramers_v(cat_x: np.ndarray, cat_y: np.ndarray) -> tuple[float, MetricStatus]:
    """Compute Cramér's V association statistic from a 2D contingency table.

    V = sqrt(chi2 / (N * min(R - 1, C - 1))) in [0.0, 1.0].

    Args:
        cat_x: 1D categorical array.
        cat_y: 1D categorical array.

    Returns:
        (V, MetricStatus.VALID) or (NaN, MetricStatus.UNDEFINED_NAN)
    """
    x_arr = np.asarray(cat_x).ravel()
    y_arr = np.asarray(cat_y).ravel()

    if len(x_arr) != len(y_arr) or len(x_arr) < 2:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    unique_x, inv_x = np.unique(x_arr, return_inverse=True)
    unique_y, inv_y = np.unique(y_arr, return_inverse=True)

    r = len(unique_x)
    c = len(unique_y)

    min_dim = min(r - 1, c - 1)
    if min_dim < 1:
        # Need at least 2 categories in both variables
        return float("nan"), MetricStatus.UNDEFINED_NAN

    n = len(x_arr)
    # Build 2D contingency table
    contingency = np.zeros((r, c), dtype=np.float64)
    np.add.at(contingency, (inv_x, inv_y), 1.0)

    # Marginal sums
    row_sums = contingency.sum(axis=1, keepdims=True)
    col_sums = contingency.sum(axis=0, keepdims=True)

    expected = (row_sums @ col_sums) / float(n)

    # Chi-square calculation where expected > 0
    valid_expected = expected > 1e-15
    if not np.any(valid_expected):
        return float("nan"), MetricStatus.UNDEFINED_NAN

    diff = contingency - expected
    chi2 = float(np.sum((diff[valid_expected] ** 2) / expected[valid_expected]))

    v_squared = chi2 / (n * min_dim)
    v_clamped = max(0.0, min(1.0, v_squared))
    v = math.sqrt(v_clamped)
    return float(v), MetricStatus.VALID


__all__ = [
    "compute_pearson",
    "compute_spearman",
    "compute_correlation_ratio",
    "compute_cramers_v",
]
