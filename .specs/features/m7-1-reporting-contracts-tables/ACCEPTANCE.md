# Guia de Aceite do Consumidor — Marco M7.1 (Contratos, Leitura e Tabelas das 7 Famílias)

> **Documento de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M7.1 (`m7-1-reporting-contracts-tables`)  
> **Público-alvo:** Pesquisador / Usuário consumidor da API pública `experimental_ml.reporting`

---

## 1. Interfaces Públicas Validadas

- **Contratos Imutáveis (`REP-01`)**: `ReportFamily` (A–G), `ReportAudience`, `PlotType`, `ColumnAlignment`, `ArtifactProvenance`, `ReportContentSelection`, `TableColumn`, `TableModel`, `PlotSeries`, `PlotSpecification`, `LoadedExperimentData`.
- **Carregamento Somente-Leitura (`REP-02`)**: `load_experiment_artifacts_readonly`, `select_report_content`.
- **Tabelas e Renderizadores (`REP-03`)**: `build_table_model`, `render_table_csv`, `render_table_markdown`, `render_table_latex`.

---

## 2. Roteiro de Validação sob a Perspectiva do Consumidor

1. **Carregar Experimento Somente-Leitura e Filtrar Conteúdo**:
   ```python
   from experimental_ml.reporting import (
       ReportAudience,
       ReportContentSelection,
       load_experiment_artifacts_readonly,
       select_report_content,
   )

   loaded = load_experiment_artifacts_readonly("caminho/do/experimento")
   sel = select_report_content(loaded, ReportContentSelection(audience=ReportAudience.ARTICLE_COMPACT))
   ```
   *Resultado esperado:* Portão Stage 5 validado e artefatos carregados sem invocar ajuste ou predição de modelos (`CA-E6-01`).

2. **Construir e Renderizar Tabelas das 7 Famílias (A–G)**:
   ```python
   from experimental_ml.reporting import (
       ReportFamily,
       build_table_model,
       render_table_csv,
       render_table_latex,
       render_table_markdown,
   )

   tbl = build_table_model(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded, sel)
   csv_txt = render_table_csv(tbl)
   md_txt = render_table_markdown(tbl)
   tex_txt = render_table_latex(tbl)
   ```
   *Resultado esperado:* Paridade numérica exata com `statistics/*.json`, distinção entre `"N/A"`, `"UNDEFINED_NAN"` e `"Inf"`/`"-Inf"`, ausência de campos `*_hash` e código LaTeX `booktabs` pronto para compilação.
