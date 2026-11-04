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
        classes_present = set(yt).union(set(yp))
        if len(classes_present) > 2:
            raise DataIntegrityError(
                f"average='binary' requires at most 2 classes, got {len(classes_present)}: {classes_present}"
            )
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
        classes_present = set(yt).union(set(yp))
        if len(classes_present) > 2:
            raise DataIntegrityError(
                f"average='binary' requires at most 2 classes, got {len(classes_present)}: {classes_present}"
            )
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
        classes_present = set(yt).union(set(yp))
        if len(classes_present) > 2:
            raise DataIntegrityError(
                f"average='binary' requires at most 2 classes, got {len(classes_present)}: {classes_present}"
            )
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


def _compute_midranks(scores: np.ndarray) -> np.ndarray:
    """Compute 1-based mid-ranks for scores resolving ties by average rank."""
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=np.float64)
    sorted_scores = scores[order]
    n = len(scores)
    i = 0
    while i < n:
        j = i
        while j < n - 1 and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        midrank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = midrank
        i = j + 1
    return ranks


def _binary_roc_auc(y_true_bin: np.ndarray, scores: np.ndarray) -> float:
    """Compute binary ROC AUC via Mann-Whitney U with mid-ranks."""
    n_pos = int(np.sum(y_true_bin))
    n_neg = len(y_true_bin) - n_pos

    if n_pos == 0 or n_neg == 0:
        return float("nan")

    ranks = _compute_midranks(scores)
    sum_ranks_pos = float(np.sum(ranks[y_true_bin]))
    u_stat = sum_ranks_pos - (n_pos * (n_pos + 1)) / 2.0
    auc = u_stat / (n_pos * n_neg)
    return float(max(0.0, min(1.0, auc)))


def roc_auc(
    y_true: Any,
    y_score: Any,
    *,
    average: str = "macro",
    labels: Sequence[Any] | None = None,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Area Under the Receiver Operating Characteristic Curve (ROC AUC) in float64.

    Computes exact Mann-Whitney U statistic with mid-ranks for ties (0.5 for constant scores).
    Supports 1D or 2D binary scores and multiclass One-vs-Rest (OVR) with macro or weighted averaging.
    Returns UNDEFINED_NAN if y_true has < 2 unique classes or any class has zero positive/negative support.
    """
    if average not in ("macro", "weighted"):
        raise ConfigurationError(
            f"Invalid average '{average}'. Must be one of: 'macro', 'weighted'"
        )

    try:
        yt = np.asarray(y_true)
        ys = np.asarray(y_score, dtype=np.float64)
    except (ValueError, TypeError) as exc:
        raise DataIntegrityError(f"Could not convert inputs to arrays: {exc}") from exc

    if yt.ndim == 2 and yt.shape[1] == 1:
        yt = yt.squeeze(axis=1)

    if yt.ndim != 1:
        raise DataIntegrityError(f"y_true must be a 1D sequence or (n, 1) vector, got shape {yt.shape}")

    n = len(yt)
    if n == 0:
        raise DataIntegrityError("Target array y_true cannot be empty (n_samples must be >= 1)")

    if len(ys) != n:
        raise DataIntegrityError(
            f"Sample length mismatch: y_true has {n} samples, but y_score has {len(ys)} samples"
        )

    if not np.all(np.isfinite(ys)):
        raise DataIntegrityError("y_score contains non-finite values (NaN, +Inf, or -Inf)")

    if np.issubdtype(yt.dtype, np.number) and not np.all(np.isfinite(yt)):
        raise DataIntegrityError("y_true contains non-finite values (NaN, +Inf, or -Inf)")

    classes = _extract_classes(yt, np.array([]), labels=labels)
    unique_yt = np.unique(yt)

    if len(unique_yt) < 2:
        return MetricValue(
            metric_id="roc_auc",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_INSUFFICIENT_CLASSES",
                    f"ROC AUC requires at least 2 distinct classes in y_true, got {len(unique_yt)}",
                    {"n_classes": len(unique_yt)},
                ),
            ),
        )

    # Binary case
    if len(classes) == 2:
        c_pos = classes[1]
        y_bin = (yt == c_pos)

        # 1D or (n, 1) or (n, 2)
        if ys.ndim == 1:
            score_col = ys
        elif ys.ndim == 2:
            if ys.shape[1] == 1:
                score_col = ys.squeeze(axis=1)
            elif ys.shape[1] == 2:
                score_col = ys[:, 1]
            else:
                raise DataIntegrityError(
                    f"Binary ROC AUC expected y_score with 1 or 2 columns, got shape {ys.shape}"
                )
        else:
            raise DataIntegrityError(f"y_score has invalid ndim {ys.ndim}")

        val = _binary_roc_auc(y_bin, score_col)
        if math.isnan(val):
            return MetricValue(
                metric_id="roc_auc",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_ABSENT_CLASS",
                        f"Binary ROC AUC is undefined because class {c_pos} has zero positive or negative support",
                    ),
                ),
            )

        return MetricValue(
            metric_id="roc_auc",
            value=val,
            status=MetricStatus.VALID,
            direction=MetricDirection.MAXIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(),
        )

    # Multiclass OVR (K >= 3)
    k_classes = len(classes)
    if ys.ndim != 2 or ys.shape[1] != k_classes:
        raise DataIntegrityError(
            f"Multiclass OVR ROC AUC expected 2D y_score with shape ({n}, {k_classes}), got {ys.shape}"
        )

    aucs: list[float] = []
    supports: list[int] = []

    for k, c in enumerate(classes):
        y_bin = (yt == c)
        n_pos = int(np.sum(y_bin))
        n_neg = n - n_pos

        if n_pos == 0 or n_neg == 0:
            return MetricValue(
                metric_id="roc_auc",
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=MetricDirection.MAXIMIZE,
                scope=scope,
                n_samples=n,
                warnings=(
                    make_warning(
                        "W_METRIC_ABSENT_CLASS",
                        f"Multiclass OVR ROC AUC is undefined because class {c} has zero positive or negative support",
                        {"class": str(c), "n_pos": n_pos, "n_neg": n_neg},
                    ),
                ),
            )

        auc_k = _binary_roc_auc(y_bin, ys[:, k])
        aucs.append(auc_k)
        supports.append(n_pos)

    if average == "macro":
        val = float(np.mean(aucs))
    else:  # weighted
        total_pos = sum(supports)
        val = float(sum(a * s for a, s in zip(aucs, supports)) / total_pos)

    return MetricValue(
        metric_id="roc_auc",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=scope,
        n_samples=n,
        warnings=(),
    )


def log_loss(
    y_true: Any,
    y_prob: Any,
    *,
    eps: float = 1e-15,
    labels: Sequence[Any] | None = None,
    scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope.PER_FOLD,
) -> MetricValue:
    """Calculate Logarithmic Loss (Cross-Entropy) in float64.

    Validates probability distribution bounds in [-1e-12, 1 + 1e-12] and row sums within 1e-6 of 1.0.
    Applies numerical clipping to [eps, 1 - eps] with default eps=1e-15.
    Returns UNDEFINED_NAN if y_true has < 2 unique classes.
    """
    try:
        yt = np.asarray(y_true)
        yp = np.asarray(y_prob, dtype=np.float64)
    except (ValueError, TypeError) as exc:
        raise DataIntegrityError(f"Could not convert inputs to arrays: {exc}") from exc

    if yt.ndim == 2 and yt.shape[1] == 1:
        yt = yt.squeeze(axis=1)

    if yt.ndim != 1:
        raise DataIntegrityError(f"y_true must be a 1D sequence or (n, 1) vector, got shape {yt.shape}")

    n = len(yt)
    if n == 0:
        raise DataIntegrityError("Target array y_true cannot be empty (n_samples must be >= 1)")

    if len(yp) != n:
        raise DataIntegrityError(
            f"Sample length mismatch: y_true has {n} samples, but y_prob has {len(yp)} samples"
        )

    if not np.all(np.isfinite(yp)):
        raise DataIntegrityError("y_prob contains non-finite values (NaN, +Inf, or -Inf)")

    if np.issubdtype(yt.dtype, np.number) and not np.all(np.isfinite(yt)):
        raise DataIntegrityError("y_true contains non-finite values (NaN, +Inf, or -Inf)")

    # Validate probability bounds [-1e-12, 1 + 1e-12]
    if np.any(yp < -1e-12) or np.any(yp > 1.0 + 1e-12):
        raise DataIntegrityError("Probabilities in y_prob must be within [0, 1]")

    # Clip slight floating-point violations to [0, 1]
    yp = np.clip(yp, 0.0, 1.0)

    classes = _extract_classes(yt, np.array([]), labels=labels)
    unique_yt = np.unique(yt)

    if len(unique_yt) < 2:
        return MetricValue(
            metric_id="log_loss",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MINIMIZE,
            scope=scope,
            n_samples=n,
            warnings=(
                make_warning(
                    "W_METRIC_INSUFFICIENT_CLASSES",
                    f"log_loss requires at least 2 distinct classes in y_true, got {len(unique_yt)}",
                    {"n_classes": len(unique_yt)},
                ),
            ),
        )

    # Check that all elements of y_true exist in classes
    classes_set = set(classes)
    for y_val in unique_yt:
        if y_val not in classes_set:
            raise DataIntegrityError(f"Target contains class {y_val} not in specified labels")

    # Format probabilities into 2D matrix (n, K)
    k_classes = len(classes)
    if k_classes == 2:
        if yp.ndim == 1:
            yp_2d = np.column_stack([1.0 - yp, yp])
        elif yp.ndim == 2:
            if yp.shape[1] == 1:
                col = yp.squeeze(axis=1)
                yp_2d = np.column_stack([1.0 - col, col])
            elif yp.shape[1] == 2:
                # Row sum check within 1e-6
                row_sums = np.sum(yp, axis=1)
                if np.any(np.abs(row_sums - 1.0) > 1e-6):
                    raise DataIntegrityError("Probability row sums must equal 1.0 within 1e-6")
                yp_2d = yp
            else:
                raise DataIntegrityError(
                    f"Binary log_loss expected 1 or 2 columns, got shape {yp.shape}"
                )
        else:
            raise DataIntegrityError(f"y_prob has invalid ndim {yp.ndim}")
    else:
        # Multiclass case (K >= 3)
        if yp.ndim != 2:
            raise DataIntegrityError(
                f"Multiclass log_loss requires 2D array of probabilities, got ndim {yp.ndim}"
            )
        if yp.shape[1] != k_classes:
            raise DataIntegrityError(
                f"Multiclass log_loss expected shape ({n}, {k_classes}), got {yp.shape}"
            )

        row_sums = np.sum(yp, axis=1)
        if np.any(np.abs(row_sums - 1.0) > 1e-6):
            raise DataIntegrityError("Probability row sums must equal 1.0 within 1e-6")
        yp_2d = yp

    # Normalize rows, clip to [eps, 1 - eps], and re-normalize
    row_sums = np.sum(yp_2d, axis=1, keepdims=True)
    yp_norm = yp_2d / row_sums
    yp_clipped = np.clip(yp_norm, eps, 1.0 - eps)
    yp_final = yp_clipped / np.sum(yp_clipped, axis=1, keepdims=True)

    class_to_idx = {c: i for i, c in enumerate(classes)}
    y_indices = np.array([class_to_idx[y_val] for y_val in yt])
    sample_probs = yp_final[np.arange(n), y_indices]

    losses = -np.log(sample_probs)
    val = float(np.mean(losses))

    return MetricValue(
        metric_id="log_loss",
        value=val,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
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
    "roc_auc",
    "log_loss",
]
