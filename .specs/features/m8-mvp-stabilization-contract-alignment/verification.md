# M8 — Estabilização do MVP e Alinhamento Contratual Verification

**HEAD**: a18cb82
**Verdict**: PASS

---

## Checks

| Check | Status | Test | Verdict & Notes |
| :--- | :--- | :--- | :--- |
| C1 | PASS | `tests/unit/reporting/test_reporting_tables.py::test_family_a_and_g_populated_from_real_artifacts` | Valida extração da Família A sobre `dataset_profile.json` no formato real (`n_rows`, `n_cols`, `columns`, `duplicate_rows`, `target`, `findings`, `summary`) com exclusão de hashes, e consolidação da Família G a partir de `runs/cells/*.json` (`diagnostics`). Falharia se a leitura aninhada ou de células fosse omitida. |
| C2 | PASS | `tests/unit/features/test_stats.py::test_categorical_stats_ignore_none_values` | Valida filtragem pairwise de `None` e `float("nan")` em arrays `dtype=object` tanto em `compute_correlation_ratio` quanto em `compute_cramers_v`, incluindo caso degenerado (`< 2` pares válidos retornando `UNDEFINED_NAN`). Falharia com `TypeError` ou status incorreto sem a filtragem. |
| C3 | PASS | `tests/unit/tuning/test_tuning_execution.py::test_nested_tuning_dynamic_selection_isolated_per_inner_fold` | Espiona `select_features_in_fold` durante `run_nested_tuning` (2 candidatos × 3 folds internos sobre 30 amostras externas) e comprova 6 execuções estritamente sobre 20 amostras (`inner_train`). Alinhado à Decisão `D1` (`AD-028`) e propagação em `split_inner_folds`. |
| C4 | PASS | `tests/unit/test_usability_cli_and_facade.py::test_run_experiment_cli_interoperability_and_seed_propagation` | Executa `run_experiment` duas vezes com `_SeedAwareRegressor(random_state=None)` e `master_seed=42`, verifica persistência de `sanitized_view.json`, `splits.csv.gz`, `splits.schema.json`, `pareto_summary.json` e `exploratory_features.json`, valida retorno `0` em `expml partition verify`, `expml run verify` e `expml report export`, e confirma determinismo. |
| C5 | PASS | `tests/unit/cli/test_cli_stats.py::test_cli_stats_kuncheva_and_multiobjective_pareto` | Executa `expml stats run` com `sanitized_view.json` (4 candidatas) e `stats_config.json` (2 objetivos em `pareto_objectives`), validando `mean_kuncheva == 1.0` ($\neq \text{None}$) e `len(pareto["objectives"]) == 2`. |
| C6 | PASS | `tests/unit/orchestration/test_matrix_resume.py::test_resume_rejects_modified_scenarios_or_models_hash` | Verifica geração de `scenarios_hash` e `models_hash` em `run_experiment_matrix` e rejeição com `DataIntegrityError` em `resume_experiment_matrix` quando `scenarios` ou `model_specs` são alterados. |
| C7 | PASS | `tests/unit/orchestration/test_cell_codecs.py::test_canonical_cell_filename_without_legacy_prefix` | Comprova gravação exclusiva em `cell_<m>__<s>__<f>.json` e `pred_<m>__<s>__<f>.json`, e que `load_cell_artifacts` lança `ConfigurationError` para arquivo legado `cell_cell_...`, cumprindo a Decisão `D2` (`AD-029`). |

---

## Findings

none

---

## Walk

- **Especificação e Artefatos TLC**:
  - `.specs/features/m8-mvp-stabilization-contract-alignment/spec.md` (linhas 1–124)
  - `.specs/features/m8-mvp-stabilization-contract-alignment/design.md` (linhas 1–100)
  - `.specs/features/m8-mvp-stabilization-contract-alignment/tasks.md` (linhas 1–137)
  - `.specs/features/m8-mvp-stabilization-contract-alignment/proofs.md` (linhas 1–59)
- **C1**:
  - Teste: `tests/unit/reporting/test_reporting_tables.py` (linhas 240–302)
  - Implementação: `src/experimental_ml/reporting/loader.py` (linhas 39–79) e `src/experimental_ml/reporting/tables.py` (linhas 100–146, 277–329)
- **C2**:
  - Teste: `tests/unit/features/test_stats.py` (linhas 157–182)
  - Implementação: `src/experimental_ml/features/stats.py` (linhas 114–243)
- **C3 (`D1` / `AD-028`)**:
  - Teste: `tests/unit/tuning/test_tuning_execution.py` (linhas 215–268)
  - Implementação: `src/experimental_ml/orchestration/execution.py` (linhas 120–244), `src/experimental_ml/tuning/engine.py` (linhas 40–235), `src/experimental_ml/tuning/partitioning.py` (linhas 12–110)
- **C4**:
  - Teste: `tests/unit/test_usability_cli_and_facade.py` (linhas 113–176)
  - Implementação: `src/experimental_ml/pipeline.py` (linhas 154–172, 345–420)
- **C5**:
  - Teste: `tests/unit/cli/test_cli_stats.py` (linhas 174–218)
  - Implementação: `src/experimental_ml/cli/cmd_stats.py` (linhas 71–87, 149–166) e `src/experimental_ml/pipeline.py` (linhas 345–380)
- **C6**:
  - Teste: `tests/unit/orchestration/test_matrix_resume.py` (linhas 484–535)
  - Implementação: `src/experimental_ml/orchestration/state.py` (linhas 38–39, 98–141) e `src/experimental_ml/orchestration/engine.py` (linhas 40–68, 330–340)
- **C7 (`D2` / `AD-029`)**:
  - Teste: `tests/unit/orchestration/test_cell_codecs.py` (linhas 231–247)
  - Implementação: `src/experimental_ml/orchestration/storage.py` (linhas 22–28, 63–114) e varredura `grep -rn "cell_cell_" src/ tests/` confirmando ausência de fallback legado em `src/`.
