# M11.1 — Avaliação em Treino (`train_metrics`) e Comparação Treino vs. Teste Verification

**HEAD**: 33ffe60
**Verdict**: PASS

---

## Checks

| Check | Status | Test | Verdict & Notes |
| :--- | :--- | :--- | :--- |
| C1 | PASS | `tests/unit/orchestration/test_cell_execution.py::test_m11_1_train_metrics_opt_in_and_storage` | Valida `collect_train_metrics=False` como opt-in estrito por padrão em `execute_single_cell`, `run_experiment_matrix`, `resume_experiment_matrix`, `run_experiment` e CLI (`--collect-train-metrics` em `quickrun` e `run start`), mantendo `CellResultRecord.train_metrics` vazio sem avaliação extra. Quando `collect_train_metrics=True`, confirma avaliação sobre `X_train_proc` (`n_samples == len(fold.train_ids)`), round-trip JSON via `cell_result_to_dict`/`cell_result_from_dict` e retrocompatibilidade quando a chave `train_metrics` está ausente. Sem mocks ou asserções relaxadas. |
| C2 | PASS | `tests/unit/statistics/test_consolidation.py::test_m11_1_train_metrics_consolidated_isolated_from_dev_cv` | Valida consolidação isolada de `train_metrics` em `ConfigurationSummary.aggregated_train_metrics` via `_aggregate_metrics_attr("train_metrics")` em `consolidate_descriptive`, sem alterar `aggregated_metrics`, `fold_metrics`, `pooled_oof_metrics`, `holdout_metrics` ou testes pareados (`run_statistical_comparisons` não referencia `train_metrics` nem `aggregated_train_metrics`). Verifica round-trip JSON em `_consolidation_to_dict`/`_consolidation_from_dict` e retrocompatibilidade na ausência de `aggregated_train_metrics`. Sem mocks ou asserções relaxadas. |
| C3 | PASS | `tests/integration/reporting/test_m11_1_train_test_e2e.py::test_m11_1_e2e_train_vs_test_table_and_figure` | Executa fluxo E2E via `run_experiment`: confirma que com `collect_train_metrics=False` (padrão) a coluna `train_mean` não aparece na Tabela D, e que com `collect_train_metrics=True` a Tabela D exibe `Train Mean` (`train_mean`) em todas as linhas e em `report.md`, enquanto a Figura D (`BAR_COMPARISON`) inclui a série `<metric> (Treino)` ao lado de `<metric> (DEV_CV)` e renderiza assinaturas válidas em `PNG`, `SVG` e `PDF`. Documentação em `docs/guia/03_interpretando_resultados.md` alinhada ao comportamento opt-in. |

---

## Findings

none

---

## Walk

- **Especificação e Artefatos TLC**:
  - `.specs/features/m11-1-train-test-diagnostics/spec.md` (linhas 1–70)
  - `.specs/features/m11-1-train-test-diagnostics/design.md` (linhas 1–21)
  - `.specs/features/m11-1-train-test-diagnostics/tasks.md` (linhas 1–88)
  - `.specs/features/m11-1-train-test-diagnostics/proofs.md` (linhas 1–49)
- **C1**:
  - Teste: `tests/unit/orchestration/test_cell_execution.py` (linhas 383–422)
  - Implementação: `src/experimental_ml/orchestration/types.py` (linhas 174, 210–215), `src/experimental_ml/orchestration/codecs.py` (linhas 166–168, 188, 205–207, 225), `src/experimental_ml/orchestration/execution.py` (linhas 174, 409–417, 468), `src/experimental_ml/orchestration/engine.py` (linhas 102, 194, 284, 430), `src/experimental_ml/pipeline.py` (linhas 230, 335), `src/experimental_ml/cli/main.py` (linhas 97–101, 204–208), `src/experimental_ml/cli/cmd_run.py` (linha 111), `src/experimental_ml/cli/cmd_init.py` (linha 249)
- **C2**:
  - Teste: `tests/unit/statistics/test_consolidation.py` (linhas 383–415)
  - Implementação: `src/experimental_ml/statistics/types.py` (linhas 109, 140–145), `src/experimental_ml/statistics/consolidation.py` (linhas 193–259, 335), `src/experimental_ml/statistics/storage.py` (linhas 261–263, 306–308)
- **C3**:
  - Teste: `tests/integration/reporting/test_m11_1_train_test_e2e.py` (linhas 30–82)
  - Implementação: `src/experimental_ml/reporting/tables.py` (linhas 259–278, 308–314), `src/experimental_ml/reporting/figures.py` (linhas 68–103), `docs/guia/03_interpretando_resultados.md` (linhas 68–75)
