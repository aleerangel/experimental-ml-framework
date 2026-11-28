# Resultados de Homologação — Submarco M11.4: Fechamento Onda 1 (`VAL-ENH-004`, `VAL-QUAL-004`, Desempenho)

- **Submarco:** `M11.4` (`m11-4-wave1-polish`)
- **Branch:** `feat/m11-4-wave1-polish`
- **Status:** `VERIFICADO (PASS)` (Aguardando aceite do consumidor em `ACCEPTANCE.md` e merge em `main`)
- **Suíte de Testes:** `651 passed in 85.91s` (`.venv/bin/pytest tests/ -q`)
- **Verificador Independente:** [`verification.md`](./verification.md) — `C1`–`C3` aprovados (`PASS`, `13 passed in 2.28s`)

---

## Resumo das Entregas (`T1`–`T3`)

1. **T1 (`e22b431`)**: `run_experiment` em `src/experimental_ml/pipeline.py` passa a aceitar `comparison_scope`, `planned_pairs` e `pareto_objectives` mantendo `ALL_PAIRWISE` e `(primary_metric, fit_mean_s)` como padrão.
2. **T2 (`47d7448`)**: Cache intra-célula (`inner_fold_cache` por `fold_idx`) em `src/experimental_ml/tuning/engine.py` e suporte opt-in a `execution_backend="process"` (`ProcessPoolExecutor` + `_rebuild_mapping_proxy`) em `src/experimental_ml/orchestration/engine.py`.
3. **T3 (`5ebc6ec`)**: Sincronização de `docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md`, `docs/referencia/api_python.md` e atualização de `VAL-ENH-004` / `VAL-QUAL-004` em `REGISTRO_DE_VALIDACAO_DO_MVP.md`.
