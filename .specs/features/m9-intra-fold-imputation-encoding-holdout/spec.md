# M9 — Imputação e Codificação Categórica Intra-Fold e Execução de Holdout Final (Specification — Draft)

- **Status**: Draft — Pending Developer Approval (Fase TLC: **Specify / Proposta Preliminar**)
- **Milestone**: `M9` (`m9-intra-fold-imputation-encoding-holdout`)
- **Related Validation Findings**: `VAL-BUG-001`, `VAL-BUG-008`, `VAL-ENH-002`, `VAL-ENH-003`

---

## Problem Statement

Duas capacidades estruturais previstas nos requisitos da Onda 1 (`RF1.2`, `RF3.2`, `RF4.1`, `RF4.3`) encontram-se implementadas apenas na metade declarativa (Etapas 1 e 4A), sem contrapartida operacional no motor de execução da Etapa 4B:

1. **Imputação e Codificação Categórica Intra-Fold (`VAL-BUG-001`):** A Etapa 1 valida e armazena regras `kind="DEFER_INTRA_FOLD"` em `SanitizedDatasetView.deferred_rules` para `E1_FEATURE_MISSING` (`MEAN`, `MEDIAN`, `MODE`), `E1_CATEGORICAL_UNENCODED` e `E1_SCALE_DISPARITY`, preservando `NaN`s e colunas `object` na matriz `X`. Entretanto, `deferred_rules` nunca é lido na Etapa 4B, `_instantiate_step_transformer` não possui implementação para `transformer_type="IMPUTER"`, e `fit_two_layer_preprocessing` rejeita matrizes com `NaN` antes de executar a Camada 1.
2. **Execução de Células `FINAL_HOLDOUT` em `CV_AND_HOLDOUT` (`VAL-BUG-008`):** A Etapa 4A particiona e valida `holdout_ids` disjuntos de `development_ids` quando `outer_scheme="CV_AND_HOLDOUT"`, mas `build_cell_matrix` na Etapa 4B gera células apenas para os $K$ folds de `development_ids`, deixando o conjunto `holdout_ids` sem avaliação final.

## Goals

- [ ] Implementar o transformador `SimpleImputer` (`MEAN`, `MEDIAN`, `MODE`) na Camada 1 de `models/preprocessing/`, ajustado estritamente em `X_train` de cada fold (interno e externo).
- [ ] Implementar codificação intra-fold para colunas categóricas diferidas via `DEFER_INTRA_FOLD` sem vazamento de categorias ou estatísticas do conjunto de validação.
- [ ] Integrar `SanitizedDatasetView.deferred_rules` ao pipeline intra-fold da Etapa 4B (`orchestration/execution.py` e `tuning/engine.py`).
- [ ] Gerar, executar e persistir células `FINAL_HOLDOUT` (treino em `development_ids`, avaliação em `holdout_ids`) sob o regime `CV_AND_HOLDOUT`, mantendo suas métricas separadas da agregação de Nadeau-Bengio dos $K$ folds de `DEVELOPMENT_CV` nas Etapas 5 e 6.

---

## Open Questions for Developer Decision (Before Closing Specify)

Para concluir a fase **Specify** deste marco, o desenvolvedor deverá definir três decisões de design:

1. **[Decisão D1 — Estratégias de Codificação Categórica Intra-Fold]:** Para variáveis categóricas com `DEFER_INTRA_FOLD`, quais estratégias devem compor o escopo do Marco `M9`?
   - **(Opção A — Recomendada para manter dimensionalidade 1:1 com `feature_names`):** `ORDINAL_ENCODING` (mapeamento determinístico ordenado por frequência ou ordem lexicográfica em `X_train`, mapeando categorias inéditas de `X_val` para `-1.0`) e `FREQUENCY_ENCODING` (proporção observada em `X_train`); ou
   - **(Opção B — Com expansão de colunas):** Incluir também `ONE_HOT_ENCODING` intra-fold (o que altera dinamicamente o número e os nomes das colunas entre a Camada 1 e a seleção de atributos / diagnósticos de coeficientes)?
2. **[Decisão D2 — Precedência entre `deferred_rules` da Etapa 1 e `ModelSpec.preprocessing` da Etapa 3]:** Quando `SanitizedDatasetView.deferred_rules` contém uma regra `DEFER_INTRA_FOLD` (ex.: `imputation_strategy="MEDIAN"`), ela deve ser injetada automaticamente como o primeiro passo da Camada 1 para todos os modelos que não declararem um `IMPUTER` explícito próprio?
3. **[Decisão D3 — Política de Hiperparâmetros na Célula `FINAL_HOLDOUT`]:** Quando um modelo possui `search_spec` (tuning) sob o regime `CV_AND_HOLDOUT`, a célula `FINAL_HOLDOUT` (treinada em todos os `development_ids`) deve:
   - **(Opção A — Padrão metodológico):** Executar `run_nested_tuning` (ou CV interna) sobre `development_ids` para escolher o hiperparâmetro final antes de avaliar em `holdout_ids`; ou
   - **(Opção B):** Reutilizar o hiperparâmetro modal/vencedor dos $K$ folds de `DEVELOPMENT_CV`?

---

## Preliminary Requirements (EARS Notation)

### R1 — Transformador `IMPUTER` na Camada 1 (`VAL-BUG-001`, `VAL-ENH-002`)
- **WHEN** um passo de Camada 1 com `transformer_type="IMPUTER"` e `strategy` em `{"MEAN", "MEDIAN", "MODE"}` é ajustado sobre `X_train`, **THE SYSTEM SHALL** calcular a estatística de imputação de cada coluna exclusivamente a partir dos valores não-ausentes de `X_train` e substituir todos os `NaN` em `X_train` e `X_val` por esses valores ajustados.
- **IF** uma coluna de `X_train` em um fold contiver 100% de valores `NaN`, **THEN THE SYSTEM SHALL** lançar `DataIntegrityError` (ou aplicar valor de fallback explícito `0.0` conforme configuração) com mensagem identificando a coluna e o fold.

### R2 — Consumo Automático de `SanitizedDatasetView.deferred_rules` (`VAL-BUG-001`)
- **WHEN** `SanitizedDatasetView.deferred_rules` contiver regras `DEFER_INTRA_FOLD` aprovadas no gate da Etapa 1, **THE SYSTEM SHALL** converter essas regras em passos de Camada 1 aplicados automaticamente dentro de cada fold na Etapa 4B antes da seleção dinâmica de atributos e antes da Camada 2 de escalonamento.

### R3 — Execução e Isolamento de Células `FINAL_HOLDOUT` (`VAL-BUG-008`, `VAL-ENH-003`)
- **WHEN** `PartitionPlan.outer_scheme == OuterScheme.CV_AND_HOLDOUT`, **THE SYSTEM SHALL** gerar na matriz de execução as $K \times M \times C$ células de `DEVELOPMENT_CV` e mais $M \times C$ células de `FINAL_HOLDOUT` (onde o treino utiliza `development_ids` e a avaliação utiliza `holdout_ids`).
- **WHEN** a Etapa 5 consolida as métricas de um experimento `CV_AND_HOLDOUT`, **THE SYSTEM SHALL** calcular média, desvio-padrão, IC de Nadeau-Bengio e testes pareados exclusivamente sobre os $K$ folds de `DEVELOPMENT_CV`, reportando o desempenho de `FINAL_HOLDOUT` em seção e colunas dedicadas sem misturá-lo como um $(K+1)$-ésimo fold.
