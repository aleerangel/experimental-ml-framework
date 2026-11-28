"""Full scientific report composer in Markdown and self-contained HTML (REP-05, RNF03, CA-E6-01, CA-E6-02, AD-036)."""

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
@page { size: A4 portrait; margin: 15mm; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1.25rem; color: #1f2937; line-height: 1.6; }
h1, h2, h3 { color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3rem; }
table { border-collapse: collapse; width: 100%; margin: 0.8rem 0 1.2rem 0; font-size: 0.92rem; }
th, td { border: 1px solid #d1d5db; padding: 0.45rem 0.65rem; }
th { background: #f3f4f6; font-weight: 600; }
.caption { font-size: 0.88rem; color: #4b5563; margin: 0.2rem 0 0.5rem 0; }
.table-notes { font-size: 0.84rem; color: #6b7280; margin: -0.6rem 0 1.1rem 0; }
.box { background: #f9fafb; border-left: 4px solid #2563eb; padding: 0.8rem 1rem; margin: 1rem 0; }
.caveat { background: #fffbeb; border-left: 4px solid #d97706; padding: 0.8rem 1rem; margin: 1rem 0; }
figure.figure-card { margin: 1rem 0 1.5rem 0; padding: 0.7rem; border: 1px solid #e5e7eb; background: #ffffff; text-align: center; }
figure.figure-card img { max-width: 100%; height: auto; display: block; margin: 0 auto; }
figure.figure-card figcaption { font-size: 0.85rem; color: #4b5563; margin-top: 0.45rem; }
@media print {
  body { margin: 0; padding: 0; max-width: none; font-size: 10.5pt; }
  table, figure.figure-card, .box, .caveat { break-inside: avoid; page-break-inside: avoid; }
  h1, h2 { break-after: avoid; page-break-after: avoid; }
}
""".strip()


_GLOSSARY_ITEMS: tuple[tuple[str, str], ...] = (
    ("Média (Mean) e Desvio Padrão (SD)", "Tendência central e dispersão amostral entre os folds válidos de desenvolvimento (DEV_CV)."),
    ("Mediana (Median) e IIQ (IQR)", "Medidas robustas de tendência central e dispersão interquartílica (Q75 - Q25) menos sensíveis a valores extremos."),
    ("Cobertura (Coverage)", "Proporção de folds planejados concluídos com sucesso para uma configuração (modelo x cenário)."),
    ("Holdout (FINAL_HOLDOUT)", "Avaliação final sobre a partição reservada holdout_ids, isolada das estatísticas descritivas e testes pareados de DEV_CV."),
    ("Teste t de Nadeau-Bengio", "Teste pareado com correção de variância para sobreposição de conjuntos de treino em validação cruzada."),
    ("Teste de Wilcoxon Pareado", "Teste não-paramétrico pareado sobre as diferenças por fold entre duas configurações."),
    ("Ajuste p_adj (Holm / BH)", "Valores-p ajustados para múltiplas comparações controlando FWER (Holm) ou FDR (Benjamini-Hochberg)."),
    ("Tamanho de Efeito (Cohen d_z)", "Magnitude padronizada da diferença pareada entre configurações."),
    ("Fronteira de Pareto", "Conjunto de configurações não dominadas considerando simultaneamente desempenho preditivo e custo computacional/estabilidade."),
    ("Estabilidade (Jaccard)", "Similaridade média de Jaccard entre conjuntos de atributos selecionados em diferentes folds (cenários dinâmicos)."),
)


def _render_html_table(table: TableModel) -> str:
    parts = [f"<h3>{html.escape(table.title)}</h3>"]
    if table.caption:
        parts.append(f"<p class=\"caption\">{html.escape(table.caption)}</p>")
    parts.extend(["<table>", "<thead><tr>"])
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
    if table.notes:
        parts.append("<ul class=\"table-notes\">")
        for note in table.notes:
            parts.append(f"<li>{html.escape(note)}</li>")
        parts.append("</ul>")
    return "\n".join(parts)


def render_full_report(
    loaded_data: LoadedExperimentData,
    fmt: str = "markdown",
    selection: ReportContentSelection | None = None,
    declarations: ResearcherDeclarations | None = None,
    figure_paths: Sequence[str] = (),
) -> str:
    """Render complete scientific report into 'markdown' or self-contained 'html' in pt-BR (REP-05, RNF03, AD-036)."""
    fmt_norm = fmt.strip().lower()
    if fmt_norm not in ("markdown", "html"):
        raise ConfigurationError(f"Unsupported report format '{fmt}'; expected 'markdown' or 'html'.")

    sel = select_report_content(loaded_data, selection)
    tables = tuple(build_table_model(fam, loaded_data, sel) for fam in sel.families)
    conc = loaded_data.statistics.conclusion
    suit = loaded_data.statistics.suitability

    if fmt_norm == "markdown":
        lines: list[str] = [
            f"# Relatório Científico Experimental — {loaded_data.experiment_id}",
            "",
            f"- **Experimento:** `{loaded_data.experiment_id}`",
            f"- **Plano de Particionamento:** `{loaded_data.partition_plan_id}`",
            f"- **Regime de Avaliação:** `{suit.evaluation_regime.value}` ($J = {suit.total_development_partitions}$)",
            "",
            "## 1. Declarações do Pesquisador (Proveniência Declarada)",
            "",
        ]
        if declarations is None:
            lines.append("_Nenhuma declaração explícita do pesquisador foi fornecida._")
        else:
            if declarations.scientific_objective:
                lines.append(f"- **Objetivo Científico:** {declarations.scientific_objective}")
            if declarations.data_origin_note:
                lines.append(f"- **Origem dos Dados:** {declarations.data_origin_note}")
            if declarations.metric_rationale:
                lines.append(f"- **Justificativa da Métrica:** {declarations.metric_rationale}")
            for note in declarations.additional_notes:
                lines.append(f"- **Nota:** {note}")

        lines.extend(["", "## 2. Fatos Computacionais Registrados", ""])
        for tbl in tables:
            lines.append(render_table_markdown(tbl))
        if loaded_data.ks_drift_report:
            dr = loaded_data.ks_drift_report
            lines.extend([
                f"### Diagnóstico de Dataset Shift (KS 2 Amostras: {dr.get('reference_label')} vs. {dr.get('comparison_label')})",
                "",
                "| Variável | Tipo | D_KS | p-valor | Drift Detectado |",
                "| :--- | :--- | ---: | ---: | :---: |",
            ])
            for feat in dr.get("features", ()):
                d_s = f"{feat['ks_statistic']:.4f}" if feat.get("ks_statistic") is not None else "N/A"
                p_s = f"{feat['p_value']:.4f}" if feat.get("p_value") is not None else "N/A"
                tipo = "Alvo" if feat.get("is_target") else "Atributo"
                lines.append(f"| {feat['feature_name']} | {tipo} | {d_s} | {p_s} | {'Sim' if feat.get('drift_detected') else 'Não'} |")
            lines.append("")
        if loaded_data.oof_residuals_diagnostics:
            lines.extend([
                "### Diagnóstico de Resíduos OOF (Lilliefors & Normal vs. Student-t)",
                "",
                "| Configuração | n | Lilliefors D | Lilliefors p | AIC Normal | AIC Student-t | Preferida |",
                "| :--- | ---: | ---: | ---: | ---: | ---: | :---: |",
            ])
            for cfg in loaded_data.oof_residuals_diagnostics.get("configurations", ()):
                lines.append(
                    f"| {cfg['model_id']}/{cfg['scenario_id']} | {cfg['n_samples']} | {cfg['lilliefors_d']:.4f} | "
                    f"{cfg['lilliefors_p']:.4f} | {cfg['normal_aic']:.2f} | {cfg['student_t_aic']:.2f} | {cfg['preferred_family']} |"
                )
            lines.append("")
        if figure_paths:
            lines.extend(["### Figuras Científicas", ""])
            for fp in figure_paths:
                if fp.lower().endswith((".png", ".svg")):
                    lines.append(f"![Figura — {fp}]({fp})")
                else:
                    lines.append(f"- `{fp}`")
            lines.append("")

        lines.extend([
            "## 3. Interpretações Derivadas e Condicionadas",
            "",
            f"- **Métrica Primária:** `{conc.primary_metric}`",
            f"- **Líder Observado:** `{conc.observed_leader}`",
            f"- **Evidência Estatística:** {conc.statistical_evidence_status}",
            f"- **Magnitude do Efeito:** {conc.effect_magnitude_summary}",
            f"- **Relevância Prática:** {conc.practical_relevance_status}",
            f"- **Trade-off Custo e Pareto:** {conc.cost_tradeoff_summary}",
            "",
            "### Síntese Narrativa",
            "",
            conc.narrative_text,
            "",
        ])
        if conc.methodological_caveats:
            lines.extend(["### Ressalvas Metodológicas", ""])
            for cav in conc.methodological_caveats:
                lines.append(f"- {cav}")
            lines.append("")

        lines.extend(["## 4. Glossário Estatístico", ""])
        for term, desc in _GLOSSARY_ITEMS:
            lines.append(f"- **{term}:** {desc}")
        lines.append("")

        return "\n".join(lines)

    # Self-contained offline HTML in pt-BR
    parts = [
        "<!DOCTYPE html>",
        "<html lang=\"pt-BR\">",
        "<head>",
        "<meta charset=\"utf-8\">",
        f"<title>Relatório Científico — {html.escape(loaded_data.experiment_id)}</title>",
        f"<style>{_EMBEDDED_CSS}</style>",
        "</head>",
        "<body>",
        f"<h1>Relatório Científico Experimental — {html.escape(loaded_data.experiment_id)}</h1>",
        f"<p><strong>Plano de Particionamento:</strong> <code>{html.escape(loaded_data.partition_plan_id)}</code> | "
        f"<strong>Regime:</strong> <code>{html.escape(suit.evaluation_regime.value)}</code> (J = {suit.total_development_partitions})</p>",
        "<h2>1. Declarações do Pesquisador (Proveniência Declarada)</h2>",
        "<div class=\"box\">",
    ]
    if declarations is None:
        parts.append("<p><em>Nenhuma declaração explícita do pesquisador foi fornecida.</em></p>")
    else:
        if declarations.scientific_objective:
            parts.append(f"<p><strong>Objetivo Científico:</strong> {html.escape(declarations.scientific_objective)}</p>")
        if declarations.data_origin_note:
            parts.append(f"<p><strong>Origem dos Dados:</strong> {html.escape(declarations.data_origin_note)}</p>")
        if declarations.metric_rationale:
            parts.append(f"<p><strong>Justificativa da Métrica:</strong> {html.escape(declarations.metric_rationale)}</p>")
        for note in declarations.additional_notes:
            parts.append(f"<p><strong>Nota:</strong> {html.escape(note)}</p>")
    parts.append("</div>")

    parts.append("<h2>2. Fatos Computacionais Registrados</h2>")
    for tbl in tables:
        parts.append(_render_html_table(tbl))
    if loaded_data.ks_drift_report:
        dr = loaded_data.ks_drift_report
        parts.append(f"<h3>Diagnóstico de Dataset Shift (KS 2 Amostras: {html.escape(str(dr.get('reference_label')))} vs. {html.escape(str(dr.get('comparison_label')))})</h3>")
        parts.append("<table><thead><tr><th>Variável</th><th>Tipo</th><th>D_KS</th><th>p-valor</th><th>Drift</th></tr></thead><tbody>")
        for feat in dr.get("features", ()):
            d_s = f"{feat['ks_statistic']:.4f}" if feat.get("ks_statistic") is not None else "N/A"
            p_s = f"{feat['p_value']:.4f}" if feat.get("p_value") is not None else "N/A"
            tipo = "Alvo" if feat.get("is_target") else "Atributo"
            parts.append(f"<tr><td>{html.escape(str(feat['feature_name']))}</td><td>{tipo}</td><td>{d_s}</td><td>{p_s}</td><td>{'Sim' if feat.get('drift_detected') else 'Não'}</td></tr>")
        parts.append("</tbody></table>")
    if loaded_data.oof_residuals_diagnostics:
        parts.append("<h3>Diagnóstico de Resíduos OOF (Lilliefors &amp; Normal vs. Student-t)</h3>")
        parts.append("<table><thead><tr><th>Configuração</th><th>n</th><th>Lilliefors D</th><th>Lilliefors p</th><th>AIC Normal</th><th>AIC Student-t</th><th>Preferida</th></tr></thead><tbody>")
        for cfg in loaded_data.oof_residuals_diagnostics.get("configurations", ()):
            parts.append(
                f"<tr><td>{html.escape(str(cfg['model_id']))}/{html.escape(str(cfg['scenario_id']))}</td>"
                f"<td>{cfg['n_samples']}</td><td>{cfg['lilliefors_d']:.4f}</td><td>{cfg['lilliefors_p']:.4f}</td>"
                f"<td>{cfg['normal_aic']:.2f}</td><td>{cfg['student_t_aic']:.2f}</td><td>{html.escape(str(cfg['preferred_family']))}</td></tr>"
            )
        parts.append("</tbody></table>")
    if figure_paths:
        parts.append("<h3>Figuras Científicas</h3>")
        for fp in figure_paths:
            esc_fp = html.escape(fp)
            if fp.lower().endswith((".png", ".svg")):
                parts.append(
                    f"<figure class=\"figure-card\"><img src=\"{esc_fp}\" alt=\"{esc_fp}\">"
                    f"<figcaption><code>{esc_fp}</code></figcaption></figure>"
                )
            else:
                parts.append(f"<p><code>{esc_fp}</code></p>")

    parts.extend([
        "<h2>3. Interpretações Derivadas e Condicionadas</h2>",
        f"<p><strong>Métrica Primária:</strong> <code>{html.escape(conc.primary_metric)}</code></p>",
        f"<p><strong>Líder Observado:</strong> <code>{html.escape(str(conc.observed_leader))}</code></p>",
        f"<p><strong>Evidência Estatística:</strong> {html.escape(conc.statistical_evidence_status)}</p>",
        f"<p><strong>Magnitude do Efeito:</strong> {html.escape(conc.effect_magnitude_summary)}</p>",
        f"<p><strong>Relevância Prática:</strong> {html.escape(conc.practical_relevance_status)}</p>",
        f"<p><strong>Trade-off Custo e Pareto:</strong> {html.escape(conc.cost_tradeoff_summary)}</p>",
        f"<div class=\"box\"><p>{html.escape(conc.narrative_text)}</p></div>",
    ])
    if conc.methodological_caveats:
        parts.append("<div class=\"caveat\"><strong>Ressalvas Metodológicas:</strong><ul>")
        for cav in conc.methodological_caveats:
            parts.append(f"<li>{html.escape(cav)}</li>")
        parts.append("</ul></div>")

    parts.append("<h2>4. Glossário Estatístico</h2><ul>")
    for term, desc in _GLOSSARY_ITEMS:
        parts.append(f"<li><strong>{html.escape(term)}:</strong> {html.escape(desc)}</li>")
    parts.append("</ul>")

    parts.extend(["</body>", "</html>"])
    return "\n".join(parts) + "\n"
