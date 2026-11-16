"""Scientific table builders (Families A-G) and pure CSV/Markdown/LaTeX renderers (REP-03)."""

from __future__ import annotations

import csv
import io
import math
from typing import Any

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.reporting.loader import select_report_content
from experimental_ml.reporting.types import (
    ArtifactProvenance,
    ColumnAlignment,
    LoadedExperimentData,
    ReportContentSelection,
    ReportFamily,
    TableColumn,
    TableModel,
)


def _is_technical_hash_field(field_name: str) -> bool:
    lower = field_name.lower()
    return lower.endswith(("_hash", "_digest")) or lower in ("sha256", "checksum", "checksums")


def _sanitize_row_dict(raw: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in raw.items() if not _is_technical_hash_field(k)}


def _format_cell_value(val: Any, numeric_format: str | None = None, *, full_precision: bool = False) -> str:
    if val is None:
        return "N/A"
    if isinstance(val, bool):
        return str(val)
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        if math.isnan(val):
            return "UNDEFINED_NAN"
        if math.isinf(val):
            return "Inf" if val > 0 else "-Inf"
        if full_precision or numeric_format is None:
            return repr(val)
        return numeric_format.format(val)
    return str(val)


def _escape_latex(text: str) -> str:
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
    ]
    out = text
    for old, new in replacements:
        out = out.replace(old, new)
    return out


def _make_provenance(
    artifact_id: str,
    family: ReportFamily,
    loaded: LoadedExperimentData,
    sel: ReportContentSelection,
    rel_paths: tuple[str, ...],
) -> ArtifactProvenance:
    return ArtifactProvenance(
        artifact_id=artifact_id,
        artifact_type="table",
        family=family,
        experiment_id=loaded.experiment_id,
        partition_plan_id=loaded.partition_plan_id,
        model_ids=sel.model_ids,
        scenario_ids=sel.scenario_ids,
        metrics=sel.metric_ids,
        source_relative_paths=rel_paths,
        created_at_utc=loaded.statistics.consolidation.timestamp_utc,
    )


def build_table_model(
    family: ReportFamily,
    loaded_data: LoadedExperimentData,
    selection: ReportContentSelection | None = None,
) -> TableModel:
    """Build an immutable TableModel for any of the 7 canonical families A-G (REP-03, CA-E6-01, CA-E6-02)."""
    if not isinstance(family, ReportFamily):
        family = ReportFamily(family)
    sel = select_report_content(loaded_data, selection)

    if family == ReportFamily.A_DATA_CHARACTERIZATION:
        cols = (
            TableColumn("attribute", "Attribute", ColumnAlignment.LEFT),
            TableColumn("value", "Value", ColumnAlignment.RIGHT),
        )
        rows: list[dict[str, Any]] = []
        if loaded_data.dataset_profile:
            for k in sorted(loaded_data.dataset_profile.keys()):
                if not _is_technical_hash_field(k):
                    v = loaded_data.dataset_profile[k]
                    if isinstance(v, (str, int, float, bool)) or v is None:
                        rows.append({"attribute": k, "value": v})
        prov = _make_provenance("tbl_family_a", family, loaded_data, sel, ("data/dataset_profile.json",))
        return TableModel("tbl_family_a", family, "Data Characterization", "Dataset structural summary", cols, tuple(rows), (), prov)

    if family == ReportFamily.B_FEATURE_SCENARIOS:
        cols = (
            TableColumn("scenario_id", "Scenario", ColumnAlignment.LEFT),
            TableColumn("mode", "Selection Mode", ColumnAlignment.LEFT),
            TableColumn("n_features", "Features", ColumnAlignment.RIGHT),
        )
        rows = []
        if loaded_data.scenarios_catalog:
            for sc in loaded_data.scenarios_catalog.get("scenarios", ()):
                sc_id = str(sc.get("scenario_id", ""))
                if not sel.scenario_ids or sc_id in sel.scenario_ids:
                    feats = sc.get("selected_features", sc.get("features", sc.get("candidate_features", ())))
                    rows.append(_sanitize_row_dict({"scenario_id": sc_id, "mode": sc.get("mode", "N/A"), "n_features": len(feats)}))
        prov = _make_provenance("tbl_family_b", family, loaded_data, sel, ("configuration/scenarios.json",))
        return TableModel("tbl_family_b", family, "Feature Scenarios", "Declared feature scenarios", cols, tuple(rows), (), prov)

    if family == ReportFamily.C_MODELS_CONFIG:
        cols = (
            TableColumn("model_id", "Model ID", ColumnAlignment.LEFT),
            TableColumn("family", "Model Family", ColumnAlignment.LEFT),
            TableColumn("task_type", "Task Type", ColumnAlignment.LEFT),
        )
        rows = []
        if loaded_data.models_catalog:
            for m in loaded_data.models_catalog.get("models", ()):
                m_id = str(m.get("model_id", ""))
                if not sel.model_ids or m_id in sel.model_ids:
                    rows.append(_sanitize_row_dict({"model_id": m_id, "family": m.get("family", "N/A"), "task_type": m.get("task_type", "N/A")}))
        prov = _make_provenance("tbl_family_c", family, loaded_data, sel, ("configuration/models.json",))
        return TableModel("tbl_family_c", family, "Models Configuration", "Registered models catalog", cols, tuple(rows), (), prov)

    if family == ReportFamily.D_PREDICTIVE_PERFORMANCE:
        cols = (
            TableColumn("model_id", "Model", ColumnAlignment.LEFT),
            TableColumn("scenario_id", "Scenario", ColumnAlignment.LEFT),
            TableColumn("metric", "Metric", ColumnAlignment.LEFT),
            TableColumn("status", "Status", ColumnAlignment.CENTER),
            TableColumn("mean", "Mean", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("std", "SD", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("median", "Median", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("iqr", "IQR", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("coverage", "Coverage", ColumnAlignment.RIGHT, "{:.2%}"),
        )
        rows = []
        consol = loaded_data.statistics.consolidation
        for (m_id, sc_id), summary in sorted(consol.configurations.items()):
            if (sel.model_ids and m_id not in sel.model_ids) or (sel.scenario_ids and sc_id not in sel.scenario_ids):
                continue
            for met_name, agg in sorted(summary.aggregated_metrics.items()):
                if sel.metric_ids and met_name not in sel.metric_ids:
                    continue
                mean_val = float("nan") if agg.status == MetricStatus.UNDEFINED_NAN else agg.mean
                rows.append({
                    "model_id": m_id,
                    "scenario_id": sc_id,
                    "metric": met_name,
                    "status": agg.status.value,
                    "mean": mean_val,
                    "std": agg.std,
                    "median": agg.median,
                    "iqr": agg.iqr,
                    "coverage": summary.coverage,
                })
        prov = _make_provenance("tbl_family_d", family, loaded_data, sel, ("statistics/descriptive_consolidation.json",))
        return TableModel("tbl_family_d", family, "Predictive Performance", "Cross-validation descriptive performance", cols, tuple(rows), (), prov)

    if family == ReportFamily.E_STATISTICAL_COMPARISONS:
        cols = (
            TableColumn("config_a", "Config A", ColumnAlignment.LEFT),
            TableColumn("config_b", "Config B", ColumnAlignment.LEFT),
            TableColumn("metric", "Metric", ColumnAlignment.LEFT),
            TableColumn("observed_difference", "Diff", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("t_statistic", "t (NB)", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("nadeau_bengio_adjusted_p", "p_adj (NB)", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("wilcoxon_adjusted_p", "p_adj (WX)", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("cohens_d", "Cohen d_z", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("practical_relevance", "Practical Relevance", ColumnAlignment.LEFT),
        )
        rows = []
        for cmp_res in loaded_data.statistics.comparisons.comparisons:
            if sel.metric_ids and cmp_res.metric_name not in sel.metric_ids:
                continue
            rows.append({
                "config_a": f"{cmp_res.config_a[0]}/{cmp_res.config_a[1]}",
                "config_b": f"{cmp_res.config_b[0]}/{cmp_res.config_b[1]}",
                "metric": cmp_res.metric_name,
                "observed_difference": cmp_res.observed_difference,
                "t_statistic": cmp_res.nadeau_bengio.t_statistic,
                "nadeau_bengio_adjusted_p": cmp_res.nadeau_bengio_adjusted_p,
                "wilcoxon_adjusted_p": cmp_res.wilcoxon_adjusted_p,
                "cohens_d": cmp_res.effect_size.cohens_d,
                "practical_relevance": cmp_res.practical_relevance.value,
            })
        prov = _make_provenance("tbl_family_e", family, loaded_data, sel, ("statistics/statistical_comparisons.json",))
        return TableModel("tbl_family_e", family, "Statistical Comparisons", "Paired comparisons and multiplicity adjustments", cols, tuple(rows), (), prov)

    if family == ReportFamily.F_STABILITY_COST_PARETO:
        cols = (
            TableColumn("model_id", "Model", ColumnAlignment.LEFT),
            TableColumn("scenario_id", "Scenario", ColumnAlignment.LEFT),
            TableColumn("fit_mean_s", "Fit Time (s)", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("total_cell_mean_s", "Total Time (s)", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("mean_jaccard", "Stability (Jaccard)", ColumnAlignment.RIGHT, "{:.4f}"),
            TableColumn("pareto_optimal", "Pareto Optimal", ColumnAlignment.CENTER),
        )
        pareto_ids = (
            {pt.config_id for pt in loaded_data.statistics.pareto.pareto_frontier}
            if loaded_data.statistics.pareto is not None
            else set()
        )
        rows = []
        for (m_id, sc_id), summary in sorted(loaded_data.statistics.consolidation.configurations.items()):
            if (sel.model_ids and m_id not in sel.model_ids) or (sel.scenario_ids and sc_id not in sel.scenario_ids):
                continue
            fit_t = summary.aggregated_timing.fit_mean_s if summary.aggregated_timing else None
            tot_t = summary.aggregated_timing.total_cell_mean_s if summary.aggregated_timing else None
            stab = summary.feature_stability.mean_jaccard if summary.feature_stability else None
            rows.append({
                "model_id": m_id,
                "scenario_id": sc_id,
                "fit_mean_s": fit_t,
                "total_cell_mean_s": tot_t,
                "mean_jaccard": stab,
                "pareto_optimal": (m_id, sc_id) in pareto_ids if loaded_data.statistics.pareto is not None else None,
            })
        rel_paths = ("statistics/descriptive_consolidation.json", "statistics/pareto_summary.json") if loaded_data.statistics.pareto else ("statistics/descriptive_consolidation.json",)
        prov = _make_provenance("tbl_family_f", family, loaded_data, sel, rel_paths)
        return TableModel("tbl_family_f", family, "Stability, Cost & Pareto", "Computational cost, feature stability, and Pareto optimality", cols, tuple(rows), (), prov)

    if family == ReportFamily.G_MODEL_SPECIFIC_ARTIFACTS:
        cols = (
            TableColumn("model_id", "Model", ColumnAlignment.LEFT),
            TableColumn("artifact_key", "Artifact", ColumnAlignment.LEFT),
            TableColumn("summary", "Summary", ColumnAlignment.LEFT),
        )
        rows = []
        if loaded_data.models_catalog:
            for m in loaded_data.models_catalog.get("models", ()):
                m_id = str(m.get("model_id", ""))
                if sel.model_ids and m_id not in sel.model_ids:
                    continue
                for k in sorted(m.get("diagnostics", {}).keys()):
                    if not _is_technical_hash_field(k):
                        rows.append({"model_id": m_id, "artifact_key": k, "summary": str(m["diagnostics"][k])})
        prov = _make_provenance("tbl_family_g", family, loaded_data, sel, ("configuration/models.json",))
        notes = ("No model-specific adapter diagnostics exported.",) if not rows else ()
        return TableModel("tbl_family_g", family, "Model-Specific Artifacts", "Adapter-specific model diagnostics", cols, tuple(rows), notes, prov)

    raise ConfigurationError(f"Unsupported ReportFamily: {family}")


def render_table_csv(table: TableModel) -> str:
    """Render TableModel as deterministic RFC 4180 CSV preserving full numeric precision."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow([col.header for col in table.columns])
    for row in table.rows:
        writer.writerow([
            _format_cell_value(row.get(col.key), full_precision=True)
            for col in table.columns
        ])
    return buf.getvalue()


def render_table_markdown(table: TableModel) -> str:
    """Render TableModel as aligned GitHub-Flavored Markdown table."""
    lines: list[str] = [f"### {table.title}", ""]
    headers = [col.header for col in table.columns]
    lines.append("| " + " | ".join(headers) + " |")

    align_tokens = []
    for col in table.columns:
        if col.align == ColumnAlignment.RIGHT:
            align_tokens.append("---:")
        elif col.align == ColumnAlignment.CENTER:
            align_tokens.append(":---:")
        else:
            align_tokens.append(":---")
    lines.append("| " + " | ".join(align_tokens) + " |")

    for row in table.rows:
        cells = [
            _format_cell_value(row.get(col.key), col.numeric_format, full_precision=False)
            for col in table.columns
        ]
        lines.append("| " + " | ".join(cells) + " |")

    if table.notes:
        lines.append("")
        for note in table.notes:
            lines.append(f"> Note: {note}")
    return "\n".join(lines) + "\n"


def render_table_latex(table: TableModel) -> str:
    """Render TableModel as LaTeX booktabs table with escaped special characters."""
    col_spec = "".join(
        "r" if c.align == ColumnAlignment.RIGHT else ("c" if c.align == ColumnAlignment.CENTER else "l")
        for c in table.columns
    )
    lines = [
        "\\begin{table}[htbp]",
        "\\centering",
        f"\\caption{{{_escape_latex(table.caption)}}}",
        f"\\begin{{tabular}}{{{col_spec}}}",
        "\\toprule",
        " & ".join(_escape_latex(col.header) for col in table.columns) + " \\\\",
        "\\midrule",
    ]
    for row in table.rows:
        cells = [
            _escape_latex(_format_cell_value(row.get(col.key), col.numeric_format, full_precision=False))
            for col in table.columns
        ]
        lines.append(" & ".join(cells) + " \\\\")
    lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ])
    return "\n".join(lines) + "\n"
