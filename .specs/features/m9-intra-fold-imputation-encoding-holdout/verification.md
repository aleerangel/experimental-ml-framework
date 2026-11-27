# M9 — Imputação e Codificação Categórica Intra-Fold e Execução de Holdout Final Verification

**HEAD**: 31fefba
**Verdict**: PASS

---

## Checks

| Check | Status | Test | Verdict & Notes |
| :--- | :--- | :--- | :--- |
| C1 | PASS | `tests/unit/models/test_preprocessing_imputers.py::test_simple_imputer_mean_median_mode_and_all_missing` | Valida `SimpleImputer` nas estratégias `MEAN`, `MEDIAN` e `MODE` com valores extremos (`1e6`) e `NaN` em `X_val` sem afetar as estatísticas ajustadas estritamente em `X_train`, além de verificar lançamento de `DataIntegrityError` em coluna 100% ausente. Sem mocks ou asserções relaxadas. |
| C2 | PASS | `tests/unit/models/test_preprocessing_encoders.py::test_categorical_encoders_1to1_and_unseen_categories` | Valida `OrdinalCategoryEncoder` e `FrequencyCategoryEncoder` aprendendo mapeamentos exclusivamente em `X_train`, preservando shape 1:1 e `dtype=float64`, mantendo `None`/`NaN` como `NaN` para imputação posterior e mapeando categorias inéditas em `X_val` para `-1.0` e `0.0`, respectivamente. |
| C3 | PASS | `tests/integration/test_m9_deferred_preprocessing_e2e.py::test_deferred_missing_and_categorical_e2e_no_leakage` | Executa experimento E2E completo (Etapas 1 a 6 via `run_experiment`) com dataset real contendo `NaN` e coluna categórica em texto, regras `DEFER_INTRA_FOLD` (`MEDIAN`, `MODE`, `ORDINAL_ENCODER`), seleção dinâmica (`TOP_K_RELEVANCE`) e `GRID_SEARCH` (Nested CV, `inner_cv_folds=3`), comprovando `completed_cells == 6`, `failed_cells == 0` e geração de `report.md`/`report.html`. |
| C4 | PASS | `tests/unit/statistics/test_consolidation.py::test_final_holdout_isolated_from_dev_cv_consolidation` e `tests/unit/orchestration/test_matrix_builder.py::test_build_cell_matrix_cv_and_holdout_adds_final_holdout` | Valida criação de células `FINAL_HOLDOUT` (`cell_<m>__<s>__final_holdout`) sobre `(development_ids, holdout_ids)` sob `CV_AND_HOLDOUT`, isolamento estrito das estatísticas de `DEV_CV` (`mean`, `std`, `completed_folds`, `fold_metrics`) frente a métrica `99.0` do holdout, round-trip JSON de `holdout_metrics` e exibição na coluna `Holdout` (`holdout_mean`) da Tabela D. |

---

## Findings

none

---

## Walk

- **Especificação e Artefatos TLC**:
  - `.specs/features/m9-intra-fold-imputation-encoding-holdout/spec.md` (linhas 1–85)
  - `.specs/features/m9-intra-fold-imputation-encoding-holdout/design.md` (linhas 1–83)
  - `.specs/features/m9-intra-fold-imputation-encoding-holdout/tasks.md` (linhas 1–120)
  - `.specs/features/m9-intra-fold-imputation-encoding-holdout/proofs.md` (linhas 1–51)
- **C1**:
  - Teste: `tests/unit/models/test_preprocessing_imputers.py` (linhas 12–58)
  - Implementação: `src/experimental_ml/models/preprocessing/imputers.py` (linhas 37–133)
- **C2**:
  - Teste: `tests/unit/models/test_preprocessing_encoders.py` (linhas 15–61)
  - Implementação: `src/experimental_ml/models/preprocessing/encoders.py` (linhas 44–137)
- **C3**:
  - Teste: `tests/integration/test_m9_deferred_preprocessing_e2e.py` (linhas 50–144)
  - Implementação: `src/experimental_ml/models/preprocessing/pipeline.py` (linhas 45–329), `src/experimental_ml/orchestration/execution.py` (linhas 46–128, 187, 255–275), `src/experimental_ml/tuning/engine.py` (linhas 108–221)
- **C4**:
  - Testes: `tests/unit/statistics/test_consolidation.py` (linhas 330–380) e `tests/unit/orchestration/test_matrix_builder.py` (linhas 166–199)
  - Implementação: `src/experimental_ml/orchestration/matrix.py` (linhas 131–158), `src/experimental_ml/orchestration/oof.py` (linhas 570–576), `src/experimental_ml/orchestration/execution.py` (linhas 165–172), `src/experimental_ml/statistics/types.py` (linhas 110, 146–150), `src/experimental_ml/statistics/consolidation.py` (linhas 158–178, 312–336), `src/experimental_ml/statistics/storage.py` (linhas 264–266, 306–308), `src/experimental_ml/reporting/tables.py` (linhas 179–229)
