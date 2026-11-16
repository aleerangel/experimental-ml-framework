"""Multiple hypothesis testing correction procedures (STAT-08, CA-E5-02).

Implements pure-NumPy Holm-Bonferroni (FWER) and Benjamini-Hochberg (FDR)
p-value adjustments without SciPy (XCUT-02).
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from experimental_ml.core.findings import ContractViolationError


def _validate_pvalues(p_values: Sequence[float]) -> np.ndarray:
    """Validate that all p-values are finite numbers in [0.0, 1.0]."""
    arr = np.asarray(p_values, dtype=np.float64)
    if arr.ndim != 1:
        raise ContractViolationError("p_values must be a 1-dimensional sequence.")
    for val in arr:
        fval = float(val)
        if not math.isfinite(fval) or fval < 0.0 or fval > 1.0:
            raise ContractViolationError(
                f"All p-values must be finite and in [0.0, 1.0]; got {fval}."
            )
    return arr


def adjust_pvalues_holm(p_values: Sequence[float]) -> list[float]:
    """Apply Holm-Bonferroni step-down FWER adjustment preserving original order (STAT-08).

    Args:
        p_values: Sequence of raw p-values in [0.0, 1.0].

    Returns:
        List of adjusted p-values in [0.0, 1.0] matching input order.
    """
    arr = _validate_pvalues(p_values)
    m = int(arr.shape[0])
    if m == 0:
        return []
    if m == 1:
        return [float(arr[0])]

    order = np.argsort(arr, kind="mergesort")
    sorted_p = arr[order]

    adjusted_sorted = np.empty(m, dtype=np.float64)
    running_max = 0.0
    for i in range(m):
        raw_adj = float(sorted_p[i]) * (m - i)
        clamped = min(1.0, raw_adj)
        running_max = max(running_max, clamped)
        adjusted_sorted[i] = running_max

    result = np.empty(m, dtype=np.float64)
    result[order] = adjusted_sorted
    return [float(v) for v in result]


def adjust_pvalues_bh(p_values: Sequence[float]) -> list[float]:
    """Apply Benjamini-Hochberg step-up FDR adjustment preserving original order (STAT-08).

    Args:
        p_values: Sequence of raw p-values in [0.0, 1.0].

    Returns:
        List of adjusted p-values (q-values) in [0.0, 1.0] matching input order.
    """
    arr = _validate_pvalues(p_values)
    m = int(arr.shape[0])
    if m == 0:
        return []
    if m == 1:
        return [float(arr[0])]

    order = np.argsort(arr, kind="mergesort")
    sorted_p = arr[order]

    adjusted_sorted = np.empty(m, dtype=np.float64)
    running_min = 1.0
    for i in range(m - 1, -1, -1):
        rank_1based = i + 1
        raw_adj = float(sorted_p[i]) * (m / rank_1based)
        clamped = min(1.0, raw_adj)
        running_min = min(running_min, clamped)
        adjusted_sorted[i] = running_min

    result = np.empty(m, dtype=np.float64)
    result[order] = adjusted_sorted
    return [float(v) for v in result]
