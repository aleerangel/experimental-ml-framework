# M11.1 — Avaliação em Treino (`train_metrics`) e Comparação Treino vs. Teste

- **Status**: Approved (`AD-038`) — Fase TLC: **Specify**
**Approved**: 2026-11-28 - user: "aprovado"
- **Milestone**: `M11.1` (`m11-1-train-test-diagnostics`)
- **Branch**: `feat/m11-1-train-test-diagnostics`
- **Related Validation Finding**: `VAL-ENH-005`

---

## Problem Statement

Atualmente, `execute_single_cell` (`src/experimental_ml/orchestration/execution.py`) avalia as métricas do estimador apenas sobre a partição de validação/teste (`X_val`, `y_val`), gravando `metrics` em `CellResultRecord`. Não há registro de desempenho em treino (`train_metrics`), impossibilitando que o pesquisador diagnostique *overfitting* (erro de treino muito baixo e erro de teste alto) ou *underfitting* (ambos altos) diretamente nas tabelas e gráficos da Etapa 6.

---

## Architectural Decision (`AD-038`)

- Nenhum cálculo ou coleta adicional ocorre de forma oculta: `collect_train_metrics: bool = False` é **opt-in explícito** em `execute_single_cell`, `run_experiment_matrix`, `run_experiment` e CLI (`--collect-train-metrics`), documentado como opção recomendada quando o pesquisador deseja diagnosticar *overfitting* / *underfitting*.
- Quando ativado pelo pesquisador, `train_metrics` é mantido **estritamente isolado** de `aggregated_metrics`, OOF e dos testes estatísticos pareados (`Nadeau-Bengio` / `Wilcoxon`) de `DEV_CV`.

---

## Requirements (EARS Notation)

### M111-01 — Coleta Explícita (Opt-In) e Persistência de `train_metrics` (`orchestration`, `pipeline`, `cli`)
- **WHEN** o pesquisador ativa explicitamente `collect_train_metrics=True` (ou `--collect-train-metrics` na CLI; padrão `False`), **THE SYSTEM SHALL** avaliar após `fit_model` as mesmas métricas configuradas sobre `(X_train_sel, y_train)` e persistir em `CellResultRecord.train_metrics` (inclusive em `runs/cells/cell_*.json`, preservando retrocompatibilidade para JSONs antigos sem `train_metrics`).
- **WHEN** `collect_train_metrics=False` (padrão), **THE SYSTEM SHALL NOT** executar avaliação extra sobre `X_train` e manterá `CellResultRecord.train_metrics` vazio.

### M111-02 — Consolidação Descritiva Isolada de `train_metrics` (`statistics`)
- **WHEN** `consolidate_descriptive` consolida células `DEV_CV`, **THE SYSTEM SHALL** agregar `train_metrics` separadamente em `ConfigurationSummary.aggregated_train_metrics` (e persistir em `descriptive_consolidation.json`), **WITHOUT** alterar `aggregated_metrics`, `fold_metrics`, `pooled_oof_metrics` ou os testes inferenciais pareados (`run_statistical_comparisons`).

### M111-03 — Comparação Tabular e Visual Treino vs. Teste (`reporting`)
- **WHEN** `build_table_model(ReportFamily.D_PREDICTIVE_PERFORMANCE, ...)` é executado e `aggregated_train_metrics` está presente, **THE SYSTEM SHALL** incluir a coluna `Train Mean` (`train_mean`) ao lado de `Mean` (validação/teste) na Tabela D.
- **WHEN** `build_figure_spec(ReportFamily.D_PREDICTIVE_PERFORMANCE, ...)` é executado e `aggregated_train_metrics` está presente, **THE SYSTEM SHALL** incluir a série `Treino (DEV_CV)` ao lado de `Validação/Teste (DEV_CV)` (e `Holdout`, se presente) no gráfico comparativo de desempenho, renderizando em `PNG`, `SVG` e `PDF` via Matplotlib.

---

## Out of Scope
- Teste KS, detecção de *dataset shift* e Q-Q Plot de resíduos (`VAL-ENH-006` / `M11.2`).
- Caracterização estatística ampliada e `dataset_meta_features` (`VAL-ENH-007` / `M11.3`).
- Múltiplos objetivos de Pareto / `planned_pairs` via CLI (`VAL-ENH-004` / `M11.4`).

---

## User Stories

1. **Como pesquisador**, quero visualizar `Train Mean` ao lado de `Mean` (validação/teste) na Tabela D e no gráfico da Família D para diagnosticar rapidamente *overfitting* e *underfitting* entre famílias de modelos.
2. **Como mantenedor**, quero garantir que `train_metrics` nunca contamine as comparações estatísticas pareadas nem quebre o carregamento de experimentos antigos gravados sem esse campo.

---

## Assumptions & Open Questions

### Assumptions
- Modelos analíticos (`requires_fit=False`) também permitem `predict_model` sobre `X_train` após o estágio de pré-processamento da célula.
- `EvaluationScope` ou marcação das métricas de treino preserva compatibilidade com `MetricValue` e `save_statistics_artifacts`.

### Open Questions
Open questions: none (`AD-038` revisada com opt-in explícito conforme diretriz do desenvolvedor em 2026-11-28).

---

## Requirement Traceability

| Requisito | Origem | Critério de Verificação |
| :--- | :--- | :--- |
| M111-01 | `VAL-ENH-005`, `AD-038` | `C1`: `collect_train_metrics=False` por padrão não avalia treino; quando `True`, `CellResultRecord.train_metrics` é preenchido e serializado com retrocompatibilidade |
| M111-02 | `VAL-ENH-005`, `AD-038` | `C2`: `ConfigurationSummary.aggregated_train_metrics` consolidado e isolado dos testes pareados `DEV_CV` |
| M111-03 | `VAL-ENH-005`, `AD-038` | `C3`: Tabela D exibe `Train Mean` e Figura D plota barras comparativas `Treino` vs. `DEV_CV` em `PNG`/`SVG`/`PDF` |
