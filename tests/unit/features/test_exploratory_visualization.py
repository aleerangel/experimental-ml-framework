"""Unit tests for Stage 2 exploratory feature redesign: unique Top-N, CSVs, labeled PNGs, and print-ready HTML."""

from __future__ import annotations

import numpy as np
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
    render_exploratory_target_csv,
)


def _sample_report() -> ExploratoryFeatureReport:
    return ExploratoryFeatureReport(
        scope=SCOPE_EXPLORATORY_FULL_DATA,
        dataset_hash="a" * 64,
        task_type=TaskType.REGRESSION,
        target_associations=(
            AssociationMeasure("x_fraco", "alvo", "PEARSON", 0.12, MetricStatus.VALID),
            AssociationMeasure("x_fraco", "alvo", "SPEARMAN", 0.14, MetricStatus.VALID),
            AssociationMeasure("x_neg_forte", "alvo", "PEARSON", -0.88, MetricStatus.VALID),
            AssociationMeasure("x_neg_forte", "alvo", "SPEARMAN", -0.90, MetricStatus.VALID),
            AssociationMeasure("x_const", "alvo", "PEARSON", float("nan"), MetricStatus.UNDEFINED_NAN),
            AssociationMeasure("x_const", "alvo", "SPEARMAN", float("nan"), MetricStatus.UNDEFINED_NAN),
            AssociationMeasure("x_mod", "alvo", "PEARSON", 0.45, MetricStatus.VALID),
            AssociationMeasure("x_mod", "alvo", "SPEARMAN", 0.55, MetricStatus.VALID),
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
    """summary() aggregates unique features by mean |value|, avoids duplicates, and keeps UNDEFINED_NAN separate."""
    report = _sample_report()
    text = report.summary(top_n=2)

    assert "EXPLORATORY_FULL_DATA" in text
    assert "a" * 64 not in text  # never expose raw 64-hex hash
    assert "Atributos avaliados: 4 (válidos: 3, indefinidos: 1)" in text
    assert "1. x_neg_forte — Média |·|: 0.8900 (Forte) [PEARSON=-0.8800, SPEARMAN=-0.9000]" in text
    assert "2. x_mod — Média |·|: 0.5000 (Moderada) [PEARSON=+0.4500, SPEARMAN=+0.5500]" in text
    assert text.count("x_neg_forte —") == 1
    assert "x_fraco" not in text  # top_n=2 limits to 2 unique features
    assert "x_const (UNDEFINED_NAN)" in text
    assert "x_neg_forte <-> x_mod [PEARSON]: +0.9200" in text
    for w in METHODOLOGICAL_WARNINGS:
        assert w in text

    with pytest.raises(ConfigurationError):
        report.summary(top_n=0)


def test_render_exploratory_report_md_and_html() -> None:
    """render_exploratory_report generates clean Markdown and print/PDF-ready offline HTML without giant inline matrix."""
    report = _sample_report()
    figs = (
        "../figures/exploratory_target_associations.png",
        "../figures/exploratory_redundancy_heatmap.png",
    )
    md = render_exploratory_report(report, fmt="markdown", figure_paths=figs)
    assert "EXPLORATORY_FULL_DATA" in md
    assert "| 1 | `x_neg_forte` | 0.8900 | Forte |" in md
    assert md.split("## 2.")[0].count("| `x_neg_forte` |") == 1
    assert "exploratory_target_associations.csv" in md
    assert "exploratory_redundancy_matrix.csv" in md
    assert "exploratory_target_associations.png" in md
    assert "## 4. Como Usar Estes Indicadores para Montar Cenários" in md

    html_doc = render_exploratory_report(report, fmt="html", figure_paths=figs)
    assert "<!DOCTYPE html>" in html_doc
    assert "@page { size: A4 portrait;" in html_doc
    assert "@media print" in html_doc
    assert "print-color-adjust: exact" in html_doc
    assert "matrix-wrap" not in html_doc
    assert "http://" not in html_doc and "https://" not in html_doc
    assert "a" * 64 not in html_doc

    with pytest.raises(ConfigurationError):
        render_exploratory_report(report, fmt="pdf")


def test_exploratory_csv_exports() -> None:
    """CSV renderers export deduplicated ranked associations and full symmetric redundancy matrix."""
    report = _sample_report()
    target_csv = render_exploratory_target_csv(report).strip().splitlines()
    assert target_csv[0] == "rank,feature,mean_abs,strength,metrics_detail,status"
    assert len(target_csv) == 5  # header + 3 valid + 1 nan
    assert target_csv[1].startswith("1,x_neg_forte,0.890000,Forte,")
    assert target_csv[4].startswith(",x_const,NaN,N/A,")

    matrix_csv = render_exploratory_redundancy_csv(report).strip().splitlines()
    assert matrix_csv[0] == "feature,x_neg_forte,x_mod,x_fraco"
    assert len(matrix_csv) == 4


def test_exploratory_png_charts_labeled_and_no_svg() -> None:
    """PNG bar chart and heatmap are deterministic, contain rendered bitmap labels, and reject SVG."""
    report = _sample_report()

    png_bar_1 = render_exploratory_target_chart(report, fmt="png")
    png_bar_2 = render_exploratory_target_chart(report, fmt="png")
    assert png_bar_1 == png_bar_2
    assert png_bar_1.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(png_bar_1) > 2000

    png_hm_1 = render_exploratory_redundancy_heatmap(report, fmt="png")
    png_hm_2 = render_exploratory_redundancy_heatmap(report, fmt="png")
    assert png_hm_1 == png_hm_2
    assert png_hm_1.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(png_hm_1) > 2000

    with pytest.raises(ConfigurationError):
        render_exploratory_target_chart(report, fmt="svg")
    with pytest.raises(ConfigurationError):
        render_exploratory_redundancy_heatmap(report, fmt="svg")


def test_m10_exploratory_charts_matplotlib_utf8() -> None:
    """C3 (M10): Stage 2 charts use Matplotlib Agg, preserve Portuguese UTF-8 accents, and handle long feature names."""
    from experimental_ml.features.visualization import _prepare_target_chart_data, _prepare_redundancy_heatmap_data

    long_name = "razão_média_de_atenuação_biométrica_longa_35chars"
    report = ExploratoryFeatureReport(
        scope=SCOPE_EXPLORATORY_FULL_DATA,
        dataset_hash="b" * 64,
        task_type=TaskType.REGRESSION,
        target_associations=(
            AssociationMeasure(long_name, "alvo_saúde", "PEARSON", 0.78, MetricStatus.VALID),
            AssociationMeasure("pressão_sistólica", "alvo_saúde", "PEARSON", -0.42, MetricStatus.VALID),
        ),
        pairwise_redundancy_matrix={
            long_name: {long_name: 1.0, "pressão_sistólica": 0.35},
            "pressão_sistólica": {long_name: 0.35, "pressão_sistólica": 1.0},
        },
        high_redundancy_pairs=(),
        warnings=("Aviso metodológico de teste",),
    )

    t_name, labels, vals, _, _ = _prepare_target_chart_data(report, top_n=10)
    assert t_name == "alvo_saúde"
    assert labels[0] == long_name
    assert vals[0] == pytest.approx(0.78)

    feats, mat = _prepare_redundancy_heatmap_data(report)
    assert feats == [long_name, "pressão_sistólica"]
    assert mat.shape == (2, 2)

    png_bar = render_exploratory_target_chart(report, fmt="png")
    png_hm = render_exploratory_redundancy_heatmap(report, fmt="png")
    assert png_bar.startswith(b"\x89PNG\r\n\x1a\n")
    assert png_hm.startswith(b"\x89PNG\r\n\x1a\n")
