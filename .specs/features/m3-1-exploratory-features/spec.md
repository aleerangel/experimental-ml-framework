# M3.1 — Relatório Exploratório de Relações de Features (m3-1-exploratory-features) Specification

**Approved**: 2026-11-10 - user: "aprovado"

## Problem Statement

A Etapa 2 do pipeline experimental (`features`) tem como responsabilidade explorar as relações entre os atributos preditores e entre preditores e a variável-alvo, além de fundamentar a definição de cenários de features (`RF2.1`, `CA-E2-01`).

No entanto, em experimentos de aprendizado de máquina e modelagem preditiva com rigor científico:
1. **Risco de Vazamento de Dados (*Data Leakage*):** Se a exploração de atributos na base completa for confundida com a seleção formal de features, o pesquisador incorre em vazamento por seleção pré-partição (*selection bias*), invalidando as estimativas estatísticas posteriores (Etapas 4 e 5).
2. **Confusão Metodológica Causal e Multivariada:** Correlações estatísticas univariadas não implicam relações causais, e preditores com correlação linear próxima de zero podem possuir forte poder preditivo quando combinados de forma não linear ou em interações multivariadas.
3. **Ausência de Ferramenta Diagnóstica Estruturada e Agnóstica:** É necessário um módulo puro, sem dependências externas além do NumPy (`XCUT-02`), capaz de computar associações estatísticas adequadas ao tipo de variável (contínua x contínua via Pearson e Spearman; contínua x categórica via Razão de Correlação $\eta$; categórica x categórica via V de Cramér) e diagnosticar pares de preditores redundantes/multicolineares antes da partição.

O Sub-marco M3.1 resolve essa demanda implementando o primeiro componente da Etapa 2 (`experimental_ml.features`):
- `explore_features(view, redundancy_threshold=0.85)`: função pura que realiza a triagem estatística univariada e bivariada sobre a `SanitizedDatasetView` (gerada em M2.2).
- `ExploratoryFeatureReport`: estrutura de dados imutável marcada obrigatoriamente com o metadado `scope = "EXPLORATORY_FULL_DATA"` e acompanhada de três avisos metodológicos mandatórios (`CA-E2-01`).
- `target_associations`: métricas de associação preditor-alvo (Pearson $r$, Spearman $\rho$, Razão de Correlação $\eta$, V de Cramér $V$), com status de computabilidade (`MetricStatus.VALID` ou `MetricStatus.UNDEFINED_NAN` para variância zero/degenerescência).
- `feature_redundancy`: matriz completa de associação entre preditores candidatos e lista ordenada de pares com alta redundância que excedem o limiar configurado (`high_redundancy_pairs`).
- Serialização determinística bidirecional (`to_dict` / `from_dict`), compatível com JSON UTF-8 NFC e preservando rastreabilidade com o `dataset_hash`.

## Out of Scope

Explicitamente excluído para manter isolamento e controle de escopo:

| Feature | Reason |
| --- | --- |
| Definição e validação de cenários de features (`FeatureScenario`, `validate_scenarios`, `scenarios.json`) | Escopo do Sub-marco M3.2 |
| Seleção dinâmica intra-fold (`select_features_in_fold`, `SelectionResult`) | Escopo do Sub-marco M3.3 |
| Interface de linha de comando (`expml features explore`, `expml features scenarios`) | Escopo do Sub-marco M3.4 |
| Persistência atômica de `exploratory_features.json` via CLI | Escopo do Sub-marco M3.4 |
| Algoritmos com dependência de `scipy`, `scikit-learn` ou `statsmodels` | RNF01 / XCUT-02: runtime exclusivo com `numpy>=1.24.0` |
| Pré-processamento e transformação de features (imputação, scaling, PCA) | Escopo dos Marcos M3.3 e M4 |

---

## Assumptions & Open Questions

As premissas baseiam-se nos requisitos RF2.1, CA-E2-01, nas decisões consolidadas de arquitetura (ADR-005, ADR-007, ADR-008) e nas regras de governança do framework:

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Rotulagem Exploratória Mandatória | Todo relatório emitido por `explore_features` registra imutavelmente `scope = "EXPLORATORY_FULL_DATA"` e os 3 avisos metodológicos do SRS. | Cumpre rigorosamente `CA-E2-01` e impede que o relatório seja consumido como seleção automatizada pré-partição | y |
| Dependência Única NumPy | Cálculos de Pearson, Spearman (com postos médios para empates), Razão de Correlação ($\eta$) e V de Cramér implementados com arrays NumPy puros. | Mantém o contrato de dependência zero externa em runtime (XCUT-02) | y |
| Suporte aos Tipos de Tarefa e Variáveis | Para alvos contínuos (regressão), avalia Pearson e Spearman contra preditores numéricos e $\eta$ contra preditores categóricos; para alvos categóricos (classificação), avalia V de Cramér contra preditores categóricos e $\eta$ contra numéricos. | Adequação matemática estrita conforme a natureza da escala de mensuração | y |
| Tratamento de Degenerescência | Variância nula, colunas constantes residuais ou divisão por zero resultam em `NaN` e `status = "UNDEFINED_NAN"`, sem falhas não capturadas nem conversão silenciosa para `0.0`. | Aderência estrita à ADR-005 e `CA-GER-03` | y |
| Matriz de Redundância Simétrica | A matriz de redundância preditor-preditor avalia todos os pares de atributos candidatos em `view.candidate_feature_cols`. `high_redundancy_pairs` lista apenas pares com índice $i < j$ onde $|\text{associação}| \ge \text{threshold}$, ordenados decrescentemente por intensidade. | Evita redundância de espelhamento e garante ordenação canônica e determinística | y |
| Imutabilidade e Serialização | `ExploratoryFeatureReport` encapsula estruturas imutáveis (`MappingProxyType` ou tuplas/dicionários protegidos) com `.to_dict()` produzindo JSON primitivo seguro. | Coerência com ADR-008 e padrões do framework | y |

**Open questions:** none - as responsabilidades conceituais e os contratos do relatório exploratório foram integralmente definidos em `ARQUITETURA_E_CONTRATOS.md` e `ESPECIFICACAO_REQUISITOS.md`.

---

## User Stories

### P1: M3.1 — Relatório Exploratório de Relações de Features ⭐ MVP

**User Story**: Como pesquisador, quero executar uma análise exploratória das relações entre atributos preditores e a variável-alvo, bem como diagnosticar a redundância entre os preditores candidatos, recebendo avisos metodológicos mandatórios e a marcação explícita de escopo exploratório, para obter fundamentação analítica sem incorrer em vazamento de dados (*data leakage*).

**Why P1**: Atende diretamente aos requisitos `RF2.1` e ao critério de aceitação `CA-E2-01`. Fornece a base estatística descritiva e os alertas necessários antes da definição dos cenários de atributos da Etapa 2.

**Acceptance Criteria**:

1. WHEN `explore_features(view)` is called THEN the system SHALL return an `ExploratoryFeatureReport` with `scope = "EXPLORATORY_FULL_DATA"`, `dataset_hash = view.dataset_hash`, and a structured `warnings` mapping containing all three required methodological statements:
   (a) correlation does not imply causation;
   (b) low univariate correlation does not rule out multivariate predictive importance;
   (c) statistics computed on the full dataset are purely exploratory and must not be used for biased feature selection prior to train/val partitioning (EXP-01).

2. WHEN the dataset task is `REGRESSION` and a candidate feature is numeric THEN `explore_features` SHALL compute Pearson linear correlation $r \in [-1, 1]$ and Spearman rank correlation $\rho \in [-1, 1]$ using fractional ranking for ties, matching standard mathematical definitions (EXP-02).

3. WHEN an association involves one categorical and one continuous variable (either categorical feature with continuous target in regression, or numeric feature with categorical target in classification) THEN `explore_features` SHALL compute the Correlation Ratio $\eta = \sqrt{\text{SS}_{\text{between}} / \text{SS}_{\text{total}}} \in [0, 1]$ (EXP-03).

4. WHEN both feature and target are categorical (classification task with categorical feature) THEN `explore_features` SHALL compute Cramér's V statistic $V = \sqrt{\chi^2 / (N \cdot \min(R - 1, C - 1))} \in [0, 1]$ derived from the 2D contingency table (EXP-04).

5. WHEN a feature has zero variance, constant values, or encounters numerical degeneracy in association computation THEN `explore_features` SHALL record `value = float('nan')` and `status = "UNDEFINED_NAN"` without raising unhandled exceptions or substituting with `0.0` (EXP-05).

6. WHEN `explore_features(view, redundancy_threshold=0.85)` is evaluated THEN the system SHALL compute the pairwise association matrix across all `candidate_feature_cols` and return `high_redundancy_pairs` containing all unique pairs $(i < j)$ where the association magnitude meets or exceeds `redundancy_threshold`, canonically sorted by descending absolute correlation and feature names (EXP-06).

7. WHEN `report.to_dict()` is executed THEN the system SHALL return a JSON-compliant primitive dictionary with float representations conforming to IEEE 754, such that `ExploratoryFeatureReport.from_dict(data)` perfectly reconstructs the original report instance and preserves numeric equality and metadata integrity (EXP-07).

8. WHEN `explore_features` is invoked with an invalid view, non-sanitized data, empty candidate features, or an invalid `redundancy_threshold` (e.g. outside $[0, 1]$) THEN the system SHALL raise a typed domain error (`ValidationError` or `ConfigurationError`) with an explicit diagnostic message (EXP-08).

---

## Requirement Traceability

| Requirement ID | Description | Source / Rationale | Status |
| :--- | :--- | :--- | :--- |
| EXP-01 | Escopo obrigatório `EXPLORATORY_FULL_DATA` e três avisos metodológicos mandatórios | CA-E2-01, RF2.1 | in design |
| EXP-02 | Correlações contínua-contínua (Pearson $r$ e Spearman $\rho$ com postos médios para empates) | RF2.1, XCUT-02 | in design |
| EXP-03 | Razão de correlação $\eta$ (ANOVA univariada) para pares contínua-categórica | RF2.1, XCUT-02 | in design |
| EXP-04 | V de Cramér derivado de tabela de contingência para pares categórica-categórica | RF2.1, XCUT-02 | in design |
| EXP-05 | Tratamento de variância zero e degenerescência com `NaN` e `status = UNDEFINED_NAN` | ADR-005, CA-GER-03 | in design |
| EXP-06 | Matriz de redundância preditor-preditor e pares com alta redundância acima de limiar | RF2.1, CA-E2-01 | in design |
| EXP-07 | Serialização e reconstrução determinística (`to_dict` / `from_dict`) compatível com JSON | ADR-007, ADR-008 | in design |
| EXP-08 | Validação de entrada, integridade da visão saneada e verificação de parâmetros | RNF05, RNF07 | in design |

