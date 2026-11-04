"""Vectorized regression and kernel alignment metrics for experimental_ml.metrics."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from experimental_ml.core.enums import AggregationScope, MetricDirection, MetricStatus
from experimental_ml.core.findings import DataIntegrityError, Finding, make_warning
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue
from experimental_ml.metrics.validation import scaled_quadratic_sum, validate_numeric_arrays


def mae(
    y_true: Any,
    y_pred: Any,
    *,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Mean Absolute Error (MAE) in double precision (float64).

    MAE = (1 / n) * sum(|y_true_i - y_pred_i|)
    """
    yt, yp, n = validate_numeric_arrays(y_true, y_pred)
    diff = np.abs(yp - yt)
    val = float(np.mean(diff))

    if not math.isfinite(val):
        return MetricValue(
            metric_id="mae",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MINIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(make_warning("W_METRIC_NUMERICAL_OVERFLOW", "Numerical overflow in MAE computation"),),
        )

    return MetricValue(
        metric_id="mae",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def rmse(
    y_true: Any,
    y_pred: Any,
    *,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Root Mean Squared Error (RMSE) in double precision (float64).

    RMSE = sqrt((1 / n) * sum((y_pred_i - y_true_i)**2))
    Applies scaled_quadratic_sum to mitigate intermediate quadratic overflow.
    """
    yt, yp, n = validate_numeric_arrays(y_true, y_pred)
    diff = yp - yt
    m, s = scaled_quadratic_sum(diff)

    if m == 0.0:
        val = 0.0
    else:
        val = m * math.sqrt(s / n)

    if not math.isfinite(val):
        return MetricValue(
            metric_id="rmse",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MINIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(make_warning("W_METRIC_NUMERICAL_OVERFLOW", "Numerical overflow in RMSE computation"),),
        )

    return MetricValue(
        metric_id="rmse",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def mbe(
    y_true: Any,
    y_pred: Any,
    *,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Mean Bias Error (MBE) preserving signed direction in float64.

    MBE = (1 / n) * sum(y_pred_i - y_true_i)
    Positive indicates overestimation (y_pred > y_true on average).
    Negative indicates underestimation (y_pred < y_true on average).
    """
    yt, yp, n = validate_numeric_arrays(y_true, y_pred)
    val = float(np.mean(yp - yt))

    if not math.isfinite(val):
        return MetricValue(
            metric_id="mbe",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MINIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(make_warning("W_METRIC_NUMERICAL_OVERFLOW", "Numerical overflow in MBE computation"),),
        )

    return MetricValue(
        metric_id="mbe",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def r2(
    y_true: Any,
    y_pred: Any,
    *,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Coefficient of Determination (R2) in float64.

    R2 = 1 - (SS_res / SS_tot).
    Returns UNDEFINED_NAN if n < 2 or SS_tot == 0.
    """
    yt, yp, n = validate_numeric_arrays(y_true, y_pred)

    if n < 2:
        return MetricValue(
            metric_id="r2",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_INSUFFICIENT_SAMPLES",
                    f"R2 requires at least 2 samples, got n={n}",
                    {"n_samples": n},
                ),
            ),
        )

    # Compute SS_tot with scaling
    y_mean = float(np.mean(yt))
    dev_tot = yt - y_mean
    m_tot, s_tot = scaled_quadratic_sum(dev_tot)

    if m_tot == 0.0 or s_tot == 0.0:
        return MetricValue(
            metric_id="r2",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_ZERO_VARIANCE",
                    "R2 is undefined when target variable y_true has zero variance",
                    {"n_samples": n},
                ),
            ),
        )

    dev_res = yt - yp
    m_res, s_res = scaled_quadratic_sum(dev_res)

    if m_res == 0.0:
        val = 1.0
    else:
        # SS_res / SS_tot = (m_res / m_tot)**2 * (s_res / s_tot)
        ratio = (m_res / m_tot) ** 2 * (s_res / s_tot)
        val = float(1.0 - ratio)

    if not math.isfinite(val):
        return MetricValue(
            metric_id="r2",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(make_warning("W_METRIC_NUMERICAL_OVERFLOW", "Numerical overflow in R2 computation"),),
        )

    return MetricValue(
        metric_id="r2",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def rmse_rel_pct(
    y_true: Any,
    y_pred: Any,
    *,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Relative Root Mean Squared Error (RMSE %) in float64.

    RMSE_rel_pct = 100.0 * (RMSE / |mean(y_true)|).
    Returns UNDEFINED_NAN if mean(y_true) == 0.
    """
    yt, yp, n = validate_numeric_arrays(y_true, y_pred)
    mean_y = float(np.mean(yt))
    abs_mean = abs(mean_y)

    if abs_mean == 0.0:
        return MetricValue(
            metric_id="rmse_rel_pct",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MINIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_ZERO_MEAN",
                    "RMSE relative % is undefined when mean(y_true) is zero",
                    {"mean_y_true": mean_y},
                ),
            ),
        )

    res_rmse = rmse(yt, yp, scope=scope)
    if res_rmse.status != MetricStatus.VALID or not math.isfinite(res_rmse.value):
        return MetricValue(
            metric_id="rmse_rel_pct",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MINIMIZE,
            scope=scope,
            n_samples=n,
            warnings=res_rmse.warnings,
        )

    val = float(100.0 * (res_rmse.value / abs_mean))

    if not math.isfinite(val):
        return MetricValue(
            metric_id="rmse_rel_pct",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MINIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(make_warning("W_METRIC_NUMERICAL_OVERFLOW", "Numerical overflow in RMSE_rel_pct computation"),),
        )

    return MetricValue(
        metric_id="rmse_rel_pct",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def mape(
    y_true: Any,
    y_pred: Any,
    *,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Mean Absolute Percentage Error (MAPE %) in float64.

    MAPE = (100.0 / n) * sum(|(y_true_i - y_pred_i) / y_true_i|).
    Returns UNDEFINED_NAN if any y_true_i == 0.
    """
    yt, yp, n = validate_numeric_arrays(y_true, y_pred)
    zero_mask = yt == 0.0

    if np.any(zero_mask):
        n_zeros = int(np.sum(zero_mask))
        return MetricValue(
            metric_id="mape",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MINIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_ZERO_TARGET",
                    f"MAPE is undefined when target variable contains zero observations ({n_zeros} zero targets found)",
                    {"n_zero_targets": n_zeros},
                ),
            ),
        )

    pct_diff = np.abs((yt - yp) / yt)
    val = float(100.0 * np.mean(pct_diff))

    if not math.isfinite(val):
        return MetricValue(
            metric_id="mape",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MINIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(make_warning("W_METRIC_NUMERICAL_OVERFLOW", "Numerical overflow in MAPE computation"),),
        )

    return MetricValue(
        metric_id="mape",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def pearson(
    y_true: Any,
    y_pred: Any,
    *,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Pearson Correlation Coefficient in float64.

    Returns UNDEFINED_NAN if n < 2, Var(y_true) == 0, or Var(y_pred) == 0.
    """
    yt, yp, n = validate_numeric_arrays(y_true, y_pred)

    if n < 2:
        return MetricValue(
            metric_id="pearson",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_INSUFFICIENT_SAMPLES",
                    f"Pearson correlation requires at least 2 samples, got n={n}",
                    {"n_samples": n},
                ),
            ),
        )

    dev_t = yt - np.mean(yt)
    dev_p = yp - np.mean(yp)

    mt, st = scaled_quadratic_sum(dev_t)
    mp, sp = scaled_quadratic_sum(dev_p)

    if mt == 0.0 or st == 0.0 or mp == 0.0 or sp == 0.0:
        return MetricValue(
            metric_id="pearson",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_ZERO_VARIANCE",
                    "Pearson correlation is undefined when y_true or y_pred has zero variance",
                    {"var_y_true_zero": mt == 0.0, "var_y_pred_zero": mp == 0.0},
                ),
            ),
        )

    # Numerator with scaling: sum((dev_t / mt) * (dev_p / mp))
    cov_scaled = float(np.sum((dev_t / mt) * (dev_p / mp)))
    denom = math.sqrt(st * sp)

    if denom == 0.0:
        val = 0.0
    else:
        val = cov_scaled / denom

    # Clamp rounding noise to [-1.0, 1.0]
    val = max(-1.0, min(1.0, val))

    return MetricValue(
        metric_id="pearson",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def kta(
    k_true: Any,
    k_pred: Any,
    *,
    centered: bool = False,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Kernel Target Alignment (KTA) in float64.

    Accepts 2D square Gram matrices (n, n) or 1D vectors v (converted to v * v^T).
    If centered=True, applies double centering H * K * H with H = I - (1/n)*1*1^T.
    Returns UNDEFINED_NAN if Frobenius norm of either Gram matrix is zero.
    """
    try:
        k1 = np.asarray(k_true, dtype=np.float64)
        k2 = np.asarray(k_pred, dtype=np.float64)
    except (ValueError, TypeError) as exc:
        raise DataIntegrityError(f"Could not convert kernel inputs to float64: {exc}") from exc

    if not np.all(np.isfinite(k1)) or not np.all(np.isfinite(k2)):
        raise DataIntegrityError("Kernel matrices contain non-finite values (NaN, +Inf, -Inf)")

    # Squeeze (n, 1) column vectors to 1D
    if k1.ndim == 2 and k1.shape[1] == 1:
        k1 = k1.squeeze(axis=1)
    if k2.ndim == 2 and k2.shape[1] == 1:
        k2 = k2.squeeze(axis=1)

    # Convert 1D vectors to outer-product Gram matrices
    if k1.ndim == 1:
        k1 = np.outer(k1, k1)
    if k2.ndim == 1:
        k2 = np.outer(k2, k2)

    if k1.ndim != 2 or k1.shape[0] != k1.shape[1]:
        raise DataIntegrityError(f"k_true must be a square 2D matrix or 1D vector, got shape {k1.shape}")

    if k2.ndim != 2 or k2.shape[0] != k2.shape[1]:
        raise DataIntegrityError(f"k_pred must be a square 2D matrix or 1D vector, got shape {k2.shape}")

    if k1.shape != k2.shape:
        raise DataIntegrityError(f"Kernel matrix shape mismatch: k_true is {k1.shape}, k_pred is {k2.shape}")

    n = k1.shape[0]
    if n == 0:
        raise DataIntegrityError("Kernel matrix dimension cannot be zero")

    if centered:
        # Centering matrix H = I - (1/n) * J
        h = np.eye(n, dtype=np.float64) - (1.0 / n) * np.ones((n, n), dtype=np.float64)
        k1 = h @ k1 @ h
        k2 = h @ k2 @ h

    # Frobenius scaling
    m1 = float(np.max(np.abs(k1)))
    m2 = float(np.max(np.abs(k2)))

    if m1 == 0.0 or m2 == 0.0:
        return MetricValue(
            metric_id="kta",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_ZERO_GRAM_NORM",
                    "KTA is undefined when Frobenius norm of either Gram matrix is zero",
                    {"norm_k_true_zero": m1 == 0.0, "norm_k_pred_zero": m2 == 0.0},
                ),
            ),
        )

    k1_scaled = k1 / m1
    k2_scaled = k2 / m2

    norm1 = math.sqrt(float(np.sum(k1_scaled * k1_scaled)))
    norm2 = math.sqrt(float(np.sum(k2_scaled * k2_scaled)))

    if norm1 == 0.0 or norm2 == 0.0:
        return MetricValue(
            metric_id="kta",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_ZERO_GRAM_NORM",
                    "KTA is undefined when Frobenius norm of either Gram matrix is zero",
                ),
            ),
        )

    frob_inner = float(np.sum(k1_scaled * k2_scaled))
    val = frob_inner / (norm1 * norm2)
    val = max(-1.0, min(1.0, val))

    return MetricValue(
        metric_id="kta",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


__all__ = [
    "mae",
    "rmse",
    "mbe",
    "r2",
    "rmse_rel_pct",
    "mape",
    "pearson",
    "kta",
]
