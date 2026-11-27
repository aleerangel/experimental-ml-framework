# M10 — Redesenho do Subsistema de Visualização Científica e Relatórios

- **Status**: Approved (`AD-033`, `AD-034`, `AD-035`, `AD-036`) — Fase TLC: **Specify**
**Approved**: 2026-11-27 - user: "Pode"
- **Milestone**: `M10` (`m10-scientific-visualization-reporting-redesign`)
- **Branch**: `feat/m10-visualization-reporting`
- **Related Validation Findings**: `VAL-BUG-006`, `VAL-QUAL-001`, `VAL-QUAL-002`, `VAL-ENH-001`

---

## Problem Statement

A auditoria técnica da camada de visualização e relatórios identificou limitações estruturais decorrentes da construção manual de rasterizadores bitmap e streams PDF/SVG crus, além de acoplamentos e lacunas nas tabelas e relatórios:

1. **Falhas nos renderizadores e especificação de figuras da Etapa 6 (`reporting/figures.py`, `VAL-BUG-006`):**
   - `SCATTER_PARITY`, `HEATMAP` e `LINE_LEARNING` existem em `PlotType`, mas nunca são instanciados nem renderizados;
   - Em `PARETO_TRADEOFF`, `SVG`, `PNG` e `PDF` ignoram `s.x_values` e posicionam pontos pelo índice sequencial `0..n-1`, sem rótulos de configuração;
   - `_render_png_300dpi` não renderiza texto (sem título, eixos, ticks ou legenda);
   - `_render_pdf` desenha apenas barras azuis, ignorando `PAIRED_DIFF_CI`, `PARETO_TRADEOFF`, `y_err` e símbolos Unicode (`latin-1`);
   - `_render_svg` omite escala numérica no eixo Y, legenda e linha de referência `y=0`, causando sobreposição de rótulos horizontais no eixo X;
   - Famílias A, B, C e G caem em fallback de 1 barra dummy (`"total_configs"`), e não há gráficos de distribuição de folds, paridade/resíduos ou importâncias/diagnósticos.
2. **Limitações tipográficas nos PNGs da Etapa 2 (`features/visualization.py`, `VAL-QUAL-001`):**
   - Fonte bitmap 5×7 manual remove toda a acentuação em português (`_to_ascii_label`), trunca nomes com mais de 24 caracteres e sofre colisões de layout no heatmap.
3. **Lacunas nas Tabelas A–G (`reporting/tables.py`, `VAL-QUAL-002`):**
   - Tabela B reporta `n_features = 0` em cenários `DYNAMIC` e omite estratégia/parâmetros/justificativa;
   - Tabela C exibe `"N/A"` em `Task Type` e omite capacidades, pré-processamento e hiperparâmetros;
   - Tabela E não filtra por `sel.model_ids`/`sel.scenario_ids`;
   - Tabela G colapsa listas de importâncias/coeficientes por fold em string truncada.
4. **Relatório consolidado e integração com `pipeline.py` (`reporting/report.py`, `VAL-QUAL-002`):**
   - `report.md` e `report.html` são gerados em inglês (`<html lang="en">`), listam `figure_paths` apenas como texto sem embutir imagens, não possuem `@media print` nem glossário estatístico;
   - `pipeline.py` gera apenas `exploratory_features.md` (sem PNGs/HTML) e `report.{md,html}` sem figuras/tabelas exportadas.

---

## Architectural Decisions (`AD-033` a `AD-036`)

1. **`AD-033` (`matplotlib>=3.7` na camada visual)**: Autorizar `matplotlib>=3.7` (backend headless `Agg` via lazy import) exclusivamente em `src/experimental_ml/features/visualization.py` e `src/experimental_ml/reporting/figures.py`. Todo o núcleo científico/estatístico permanece 100% Python stdlib + NumPy.
2. **`AD-034` (`pandas>=2.0` restrito à preparação tabular)**: Manter `LoadedExperimentData`, `TableModel`, `PlotSpecification` e entidades do núcleo 100% livres de `pd.DataFrame`. Permitir `pandas` exclusivamente dentro de `reporting/tables.py` (lazy import) para organização, junção, ordenação, agregação de diagnósticos por fold e preparação tabular, convertendo de volta para `TableModel` imutável, além de utilitário opcional `to_dataframe()` na borda.
3. **`AD-035` (Dependências obrigatórias + revisão controlada de `XCUT-02`)**: Declarar `matplotlib>=3.7.0` e `pandas>=2.0.0` em `project.dependencies` no `pyproject.toml`, mantendo lazy imports para preservar `CLI-10` e atualizando os testes de invariantes AST (`test_mvp_audit_invariants.py`, `test_m71..m73`, `test_run_e2e.py`) para permitir `matplotlib`/`pandas` exclusivamente nos módulos autorizados.
4. **`AD-036` (Idioma `pt-BR`, glossário e escopo)**: Padronizar `report.md` e `report.html` em português (`pt-BR`) com figuras embutidas e glossário estatístico; manter `VAL-ENH-005` (Treino vs. Teste / `train_metrics`) fora do escopo do `M10`.

---

## Requirements (EARS Notation)

### M10-01 — Revisão Controlada de `XCUT-02` e Dependências (`AD-033`, `AD-034`, `AD-035`)
- **THE SYSTEM SHALL** declarar `matplotlib>=3.7.0` e `pandas>=2.0.0` em `pyproject.toml` e manter os módulos de núcleo (`core`, `metrics`, `data`, `features/stats`, `features/selection`, `models`, `tuning`, `validation`, `orchestration`, `statistics`) e contratos (`reporting/types.py`) 100% livres de `matplotlib` e `pandas` em runtime, com imports tardios nos módulos autorizados (`reporting/tables.py`, `reporting/figures.py`, `features/visualization.py`).

### M10-02 — Separação Domínio → Preparação Visual → Renderização e Contratos (`VAL-ENH-001`)
- **THE SYSTEM SHALL** construir todas as séries numéricas, coordenadas reais `(x, y)`, rótulos de pontos, intervalos de confiança e metadados visuais em funções puras Python/NumPy retornando objetos imutáveis `PlotSpecification` / `PlotSeries` (sem `matplotlib`/`pandas` em `reporting/types.py`), delegando exclusivamente a renderização ao backend Matplotlib (`Agg`).

### M10-03 — Gráficos Científicos da Etapa 6 em `PNG 300 DPI`, `SVG` e `PDF` (`VAL-BUG-006`)
- **WHEN** `build_figure_spec` e `render_figure` processam as famílias da Etapa 6 nos formatos `PNG`, `SVG` e `PDF`, **THE SYSTEM SHALL** renderizar título, subtítulo, rótulos de eixos com acentuação UTF-8, marcas numéricas em ambos os eixos, legenda sem sobreposição e:
  - **Família D**: comparação de desempenho com barras de erro/IC e, quando houver predições OOF disponíveis, gráfico de paridade/resíduos (`SCATTER_PARITY`);
  - **Família E**: diferenças pareadas com IC (`PAIRED_DIFF_CI`) e linha de referência `y = 0`;
  - **Família F**: fronteira de Pareto 2D (`PARETO_TRADEOFF`) usando as coordenadas numéricas reais `x_values` e `y_values` e identificando os pontos de Pareto;
  - **Família G**: diagnósticos reais de modelo (ex.: importâncias de atributos agregadas por fold via `HEATMAP` ou `BAR_COMPARISON`) quando presentes em `cell_diagnostics`.

### M10-04 — Gráficos Exploratórios da Etapa 2 com Matplotlib (`VAL-QUAL-001`)
- **WHEN** `render_exploratory_target_chart` e `render_exploratory_redundancy_heatmap` geram imagens da Etapa 2, **THE SYSTEM SHALL** usar Matplotlib (`Agg`) com suporte completo a UTF-8 em português, ajuste automático de margens para nomes longos sem truncamento e barra de cores com escala explícita no heatmap.

### M10-05 — Preparação Tabular com Pandas e Enriquecimento das Tabelas A–G (`VAL-QUAL-002`, `AD-034`)
- **WHEN** `build_table_model` constrói as Tabelas A–G em `reporting/tables.py`, **THE SYSTEM SHALL** usar `pandas` internamente (sem expor `pd.DataFrame` no retorno `TableModel`) para organizar, filtrar e agregar os dados, exibindo metadados completos na Tabela B (`mode`, `strategy`, `n_features`/`candidates`, `scientific_justification`), Tabela C (`family`, `task_type`/`capabilities`, `preprocessing`, `tuning`), filtragem por `model_ids`/`scenario_ids` na Tabela E e agregação numérica por atributo/fold na Tabela G.

### M10-06 — Relatório Consolidado em Português, Glossário e Integração no `pipeline.py` (`VAL-QUAL-002`, `AD-036`)
- **WHEN** `render_full_report` gera `report.md` e `report.html`, **THE SYSTEM SHALL** redigir todo o documento em português (`pt-BR`, `<html lang="pt-BR">`), embutir as figuras geradas por seção, incluir CSS `@media print` no HTML e adicionar uma seção de **Glossário Estatístico** explicando as métricas e testes reportados.
- **WHEN** `run_experiment` executa o pipeline completo em `pipeline.py`, **THE SYSTEM SHALL** gerar também os artefatos visuais da Etapa 2 (`exploratory_features.html` e PNGs) e o pacote/figuras da Etapa 6 vinculadas ao relatório final.

---

## Out of Scope
- Avaliação de erro em treino (`train_metrics`) e comparação Treino vs. Teste (`VAL-ENH-005`), reservados para marco posterior.
- Alteração de fórmulas estatísticas da Etapa 5 ou contratos de execução das Etapas 1–4.

---

## User Stories

1. **Como pesquisador**, quero que os gráficos da Etapa 2 (`exploratory_features`) e da Etapa 6 (`PNG 300 DPI`, `SVG`, `PDF`) tenham qualidade de publicação acadêmica, com acentuação em português, escalas numéricas, legendas, coordenadas 2D reais no Pareto, linha de referência no gráfico de diferenças pareadas e diagnósticos visuais reais, para interpretá-los diretamente em artigos e relatórios.
2. **Como pesquisador**, quero que as Tabelas B, C, E e G exibam todos os metadados declarados, filtragem consistente e agregações numéricas reais de importância/diagnósticos, além de um relatório consolidado (`report.md` e `report.html`) em português com figuras embutidas e glossário estatístico.
3. **Como mantenedor do framework**, quero que o núcleo científico (`core` até `statistics`) permaneça 100% independente de `pandas` e `matplotlib`, restringindo `pandas` à preparação tabular interna (`reporting/tables.py`) e `matplotlib` à renderização visual (`features/visualization.py` e `reporting/figures.py`).

---

## Assumptions & Open Questions

### Assumptions
- `matplotlib>=3.7.0` (com backend headless `Agg`) e `pandas>=2.0.0` estarão instalados como dependências do pacote (`pyproject.toml`) e importados sob demanda (lazy import) para preservar o tempo de startup da CLI (`CLI-10`).
- Todos os contratos públicos de domínio (`LoadedExperimentData`, `TableModel`, `PlotSpecification`, `PlotSeries`) permanecem imutáveis e livres de tipos de `pandas` ou `matplotlib`.

### Open Questions
Open questions: none (`AD-033`, `AD-034`, `AD-035` e `AD-036` aprovadas pelo desenvolvedor em 2026-11-27).

---

## Requirement Traceability

| Requisito | Achado / Origem | Critério de Aceite / Prova |
| :--- | :--- | :--- |
| M10-01 | `AD-033`, `AD-034`, `AD-035` (`XCUT-02`) | `C1`: Auditoria AST confirma `matplotlib` apenas em `features/visualization.py` e `reporting/figures.py`, e `pandas` apenas em `reporting/tables.py` (+ `to_dataframe()`), com núcleo puro |
| M10-02 | `VAL-ENH-001` | `C2`: `PlotSpecification` / `PlotSeries` puros com rótulos, direção e séries reais sem objetos Matplotlib/Pandas |
| M10-03 | `VAL-BUG-006` | `C2`: Gráficos da Etapa 6 (`PNG`, `SVG`, `PDF`) renderizam texto UTF-8, ticks, legendas, `PARETO_TRADEOFF` em `(x, y)` real, `PAIRED_DIFF_CI` com `y=0`, `SCATTER_PARITY` e diagnósticos G |
| M10-04 | `VAL-QUAL-001` | `C3`: Gráficos exploratórios da Etapa 2 (`render_exploratory_target_chart`, `render_exploratory_redundancy_heatmap`) via Matplotlib com acentuação UTF-8 e sem truncamento |
| M10-05 | `VAL-QUAL-002`, `AD-034` | `C4`: Tabelas A–G preparadas com Pandas internamente e convertidas para `TableModel` imutável, com metadados completos em B/C, filtro em E e agregação numérica em G |
| M10-06 | `VAL-QUAL-002`, `AD-036` | `C5`: `report.md` e `report.html` em `pt-BR` com figuras embutidas, `@media print`, glossário estatístico e geração integrada no `pipeline.py` |
