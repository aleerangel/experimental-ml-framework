# Guia de Aceite do Consumidor — Marco M7.2 (Figuras Determinísticas e Relatório Completo)

> **Documento de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M7.2 (`m7-2-figures-full-report`)  
> **Público-alvo:** Pesquisador / Usuário consumidor da API pública `experimental_ml.reporting`

---

## 1. Interfaces Públicas Validadas

- **Figuras (`REP-04`, `XCUT-02`)**: `build_figure_spec`, `render_figure` (`svg`, `png` 300 DPI, `pdf` 1.4).
- **Relatório Completo (`REP-05`, `RNF03`)**: `ResearcherDeclarations`, `render_full_report` (`markdown`, `html` autocontido com CSS embutido).

---

## 2. Roteiro de Validação sob a Perspectiva do Consumidor

1. **Gerar Especificação e Renderizar Figuras**:
   ```python
   from experimental_ml.reporting import ReportFamily, build_figure_spec, render_figure

   fig_spec = build_figure_spec(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded, metric_name="rmse")
   svg_bytes = render_figure(fig_spec, "svg")
   png_bytes = render_figure(fig_spec, "png")
   pdf_bytes = render_figure(fig_spec, "pdf")
   ```
   *Resultado esperado:* Bytes determinísticos sem dependência de `matplotlib`/`pillow`.

2. **Compor Relatório Científico Completo**:
   ```python
   from experimental_ml.reporting import ResearcherDeclarations, render_full_report

   decl = ResearcherDeclarations(scientific_objective="Avaliar generalização.")
   md_report = render_full_report(loaded, fmt="markdown", declarations=decl)
   html_report = render_full_report(loaded, fmt="html", declarations=decl)
   ```
   *Resultado esperado:* Três seções explícitas (Declarações do Pesquisador, Fatos Computacionais Registrados, Interpretações Derivadas e Condicionadas), sem exposição de `*_hash` e HTML 100% offline.
