# M3.3 — Seleção Dinâmica Intra-Fold de Features e Estabilidade (m3-3-intra-fold-selection) Specification

**Approved**: 2026-11-10 - user: "prossiga para o m3.3"

## Problem Statement

Na modelagem preditiva e no aprendizado de máquina experimental com rigor científico, qualquer seleção ou transformação de atributos dependente das observações deve ser executada **estritamente dentro dos dados de treino de cada partição** (`RF2.4`, `CA-E2-02`, `ADR-002`). Se os preditores fossem selecionados na base completa antes da divisão em folds, as métricas de validação cruzada seriam infladas artificialmente devido a vazamento de dados por viés de seleção (*selection bias* / *data leakage*).

Adicionalmente, quando a seleção de atributos varia entre diferentes partições de treino, o pesquisador precisa quantificar a **estabilidade da seleção** (`RF2.1`), mensurando se o subconjunto selecionado é robusto a perturbações na amostragem ou se os modelos estão selecionando variáveis espúrias dependentes da partição.

O Sub-marco M3.3 resolve essa demanda implementando o motor de seleção intra-fold e medição de estabilidade:
- `select_features_in_fold(X_train, y_train, scenario, random_state) -> SelectionResult`: despachante funcional puro que executa a seleção de atributos exclusivamente sobre os dados de treino do fold.
  - Para cenários `FIXED`: retorna diretamente a lista estática pré-declarada de atributos.
  - Para cenários `DYNAMIC`: ajusta estatísticas (variância, correlação/relevância com o alvo) estritamente sobre $(X_{\text{train}}, y_{\text{train}})$ e seleciona os atributos correspondentes.
- `apply_feature_selection(X_eval, selection_result) -> dict[str, np.ndarray]`: função pura que projeta a seleção ajustada no treino sobre os dados de validação/teste ($X_{\text{eval}}$).
- `compute_selection_stability(fold_selections, n_total_candidates) -> SelectionStabilityReport`: computa métricas rigorosas de estabilidade entre folds, incluindo a similaridade de Jaccard par a par e o Índice de Estabilidade de Kuncheva corrigido para o acaso.

## Out of Scope

Explicitamente excluído para manter isolamento e controle de escopo:

| Feature | Reason |
| --- | --- |
| Interface de linha de comando (`expml features ...`) | Escopo do Sub-marco M3.4 |
| Orquestração do loop de validação cruzada e matriz de modelos | Pertence ao Marco M5 (`orchestration`) |
| Pré-processamento específico de modelos (Camada 2, normalização, scaling) | Pertence ao Marco M4 (`models`) |
| Modelos preditivos ou pipelines de estimadores externos (Scikit-Learn/XGBoost) | Pertence ao Marco M4 (`models`) |
| Redutores complexos dependentes de SciPy (ex.: decomposições de grafos) | RNF01 / XCUT-02: runtime exclusivo em `numpy>=1.24.0` |

---

## Assumptions & Open Questions

As premissas baseiam-se nos requisitos RF2.1, RF2.4, nas decisões de arquitetura (ADR-002, ADR-005, ADR-007, ADR-008) e nas regras de governança do framework:

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Paradigma Funcional sem Estado | `select_features_in_fold` é uma função pura; retorna `SelectionResult` contendo os parâmetros ajustados (`fitted_params`), sem manter estado em objetos mutáveis. | ADR-008 e prevenção contra vazamento de dados entre folds | y |
| Isolamento Estrito do Treino | Em cenários dinâmicos, $X_{\text{eval}}$ ou dados de holdout jamais são consultados durante `select_features_in_fold`. | RF2.4 e ADR-002 (eliminação irrestrita de data leakage) | y |
| Estabilidade de Kuncheva Corrigida | Utiliza a formulação canônica de Kuncheva (2007) corrigida para o acaso: $K(S_i, S_j) = \frac{r \cdot N - k_i \cdot k_j}{k_i \cdot (N - k_j)}$. | Proporciona métrica com valor 0 para seleção aleatória e 1 para concordância perfeita | y |
| Tratamento de Degenerescência | Se nenhum atributo satisfizer o critério de seleção (ex.: limiar de variância excessivo), levanta `DataIntegrityError` informando o pesquisador. | Impede que conjuntos de treino com 0 features avancem para ajuste de modelos | y |
| Runtime Puro NumPy | Todos os cálculos de variância, correlação intra-fold, Jaccard e Kuncheva implementados em NumPy padrão. | Aderência estrita a XCUT-02 | y |

**Open questions:** none - os contratos funcionais de seleção intra-fold foram definidos na seção 3.2 de `ARQUITETURA_E_CONTRATOS.md`.

---

## User Stories

### P1: M3.3 — Seleção Dinâmica Intra-Fold de Features e Estabilidade ⭐ MVP

**User Story**: Como pesquisador, quero executar a seleção de atributos exclusivamente sobre os dados de treino de cada partição e aplicar a mesma seleção sobre os dados de avaliação, além de medir a estabilidade da seleção entre folds via Jaccard e índice de Kuncheva, para garantir validade científica livre de vazamento de dados (*data leakage*).

**Why P1**: Atende diretamente aos requisitos `RF2.1`, `RF2.4` e à diretriz `ADR-002`. É o componente que conecta os cenários declarativos da Etapa 2 à execução matricial de modelos em cada partição na Etapa 4B.

**Acceptance Criteria**:

1. WHEN `select_features_in_fold(X_train, y_train, scenario, random_state)` is executed THEN the system SHALL return an immutable `SelectionResult(frozen=True, slots=True)` containing `selected_features` (tuple of strings), `scores` (MappingProxyType of float scores), `fitted_params` (MappingProxyType), and `strategy_name` (SEL-01).

2. WHEN a scenario has `mode = "FIXED"` THEN `select_features_in_fold` SHALL immediately return `SelectionResult` with `selected_features = scenario.selected_features`, empty `scores`, empty `fitted_params`, and `strategy_name = "FIXED"` without computing data-dependent statistics or requiring `y_train` (SEL-02).

3. WHEN a dynamic scenario specifies `strategy_name = "VARIANCE_THRESHOLD"` with `strategy_params = {"threshold": t}` THEN `select_features_in_fold` SHALL compute sample variances $\sigma^2$ strictly on numeric predictors in `X_train`, select all features with $\sigma^2 > t$ sorted canonically by descending variance, and record the variances in `scores` (SEL-03).

4. WHEN a dynamic scenario specifies correlation-based selection (e.g. `strategy_name = "TOP_K_RELEVANCE"` with `strategy_params = {"k": k}`) THEN `select_features_in_fold` SHALL compute association metrics against `y_train` strictly on the fold training data, select the top-$k$ predictors sorted by descending absolute association, and record individual association scores (SEL-04).

5. WHEN `apply_feature_selection(X_eval, selection_result)` is called THEN the system SHALL project the selection onto `X_eval`, returning a dictionary of arrays containing strictly the columns in `selection_result.selected_features` in identical order, raising `ContractViolationError` if any selected feature is missing from `X_eval` (SEL-05).

6. WHEN `compute_selection_stability(fold_selections, n_total_candidates)` is called with selections across $K \ge 2$ folds THEN the system SHALL compute pairwise Jaccard similarities $J(S_i, S_j) = \frac{|S_i \cap S_j|}{|S_i \cup S_j|}$ and Kuncheva consistency indices $K(S_i, S_j) = \frac{r \cdot N - k_i \cdot k_j}{k_i \cdot (N - k_j)}$, returning an immutable `SelectionStabilityReport` with mean, std, and pairwise matrices (SEL-06).

7. WHEN all features fail a dynamic selection criterion (e.g. threshold too high) or inputs have zero valid rows/columns THEN `select_features_in_fold` SHALL raise `DataIntegrityError` or `ContractViolationError` rather than returning an empty feature set (SEL-07).

8. WHEN `select_features_in_fold`, `apply_feature_selection`, and `compute_selection_stability` are executed THEN all calculations SHALL be performed strictly using `numpy` and Python standard library constructs without importing `scipy`, `sklearn`, or `pandas` (`XCUT-02`) (SEL-08).

---

## Requirement Traceability

| Requirement ID | Description | Source / Rationale | Status |
| :--- | :--- | :--- | :--- |
| SEL-01 | Modelo de dados imutável `SelectionResult` com atributos selecionados, escores e parâmetros | RF2.4, ADR-008 | in design |
| SEL-02 | Execução imediata para cenários `FIXED` retornando atributos estáticos sem cálculo | RF2.2, CA-E2-02 | in design |
| SEL-03 | Estratégia dinâmica `VARIANCE_THRESHOLD` ajustada estritamente no treino do fold | RF2.3, ADR-002 | in design |
| SEL-04 | Estratégia dinâmica `TOP_K_RELEVANCE` com métricas calculadas sobre o treino do fold | RF2.3, RF2.4, ADR-002 | in design |
| SEL-05 | Aplicação pura da seleção sobre dados de avaliação (`apply_feature_selection`) | RF2.4, ADR-008 | in design |
| SEL-06 | Medição de estabilidade de seleção entre folds via Jaccard e índice de Kuncheva corrigido | RF2.1, CA-E2-01 | in design |
| SEL-07 | Tratamento de degenerescência e rejeição de seleções vazias via `DataIntegrityError` | RNF05, ADR-005 | in design |
| SEL-08 | Pureza de tempo de execução com arrays NumPy puros sem dependências externas | RNF01, XCUT-02 | in design |
