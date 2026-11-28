# Resultados de Homologação — Submarco M11.1: Avaliação em Treino (`train_metrics`)

- **Submarco:** `M11.1` (`m11-1-train-test-diagnostics`)
- **Branch:** `feat/m11-1-train-test-diagnostics`
- **Status:** `VERIFICADO (PASS)` (Aguardando aceite do consumidor em `ACCEPTANCE.md` e merge em `main`)
- **Suíte de Testes:** `637 passed in 77.42s` (`.venv/bin/pytest tests/ -q`)
- **Verificador Independente:** [`verification.md`](./verification.md) — `C1`–`C3` aprovados (`PASS`)

---

## Resumo das Entregas (`T1`–`T4`)

1. **T1 (`e0bc947`)**: `CellResultRecord.train_metrics` com coleta opt-in `collect_train_metrics: bool = False` em `execute_single_cell`, `run_experiment_matrix` e `resume_experiment_matrix`, com round-trip JSON retrocompatível.
2. **T2 (`52c8576`)**: `ConfigurationSummary.aggregated_train_metrics` consolidado isoladamente em `consolidate_descriptive` e persistido em JSON sem alterar `aggregated_metrics`, OOF ou testes pareados `DEV_CV`.
3. **T3 (`f4bec8e`)**: Coluna `Train Mean` (`train_mean`) na Tabela D e série `(Treino)` na Figura D renderizada em `PNG`, `SVG` e `PDF`.
4. **T4 (`33ffe60`)**: Exposição explícita em `run_experiment(..., collect_train_metrics=False)`, CLI (`--collect-train-metrics`), documentação em `03_interpretando_resultados.md` e teste E2E.
