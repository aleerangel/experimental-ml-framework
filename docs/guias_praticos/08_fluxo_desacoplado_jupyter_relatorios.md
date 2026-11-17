# Guia Prático 8: Fluxo Desacoplado para Jupyter Notebooks e Relatórios sem Retreino

## Contexto Científico

Em experimentos computacionalmente pesados (como busca aninhada de hiperparâmetros ou circuitos quânticos simulados), é comum executar a matriz experimental (Etapa 4) em um servidor ou terminal via CLI e, posteriormente, explorar resultados, reconfigurar comparações estatísticas (Etapa 5) e gerar tabelas LaTeX ou figuras vetoriais (Etapa 6) interativamente em um **Jupyter Notebook** local.

Graças ao **desacoplamento entre execução e relato**, a camada `experimental_ml.reporting` lê os artefatos persistidos em modo estritamente somente-leitura, sem jamais retreinar modelos ou recalcular métricas de forma oculta.

---

## Padrão em 2 Fases

### Fase 1: Execução em Lote no Servidor (CLI)

```bash
expml run start --exp-dir exp_servidor --metrics accuracy f1 roc_auc --outer-n-jobs 4
expml stats run --exp-dir exp_servidor --primary-metric accuracy
```

### Fase 2: Exploração Interativa e Exportação em Notebook (Somente-Leitura)

```python
# conceptual
from experimental_ml.reporting import (
    ReportAudience,
    ReportContentSelection,
    ReportFamily,
    build_figure_spec,
    build_table_model,
    load_experiment_artifacts_readonly,
    render_figure,
    render_table_latex,
    select_report_content,
)

# 1. Carregamento imutável dos artefatos persistidos (Etapas 1 a 5)
loaded = load_experiment_artifacts_readonly("exp_servidor")

# 2. Filtragem de famílias de interesse para o artigo (ex.: desempenho e comparações)
selection = select_report_content(
    loaded,
    ReportContentSelection(
        audience=ReportAudience.SCIENTIFIC_PAPER,
        families=(
            ReportFamily.D_PREDICTIVE_PERFORMANCE,
            ReportFamily.E_STATISTICAL_COMPARISONS,
        ),
    ),
)

# 3. Geração de tabela LaTeX booktabs e figura SVG sem retreinar nenhum modelo
tabela_perf = build_table_model(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded, selection)
codigo_latex = render_table_latex(tabela_perf)

spec_fig = build_figure_spec(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded, selection)
svg_bytes = render_figure(spec_fig, fmt="svg")
```

---

## Garantias de Integridade

- **Paridade Numérica:** Os números exibidos nas tabelas `CSV`, `Markdown` e `LaTeX` são exatamente os valores consolidados na Etapa 5, preservando a semântica de `UNDEFINED_NAN` e `CoverageStatus`.
- **Zero Dependências Externas (`XCUT-02`):** Mesmo a renderização de gráficos em `SVG`, `PNG` e `PDF` ocorre nativamente em Python/NumPy puro, sem exigir Matplotlib ou LaTeX instalado no ambiente de execução.
