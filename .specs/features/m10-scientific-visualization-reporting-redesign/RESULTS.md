# Resultados de Homologação — Marco M10: Redesenho do Subsistema de Visualização Científica e Relatórios

- **Marco:** `M10` (`m10-scientific-visualization-reporting-redesign`)
- **Branch:** `feat/m10-visualization-reporting`
- **Status:** `VERIFICADO (PASS)` (Aguardando aceite do consumidor em `ACCEPTANCE.md` e merge em `main`)
- **Suíte de Testes:** `632 passed in 66.10s` (`.venv/bin/pytest tests/ -q`)
- **Verificador Independente:** [`verification.md`](./verification.md) — `C1`–`C5` aprovados (`PASS`)

---

## Resumo das Entregas (`T1`–`T6`)

1. **T1 (`5fc348c`)**: Adicionados `matplotlib>=3.7.0` e `pandas>=2.0.0` em `pyproject.toml`, com revisão controlada de `XCUT-02` e auditoria AST em `test_mvp_audit_invariants.py`.
2. **T2 (`a935d27`)**: Preparação tabular com Pandas em `reporting/tables.py` retornando `TableModel` imutável, metadados completos nas Tabelas B e C, filtro `model_ids`/`scenario_ids` na Tabela E, agregação numérica na Tabela G e `table_to_dataframe`.
3. **T3 (`79a806e`)**: Gráficos exploratórios da Etapa 2 (`features/visualization.py`) migrados para Matplotlib (`Agg`) com suporte completo a UTF-8 em português e ajuste automático de margens.
4. **T4 (`36c795d`)**: Reestruturação de `reporting/figures.py` com Matplotlib (`PNG 300 DPI`, `SVG`, `PDF`), `PARETO_TRADEOFF` em `(x, y)` real, `PAIRED_DIFF_CI` com `y = 0`, `SCATTER_PARITY`, `HEATMAP`, `LINE_LEARNING` e diagnósticos da Família G.
5. **T5 (`e0fcab8`)**: Padronização de `report.md` e `report.html` em `pt-BR` (`<html lang="pt-BR">`), figuras embutidas, `@media print` e Glossário Estatístico.
6. **T6 (`decf35b`)**: Alinhamento de `pipeline.py` (`run_experiment`) e `cli/cmd_report.py` gerando artefatos visuais das Etapas 2 e 6 vinculados ao relatório final.
