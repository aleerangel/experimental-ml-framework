"""Stage 2 exploratory feature visualization: Markdown/HTML reports and pure-NumPy SVG/PNG charts.

Complies with EXPL-01..EXPL-05, CA-E2-01, XCUT-02 (pure Python stdlib + numpy), and CLI-11.
"""

from __future__ import annotations

import html
import math
import struct
from typing import Sequence
from xml.sax.saxutils import escape as xml_escape
import zlib

import numpy as np

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.features.types import AssociationMeasure, ExploratoryFeatureReport


_DPI_300_PX_PER_METER = 11811  # round(300 / 0.0254)

_HTML_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1040px; margin: 2rem auto; padding: 0 1.25rem; color: #1f2937; line-height: 1.6; }
h1, h2, h3 { color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3rem; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0 1.5rem 0; font-size: 0.92rem; }
th, td { border: 1px solid #d1d5db; padding: 0.45rem 0.65rem; text-align: left; }
th { background: #f3f4f6; font-weight: 600; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.matrix-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 6px; margin: 0.75rem 0 1.5rem 0; }
table.matrix-table { width: max-content; min-width: 100%; margin: 0; font-size: 0.82rem; border: none; }
table.matrix-table th, table.matrix-table td { padding: 0.4rem 0.55rem; white-space: nowrap; }
table.matrix-table th.col-hdr { text-align: center; min-width: 3.6rem; font-size: 0.78rem; }
table.matrix-table th.row-hdr, table.matrix-table td.row-hdr { position: sticky; left: 0; background: #f9fafb; z-index: 1; font-weight: 600; border-right: 2px solid #d1d5db; }
table.matrix-table td.matrix-cell { text-align: center; font-variant-numeric: tabular-nums; min-width: 3.6rem; }
table.matrix-table td.matrix-diag { background: #f1f5f9; color: #64748b; font-weight: 600; }
.legend { display: flex; align-items: center; gap: 0.75rem; font-size: 0.84rem; color: #4b5563; margin: 0.5rem 0; flex-wrap: wrap; }
.legend-swatch { display: inline-block; width: 14px; height: 14px; border-radius: 3px; vertical-align: middle; margin-right: 4px; border: 1px solid #d1d5db; }
.warning-box { background: #fffbeb; border-left: 4px solid #d97706; padding: 0.85rem 1.1rem; margin: 1rem 0; }
.guide-box { background: #eff6ff; border-left: 4px solid #2563eb; padding: 0.85rem 1.1rem; margin: 1rem 0; }
.badge-forte { background: #dcfce7; color: #166534; padding: 0.12rem 0.45rem; border-radius: 4px; font-weight: 600; font-size: 0.82rem; }
.badge-mod { background: #fef9c3; color: #854d0e; padding: 0.12rem 0.45rem; border-radius: 4px; font-weight: 600; font-size: 0.82rem; }
.badge-fraca { background: #f3f4f6; color: #4b5563; padding: 0.12rem 0.45rem; border-radius: 4px; font-size: 0.82rem; }
img.chart { max-width: 100%; height: auto; border: 1px solid #e5e7eb; margin: 0.75rem 0 1.25rem 0; background: #ffffff; }
""".strip()


def _strength_label(abs_val: float) -> str:
    if abs_val >= 0.70:
        return "Forte"
    if abs_val >= 0.30:
        return "Moderada"
    return "Fraca"


def _split_ranked_associations(
    report: ExploratoryFeatureReport,
) -> tuple[list[AssociationMeasure], list[AssociationMeasure]]:
    valid: list[AssociationMeasure] = []
    undef: list[AssociationMeasure] = []
    for assoc in report.target_associations:
        if assoc.status == MetricStatus.VALID and math.isfinite(assoc.value):
            valid.append(assoc)
        else:
            undef.append(assoc)
    valid.sort(key=lambda a: (-abs(a.value), a.feature_name, a.metric_name))
    return valid, undef


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _encode_rgb_png(rgb: np.ndarray) -> bytes:
    """Encode an HxWx3 uint8 array into deterministic PNG bytes with 300 DPI metadata."""
    h, w, c = rgb.shape
    if c != 3:
        raise ConfigurationError(f"Expected RGB image with 3 channels, got {c}")
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    phys = struct.pack(">IIB", _DPI_300_PX_PER_METER, _DPI_300_PX_PER_METER, 1)
    idat = zlib.compress(raw, level=6)
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", ihdr),
            _png_chunk(b"pHYs", phys),
            _png_chunk(b"IDAT", idat),
            _png_chunk(b"IEND", b""),
        ]
    )


def _fill_rect(
    canvas: np.ndarray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    h, w, _ = canvas.shape
    cx0, cy0 = max(0, min(x0, x1)), max(0, min(y0, y1))
    cx1, cy1 = min(w, max(x0, x1)), min(h, max(y0, y1))
    if cx1 > cx0 and cy1 > cy0:
        canvas[cy0:cy1, cx0:cx1] = color


def _heat_color(abs_val: float) -> tuple[int, int, int]:
    """Interpolate |corr| in [0, 1] from light blue-gray to amber/crimson."""
    t = max(0.0, min(1.0, abs_val))
    if t < 0.5:
        u = t * 2.0
        r = int(241 + u * (251 - 241))
        g = int(245 + u * (191 - 245))
        b = int(249 + u * (36 - 249))
    else:
        u = (t - 0.5) * 2.0
        r = int(251 + u * (220 - 251))
        g = int(191 + u * (38 - 191))
        b = int(36 + u * (38 - 36))
    return (r, g, b)


def render_exploratory_target_chart(
    report: ExploratoryFeatureReport,
    fmt: str = "svg",
    *,
    top_n: int = 15,
) -> bytes:
    """Render horizontal bar chart of feature-target associations in pure SVG or PNG."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm not in ("svg", "png"):
        raise ConfigurationError(f"Unsupported chart format '{fmt}'; expected 'svg' or 'png'.")
    if top_n < 1:
        raise ConfigurationError(f"top_n must be >= 1, got {top_n}")

    valid, _ = _split_ranked_associations(report)
    items = valid[:top_n]
    target_name = (
        report.target_associations[0].target_name
        if report.target_associations
        else str(report.metadata.get("target_col", "alvo"))
    )

    if fmt_norm == "svg":
        width = 760
        row_h = 30
        top_pad = 64
        bottom_pad = 36
        height = max(180, top_pad + bottom_pad + max(1, len(items)) * row_h)
        label_x = 185
        bar_area_w = 430
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
            f'<text x="20" y="28" font-family="sans-serif" font-size="16" font-weight="bold" fill="#111827">'
            f'Associação Exploratória com o Alvo ({xml_escape(target_name)})</text>',
            f'<text x="20" y="46" font-family="sans-serif" font-size="11" fill="#6b7280">'
            f'Escopo: {xml_escape(report.scope)} — Top {len(items)} por |valor|</text>',
        ]
        if not items:
            parts.append(
                '<text x="20" y="95" font-family="sans-serif" font-size="13" fill="#6b7280">'
                'Nenhuma associação válida disponível.</text>'
            )
        else:
            max_abs = max(max(abs(a.value) for a in items), 1e-9)
            scale_max = 1.0 if max_abs <= 1.0 else max_abs
            for i, assoc in enumerate(items):
                y = top_pad + i * row_h
                bar_w = int(round((abs(assoc.value) / scale_max) * bar_area_w))
                bar_w = max(2, bar_w)
                color = "#2563eb" if assoc.value >= 0 else "#dc2626"
                parts.append(
                    f'<text x="{label_x - 8}" y="{y + 16}" text-anchor="end" font-family="sans-serif" '
                    f'font-size="12" fill="#1f2937">{xml_escape(assoc.feature_name)}</text>'
                )
                parts.append(
                    f'<rect x="{label_x}" y="{y + 3}" width="{bar_w}" height="18" rx="3" fill="{color}"/>'
                )
                parts.append(
                    f'<text x="{label_x + bar_w + 8}" y="{y + 16}" font-family="monospace" '
                    f'font-size="11" fill="#374151">{assoc.value:+.4f} ({xml_escape(assoc.metric_name)})</text>'
                )
        parts.append("</svg>")
        return "\n".join(parts).encode("utf-8")

    # Deterministic PNG rasterization
    width = 680
    row_h = 28
    top_pad = 40
    height = max(120, top_pad + 24 + max(1, len(items)) * row_h)
    canvas = np.full((height, width, 3), 255, dtype=np.uint8)
    _fill_rect(canvas, 0, 0, width, 3, (37, 99, 235))
    if items:
        max_abs = max(max(abs(a.value) for a in items), 1e-9)
        scale_max = 1.0 if max_abs <= 1.0 else max_abs
        bar_x0 = 140
        max_bar_w = 480
        _fill_rect(canvas, bar_x0 - 2, top_pad, bar_x0, top_pad + len(items) * row_h, (209, 213, 219))
        for i, assoc in enumerate(items):
            y0 = top_pad + i * row_h + 4
            bar_w = max(3, int(round((abs(assoc.value) / scale_max) * max_bar_w)))
            col = (37, 99, 235) if assoc.value >= 0 else (220, 38, 38)
            _fill_rect(canvas, bar_x0, y0, bar_x0 + bar_w, y0 + 18, col)
    return _encode_rgb_png(canvas)


def render_exploratory_redundancy_heatmap(
    report: ExploratoryFeatureReport,
    fmt: str = "svg",
) -> bytes:
    """Render symmetric predictor-predictor redundancy heatmap in pure SVG or PNG."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm not in ("svg", "png"):
        raise ConfigurationError(f"Unsupported chart format '{fmt}'; expected 'svg' or 'png'.")

    features = list(report.pairwise_redundancy_matrix.keys())
    n = len(features)

    if fmt_norm == "svg":
        cell = 44
        margin_left = 150
        margin_top = 80
        width = max(360, margin_left + max(1, n) * cell + 30)
        height = max(200, margin_top + max(1, n) * cell + 30)
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
            '<text x="20" y="28" font-family="sans-serif" font-size="16" font-weight="bold" fill="#111827">'
            'Matriz de Redundância Preditor × Preditor</text>',
            f'<text x="20" y="46" font-family="sans-serif" font-size="11" fill="#6b7280">'
            f'Escopo: {xml_escape(report.scope)} — Intensidade por |associação|</text>',
        ]
        if n == 0:
            parts.append(
                '<text x="20" y="95" font-family="sans-serif" font-size="13" fill="#6b7280">'
                'Matriz vazia.</text>'
            )
        else:
            for j, feat in enumerate(features):
                cx = margin_left + j * cell + cell // 2
                parts.append(
                    f'<text x="{cx}" y="{margin_top - 8}" text-anchor="middle" font-family="sans-serif" '
                    f'font-size="10" fill="#374151">{xml_escape(feat[:10])}</text>'
                )
            for i, fa in enumerate(features):
                ry = margin_top + i * cell
                parts.append(
                    f'<text x="{margin_left - 8}" y="{ry + cell // 2 + 4}" text-anchor="end" '
                    f'font-family="sans-serif" font-size="11" fill="#1f2937">{xml_escape(fa)}</text>'
                )
                row = report.pairwise_redundancy_matrix.get(fa, {})
                for j, fb in enumerate(features):
                    cx = margin_left + j * cell
                    val = row.get(fb)
                    if val is None or not math.isfinite(val):
                        fill_hex = "#e5e7eb"
                        txt = "N/A"
                        txt_col = "#4b5563"
                    else:
                        r, g, b = _heat_color(abs(val))
                        fill_hex = f"#{r:02x}{g:02x}{b:02x}"
                        txt = f"{val:.2f}"
                        txt_col = "#ffffff" if abs(val) >= 0.65 else "#111827"
                    parts.append(
                        f'<rect x="{cx}" y="{ry}" width="{cell}" height="{cell}" fill="{fill_hex}" stroke="#ffffff" stroke-width="1"/>'
                    )
                    parts.append(
                        f'<text x="{cx + cell // 2}" y="{ry + cell // 2 + 4}" text-anchor="middle" '
                        f'font-family="monospace" font-size="10" fill="{txt_col}">{txt}</text>'
                    )
        parts.append("</svg>")
        return "\n".join(parts).encode("utf-8")

    # PNG heatmap
    cell_px = 36
    pad = 24
    side = max(1, n) * cell_px + 2 * pad
    canvas = np.full((side, side, 3), 255, dtype=np.uint8)
    for i, fa in enumerate(features):
        row = report.pairwise_redundancy_matrix.get(fa, {})
        for j, fb in enumerate(features):
            val = row.get(fb)
            col = (229, 231, 235) if (val is None or not math.isfinite(val)) else _heat_color(abs(val))
            x0, y0 = pad + j * cell_px, pad + i * cell_px
            _fill_rect(canvas, x0 + 1, y0 + 1, x0 + cell_px - 1, y0 + cell_px - 1, col)
    return _encode_rgb_png(canvas)


def render_exploratory_report(
    report: ExploratoryFeatureReport,
    fmt: str = "markdown",
    *,
    top_n: int = 15,
    figure_paths: Sequence[str] = (),
) -> str:
    """Render Stage 2 exploratory feature report into Markdown or offline self-contained HTML."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm not in ("markdown", "html"):
        raise ConfigurationError(f"Unsupported report format '{fmt}'; expected 'markdown' or 'html'.")
    if top_n < 1:
        raise ConfigurationError(f"top_n must be >= 1, got {top_n}")

    valid, undef = _split_ranked_associations(report)
    displayed = valid[:top_n]
    target_name = (
        report.target_associations[0].target_name
        if report.target_associations
        else str(report.metadata.get("target_col", "N/A"))
    )
    sorted_pairs = sorted(
        report.high_redundancy_pairs,
        key=lambda p: (-abs(p.value), p.feature_a, p.feature_b),
    )
    features = list(report.pairwise_redundancy_matrix.keys())

    if fmt_norm == "markdown":
        lines: list[str] = [
            f"# Relatório Exploratório de Atributos (Etapa 2) — `{target_name}`",
            "",
            f"- **Escopo:** `{report.scope}`",
            f"- **Tarefa:** `{report.task_type.value}`",
            f"- **Atributos analisados:** {len(report.target_associations)} (válidos: {len(valid)}, indefinidos: {len(undef)})",
            "",
            "> [!WARNING]",
            "> **Aviso Anti-Leakage (`EXPLORATORY_FULL_DATA`):** Estas estatísticas foram calculadas sobre a base completa apenas para entendimento inicial dos dados. Não remova ou escolha variáveis definitivas apenas por estes números sem validar em cenários controlados dentro das dobras.",
        ]
        for w in report.warnings:
            lines.append(f"> - {w}")

        lines.extend([
            "",
            f"## 1. Ranking de Associação Atributo × Alvo (Top {min(top_n, len(valid))})",
            "",
            "| Posição | Atributo | Métrica | Valor | \\|Valor\\| | Força | Status |",
            "| :---: | :--- | :--- | ---: | ---: | :---: | :---: |",
        ])
        for idx, assoc in enumerate(displayed, start=1):
            abs_v = abs(assoc.value)
            lines.append(
                f"| {idx} | `{assoc.feature_name}` | `{assoc.metric_name}` | "
                f"{assoc.value:+.4f} | {abs_v:.4f} | {_strength_label(abs_v)} | `{assoc.status.value}` |"
            )
        if not displayed:
            lines.append("| — | *(nenhuma associação válida)* | — | — | — | — | — |")

        if undef:
            undef_list = ", ".join(f"`{a.feature_name}` (`{a.status.value}`)" for a in undef)
            lines.extend(["", f"**Associações indefinidas (nunca convertidas para `0.0`):** {undef_list}"])

        lines.extend(["", f"## 2. Pares Redundantes / Multicolinearidade ({len(sorted_pairs)})", ""])
        if not sorted_pairs:
            lines.append("Nenhum par de preditores superou o limiar de redundância configurado.")
        else:
            lines.extend([
                "| Atributo A | Atributo B | Métrica | Associação |",
                "| :--- | :--- | :--- | ---: |",
            ])
            for p in sorted_pairs:
                lines.append(f"| `{p.feature_a}` | `{p.feature_b}` | `{p.metric_name}` | {p.value:+.4f} |")

        lines.extend(["", "## 3. Matriz Completa Preditor × Preditor", ""])
        if not features:
            lines.append("*(Matriz vazia)*")
        else:
            header = "| Atributo | " + " | ".join(f"`{f}`" for f in features) + " |"
            sep = "| :--- | " + " | ".join("---:" for _ in features) + " |"
            lines.extend([header, sep])
            for fa in features:
                row = report.pairwise_redundancy_matrix.get(fa, {})
                cells = []
                for fb in features:
                    v = row.get(fb)
                    cells.append("N/A" if (v is None or not math.isfinite(v)) else f"{v:+.2f}")
                lines.append(f"| `{fa}` | " + " | ".join(cells) + " |")

        if figure_paths:
            lines.extend(["", "## 4. Visualizações Geradas", ""])
            for fp in figure_paths:
                lines.append(f"![Gráfico exploratório]({fp})")

        lines.extend([
            "",
            "## 5. Como Usar Estes Indicadores para Montar Cenários (`scenarios.json`)",
            "",
            "- **Cenário `FIXED` de referência:** mantenha todas as variáveis preditoras (`todas_features`) como linha de base.",
            "- **Cenário `FIXED` sem redundância:** quando houver pares muito correlacionados na Seção 2, crie um segundo cenário removendo um membro de cada par redundante para testar se modelos lineares/kernels ficam mais estáveis.",
            "- **Cenário `DYNAMIC` (`VARIANCE_THRESHOLD` ou `TOP_K_RELEVANCE`):** deixe o framework recalcular a filtragem estritamente dentro do treino de cada dobra na Etapa 4B, evitando vazamento de dados.",
        ])
        return "\n".join(lines) + "\n"

    # Offline self-contained HTML
    parts = [
        "<!DOCTYPE html>",
        '<html lang="pt-BR">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>Relatório Exploratório (Etapa 2) — {html.escape(target_name)}</title>",
        f"<style>{_HTML_CSS}</style>",
        "</head>",
        "<body>",
        f"<h1>Relatório Exploratório de Atributos (Etapa 2) — <code>{html.escape(target_name)}</code></h1>",
        f"<p><strong>Escopo:</strong> <code>{html.escape(report.scope)}</code> | "
        f"<strong>Tarefa:</strong> <code>{html.escape(report.task_type.value)}</code> | "
        f"<strong>Atributos:</strong> {len(report.target_associations)} "
        f"(válidos: {len(valid)}, indefinidos: {len(undef)})</p>",
        '<div class="warning-box"><strong>Aviso Anti-Leakage (EXPLORATORY_FULL_DATA):</strong> '
        "Estas estatísticas foram calculadas sobre a base completa apenas para exploração. "
        "Não selecione variáveis definitivas sem validar em cenários dentro das dobras.<ul>",
    ]
    for w in report.warnings:
        parts.append(f"<li>{html.escape(w)}</li>")
    parts.append("</ul></div>")

    parts.append(f"<h2>1. Ranking de Associação Atributo × Alvo (Top {min(top_n, len(valid))})</h2>")
    parts.append(
        "<table><thead><tr><th>#</th><th>Atributo</th><th>Métrica</th>"
        '<th class="num">Valor</th><th class="num">|Valor|</th><th>Força</th><th>Status</th></tr></thead><tbody>'
    )
    for idx, assoc in enumerate(displayed, start=1):
        abs_v = abs(assoc.value)
        strength = _strength_label(abs_v)
        badge_cls = "badge-forte" if abs_v >= 0.70 else ("badge-mod" if abs_v >= 0.30 else "badge-fraca")
        parts.append(
            f"<tr><td>{idx}</td><td><code>{html.escape(assoc.feature_name)}</code></td>"
            f"<td><code>{html.escape(assoc.metric_name)}</code></td>"
            f'<td class="num">{assoc.value:+.4f}</td><td class="num">{abs_v:.4f}</td>'
            f'<td><span class="{badge_cls}">{strength}</span></td>'
            f"<td><code>{html.escape(assoc.status.value)}</code></td></tr>"
        )
    parts.append("</tbody></table>")
    if undef:
        undef_html = ", ".join(
            f"<code>{html.escape(a.feature_name)}</code> (<code>{html.escape(a.status.value)}</code>)"
            for a in undef
        )
        parts.append(f"<p><strong>Associações indefinidas (sem coerção para 0.0):</strong> {undef_html}</p>")

    parts.append(f"<h2>2. Pares Redundantes / Multicolinearidade ({len(sorted_pairs)})</h2>")
    if not sorted_pairs:
        parts.append("<p>Nenhum par de preditores superou o limiar de redundância configurado.</p>")
    else:
        parts.append(
            '<table><thead><tr><th>Atributo A</th><th>Atributo B</th><th>Métrica</th><th class="num">Associação</th></tr></thead><tbody>'
        )
        for p in sorted_pairs:
            parts.append(
                f"<tr><td><code>{html.escape(p.feature_a)}</code></td>"
                f"<td><code>{html.escape(p.feature_b)}</code></td>"
                f"<td><code>{html.escape(p.metric_name)}</code></td>"
                f'<td class="num">{p.value:+.4f}</td></tr>'
            )
        parts.append("</tbody></table>")

    parts.append("<h2>3. Matriz Completa Preditor × Preditor</h2>")
    if not features:
        parts.append("<p><em>(Matriz vazia)</em></p>")
    else:
        parts.append(
            '<div class="legend">'
            '<span><strong>Intensidade fora da diagonal (|associação|):</strong></span>'
            '<span><i class="legend-swatch" style="background:#f1f5f9;"></i>0.00 (baixa)</span>'
            '<span><i class="legend-swatch" style="background:#fbbf24;"></i>0.50 (moderada)</span>'
            '<span><i class="legend-swatch" style="background:#dc2626;"></i>1.00 (alta / redundante)</span>'
            '<span><i class="legend-swatch" style="background:#f1f5f9;"></i>Diagonal (autossimilaridade)</span>'
            '</div>'
        )
        parts.append('<div class="matrix-wrap"><table class="matrix-table"><thead><tr><th class="row-hdr">Atributo</th>')
        for f in features:
            parts.append(f'<th class="col-hdr" title="{html.escape(f)}">{html.escape(f)}</th>')
        parts.append("</tr></thead><tbody>")
        for fa in features:
            parts.append(f'<tr><td class="row-hdr"><code>{html.escape(fa)}</code></td>')
            row = report.pairwise_redundancy_matrix.get(fa, {})
            for fb in features:
                v = row.get(fb)
                if v is None or not math.isfinite(v):
                    parts.append('<td class="matrix-cell">N/A</td>')
                elif fa == fb:
                    parts.append(
                        f'<td class="matrix-cell matrix-diag" title="{html.escape(fa)} × {html.escape(fb)}: {v:+.4f}">{v:+.2f}</td>'
                    )
                else:
                    r, g, b = _heat_color(abs(v))
                    txt_col = "#ffffff" if abs(v) >= 0.65 else "#111827"
                    parts.append(
                        f'<td class="matrix-cell" title="{html.escape(fa)} × {html.escape(fb)}: {v:+.4f}" '
                        f'style="background:rgb({r},{g},{b});color:{txt_col};">{v:+.2f}</td>'
                    )
            parts.append("</tr>")
        parts.append("</tbody></table></div>")

    if figure_paths:
        parts.append("<h2>4. Visualizações Geradas</h2>")
        for fp in figure_paths:
            parts.append(f'<img class="chart" src="{html.escape(fp)}" alt="Visualização exploratória"/>')

    parts.extend([
        "<h2>5. Como Usar Estes Indicadores para Montar Cenários (<code>scenarios.json</code>)</h2>",
        '<div class="guide-box"><ul>',
        "<li><strong>Cenário <code>FIXED</code> de referência:</strong> mantenha todas as variáveis (<code>todas_features</code>) como linha de base.</li>",
        "<li><strong>Cenário <code>FIXED</code> sem redundância:</strong> se houver pares redundantes na Seção 2, crie um cenário alternativo removendo um item de cada par.</li>",
        "<li><strong>Cenário <code>DYNAMIC</code> (<code>VARIANCE_THRESHOLD</code> ou <code>TOP_K_RELEVANCE</code>):</strong> a filtragem é recalculada estritamente dentro do treino de cada dobra na Etapa 4B, sem vazamento.</li>",
        "</ul></div>",
        "</body></html>",
    ])
    return "\n".join(parts)
