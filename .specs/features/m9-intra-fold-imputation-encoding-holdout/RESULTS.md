# Resultados de Homologação — Marco M9: Imputação/Codificação Intra-Fold e Holdout Final

- **Marco:** `M9` (`m9-intra-fold-imputation-encoding-holdout`)
- **Branch:** `feat/m9-intra-fold-holdout`
- **Status:** `VERIFICADO (PASS)` (Aguardando aceite do consumidor em `ACCEPTANCE.md` e merge em `main`)
- **Suíte de Testes:** `628 passed in 18.01s` (`.venv/bin/pytest tests/ -q`)
- **Verificador Independente:** [`verification.md`](./verification.md) — `C1`–`C4` aprovados (`PASS`)

---

## Resumo das Entregas (`T1`–`T6`)

1. **T1 (`fa7623c`)**: `SimpleImputer` (`MEAN`, `MEDIAN`, `MODE`) estritamente intra-fold em `src/experimental_ml/models/preprocessing/imputers.py`, com `DataIntegrityError` em coluna 100% ausente.
2. **T2 (`04d17ad`)**: `OrdinalCategoryEncoder` e `FrequencyCategoryEncoder` 1:1 em `src/experimental_ml/models/preprocessing/encoders.py` (`-1.0` / `0.0` para categorias inéditas).
3. **T3 (`4a2ae0a`)**: Registro de `IMPUTER`, `ORDINAL_ENCODER` e `FREQUENCY_ENCODER` na Layer 1 em `src/experimental_ml/models/preprocessing/pipeline.py`.
4. **T4 (`94ace9a`)**: Resolução automática de `DEFER_INTRA_FOLD` (`resolve_deferred_preprocessing`) no fold externo (`orchestration/execution.py`) e nos sub-folds do Nested CV (`tuning/engine.py`) antes da seleção dinâmica.
5. **T5 (`f53d17d`)**: Geração, execução (inclusive com `run_nested_tuning`) e preservação de OOF exclusivo de `DEV_CV` para células `FINAL_HOLDOUT` sob `CV_AND_HOLDOUT`.
6. **T6 (`31fefba`)**: Isolamento de `holdout_metrics` em `ConfigurationSummary`, persistência JSON em `statistics/storage.py` e exibição na Tabela D (`Holdout`) em `reporting/tables.py`.
