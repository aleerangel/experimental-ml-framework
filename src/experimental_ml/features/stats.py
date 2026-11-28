"""Pure NumPy statistical association metrics with strict degeneracy handling.

Complies with EXP-02, EXP-03, EXP-04, EXP-05, RF2.1, ADR-005, CA-GER-03, and XCUT-02.
Zero runtime dependencies outside numpy.
"""

from __future__ import annotations

import math
from typing import Any, Tuple

import numpy as np

from experimental_ml.core.enums import MetricStatus, TaskType


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


def _is_missing_categorical(val: Any) -> bool:
    """Return True when a categorical element represents a missing value (None or NaN)."""
    if val is None:
        return True
    if isinstance(val, (float, np.floating)):
        return bool(math.isnan(float(val)))
    return False


def _valid_categorical_mask(arr: np.ndarray) -> np.ndarray:
    """Boolean mask identifying non-missing elements in a 1D categorical array."""
    if arr.dtype.kind in ("U", "S", "i", "u", "b"):
        return np.ones(len(arr), dtype=bool)
    if arr.dtype.kind == "f":
        return ~np.isnan(arr)
    return np.fromiter((not _is_missing_categorical(v) for v in arr), dtype=bool, count=len(arr))


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

    valid_mask = (~np.isnan(cont_arr)) & _valid_categorical_mask(cat_arr)
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

    valid_mask = _valid_categorical_mask(x_arr) & _valid_categorical_mask(y_arr)
    if np.count_nonzero(valid_mask) < 2:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    x_clean = x_arr[valid_mask]
    y_clean = y_arr[valid_mask]

    unique_x, inv_x = np.unique(x_clean, return_inverse=True)
    unique_y, inv_y = np.unique(y_clean, return_inverse=True)

    r = len(unique_x)
    c = len(unique_y)

    min_dim = min(r - 1, c - 1)
    if min_dim < 1:
        # Need at least 2 categories in both variables
        return float("nan"), MetricStatus.UNDEFINED_NAN

    n = len(x_clean)
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


def compute_vif(X: np.ndarray) -> tuple[np.ndarray, MetricStatus]:
    """Compute Variance Inflation Factor (VIF) per numeric column using np.linalg.pinv."""
    x_arr = np.asarray(X, dtype=np.float64)
    if x_arr.ndim != 2 or x_arr.shape[0] < 3 or x_arr.shape[1] < 1:
        return np.empty(0, dtype=np.float64), MetricStatus.UNDEFINED_NAN

    valid_rows = np.all(np.isfinite(x_arr), axis=1)
    x_clean = x_arr[valid_rows]
    if x_clean.shape[0] < 3:
        return np.full(x_arr.shape[1], float("nan"), dtype=np.float64), MetricStatus.UNDEFINED_NAN

    p = x_clean.shape[1]
    if p == 1:
        return np.ones(1, dtype=np.float64), MetricStatus.VALID

    means = np.mean(x_clean, axis=0)
    stds = np.std(x_clean, axis=0, ddof=0)
    non_const = stds > 1e-12
    vifs = np.full(p, float("nan"), dtype=np.float64)
    if np.count_nonzero(non_const) < 2:
        if np.count_nonzero(non_const) == 1:
            vifs[non_const] = 1.0
            return vifs, MetricStatus.VALID
        return vifs, MetricStatus.UNDEFINED_NAN

    z = (x_clean[:, non_const] - means[non_const]) / stds[non_const]
    corr = (z.T @ z) / float(z.shape[0])
    inv_corr = np.linalg.pinv(corr, rcond=1e-12)
    diag = np.maximum(1.0, np.diag(inv_corr))
    vifs[non_const] = diag
    return vifs, MetricStatus.VALID


def compute_distance_correlation(
    x: np.ndarray,
    y: np.ndarray,
    *,
    max_samples: int = 2000,
) -> tuple[float, MetricStatus]:
    """Compute Distance Correlation (Szekely et al., 2007) in pure NumPy."""
    x_arr = np.asarray(x, dtype=np.float64).ravel()
    y_arr = np.asarray(y, dtype=np.float64).ravel()
    if len(x_arr) != len(y_arr) or len(x_arr) < 3:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    valid = np.isfinite(x_arr) & np.isfinite(y_arr)
    if np.count_nonzero(valid) < 3:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    xc = x_arr[valid]
    yc = y_arr[valid]
    if len(xc) > max_samples:
        idx = np.linspace(0, len(xc) - 1, max_samples, dtype=int)
        xc = xc[idx]
        yc = yc[idx]

    a = np.abs(xc[:, None] - xc[None, :])
    b = np.abs(yc[:, None] - yc[None, :])
    a_c = a - a.mean(axis=0, keepdims=True) - a.mean(axis=1, keepdims=True) + a.mean()
    b_c = b - b.mean(axis=0, keepdims=True) - b.mean(axis=1, keepdims=True) + b.mean()

    dcov2_xx = float(np.mean(a_c * a_c))
    dcov2_yy = float(np.mean(b_c * b_c))
    if dcov2_xx <= 1e-15 or dcov2_yy <= 1e-15:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    dcov2_xy = float(np.mean(a_c * b_c))
    dcor = math.sqrt(max(0.0, dcov2_xy) / math.sqrt(dcov2_xx * dcov2_yy))
    return float(max(0.0, min(1.0, dcor))), MetricStatus.VALID


def compute_linearity_score(
    X: np.ndarray,
    y: np.ndarray,
    task_type: TaskType,
) -> tuple[float, MetricStatus]:
    """Compute exploratory linearity score: OLS R^2 for regression, Ridge/LDA balanced accuracy for classification."""
    x_arr = np.asarray(X, dtype=np.float64)
    y_arr = np.asarray(y).ravel()
    if x_arr.ndim != 2 or x_arr.shape[0] != len(y_arr) or x_arr.shape[0] < 4 or x_arr.shape[1] < 1:
        return float("nan"), MetricStatus.UNDEFINED_NAN

    valid_x = np.all(np.isfinite(x_arr), axis=1)
    if task_type == TaskType.REGRESSION:
        y_float = np.asarray(y_arr, dtype=np.float64)
        valid = valid_x & np.isfinite(y_float)
        if np.count_nonzero(valid) < 4:
            return float("nan"), MetricStatus.UNDEFINED_NAN
        xc = x_arr[valid]
        yc = y_float[valid]
        stds = np.std(xc, axis=0, ddof=0)
        keep = stds > 1e-12
        if not np.any(keep):
            return float("nan"), MetricStatus.UNDEFINED_NAN
        z = (xc[:, keep] - np.mean(xc[:, keep], axis=0)) / stds[keep]
        x_aug = np.column_stack([np.ones(z.shape[0], dtype=np.float64), z])
        coef, *_ = np.linalg.lstsq(x_aug, yc, rcond=None)
        preds = x_aug @ coef
        ss_res = float(np.sum((yc - preds) ** 2))
        ss_tot = float(np.sum((yc - np.mean(yc)) ** 2))
        if ss_tot <= 1e-15:
            return float("nan"), MetricStatus.UNDEFINED_NAN
        r2 = max(0.0, min(1.0, 1.0 - ss_res / ss_tot))
        return float(r2), MetricStatus.VALID

    valid_y = np.array([not _is_missing_categorical(v) for v in y_arr], dtype=bool)
    valid = valid_x & valid_y
    if np.count_nonzero(valid) < 4:
        return float("nan"), MetricStatus.UNDEFINED_NAN
    xc = x_arr[valid]
    yc = y_arr[valid]
    classes, y_idx = np.unique(yc, return_inverse=True)
    if len(classes) < 2:
        return float("nan"), MetricStatus.UNDEFINED_NAN
    stds = np.std(xc, axis=0, ddof=0)
    keep = stds > 1e-12
    if not np.any(keep):
        return float("nan"), MetricStatus.UNDEFINED_NAN
    z = (xc[:, keep] - np.mean(xc[:, keep], axis=0)) / stds[keep]
    x_aug = np.column_stack([np.ones(z.shape[0], dtype=np.float64), z])
    y_oh = np.eye(len(classes), dtype=np.float64)[y_idx]
    reg = 1e-4 * np.eye(x_aug.shape[1], dtype=np.float64)
    reg[0, 0] = 0.0
    w = np.linalg.pinv(x_aug.T @ x_aug + reg) @ (x_aug.T @ y_oh)
    pred_idx = np.argmax(x_aug @ w, axis=1)
    recalls = [
        float(np.mean(pred_idx[y_idx == c] == c))
        for c in range(len(classes))
        if np.any(y_idx == c)
    ]
    return float(np.mean(recalls)), MetricStatus.VALID


__all__ = [
    "compute_pearson",
    "compute_spearman",
    "compute_correlation_ratio",
    "compute_cramers_v",
    "compute_vif",
    "compute_distance_correlation",
    "compute_linearity_score",
]
