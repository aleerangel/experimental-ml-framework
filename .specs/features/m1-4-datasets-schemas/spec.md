# m1-4-datasets-schemas Specification

**Approved**: 2026-11-04 - user: "aprovado. commita e espera"

## Problem Statement

O `experimental-ml-framework` necessita de uma camada fundacional de ingestão tabular imutável e validação estrutural de esquemas (`experimental_ml.data`, Nível 1 da arquitetura) que carregue dados a partir de arquivos em disco (`.csv`, `.txt`, `.tsv`) ou estruturas em memória (`dict`, `ndarray` 2D, `DataFrame` duck-typed), valide a consistência entre os dados e os papéis declarados no `DatasetSchemaSpec` (`target_col`, `task_type`, `group_col`, `observation_id_col`, `time_col`, `ignore_cols`, `column_semantic_types`), atribua ou valide identificadores únicos de observação (`ObservationId`) e produza um `DatasetBundle` com isolamento de memória estrito e propriedade exclusiva dos dados, vinculado ao `dataset_hash` canônico do conteúdo carregado e ao `raw_source_hash` da fonte original (**ADR-007**). Sem esse contrato estrutural, as etapas subsequentes de perfilamento estatístico (`profile_dataset`), saneamento (`sanitize_dataset`) e particionamento (`build_partition_plan`) no Marco M2 ficariam expostas a mutações silenciosas de referências compartilhadas, reativação de escrita em arrays NumPy, parsing ambíguo de delimitadores, confusão entre tipos físicos e significado semântico, colisões de identificadores de observação ou perda de rastreabilidade criptográfica da base original (`RF1.1`, `RF1.7`, `CA-E1-01`).

## Goals

- [ ] Definir a enumeração `ColumnSemanticType(StrEnum)` e as estruturas de dados imutáveis (`@dataclass(frozen=True, slots=True)`) de esquema e representação tabular: `DatasetSchemaSpec`, `ColumnDescriptor` e `DatasetBundle`.
- [ ] Validar estritamente o esquema declarativo (`DatasetSchemaSpec`), assegurando disjunção entre papéis de colunas (`target_col`, `group_col`, `observation_id_col`, `time_col`, `ignore_cols`), suporte opcional à especificação manual de tipos semânticos (`column_semantic_types`), normalização Unicode NFC de nomes de colunas e conformidade com o recorte da Onda 1 do MVP (`REGRESSION`, `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION` com `target_col: str`).
- [ ] Implementar a ingestão tabular determinística (`load_dataset`) com parsing estrito de arquivos `.csv`/`.txt`/`.tsv`, suporte a aspas RFC 4180, detecção automática segura de delimitadores com fallback e falha explícita sob ambiguidade ou linhas irregulares (*ragged rows*), além de ingestão de estruturas em memória (`Mapping`, `ndarray` 2D, sequência de registros ou `DataFrame` via duck-typing), sem dependência obrigatória de `pandas`.
- [ ] Assegurar propriedade exclusiva dos dados e imutabilidade profunda do `DatasetBundle` em memória: colunas numéricas/booleanas derivadas de buffers imutáveis `bytes` que recusam `setflags(write=True)` com `ValueError`, rejeição de objetos mutáveis em colunas `object`, arrays colunares 1D congelados com `flags.writeable = False` e dicionários encapsulados em `MappingProxyType`.
- [ ] Formalizar a semântica tripartite de identidade e regras de canonização: `raw_source_hash` (integridade da fonte bruta em disco ou memória), `dataset_hash` (conteúdo tabular canônico normalizado em memória sensível a ordem de linhas/colunas, tipos físicos e representação de nulos) e `schema_hash` (configuração declarativa do esquema), compatíveis com `core.dataset_hash` e `core.config_hash` (**ADR-007**).
- [ ] Formalizar as regras de atribuição de `ObservationId`: geração sequencial determinística `obs_000000` (identificando posições dentro da carga, com limitação explícita sob reordenação) e validação de não-nulidade e unicidade estrita quando informada na fonte, além de utilitários funcionais somente-leitura (`get_column_array`, `slice_bundle_by_observation_ids` preservando a ordem solicitada pelo chamador).

## Out of Scope

| Feature | Reason |
| --- | --- |
| Diagnóstico estatístico estrutural (`profile_dataset`, `DatasetProfile`) e classificação de anomalias (`CONFIRMED_ISSUE` vs. `HEURISTIC_WARNING`) | Pertencem ao Marco M2 (segunda etapa do módulo `experimental_ml.data`). |
| Plano de preparação (`create_preparation_plan`, `PreparationPlan`) e saneamento pré-partição (`sanitize_dataset`, `SanitizedDatasetView`) | Pertencem ao Marco M2 (`experimental_ml.data`). |
| Geração e validação matemática de partições (`build_partition_plan`, `validate_partition_plan`, `PartitionPlan`) | Pertencem ao Marco M2 (`experimental_ml.validation`). |
| Subcomandos de terminal `expml data` e `expml partition` | Pertencem ao Marco M2 (`experimental_ml.cli`). |
| Regressão multialvo (`MULTI_TARGET_REGRESSION` / `target_col: Sequence[str]`), `TargetTransformSpec` e `unlabeled_pool` | Pertencem à Onda 2 do MVP (`ARQUITETURA_E_CONTRATOS.md` Seção 6.1). |
| Imputação de valores ausentes, codificação de categorias ou escalonamento de atributos | Vedados na ingestão por construção (**Princípio 2**, **ADR-002**, `RF1.7`). |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Nome e localização do pacote Python | Implementar em `src/experimental_ml/data/` (`experimental_ml.data`, Nível 1) | `ARQUITETURA_E_CONTRATOS.md` (Seção 2.3 e 3.1), `ETAPA_ATUAL_ENGENHARIA.md` (Seção 2) e `tests/test_smoke.py` (linha 135) definem `experimental_ml.data` como o único pacote Nível 1 da Etapa 1; o M1.4 entrega a fundação de esquemas e ingestão de `data`, evitando criar um pacote paralelo `datasets` que duplicaria contratos no M2. | y |
| Dependências externas e representação em memória | Utilizar exclusivamente a biblioteca padrão do Python (`csv`, `io`, `types`, `pathlib`, `re`) e `numpy>=1.24.0`, armazenando colunas como `np.ndarray` 1D com `writeable=False` dentro de `MappingProxyType` | Mantém o projeto autônomo e offline (`RNF03`, `RNF06`), garante imutabilidade real e suporta `pandas.DataFrame` externo por *duck-typing* (`columns`, `__getitem__`, `to_numpy`) de forma idêntica ao `dataset_hash` do M1.2. | y |
| Nível de garantia de imutabilidade dos arrays | Colunas numéricas/booleanas derivadas de buffers `bytes` imutáveis (`np.frombuffer`), tornando impossível reativar escrita via `setflags(write=True)`; colunas `object` restritas a escalares imutáveis (`str`, `None`) com `writeable=False`; cópia defensiva irrestrita na ingestão | Bloqueia tanto mutações in-place diretas quanto tentativas de reativar escrita em views/arrays numéricos, isolando totalmente o bundle da memória da fonte original e de mutações no consumidor. | y |
| Semântica tripartite e canonização de hashes | `dataset_hash` reflete o conteúdo tabular canônico normalizado em memória via `core.dataset_hash(bundle.columns, schema)`; `raw_source_hash` reflete a integridade da fonte original via `core.dataset_hash(source, schema)`; `schema_hash` reflete `core.config_hash(schema)` | Permite que fontes com mesma informação lógica carregadas de CSV (`\r\n` vs `\n`) ou memória tenham o mesmo `dataset_hash`, enquanto `raw_source_hash` audita a integridade física do arquivo em disco sem alterar o Core. | y |
| Regras de detecção de delimitadores e parsing estrito | Delimitadores suportados: `,`, `;`, `\t`, `|`, e múltiplos espaços `r"[ \t]+"`. Delimiter automático avalia consistência na amostra (100 linhas); sob ambiguidade ou linhas com contagens distintas de colunas, lança `DataIntegrityError` com diagnóstico | Prioriza a integridade dos dados e impede interpretação silenciosamente incorreta de bases tabulares; permite sobrescrita manual explícita via argumento `delimiter`. | y |
| Distinção entre tipo físico e tipo semântico | `ColumnDescriptor` expõe `physical_type` (`dtype_str`), `semantic_type` (`ColumnSemanticType`) e `is_semantic_declared`; o usuário pode declarar `column_semantic_types` no schema | Evita que o framework deduza indevidamente intenção científica de colunas inteiras ou numéricas, respeitando a prerrogativa do pesquisador com fallback neutro transparente. | y |
| Semântica e estabilidade de `ObservationId` | IDs gerados (`obs_000000`) identificam posições dentro da carga corrente; reordenação da fonte altera a associação posicional; persistência entre cargas exige `observation_id_col` intrínseca; `slice_bundle_by_observation_ids` preserva estritamente a ordem solicitada pelo chamador | Atende às necessidades de amostragem ordenada, estratificada e particionamento do Marco M2, exigindo coluna de ID para rastreabilidade persistente sob permutação física. | y |
| Tratamento de campos da Onda 2 no `DatasetSchemaSpec` (`MULTI_TARGET_REGRESSION`, `target_transform_spec`) | Declarar os campos opcionais na assinatura de `DatasetSchemaSpec` para estabilidade do contrato, suportando `time_col` na validação estrutural de colunas disjuntas e rejeitando `MULTI_TARGET_REGRESSION`, `target_col` não-string e `target_transform_spec != None` com `ConfigurationError` explícito da Onda 1 | Respeita o recorte estratégico da Seção 6.1 de `ARQUITETURA_E_CONTRATOS.md` (Onda 1 vs. Onda 2) sem exigir quebra de assinatura futura na dataclass `DatasetSchemaSpec`. | y |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Especificação Imutável de Esquema, Papéis e Tipagem Semântica (`DatasetSchemaSpec`) ⭐ MVP

**User Story**: Como pesquisador configurando um experimento tabular, quero declarar explicitamente os papéis das variáveis (`target_col`, `task_type`, `group_col`, `observation_id_col`, `time_col`, `ignore_cols`) e opcionalmente seus tipos semânticos (`column_semantic_types`) em uma estrutura imutável `DatasetSchemaSpec`, para que o framework valide a disjunção entre papéis e impeça que variáveis de alvo, agrupamento ou identificadores vazem como atributos preditores.

**Why P1**: O esquema de papéis de colunas é o contrato de entrada obrigatório da Etapa 1 (`RF1.1`, `ARQUITETURA_E_CONTRATOS.md` Seção 3.1) e compõe o cálculo de `dataset_hash` (**ADR-007**).

**Acceptance Criteria**:

1. The system SHALL provide frozen, immutable data structures `DatasetSchemaSpec`, `ColumnDescriptor`, and `DatasetBundle`, as well as the canonical enumeration `ColumnSemanticType(StrEnum)` with members `"NUMERIC_CONTINUOUS"`, `"NUMERIC_DISCRETE"`, `"CATEGORICAL"`, `"BOOLEAN"`, `"TEMPORAL"`, and `"IDENTIFIER"`, in `experimental_ml.data`.
2. The system SHALL normalize all column names declared in `DatasetSchemaSpec` (`target_col`, `group_col`, `observation_id_col`, `time_col`, elements of `ignore_cols`, and keys of `column_semantic_types`) using Unicode NFC (`unicodedata.normalize("NFC", ...)`), convert `ignore_cols` into a deduplicated immutable `tuple[str, ...]` preserving declaration order, encapsulate `column_semantic_types` in a read-only mapping, and validate that `task_type` is a valid `TaskType` instance.
3. IF `target_col` (or any provided optional column name in `group_col`, `observation_id_col`, `time_col`, or `ignore_cols`) is empty, whitespace-only, or contains control/newline characters (`\n`, `\r`, `\t`, `\x00`), THEN `DatasetSchemaSpec` SHALL raise a `ConfigurationError`.
4. IF `task_type` is `TaskType.MULTI_TARGET_REGRESSION`, or if `target_col` is a non-string sequence of multiple targets, or if `target_transform_spec` is not `None`, THEN `DatasetSchemaSpec` SHALL raise a `ConfigurationError` indicating that Wave 2 features are not enabled in Wave 1 MVP.
5. IF any column name is assigned to more than one structural role among `target_col`, `group_col`, `observation_id_col`, `time_col`, and `ignore_cols` (e.g., `target_col == group_col` or `target_col in ignore_cols`), THEN `DatasetSchemaSpec` SHALL raise a `ConfigurationError`.
6. WHEN `config_hash(schema)` is invoked on `DatasetSchemaSpec`, THEN the system SHALL produce a deterministic 64-character hexadecimal SHA-256 digest invariant to Unicode NFD/NFC representation of column names and dictionary key insertion order.

**Independent Test**: Instanciar `DatasetSchemaSpec` com configurações válidas da Onda 1 (incluindo `column_semantic_types`), verificar congelamento (`FrozenInstanceError`), normalização NFC e `config_hash`, e comprovar que papéis sobrepostos, nomes vazios ou recursos da Onda 2 levantam `ConfigurationError`.

---

### P1: Ingestão Tabular com Isolamento Profundo de Memória e Propriedade Exclusiva dos Dados (`load_dataset` e `DatasetBundle`) ⭐ MVP

**User Story**: Como pesquisador, quero carregar bases de dados a partir de arquivos `.csv`/`.txt`/`.tsv` ou estruturas tabulares em memória com isolamento total de memória, para que o `DatasetBundle` assuma propriedade exclusiva dos dados e nenhuma mutação na estrutura original do chamador ou tentativas de alteração em referências retornadas afetem a integridade do bundle.

**Why P1**: Implementa `RF1.1`, `RF1.2` (dimensões, memória e hashing), `RF1.7` (imutabilidade rigorosa da base original) e `CA-E1-01`.

**Acceptance Criteria**:

1. WHEN `load_dataset(source, schema, *, delimiter=None, has_header=True, column_names=None, encoding="utf-8")` is called with a valid file path (`.csv`, `.txt`, `.tsv`) or in-memory tabular structure (`Mapping[str, Sequence]`, 2D `np.ndarray`, non-empty `Sequence[Mapping[str, Any]]`, or duck-typed `DataFrame` exposing `columns` and `__getitem__`), THEN the system SHALL return an immutable `DatasetBundle` with complete ownership of the data, without mutating the caller's input structure or file on disk.
2. The system SHALL create defensive memory copies of all ingested tabular columns such that mutating the caller's original in-memory dictionary, list, NumPy array, or DataFrame after `load_dataset` has executed has zero effect on `bundle.columns`.
3. The system SHALL store numeric and boolean tabular columns inside `DatasetBundle.columns` as read-only arrays backed by immutable `bytes` buffers, such that calling `arr.setflags(write=True)` on internal column arrays or on views exposed through `bundle.columns` raises a `ValueError` refusing writeable reactivation.
4. The system SHALL store object columns inside `DatasetBundle.columns` containing strictly immutable scalar values (`str`, `int`, `float`, `bool`, or `None`), with `flags.writeable == False`, raising `DataIntegrityError` if any column contains a mutable object such as a list, dict, set, or bytearray.
5. The system SHALL preserve original missing values (`np.nan` in `float64` numeric columns and `None` in object/string/boolean columns) without performing silent imputation, row deletion, or scaling.
6. The system SHALL record in `DatasetBundle` the exact structural metadata: `schema: DatasetSchemaSpec`, `n_rows: int`, `n_cols: int`, `column_names: tuple[str, ...]`, `feature_cols: tuple[str, ...]` (all columns in `column_names` ordered as in the source, excluding `{target_col, group_col, observation_id_col, time_col} ∪ set(ignore_cols)`), `descriptors: Mapping[str, ColumnDescriptor]`, `observation_ids: tuple[ObservationId, ...]`, `dataset_hash: str`, `raw_source_hash: str`, `schema_hash: str`, `memory_bytes: int`, and `source_path: str | None`.
7. WHEN `load_dataset` computes `DatasetBundle.dataset_hash`, THEN the system SHALL compute the canonical in-memory binary digest across normalized `bundle.columns`, `observation_ids`, and `schema` via `experimental_ml.core.dataset_hash(bundle.columns, schema)` such that identical tabular data loaded from a CSV file (regardless of line endings `\r\n` vs `\n`) or from an in-memory dictionary produces the exact same `dataset_hash`, where `1` (int64) and `1.0` (float64) are distinct non-equivalent types, column order and observation order are preserved as structural identity, and all missing representations evaluate to canonical null bytes.
8. WHEN `load_dataset` computes `DatasetBundle.raw_source_hash`, THEN the system SHALL compute the digest of the raw source input via `experimental_ml.core.dataset_hash(source, schema)`, matching the exact raw file bytes on disk when loaded from a path or the original in-memory structure when loaded from memory.

**Independent Test**: Carregar dados a partir de um array NumPy e um dict em memória; alterar a matriz original in-place (`orig[0, 0] = 9999`) e verificar que `bundle.columns` permanece intacto; tentar alterar `bundle.columns["col"][0] = 123` e verificar que levanta `ValueError` (read-only); tentar reativar escrita via `bundle.columns["col"].setflags(write=True)` e comprovar que levanta `ValueError`; tentar injetar `[1, [2, 3]]` e verificar que levanta `DataIntegrityError`; carregar o mesmo dataset via CSV com `\r\n` e via dicionário em memória e comprovar que `bundle.dataset_hash` é rigorosamente idêntico.

---

### P1: Parsing Estrito de Arquivos Tabulares e Detecção Segura de Delimitadores ⭐ MVP

**User Story**: Como pesquisador, quero que o carregamento de arquivos tabulares suporte delimitadores padronizados (vírgula, ponto-e-vírgula, tabulação, barra vertical e múltiplos espaços), respeite aspas RFC 4180 e falhe explicitamente com diagnósticos claros caso haja ambiguidade de delimitadores ou linhas com contagens distintas de colunas (*ragged rows*), para prevenir corrupção silenciosa de dados.

**Why P1**: Garante robustez científica e integridade física de arquivos legados de inventários e benchmarks (`RF1.1`, `RNF07`).

**Acceptance Criteria**:

1. The system SHALL support tabular text parsing with delimiters `","`, `";"`, `"\t"`, `"|"`, and arbitrary whitespace sequences `r"[ \t]+"` in `.txt` files, honoring double quotes (`"`) according to RFC 4180 such that delimiters and newline characters inside quoted fields are treated as literal field content and escaped quotes (`""`) evaluate to a single literal quote.
2. WHEN `delimiter=None` (automatic detection), THEN `load_dataset` SHALL inspect up to the first 100 non-empty lines using a strict sniffer across `,`, `;`, `\t`, `|`, and whitespace sequences, verifying that exactly one candidate delimiter produces a constant column count $M \ge 2$ across all sampled lines.
3. IF `delimiter=None` and multiple candidate delimiters produce conflicting valid column counts across the sample, or if no candidate delimiter produces a strictly uniform column count $M \ge 2$ across all sampled lines, THEN `load_dataset` SHALL raise a `DataIntegrityError` stating that delimiter detection was ambiguous or failed, prompting the user to declare `delimiter` explicitly.
4. WHEN an explicit `delimiter` is provided by the caller, THEN `load_dataset` SHALL disable automatic detection and parse all rows strictly using the specified delimiter.
5. IF any non-empty row in a tabular file has a different number of columns than the header or the first row (ragged rows), THEN `load_dataset` SHALL raise a `DataIntegrityError` detailing the 1-based line number, expected column count, and actual column count, without silently dropping rows or padding columns with nulls.
6. IF a file on disk has zero bytes, contains only whitespace/blank lines, or contains only a header line with zero data rows ($N = 0$), THEN `load_dataset` SHALL raise a `DataIntegrityError`.
7. WHEN `has_header=False` is specified, THEN `load_dataset` SHALL assign `column_names` if provided, or generate canonical positional names `("col_0", "col_1", ..., f"col_{M-1}")` if `column_names=None`; IF `column_names` has length different from the number of columns $M$, THEN `load_dataset` SHALL raise a `DataIntegrityError`.
8. IF a header line contains empty column names after trimming or duplicate column names after Unicode NFC normalization, THEN `load_dataset` SHALL raise a `DataIntegrityError`.

**Independent Test**: Testar arquivos válidos com vírgula, ponto-e-vírgula, tabulação e múltiplos espaços; testar campos contendo vírgulas entre aspas (`"Silva, João"`); testar arquivo com linha contendo coluna a mais ou a menos (verificando `DataIntegrityError` com linha indicada); testar arquivo com delimitador ambíguo (vírgulas e pontos-e-vírgulas equilibrados) sem `delimiter` explícito (verificando `DataIntegrityError`), e testar resolução ao fornecer `delimiter=";"`.

---

### P1: Tipagem Semântica vs. Representação Física em `ColumnDescriptor` ⭐ MVP

**User Story**: Como pesquisador, quero que o descritor de cada coluna registre separadamente sua representação física em memória e seu significado semântico no experimento, permitindo declaração manual no esquema ou inferência padrão neutra e documentada, para que variáveis discretas, identificadores e contínuas não sejam confundidas.

**Why P1**: Implementa `RF1.3` (tipagem semântica) e prepara a base para o diagnóstico estatístico do Marco M2 sem inferir indevidamente intenções de domínio.

**Acceptance Criteria**:

1. The system SHALL populate `ColumnDescriptor` for each column in `DatasetBundle.descriptors` with fields `name: str`, `index: int`, `role: str` (`"target"`, `"group"`, `"observation_id"`, `"time"`, `"ignored"`, or `"feature"`), `physical_type: str` (`"float64"`, `"int64"`, `"bool"`, or `"object"`), `semantic_type: ColumnSemanticType`, `is_semantic_declared: bool`, `n_missing: int`, and `memory_bytes: int`.
2. WHEN `schema.column_semantic_types` explicitly defines the semantic type for a column, THEN `ColumnDescriptor.semantic_type` SHALL equal that declared type and `ColumnDescriptor.is_semantic_declared` SHALL be `True`.
3. WHEN `schema.column_semantic_types` does not specify a column's semantic type, THEN `ColumnDescriptor.semantic_type` SHALL be assigned according to neutral structural defaults: `IDENTIFIER` for `observation_id_col`; `TEMPORAL` for `time_col`; `CATEGORICAL` for `group_col`; `NUMERIC_CONTINUOUS` (if float) or `NUMERIC_DISCRETE` (if int) for `target_col` under `REGRESSION`; `CATEGORICAL` (or `BOOLEAN` if bool) for `target_col` under classification; and for feature columns: `BOOLEAN` for boolean dtypes, `NUMERIC_CONTINUOUS` for `float64`, `NUMERIC_DISCRETE` for `int64`, and `CATEGORICAL` for `object`/strings, setting `ColumnDescriptor.is_semantic_declared` to `False`.
4. IF a column declared in `schema.column_semantic_types` does not exist in the dataset, THEN `validate_dataset_schema` and `load_dataset` SHALL raise a `DataIntegrityError`.

**Independent Test**: Carregar dataset com coluna de números inteiros (`int64` físico) declarada como `CATEGORICAL` em `schema.column_semantic_types`, comprovando que `physical_type == "int64"`, `semantic_type == ColumnSemanticType.CATEGORICAL` e `is_semantic_declared == True`; carregar sem declaração e comprovar a inferência neutra padrão como `NUMERIC_DISCRETE` e `is_semantic_declared == False`.

---

### P1: Geração Posicional e Validação Estrita de `ObservationId` (`validate_dataset_schema`) ⭐ MVP

**User Story**: Como pesquisador, quero que o carregamento garanta $N$ identificadores de observação únicos e não-nulos (gerando `obs_000000` sequencialmente para rastrear posições na carga, com ciência expressa de que a reordenação prévia altera a associação, ou validando a coluna de ID intrínseca da fonte), para assegurar rastreabilidade matemática de cada linha nos planos de partição subsequentes.

**Why P1**: Cumpre diretamente o critério obrigatório `CA-E1-01` e garante a integridade de proveniência por observação no `DatasetBundle`.

**Acceptance Criteria**:

1. WHEN `schema.observation_id_col` is `None`, THEN `load_dataset` SHALL deterministically generate $N$ unique `ObservationId` instances formatted as `ObservationId(f"obs_{i:06d}")` for $i \in \{0, \dots, N-1\}$ matching the physical row sequence of the input, documenting that these identifiers represent load positions rather than persistent entity identities.
2. WHEN `schema.observation_id_col` is specified, THEN `load_dataset` SHALL extract that column's values, normalize them to Unicode NFC, validate that no value is null (`None`, `NaN`, empty string, or whitespace-only), convert each value to an `ObservationId`, and verify that all $N$ identifiers are strictly unique (`len(set(observation_ids)) == N`).
3. IF `schema.observation_id_col` contains any missing/null value, invalid identifier characters, or duplicate values across rows, THEN `load_dataset` (and `validate_dataset_schema`) SHALL raise a `DataIntegrityError` detailing the 1-based row index and duplicate value.
4. IF any column declared in `DatasetSchemaSpec` (`target_col`, `group_col`, `observation_id_col`, `time_col`, or elements of `ignore_cols`) does not exist in the dataset's `column_names`, THEN `validate_dataset_schema` and `load_dataset` SHALL raise a `DataIntegrityError` listing the missing column(s).
5. IF the dataset has zero rows ($N = 0$), zero columns ($M = 0$), duplicate column names after NFC normalization, inconsistent column lengths, or zero remaining candidate predictor columns (`len(feature_cols) == 0`), THEN `load_dataset` and `validate_dataset_schema` SHALL raise a `DataIntegrityError`.

**Independent Test**: Testar dataset sem coluna de ID (verificando geração de `obs_000000` a `obs_000009` em ordem determinística); testar com coluna de ID válida (verificando preservação de IDs originais); testar com coluna de ID contendo duplicata ou valor nulo (verificando `DataIntegrityError` com linha indicada); testar dataset onde todas as colunas não-alvo estão em `ignore_cols` (`len(feature_cols) == 0`) levantando `DataIntegrityError`.

---

### P2: Utilitários Funcionais Somente-Leitura e Recorte Ordenado por `ObservationId`

**User Story**: Como desenvolvedor dos módulos `data` (M2), `features` (M3) e `validation` (M2), quero funções puras de consulta sobre `DatasetBundle` (extração de array de coluna ou recorte ordenado de linhas por sequência de `ObservationId`) que retornem cópias ou visões somente-leitura preservando estritamente a ordem solicitada pelo chamador com recalculo de hash, para manipular dados tabulares sem quebrar a imutabilidade do `DatasetBundle`.

**Why P2**: Facilita a integração limpa com `profile_dataset`, `sanitize_dataset` e `build_partition_plan` no Marco M2 mantendo a programação funcional (**ADR-008**).

**Acceptance Criteria**:

1. WHEN `get_column_array(bundle, col_name, *, copy=False)` is called for an existing column, THEN the system SHALL return a 1D `np.ndarray` with `flags.writeable == False` when `copy=False` (raising `ValueError` upon `setflags(write=True)` on buffer-backed arrays) or a writeable independent copy when `copy=True`; IF `col_name` does not exist in `bundle.column_names`, THEN the system SHALL raise a `DataIntegrityError`.
2. WHEN `slice_bundle_by_observation_ids(bundle, observation_ids)` is called with a non-empty sequence of valid `ObservationId`s present in `bundle.observation_ids`, THEN the system SHALL return a new immutable `DatasetBundle` containing the requested observations strictly ordered according to the caller's requested `observation_ids` sequence, with updated `n_rows`, `descriptors`, and recalculated in-memory `dataset_hash`, while leaving the original `bundle` completely unchanged.
3. IF `slice_bundle_by_observation_ids` receives an empty sequence, duplicate `ObservationId`s, or any `ObservationId` not present in `bundle.observation_ids`, THEN the system SHALL raise a `DataIntegrityError`.

**Independent Test**: Extrair colunas via `get_column_array` com `copy=False` e `copy=True`; fatiar um subconjunto na ordem invertida dos IDs via `slice_bundle_by_observation_ids` comprovando que o novo bundle reflete a ordem solicitada pelo chamador e recalcula `dataset_hash`; comprovar que IDs duplicados, inexistentes ou sequência vazia levantam `DataIntegrityError`.

---

## Edge Cases

- IF a `.csv`, `.txt`, or `.tsv` file path passed to `load_dataset` does not exist or points to a directory, THEN the system SHALL raise `FileNotFoundError`.
- IF a text file cannot be decoded with the specified `encoding` (default `utf-8`), THEN `load_dataset` SHALL raise a `DataIntegrityError` stating the decoding failure.
- IF numeric columns in text files contain standard missing tokens (`""`, `"NA"`, `"NaN"`, `"null"`, `"None"`, `"nan"`) alongside numeric values, THEN `load_dataset` SHALL parse the numeric values as `float64` and represent the missing entries as `np.nan` without raising a parsing error or dropping the row.
- IF a caller passes a 2D `np.ndarray` without `column_names` and `has_header=True`, THEN `load_dataset` SHALL generate canonical column names `("col_0", ..., f"col_{M-1}")` so in-memory arrays can be ingested seamlessly when `schema` references those canonical names.
- IF a dataset contains columns with trailing or leading whitespace in column names, THEN `load_dataset` SHALL strip and normalize column names to Unicode NFC, raising `DataIntegrityError` if stripping reveals duplicate names.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| DATA-01 | P1: Especificação Imutável de Esquema (`DatasetSchemaSpec`) | Specify | pending |
| DATA-02 | P1: Especificação Imutável de Esquema (`DatasetSchemaSpec`) | Specify | pending |
| DATA-03 | P1: Especificação Imutável de Esquema (`DatasetSchemaSpec`) | Specify | pending |
| DATA-04 | P1: Especificação Imutável de Esquema (`DatasetSchemaSpec`) | Specify | pending |
| DATA-05 | P1: Especificação Imutável de Esquema (`DatasetSchemaSpec`) | Specify | pending |
| DATA-06 | P1: Especificação Imutável de Esquema (`DatasetSchemaSpec`) | Specify | pending |
| DATA-07 | P1: Ingestão Tabular com Isolamento Profundo de Memória | Specify | pending |
| DATA-08 | P1: Ingestão Tabular com Isolamento Profundo de Memória | Specify | pending |
| DATA-09 | P1: Ingestão Tabular com Isolamento Profundo de Memória | Specify | pending |
| DATA-10 | P1: Ingestão Tabular com Isolamento Profundo de Memória | Specify | pending |
| DATA-11 | P1: Ingestão Tabular com Isolamento Profundo de Memória | Specify | pending |
| DATA-12 | P1: Ingestão Tabular com Isolamento Profundo de Memória | Specify | pending |
| DATA-13 | P1: Ingestão Tabular com Isolamento Profundo de Memória | Specify | pending |
| DATA-14 | P1: Ingestão Tabular com Isolamento Profundo de Memória | Specify | pending |
| DATA-15 | P1: Parsing Estrito de Arquivos Tabulares e Delimitadores | Specify | pending |
| DATA-16 | P1: Parsing Estrito de Arquivos Tabulares e Delimitadores | Specify | pending |
| DATA-17 | P1: Parsing Estrito de Arquivos Tabulares e Delimitadores | Specify | pending |
| DATA-18 | P1: Parsing Estrito de Arquivos Tabulares e Delimitadores | Specify | pending |
| DATA-19 | P1: Parsing Estrito de Arquivos Tabulares e Delimitadores | Specify | pending |
| DATA-20 | P1: Parsing Estrito de Arquivos Tabulares e Delimitadores | Specify | pending |
| DATA-21 | P1: Parsing Estrito de Arquivos Tabulares e Delimitadores | Specify | pending |
| DATA-22 | P1: Parsing Estrito de Arquivos Tabulares e Delimitadores | Specify | pending |
| DATA-23 | P1: Tipagem Semântica vs. Representação Física | Specify | pending |
| DATA-24 | P1: Tipagem Semântica vs. Representação Física | Specify | pending |
| DATA-25 | P1: Identificação (`ObservationId`) e Consistência Esquema-Dados | Specify | pending |
| DATA-26 | P1: Identificação (`ObservationId`) e Consistência Esquema-Dados | Specify | pending |
| DATA-27 | P1: Identificação (`ObservationId`) e Consistência Esquema-Dados | Specify | pending |
| DATA-28 | P2: Utilitários Funcionais Somente-Leitura | Specify | pending |
| DATA-29 | P2: Utilitários Funcionais Somente-Leitura | Specify | pending |

---

## Sources

- `engenharia_software/ARQUITETURA_E_CONTRATOS.md` Seção 1 (Princípio 2 — Imutabilidade dos Dados de Origem e Zero Transformação Silenciosa), Seção 2.3 (Nível 1 — `experimental_ml.data`), Seção 3.1 (Etapa 1: `DatasetSchemaSpec`, `DatasetBundle`, `load_dataset`), Seção 6.1 (Recorte Estratégico Onda 1 vs. Onda 2) e Seção 7 (`TA-M2.1` / `CA-E1-01`).
- `engenharia_software/ARQUITETURA_E_CONTRATOS.md` ADR-002 (Separação entre Saneamento Estrutural Pré-Partição e Transformação Parametrizada Intra-Fold), ADR-007 (Contrato Formal de Serialização Canônica e Distinção entre `config_hash` e `dataset_hash`) e ADR-008 (Paradigma Modular Baseado em Funções e Estruturas Imutáveis Sem OOP).
- `engenharia_software/ESPECIFICACAO_REQUISITOS.md` `RF1.1` (Ingestão, Cabeçalhos e Papéis das Variáveis), `RF1.2` (Diagnóstico Estrutural, Memória e `dataset_hash`), `RF1.3` (Tipagem Semântica por Coluna), `RF1.7` (Imutabilidade na Etapa 1), `CA-GER-02`, `CA-E1-01`, `RNF01`–`RNF07`.
- `REFERENCIAS_E_FUNDAMENTACAO.md` Seção 3.1 (Parnas, 1972 — Ocultamento de Informação e Transparência Referencial), Seção 4.1 (Kapoor & Narayanan, 2023; Heil et al., 2021 — Prevenção de Data Leakage e Imutabilidade Bruta), Seção 7.1 (Freire et al., 2008; REFORMS, 2024 — Proveniência Prospectiva e Retrospectiva) e Seção 8.1 (NIST FIPS 180-4; Unicode UAX #15; RFC 4180 — Canonicalização, Delimitação e Hashing Estrutural).

---

## Success Criteria

- [ ] Enumeração `ColumnSemanticType` e estruturas imutáveis `DatasetSchemaSpec`, `ColumnDescriptor` e `DatasetBundle` definidas e exportadas em `experimental_ml.data`.
- [ ] Validação estrita de papéis disjuntos, nomes de colunas em Unicode NFC, especificação manual de tipos semânticos (`column_semantic_types`) e fronteira Onda 1 vs. Onda 2 em `DatasetSchemaSpec`.
- [ ] Função pura `load_dataset` implementando isolamento profundo de memória: propriedade exclusiva dos dados, colunas numéricas/booleanas derivadas de buffers `bytes` imutáveis que impedem reativação de escrita (`ValueError` em `setflags(write=True)`), proibição de objetos mutáveis em colunas `object` e `MappingProxyType`.
- [ ] Parsing tabular robusto em conformidade com RFC 4180 para campos entre aspas, delimitadores `,`, `;`, `\t`, `|` e múltiplos espaços, detecção automática com fallback e falha estrita sob ambiguidade ou linhas com contagens distintas de colunas (*ragged rows*).
- [ ] Semântica de hashing tripartite formalizada e verificada: `dataset_hash` (conteúdo canônico em memória sensível a ordem de linhas/colunas, tipos e valores), `raw_source_hash` (integridade da fonte original) e `schema_hash` (`config_hash(schema)`).
- [ ] `ColumnDescriptor` registrando separadamente representação física (`physical_type`), significado semântico (`semantic_type`) e indicador de declaração explícita (`is_semantic_declared`).
- [ ] Atribuição posicional de `ObservationId` (`obs_000000` sequencial com limites documentados de permutação e validação estrita de não-nulidade e unicidade quando informada na fonte), além de utilitários funcionais `get_column_array` e `slice_bundle_by_observation_ids` preservando a ordem solicitada pelo chamador.
- [ ] Suíte de testes unitários `tests/unit/test_data_schemas.py` planejada com cobertura 1:1 para os 29 requisitos `DATA-01` a `DATA-29`.
