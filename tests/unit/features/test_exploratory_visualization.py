"""Unit tests for Stage 2 exploratory feature visualization, summary, and charts."""

from __future__ import annotations

import pytest

from experimental_ml.core.enums import MetricStatus, TaskType
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.features.types import (
    METHODOLOGICAL_WARNINGS,
    SCOPE_EXPLORATORY_FULL_DATA,
    AssociationMeasure,
    ExploratoryFeatureReport,
    RedundancyPair,
)


def _sample_report() -> ExploratoryFeatureReport:
    return ExploratoryFeatureReport(
        scope=SCOPE_EXPLORATORY_FULL_DATA,
        dataset_hash="a" * 64,
        task_type=TaskType.REGRESSION,
        target_associations=(
            AssociationMeasure("x_fraco", "alvo", "PEARSON", 0.12, MetricStatus.VALID),
            AssociationMeasure("x_neg_forte", "alvo", "PEARSON", -0.88, MetricStatus.VALID),
            AssociationMeasure("x_const", "alvo", "PEARSON", float("nan"), MetricStatus.UNDEFINED_NAN),
            AssociationMeasure("x_mod", "alvo", "PEARSON", 0.45, MetricStatus.VALID),
        ),
        pairwise_redundancy_matrix={
            "x_neg_forte": {"x_neg_forte": 1.0, "x_mod": 0.92, "x_fraco": 0.05},
            "x_mod": {"x_neg_forte": 0.92, "x_mod": 1.0, "x_fraco": -0.10},
            "x_fraco": {"x_neg_forte": 0.05, "x_mod": -0.10, "x_fraco": 1.0},
        },
        high_redundancy_pairs=(
            RedundancyPair("x_neg_forte", "x_mod", "PEARSON", 0.92, MetricStatus.VALID),
        ),
        warnings=METHODOLOGICAL_WARNINGS,
    )


def test_exploratory_report_summary_ranking_and_nan() -> None:
    """summary() ranks valid associations by |value|, keeps UNDEFINED_NAN separate, and lists warnings."""
    report = _sample_report()
    text = report.summary(top_n=2)

    assert "EXPLORATORY_FULL_DATA" in text
    assert "a" * 64 not in text  # never expose raw 64-hex hash
    assert "1. x_neg_forte [PEARSON]: -0.8800 (Forte)" in text
    assert "2. x_mod [PEARSON]: +0.4500 (Moderada)" in text
    assert "x_fraco" not in text  # top_n=2 limits ranked list
    assert "x_const (UNDEFINED_NAN)" in text
    assert "x_neg_forte <-> x_mod [PEARSON]: +0.9200" in text
    for w in METHODOLOGICAL_WARNINGS:
        assert w in text

    with pytest.raises(ConfigurationError):
        report.summary(top_n=0)
