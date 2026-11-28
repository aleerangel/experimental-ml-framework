"""Scientific figure builders and Matplotlib (Agg) renderers for PNG (300 DPI), SVG, and PDF (REP-04, AD-033)."""

from __future__ import annotations

import io
import math
import struct
import zlib
from typing import Any

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
    """Build an immutable PlotSpecification from LoadedExperimentData (CA-E6-01, REP-04, M10-02)."""
    if not isinstance(family, ReportFamily):
        family = ReportFamily(family)
    sel = select_report_content(loaded_data, selection)
    target_metric = metric_name or (sel.metric_ids[0] if sel.metric_ids else "metric")
    notes: list[str] = []

    if family == ReportFamily.D_PREDICTIVE_PERFORMANCE:
        x_vals: list[str] = []
        y_vals: list[float] = []
        y_errs: list[float] = []
        train_vals: list[float] = []
        train_errs: list[float] = []
        has_train = False
        holdout_vals: list[float] = []
        has_holdout = False

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

            t_agg = summary.aggregated_train_metrics.get(target_metric)
            if t_agg is not None and t_agg.status != MetricStatus.UNDEFINED_NAN and t_agg.mean is not None and math.isfinite(t_agg.mean):
                train_vals.append(float(t_agg.mean))
                train_errs.append(float(t_agg.std) if t_agg.std is not None and math.isfinite(t_agg.std) else 0.0)
                has_train = True
            else:
                train_vals.append(float("nan"))
                train_errs.append(0.0)

            hmv = summary.holdout_metrics.get(target_metric)
            if hmv is not None and hmv.status != MetricStatus.UNDEFINED_NAN and math.isfinite(hmv.value):
                holdout_vals.append(float(hmv.value))
                has_holdout = True
            else:
                holdout_vals.append(float("nan"))

        series_list: list[PlotSeries] = []
        if has_train:
            series_list.append(PlotSeries(name=f"{target_metric} (Treino)", x_values=tuple(x_vals), y_values=tuple(train_vals), y_err=tuple(train_errs)))
        series_list.append(PlotSeries(name=f"{target_metric} (DEV_CV)", x_values=tuple(x_vals), y_values=tuple(y_vals), y_err=tuple(y_errs)))
        if has_holdout:
            series_list.append(PlotSeries(name=f"{target_metric} (Holdout)", x_values=tuple(x_vals), y_values=tuple(holdout_vals)))

        prov = _make_fig_provenance("fig_family_d", family, loaded_data, sel, ("statistics/descriptive_consolidation.json",))
        return PlotSpecification(
            plot_id="fig_family_d",
            family=family,
            plot_type=PlotType.BAR_COMPARISON,
            title=f"Desempenho Preditivo ({target_metric})",
            subtitle="Média ± desvio padrão entre folds (DEV_CV)",
            x_label="Configuração",
            y_label=target_metric,
            series=tuple(series_list),
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
            if sel.model_ids and (cmp_res.config_a[0] not in sel.model_ids or cmp_res.config_b[0] not in sel.model_ids):
                continue
            if sel.scenario_ids and (cmp_res.config_a[1] not in sel.scenario_ids or cmp_res.config_b[1] not in sel.scenario_ids):
                continue
            diff = cmp_res.observed_difference
            ci_lo, ci_hi = cmp_res.nadeau_bengio.confidence_interval
            if not (math.isfinite(diff) and math.isfinite(ci_lo) and math.isfinite(ci_hi)):
                notes.append(f"Excluded comparison {cmp_res.comparison_id} due to non-finite difference/CI.")
                continue
            x_vals.append(f"{cmp_res.config_a[0]}/{cmp_res.config_a[1]} vs {cmp_res.config_b[0]}/{cmp_res.config_b[1]}")
            y_vals.append(float(diff))
            y_errs.append(0.5 * abs(float(ci_hi) - float(ci_lo)))

        series = (PlotSeries(name=f"Diferença ({target_metric})", x_values=tuple(x_vals), y_values=tuple(y_vals), y_err=tuple(y_errs)),)
        prov = _make_fig_provenance("fig_family_e", family, loaded_data, sel, ("statistics/statistical_comparisons.json",))
        return PlotSpecification(
            plot_id="fig_family_e",
            family=family,
            plot_type=PlotType.PAIRED_DIFF_CI,
            title=f"Diferenças Pareadas e IC 95% ({target_metric})",
            subtitle="Teste t corrigido de Nadeau-Bengio",
            x_label="Comparação",
            y_label=f"Δ ({target_metric})",
            series=series,
            notes=tuple(notes),
            provenance=prov,
            reference_y=0.0,
            reference_label="Δ = 0 (equivalência)",
        )

    if family == ReportFamily.F_STABILITY_COST_PARETO:
        pareto_x: list[float] = []
        pareto_y: list[float] = []
        pareto_labels: list[str] = []
        dom_x: list[float] = []
        dom_y: list[float] = []
        dom_labels: list[str] = []
        pareto = loaded_data.statistics.pareto
        if pareto is not None and len(pareto.objectives) >= 2:
            o1, o2 = pareto.objectives[0].name, pareto.objectives[1].name
            for pt in pareto.pareto_frontier:
                pareto_x.append(float(pt.objective_values[o1]))
                pareto_y.append(float(pt.objective_values[o2]))
                pareto_labels.append(f"{pt.config_id[0]}/{pt.config_id[1]}")
            for pt in pareto.dominated_configurations:
                dom_x.append(float(pt.objective_values[o1]))
                dom_y.append(float(pt.objective_values[o2]))
                dom_labels.append(f"{pt.config_id[0]}/{pt.config_id[1]}")
            x_lbl, y_lbl = o1, o2
        else:
            x_lbl, y_lbl = "Tempo médio por célula (s)", target_metric
            for (m_id, sc_id), summary in sorted(loaded_data.statistics.consolidation.configurations.items()):
                if (sel.model_ids and m_id not in sel.model_ids) or (sel.scenario_ids and sc_id not in sel.scenario_ids):
                    continue
                agg = summary.aggregated_metrics.get(target_metric)
                if agg is not None and agg.mean is not None and math.isfinite(agg.mean):
                    t_val = summary.aggregated_timing.total_cell_mean_s if summary.aggregated_timing else float(len(pareto_x) + 1)
                    pareto_x.append(float(t_val))
                    pareto_y.append(float(agg.mean))
                    pareto_labels.append(f"{m_id}/{sc_id}")

        series_list = [
            PlotSeries("Fronteira de Pareto", tuple(pareto_x), tuple(pareto_y), point_labels=tuple(pareto_labels)),
        ]
        if dom_x:
            series_list.append(PlotSeries("Dominadas", tuple(dom_x), tuple(dom_y), point_labels=tuple(dom_labels)))
        prov = _make_fig_provenance("fig_family_f", family, loaded_data, sel, ("statistics/pareto_summary.json",))
        return PlotSpecification(
            plot_id="fig_family_f",
            family=family,
            plot_type=PlotType.PARETO_TRADEOFF,
            title="Trade-off Multiobjetivo e Fronteira de Pareto",
            subtitle="Coordenadas numéricas reais dos objetivos",
            x_label=x_lbl,
            y_label=y_lbl,
            series=tuple(series_list),
            notes=tuple(notes),
            provenance=prov,
        )

    if family == ReportFamily.G_MODEL_SPECIFIC_ARTIFACTS and loaded_data.cell_diagnostics:
        feat_vals: dict[str, list[float]] = {}
        for entry in loaded_data.cell_diagnostics:
            m_id = str(entry.get("model_id", ""))
            sc_id = str(entry.get("scenario_id", ""))
            if sel.model_ids and m_id not in sel.model_ids:
                continue
            if sel.scenario_ids and sc_id not in sel.scenario_ids:
                continue
            diags = entry.get("diagnostics", {})
            if not isinstance(diags, dict):
                continue
            for key in ("feature_importances", "importances", "coefficients"):
                val = diags.get(key)
                if isinstance(val, dict):
                    for f_name, f_val in val.items():
                        if isinstance(f_val, (int, float)) and math.isfinite(float(f_val)):
                            feat_vals.setdefault(str(f_name), []).append(abs(float(f_val)))
        if feat_vals:
            ranked = sorted(
                ((f, float(np.mean(vs)), float(np.std(vs, ddof=1)) if len(vs) > 1 else 0.0) for f, vs in feat_vals.items()),
                key=lambda item: (-item[1], item[0]),
            )[:15]
            prov = _make_fig_provenance("fig_family_g", family, loaded_data, sel, ("runs/cells",))
            return PlotSpecification(
                plot_id="fig_family_g",
                family=family,
                plot_type=PlotType.BAR_COMPARISON,
                title="Diagnósticos de Modelo — Importância Média de Atributos",
                subtitle="Média ± desvio padrão entre folds",
                x_label="Atributo",
                y_label="Importância |valor|",
                series=(
                    PlotSeries(
                        "Importância média",
                        tuple(r[0] for r in ranked),
                        tuple(r[1] for r in ranked),
                        y_err=tuple(r[2] for r in ranked),
                    ),
                ),
                notes=tuple(notes),
                provenance=prov,
            )

    # Fallback summary for A, B, C, or G without numeric diagnostics
    prov = _make_fig_provenance(f"fig_{family.value.lower()}", family, loaded_data, sel, ("statistics/statistics_manifest.json",))
    return PlotSpecification(
        plot_id=f"fig_{family.value.lower()}",
        family=family,
        plot_type=PlotType.BAR_COMPARISON,
        title=f"Resumo ({family.value})",
        x_label="Item",
        y_label="Quantidade",
        series=(PlotSeries("Resumo", ("total_configs",), (float(loaded_data.statistics.consolidation.total_configurations),)),),
        notes=tuple(notes),
        provenance=prov,
    )


def _ensure_png_300dpi_phys(png_bytes: bytes) -> bytes:
    """Ensure PNG bytes contain deterministic pHYs chunk at 300 DPI (11811 px/m)."""
    phys_data = struct.pack(">IIB", _DPI_300_PX_PER_METER, _DPI_300_PX_PER_METER, 1)
    phys_chunk = struct.pack(">I", len(phys_data)) + b"pHYs" + phys_data + struct.pack(">I", zlib.crc32(b"pHYs" + phys_data) & 0xFFFFFFFF)
    if b"pHYs" in png_bytes:
        idx = png_bytes.index(b"pHYs")
        chunk_start = idx - 4
        chunk_len = struct.unpack(">I", png_bytes[chunk_start:idx])[0]
        chunk_end = idx + 4 + chunk_len + 4
        return png_bytes[:chunk_start] + phys_chunk + png_bytes[chunk_end:]
    ihdr_end = 8 + 4 + 4 + 13 + 4
    return png_bytes[:ihdr_end] + phys_chunk + png_bytes[ihdr_end:]


def _draw_matplotlib_figure(spec: PlotSpecification) -> Any:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["svg.hashsalt"] = "experimental-ml-framework"

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    palette = ["#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed"]

    if spec.plot_type == PlotType.BAR_COMPARISON:
        n_series = max(1, len(spec.series))
        first_x = spec.series[0].x_values if spec.series else ()
        n_cats = len(first_x)
        x_idx = np.arange(n_cats, dtype=float)
        bar_w = 0.72 / n_series
        for s_idx, s in enumerate(spec.series):
            offset = (s_idx - (n_series - 1) / 2.0) * bar_w
            y_arr = np.array(s.y_values, dtype=float)
            valid_mask = np.isfinite(y_arr)
            if np.any(valid_mask):
                yerr_arr = np.array(s.y_err, dtype=float) if s.y_err else None
                ax.bar(
                    x_idx[valid_mask] + offset,
                    y_arr[valid_mask],
                    width=bar_w * 0.92,
                    yerr=yerr_arr[valid_mask] if yerr_arr is not None else None,
                    capsize=3.5,
                    color=palette[s_idx % len(palette)],
                    edgecolor="#1e293b",
                    linewidth=0.4,
                    label=s.name,
                )
        ax.set_xticks(x_idx)
        rot = 30 if n_cats > 4 or any(len(str(x)) > 14 for x in first_x) else 0
        ax.set_xticklabels([str(x) for x in first_x], rotation=rot, ha="right" if rot else "center", fontsize=8.5)

    elif spec.plot_type == PlotType.PAIRED_DIFF_CI:
        for s_idx, s in enumerate(spec.series):
            x_idx = np.arange(len(s.x_values), dtype=float)
            ax.errorbar(
                x_idx,
                s.y_values,
                yerr=s.y_err,
                fmt="o",
                color=palette[s_idx % len(palette)],
                ecolor="#334155",
                elinewidth=1.4,
                capsize=4,
                markersize=6,
                label=s.name,
            )
            ax.set_xticks(x_idx)
            rot = 25 if len(s.x_values) > 3 or any(len(str(x)) > 16 for x in s.x_values) else 0
            ax.set_xticklabels([str(x) for x in s.x_values], rotation=rot, ha="right" if rot else "center", fontsize=8.5)
        ref_y = 0.0 if spec.reference_y is None else spec.reference_y
        ax.axhline(ref_y, color="#dc2626", linestyle="--", linewidth=1.1, label=spec.reference_label or f"y = {ref_y}")

    elif spec.plot_type in (PlotType.PARETO_TRADEOFF, PlotType.SCATTER_PARITY):
        all_x: list[float] = []
        all_y: list[float] = []
        for s_idx, s in enumerate(spec.series):
            xs = [float(v) for v in s.x_values]
            ys = [float(v) for v in s.y_values]
            all_x.extend(xs)
            all_y.extend(ys)
            marker = "*" if s_idx == 0 and spec.plot_type == PlotType.PARETO_TRADEOFF else "o"
            size = 110 if marker == "*" else 55
            ax.scatter(xs, ys, s=size, marker=marker, color=palette[s_idx % len(palette)], edgecolor="#1e293b", linewidth=0.5, label=s.name, zorder=3)
            if s.point_labels:
                for px, py, lbl in zip(xs, ys, s.point_labels):
                    ax.annotate(lbl, (px, py), textcoords="offset points", xytext=(5, 5), fontsize=7.5, color="#334155")
        if spec.plot_type == PlotType.SCATTER_PARITY and all_x and all_y:
            lo = min(min(all_x), min(all_y))
            hi = max(max(all_x), max(all_y))
            ax.plot([lo, hi], [lo, hi], linestyle="--", color="#64748b", linewidth=1.0, label="Identidade (y = x)")

    elif spec.plot_type == PlotType.HEATMAP:
        if spec.series:
            mat = np.array([list(s.y_values) for s in spec.series], dtype=float)
            im = ax.imshow(mat, cmap="YlOrRd", aspect="auto")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            ax.set_yticks(np.arange(len(spec.series)))
            ax.set_yticklabels([s.name for s in spec.series], fontsize=8.5)
            x_lbls = spec.series[0].x_values
            ax.set_xticks(np.arange(len(x_lbls)))
            ax.set_xticklabels([str(x) for x in x_lbls], rotation=35, ha="right", fontsize=8.5)

    elif spec.plot_type == PlotType.LINE_LEARNING:
        for s_idx, s in enumerate(spec.series):
            xs = [float(v) for v in s.x_values] if all(isinstance(v, (int, float)) for v in s.x_values) else np.arange(len(s.y_values), dtype=float)
            ys = np.array(s.y_values, dtype=float)
            col = palette[s_idx % len(palette)]
            ax.plot(xs, ys, marker="o", color=col, linewidth=1.6, label=s.name)
            if s.y_err is not None:
                err = np.array(s.y_err, dtype=float)
                ax.fill_between(xs, ys - err, ys + err, color=col, alpha=0.18)

    ax.grid(True, linestyle="--", alpha=0.35, color="#9ca3af")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel(spec.x_label, fontsize=9.5)
    ax.set_ylabel(spec.y_label, fontsize=9.5)

    full_title = f"{spec.title}\n{spec.subtitle}" if spec.subtitle else spec.title
    ax.set_title(full_title, fontsize=11, fontweight="bold", loc="left", pad=10)

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, frameon=True, fontsize=8.2, loc="best")

    if spec.notes:
        note_txt = "Nota: " + "; ".join(spec.notes[:2])
        fig.text(0.01, 0.01, note_txt, fontsize=7.5, color="#6b7280")

    fig.tight_layout(rect=(0.0, 0.03 if spec.notes else 0.0, 1.0, 1.0))
    return fig


def render_figure(plot_spec: PlotSpecification, fmt: str = "svg") -> bytes:
    """Render PlotSpecification deterministically to 'svg', 'png' (300 DPI), or 'pdf' (REP-04, AD-033)."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm not in ("svg", "png", "pdf"):
        raise ConfigurationError(f"Unsupported figure format '{fmt}'; expected 'svg', 'png', or 'pdf'.")

    import matplotlib.pyplot as plt

    fig = _draw_matplotlib_figure(plot_spec)
    buf = io.BytesIO()
    try:
        if fmt_norm == "svg":
            fig.savefig(buf, format="svg", bbox_inches="tight", facecolor="white", metadata={"Date": None, "Creator": "experimental-ml-framework"})
            svg_text = buf.getvalue().decode("utf-8")
            idx = svg_text.find("<svg ")
            return (svg_text[idx:] if idx >= 0 else svg_text).encode("utf-8")
        if fmt_norm == "png":
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight", facecolor="white", metadata={"Software": "experimental-ml-framework"})
            return _ensure_png_300dpi_phys(buf.getvalue())
        fig.savefig(buf, format="pdf", bbox_inches="tight", facecolor="white", metadata={"CreationDate": None, "Creator": "experimental-ml-framework"})
        return buf.getvalue()
    finally:
        plt.close(fig)


def _norm_ppf_approx(p: np.ndarray) -> np.ndarray:
    """Acklam rational approximation for standard normal inverse CDF (pure NumPy)."""
    a = (-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02, 1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00)
    b = (-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01, -1.328068155288572e01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00, -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00)
    p_low, p_high = 0.02425, 1.0 - 0.02425
    out = np.empty_like(p, dtype=np.float64)
    for idx, val in enumerate(p):
        if val < p_low:
            q = math.sqrt(-2.0 * math.log(val))
            out[idx] = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
        elif val <= p_high:
            q = val - 0.5
            r = q * q
            out[idx] = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1.0)
        else:
            q = math.sqrt(-2.0 * math.log(1.0 - val))
            out[idx] = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    return out


def render_residuals_diagnostic_figure(oof_diagnostics: dict[str, Any], fmt: str = "png") -> bytes:
    """Render dual-panel OOF Residuals vs. Predicted and Normal Q-Q Plot in PNG/SVG/PDF (VAL-ENH-006)."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm not in ("svg", "png", "pdf"):
        raise ConfigurationError(f"Unsupported figure format '{fmt}'; expected 'svg', 'png', or 'pdf'.")

    configs = oof_diagnostics.get("configurations", [])
    target_cfg = next((c for c in configs if c.get("residuals") and c.get("y_pred")), None)
    if target_cfg is None:
        raise ConfigurationError("OOF residuals diagnostic payload does not contain 'y_pred' and 'residuals'.")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["svg.hashsalt"] = "experimental-ml-framework"
    y_pred = np.asarray(target_cfg["y_pred"], dtype=np.float64)
    res = np.asarray(target_cfg["residuals"], dtype=np.float64)
    mask = np.isfinite(y_pred) & np.isfinite(res)
    y_pred, res = y_pred[mask], res[mask]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.4))
    ax1.scatter(y_pred, res, s=28, color="#2563eb", alpha=0.75, edgecolor="#1e293b", linewidth=0.35)
    ax1.axhline(0.0, color="#dc2626", linestyle="--", linewidth=1.1)
    ax1.set_title("Resíduos OOF vs. Predito", fontsize=10.5, fontweight="bold", loc="left")
    ax1.set_xlabel("Valor Predito", fontsize=9)
    ax1.set_ylabel("Resíduo (y - ŷ)", fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.35)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    n = len(res)
    sorted_res = np.sort(res)
    probs = (np.arange(1, n + 1, dtype=np.float64) - 0.5) / float(n)
    theo_q = _norm_ppf_approx(probs)
    mu_r, std_r = float(np.mean(sorted_res)), max(float(np.std(sorted_res, ddof=1)), 1e-12)
    ax2.scatter(theo_q, sorted_res, s=28, color="#059669", alpha=0.75, edgecolor="#1e293b", linewidth=0.35)
    ax2.plot([theo_q[0], theo_q[-1]], [mu_r + std_r * theo_q[0], mu_r + std_r * theo_q[-1]], color="#dc2626", linestyle="--", linewidth=1.1, label="Referência Normal")
    ax2.set_title("Q-Q Plot Normal (Resíduos OOF)", fontsize=10.5, fontweight="bold", loc="left")
    ax2.set_xlabel("Quantis Teóricos N(0, 1)", fontsize=9)
    ax2.set_ylabel("Quantis Amostrais dos Resíduos", fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.35)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.legend(fontsize=8, frameon=True)

    cfg_lbl = f"{target_cfg.get('model_id', '')}/{target_cfg.get('scenario_id', '')}"
    lill_p = float(target_cfg.get("lilliefors_p", float("nan")))
    pref = str(target_cfg.get("preferred_family", "N/A"))
    fig.suptitle(f"Diagnóstico de Resíduos OOF — {cfg_lbl} (Lilliefors p={lill_p:.4f} | AIC: {pref})", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))

    buf = io.BytesIO()
    try:
        if fmt_norm == "svg":
            fig.savefig(buf, format="svg", bbox_inches="tight", facecolor="white", metadata={"Date": None, "Creator": "experimental-ml-framework"})
            svg_text = buf.getvalue().decode("utf-8")
            idx = svg_text.find("<svg ")
            return (svg_text[idx:] if idx >= 0 else svg_text).encode("utf-8")
        if fmt_norm == "png":
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight", facecolor="white", metadata={"Software": "experimental-ml-framework"})
            return _ensure_png_300dpi_phys(buf.getvalue())
        fig.savefig(buf, format="pdf", bbox_inches="tight", facecolor="white", metadata={"CreationDate": None, "Creator": "experimental-ml-framework"})
        return buf.getvalue()
    finally:
        plt.close(fig)
