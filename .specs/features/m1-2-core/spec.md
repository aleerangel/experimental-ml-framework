# m1-2-core Specification

**Approved**: 2026-10-31 - user: "avança"

## Problem Statement

O framework `experimental-ml-framework` necessita de uma camada fundacional transversal (`core`, Nível 0 da arquitetura) que estabeleça os tipos elementares, constantes, enumerações, geradores de sementes e algoritmos de integridade criptográfica. Sem essa fundação, os módulos funcionais subsequentes (`metrics` em M1.3, `data` e `validation` em M2) não possuem definições padronizadas para identificadores imutáveis, controle de estado, derivação determinística de pseudoaleatoriedade ou garantia de rastreabilidade e integridade via hashes canônicos imunes a variações de plataforma.

## Goals

- [ ] Implementar tipos de identificadores de domínio imutáveis e validadores de integridade estrutural (`ExperimentId`, `PartitionPlanId`, `ScenarioId`, `ModelId`, `CellId`, `ComparisonId`, `ArtifactId`, `ObservationId`).
- [ ] Definir o conjunto fechado de enumerações canônicas do ciclo experimental (`TaskType`, `ExecutionStatus`, `FindingSeverity`, `MetricDirection`, `AggregationScope`, `MetricStatus`, `ErrorPolicy`).
- [ ] Implementar funções puras de derivação hierárquica e determinística de sementes pseudoaleatórias (`derive_seeds`, `spawn_child_seeds`) baseadas em `numpy.random.SeedSequence`.
- [ ] Implementar a função de serialização canônica e hashing de configurações `config_hash(obj)` conforme o contrato formal do **ADR-007** (Unicode NFC, distinção estrita de escalares, tipos compostos e tratamento de `NaN`/`Inf` e `-0.0`).
- [ ] Implementar a função de hash de dados tabulares `dataset_hash(data_or_path, schema)` com suporte a arquivos brutos e estruturas em memória.
- [ ] Fornecer construtores padronizados para registros de diagnósticos estruturados (`make_finding`, `make_warning`) e exceções formais de violação de contrato.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Catálogo de métricas, `MetricValue` e funções de métricas | Pertencem ao Marco M1.3 (`metrics`). |
| Ingestão de arquivos CSV/TXT, sanitização e plano de preparação | Pertencem ao Marco M2 (`data`). |
| Algoritmos de particionamento (K-Fold, Stratified, Group) | Pertencem ao Marco M2 (`validation`). |
| Classes de serviço com estado mutável ou orientação a objetos | Vedação arquitetural permanente do framework (**ADR-008**). |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Dependência externa de NumPy | `numpy>=1.24.0` adicionada a `pyproject.toml` | Obrigatória para `numpy.random.SeedSequence` e tipos numéricos IEEE 754 conforme especificado no ADR-007 e Seção 7.1 de `ARQUITETURA_E_CONTRATOS.md`. | y |
| Formato dos hashes gerados | String hexadecimal minúscula de 64 caracteres (SHA-256) | Padrão FIPS 180-4 adotado em toda a especificação arquitetural (ADR-007). | y |
| Natureza dos identificadores | Tipos baseados em `str` validados (`NewType` ou subclasses imutáveis de string) | Permite validação estrita sem custo de serialização ou perda de interoperabilidade com JSON e dicionários. | y |
| Representação de enumerações | Subclasses de `str, Enum` (compatível com `StrEnum` do Python 3.11+) | Permite serialização JSON direta e preserva legibilidade sem coerção manual de tipos. | y |
| Organização do submódulo | Pacote `src/experimental_ml/core/` com submódulos temáticos (`types`, `enums`, `seeds`, `hashing`, `findings`) e reexportação no `__init__.py` | Mantém coesão física e atende ao Nível 0 de dependências arquiteturais sem arquivos monolíticos. | y |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Identificadores Imutáveis e Tipos de Domínio ⭐ MVP

**User Story**: Como desenvolvedor do framework, quero tipos padronizados para identificadores de domínio (`ExperimentId`, `PartitionPlanId`, `ScenarioId`, `ModelId`, `CellId`, `ComparisonId`, `ArtifactId`, `ObservationId`), para que o sistema impeça identificadores vazios, inválidos ou misturas acidentais de tipos.

**Why P1**: É a base de rastreabilidade de todo o ciclo experimental; todo registro e artefato persistido depende desses identificadores.

**Acceptance Criteria**:

1. The system SHALL provide immutable string-based types for domain identifiers: `ExperimentId`, `PartitionPlanId`, `ScenarioId`, `ModelId`, `CellId`, `ComparisonId`, `ArtifactId`, and `ObservationId`.
2. The system SHALL validate that identifier values are non-empty strings, stripped of leading and trailing whitespace.
3. IF an empty string, pure whitespace, or non-string value is passed to an identifier constructor, THEN the system SHALL raise a `ValidationError` or `ValueError` with an informative error message.

**Independent Test**: Instanciar cada tipo de identificador com valores válidos comprovando imutabilidade e igualdade, e verificar que valores nulos ou vazios disparam exceção imediata.

---

### P1: Enumerações Fundamentais do Ciclo Experimental ⭐ MVP

**User Story**: Como desenvolvedor de módulos experimentais, quero enumerações estritas para modalidades de tarefa, status de execução, severidade de achados, direção de métrica, escopo de agregação, status de métrica e política de erro, para garantir consistência e evitar strings arbitrárias.

**Why P1**: Garante integridade semântica em todas as etapas, impedindo erros de digitação ou estados não previstos.

**Acceptance Criteria**:

1. The system SHALL define `TaskType` supporting values `"REGRESSION"`, `"MULTI_TARGET_REGRESSION"`, `"BINARY_CLASSIFICATION"`, and `"MULTICLASS_CLASSIFICATION"`.
2. The system SHALL define `ExecutionStatus` supporting values `"PENDING"`, `"RUNNING"`, `"COMPLETED"`, `"FAILED"`, and `"CANCELLED"`.
3. The system SHALL define `FindingSeverity` supporting values `"CONFIRMED_ISSUE"` and `"HEURISTIC_WARNING"`.
4. The system SHALL define `MetricDirection` supporting values `"MAXIMIZE"` and `"MINIMIZE"`.
5. The system SHALL define `AggregationScope` supporting values `"FOLD_AGGREGATION"`, `"REPETITION_AGGREGATION"`, and `"OVERALL_AGGREGATION"`.
6. The system SHALL define `MetricStatus` supporting values `"VALID"`, `"UNDEFINED_NAN"`, `"PARTIAL_COVERAGE"`, and `"UNRANKABLE"`.
7. The system SHALL define `ErrorPolicy` supporting values `"FAULT_TOLERANT"` and `"FAIL_FAST"`.
8. The system SHALL implement all fundamental enums as string-compatible enums (`str, Enum`), ensuring direct equality with string literals and native JSON serialization.

**Independent Test**: Verificar que cada enum possui exatamente os membros especificados, compara com strings literais e serializa nativamente para JSON.

---

### P1: Derivação Hierárquica Determinística de Sementes ⭐ MVP

**User Story**: Como pesquisador, quero derivar sequências de sementes reprodutíveis a partir de uma semente mestre utilizando `numpy.random.SeedSequence`, para que execuções sequenciais ou paralelas produzam fluxos estocásticos independentes e idênticos sob a mesma semente inicial.

**Why P1**: É a garantia matemática de reprodutibilidade experimental exigida pelo RNF01 e pelo ADR-007.

**Acceptance Criteria**:

1. The system SHALL implement `derive_seeds(master_seed: int, count: int) -> tuple[int, ...]` using `numpy.random.SeedSequence`.
2. The system SHALL implement `spawn_child_seeds(parent_seed: int, count: int) -> tuple[int, ...]` deriving independent child seed sequences.
3. WHEN called with the same `master_seed` and `count`, THEN `derive_seeds` SHALL deterministically produce the exact same tuple of integers.
4. IF `count` is less than 1, THEN `derive_seeds` and `spawn_child_seeds` SHALL raise a `ValueError`.
5. WHEN spawning child seeds, THEN the resulting integer values SHALL be distinct from one another with high probability and valid as random states.

**Independent Test**: Executar `derive_seeds` múltiplas vezes com a mesma semente verificando identidade exata dos resultados e independência estocástica entre sementes geradas.

---

### P1: Serialização Canônica e Hashing de Configurações (`config_hash`) ⭐ MVP

**User Story**: Como pesquisador e auditor de experimentos, quero calcular hashes canônicos determinísticos de configurações (`config_hash`) imunes a ordenação de chaves, decomposição Unicode e representações numéricas equivalentes, para que qualquer alteração de hiperparâmetros ou opções seja detectada com precisão.

**Why P1**: Núcleo da verificação de integridade entre etapas e detecção de desvios (ADR-007).

**Acceptance Criteria**:

1. The system SHALL implement `config_hash(obj: Any) -> str` returning a lowercase 64-character hexadecimal SHA-256 digest over canonical UTF-8 bytes.
2. The system SHALL normalize all string values to Unicode NFC (`unicodedata.normalize("NFC", s)`) before computing `config_hash`.
3. The system SHALL sort dictionary keys lexicographically by UTF-8 code points, ensuring invariance of `config_hash` to key insertion order.
4. The system SHALL strictly distinguish scalar types in `config_hash`: `True` SHALL NOT equal `1`, `False` SHALL NOT equal `0`, and integer `1` SHALL NOT equal float `1.0`.
5. The system SHALL distinguish collection types: a `tuple` SHALL produce a distinct `config_hash` from a `list` containing identical elements.
6. The system SHALL sort `set` and `frozenset` elements by their canonical item hashes, ensuring invariance to set insertion order.
7. The system SHALL normalize `-0.0` to `0.0`, and normalize all `NaN` payloads to a canonical representation `{"__float_special__": "NaN"}` while keeping distinct canonical representations for `+Inf` and `-Inf`.

**Independent Test**: Executar suíte de testes de asserção de hashes canônicos validando igualdades obrigatórias (NFC vs NFD, ordem de chaves, -0.0 vs +0.0) e distinções obrigatórias (bool vs int, int vs float, list vs tuple).

---

### P1: Hashing de Dados Tabulares (`dataset_hash`) ⭐ MVP

**User Story**: Como pesquisador, quero calcular um hash de integridade estrutural da base de dados (`dataset_hash`), tanto para arquivos em disco quanto para estruturas em memória, para ancorar a linhagem de reprodutibilidade e impedir execução sobre dados modificados.

**Why P1**: Atende ao critério de integridade do RNF06 e ao critério de aceitação `CA-E1-01`.

**Acceptance Criteria**:

1. The system SHALL implement `dataset_hash(data_or_path: Union[str, Path, Any], schema: Optional[Any] = None) -> str` returning a lowercase 64-character hexadecimal SHA-256 digest.
2. WHEN given an existing file path (`.csv` or `.txt`), THEN `dataset_hash` SHALL compute the SHA-256 of the raw file contents combined with the canonical hash of the schema if provided.
3. WHEN given in-memory tabular data, THEN `dataset_hash` SHALL compute a deterministic digest across columns and row observations using little-endian binary buffers and NFC text.
4. IF two tabular datasets have identical values but different column names, different data types, or different observation order, THEN `dataset_hash` SHALL produce different hashes.
5. IF a non-existent file path is provided, THEN `dataset_hash` SHALL raise a `FileNotFoundError`.

**Independent Test**: Calcular `dataset_hash` de arquivo CSV sintético e de dados em memória, comprovando que alterações em valores, nomes de colunas ou tipos alteram o hash final.

---

### P1: Construtores de Diagnósticos e Sinalizadores de Contrato ⭐ MVP

**User Story**: Como desenvolvedor de módulos das etapas, quero construtores padronizados para achados de integridade (`make_finding`, `make_warning`) e exceções formais do framework, para padronizar erros estruturados e alertas pedagógicos.

**Why P1**: Exigência central do RNF07 e da separação formal entre problemas confirmados e alertas heurísticos (RF1.6 e ADR-002).

**Acceptance Criteria**:

1. The system SHALL implement `make_finding(code: str, message: str, context: Optional[dict] = None) -> Finding` representing a confirmed issue (`FindingSeverity.CONFIRMED_ISSUE`).
2. The system SHALL implement `make_warning(code: str, message: str, context: Optional[dict] = None) -> Finding` representing a heuristic warning (`FindingSeverity.HEURISTIC_WARNING`).
3. The system SHALL provide framework-specific exceptions: `ContractViolationError`, `DataIntegrityError`, and `ConfigurationError`.
4. The system SHALL ensure that `Finding` objects are immutable structures containing `severity`, `code`, `message`, and optional `context`.

**Independent Test**: Construir achados de erro e alerta, inspecionar campos, imutabilidade e disparar exceções de contrato verificando mensagens e tipos.

---

## Edge Cases

- IF a floating point value is negative zero (`-0.0`), THEN `config_hash` SHALL treat it as positive zero (`0.0`).
- IF a floating point value is `NaN` (qualquer NaN IEEE 754), THEN `config_hash` SHALL normalize it to `{"__float_special__": "NaN"}`.
- IF an object contains circular references, THEN `config_hash` SHALL raise a `ValueError` indicating recursion depth exceeded.
- IF an unsupported object type is passed to `config_hash`, THEN the system SHALL raise a `TypeError` indicating non-serializable type.
- IF an identifier contains newline, carriage return, or tab characters, THEN identifier validation SHALL reject it with `ValueError`.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| CORE-01 | P1: Identificadores Imutáveis | Specify | Pending |
| CORE-02 | P1: Identificadores Imutáveis | Specify | Pending |
| CORE-03 | P1: Identificadores Imutáveis | Specify | Pending |
| CORE-04 | P1: Enumerações Fundamentais | Specify | Pending |
| CORE-05 | P1: Enumerações Fundamentais | Specify | Pending |
| CORE-06 | P1: Enumerações Fundamentais | Specify | Pending |
| CORE-07 | P1: Derivação de Sementes | Specify | Pending |
| CORE-08 | P1: Derivação de Sementes | Specify | Pending |
| CORE-09 | P1: Derivação de Sementes | Specify | Pending |
| CORE-10 | P1: Hashing de Configurações | Specify | Pending |
| CORE-11 | P1: Hashing de Configurações | Specify | Pending |
| CORE-12 | P1: Hashing de Configurações | Specify | Pending |
| CORE-13 | P1: Hashing de Configurações | Specify | Pending |
| CORE-14 | P1: Hashing de Dados Tabulares | Specify | Pending |
| CORE-15 | P1: Hashing de Dados Tabulares | Specify | Pending |
| CORE-16 | P1: Hashing de Dados Tabulares | Specify | Pending |
| CORE-17 | P1: Construtores de Diagnósticos | Specify | Pending |
| CORE-18 | P1: Construtores de Diagnósticos | Specify | Pending |

---

## Sources

- `ARQUITETURA_E_CONTRATOS.md` Seção 2.1, 2.3, 7.1 — Define o escopo transversal do módulo `core`, níveis de dependência (Nível 0) e os critérios de aceitação do Marco M1.2 (`TA-M1.2`).
- `ARQUITETURA_E_CONTRATOS.md` ADR-007 — Define o contrato formal de serialização canônica para `config_hash` e `dataset_hash`.
- `ARQUITETURA_E_CONTRATOS.md` ADR-008 — Diretriz de programação modular baseada em funções puras e estruturas de dados imutáveis (sem OOP).
- `ESPECIFICACAO_REQUISITOS.md` RNF01, RNF06, `CA-GER-01`, `CA-GER-02` — Especificação de determinismo de sementes, canonicidade de hashes e códigos de integridade.

---

## Success Criteria

- [ ] Todos os identificadores de domínio são instanciáveis, imutáveis e rejeitam strings vazias.
- [ ] Todas as enumerações fundamentais contêm os membros requeridos e são serializáveis para JSON.
- [ ] `derive_seeds` e `spawn_child_seeds` produzem sementes reprodutíveis e determinísticas com `numpy.random.SeedSequence`.
- [ ] `config_hash` cumpre 100% das regras canônicas do ADR-007 (NFC, ordenação de chaves, `-0.0 == 0.0`, distinção estrita de tipos escalares e coleções).
- [ ] `dataset_hash` calcula hashes SHA-256 determinísticos para arquivos e dados em memória, diferenciando esquemas, nomes de colunas e dados.
- [ ] Construtores `make_finding` e `make_warning` criam registros estruturados imutáveis e exceções do framework são devidamente hierarquizadas.
- [ ] Suíte de testes `tests/unit/test_core.py` implementada com 100% de aprovação.
