"""Experimental reporting and reproducibility package (Marco M7 — Etapa 6).

Provides immutable publication contracts, read-only Stage 1-5 loaders,
7-family scientific table builders, and deterministic CSV/Markdown/LaTeX renderers.
"""

from experimental_ml.reporting.figures import (
    build_figure_spec,
    render_figure,
)
from experimental_ml.reporting.loader import (
    load_experiment_artifacts_readonly,
    select_report_content,
)
from experimental_ml.reporting.packaging import build_reproducibility_package
from experimental_ml.reporting.report import render_full_report
from experimental_ml.reporting.tables import (
    build_table_model,
    render_table_csv,
    render_table_latex,
    render_table_markdown,
)
from experimental_ml.reporting.types import (
    ArtifactProvenance,
    ColumnAlignment,
    LoadedExperimentData,
    PackageMode,
    PlotSeries,
    PlotSpecification,
    PlotType,
    ReportAudience,
    ReportContentSelection,
    ReportFamily,
    ReproducibilityPackageManifest,
    ResearcherDeclarations,
    TableColumn,
    TableModel,
)

__all__ = [
    "ReportFamily",
    "ReportAudience",
    "PlotType",
    "ColumnAlignment",
    "PackageMode",
    "ArtifactProvenance",
    "ReportContentSelection",
    "ResearcherDeclarations",
    "ReproducibilityPackageManifest",
    "TableColumn",
    "TableModel",
    "PlotSeries",
    "PlotSpecification",
    "LoadedExperimentData",
    "load_experiment_artifacts_readonly",
    "select_report_content",
    "build_table_model",
    "render_table_csv",
    "render_table_markdown",
    "render_table_latex",
    "build_figure_spec",
    "render_figure",
    "render_full_report",
    "build_reproducibility_package",
]
