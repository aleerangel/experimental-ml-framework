# M10 — Redesenho do Subsistema de Visualização Científica e Relatórios (Specification — Draft)

- **Status**: Draft — Pending Architectural & Developer Approval (Fase TLC: **Specify / Proposta Preliminar com Revisão de ADR**)
- **Milestone**: `M10` (`m10-scientific-visualization-reporting-redesign`)
- **Related Validation Findings**: `VAL-BUG-006`, `VAL-QUAL-001`, `VAL-QUAL-002`, `VAL-ENH-001`

---

## Problem Statement

A camada de apresentação visual e documental das Etapas 2 e 6 apresenta limitações estruturais decorrentes da construção manual de rasterizadores bitmap e streams PDF/SVG crus sem biblioteca gráfica especializada:

1. **Falhas nos renderizadores da Etapa 6 (`VAL-BUG-006`):**
   - `_render_png_300dpi` (`reporting/figures.py:L253-302`) não renderiza nenhum texto (gera apenas retângulos mudos sem título, sem rótulos de eixo e sem escala numérica);
   - `_render_pdf` (`L305-356`) ignora `plot_type` e intervalos de confiança (`y_err`), desenhando apenas barras verticais azuis inclusive para gráficos de dispersão `PAIRED_DIFF_CI` e `PARETO_TRADEOFF`;
   - `_render_svg` (`L193-245`) plota a coordenada horizontal do gráfico de Pareto usando o índice da lista `i` em vez do valor numérico `s.x_values[i]`, omite escala numérica no eixo Y, omite a linha $y=0$ em `PAIRED_DIFF_CI` e não exibe legenda;
   - As Famílias A, B, C e G geram apenas um gráfico dummy de 1 barra (`"total_configs"`), e `SCATTER_PARITY`, `HEATMAP` e `LINE_LEARNING` não são gerados.
2. **Limitações tipográficas nos PNGs da Etapa 2 (`VAL-QUAL-001`):**
   - `features/visualization.py` usa uma fonte bitmap 5×7 sem anti-aliasing que remove toda a acentuação da língua portuguesa (`_to_ascii_label`), trunca nomes de atributos com mais de 25 caracteres na margem esquerda e sobrepõe cabeçalhos verticais longos à barra de cores no heatmap de redundância.
3. **Incompletude das Tabelas B e C e idioma misto no relatório consolidado (`VAL-QUAL-002`):**
   - A Tabela B exibe `n_features = 0` para cenários `DYNAMIC` e omite estratégia e justificativa científica; a Tabela C exibe `"N/A"` fixo em `Task Type` e omite hiperparâmetros e pré-processamento; e `report.md`/`report.html` são gerados em inglês sem glossário estatístico.

## Goals

- [ ] Desacoplar a preparação de dados visuais (`VisualDataModel` / `FigureSpec` em Python + NumPy puro) do backend de renderização gráfica (`MatplotlibRenderer` com backend headless `Agg`).
- [ ] Produzir figuras científicas de qualidade de publicação acadêmica e consistentes nos três formatos exigidos (`PNG 300 DPI`, `SVG`, `PDF`) tanto na Etapa 2 quanto na Etapa 6, com suporte completo a UTF-8 e acentuação em português.
- [ ] Implementar gráficos reais para todas as famílias relevantes da Etapa 6: comparação de desempenho com IC 95% de Nadeau-Bengio (Família D), diferenças pareadas com IC e linha de referência $y=0$ (Família E), fronteira de Pareto 2D em coordenadas numéricas reais (Família F), paridade predito vs. observado / resíduos e diagnósticos de importância de atributos / coeficientes (Família G).
- [ ] Enriquecer as Tabelas B e C com todos os metadados declarados e padronizar `report.md` e `report.html` em português com glossário interpretativo das colunas estatísticas.

---

## Architectural Decision Review Required (Before Closing Specify)

Conforme a regra 2.2 e a análise detalhada na Seção 3 de `docs/engenharia_software/ROADMAP_EVOLUCAO.md`, este marco requer a deliberação do desenvolvedor sobre a revisão controlada do requisito transversal `XCUT-02`:

1. **[Decisão Arquitetural AD-M10-01 — Uso de `matplotlib` na camada de visualização]:**
   - **Proposta:** Manter `core`, `metrics`, `data`, `features/stats`, `features/selection`, `models`, `tuning`, `validation`, `orchestration` e `statistics` **100% restritos à biblioteca padrão do Python e ao NumPy/SciPy**, e autorizar `matplotlib` exclusivamente nos módulos de renderização visual (`features/visualization.py` e `reporting/figures.py`).
   - Você aprova adicionar `matplotlib>=3.7` como dependência da camada de visualização (ou como extra `[viz]` com fallback SVG corrigido)?
2. **[Decisão Arquitetural AD-M10-02 — Uso de `pandas` na camada de apresentação tabular]:**
   - **Proposta:** Manter as estruturas internas de domínio imutáveis (`tuple`, `@dataclass(frozen=True)`, `np.ndarray`) sem `pandas` no pipeline de execução, utilizando `pandas` apenas como utilitário de borda/apresentação (`ExperimentRunSummary.to_dataframe()` e conversão opcional de `TableModel.to_dataframe()` para inspeção em notebooks Jupyter).
   - Você prefere manter `pandas` apenas como dependência opcional de apresentação em notebooks ou integrá-lo também à formatação interna de `reporting/tables.py`?
3. **[Decisão D3 — Idioma do Relatório Consolidado (`report.md` / `report.html`)]:**
   - Confirmar a padronização de `report.md` e `report.html` em **português (`pt-BR`)** (alinhando com `exploratory_features.md` da Etapa 2 e com `ExperimentRunSummary.summary()`), incluindo uma seção de glossário estatístico ao final do relatório.

---

## Preliminary Requirements (EARS Notation)

### R1 — Separação entre Modelo Visual Puro e Backend de Renderização (`VAL-ENH-001`)
- **THE SYSTEM SHALL** construir todas as séries numéricas, coordenadas $(x, y)$, intervalos de confiança, ordenações e rótulos de figuras em funções puras baseadas exclusivamente em tipos nativos do Python e `numpy.ndarray`, entregando objetos imutáveis `FigureSpec` ao backend de renderização.

### R2 — Fidelidade Gráfica e Tipográfica nos Formatos PNG (300 DPI), SVG e PDF (`VAL-BUG-006`, `VAL-QUAL-001`)
- **WHEN** `export_figure` ou `export_exploratory_pngs` renderiza uma figura nos formatos `PNG`, `SVG` ou `PDF`, **THE SYSTEM SHALL** incluir título, subtítulo/metadados, rótulos de eixos com acentuação UTF-8 em português, marcas numéricas de escala em ambos os eixos, barras de erro (`y_err`/`x_err`) quando presentes e legenda sem truncamento nem sobreposição de textos.
- **WHEN** `PlotType.PARETO_TRADEOFF` é renderizado, **THE SYSTEM SHALL** posicionar cada configuração nas coordenadas numéricas exatas `(x_value, y_value)` dos dois objetivos avaliados e destacar visualmente a fronteira Pareto-ótima das configurações dominadas.
- **WHEN** `PlotType.PAIRED_DIFF_CI` é renderizado, **THE SYSTEM SHALL** desenhar a linha de referência de equivalência ($\Delta = 0$) e os intervalos de confiança de cada comparação pareada.

### R3 — Completude das Tabelas B e C e Relatório em Português com Glossário (`VAL-QUAL-002`)
- **WHEN** `build_table_model(ReportFamily.B_FEATURE_SCENARIOS, loaded_data)` é executado, **THE SYSTEM SHALL** exibir `Scenario ID`, `Mode` (`FIXED`/`DYNAMIC`), `Strategy`, `Candidate/Selected Count`, `Parameters` e `Scientific Justification`.
- **WHEN** `build_table_model(ReportFamily.C_MODELS_CONFIG, loaded_data)` é executado, **THE SYSTEM SHALL** exibir `Model ID`, `Display Name`, `Family`, `Execution Mode`, `Preprocessing (L1/L2)`, `Tuning Strategy` e `Hyperparameters`.
- **WHEN** `generate_consolidated_report` gera `report.md` e `report.html`, **THE SYSTEM SHALL** redigir os títulos, seções e notas interpretativas em português e incluir um glossário explicativo das métricas e testes estatísticos reportados.
