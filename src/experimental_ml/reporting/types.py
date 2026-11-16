"""Domain enumerations and immutable frozen dataclasses for Stage 6 reporting (REP-01).

Conforms to XCUT-02 (numpy and stdlib only), CA-E6-01, CA-E6-02, and RNF02.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from types import MappingProxyType
from typing import Any, Mapping

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.statistics.storage import LoadedStatisticsArtifacts


class ReportFamily(StrEnum):
    """Canonical 7 families of scientific tables and visualizations (RF6.2)."""

    A_DATA_CHARACTERIZATION = "A_DATA_CHARACTERIZATION"
    B_FEATURE_SCENARIOS = "B_FEATURE_SCENARIOS"
    C_MODELS_CONFIG = "C_MODELS_CONFIG"
    D_PREDICTIVE_PERFORMANCE = "D_PREDICTIVE_PERFORMANCE"
    E_STATISTICAL_COMPARISONS = "E_STATISTICAL_COMPARISONS"
    F_STABILITY_COST_PARETO = "F_STABILITY_COST_PARETO"
    G_MODEL_SPECIFIC_ARTIFACTS = "G_MODEL_SPECIFIC_ARTIFACTS"


class ReportAudience(StrEnum):
    """Target audience presets for deterministic report content selection (RF6.1)."""

    FULL_LAB = "FULL_LAB"
    ARTICLE_COMPACT = "ARTICLE_COMPACT"
    CUSTOM = "CUSTOM"


class PlotType(StrEnum):
    """Supported plot specification types for Stage 6 visualizations."""

    BAR_COMPARISON = "BAR_COMPARISON"
    SCATTER_PARITY = "SCATTER_PARITY"
    PAIRED_DIFF_CI = "PAIRED_DIFF_CI"
    PARETO_TRADEOFF = "PARETO_TRADEOFF"
    HEATMAP = "HEATMAP"
    LINE_LEARNING = "LINE_LEARNING"


class ColumnAlignment(StrEnum):
    """Column text alignment for tabular renderers."""

    LEFT = "LEFT"
    RIGHT = "RIGHT"
    CENTER = "CENTER"


def _is_absolute_any_os(path_str: str) -> bool:
    return Path(path_str).is_absolute() or PureWindowsPath(path_str).is_absolute()


@dataclass(frozen=True, slots=True)
class ArtifactProvenance:
    """Lineage and provenance manifest for an exported table or figure (RF6.3, CA-E6-02)."""

    artifact_id: str
    artifact_type: str
    family: ReportFamily
    experiment_id: str
    partition_plan_id: str
    model_ids: tuple[str, ...]
    scenario_ids: tuple[str, ...]
    metrics: tuple[str, ...]
    source_relative_paths: tuple[str, ...]
    created_at_utc: str

    def __post_init__(self) -> None:
        if not isinstance(self.family, ReportFamily):
            object.__setattr__(self, "family", ReportFamily(self.family))
        for p in self.source_relative_paths:
            if _is_absolute_any_os(str(p)):
                raise ContractViolationError(
                    f"ArtifactProvenance.source_relative_paths must contain only relative paths; got {p!r}."
                )
        object.__setattr__(self, "model_ids", tuple(str(x) for x in self.model_ids))
        object.__setattr__(self, "scenario_ids", tuple(str(x) for x in self.scenario_ids))
        object.__setattr__(self, "metrics", tuple(str(x) for x in self.metrics))
        object.__setattr__(
            self, "source_relative_paths", tuple(str(x) for x in self.source_relative_paths)
        )


@dataclass(frozen=True, slots=True)
class ReportContentSelection:
    """Deterministic filter selection for Stage 6 reporting (RF6.1)."""

    audience: ReportAudience = ReportAudience.FULL_LAB
    families: tuple[ReportFamily, ...] = field(default_factory=tuple)
    model_ids: tuple[str, ...] = field(default_factory=tuple)
    scenario_ids: tuple[str, ...] = field(default_factory=tuple)
    metric_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.audience, ReportAudience):
            object.__setattr__(self, "audience", ReportAudience(self.audience))
        fams = tuple(f if isinstance(f, ReportFamily) else ReportFamily(f) for f in self.families)
        if self.audience == ReportAudience.CUSTOM and not fams:
            raise ConfigurationError(
                "ReportContentSelection.families must not be empty when audience is CUSTOM."
            )
        object.__setattr__(self, "families", fams)
        object.__setattr__(self, "model_ids", tuple(str(m) for m in self.model_ids))
        object.__setattr__(self, "scenario_ids", tuple(str(s) for s in self.scenario_ids))
        object.__setattr__(self, "metric_ids", tuple(str(m) for m in self.metric_ids))


@dataclass(frozen=True, slots=True)
class TableColumn:
    """Column metadata for TableModel."""

    key: str
    header: str
    align: ColumnAlignment = ColumnAlignment.LEFT
    numeric_format: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.align, ColumnAlignment):
            object.__setattr__(self, "align", ColumnAlignment(self.align))


@dataclass(frozen=True, slots=True)
class TableModel:
    """Format-independent immutable table representation storing exact values (CA-E6-01)."""

    table_id: str
    family: ReportFamily
    title: str
    caption: str
    columns: tuple[TableColumn, ...]
    rows: tuple[Mapping[str, Any], ...]
    notes: tuple[str, ...]
    provenance: ArtifactProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.family, ReportFamily):
            object.__setattr__(self, "family", ReportFamily(self.family))
        object.__setattr__(self, "columns", tuple(self.columns))
        frozen_rows = tuple(
            r if isinstance(r, MappingProxyType) else MappingProxyType(dict(r))
            for r in self.rows
        )
        object.__setattr__(self, "rows", frozen_rows)
        object.__setattr__(self, "notes", tuple(str(n) for n in self.notes))


@dataclass(frozen=True, slots=True)
class PlotSeries:
    """Single data series in a PlotSpecification."""

    name: str
    x_values: tuple[Any, ...]
    y_values: tuple[float, ...]
    y_err: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "x_values", tuple(self.x_values))
        object.__setattr__(self, "y_values", tuple(float(y) for y in self.y_values))
        if self.y_err is not None:
            object.__setattr__(self, "y_err", tuple(float(e) for e in self.y_err))


@dataclass(frozen=True, slots=True)
class PlotSpecification:
    """Format-independent immutable visualization specification (RF6.2)."""

    plot_id: str
    family: ReportFamily
    plot_type: PlotType
    title: str
    x_label: str
    y_label: str
    series: tuple[PlotSeries, ...]
    notes: tuple[str, ...]
    provenance: ArtifactProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.family, ReportFamily):
            object.__setattr__(self, "family", ReportFamily(self.family))
        if not isinstance(self.plot_type, PlotType):
            object.__setattr__(self, "plot_type", PlotType(self.plot_type))
        object.__setattr__(self, "series", tuple(self.series))
        object.__setattr__(self, "notes", tuple(str(n) for n in self.notes))


@dataclass(frozen=True, slots=True)
class LoadedExperimentData:
    """Immutable read-only container of Stage 1-5 persisted experiment artifacts (CA-E6-01)."""

    experiment_id: str
    partition_plan_id: str
    statistics: LoadedStatisticsArtifacts
    dataset_profile: Mapping[str, Any] | None = None
    preparation_plan: Mapping[str, Any] | None = None
    partition_plan: Mapping[str, Any] | None = None
    scenarios_catalog: Mapping[str, Any] | None = None
    models_catalog: Mapping[str, Any] | None = None
    execution_state: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for attr in (
            "dataset_profile",
            "preparation_plan",
            "partition_plan",
            "scenarios_catalog",
            "models_catalog",
            "execution_state",
        ):
            val = getattr(self, attr)
            if val is not None and not isinstance(val, MappingProxyType):
                object.__setattr__(self, attr, MappingProxyType(dict(val)))


@dataclass(frozen=True, slots=True)
class ResearcherDeclarations:
    """Explicitly declared scientific provenance provided by the researcher (ARQUITETURA §3.6)."""

    scientific_objective: str = ""
    data_origin_note: str = ""
    metric_rationale: str = ""
    additional_notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.additional_notes, tuple):
            object.__setattr__(
                self, "additional_notes", tuple(str(n) for n in self.additional_notes)
            )


class PackageMode(StrEnum):
    """Export mode for the Stage 6 reproducibility package (RF6.4)."""

    FULL_PACKAGE = "full_package"
    REDUCED_NO_RAW_DATA = "reduced_no_raw_data"


def _validate_relative_posix(path_str: str, field_name: str) -> str:
    if not path_str or "\\" in path_str:
        raise ContractViolationError(f"{field_name} must be a relative POSIX path: {path_str!r}")
    if Path(path_str).is_absolute() or PureWindowsPath(path_str).is_absolute():
        raise ContractViolationError(f"{field_name} must not be an absolute path: {path_str!r}")
    if ".." in path_str.split("/"):
        raise ContractViolationError(f"{field_name} must not contain '..' traversal: {path_str!r}")
    return path_str


@dataclass(frozen=True, slots=True)
class ReproducibilityPackageManifest:
    """Immutable manifest describing an exported Stage 6 reproducibility package (RF6.3, RF6.4)."""

    experiment_id: str
    partition_plan_id: str
    package_mode: PackageMode
    reproduction_level: str
    exported_files: tuple[str, ...]
    checksums_file: str
    provenance_file: str

    def __post_init__(self) -> None:
        if not isinstance(self.package_mode, PackageMode):
            object.__setattr__(self, "package_mode", PackageMode(self.package_mode))
        validated_files = tuple(
            _validate_relative_posix(str(p), "exported_files") for p in self.exported_files
        )
        object.__setattr__(self, "exported_files", validated_files)
        _validate_relative_posix(self.checksums_file, "checksums_file")
        _validate_relative_posix(self.provenance_file, "provenance_file")
