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
from experimental_ml.features.visualization import (
    render_exploratory_redundancy_csv,
    render_exploratory_redundancy_heatmap,
    render_exploratory_report,
    render_exploratory_target_chart,
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


def test_render_exploratory_report_md_and_html() -> None:
    """render_exploratory_report generates Markdown and offline HTML with all 5 sections."""
    report = _sample_report()
    md = render_exploratory_report(
        report,
        fmt="markdown",
        figure_paths=("../figures/exploratory_target_associations.svg",),
    )
    assert "EXPLORATORY_FULL_DATA" in md
    assert "| 1 | `x_neg_forte` | `PEARSON` | -0.8800 | 0.8800 | Forte |" in md
    assert "x_const" in md
    assert "x_neg_forte` | `x_mod`" in md
    assert "## 3. Matriz Completa Preditor × Preditor" in md
    assert "## 5. Como Usar Estes Indicadores para Montar Cenários" in md
    assert "![Gráfico exploratório](../figures/exploratory_target_associations.svg)" in md

    html_doc = render_exploratory_report(
        report,
        fmt="html",
        figure_paths=("../figures/exploratory_target_associations.svg",),
    )
    assert "<!DOCTYPE html>" in html_doc
    assert "warning-box" in html_doc
    assert "guide-box" in html_doc
    assert "http://" not in html_doc and "https://" not in html_doc
    assert "x_neg_forte" in html_doc
    assert "a" * 64 not in html_doc

    with pytest.raises(ConfigurationError):
        render_exploratory_report(report, fmt="pdf")


def test_exploratory_svg_and_png_charts_deterministic() -> None:
    """Target bar chart and redundancy heatmap produce deterministic SVG and PNG bytes."""
    report = _sample_report()

    svg_bar_1 = render_exploratory_target_chart(report, fmt="svg")
    svg_bar_2 = render_exploratory_target_chart(report, fmt="svg")
    assert svg_bar_1 == svg_bar_2
    assert svg_bar_1.startswith(b"<svg ")
    assert b"x_neg_forte" in svg_bar_1

    png_bar = render_exploratory_target_chart(report, fmt="png")
    assert png_bar.startswith(b"\x89PNG\r\n\x1a\n")

    svg_hm = render_exploratory_redundancy_heatmap(report, fmt="svg")
    assert svg_hm.startswith(b"<svg ")
    assert b"0.92" in svg_hm

    png_hm_1 = render_exploratory_redundancy_heatmap(report, fmt="png")
    png_hm_2 = render_exploratory_redundancy_heatmap(report, fmt="png")
    assert png_hm_1 == png_hm_2
    assert png_hm_1.startswith(b"\x89PNG\r\n\x1a\n")


def test_large_redundancy_matrix_externalized_to_csv_and_heatmap() -> None:
    """When >8 predictors exist, MD/HTML link to exploratory_redundancy_matrix.csv & heatmap without giant inline table."""
    feats = [f"f_{i:02d}" for i in range(10)]
    matrix = {fa: {fb: (1.0 if fa == fb else 0.1) for fb in feats} for fa in feats}
    large_report = ExploratoryFeatureReport(
        scope=SCOPE_EXPLORATORY_FULL_DATA,
        dataset_hash="b" * 64,
        task_type=TaskType.REGRESSION,
        target_associations=(AssociationMeasure("f_00", "alvo", "PEARSON", 0.5, MetricStatus.VALID),),
        pairwise_redundancy_matrix=matrix,
        high_redundancy_pairs=(),
        warnings=METHODOLOGICAL_WARNINGS,
    )

    csv_text = render_exploratory_redundancy_csv(large_report)
    lines = csv_text.strip().splitlines()
    assert len(lines) == 11
    assert lines[0].startswith("feature,f_00,f_01")

    md = render_exploratory_report(large_report, fmt="markdown")
    assert "exploratory_redundancy_matrix.csv" in md
    assert "exploratory_redundancy_heatmap.svg" in md
    assert "| Atributo | `f_00`" not in md

    html_doc = render_exploratory_report(large_report, fmt="html")
    assert "exploratory_redundancy_matrix.csv" in html_doc
    assert '<table class="matrix-table">' not in html_doc
