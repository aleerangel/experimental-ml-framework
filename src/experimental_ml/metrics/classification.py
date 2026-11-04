"""Vectorized classification metrics for experimental_ml.metrics."""

from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np

from experimental_ml.core.enums import AggregationScope, MetricDirection, MetricStatus
from experimental_ml.core.findings import ConfigurationError, DataIntegrityError, make_warning
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue


def validate_discrete_arrays(
    y_true: Any,
    y_pred: Any,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Convert and strictly validate discrete target and prediction arrays.

    Args:
        y_true: Array-like ground truth class labels.
        y_pred: Array-like predicted class labels.

    Returns:
        Tuple of (y_true_arr, y_pred_arr, n_samples).

    Raises:
        DataIntegrityError: If arrays are empty, length mismatched, contain non-finites (NaN/Inf),
                            or have incompatible shapes.
    """
    try:
        yt_arr = np.asarray(y_true)
        yp_arr = np.asarray(y_pred)
    except (ValueError, TypeError) as exc:
        raise DataIntegrityError(f"Could not convert inputs to arrays: {exc}") from exc

    # Squeeze (n, 1) column vectors to 1D
    if yt_arr.ndim == 2 and yt_arr.shape[1] == 1:
        yt_arr = yt_arr.squeeze(axis=1)
    if yp_arr.ndim == 2 and yp_arr.shape[1] == 1:
        yp_arr = yp_arr.squeeze(axis=1)

    if yt_arr.ndim != 1:
        raise DataIntegrityError(f"y_true must be a 1D sequence or (n, 1) column vector, got shape {yt_arr.shape}")
    if yp_arr.ndim != 1:
        raise DataIntegrityError(f"y_pred must be a 1D sequence or (n, 1) column vector, got shape {yp_arr.shape}")

    n = len(yt_arr)
    if n == 0:
        raise DataIntegrityError("Target array y_true cannot be empty (n_samples must be >= 1)")

    if len(yp_arr) != n:
        raise DataIntegrityError(
            f"Sample length mismatch: y_true has {n} samples, but y_pred has {len(yp_arr)} samples"
        )

    # Check finitude for numeric arrays
    if np.issubdtype(yt_arr.dtype, np.number) and not np.all(np.isfinite(yt_arr)):
        raise DataIntegrityError("y_true contains non-finite values (NaN, +Inf, or -Inf)")
    if np.issubdtype(yp_arr.dtype, np.number) and not np.all(np.isfinite(yp_arr)):
        raise DataIntegrityError("y_pred contains non-finite values (NaN, +Inf, or -Inf)")

    return yt_arr, yp_arr, n


def _extract_classes(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: Sequence[Any] | None = None,
) -> list[Any]:
    """Extract ordered unique classes from labels or inputs."""
    if labels is not None:
        # Preserve user labels order while ensuring uniqueness
        seen = set()
        classes = []
        for lbl in labels:
            if lbl not in seen:
                seen.add(lbl)
                classes.append(lbl)
        return classes

    # Union of unique classes present in y_true and y_pred
    unique_yt = np.unique(y_true)
    unique_yp = np.unique(y_pred)
    combined = np.unique(np.concatenate([unique_yt, unique_yp]))
    return list(combined)


def accuracy(
    y_true: Any,
    y_pred: Any,
    *,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Classification Accuracy in float64.

    Accuracy = (1 / n) * sum(I(y_true_i == y_pred_i)).
    """
    yt, yp, n = validate_discrete_arrays(y_true, y_pred)
    val = float(np.mean(yt == yp))

    return MetricValue(
        metric_id="accuracy",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def balanced_accuracy(
    y_true: Any,
    y_pred: Any,
    *,
    labels: Sequence[Any] | None = None,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Balanced Accuracy in float64.

    Balanced Accuracy = (1 / |C|) * sum_{c in C} Recall_c.
    Returns UNDEFINED_NAN if |C| < 2 or any class in C has zero positive support in y_true.
    """
    yt, yp, n = validate_discrete_arrays(y_true, y_pred)
    classes = _extract_classes(yt, yp, labels=labels)

    if len(classes) < 2:
        return MetricValue(
            metric_id="balanced_accuracy",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_INSUFFICIENT_CLASSES",
                    f"Balanced accuracy requires at least 2 distinct classes, got {len(classes)}",
                    {"n_classes": len(classes)},
                ),
            ),
        )

    recalls: list[float] = []
    for c in classes:
        support_c = int(np.sum(yt == c))
        if support_c == 0:
            return MetricValue(
                metric_id="balanced_accuracy",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_ABSENT_CLASS",
                        f"Balanced accuracy is undefined because class {c} has zero support in y_true",
                        {"class": str(c)},
                    ),
                ),
            )
        tp_c = int(np.sum((yt == c) & (yp == c)))
        recalls.append(tp_c / support_c)

    val = float(np.mean(recalls))
    return MetricValue(
        metric_id="balanced_accuracy",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def precision(
    y_true: Any,
    y_pred: Any,
    *,
    average: str = "binary",
    pos_label: Any = 1,
    labels: Sequence[Any] | None = None,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Precision in float64.

    Precision = TP / (TP + FP).
    Returns UNDEFINED_NAN if TP + FP == 0 (no positive predictions made).
    Returns valid 0.0 when TP == 0 with FP > 0.
    """
    yt, yp, n = validate_discrete_arrays(y_true, y_pred)

    if average not in ("binary", "macro", "weighted"):
        raise ConfigurationError(
            f"Invalid average '{average}'. Must be one of: 'binary', 'macro', 'weighted'"
        )

    if average == "binary":
        tp = int(np.sum((yt == pos_label) & (yp == pos_label)))
        fp = int(np.sum((yt != pos_label) & (yp == pos_label)))

        if tp + fp == 0:
            return MetricValue(
                metric_id="precision",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_ZERO_PREDICTIONS",
                        f"Precision is undefined because no positive predictions were made for pos_label={pos_label}",
                        {"pos_label": str(pos_label)},
                    ),
                ),
            )

        val = float(tp / (tp + fp))
        return MetricValue(
            metric_id="precision",
            value=val,
            status=MetricStatus.VALID,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(),
        )

    # Multiclass average: macro or weighted
    classes = _extract_classes(yt, yp, labels=labels)
    class_precisions: list[float] = []
    class_supports: list[int] = []

    for c in classes:
        tp_c = int(np.sum((yt == c) & (yp == c)))
        fp_c = int(np.sum((yt != c) & (yp == c)))
        fn_c = int(np.sum((yt == c) & (yp != c)))
        support_c = tp_c + fn_c

        if tp_c + fp_c == 0:
            return MetricValue(
                metric_id="precision",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_ZERO_PREDICTIONS",
                        f"Precision is undefined because no positive predictions were made for class {c}",
                        {"class": str(c)},
                    ),
                ),
            )

        class_precisions.append(tp_c / (tp_c + fp_c))
        class_supports.append(support_c)

    if average == "macro":
        val = float(np.mean(class_precisions))
    else:  # weighted
        total_support = sum(class_supports)
        if total_support == 0:
            return MetricValue(
                metric_id="precision",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_ZERO_TOTAL_SUPPORT",
                        "Weighted precision is undefined because total class support is zero",
                    ),
                ),
            )
        val = float(sum(p * s for p, s in zip(class_precisions, class_supports)) / total_support)

    return MetricValue(
        metric_id="precision",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def recall(
    y_true: Any,
    y_pred: Any,
    *,
    average: str = "binary",
    pos_label: Any = 1,
    labels: Sequence[Any] | None = None,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Recall (Sensitivity / True Positive Rate) in float64.

    Recall = TP / (TP + FN).
    Returns UNDEFINED_NAN if TP + FN == 0 (class absent in ground truth y_true).
    Returns valid 0.0 when TP == 0 with FN > 0.
    """
    yt, yp, n = validate_discrete_arrays(y_true, y_pred)

    if average not in ("binary", "macro", "weighted"):
        raise ConfigurationError(
            f"Invalid average '{average}'. Must be one of: 'binary', 'macro', 'weighted'"
        )

    if average == "binary":
        tp = int(np.sum((yt == pos_label) & (yp == pos_label)))
        fn = int(np.sum((yt == pos_label) & (yp != pos_label)))

        if tp + fn == 0:
            return MetricValue(
                metric_id="recall",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_ABSENT_CLASS",
                        f"Recall is undefined because pos_label={pos_label} has zero support in y_true",
                        {"pos_label": str(pos_label)},
                    ),
                ),
            )

        val = float(tp / (tp + fn))
        return MetricValue(
            metric_id="recall",
            value=val,
            status=MetricStatus.VALID,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(),
        )

    # Multiclass average: macro or weighted
    classes = _extract_classes(yt, yp, labels=labels)
    class_recalls: list[float] = []
    class_supports: list[int] = []

    for c in classes:
        tp_c = int(np.sum((yt == c) & (yp == c)))
        fn_c = int(np.sum((yt == c) & (yp != c)))
        support_c = tp_c + fn_c

        if support_c == 0:
            return MetricValue(
                metric_id="recall",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_ABSENT_CLASS",
                        f"Recall is undefined because class {c} has zero support in y_true",
                        {"class": str(c)},
                    ),
                ),
            )

        class_recalls.append(tp_c / support_c)
        class_supports.append(support_c)

    if average == "macro":
        val = float(np.mean(class_recalls))
    else:  # weighted
        total_support = sum(class_supports)
        if total_support == 0:
            return MetricValue(
                metric_id="recall",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_ZERO_TOTAL_SUPPORT",
                        "Weighted recall is undefined because total class support is zero",
                    ),
                ),
            )
        val = float(sum(r * s for r, s in zip(class_recalls, class_supports)) / total_support)

    return MetricValue(
        metric_id="recall",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def f1(
    y_true: Any,
    y_pred: Any,
    *,
    average: str = "binary",
    pos_label: Any = 1,
    labels: Sequence[Any] | None = None,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate F1 Score evaluated directly by its own denominator in float64.

    F1 = 2 * TP / (2 * TP + FP + FN).
    Returns UNDEFINED_NAN if and only if (2 * TP + FP + FN) == 0 (zero support in both target and prediction).
    Returns valid 0.0 when denominator > 0 and TP == 0.
    """
    yt, yp, n = validate_discrete_arrays(y_true, y_pred)

    if average not in ("binary", "macro", "weighted"):
        raise ConfigurationError(
            f"Invalid average '{average}'. Must be one of: 'binary', 'macro', 'weighted'"
        )

    if average == "binary":
        tp = int(np.sum((yt == pos_label) & (yp == pos_label)))
        fp = int(np.sum((yt != pos_label) & (yp == pos_label)))
        fn = int(np.sum((yt == pos_label) & (yp != pos_label)))
        denom = 2 * tp + fp + fn

        if denom == 0:
            return MetricValue(
                metric_id="f1",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_F1_ZERO_SUPPORT",
                        f"F1 is undefined because denominator (2*TP + FP + FN) is zero for pos_label={pos_label}",
                        {"pos_label": str(pos_label)},
                    ),
                ),
            )

        val = float(2 * tp / denom)
        return MetricValue(
            metric_id="f1",
            value=val,
            status=MetricStatus.VALID,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(),
        )

    # Multiclass average: macro or weighted
    classes = _extract_classes(yt, yp, labels=labels)
    class_f1s: list[float] = []
    class_supports: list[int] = []

    for c in classes:
        tp_c = int(np.sum((yt == c) & (yp == c)))
        fp_c = int(np.sum((yt != c) & (yp == c)))
        fn_c = int(np.sum((yt == c) & (yp != c)))
        support_c = tp_c + fn_c
        denom_c = 2 * tp_c + fp_c + fn_c

        if denom_c == 0:
            return MetricValue(
                metric_id="f1",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_F1_ZERO_SUPPORT",
                        f"F1 is undefined because denominator (2*TP + FP + FN) is zero for class {c}",
                        {"class": str(c)},
                    ),
                ),
            )

        class_f1s.append(2 * tp_c / denom_c)
        class_supports.append(support_c)

    if average == "macro":
        val = float(np.mean(class_f1s))
    else:  # weighted
        total_support = sum(class_supports)
        if total_support == 0:
            return MetricValue(
                metric_id="f1",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_ZERO_TOTAL_SUPPORT",
                        "Weighted F1 is undefined because total class support is zero",
                    ),
                ),
            )
        val = float(sum(f * s for f, s in zip(class_f1s, class_supports)) / total_support)

    return MetricValue(
        metric_id="f1",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


__all__ = [
    "validate_discrete_arrays",
    "accuracy",
    "balanced_accuracy",
    "precision",
    "recall",
    "f1",
]
