# Verificação Independente TLC — M11.4 (`m11-4-wave1-polish`)

- **Feature**: `m11-4-wave1-polish`
- **Veredito**: **PASS**
- **Data**: 2026-11-28
- **Suite executada**: `.venv/bin/pytest tests/unit/tuning/test_tuning_execution.py tests/unit/orchestration/test_matrix_engine_parallel.py tests/integration/reporting/test_m11_4_wave1_polish_e2e.py -q` → `13 passed in 2.28s`

---

## Checks

**C1** (`M114-01`, `VAL-ENH-004`) — `run_experiment` respeita `comparison_scope`, `planned_pairs` e `pareto_objectives` customizados preservando os padrões
- **Veredito**: **PASS**
- **Evidência de código**:
  - `src/experimental_ml/pipeline.py`: `run_experiment` expõe `comparison_scope: ComparisonScope = ComparisonScope.ALL_PAIRWISE`, `planned_pairs: Sequence[tuple[tuple[str, str], tuple[str, str]]] = ()` e `pareto_objectives: Sequence[ObjectiveSpec] | None = None`, repassando-os para `ComparisonSpec` e `MultiObjectiveSpec` (via `resolved_pareto_objs`), mantendo `ALL_PAIRWISE` e `(primary_metric, fit_mean_s)` quando omitidos.
- **Evidência de teste**: `tests/integration/reporting/test_m11_4_wave1_polish_e2e.py::test_m11_4_run_experiment_planned_pairs_and_pareto` (PASSED; valida `statistical_comparisons.json` restrito ao par planejado e `pareto_summary.json` com os objetivos configurados).

**C2** (`M114-02`, Categoria 5) — Cache intra-célula no Nested CV reduz recomputação mantendo resultado e `execution_backend="process"` executa via `ProcessPoolExecutor`
- **Veredito**: **PASS**
- **Evidência de código**:
  - `src/experimental_ml/tuning/engine.py`: `run_nested_tuning` mantém `inner_fold_cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}` indexado por `fold_idx`, armazenando e reutilizando `(X_in_train_trans, X_in_val_trans)` entre candidatos de hiperparâmetros para evitar recomputação de Camada 1, seleção dinâmica (`select_features_in_fold`) e Camada 2.
  - `src/experimental_ml/orchestration/engine.py`: `run_experiment_matrix` e `resume_experiment_matrix` aceitam `execution_backend: str = "thread"` (validando `"thread"` ou `"process"`), despachando células via `ProcessPoolExecutor(max_workers=outer_n_jobs)` com `_run_cell_in_subprocess` e suporte a serialização de `MappingProxyType` via `_rebuild_mapping_proxy` / `_reduce_mapping_proxy` registrados em `copyreg.pickle`, preservando a persistência via `save_cell_artifacts`.
- **Evidência de teste**: `tests/unit/tuning/test_tuning_execution.py::test_m11_4_nested_cv_caches_inner_fold_preprocessing` (PASSED; confirma `fit_calls == 3` para 3 candidatos × 3 sub-folds internos) e `tests/unit/orchestration/test_matrix_engine_parallel.py::test_m11_4_process_pool_backend` (PASSED; confirma 3/3 células concluídas com `outer_n_jobs=2` e `execution_backend="process"`).

**C3** (`M114-03`, `VAL-QUAL-004`) — `ARQUITETURA_E_CONTRATOS.md`, `api_python.md` e `REGISTRO_DE_VALIDACAO_DO_MVP.md` sincronizados sem regressão na suíte
- **Veredito**: **PASS**
- **Evidência de código**:
  - `docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md`: utiliza os regimes reais `CV_ONLY`, `HOLDOUT_ONLY` e `CV_AND_HOLDOUT` (sem `CROSS_VALIDATION_ONLY`).
  - `docs/referencia/api_python.md`: documenta os símbolos públicos introduzidos em `M8`–`M11.3` (incluindo `compute_vif`, `ks_2samp`, `build_dataset_meta_features` e `render_residuals_diagnostic_figure`).
  - `docs/engenharia_software/REGISTRO_DE_VALIDACAO_DO_MVP.md`: tabela-resumo atualizada com `VERIFICADO (M11.4)` para `VAL-QUAL-004` e `VAL-ENH-004`.
- **Evidência de teste**: `tests/integration/reporting/test_m11_4_wave1_polish_e2e.py::test_m11_4_docs_symbols_synced` (PASSED).
