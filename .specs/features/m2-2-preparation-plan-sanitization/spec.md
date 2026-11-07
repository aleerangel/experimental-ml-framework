# M2.2 — Preparation Plan and Sanitized Dataset View (m2-2-preparation-plan-sanitization) Specification

**Approved**: 2026-11-07 - user: "aprovado"

## Problem Statement

O Marco M2.1 entregou o motor de diagnóstico e profiling estrutural (`profile_dataset` e `DatasetProfile`), identificando problemas confirmados de integridade (`CONFIRMED_ISSUE`) e alertas heurísticos (`HEURISTIC_WARNING`). Contudo, o framework ainda não possui o mecanismo para declarar formalmente o tratamento dessas anomalias nem para produzir a visão saneada dos dados (`SanitizedDatasetView`) necessária para o particionamento (M2.3) e execução de modelos.

Sem um plano explícito de preparação (`PreparationPlan`), transformações poderiam ocorrer de forma silenciosa ou arbitrária, violando o princípio de zero mutações silenciosas e o requisito de prevenção de vazamento de dados (**ADR-002**), que proíbe o ajuste global de transformações que aprendem parâmetros a partir dos dados (imputação, escalonamento ou codificação) antes da partição treino/validação.

O Sub-marco M2.2 resolve esse problema fornecendo:
1. `create_preparation_plan(profile, rules)`: construtor puro que exige regras explícitas para todos os `CONFIRMED_ISSUE`, emitindo status `READY` apenas sob cobertura total ou `INCOMPLETE` com listagem de achados pendentes.
2. `sanitize_dataset(bundle, profile, plan)`: executor puro que aplica estritamente as regras estruturais pré-partição (`DROP_ROWS`, `EXCLUDE_COLUMN`, `MAP_BINARY_TARGET`), mantendo colunas deferidas (`DEFER_INTRA_FOLD`, `ACCEPT_AS_IS`) 100% inalteradas, e gerando a estrutura imutável `SanitizedDatasetView` com novo `dataset_hash` canônico e preservação estrita do `DatasetBundle` original.

## Out of Scope

Explicitamente excluído para manter isolamento e controle de escopo:

| Feature | Reason |
| --- | --- |
| Ajuste ou aplicação de imputação numérica (`MEAN`, `MEDIAN`, `MODE`) | ADR-002: deve ser ajustado e aplicado exclusivamente dentro de cada fold na Etapa 4B |
| Ajuste ou aplicação de codificação categórica (`ONE_HOT`, `ORDINAL`, etc.) | ADR-002: o vocabulário e a execução de codificação pertencem aos Marcos M4 e M5 |
| Geração e validação de partições (`PartitionPlan`) | Escopo do Sub-marco M2.3 |
| Interface de linha de comando (`expml data prepare`, `expml data sanitize`) | Escopo do Sub-marco M2.4 |
| Persistência atômica em disco de arquivos JSON | Escopo do Sub-marco M2.4 |
| `TargetTransformSpec` e transformações reversíveis de alvo | Alocado na Onda 2 (Decisão D1 aprovada) |
| Suporte a múltiplos alvos simultâneos (`MULTI_TARGET_REGRESSION`) | Alocado na Onda 2 |
| Regras específicas de domínio aplicado | RNF02: o framework permanece 100% agnóstico a domínio |

---

## Assumptions & Open Questions

As premissas e decisões de projeto baseiam-se nas decisões consolidadas D1 a D12 de M2 e nas regras de governança arquitetural.

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| D2 / AUD-F-011: Mapeamento de alvo binário | `MAP_BINARY_TARGET(positive_label)` mapeia explicitamente a classe positiva para `1` e a alternativa para `0` em `int64`, registrando `target_label_mapping` na visão sem alterar o módulo `metrics` | Evita inferência silenciosa e preserva rastreabilidade entre rótulos originais e codificação numérica | y |
| D5: Vocabulário fechado de regras | Estruturais: `DROP_ROWS`, `EXCLUDE_COLUMN`, `MAP_BINARY_TARGET`. Declarativas: `DEFER_INTRA_FOLD` (estratégias `MEAN`, `MEDIAN`, `MODE` ou encoding), `ACCEPT_AS_IS` | Garante que nenhuma transformação com aprendizado de parâmetros ocorra antes do particionamento (ADR-002) | y |
| Admissibilidade estrita por código | Cada código de `CONFIRMED_ISSUE` aceita apenas o subconjunto documentado no catálogo; regras direcionadas a códigos inexistentes ou `HEURISTIC_WARNING` são rejeitadas com `ConfigurationError` | Impede parametrizações inválidas ou regras órfãs no plano de preparação | y |
| Imutabilidade da visão saneada | `SanitizedDatasetView` encapsula arrays com `writeable = False`, mapeamentos com `MappingProxyType` e tuplas imutáveis de `ObservationId` | Garante que a visão não sofra mutações acidentais pelas etapas subsequentes | y |
| Invariância do `DatasetBundle` fonte | `sanitize_dataset` não modifica o `bundle` original em memória; `bundle.dataset_hash` e arrays de entrada permanecem idênticos antes e após a chamada | Integridade garantida da base de entrada para múltiplas derivações experimentais | y |
| Preservação de ordem e linhagem | `SanitizedDatasetView.observation_ids` preserva a ordenação relativa original do bundle, filtrando apenas linhas descartadas; `dropped_observation_ids` registra a sequência descartada | Rastreabilidade retrospectiva ponta a ponta por observação | y |
| Validação de não-vacuidade | Se o saneamento resultar em 0 observações válidas ou 0 features candidatas, levanta `DataIntegrityError` | Impede avanço para particionamento de datasets vazios ou sem preditores | y |

**Open questions:** none - as decisões estruturais e o catálogo de regras foram consolidados e aprovados nas decisões D1 a D12 do Marco M2.

---

## User Stories

### P1: M2.2 — Plano de preparação e visão saneada ⭐ MVP

**User Story**: Como pesquisador, quero declarar regras explícitas para cada problema confirmado identificado no perfil e obter uma visão saneada imutável da base, para fixar o universo amostral antes do particionamento sem ajustar estatísticas globais.

**Why P1**: Atende ao critério de aceitação `CA-E1-02` e à diretriz `ADR-002`. Define o universo de observações e atributos candidatos consumido pelas etapas subsequentes do ciclo experimental.

**Acceptance Criteria**:

1. WHEN `create_preparation_plan(profile, rules)` receives exactly one admissible rule for every `CONFIRMED_ISSUE` key in `profile.findings` THEN the system SHALL return an immutable `PreparationPlan` with `status = "READY"`, bound to `profile.source_dataset_hash` and to the profile digest, with rules in canonical order (PREP-01).
2. WHEN at least one `CONFIRMED_ISSUE` key has no rule, or the profile holds a `CONFIRMED_ISSUE` with no admissible rule THEN the system SHALL return `status = "INCOMPLETE"` with `unresolved_findings` listing every uncovered `(code, column)` (PREP-02).
3. IF a rule targets a key that is not a `CONFIRMED_ISSUE` of the profile, duplicates another rule for the same key, uses a rule kind not admissible for its code, or carries invalid parameters THEN the system SHALL raise `ConfigurationError` (PREP-03).
4. WHEN `sanitize_dataset(bundle, profile, plan)` receives a `READY` plan whose bindings match the bundle and the profile THEN the system SHALL apply only `DROP_ROWS`, `EXCLUDE_COLUMN` and `MAP_BINARY_TARGET` and SHALL return an immutable `SanitizedDatasetView` (PREP-04).
5. IF `plan.status` is not `READY` THEN the system SHALL raise `ContractViolationError` and SHALL NOT build a view, and IF the plan, profile and bundle bindings diverge THEN the system SHALL raise `DataIntegrityError` (PREP-05).
6. The `SanitizedDatasetView` SHALL expose `observation_ids` as a tuple of `ObservationId` preserving the original relative order, `candidate_feature_cols`, `dropped_observation_ids`, `target_label_mapping`, `deferred_rules`, the source dataset hash, the plan digest and a `dataset_hash` equal to `core.dataset_hash(view.columns, view.schema, observation_ids=view.observation_ids)` (PREP-06).
7. WHILE a column is covered only by `DEFER_INTRA_FOLD` or `ACCEPT_AS_IS` the system SHALL keep its values, including missing values, bit-identical to the source bundle (PREP-07).
8. WHEN `MAP_BINARY_TARGET(positive_label)` is applied THEN the system SHALL encode the target as `int64` with `positive_label` mapped to 1 and the other class mapped to 0, and SHALL record the mapping in `target_label_mapping` (PREP-08).
9. IF sanitization leaves zero observations or zero candidate feature columns THEN the system SHALL raise `DataIntegrityError` (PREP-09).
10. WHEN `sanitize_dataset` returns THEN the source `DatasetBundle` SHALL keep its `dataset_hash` and column buffers unchanged, and identical bundle, profile and plan SHALL yield an identical view `dataset_hash` and plan digest (PREP-10).

---

## Requirement Traceability

| Requirement ID | Description | Source / Rationale | Status |
| :--- | :--- | :--- | :--- |
| PREP-01 | Geração de `PreparationPlan` com `status = "READY"` sob cobertura total | CA-E1-02, D4, ADR-002 | in design |
| PREP-02 | Geração de plano `INCOMPLETE` sob cobertura parcial ou achados irresolúveis | CA-E1-02, D4 | in design |
| PREP-03 | Validação de regras e rejeição de regras inválidas/inadmissíveis via `ConfigurationError` | D5, RNF07 | in design |
| PREP-04 | Aplicação exclusiva de regras estruturais (`DROP_ROWS`, `EXCLUDE_COLUMN`, `MAP_BINARY_TARGET`) | ADR-002, CA-E1-02 | in design |
| PREP-05 | Bloqueio de saneamento sob status não-READY ou divergência de hashes de ligação | CA-GER-01, CA-E1-02 | in design |
| PREP-06 | Contrato imutável de `SanitizedDatasetView` com equivalência de `dataset_hash` | ADR-007, ADR-008, CA-E1-01 | in design |
| PREP-07 | Preservação bit a bit de colunas com regras deferidas ou aceitas sem mutação | ADR-002, RF1.7 | in design |
| PREP-08 | Codificação rastreável e determinística de alvo binário textual em `{0, 1}` | D2, AUD-F-011 | in design |
| PREP-09 | Validação de não-vacuidade de linhas e atributos candidatos após sanitização | RF1.1, RNF05 | in design |
| PREP-10 | Imutabilidade e determinismo do saneamento com preservação do bundle de entrada | ADR-007, ADR-008, CA-E1-01 | in design |
