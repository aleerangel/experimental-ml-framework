# M9 — Imputação e Codificação Categórica Intra-Fold e Execução de Holdout Final (Specification)

- **Status**: Approved (Fase TLC: **Specify** concluída)
**Approved**: 2026-11-27 - user: "D1: Opção A; D2: Sim; D3: Opção A"
- **Milestone**: `M9` (`m9-intra-fold-imputation-encoding-holdout`)
- **Related Validation Findings**: `VAL-BUG-001`, `VAL-BUG-008`, `VAL-ENH-002`, `VAL-ENH-003`

---

## Problem Statement

Duas capacidades estruturais previstas nos requisitos da Onda 1 (`RF1.2`, `RF3.2`, `RF4.1`, `RF4.3`) encontram-se implementadas apenas na metade declarativa (Etapas 1 e 4A), sem contrapartida operacional no motor de execução da Etapa 4B:

1. **Imputação e Codificação Categórica Intra-Fold (`VAL-BUG-001`):** A Etapa 1 valida e armazena regras `kind="DEFER_INTRA_FOLD"` em `SanitizedDatasetView.deferred_rules` para `E1_FEATURE_MISSING` (`MEAN`, `MEDIAN`, `MODE`), `E1_CATEGORICAL_UNENCODED` e `E1_SCALE_DISPARITY`, preservando `NaN`s e colunas `object` na matriz `X`. Entretanto, `deferred_rules` nunca é lido na Etapa 4B, `_instantiate_step_transformer` não possui implementação para `transformer_type="IMPUTER"`, e `fit_two_layer_preprocessing` rejeita matrizes com `NaN` antes de executar a Camada 1.
2. **Execução de Células `FINAL_HOLDOUT` em `CV_AND_HOLDOUT` (`VAL-BUG-008`):** A Etapa 4A particiona e valida `holdout_ids` disjuntos de `development_ids` quando `outer_scheme="CV_AND_HOLDOUT"`, mas `build_cell_matrix` na Etapa 4B gera células apenas para os $K$ folds de `development_ids`, deixando o conjunto `holdout_ids` sem avaliação final.

## Goals

- [ ] Implementar o transformador `SimpleImputer` (`MEAN`, `MEDIAN`, `MODE`) na Camada 1 de `models/preprocessing/`, ajustado estritamente em `X_train` de cada fold (interno e externo).
- [ ] Implementar codificação categórica intra-fold (`ORDINAL_ENCODING` e `FREQUENCY_ENCODING`) preservando dimensionalidade 1:1 com `feature_names` (`AD-030`).
- [ ] Injetar automaticamente `SanitizedDatasetView.deferred_rules` na Camada 1/2 quando não houver passo equivalente no `ModelSpec` (`AD-031`), integrando ao pipeline intra-fold da Etapa 4B e do Nested CV.
- [ ] Gerar, executar, persistir e consolidar separadamente células `FINAL_HOLDOUT` (treino em `development_ids`, avaliação em `holdout_ids`, com `run_nested_tuning` quando `search_spec` estiver ativo — `AD-032`) sob o regime `CV_AND_HOLDOUT`.

## Out of Scope

- `ONE_HOT_ENCODING` intra-fold com expansão dinâmica de colunas (`AD-030`).
- Redesenho dos renderizadores gráficos das Etapas 2 e 6 ou comparação visual Treino vs. Teste (`M10` / `VAL-ENH-005`).

---

## User Stories

- **US-01 (Pesquisador / Dados Reais com Missing e Categóricos):** Como pesquisador, quero declarar `DEFER_INTRA_FOLD` na Etapa 1 para valores ausentes e variáveis categóricas e executar toda a matriz na Etapa 4B sem `NaN`/`object` crashes e sem vazamento entre treino e validação.
- **US-02 (Pesquisador / Protocolo `CV_AND_HOLDOUT`):** Como pesquisador, quero que o regime `CV_AND_HOLDOUT` execute tanto os $K$ folds de desenvolvimento quanto a avaliação final no conjunto `holdout_ids`, reportando as métricas do Holdout Final separadamente da inferência estatística de Nadeau-Bengio.

---

## Assumptions & Open Questions

Open questions: none (Decisões D1, D2 e D3 resolvidas pelo desenvolvedor em 2026-11-27 e registradas em `AD-030`, `AD-031`, `AD-032`).

### Decisões Registradas (`AD-030`, `AD-031`, `AD-032`)
1. **D1 (`AD-030`):** Estratégias categóricas intra-fold: `ORDINAL_ENCODING` e `FREQUENCY_ENCODING` (dimensionalidade 1:1 com `feature_names`).
2. **D2 (`AD-031`):** Regras `DEFER_INTRA_FOLD` são injetadas automaticamente nos modelos que não declararem `IMPUTER`/encoder/scaler equivalente em `ModelSpec.preprocessing`.
3. **D3 (`AD-032`):** Sob `CV_AND_HOLDOUT` com `search_spec`, a célula `FINAL_HOLDOUT` executa `run_nested_tuning` sobre `development_ids` antes de avaliar `holdout_ids`.

---

## Requirements (EARS Notation)

### M9-01 — Transformador `IMPUTER` na Camada 1 (`VAL-BUG-001`, `VAL-ENH-002`)
- **WHEN** um passo de Camada 1 com `transformer_type="IMPUTER"` e `strategy` em `{"MEAN", "MEDIAN", "MODE"}` é ajustado sobre `X_train`, **THE SYSTEM SHALL** calcular a estatística de imputação de cada coluna exclusivamente a partir dos valores não-ausentes de `X_train` e substituir todos os valores ausentes (`NaN`/`None`) em `X_train` e `X_val` por esses valores ajustados.
- **IF** uma coluna de `X_train` em um fold contiver 100% de valores ausentes, **THEN THE SYSTEM SHALL** lançar `DataIntegrityError` identificando a coluna/índice e o fold.

### M9-02 — Codificação Categórica Intra-Fold 1:1 (`VAL-BUG-001`, `AD-030`)
- **WHEN** um passo de Camada 1 com `transformer_type` em `{"ORDINAL_ENCODER", "FREQUENCY_ENCODER"}` (ou regra `DEFER_INTRA_FOLD` de `E1_CATEGORICAL_UNENCODED`) é ajustado sobre `X_train`, **THE SYSTEM SHALL** aprender o mapeamento categórico exclusivamente em `X_train` e transformar `X_train` e `X_val` para `float64` mantendo o mesmo número e ordem de colunas, mapeando categorias inéditas em `X_val` para `-1.0` (`ORDINAL_ENCODER`) ou `0.0` (`FREQUENCY_ENCODER`).

### M9-03 — Consumo Automático de `SanitizedDatasetView.deferred_rules` (`VAL-BUG-001`, `AD-031`)
- **WHEN** `SanitizedDatasetView.deferred_rules` contiver regras `DEFER_INTRA_FOLD` aprovadas no gate da Etapa 1, **THE SYSTEM SHALL** injetar os passos correspondentes de Camada 1 (`ORDINAL_ENCODER`/`FREQUENCY_ENCODER`, `IMPUTER`) e Camada 2 (`E1_SCALE_DISPARITY`) no pipeline efetivo de pré-processamento do modelo quando este não declarar passo equivalente, executando-os intra-fold (inclusive nos sub-folds internos do Nested CV) antes da seleção dinâmica de atributos e do escalonamento final.

### M9-04 — Execução e Consolidação Separada de Células `FINAL_HOLDOUT` (`VAL-BUG-008`, `VAL-ENH-003`, `AD-032`)
- **WHEN** `PartitionPlan.regime == EvaluationRegime.CV_AND_HOLDOUT` e `PartitionPlan.holdout_ids` não é vazio, **THE SYSTEM SHALL** gerar na matriz de execução as $K \times M \times C$ células de `DEV_CV` e mais $M \times C$ células com `phase="FINAL_HOLDOUT"` (treino em `development_ids`, avaliação em `holdout_ids`, executando `run_nested_tuning` sobre `development_ids` quando `search_spec` estiver ativo).
- **WHEN** a Etapa 5 consolida métricas e realiza inferência estatística sobre células contendo `phase="FINAL_HOLDOUT"`, **THE SYSTEM SHALL** calcular estatísticas descritivas, IC de Nadeau-Bengio e testes pareados exclusivamente sobre as células de `DEV_CV`, armazenando e reportando os resultados de `FINAL_HOLDOUT` separadamente sem contaminar os $K$ folds de CV.

---

## Acceptance Criteria Summary

| ID | Criterion | Verification Method |
| :--- | :--- | :--- |
| `AC-M9-01` | `IMPUTER` (`MEAN`, `MEDIAN`, `MODE`) calcula estatísticas apenas em `X_train` (sem vazamento de `X_val`) e lança `DataIntegrityError` em coluna 100% ausente. | Teste unitário anti-leakage (`pytest`). |
| `AC-M9-02` | `ORDINAL_ENCODER` e `FREQUENCY_ENCODER` aprendem categorias apenas em `X_train` e tratam categorias inéditas em `X_val` sem erro (`-1.0` / `0.0`). | Teste unitário (`pytest`). |
| `AC-M9-03` | Experimento com `NaN` + coluna categórica em texto + `DEFER_INTRA_FOLD` executa da Etapa 1 à Etapa 6 com sucesso e sem vazamento. | Teste de integração E2E (`pytest`). |
| `AC-M9-04` | Sob `CV_AND_HOLDOUT`, células `FINAL_HOLDOUT` são geradas e executadas sobre `(development_ids, holdout_ids)`, e `consolidate_descriptive` / `report.md` reportam `FINAL_HOLDOUT` separado de `DEV_CV`. | Teste unitário e integração (`pytest`). |

---

## Requirement Traceability

| Requirement ID | Origin / Finding | Acceptance Criteria |
| :--- | :--- | :--- |
| M9-01 | `VAL-BUG-001`, `VAL-ENH-002` | `AC-M9-01` |
| M9-02 | `VAL-BUG-001`, `AD-030` | `AC-M9-02` |
| M9-03 | `VAL-BUG-001`, `AD-031` | `AC-M9-03` |
| M9-04 | `VAL-BUG-008`, `VAL-ENH-003`, `AD-032` | `AC-M9-04` |
