# M2.3 — Partitioning Engine (m2-3-partitioning-engine) Specification

**Approved**: 2026-11-07 - user: "aprovado"

## Problem Statement

O framework experimental requer a geração e validação de partições de dados rigorosas, determinísticas e compartilhadas (`PartitionPlan`), em conformidade com o requisito `RF4.1`, `RF4.2` e o critério de aceitação `CA-E4A-01` e `CA-E4A-02`. 

Sem um motor de particionamento independente e auditado:
1. Modelos, cenários de atributos e múltiplos alvos avaliados poderiam utilizar divisões inconsistentes ou não comparáveis, inviabilizando comparações estatísticas pareadas válidas (Etapa 5).
2. Divisões poderiam introduzir vazamento de dados (*data leakage*) inadvertido entre treino e validação, tal como a presença de instâncias do mesmo grupo/unidade amostral em ambos os conjuntos ou inversão cronológica de eventos temporais.
3. A ausência de validação matemática a priori de disjunção ($\text{Train}_k \cap \text{Val}_k = \emptyset$) permitiria que planos degenerados avançassem silenciosamente para a execução matricial (Etapa 4B).

O Sub-marco M2.3 resolve esse problema criando o pacote `experimental_ml.validation` com o motor puro de particionamento e validação:
- Construtor `build_partition_plan` que suporta K-Fold, Stratified K-Fold, Group K-Fold, Bootstrap (com OOB), Temporal e Holdout em três regimes (`CV_ONLY`, `HOLDOUT_ONLY`, `CV_AND_HOLDOUT`).
- Validador matemático `validate_partition_plan` que prova disjunção estrita e conformidade estrutural.
- Estrutura imutável e compartilhada `PartitionPlan` com identificador determinístico `plan_id` derivado via SHA-256 e suporte explícito a `development_ids` (Decisão D7) e semente mestre reprodutível (Decisão D8).

## Out of Scope

Explicitamente excluído para manter isolamento e controle de escopo:

| Feature | Reason |
| --- | --- |
| Execução da matriz experimental $(\text{Modelos} \times \text{Cenários} \times \text{Folds})$ | Pertence à Etapa 4B no módulo `orchestration` (Marco M5) |
| Persistência atômica de partições em arquivos `.csv.gz` em disco | Pertence à CLI e utilitários de persistência no Marco M2.4 |
| Comandos de terminal `expml partition generate` e `expml partition validate` | Escopo do Sub-marco M2.4 |
| Seleção de atributos dentro do fold (*intra-fold feature selection*) | Pertence ao módulo `features` na Etapa 2 |
| Ajuste e aplicação de pré-processamento dentro do fold | Pertence ao módulo `models` na Etapa 3/4B |
| Algoritmos de divisão dependentes de bibliotecas externas adicionais | RNF01: dependência única de execução é `numpy>=1.24.0` |

---

## Assumptions & Open Questions

As premissas baseiam-se nos requisitos RF4.1 e RF4.2, nas decisões D6, D7 e D8 do Marco M2 e nas diretrizes arquiteturais de governança:

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| D7: Separação de `development_ids` e `holdout_ids` | Em regimes com holdout (`CV_AND_HOLDOUT` e `HOLDOUT_ONLY`), `holdout_ids` são extraídos primeiro e `development_ids` contém o restante. Em `CV_AND_HOLDOUT`, os folds de CV dividem exclusivamente `development_ids`. | Garante que o holdout final permaneça completamente intocado durante toda a validação cruzada | y |
| D8: Reprodutibilidade e Rastreabilidade | Mesma configuração, mesmos dados (`dataset_hash` e ordem de `observation_ids`) e mesma `master_seed` produzem exatamente o mesmo `plan_id` e as mesmas partições. Derivação determinística via gerador estável do framework. | Atende a CA-E4A-02 sem depender de estabilidade perpétua do `np.random.Generator` entre versões futuras do NumPy | y |
| Ressalva Arquitetural de Dependência | O pacote `validation` opera sobre `SanitizedDatasetView` ou `DatasetBundle` consumindo apenas identificadores e arrays expostos pelo contrato, sem depender ou importar lógicas internas de sanitização. | Preserva desacoplamento estrito entre `data` e `validation` | y |
| Bootstrap Out-of-Bag (OOB) | Em `BOOTSTRAP`, cada repetição gera um conjunto de treino amostrado com reposição ($|Train| = N$) e o conjunto de validação é formado estritamente pelas observações não amostradas (*out-of-bag*). | Conforme RF4.1 e metodologia estatística padrão para estimativa de erro | y |
| Validação Matemática Obrigatória | `validate_partition_plan` verifica disjunção estrita ($\text{Train} \cap \text{Val} = \emptyset$ e $\text{Train}/\text{Val} \cap \text{Holdout} = \emptyset$), integridade de grupos e ordenação temporal. | Previne vazamento de dados antes de qualquer treinamento (CA-E4A-01) | y |

**Open questions:** none - as estratégias, regimes e decisões de projeto foram integralmente consolidados e aprovados nas decisões D1 a D12 do Marco M2.

---

## User Stories

### P1: M2.3 — Motor de Particionamento Compartilhado e Validado ⭐ MVP

**User Story**: Como pesquisador, quero gerar um plano de particionamento imutável e auditado (`PartitionPlan`) a partir da visão saneada dos dados, para fixar as mesmas divisões de treino, validação e teste para todos os modelos da matriz experimental sem vazamento de dados.

**Why P1**: Atende aos requisitos `RF4.1`, `RF4.2` e aos critérios de aceitação `CA-E4A-01` e `CA-E4A-02`. Constitui a base de integridade para toda a execução experimental das Etapas 4A e 4B.

**Acceptance Criteria**:

1. WHEN `build_partition_plan(data_view, config)` receives a valid `PartitionConfig` with `regime = "CV_ONLY"` and `strategy = "KFOLD"` THEN the system SHALL partition `observation_ids` into $K$ disjoint validation folds whose union equals `development_ids`, with `holdout_ids = ()`, and $\text{Train}_k \cap \text{Val}_k = \emptyset$ for every fold (PART-01).
2. WHEN `build_partition_plan` is executed with `strategy = "STRATIFIED_KFOLD"` on classification data THEN the system SHALL preserve class frequency proportions in each validation fold within 1 sample of nominal proportion (PART-02).
3. WHEN `build_partition_plan` is executed with `strategy = "GROUP_KFOLD"` THEN the system SHALL partition groups such that $\text{Groups}(\text{Train}_k) \cap \text{Groups}(\text{Val}_k) = \emptyset$ for every fold, with zero group overlap between train and validation (PART-03).
4. WHEN `build_partition_plan` is executed with `strategy = "TEMPORAL"` THEN the system SHALL sort observations by time and ensure that $\max(\text{Time}(\text{Train}_k)) \le \min(\text{Time}(\text{Val}_k))$ for every fold, preventing forward temporal leakage (PART-04).
5. WHEN `build_partition_plan` is executed with `strategy = "BOOTSTRAP"` THEN the system SHALL generate $B$ resamples where each training set is sampled with replacement with size equal to development set size and each validation set contains strictly the out-of-bag observations (PART-05).
6. WHEN `build_partition_plan` is executed with `regime = "CV_AND_HOLDOUT"` or `regime = "HOLDOUT_ONLY"` THEN the system SHALL partition `observation_ids` into `holdout_ids` and `development_ids` disjointly, confining any cross-validation folds strictly to `development_ids` (PART-06).
7. WHEN `validate_partition_plan(plan, data_view)` is called THEN the system SHALL verify mathematical disjointness of train and validation sets, holdout disjointness, group non-overlap, and temporal monotonicity, raising `DataIntegrityError` if any invariant is violated (PART-07).
8. The `PartitionPlan` SHALL be an immutable dataclass with slots exposing `plan_id` as a deterministic 64-character SHA-256 digest computed from `source_dataset_hash`, config parameters, `development_ids`, `holdout_ids`, and fold tuples, ignoring volatile metadata (PART-08).
9. WHEN `build_partition_plan` is invoked repeatedly with identical `data_view` (`dataset_hash` and `observation_ids` order), identical config and identical `master_seed` THEN the system SHALL produce identical `plan_id`, `train_ids`, `val_ids`, `development_ids` and `holdout_ids` (PART-09).
10. IF `n_splits < 2` in cross-validation, `holdout_fraction <= 0` or `>= 1.0` in holdout regimes, `group_col` is missing for `GROUP_KFOLD`, `time_col` is missing for `TEMPORAL`, or number of unique groups is less than `n_splits` in `GROUP_KFOLD` THEN the system SHALL raise `ConfigurationError` (PART-10).

---

## Requirement Traceability

| Requirement ID | Description | Source / Rationale | Status |
| :--- | :--- | :--- | :--- |
| PART-01 | Divisão K-Fold pura com disjunção estrita e cobertura total de development | RF4.1, CA-E4A-01 | proposed |
| PART-02 | Divisão Estratificada preservando distribuição de classes | RF4.1, CA-E4A-01 | proposed |
| PART-03 | Divisão Agrupada com disjunção estrita de grupos ($\text{Groups}(Train) \cap \text{Groups}(Val) = \emptyset$) | RF4.1, CA-E4A-01, ADR-002 | proposed |
| PART-04 | Divisão Temporal com ordenação cronológica e prevenção de vazamento temporal | RF4.1, CA-E4A-01 | proposed |
| PART-05 | Reamostragem Bootstrap com conjunto de validação Out-of-Bag (OOB) | RF4.1, RF4.7 | proposed |
| PART-06 | Separação de Holdout e confinamento de CV a `development_ids` | RF4.1, D7, CA-E4A-01 | proposed |
| PART-07 | Validador matemático `validate_partition_plan` com checagem de invariantes | CA-E4A-01, ADR-008 | proposed |
| PART-08 | Contrato imutável de `PartitionPlan` com `plan_id` SHA-256 determinístico | RF4.2, CA-E4A-02, ADR-007 | proposed |
| PART-09 | Determinismo e reprodutibilidade de partições a partir de semente mestre | CA-E4A-02, D8 | proposed |
| PART-10 | Validação de limites e configurações de particionamento via `ConfigurationError` | RNF05, RNF07 | proposed |
