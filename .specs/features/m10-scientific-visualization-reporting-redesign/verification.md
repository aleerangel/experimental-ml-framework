# M10 — Redesenho do Subsistema de Visualização Científica e Relatórios Verification

**HEAD**: decf35b
**Verdict**: PASS

---

## Checks

| Check | Status | Test | Verdict & Notes |
| :--- | :--- | :--- | :--- |
| C1 | PASS | `tests/integration/test_mvp_audit_invariants.py::test_audit_xcut02_runtime_purity_ast` e `tests/integration/test_profiling_integration.py::test_single_runtime_dependency_xcut_02` | Valida por inspeção AST que nenhum módulo de núcleo (`core`, `metrics`, `data`, `features/{stats,selection}`, `models`, `tuning`, `validation`, `orchestration`, `statistics`) nem contratos (`reporting/types.py`) importam `pandas` ou `matplotlib` em runtime; `matplotlib` restringe-se a `features/visualization.py` e `reporting/figures.py`, e `pandas` a `reporting/tables.py`, com `pyproject.toml` declarando exatamente `numpy`, `matplotlib` e `pandas`. |
| C2 | PASS | `tests/unit/reporting/test_reporting_figures.py::test_m10_figures_pareto_paired_parity_and_formats` | Valida que `PlotSpecification`/`PlotSeries` permanecem puros (sem objetos Matplotlib/Pandas), `PAIRED_DIFF_CI` usa `reference_y=0.0` e renderiza linha `Δ = 0` em SVG, `PARETO_TRADEOFF` preserva coordenadas numéricas reais (`float`) e `point_labels`, e `SCATTER_PARITY` renderiza corretamente em `SVG`, `PNG` (300 DPI) e `PDF` (`%PDF-1.4`). |
| C3 | PASS | `tests/unit/features/test_exploratory_visualization.py::test_m10_exploratory_charts_matplotlib_utf8` | Valida a separação preparação→renderização (`_prepare_target_chart_data`, `_prepare_redundancy_heatmap_data`) e a renderização via Matplotlib (`Agg`) em PNG válido com suporte a acentuação UTF-8 em português (`alvo_saúde`, `pressão_sistólica`) e nomes longos de atributos sem truncamento. |
| C4 | PASS | `tests/unit/reporting/test_reporting_tables.py::test_m10_tables_pandas_prep_and_enriched_metadata` | Valida preparação tabular interna com `pandas` retornando `TableModel` imutável (`MappingProxyType` nas linhas, sem `pd.DataFrame` no contrato), metadados enriquecidos nas Tabelas B (`mode`, `strategy`, `n_features`, `scientific_justification`) e C (`display_name`, `task_type`, `preprocessing`, `hyperparameters`), filtragem por `model_ids`/`scenario_ids` na Tabela E, agregação numérica por fold na Tabela G e conversão opcional de borda via `table_to_dataframe`. |
| C5 | PASS | `tests/integration/reporting/test_m10_reporting_e2e.py::test_m10_pipeline_e2e_ptbr_report_and_figures` | Executa `run_experiment` E2E com dataset real e dois modelos lineares, comprovando geração de `exploratory_target.png`, `exploratory_redundancy.png`, `exploratory_features.{md,html}` na Etapa 2 e figuras (`fig_family_d.png`, `fig_family_e.png`, `fig_family_f.png`) vinculadas ao `report.md` e `report.html` em `pt-BR` (`<html lang="pt-BR">`), com `@media print` e seção `4. Glossário Estatístico`. |

---

## Findings

none

---

## Walk

- **Especificação e Artefatos TLC**:
  - `.specs/features/m10-scientific-visualization-reporting-redesign/spec.md` (linhas 1–105)
  - `.specs/features/m10-scientific-visualization-reporting-redesign/design.md` (linhas 1–64)
  - `.specs/features/m10-scientific-visualization-reporting-redesign/tasks.md` (linhas 1–116)
  - `.specs/features/m10-scientific-visualization-reporting-redesign/proofs.md` (linhas 1–68)
- **C1**:
  - Configuração: `pyproject.toml` (linhas 24–28)
  - Testes: `tests/integration/test_mvp_audit_invariants.py` (linhas 18–110), `tests/integration/test_profiling_integration.py` (linhas 129–140)
- **C2**:
  - Implementação: `src/experimental_ml/reporting/types.py` (linhas 130–234), `src/experimental_ml/reporting/figures.py` (linhas 51–408)
  - Teste: `tests/unit/reporting/test_reporting_figures.py` (linhas 171–210)
- **C3**:
  - Implementação: `src/experimental_ml/features/visualization.py` (linhas 297–450)
  - Teste: `tests/unit/features/test_exploratory_visualization.py` (linhas 139–172)
- **C4**:
  - Implementação: `src/experimental_ml/reporting/tables.py` (linhas 90–447)
  - Teste: `tests/unit/reporting/test_reporting_tables.py` (linhas 305–390)
- **C5**:
  - Implementação: `src/experimental_ml/reporting/report.py` (linhas 23–228), `src/experimental_ml/pipeline.py` (linhas 518–558), `src/experimental_ml/cli/cmd_report.py` (linhas 55, 96)
  - Teste: `tests/integration/reporting/test_m10_reporting_e2e.py` (linhas 29–77)
