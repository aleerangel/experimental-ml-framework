"""Metrics module for Experimental ML Framework (Nível 1).

Provides pure, vectorized functions for predictive performance evaluation,
immutable evaluation records, formal metric catalog, and ADR-005 compliant
aggregation and ranking.
"""

from __future__ import annotations

from experimental_ml.metrics.classification import (
    accuracy,
    balanced_accuracy,
    f1,
    precision,
    recall,
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
]
