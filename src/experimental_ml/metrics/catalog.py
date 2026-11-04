"""Centralized metric catalog and resolution functions for experimental_ml.metrics."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from experimental_ml.core.enums import MetricDirection, TaskType
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.metrics.classification import (
    accuracy,
    balanced_accuracy,
    f1,
    log_loss,
    precision,
    recall,
    roc_auc,
)
from experimental_ml.metrics.regression import (
    kta,
    mae,
    mape,
    mbe,
    pearson,
    r2,
    rmse,
    rmse_rel_pct,
)
from experimental_ml.metrics.types import MetricSpec, MetricValue

_SPECS: dict[str, MetricSpec] = {
    "mae": MetricSpec(
        metric_id="mae",
        name="Mean Absolute Error",
        family="Direct-Scale Error",
        direction=MetricDirection.MINIMIZE,
        compare_by_abs=False,
        supported_tasks=(TaskType.REGRESSION,),
        func=mae,
        rtol=1e-12,
        atol=1e-12,
    ),
    "rmse": MetricSpec(
        metric_id="rmse",
        name="Root Mean Squared Error",
        family="Direct-Scale Error",
        direction=MetricDirection.MINIMIZE,
        compare_by_abs=False,
        supported_tasks=(TaskType.REGRESSION,),
        func=rmse,
        rtol=1e-12,
        atol=1e-12,
    ),
    "mbe": MetricSpec(
        metric_id="mbe",
        name="Mean Bias Error",
        family="Direct-Scale Error",
        direction=MetricDirection.MINIMIZE,
        compare_by_abs=True,
        supported_tasks=(TaskType.REGRESSION,),
        func=mbe,
        rtol=1e-12,
        atol=1e-12,
    ),
    "r2": MetricSpec(
        metric_id="r2",
        name="Coefficient of Determination (R2)",
        family="Dimensionless Ratio",
        direction=MetricDirection.MAXIMIZE,
        compare_by_abs=False,
        supported_tasks=(TaskType.REGRESSION,),
        func=r2,
        rtol=1e-10,
        atol=1e-12,
    ),
    "rmse_rel_pct": MetricSpec(
        metric_id="rmse_rel_pct",
        name="Relative Root Mean Squared Error %",
        family="Dimensionless Ratio",
        direction=MetricDirection.MINIMIZE,
        compare_by_abs=False,
        supported_tasks=(TaskType.REGRESSION,),
        func=rmse_rel_pct,
        rtol=1e-10,
        atol=1e-12,
    ),
    "mape": MetricSpec(
        metric_id="mape",
        name="Mean Absolute Percentage Error",
        family="Dimensionless Ratio",
        direction=MetricDirection.MINIMIZE,
        compare_by_abs=False,
        supported_tasks=(TaskType.REGRESSION,),
        func=mape,
        rtol=1e-10,
        atol=1e-12,
    ),
    "pearson": MetricSpec(
        metric_id="pearson",
        name="Pearson Correlation Coefficient",
        family="Dimensionless Ratio",
        direction=MetricDirection.MAXIMIZE,
        compare_by_abs=False,
        supported_tasks=(TaskType.REGRESSION,),
        func=pearson,
        rtol=1e-10,
        atol=1e-12,
    ),
    "kta": MetricSpec(
        metric_id="kta",
        name="Kernel Target Alignment",
        family="Kernel Alignment",
        direction=MetricDirection.MAXIMIZE,
        compare_by_abs=False,
        supported_tasks=(
            TaskType.REGRESSION,
            TaskType.BINARY_CLASSIFICATION,
            TaskType.MULTICLASS_CLASSIFICATION,
        ),
        func=kta,
        rtol=1e-10,
        atol=1e-12,
    ),
    "accuracy": MetricSpec(
        metric_id="accuracy",
        name="Accuracy",
        family="Discrete Ratio",
        direction=MetricDirection.MAXIMIZE,
        compare_by_abs=False,
        supported_tasks=(
            TaskType.BINARY_CLASSIFICATION,
            TaskType.MULTICLASS_CLASSIFICATION,
        ),
        func=accuracy,
        rtol=1e-14,
        atol=1e-15,
    ),
    "balanced_accuracy": MetricSpec(
        metric_id="balanced_accuracy",
        name="Balanced Accuracy",
        family="Discrete Ratio",
        direction=MetricDirection.MAXIMIZE,
        compare_by_abs=False,
        supported_tasks=(
            TaskType.BINARY_CLASSIFICATION,
            TaskType.MULTICLASS_CLASSIFICATION,
        ),
        func=balanced_accuracy,
        rtol=1e-14,
        atol=1e-15,
    ),
    "precision": MetricSpec(
        metric_id="precision",
        name="Precision",
        family="Discrete Ratio",
        direction=MetricDirection.MAXIMIZE,
        compare_by_abs=False,
        supported_tasks=(
            TaskType.BINARY_CLASSIFICATION,
            TaskType.MULTICLASS_CLASSIFICATION,
        ),
        func=precision,
        rtol=1e-14,
        atol=1e-15,
    ),
    "recall": MetricSpec(
        metric_id="recall",
        name="Recall",
        family="Discrete Ratio",
        direction=MetricDirection.MAXIMIZE,
        compare_by_abs=False,
        supported_tasks=(
            TaskType.BINARY_CLASSIFICATION,
            TaskType.MULTICLASS_CLASSIFICATION,
        ),
        func=recall,
        rtol=1e-14,
        atol=1e-15,
    ),
    "f1": MetricSpec(
        metric_id="f1",
        name="F1 Score",
        family="Discrete Ratio",
        direction=MetricDirection.MAXIMIZE,
        compare_by_abs=False,
        supported_tasks=(
            TaskType.BINARY_CLASSIFICATION,
            TaskType.MULTICLASS_CLASSIFICATION,
        ),
        func=f1,
        rtol=1e-14,
        atol=1e-15,
    ),
    "roc_auc": MetricSpec(
        metric_id="roc_auc",
        name="Area Under ROC Curve",
        family="Probabilistic / Ranking",
        direction=MetricDirection.MAXIMIZE,
        compare_by_abs=False,
        supported_tasks=(
            TaskType.BINARY_CLASSIFICATION,
            TaskType.MULTICLASS_CLASSIFICATION,
        ),
        func=roc_auc,
        rtol=1e-9,
        atol=1e-11,
    ),
    "log_loss": MetricSpec(
        metric_id="log_loss",
        name="Logarithmic Loss",
        family="Probabilistic / Ranking",
        direction=MetricDirection.MINIMIZE,
        compare_by_abs=False,
        supported_tasks=(
            TaskType.BINARY_CLASSIFICATION,
            TaskType.MULTICLASS_CLASSIFICATION,
        ),
        func=log_loss,
        rtol=1e-9,
        atol=1e-11,
    ),
}

METRICS_CATALOG: Mapping[str, MetricSpec] = MappingProxyType(_SPECS)


def get_metric_spec(metric_id: str) -> MetricSpec:
    """Retrieve MetricSpec from catalog case-insensitively.

    Args:
        metric_id: Identifier of metric (e.g. 'rmse', 'mbe', 'accuracy').

    Returns:
        MetricSpec for the given metric.

    Raises:
        ConfigurationError: If metric_id is not in catalog.
    """
    key = str(metric_id).strip().lower()
    if key not in METRICS_CATALOG:
        raise ConfigurationError(
            f"Metric '{metric_id}' not found in catalog. Available metrics: {sorted(METRICS_CATALOG.keys())}"
        )
    return METRICS_CATALOG[key]


def list_metrics(task: TaskType | str | None = None) -> tuple[str, ...]:
    """List available metric identifiers sorted alphabetically, optionally filtered by task.

    Args:
        task: Optional TaskType enum or string representation to filter supported metrics.

    Returns:
        Sorted tuple of canonical metric identifiers.

    Raises:
        ConfigurationError: If task string cannot be coerced to TaskType.
    """
    if task is not None:
        if isinstance(task, str):
            try:
                task_enum = TaskType(task)
            except ValueError as exc:
                raise ConfigurationError(
                    f"Unknown task type '{task}'. Valid task types: {[t.value for t in TaskType]}"
                ) from exc
        else:
            task_enum = task

        filtered = [
            m_id for m_id, spec in METRICS_CATALOG.items() if task_enum in spec.supported_tasks
        ]
        return tuple(sorted(filtered))

    return tuple(sorted(METRICS_CATALOG.keys()))


def compute_metric(
    metric_id: str,
    y_true: Any,
    y_pred_or_score: Any,
    **kwargs: Any,
) -> MetricValue:
    """Compute metric by resolving spec from catalog and dispatching to implementation.

    Args:
        metric_id: Identifier of the metric to compute.
        y_true: Ground truth observations.
        y_pred_or_score: Predictions, probabilities, scores or Gram matrices.
        **kwargs: Additional parameters forwarded to metric function (e.g. scope, average, pos_label).

    Returns:
        MetricValue result.
    """
    spec = get_metric_spec(metric_id)
    return spec.func(y_true, y_pred_or_score, **kwargs)


__all__ = [
    "METRICS_CATALOG",
    "get_metric_spec",
    "list_metrics",
    "compute_metric",
]
