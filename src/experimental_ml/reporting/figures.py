"""Deterministic pure-Python/NumPy figure builders and SVG/PNG/PDF renderers (REP-04, XCUT-02)."""

from __future__ import annotations

import math
import struct
from xml.sax.saxutils import escape as xml_escape
import zlib

import numpy as np

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.reporting.loader import select_report_content
from experimental_ml.reporting.types import (
    ArtifactProvenance,
    LoadedExperimentData,
    PlotSeries,
    PlotSpecification,
    PlotType,
    ReportContentSelection,
    ReportFamily,
)


_DPI_300_PX_PER_METER = 11811  # round(300 / 0.0254)


def _make_fig_provenance(
    plot_id: str,
    family: ReportFamily,
    loaded: LoadedExperimentData,
    sel: ReportContentSelection,
    rel_paths: tuple[str, ...],
) -> ArtifactProvenance:
    return ArtifactProvenance(
        artifact_id=plot_id,
        artifact_type="figure",
        family=family,
        experiment_id=loaded.experiment_id,
        partition_plan_id=loaded.partition_plan_id,
        model_ids=sel.model_ids,
        scenario_ids=sel.scenario_ids,
        metrics=sel.metric_ids,
        source_relative_paths=rel_paths,
        created_at_utc=loaded.statistics.consolidation.timestamp_utc,
    )


def build_figure_spec(
    family: ReportFamily,
    loaded_data: LoadedExperimentData,
    selection: ReportContentSelection | None = None,
    metric_name: str | None = None,
) -> PlotSpecification:
    """Build an immutable PlotSpecification from LoadedExperimentData (CA-E6-01, REP-04)."""
    if not isinstance(family, ReportFamily):
        family = ReportFamily(family)
    sel = select_report_content(loaded_data, selection)
    target_metric = metric_name or (sel.metric_ids[0] if sel.metric_ids else "metric")

    notes: list[str] = []

    if family == ReportFamily.D_PREDICTIVE_PERFORMANCE:
        x_vals: list[str] = []
        y_vals: list[float] = []
        y_errs: list[float] = []
        for (m_id, sc_id), summary in sorted(loaded_data.statistics.consolidation.configurations.items()):
            if (sel.model_ids and m_id not in sel.model_ids) or (sel.scenario_ids and sc_id not in sel.scenario_ids):
                continue
            agg = summary.aggregated_metrics.get(target_metric)
            if agg is None or agg.status == MetricStatus.UNDEFINED_NAN or agg.mean is None or not math.isfinite(agg.mean):
                notes.append(f"Excluded {m_id}/{sc_id} from '{target_metric}' plot due to UNDEFINED_NAN or missing value.")
                continue
            x_vals.append(f"{m_id}/{sc_id}")
            y_vals.append(float(agg.mean))
            y_errs.append(float(agg.std) if agg.std is not None and math.isfinite(agg.std) else 0.0)
        series = (PlotSeries(name=target_metric, x_values=tuple(x_vals), y_values=tuple(y_vals), y_err=tuple(y_errs)),)
        prov = _make_fig_provenance("fig_family_d", family, loaded_data, sel, ("statistics/descriptive_consolidation.json",))
        return PlotSpecification(
            plot_id="fig_family_d",
            family=family,
            plot_type=PlotType.BAR_COMPARISON,
            title=f"Predictive Performance ({target_metric})",
            x_label="Configuration",
            y_label=target_metric,
            series=series,
            notes=tuple(notes),
            provenance=prov,
        )

    if family == ReportFamily.E_STATISTICAL_COMPARISONS:
        x_vals = []
        y_vals = []
        y_errs = []
        for cmp_res in loaded_data.statistics.comparisons.comparisons:
            if cmp_res.metric_name != target_metric:
                continue
            diff = cmp_res.observed_difference
            ci_lo, ci_hi = cmp_res.nadeau_bengio.confidence_interval
            if not (math.isfinite(diff) and math.isfinite(ci_lo) and math.isfinite(ci_hi)):
                notes.append(f"Excluded comparison {cmp_res.comparison_id} due to non-finite difference/CI.")
                continue
            x_vals.append(f"{cmp_res.config_a[0]} vs {cmp_res.config_b[0]}")
            y_vals.append(float(diff))
            y_errs.append(0.5 * abs(float(ci_hi) - float(ci_lo)))
        series = (PlotSeries(name=f"{target_metric} diff", x_values=tuple(x_vals), y_values=tuple(y_vals), y_err=tuple(y_errs)),)
        prov = _make_fig_provenance("fig_family_e", family, loaded_data, sel, ("statistics/statistical_comparisons.json",))
        return PlotSpecification(
            plot_id="fig_family_e",
            family=family,
            plot_type=PlotType.PAIRED_DIFF_CI,
            title=f"Paired Differences & 95% CI ({target_metric})",
            x_label="Comparison",
            y_label=f"Delta ({target_metric})",
            series=series,
            notes=tuple(notes),
            provenance=prov,
        )

    if family == ReportFamily.F_STABILITY_COST_PARETO:
        pareto_x: list[float] = []
        pareto_y: list[float] = []
        dom_x: list[float] = []
        dom_y: list[float] = []
        pareto = loaded_data.statistics.pareto
        if pareto is not None and len(pareto.objectives) >= 2:
            o1, o2 = pareto.objectives[0].name, pareto.objectives[1].name
            for pt in pareto.pareto_frontier:
                pareto_x.append(float(pt.objective_values[o1]))
                pareto_y.append(float(pt.objective_values[o2]))
            for pt in pareto.dominated_configurations:
                dom_x.append(float(pt.objective_values[o1]))
                dom_y.append(float(pt.objective_values[o2]))
            x_lbl, y_lbl = o1, o2
        else:
            x_lbl, y_lbl = "Configuration", target_metric
            for (m_id, sc_id), summary in sorted(loaded_data.statistics.consolidation.configurations.items()):
                agg = summary.aggregated_metrics.get(target_metric)
                if agg is not None and agg.mean is not None and math.isfinite(agg.mean):
                    pareto_x.append(float(len(pareto_x) + 1))
                    pareto_y.append(float(agg.mean))
        series_list = [PlotSeries("Pareto Frontier", tuple(pareto_x), tuple(pareto_y))]
        if dom_x:
            series_list.append(PlotSeries("Dominated", tuple(dom_x), tuple(dom_y)))
        prov = _make_fig_provenance("fig_family_f", family, loaded_data, sel, ("statistics/pareto_summary.json",))
        return PlotSpecification(
            plot_id="fig_family_f",
            family=family,
            plot_type=PlotType.PARETO_TRADEOFF,
            title="Multi-Objective Pareto Trade-off",
            x_label=x_lbl,
            y_label=y_lbl,
            series=tuple(series_list),
            notes=tuple(notes),
            provenance=prov,
        )

    # Generic summary PlotSpecification for Families A, B, C, G
    prov = _make_fig_provenance(f"fig_{family.value.lower()}", family, loaded_data, sel, ("statistics/statistics_manifest.json",))
    return PlotSpecification(
        plot_id=f"fig_{family.value.lower()}",
        family=family,
        plot_type=PlotType.BAR_COMPARISON,
        title=f"Summary ({family.value})",
        x_label="Item",
        y_label="Value",
        series=(PlotSeries("Summary", ("total_configs",), (float(loaded_data.statistics.consolidation.total_configurations),)),),
        notes=tuple(notes),
        provenance=prov,
    )


def _compute_y_bounds(spec: PlotSpecification) -> tuple[float, float]:
    vals: list[float] = []
    for s in spec.series:
        for idx, y in enumerate(s.y_values):
            if math.isfinite(y):
                err = s.y_err[idx] if (s.y_err is not None and idx < len(s.y_err) and math.isfinite(s.y_err[idx])) else 0.0
                vals.append(y - err)
                vals.append(y + err)
    if not vals:
        return 0.0, 1.0
    ymin, ymax = min(vals), max(vals)
    if ymin > 0.0 and spec.plot_type == PlotType.BAR_COMPARISON:
        ymin = 0.0
    if ymax == ymin:
        ymax = ymin + 1.0
    pad = 0.1 * (ymax - ymin)
    return ymin - (pad if ymin != 0.0 else 0.0), ymax + pad


def _render_svg(spec: PlotSpecification) -> bytes:
    w, h = 800, 500
    ml, mr, mt, mb = 80, 40, 60, 80
    pw, ph = w - ml - mr, h - mt - mb
    ymin, ymax = _compute_y_bounds(spec)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'  <rect width="{w}" height="{h}" fill="#ffffff"/>',
        f'  <text x="{w // 2}" y="34" text-anchor="middle" font-family="sans-serif" font-size="16" font-weight="bold" fill="#1f2937">{xml_escape(spec.title)}</text>',
        f'  <line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt + ph}" stroke="#374151" stroke-width="1.5"/>',
        f'  <line x1="{ml}" y1="{mt + ph}" x2="{ml + pw}" y2="{mt + ph}" stroke="#374151" stroke-width="1.5"/>',
        f'  <text x="{ml + pw // 2}" y="{h - 20}" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#374151">{xml_escape(spec.x_label)}</text>',
        f'  <text x="22" y="{mt + ph // 2}" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#374151" transform="rotate(-90 22 {mt + ph // 2})">{xml_escape(spec.y_label)}</text>',
    ]

    def _y_px(val: float) -> float:
        return mt + ph - ((val - ymin) / (ymax - ymin)) * ph

    palette = ("#2563eb", "#dc2626", "#16a34a", "#d97706")
    for s_idx, s in enumerate(spec.series):
        color = palette[s_idx % len(palette)]
        n = len(s.y_values)
        if n == 0:
            continue
        step = pw / max(1, n)
        for i, y in enumerate(s.y_values):
            cx = ml + (i + 0.5) * step
            cy = _y_px(y)
            if spec.plot_type == PlotType.BAR_COMPARISON:
                bar_w = max(8.0, min(60.0, step * 0.55))
                y0 = _y_px(max(ymin, 0.0))
                top = min(cy, y0)
                bh = max(1.0, abs(y0 - cy))
                lines.append(
                    f'  <rect x="{cx - bar_w / 2:.1f}" y="{top:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" fill="{color}" opacity="0.85"/>'
                )
            else:
                lines.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{color}"/>')

            if s.y_err is not None and i < len(s.y_err) and s.y_err[i] > 0.0:
                y_hi = _y_px(y + s.y_err[i])
                y_lo = _y_px(y - s.y_err[i])
                lines.append(f'  <line x1="{cx:.1f}" y1="{y_hi:.1f}" x2="{cx:.1f}" y2="{y_lo:.1f}" stroke="#111827" stroke-width="1.5"/>')

            if s_idx == 0 and i < len(s.x_values):
                lbl = xml_escape(str(s.x_values[i]))
                lines.append(
                    f'  <text x="{cx:.1f}" y="{mt + ph + 20}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#4b5563">{lbl}</text>'
                )

    lines.append("</svg>\n")
    return "\n".join(lines).encode("utf-8")


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def _render_png_300dpi(spec: PlotSpecification) -> bytes:
    w, h = 800, 500
    ml, mr, mt, mb = 80, 40, 60, 80
    pw, ph = w - ml - mr, h - mt - mb
    ymin, ymax = _compute_y_bounds(spec)

    img = np.full((h, w, 3), 255, dtype=np.uint8)
    # Draw axes (dark gray)
    img[mt : mt + ph + 1, ml : ml + 2] = (55, 65, 81)
    img[mt + ph : mt + ph + 2, ml : ml + pw + 1] = (55, 65, 81)

    def _y_px(val: float) -> int:
        y = int(round(mt + ph - ((val - ymin) / (ymax - ymin)) * ph))
        return max(mt, min(mt + ph, y))

    colors = ((37, 99, 235), (220, 38, 38), (22, 163, 74))
    for s_idx, s in enumerate(spec.series):
        col = colors[s_idx % len(colors)]
        n = len(s.y_values)
        if n == 0:
            continue
        step = pw / max(1, n)
        for i, y in enumerate(s.y_values):
            cx = int(round(ml + (i + 0.5) * step))
            cy = _y_px(y)
            if spec.plot_type == PlotType.BAR_COMPARISON:
                half_w = int(max(4, min(28, step * 0.25)))
                y0 = _y_px(max(ymin, 0.0))
                top, bot = min(cy, y0), max(cy, y0)
                img[top : bot + 1, max(ml, cx - half_w) : min(ml + pw, cx + half_w)] = col
            else:
                img[max(0, cy - 4) : min(h, cy + 5), max(0, cx - 4) : min(w, cx + 5)] = col

            if s.y_err is not None and i < len(s.y_err) and s.y_err[i] > 0.0:
                y_hi = _y_px(y + s.y_err[i])
                y_lo = _y_px(y - s.y_err[i])
                img[min(y_hi, y_lo) : max(y_hi, y_lo) + 1, cx : cx + 2] = (17, 24, 39)

    raw_rows = b"".join(b"\x00" + img[row].tobytes() for row in range(h))
    compressed = zlib.compress(raw_rows, level=9)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    phys = struct.pack(">IIB", _DPI_300_PX_PER_METER, _DPI_300_PX_PER_METER, 1)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"pHYs", phys)
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )


def _render_pdf(spec: PlotSpecification) -> bytes:
    w, h = 800, 500
    ml, mr, mt, mb = 80, 40, 60, 80
    pw, ph = w - ml - mr, h - mt - mb
    ymin, ymax = _compute_y_bounds(spec)

    def _y_pt(val: float) -> float:
        return mb + ((val - ymin) / (ymax - ymin)) * ph

    safe_title = spec.title.replace("(", "[").replace(")", "]").replace("\\", "/")
    cmds = [
        "0.2 0.25 0.32 RG 1.5 w",
        f"{ml} {mb} m {ml} {mb + ph} l S",
        f"{ml} {mb} m {ml + pw} {mb} l S",
        f"BT /F1 14 Tf {ml} {h - 36} Td ({safe_title}) Tj ET",
    ]
    for s in spec.series:
        n = len(s.y_values)
        if n == 0:
            continue
        step = pw / max(1, n)
        cmds.append("0.15 0.39 0.92 rg")
        for i, y in enumerate(s.y_values):
            cx = ml + (i + 0.5) * step
            cy = _y_pt(y)
            y0 = _y_pt(max(ymin, 0.0))
            bar_w = max(8.0, min(50.0, step * 0.5))
            cmds.append(f"{cx - bar_w / 2:.2f} {min(y0, cy):.2f} {bar_w:.2f} {max(1.0, abs(cy - y0)):.2f} re f")

    stream_bytes = "\n".join(cmds).encode("latin-1", errors="replace")
    objs = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n".encode("ascii"),
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        f"5 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii") + stream_bytes + b"\nendstream\nendobj\n",
    ]

    buf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for obj in objs:
        offsets.append(len(buf))
        buf.extend(obj)

    xref_pos = len(buf)
    buf.extend(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for off in offsets:
        buf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    buf.extend(
        f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )
    return bytes(buf)


def render_figure(plot_spec: PlotSpecification, fmt: str = "svg") -> bytes:
    """Render PlotSpecification deterministically to 'svg', 'png' (300 DPI), or 'pdf' (REP-04, XCUT-02)."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm == "svg":
        return _render_svg(plot_spec)
    if fmt_norm == "png":
        return _render_png_300dpi(plot_spec)
    if fmt_norm == "pdf":
        return _render_pdf(plot_spec)
    raise ConfigurationError(f"Unsupported figure format '{fmt}'; expected 'svg', 'png', or 'pdf'.")
