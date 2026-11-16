"""Unit tests for M7.1 reporting contracts and ArtifactProvenance (REP-01)."""

from dataclasses import FrozenInstanceError
import pytest

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.reporting.types import (
    ArtifactProvenance,
    ColumnAlignment,
    PlotSeries,
    PlotSpecification,
    PlotType,
    ReportAudience,
    ReportContentSelection,
    ReportFamily,
    TableColumn,
    TableModel,
)


def test_m71_01_enums_values() -> None:
    """C1: Canonical enums for ReportFamily (A-G), ReportAudience, PlotType, ColumnAlignment."""
    assert set(ReportFamily) == {
        ReportFamily.A_DATA_CHARACTERIZATION,
        ReportFamily.B_FEATURE_SCENARIOS,
        ReportFamily.C_MODELS_CONFIG,
        ReportFamily.D_PREDICTIVE_PERFORMANCE,
        ReportFamily.E_STATISTICAL_COMPARISONS,
        ReportFamily.F_STABILITY_COST_PARETO,
        ReportFamily.G_MODEL_SPECIFIC_ARTIFACTS,
    }
    assert set(ReportAudience) == {
        ReportAudience.FULL_LAB,
        ReportAudience.ARTICLE_COMPACT,
        ReportAudience.CUSTOM,
    }
    assert set(ColumnAlignment) == {
        ColumnAlignment.LEFT,
        ColumnAlignment.RIGHT,
        ColumnAlignment.CENTER,
    }
    assert PlotType.PARETO_TRADEOFF in set(PlotType)


def test_m71_01_frozen_immutability() -> None:
    """C2: Reporting dataclasses are frozen and raise FrozenInstanceError on mutation."""
    prov = ArtifactProvenance(
        artifact_id="tbl_d_001",
        artifact_type="table",
        family=ReportFamily.D_PREDICTIVE_PERFORMANCE,
        experiment_id="exp_01",
        partition_plan_id="pp_01",
        model_ids=("m1",),
        scenario_ids=("s1",),
        metrics=("rmse",),
        source_relative_paths=("statistics/descriptive_consolidation.json",),
        created_at_utc="2026-11-16T00:00:00Z",
    )
    sel = ReportContentSelection(
        audience=ReportAudience.CUSTOM,
        families=(ReportFamily.D_PREDICTIVE_PERFORMANCE,),
    )
    col = TableColumn(key="mean", header="Mean", align=ColumnAlignment.RIGHT, numeric_format="{:.4f}")
    tbl = TableModel(
        table_id="tbl_d",
        family=ReportFamily.D_PREDICTIVE_PERFORMANCE,
        title="Predictive Performance",
        caption="CV performance summary",
        columns=(col,),
        rows=({"mean": 1.234567},),
        notes=("Note 1",),
        provenance=prov,
    )
    ps = PlotSeries(name="m1", x_values=(1.0, 2.0), y_values=(0.5, 0.4))
    plot = PlotSpecification(
        plot_id="plt_01",
        family=ReportFamily.D_PREDICTIVE_PERFORMANCE,
        plot_type=PlotType.BAR_COMPARISON,
        title="RMSE Comparison",
        x_label="Model",
        y_label="RMSE",
        series=(ps,),
        notes=(),
        provenance=prov,
    )

    with pytest.raises(ConfigurationError):
        ReportContentSelection(audience=ReportAudience.CUSTOM, families=())

    for obj, attr, val in [
        (prov, "artifact_id", "x"),
        (sel, "audience", ReportAudience.FULL_LAB),
        (col, "header", "Other"),
        (tbl, "title", "Other"),
        (ps, "name", "Other"),
        (plot, "title", "Other"),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, attr, val)  # type: ignore[misc]


def test_m71_01_provenance_rejects_absolute_paths() -> None:
    """C3: ArtifactProvenance raises ContractViolationError on absolute source paths."""
    with pytest.raises(ContractViolationError):
        ArtifactProvenance(
            artifact_id="tbl_d_001",
            artifact_type="table",
            family=ReportFamily.D_PREDICTIVE_PERFORMANCE,
            experiment_id="exp_01",
            partition_plan_id="pp_01",
            model_ids=("m1",),
            scenario_ids=("s1",),
            metrics=("rmse",),
            source_relative_paths=("/abs/path/statistics/descriptive_consolidation.json",),
            created_at_utc="2026-11-16T00:00:00Z",
        )
