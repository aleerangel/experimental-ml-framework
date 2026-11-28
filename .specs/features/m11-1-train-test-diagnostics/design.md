# Design — M11.1: Avaliação em Treino (`train_metrics`) e Comparação Treino vs. Teste

- **Feature**: `m11-1-train-test-diagnostics`
- **Spec**: [`spec.md`](./spec.md)
- **Decision**: `AD-038`

---

## 1. Fluxo e Invariantes Anti-Leakage

1. **Opt-in explícito (`collect_train_metrics: bool = False`)**:
   - Padrão `False` em `execute_single_cell`, `run_experiment_matrix`, `run_experiment` e CLI (`--collect-train-metrics`).
   - Quando `True`, imediatamente após `fit_model(...)` (ou com instância já preparada em `requires_fit=False`) dentro de `execute_single_cell`, executa `predict_model(...)` sobre `X_train_sel` e computa o mesmo conjunto de métricas sobre `(y_train, y_pred_train, y_proba_train)`.
2. **Isolamento estrito da inferência `DEV_CV`**:
   - `CellResultRecord.train_metrics` nunca é lido por `consolidate_matrix_oof`, `run_statistical_comparisons`, `compute_pareto_frontier` ou `synthesize_conclusions`.
   - `consolidate_descriptive` agrega `train_metrics` de células `DEV_CV` concluídas em `ConfigurationSummary.aggregated_train_metrics`, usando a mesma lógica estatística de `aggregated_metrics` (sem alterar `aggregated_metrics` nem `fold_metrics`).
3. **Retrocompatibilidade**:
   - `orchestration/storage.py` e `statistics/storage.py` usam `.get("train_metrics", {})` e `.get("aggregated_train_metrics", {})` na desserialização JSON.
4. **Apresentação (Etapa 6)**:
   - `reporting/tables.py`: se qualquer configuração selecionada tiver `summary.aggregated_train_metrics` não vazio, Tabela D inclui `TableColumn("train_mean", "Train Mean", ColumnAlignment.RIGHT, "{:.4f}")`.
   - `reporting/figures.py`: se houver `aggregated_train_metrics` válidos, Figura D (`BAR_COMPARISON`) adiciona a série `Treino (DEV_CV)` antes de `Validação/Teste (DEV_CV)` (e `Holdout`, se presente).
