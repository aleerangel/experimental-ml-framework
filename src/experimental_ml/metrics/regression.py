"""Vectorized regression and kernel alignment metrics for experimental_ml.metrics."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from experimental_ml.core.enums import AggregationScope, MetricDirection, MetricStatus
from experimental_ml.core.findings import Finding, make_warning
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


__all__ = [
    "mae",
    "rmse",
    "mbe",
]
