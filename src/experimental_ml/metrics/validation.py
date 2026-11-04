"""Numerical validation and floating-point overflow mitigation for experimental_ml.metrics."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from experimental_ml.core.findings import ConfigurationError, DataIntegrityError
from experimental_ml.metrics.types import MetricEvaluationScope


def validate_numeric_arrays(
    y_true: Any,
    y_pred: Any,
    allow_2d_pred: bool = False,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Convert and strictly validate numeric target and prediction arrays in float64.

    Args:
        y_true: Array-like ground truth observations.
        y_pred: Array-like predicted values or scores.
        allow_2d_pred: Whether y_pred is allowed to be a 2D matrix (e.g. for multiclass probabilities).

    Returns:
        Tuple of (y_true_f64, y_pred_f64, n_samples).

    Raises:
        DataIntegrityError: If arrays are empty, length mismatched, contain non-finites (NaN/Inf),
                            or have incompatible shapes.
    """
    try:
        yt_arr = np.asarray(y_true, dtype=np.float64)
    except (ValueError, TypeError) as exc:
        raise DataIntegrityError(f"Could not convert y_true to float64 array: {exc}") from exc

    try:
        yp_arr = np.asarray(y_pred, dtype=np.float64)
    except (ValueError, TypeError) as exc:
        raise DataIntegrityError(f"Could not convert y_pred to float64 array: {exc}") from exc

    # Squeeze (n, 1) to (n,) for y_true
    if yt_arr.ndim == 2 and yt_arr.shape[1] == 1:
        yt_arr = yt_arr.squeeze(axis=1)

    if yt_arr.ndim != 1:
        raise DataIntegrityError(f"y_true must be a 1D sequence or (n, 1) column vector, got shape {yt_arr.shape}")

    n = len(yt_arr)
    if n == 0:
        raise DataIntegrityError("Target array y_true cannot be empty (n_samples must be >= 1)")

    # Squeeze (n, 1) to (n,) for y_pred if not allow_2d_pred
    if not allow_2d_pred:
        if yp_arr.ndim == 2 and yp_arr.shape[1] == 1:
            yp_arr = yp_arr.squeeze(axis=1)
        if yp_arr.ndim != 1:
            raise DataIntegrityError(f"y_pred must be a 1D sequence or (n, 1) column vector, got shape {yp_arr.shape}")
    else:
        if yp_arr.ndim not in (1, 2):
            raise DataIntegrityError(f"y_pred must be a 1D array or 2D matrix, got shape {yp_arr.shape}")

    if len(yp_arr) != n:
        raise DataIntegrityError(
            f"Sample length mismatch: y_true has {n} samples, but y_pred has {len(yp_arr)} samples"
        )

    # Check finitude (no NaN, +Inf, -Inf)
    if not np.all(np.isfinite(yt_arr)):
        raise DataIntegrityError("y_true contains non-finite values (NaN, +Inf, or -Inf)")

    if not np.all(np.isfinite(yp_arr)):
        raise DataIntegrityError("y_pred contains non-finite values (NaN, +Inf, or -Inf)")

    return yt_arr, yp_arr, n


def scaled_quadratic_sum(diff: np.ndarray) -> tuple[float, float]:
    """Calculate quadratic sum with scaling by maximum absolute value to mitigate intermediate overflow.

    Computes m = max(|diff|) and s = sum((diff / m)**2).
    The actual sum of squared differences is m**2 * s.
    For RMSE: m * sqrt(s / n).

    Args:
        diff: 1D or 2D numpy array of differences or deviations.

    Returns:
        Tuple of (m, s) where m is max absolute deviation and s is scaled squared sum.
    """
    if diff.size == 0:
        return 0.0, 0.0

    m = float(np.max(np.abs(diff)))
    if m == 0.0 or not math.isfinite(m):
        return m, 0.0

    scaled = diff / m
    s = float(np.sum(scaled * scaled))
    return m, s


__all__ = [
    "validate_numeric_arrays",
    "scaled_quadratic_sum",
]
