"""Stage 2 exploratory feature visualization: Markdown, print/PDF-ready HTML, CSVs, and Matplotlib PNGs.

Complies with EXPLR-01..EXPLR-06, CA-E2-01, AD-033 (Matplotlib Agg lazy import), and CLI-11.
"""

from __future__ import annotations

import csv
import html
import io
import math
from typing import Any, Sequence

import numpy as np

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.features.types import ExploratoryFeatureReport

# Compact 5x7 bitmap font (each row is 5 bits, MSB on the left)
_FONT_5X7: dict[str, tuple[int, ...]] = {
    " ": (0, 0, 0, 0, 0, 0, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    '"': (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
    "%": (0x19, 0x1A, 0x04, 0x04, 0x0B, 0x13, 0x00),
    "'": (0x04, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "*": (0x00, 0x15, 0x0E, 0x1F, 0x0E, 0x15, 0x00),
    "+": (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    ",": (0x00, 0x00, 0x00, 0x00, 0x04, 0x04, 0x08),
    "-": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    "/": (0x01, 0x02, 0x04, 0x04, 0x08, 0x10, 0x00),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1E, 0x01, 0x01, 0x0E, 0x01, 0x01, 0x1E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    "<": (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    "=": (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    ">": (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1C, 0x12, 0x11, 0x11, 0x11, 0x12, 0x1C),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x12, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "[": (0x0E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x0E),
    "]": (0x0E, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0E),
    "_": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F),
    "a": (0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
    "b": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x1E),
    "c": (0x00, 0x00, 0x0F, 0x10, 0x10, 0x10, 0x0F),
    "d": (0x01, 0x01, 0x0F, 0x11, 0x11, 0x11, 0x0F),
    "e": (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
    "f": (0x06, 0x08, 0x1C, 0x08, 0x08, 0x08, 0x08),
    "g": (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "h": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "i": (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    "j": (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    "k": (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    "l": (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "m": (0x00, 0x00, 0x1A, 0x15, 0x15, 0x11, 0x11),
    "n": (0x00, 0x00, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "o": (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    "p": (0x00, 0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10),
    "q": (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x01),
    "r": (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
    "s": (0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    "t": (0x08, 0x08, 0x1C, 0x08, 0x08, 0x09, 0x06),
    "u": (0x00, 0x00, 0x11, 0x11, 0x11, 0x11, 0x0F),
    "v": (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "w": (0x00, 0x00, 0x11, 0x11, 0x15, 0x15, 0x0A),
    "x": (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    "y": (0x00, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    "z": (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
    "|": (0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
}

_HTML_CSS = """
@page { size: A4 portrait; margin: 15mm; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 960px; margin: 1.5rem auto; padding: 0 1.25rem; color: #1f2937; line-height: 1.55; }
h1, h2, h3 { color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.25rem; margin-top: 1.4rem; }
table { border-collapse: collapse; width: 100%; margin: 0.75rem 0 1.25rem 0; font-size: 0.9rem; }
th, td { border: 1px solid #d1d5db; padding: 0.45rem 0.6rem; text-align: left; vertical-align: top; }
th { background: #f3f4f6; font-weight: 600; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.warning-box { background: #fffbeb; border-left: 4px solid #d97706; padding: 0.8rem 1rem; margin: 0.9rem 0; }
.guide-box { background: #eff6ff; border-left: 4px solid #2563eb; padding: 0.8rem 1rem; margin: 0.9rem 0; }
.badge-forte { background: #dcfce7; color: #166534; padding: 0.1rem 0.45rem; border-radius: 4px; font-weight: 600; font-size: 0.82rem; }
.badge-mod { background: #fef9c3; color: #854d0e; padding: 0.1rem 0.45rem; border-radius: 4px; font-weight: 600; font-size: 0.82rem; }
.badge-fraca { background: #f3f4f6; color: #4b5563; padding: 0.1rem 0.45rem; border-radius: 4px; font-size: 0.82rem; }
figure.chart-card { margin: 1rem 0 1.4rem 0; padding: 0.6rem; border: 1px solid #e5e7eb; background: #ffffff; text-align: center; }
figure.chart-card img { max-width: 100%; height: auto; display: block; margin: 0 auto; }
figure.chart-card figcaption { font-size: 0.85rem; color: #4b5563; margin-top: 0.45rem; }
@media print {
  body { margin: 0; padding: 0; max-width: none; font-size: 10.5pt; }
  table, figure.chart-card, .warning-box, .guide-box { break-inside: avoid; page-break-inside: avoid; }
  h1, h2 { break-after: avoid; page-break-after: avoid; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
""".strip()


def _to_ascii_label(text: str) -> str:
    """Fold Unicode accents cleanly for deterministic 5x7 bitmap rendering."""
    replaced = text.replace("×", "x").replace("·", ".")
    return unicodedata.normalize("NFKD", replaced).encode("ascii", "ignore").decode("ascii")


def _strength_label(abs_val: float) -> str:
    if abs_val >= 0.70:
        return "Forte"
    if abs_val >= 0.30:
        return "Moderada"
    return "Fraca"


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


def _draw_text(
    canvas: np.ndarray,
    x: int,
    y: int,
    text: str,
    color: tuple[int, int, int],
    *,
    scale: int = 2,
    align: str = "left",
) -> None:
    """Draw crisp pixel-aligned 5x7 bitmap text onto an RGB canvas."""
    clean = _to_ascii_label(text)
    if not clean:
        return
    step = 6 * scale
    total_w = len(clean) * step - scale
    start_x = x
    if align == "right":
        start_x = x - total_w
    elif align == "center":
        start_x = x - total_w // 2

    h_img, w_img, _ = canvas.shape
    for idx, ch in enumerate(clean):
        glyph = _FONT_5X7.get(ch, _FONT_5X7.get(ch.upper(), _FONT_5X7[" "]))
        gx = start_x + idx * step
        for row_idx, bits in enumerate(glyph):
            py0 = y + row_idx * scale
            if py0 >= h_img or py0 + scale <= 0:
                continue
            for col_idx in range(5):
                if (bits >> (4 - col_idx)) & 1:
                    px0 = gx + col_idx * scale
                    if px0 < w_img and px0 + scale > 0:
                        _fill_rect(canvas, px0, py0, px0 + scale, py0 + scale, color)


def _draw_text_vertical(
    canvas: np.ndarray,
    x_center: int,
    y_bottom: int,
    text: str,
    color: tuple[int, int, int],
    *,
    scale: int = 1,
) -> None:
    """Draw text rotated 90 degrees counter-clockwise (bottom-to-top) for column headers."""
    clean = _to_ascii_label(text)
    if not clean:
        return
    step = 6 * scale
    glyph_w = 7 * scale
    x0 = x_center - glyph_w // 2
    h_img, w_img, _ = canvas.shape
    for idx, ch in enumerate(clean):
        glyph = _FONT_5X7.get(ch, _FONT_5X7.get(ch.upper(), _FONT_5X7[" "]))
        base_y = y_bottom - idx * step
        for col_idx in range(5):
            py0 = base_y - (col_idx + 1) * scale
            if py0 >= h_img or py0 + scale <= 0:
                continue
            for row_idx, bits in enumerate(glyph):
                if (bits >> (4 - col_idx)) & 1:
                    px0 = x0 + row_idx * scale
                    if px0 < w_img and px0 + scale > 0:
                        _fill_rect(canvas, px0, py0, px0 + scale, py0 + scale, color)


def _heat_color(abs_val: float) -> tuple[int, int, int]:
    """Interpolate |corr| in [0, 1] from light slate to amber/crimson."""
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


def _prepare_target_chart_data(
    report: ExploratoryFeatureReport,
    top_n: int,
) -> tuple[str, list[str], list[float], list[float], list[str]]:
    """Pure data preparation for Stage 2 target association ranking chart."""
    valid_entries, _ = report.ranked_target_features()
    items = valid_entries[:top_n]
    target_name = (
        report.target_associations[0].target_name
        if report.target_associations
        else str(report.metadata.get("target_col", "alvo"))
    )
    labels: list[str] = []
    mean_abs_vals: list[float] = []
    signed_means: list[float] = []
    annotations: list[str] = []
    for feat_name, mean_abs, sub_items in items:
        labels.append(feat_name)
        mean_abs_vals.append(float(mean_abs))
        signed_mean = sum(a.value for a in sub_items) / len(sub_items)
        signed_means.append(float(signed_mean))
        detail = " ".join(f"{a.metric_name[:1]}:{a.value:+.2f}" for a in sub_items)
        annotations.append(f"{mean_abs:.3f} ({detail})")
    return target_name, labels, mean_abs_vals, signed_means, annotations


def _prepare_redundancy_heatmap_data(
    report: ExploratoryFeatureReport,
) -> tuple[list[str], np.ndarray]:
    """Pure data preparation for Stage 2 Predictor x Predictor redundancy heatmap."""
    features = list(report.pairwise_redundancy_matrix.keys())
    n = len(features)
    mat = np.full((n, n), np.nan, dtype=np.float64)
    for i, fa in enumerate(features):
        row = report.pairwise_redundancy_matrix.get(fa, {})
        for j, fb in enumerate(features):
            v = row.get(fb)
            if v is not None and math.isfinite(v):
                mat[i, j] = abs(float(v))
    return features, mat


def _fig_to_png_bytes(fig: Any) -> bytes:
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=150,
        bbox_inches="tight",
        facecolor="white",
        metadata={"Software": "experimental-ml-framework"},
    )
    return buf.getvalue()


def render_exploratory_target_chart(
    report: ExploratoryFeatureReport,
    fmt: str = "png",
    *,
    top_n: int = 15,
) -> bytes:
    """Render legible horizontal bar chart of unique features ranked by mean |value| into PNG."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm != "png":
        raise ConfigurationError(f"Unsupported chart format '{fmt}'; only 'png' is supported.")
    if top_n < 1:
        raise ConfigurationError(f"top_n must be >= 1, got {top_n}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    target_name, labels, mean_abs_vals, signed_means, annotations = _prepare_target_chart_data(report, top_n)

    if not labels:
        fig, ax = plt.subplots(figsize=(7.5, 2.6))
        ax.axis("off")
        ax.set_title(f"Ranking Único Atributo × Alvo ({target_name})", fontsize=12, fontweight="bold", loc="left")
        ax.text(0.02, 0.5, "Nenhuma associação válida disponível.", fontsize=10, color="#6b7280", transform=ax.transAxes)
        data = _fig_to_png_bytes(fig)
        plt.close(fig)
        return data

    n_items = len(labels)
    fig_h = max(3.2, 1.4 + 0.42 * n_items)
    fig, ax = plt.subplots(figsize=(9.2, fig_h))
    y_pos = np.arange(n_items)
    colors = ["#2563eb" if s >= 0 else "#dc2626" for s in signed_means]
    ax.barh(y_pos, mean_abs_vals, color=colors, height=0.62, edgecolor="#1e293b", linewidth=0.4)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()

    max_val = max(mean_abs_vals) if mean_abs_vals else 1.0
    x_lim = max(1.0, max_val * 1.38) if max_val <= 1.0 else max_val * 1.38
    ax.set_xlim(0.0, x_lim)
    ax.grid(axis="x", linestyle="--", alpha=0.35, color="#9ca3af")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for y, val, ann in zip(y_pos, mean_abs_vals, annotations):
        ax.text(val + x_lim * 0.015, y, ann, va="center", ha="left", fontsize=8, color="#374151")

    ax.set_xlabel("Média |valor| de associação com o alvo", fontsize=9)
    ax.set_title(
        f"Ranking Único Atributo × Alvo ({target_name})\nEscopo: {report.scope} | Top {n_items} por Média |valor|",
        fontsize=11,
        fontweight="bold",
        loc="left",
        pad=10,
    )
    legend_handles = [
        Patch(facecolor="#2563eb", label="Sinal médio (+)"),
        Patch(facecolor="#dc2626", label="Sinal médio (-)"),
    ]
    ax.legend(handles=legend_handles, loc="lower right", frameon=True, fontsize=8)
    fig.tight_layout()
    data = _fig_to_png_bytes(fig)
    plt.close(fig)
    return data


def render_exploratory_redundancy_heatmap(
    report: ExploratoryFeatureReport,
    fmt: str = "png",
) -> bytes:
    """Render legible symmetric Predictor x Predictor redundancy heatmap into PNG."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm != "png":
        raise ConfigurationError(f"Unsupported chart format '{fmt}'; only 'png' is supported.")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    features, mat = _prepare_redundancy_heatmap_data(report)
    n = len(features)
    if n == 0:
        fig, ax = plt.subplots(figsize=(6.5, 2.4))
        ax.axis("off")
        ax.set_title("Matriz de Redundância Preditor × Preditor", fontsize=12, fontweight="bold", loc="left")
        ax.text(0.02, 0.5, "Matriz vazia.", fontsize=10, color="#6b7280", transform=ax.transAxes)
        data = _fig_to_png_bytes(fig)
        plt.close(fig)
        return data

    side = max(4.8, min(12.0, 2.2 + 0.52 * n))
    fig, ax = plt.subplots(figsize=(side + 1.4, side))
    cmap = plt.get_cmap("YlOrRd").with_extremes(bad="#e5e7eb")
    masked = np.ma.masked_invalid(mat)
    im = ax.imshow(masked, cmap=cmap, vmin=0.0, vmax=1.0, aspect="equal")

    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    tick_fs = 9 if n <= 12 else (7.5 if n <= 24 else 6)
    ax.set_xticklabels(features, rotation=45, ha="right", rotation_mode="anchor", fontsize=tick_fs)
    ax.set_yticklabels(features, fontsize=tick_fs)

    if n <= 20:
        ann_fs = 8 if n <= 10 else 6.5
        for i in range(n):
            for j in range(n):
                val = mat[i, j]
                if not math.isfinite(val):
                    txt, col = "N/A", "#4b5563"
                else:
                    txt = f"{val:.2f}"
                    col = "white" if val >= 0.65 else "#111827"
                ax.text(j, i, txt, ha="center", va="center", fontsize=ann_fs, color=col)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("|Redundância| (0.00 a 1.00)", fontsize=8.5)
    ax.set_title(
        f"Matriz de Redundância Preditor × Preditor\nEscopo: {report.scope} | {n} × {n} preditores",
        fontsize=11,
        fontweight="bold",
        loc="left",
        pad=12,
    )
    fig.tight_layout()
    data = _fig_to_png_bytes(fig)
    plt.close(fig)
    return data


def render_exploratory_target_csv(report: ExploratoryFeatureReport) -> str:
    """Export unique-feature ranked associations (mean |value| + individual metrics) to CSV."""
    valid_entries, nan_entries = report.ranked_target_features()
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["rank", "feature", "mean_abs", "strength", "metrics_detail", "status"])
    for idx, (feat_name, mean_abs, items) in enumerate(valid_entries, start=1):
        detail = "; ".join(f"{a.metric_name}={a.value:.6f}" for a in items)
        writer.writerow([idx, feat_name, f"{mean_abs:.6f}", _strength_label(mean_abs), detail, "VALID"])
    for feat_name, items in nan_entries:
        detail = "; ".join(f"{a.metric_name}={a.status.value}" for a in items)
        writer.writerow(["", feat_name, "NaN", "N/A", detail, items[0].status.value])
    return buf.getvalue()


def render_exploratory_redundancy_csv(report: ExploratoryFeatureReport) -> str:
    """Export full Predictor x Predictor redundancy matrix to standalone CSV."""
    features = list(report.pairwise_redundancy_matrix.keys())
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["feature", *features])
    for fa in features:
        row = report.pairwise_redundancy_matrix.get(fa, {})
        vals = []
        for fb in features:
            v = row.get(fb)
            vals.append("NaN" if (v is None or not math.isfinite(v)) else f"{v:.6f}")
        writer.writerow([fa, *vals])
    return buf.getvalue()


def render_exploratory_report(
    report: ExploratoryFeatureReport,
    fmt: str = "markdown",
    *,
    top_n: int = 15,
    figure_paths: Sequence[str] = (),
) -> str:
    """Render Stage 2 exploratory feature report into clean Markdown or print/PDF-ready HTML."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm not in ("markdown", "html"):
        raise ConfigurationError(f"Unsupported report format '{fmt}'; expected 'markdown' or 'html'.")
    if top_n < 1:
        raise ConfigurationError(f"top_n must be >= 1, got {top_n}")

    valid_entries, undef_entries = report.ranked_target_features()
    displayed = valid_entries[:top_n]
    total_unique = len(valid_entries) + len(undef_entries)
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
            f"- **Atributos analisados:** {total_unique} (válidos: {len(valid_entries)}, indefinidos: {len(undef_entries)})",
            "",
            "> [!WARNING]",
            "> **Aviso Anti-Leakage (`EXPLORATORY_FULL_DATA`):** Estas estatísticas foram calculadas sobre a base completa apenas para entendimento inicial dos dados. Não remova ou escolha variáveis definitivas apenas por estes números sem validar em cenários controlados dentro das dobras.",
        ]
        for w in report.warnings:
            lines.append(f"> - {w}")

        lines.extend([
            "",
            f"## 1. Ranking Único de Associação Atributo × Alvo (Top {min(top_n, len(valid_entries))})",
            "",
            "| Posição | Atributo | Média \\|·\\| | Força | Métricas Individuais | Status |",
            "| :---: | :--- | ---: | :---: | :--- | :---: |",
        ])
        for idx, (feat_name, mean_abs, items) in enumerate(displayed, start=1):
            detail = ", ".join(f"`{a.metric_name}`={a.value:+.4f}" for a in items)
            lines.append(
                f"| {idx} | `{feat_name}` | {mean_abs:.4f} | {_strength_label(mean_abs)} | {detail} | `VALID` |"
            )
        if not displayed:
            lines.append("| — | *(nenhuma associação válida)* | — | — | — | — |")

        if undef_entries:
            undef_list = ", ".join(f"`{f}` (`{items[0].status.value}`)" for f, items in undef_entries)
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

        lines.extend([
            "",
            "## 3. Arquivos Exportados e Visualizações",
            "",
            "- **Ranking completo (CSV):** [`exploratory_target_associations.csv`](exploratory_target_associations.csv)",
            f"- **Matriz completa Preditor × Preditor ({len(features)} × {len(features)}, CSV):** [`exploratory_redundancy_matrix.csv`](exploratory_redundancy_matrix.csv)",
        ])
        for fp in figure_paths:
            lines.append(f"- ![Gráfico exploratório]({fp})")

        lines.extend([
            "",
            "## 4. Como Usar Estes Indicadores para Montar Cenários (`scenarios.json`)",
            "",
            "- **Cenário `FIXED` de referência:** mantenha todas as variáveis preditoras (`todas_features`) como linha de base.",
            "- **Cenário `FIXED` sem redundância:** quando houver pares muito correlacionados na Seção 2, crie um segundo cenário removendo um membro de cada par redundante para testar se modelos lineares/kernels ficam mais estáveis.",
            "- **Cenário `DYNAMIC` (`VARIANCE_THRESHOLD` ou `TOP_K_RELEVANCE`):** deixe o framework recalcular a filtragem estritamente dentro do treino de cada dobra na Etapa 4B, evitando vazamento de dados.",
        ])
        return "\n".join(lines) + "\n"

    # Print/PDF-ready offline HTML (clean, no horizontal scrollbars, no giant inline matrix)
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
        f"<strong>Atributos únicos:</strong> {total_unique} "
        f"(válidos: {len(valid_entries)}, indefinidos: {len(undef_entries)})</p>",
        '<div class="warning-box"><strong>Aviso Anti-Leakage (EXPLORATORY_FULL_DATA):</strong> '
        "Estas estatísticas foram calculadas sobre a base completa apenas para exploração. "
        "Não selecione variáveis definitivas sem validar em cenários dentro das dobras.<ul>",
    ]
    for w in report.warnings:
        parts.append(f"<li>{html.escape(w)}</li>")
    parts.append("</ul></div>")

    parts.append(f"<h2>1. Ranking Único Atributo × Alvo (Top {min(top_n, len(valid_entries))})</h2>")
    parts.append(
        "<table><thead><tr><th>#</th><th>Atributo</th>"
        '<th class="num">Média |·|</th><th>Força</th><th>Métricas Individuais</th><th>Status</th></tr></thead><tbody>'
    )
    for idx, (feat_name, mean_abs, items) in enumerate(displayed, start=1):
        strength = _strength_label(mean_abs)
        badge_cls = "badge-forte" if mean_abs >= 0.70 else ("badge-mod" if mean_abs >= 0.30 else "badge-fraca")
        detail = ", ".join(f"<code>{html.escape(a.metric_name)}</code>={a.value:+.4f}" for a in items)
        parts.append(
            f"<tr><td>{idx}</td><td><code>{html.escape(feat_name)}</code></td>"
            f'<td class="num">{mean_abs:.4f}</td>'
            f'<td><span class="{badge_cls}">{strength}</span></td>'
            f"<td>{detail}</td>"
            "<td><code>VALID</code></td></tr>"
        )
    parts.append("</tbody></table>")
    if undef_entries:
        undef_html = ", ".join(
            f"<code>{html.escape(f)}</code> (<code>{html.escape(items[0].status.value)}</code>)"
            for f, items in undef_entries
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

    parts.extend([
        "<h2>3. Gráficos e Planilhas Exportadas</h2>",
        "<ul>",
        '<li><strong>Ranking completo (CSV):</strong> <a href="exploratory_target_associations.csv"><code>exploratory_target_associations.csv</code></a></li>',
        f'<li><strong>Matriz completa Preditor × Preditor ({len(features)} × {len(features)}, CSV):</strong> '
        '<a href="exploratory_redundancy_matrix.csv"><code>exploratory_redundancy_matrix.csv</code></a></li>',
        "</ul>",
    ])
    for fp in figure_paths:
        cap = "Ranking único de associação com o alvo" if "target" in fp else "Mapa de calor de redundância Preditor × Preditor"
        parts.append(
            f'<figure class="chart-card"><img src="{html.escape(fp)}" alt="{html.escape(cap)}"/>'
            f"<figcaption>{html.escape(cap)}</figcaption></figure>"
        )

    parts.extend([
        "<h2>4. Como Usar Estes Indicadores para Montar Cenários (<code>scenarios.json</code>)</h2>",
        '<div class="guide-box"><ul>',
        "<li><strong>Cenário <code>FIXED</code> de referência:</strong> mantenha todas as variáveis (<code>todas_features</code>) como linha de base.</li>",
        "<li><strong>Cenário <code>FIXED</code> sem redundância:</strong> se houver pares redundantes na Seção 2, crie um cenário alternativo removendo um item de cada par.</li>",
        "<li><strong>Cenário <code>DYNAMIC</code> (<code>VARIANCE_THRESHOLD</code> ou <code>TOP_K_RELEVANCE</code>):</strong> a filtragem é recalculada estritamente dentro do treino de cada dobra na Etapa 4B, sem vazamento.</li>",
        "</ul></div>",
        "</body></html>",
    ])
    return "\n".join(parts)
