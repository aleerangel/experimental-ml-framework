# M9 — Imputação e Codificação Categórica Intra-Fold e Execução de Holdout Final Tasks

**Spec**: `.specs/features/m9-intra-fold-imputation-encoding-holdout/spec.md`
**Design**: `.specs/features/m9-intra-fold-imputation-encoding-holdout/design.md`
**Status**: Approved
**Approved**: 2026-11-27 - user: "aprovado"

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `pyproject.toml`, `docs/engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Preprocessing (`models/preprocessing/`) | unit | 1:1 para `AC-M9-01`, `AC-M9-02` + anti-leakage + coluna 100% NaN | `tests/unit/models/test_preprocessing_*.py` | `.venv/bin/pytest tests/unit/models/ -q` |
| Orchestration (`orchestration/`, `tuning/`, `stages/`) | unit + integration | `AC-M9-03` (`DEFER_INTRA_FOLD` no CV e Nested CV) e `AC-M9-04` (`FINAL_HOLDOUT`) | `tests/unit/orchestration/*.py`, `tests/integration/**/*.py` | `.venv/bin/pytest tests/ -q` |
| Statistics & Reporting (`statistics/`, `reporting/`) | unit + integration | Separação estrita `DEV_CV` vs `FINAL_HOLDOUT` em `consolidate_descriptive` e `tbl_family_d` | `tests/unit/statistics/*.py`, `tests/unit/reporting/*.py` | `.venv/bin/pytest tests/ -q` |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | Após tarefas unitárias isoladas | `.venv/bin/pytest tests/unit/models/ tests/unit/orchestration/ -q` |
| Full | Após tarefas com impacto em integração, estatística ou relatórios | `.venv/bin/pytest tests/ -q` |
| Build | Ao concluir todas as tarefas | `.venv/bin/pytest tests/ -v` |

**Build**: `.venv/bin/pytest tests/ -q`

---

## Execution Plan

### Phase 1 — Transformadores Intra-Fold (`T1`, `T2`, `T3`)
```
T1 (SimpleImputer) --> T3 (pipeline.py: _instantiate_step_transformer + NaN/object antes da Camada 1)
T2 (OrdinalCategoryEncoder + FrequencyCategoryEncoder) --> T3
```

### Phase 2 — Integração na Etapa 4B, Holdout Final e Etapa 5/6 (`T4`, `T5`, `T6`)
```
T3 --> T4 (resolve_deferred_preprocessing + execução intra-fold com NaN/categóricos)
T5 (FINAL_HOLDOUT em matrix.py, execution.py, oof.py, stage_gates.py) --> T6 (holdout_metrics em statistics/ e reporting/tables.py)
```

---

## Task Breakdown

### T1: Implementar `SimpleImputer` (`MEAN`, `MEDIAN`, `MODE`) em NumPy puro (`models/preprocessing/imputers.py`)
- [ ] Implement & test T1
**Where**: `src/experimental_ml/models/preprocessing/imputers.py`, `src/experimental_ml/models/preprocessing/__init__.py`, `tests/unit/models/test_preprocessing_imputers.py`
**Depends on**: none
**Tests**: Testes unitários para `MEAN`, `MEDIAN` e `MODE` (inclusive com `dtype=object` misto), isolamento estrito de `X_val` (sem leakage) e `DataIntegrityError` quando coluna de `X_train` é 100% ausente.
**Gate**: `.venv/bin/pytest tests/unit/models/test_preprocessing_imputers.py -v`

### T2: Implementar `OrdinalCategoryEncoder` e `FrequencyCategoryEncoder` 1:1 (`models/preprocessing/encoders.py`)
- [ ] Implement & test T2
**Where**: `src/experimental_ml/models/preprocessing/encoders.py`, `src/experimental_ml/models/preprocessing/__init__.py`, `tests/unit/models/test_preprocessing_encoders.py`
**Depends on**: none
**Tests**: Testes unitários para `ORDINAL_ENCODER` (`-1.0` para categorias inéditas) e `FREQUENCY_ENCODER` (`0.0` para inéditas), preservando `NaN` para imputação posterior e mantendo dimensionalidade 1:1.
**Gate**: `.venv/bin/pytest tests/unit/models/test_preprocessing_encoders.py -v`

### T3: Registrar `IMPUTER`, `ORDINAL_ENCODER` e `FREQUENCY_ENCODER` em `models/preprocessing/pipeline.py`
- [ ] Implement & test T3
**Where**: `src/experimental_ml/models/preprocessing/pipeline.py`, `tests/unit/models/test_preprocessing_fit.py`
**Depends on**: T1, T2
**Tests**: Testes de `fit_two_layer_preprocessing` + `apply_two_layer_preprocessing` com Camada 1 (`ORDINAL_ENCODER` + `IMPUTER`) e Camada 2 (`STANDARD_SCALER`) sobre matrizes contendo texto e `NaN`, mantendo rejeição de `NaN` quando não há `IMPUTER`.
**Gate**: `.venv/bin/pytest tests/unit/models/ -q`

### T4: Injetar `SanitizedDatasetView.deferred_rules` automaticamente na Etapa 4B e no Nested CV (`AD-031`)
- [ ] Implement & test T4
**Where**: `src/experimental_ml/orchestration/execution.py`, `src/experimental_ml/tuning/engine.py`, `tests/integration/test_m9_deferred_preprocessing_e2e.py`
**Depends on**: T3
**Tests**: Teste E2E (Etapas 1 a 6) com dataset contendo `NaN` + coluna categórica em texto + `DEFER_INTRA_FOLD`, com seleção dinâmica e `GRID_SEARCH`, provando ausência de vazamento e execução completa.
**Gate**: `.venv/bin/pytest tests/ -q`

### T5: Gerar, executar e validar células `FINAL_HOLDOUT` sob `CV_AND_HOLDOUT` (`AD-032`)
- [ ] Implement & test T5
**Where**: `src/experimental_ml/orchestration/matrix.py`, `src/experimental_ml/orchestration/execution.py`, `src/experimental_ml/orchestration/oof.py`, `src/experimental_ml/stages/stage_gates.py`, `tests/unit/orchestration/test_matrix_builder.py`
**Depends on**: none
**Tests**: Testes unitários e de integração verificando criação de `cell_<m>__<s>__final_holdout`, treino sobre `development_ids`, avaliação sobre `holdout_ids` (inclusive com `run_nested_tuning`), preservação de OOF apenas de `DEV_CV` e aprovação no `verify_runs_gate`.
**Gate**: `.venv/bin/pytest tests/ -q`

### T6: Consolidar `holdout_metrics` separadamente de `DEV_CV` na Etapa 5 e exibir na Tabela D da Etapa 6
- [ ] Implement & test T6
**Where**: `src/experimental_ml/statistics/types.py`, `src/experimental_ml/statistics/consolidation.py`, `src/experimental_ml/statistics/storage.py`, `src/experimental_ml/reporting/tables.py`, `tests/unit/statistics/test_consolidation.py`
**Depends on**: T5
**Tests**: Testes verificando que células `FINAL_HOLDOUT` não alteram `mean`, `std`, `ci_lower`/`ci_upper` de Nadeau-Bengio nem testes pareados de `DEV_CV`, que `holdout_metrics` é persistido/recarregado em JSON e exibido na Tabela D.
**Gate**: `.venv/bin/pytest tests/ -q`

---

## Checks

**Run m9_unit**: `.venv/bin/pytest tests/unit/models/test_preprocessing_imputers.py tests/unit/models/test_preprocessing_encoders.py tests/unit/orchestration/test_matrix_builder.py tests/unit/statistics/test_consolidation.py -v`
**Run m9_e2e**: `.venv/bin/pytest tests/integration/test_m9_deferred_preprocessing_e2e.py -v`

**C1** - `SimpleImputer` (`MEAN`, `MEDIAN`, `MODE`) calcula estatísticas apenas em `X_train` e lança `DataIntegrityError` em coluna 100% ausente (`M9-01`, `AC-M9-01`)
Proof: run m9_unit | test_simple_imputer_mean_median_mode_and_all_missing PASSED

**C2** - `OrdinalCategoryEncoder` e `FrequencyCategoryEncoder` aprendem em `X_train` e tratam inéditas em `X_val` como `-1.0` / `0.0` (`M9-02`, `AC-M9-02`)
Proof: run m9_unit | test_categorical_encoders_1to1_and_unseen_categories PASSED

**C3** - Experimento com `NaN` + coluna categórica + `DEFER_INTRA_FOLD` executa da Etapa 1 à Etapa 6 sem vazamento (`M9-03`, `AC-M9-03`)
Proof: run m9_e2e | test_deferred_missing_and_categorical_e2e_no_leakage PASSED

**C4** - Sob `CV_AND_HOLDOUT`, células `FINAL_HOLDOUT` são geradas/executadas e consolidadas separadamente de `DEV_CV` (`M9-04`, `AC-M9-04`)
Proof: run m9_unit | test_final_holdout_isolated_from_dev_cv_consolidation PASSED

---

## Handoff

- **Feature**: `m9-intra-fold-imputation-encoding-holdout`
- **Phase / Task**: `Specify` aprovado (`AD-030`, `AD-031`, `AD-032`); `Design` e `Tasks` elaborados e validados. Aguardando aprovação de `tasks.md` pelo desenvolvedor para criar a branch `feat/m9-intra-fold-holdout` e iniciar `T1`.
- **In-progress**: none
- **Next step**: Aprovação de `tasks.md` pelo desenvolvedor para iniciar `Execute` (`T1`–`T6`).
