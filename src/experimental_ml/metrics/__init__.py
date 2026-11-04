"""Metrics module for Experimental ML Framework (Nível 1).

Provides pure, vectorized functions for predictive performance evaluation,
immutable evaluation records, formal metric catalog, and ADR-005 compliant
aggregation and ranking.
"""

from __future__ import annotations

from experimental_ml.metrics.regression import mae, mbe, rmse
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
]
