"""Metrics module for Experimental ML Framework (Nível 1).

Provides pure, vectorized functions for predictive performance evaluation,
immutable evaluation records, formal metric catalog, and ADR-005 compliant
aggregation and ranking.
"""

from __future__ import annotations

from experimental_ml.metrics.catalog import (
    METRICS_CATALOG,
    compute_metric,
    get_metric_spec,
    list_metrics,
)
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
from experimental_ml.metrics.types import (
    AggregatedMetricValue,
    MetricEvaluationScope,
    MetricSpec,
    MetricValue,
    RankedCandidate,
)

__all__ = [
    "MetricEvaluationScope",
    "MetricValue",
    "AggregatedMetricValue",
    "MetricSpec",
    "RankedCandidate",
    "METRICS_CATALOG",
    "get_metric_spec",
    "list_metrics",
    "compute_metric",
    "mae",
    "rmse",
    "mbe",
    "r2",
    "rmse_rel_pct",
    "mape",
    "pearson",
    "kta",
    "accuracy",
    "balanced_accuracy",
    "precision",
    "recall",
    "f1",
    "roc_auc",
    "log_loss",
]
