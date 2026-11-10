# M3.2 — Definição e Validação de Cenários de Features (m3-2-feature-scenarios) Specification

**Approved**: 2026-11-10 - user: "podemos"

## Problem Statement

Na Etapa 2 do pipeline experimental (`features`), após a análise exploratória (M3.1), o pesquisador precisa definir, comparar e versionar **Cenários de Features** (`RF2.2`, `RF2.3`, `CA-E2-02`). Cenários são coleções declarativas que representam hipóteses científicas de modelagem (ex.: subconjuntos biométricos mínimos, conjunto completo de atributos ou seleção orientada a dados).

Contudo, sem uma camada formal de modelagem, validação e governança de cenários:
1. **Risco de Vazamento de Dados (*Data Leakage*):** Se cenários dinâmicos (seleção por relevância, redução de multicolinearidade, Top-$K$) calcularem ou fixarem listas de features a partir da base completa antes do particionamento, incorre-se em vazamento pré-partição (*selection bias*), violando o requisito `RF2.4` e a diretriz `ADR-002`.
2. **Inconsistência de Esquema e Contaminação de Papéis:** Cenários manuais (`FIXED`) podem acidentalmente incluir a variável-alvo, colunas de agrupamento (`group_col`), índices temporais ou atributos proibidos/excluídos no saneamento da Etapa 1.
3. **Falta de Rastreabilidade e Reprodutibilidade:** Sem um catálogo versionado e vinculado ao hash da visão saneada (`dataset_hash`), etapas posteriores (Etapa 4B e Etapa 5) não podem garantir que os modelos foram treinados sobre os mesmos recortes conceituais.

O Sub-marco M3.2 resolve essa demanda implementando o motor de definição, validação e persistência de cenários de features:
- `FeatureScenario`: modelo de dados imutável declarativo, suportando os modos `"FIXED"` e `"DYNAMIC"`, sem hierarquia de herança de classes (ADR-008).
- `validate_scenarios(scenarios, view)`: validador puro que assegura que cenários fixos contenham apenas atributos candidatos válidos e disjuntos de papéis protegidos, que cenários dinâmicos não definam listas pré-calculadas e que todos os identificadores sejam únicos.
- `ScenariosCatalog`: catálogo imutável vinculado ao `dataset_hash` da `SanitizedDatasetView`.
- Persistência atômica (`save_scenarios`, `load_scenarios`) em `configuration/scenarios.json` e portão de validação de etapa (`verify_scenarios_gate`).

## Out of Scope

Explicitamente excluído para manter isolamento e controle de escopo:

| Feature | Reason |
| --- | --- |
| Execução da seleção dinâmica intra-fold (`select_features_in_fold`) | Escopo do Sub-marco M3.3 |
| Métricas de estabilidade de seleção (Jaccard, Kuncheva) entre folds | Escopo do Sub-marco M3.3 |
| Interface de linha de comando (`expml features scenarios`) | Escopo do Sub-marco M3.4 |
| Execução de modelos sobre cenários e folds (matriz experimental) | Pertence ao Marco M5 (`orchestration`) |
| Pré-processamento específico de modelos (Camada 2) | Pertence ao Marco M4 (`models`) |
| Regras específicas de domínio aplicado | RNF02: o framework permanece 100% agnóstico a domínio |

---

## Assumptions & Open Questions

As premissas baseiam-se nos requisitos RF2.2, RF2.3, CA-E2-02, nas decisões de arquitetura (ADR-002, ADR-007, ADR-008) e nas regras de governança do framework:

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Estrutura Declarativa sem Herança | `FeatureScenario` é um contêiner imutável único parametrizado por `mode` (`"FIXED"` ou `"DYNAMIC"`). | Aderência estrita à ADR-008 (funções puras e estruturas simples, sem hierarquias OOP) | y |
| Invariante Anti-Leakage para Dinâmicos | Cenários `DYNAMIC` proíbem estritamente a atribuição de `selected_features` na Etapa 2; apenas declaram `strategy_name` e `strategy_params`. | Previne formalmente vazamento de dados pré-partição (RF2.4, ADR-002) | y |
| Disjunção Estrita com Papéis Protegidos | Colunas em cenários `FIXED` devem pertencer a `view.candidate_feature_cols` e ter interseção vazia com `{target_col, group_col, observation_id_col, time_col} ∪ ignore_cols`. | Evita que atributos administrativos, identificadores ou o próprio alvo entrem como preditores | y |
| Vinculação Criptográfica com Sanitized View | `ScenariosCatalog` e `scenarios.json` armazenam obrigatoriamente `dataset_hash = view.dataset_hash`. | Garante linhagem estrita entre a base saneada e a configuração experimental (CA-GER-01) | y |
| Validação Transacional e Portão de Etapa | `verify_scenarios_gate` bloqueia o avanço para etapas posteriores se o arquivo não existir, se o hash divergir ou se houver violação de esquema. | Garante a integridade dos portões de entrada e saída (RNF05, RNF07) | y |

**Open questions:** none - as estruturas e regras de validação de cenários foram consolidadas e especificadas em `ARQUITETURA_E_CONTRATOS.md`.

---

## User Stories

### P1: M3.2 — Definição e Validação de Cenários de Features ⭐ MVP

**User Story**: Como pesquisador, quero definir cenários de features fixos e dinâmicos de forma declarativa e validá-los formalmente contra a visão saneada da base de dados, garantindo ausência de vazamento de dados e persistindo o catálogo em `scenarios.json`, para configurar as hipóteses experimentais que serão avaliadas nas etapas de modelagem.

**Why P1**: Atende diretamente aos requisitos `RF2.2`, `RF2.3` e ao critério de aceitação `CA-E2-02`. Sem a validação e o catálogo de cenários, as etapas subsequentes de treino intra-fold (M3.3) e execução matricial (M5) não possuem especificações confiáveis de entrada.

**Acceptance Criteria**:

1. WHEN a `FeatureScenario` is instantiated THEN the system SHALL enforce immutability (`frozen=True`, `slots=True`), validated fields (`scenario_id` as non-empty valid identifier slug, `name`, `description`, `scientific_justification`, and `mode` in `{"FIXED", "DYNAMIC"}`), and immutable parameter conversion (`preprocessing_config` and `strategy_params` wrapped in `MappingProxyType`) (SCN-01).

2. WHEN a scenario has `mode = "FIXED"` THEN the system SHALL require a non-empty sequence of `selected_features` without duplicates, and forbid `strategy_name` or non-empty `strategy_params` (SCN-02).

3. WHEN a scenario has `mode = "DYNAMIC"` THEN the system SHALL require a non-empty `strategy_name`, allow `strategy_params`, and strictly forbid pre-calculated `selected_features` (`selected_features` must be empty/None) to prevent data leakage prior to fold execution (SCN-03).

4. WHEN `validate_scenarios(scenarios, view)` is called THEN the system SHALL verify that:
   (a) all `scenario_id`s in the collection are unique;
   (b) for each `FIXED` scenario, all `selected_features` exist in `view.candidate_feature_cols` and have zero intersection with `{target_col, group_col, observation_id_col, time_col} ∪ ignore_cols`;
   (c) for each `DYNAMIC` scenario, `strategy_name` is non-empty;
   and SHALL return an immutable `ScenariosCatalog` bound to `view.dataset_hash` (SCN-04).

5. WHEN `validate_scenarios` encounters duplicate scenario IDs, empty scenario sequences, unknown features, or features intersecting with protected roles (target, group, observation_id, time, ignore_cols) THEN the system SHALL raise a typed domain error (`ContractViolationError` or `ConfigurationError`) with an explicit diagnostic message and refuse catalog creation (SCN-05).

6. WHEN `catalog.to_dict()` is serialized to JSON UTF-8 NFC THEN `ScenariosCatalog.from_dict(data)` SHALL reconstruct an identical `ScenariosCatalog` instance with identical scenario records, order, and `dataset_hash` (SCN-06).

7. WHEN `save_scenarios(catalog, path, overwrite=False)` is executed THEN the system SHALL atomically write `scenarios.json` using `write_json_atomic`, raising `ConfigurationError` if the destination exists and `overwrite=False`, and `load_scenarios(path)` SHALL restore the validated catalog (SCN-07).

8. WHEN `verify_scenarios_gate(catalog_path, view)` is executed THEN the system SHALL verify the physical existence of the scenarios file, assert that `catalog.dataset_hash == view.dataset_hash`, re-run structural scenario validation against the view, and raise `ContractViolationError` or `DataIntegrityError` upon any mismatch or missing file (SCN-08).

---

## Requirement Traceability

| Requirement ID | Description | Source / Rationale | Status |
| :--- | :--- | :--- | :--- |
| SCN-01 | Estrutura imutável e declarativa `FeatureScenario` com validação de campos e parâmetros imutáveis | RF2.2, ADR-008 | in design |
| SCN-02 | Validação de restrições de cenários `FIXED` (atributos explícitos e sem estratégia dinâmica) | RF2.2, CA-E2-02 | in design |
| SCN-03 | Invariante anti-leakage para cenários `DYNAMIC` (proibição de atributos pré-calculados) | RF2.3, RF2.4, ADR-002 | in design |
| SCN-04 | Validação de catálogo de cenários contra `SanitizedDatasetView` e vinculação de `dataset_hash` | CA-E2-02, CA-GER-01 | in design |
| SCN-05 | Rejeição estrita de IDs duplicados, atributos desconhecidos ou colunas protegidas | RNF05, RNF07 | in design |
| SCN-06 | Serialização determinística `.to_dict()` e reconstrução `.from_dict()` compatível com JSON | ADR-007, ADR-008 | in design |
| SCN-07 | Persistência atômica (`save_scenarios`) com `write_json_atomic` e carregamento (`load_scenarios`) | STORE-01, CA-GER-01 | in design |
| SCN-08 | Portão de etapa `verify_scenarios_gate` com verificação de integridade e correspondência de hash | RNF05, CA-GER-01 | in design |
