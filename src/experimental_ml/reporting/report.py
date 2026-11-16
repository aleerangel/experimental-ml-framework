"""Full scientific report composer in Markdown and self-contained HTML (REP-05, RNF03, CA-E6-01, CA-E6-02)."""

from __future__ import annotations

import html
from typing import Sequence

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.reporting.loader import select_report_content
from experimental_ml.reporting.tables import (
    _format_cell_value,
    build_table_model,
    render_table_markdown,
)
from experimental_ml.reporting.types import (
    LoadedExperimentData,
    ReportContentSelection,
    ResearcherDeclarations,
    TableModel,
)


_EMBEDDED_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1.25rem; color: #1f2937; line-height: 1.6; }
h1, h2, h3 { color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3rem; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0 1.5rem 0; font-size: 0.92rem; }
th, td { border: 1px solid #d1d5db; padding: 0.45rem 0.65rem; }
th { background: #f3f4f6; font-weight: 600; }
.box { background: #f9fafb; border-left: 4px solid #2563eb; padding: 0.8rem 1rem; margin: 1rem 0; }
.caveat { background: #fffbeb; border-left: 4px solid #d97706; padding: 0.8rem 1rem; margin: 1rem 0; }
""".strip()


def _render_html_table(table: TableModel) -> str:
    parts = [f"<h3>{html.escape(table.title)}</h3>", "<table>", "<thead><tr>"]
    for col in table.columns:
        parts.append(f"<th>{html.escape(col.header)}</th>")
    parts.append("</tr></thead><tbody>")
    for row in table.rows:
        parts.append("<tr>")
        for col in table.columns:
            txt = _format_cell_value(row.get(col.key), col.numeric_format, full_precision=False)
            parts.append(f"<td>{html.escape(txt)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


def render_full_report(
    loaded_data: LoadedExperimentData,
    fmt: str = "markdown",
    selection: ReportContentSelection | None = None,
    declarations: ResearcherDeclarations | None = None,
    figure_paths: Sequence[str] = (),
) -> str:
    """Render complete scientific report into 'markdown' or self-contained 'html' (REP-05, RNF03)."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm not in ("markdown", "html"):
        raise ConfigurationError(f"Unsupported report format '{fmt}'; expected 'markdown' or 'html'.")

    sel = select_report_content(loaded_data, selection)
    tables = tuple(build_table_model(fam, loaded_data, sel) for fam in sel.families)
    conc = loaded_data.statistics.conclusion
    suit = loaded_data.statistics.suitability

    if fmt_norm == "markdown":
        lines: list[str] = [
            f"# Scientific Experiment Report — {loaded_data.experiment_id}",
            "",
            f"- **Experiment ID:** `{loaded_data.experiment_id}`",
            f"- **Partition Plan ID:** `{loaded_data.partition_plan_id}`",
            f"- **Evaluation Regime:** `{suit.evaluation_regime.value}` ($J = {suit.total_development_partitions}$)",
            "",
            "## 1. Researcher Declarations (Declared Provenance)",
            "",
        ]
        if declarations is None:
            lines.append("_No explicit researcher declarations provided._")
        else:
            if declarations.scientific_objective:
                lines.append(f"- **Scientific Objective:** {declarations.scientific_objective}")
            if declarations.data_origin_note:
                lines.append(f"- **Data Origin:** {declarations.data_origin_note}")
            if declarations.metric_rationale:
                lines.append(f"- **Metric Rationale:** {declarations.metric_rationale}")
            for note in declarations.additional_notes:
                lines.append(f"- **Note:** {note}")

        lines.extend(["", "## 2. Registered Computational Facts", ""])
        for tbl in tables:
            lines.append(render_table_markdown(tbl))
        if figure_paths:
            lines.append("### Figures")
            lines.append("")
            for fp in figure_paths:
                lines.append(f"- `{fp}`")
            lines.append("")

        lines.extend([
            "## 3. Derived and Conditioned Interpretations",
            "",
            f"- **Primary Metric:** `{conc.primary_metric}`",
            f"- **Observed Leader:** `{conc.observed_leader}`",
            f"- **Statistical Evidence:** {conc.statistical_evidence_status}",
            f"- **Effect Magnitude:** {conc.effect_magnitude_summary}",
            f"- **Practical Relevance:** {conc.practical_relevance_status}",
            f"- **Cost & Pareto Trade-off:** {conc.cost_tradeoff_summary}",
            "",
            "### Narrative Synthesis",
            "",
            conc.narrative_text,
            "",
        ])
        if conc.methodological_caveats:
            lines.append("### Methodological Caveats")
            lines.append("")
            for cav in conc.methodological_caveats:
                lines.append(f"- {cav}")
            lines.append("")

        return "\n".join(lines)

    # Self-contained offline HTML
    parts = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "<meta charset=\"utf-8\">",
        f"<title>Scientific Report — {html.escape(loaded_data.experiment_id)}</title>",
        f"<style>{_EMBEDDED_CSS}</style>",
        "</head>",
        "<body>",
        f"<h1>Scientific Experiment Report — {html.escape(loaded_data.experiment_id)}</h1>",
        f"<p><strong>Partition Plan:</strong> <code>{html.escape(loaded_data.partition_plan_id)}</code> | "
        f"<strong>Regime:</strong> <code>{html.escape(suit.evaluation_regime.value)}</code> (J = {suit.total_development_partitions})</p>",
        "<h2>1. Researcher Declarations (Declared Provenance)</h2>",
        "<div class=\"box\">",
    ]
    if declarations is None:
        parts.append("<p><em>No explicit researcher declarations provided.</em></p>")
    else:
        if declarations.scientific_objective:
            parts.append(f"<p><strong>Scientific Objective:</strong> {html.escape(declarations.scientific_objective)}</p>")
        if declarations.data_origin_note:
            parts.append(f"<p><strong>Data Origin:</strong> {html.escape(declarations.data_origin_note)}</p>")
        if declarations.metric_rationale:
            parts.append(f"<p><strong>Metric Rationale:</strong> {html.escape(declarations.metric_rationale)}</p>")
        for note in declarations.additional_notes:
            parts.append(f"<p><strong>Note:</strong> {html.escape(note)}</p>")
    parts.append("</div>")

    parts.append("<h2>2. Registered Computational Facts</h2>")
    for tbl in tables:
        parts.append(_render_html_table(tbl))
    if figure_paths:
        parts.append("<h3>Figures</h3><ul>")
        for fp in figure_paths:
            parts.append(f"<li><code>{html.escape(fp)}</code></li>")
        parts.append("</ul>")

    parts.extend([
        "<h2>3. Derived and Conditioned Interpretations</h2>",
        f"<p><strong>Primary Metric:</strong> <code>{html.escape(conc.primary_metric)}</code></p>",
        f"<p><strong>Observed Leader:</strong> <code>{html.escape(str(conc.observed_leader))}</code></p>",
        f"<p><strong>Statistical Evidence:</strong> {html.escape(conc.statistical_evidence_status)}</p>",
        f"<p><strong>Effect Magnitude:</strong> {html.escape(conc.effect_magnitude_summary)}</p>",
        f"<p><strong>Practical Relevance:</strong> {html.escape(conc.practical_relevance_status)}</p>",
        f"<p><strong>Cost &amp; Pareto Trade-off:</strong> {html.escape(conc.cost_tradeoff_summary)}</p>",
        f"<div class=\"box\"><p>{html.escape(conc.narrative_text)}</p></div>",
    ])
    if conc.methodological_caveats:
        parts.append("<div class=\"caveat\"><strong>Methodological Caveats:</strong><ul>")
        for cav in conc.methodological_caveats:
            parts.append(f"<li>{html.escape(cav)}</li>")
        parts.append("</ul></div>")

    parts.extend(["</body>", "</html>"])
    return "\n".join(parts) + "\n"
