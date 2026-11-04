# m1-4-datasets-schemas Specification

## Problem Statement

O `experimental-ml-framework` necessita de uma camada fundacional de ingestão tabular imutável e validação estrutural de esquemas (`experimental_ml.data`, Nível 1 da arquitetura) que carregue dados a partir de arquivos em disco (`.csv`, `.txt`) ou estruturas em memória (`dict`, `ndarray` 2D, `DataFrame` duck-typed), valide a consistência entre os dados e os papéis declarados no `DatasetSchemaSpec` (`target_col`, `task_type`, `group_col`, `observation_id_col`, `time_col`, `ignore_cols`), atribua ou valide identificadores únicos de observação (`ObservationId`) e produza um `DatasetBundle` estritamente somente-leitura vinculado ao `dataset_hash` canônico (**ADR-007**). Sem esse contrato estrutural, as etapas subsequentes de perfilamento diagnóstico (`profile_dataset`), saneamento (`sanitize_dataset`) e particionamento (`build_partition_plan`) no Marco M2 ficariam expostas a mutações silenciosas em memória, colisões de papéis de colunas, identificadores de observação duplicados ou perda de rastreabilidade criptográfica da base original (`RF1.1`, `RF1.7`, `CA-E1-01`).

## Goals

- [ ] Definir a enumeração `ColumnSemanticType(StrEnum)` e as estruturas de dados imutáveis (`@dataclass(frozen=True, slots=True)`) de esquema e representação tabular: `DatasetSchemaSpec`, `ColumnDescriptor` e `DatasetBundle`.
- [ ] Validar estritamente o esquema declarativo (`DatasetSchemaSpec`), assegurando disjunção entre papéis de colunas (`target_col`, `group_col`, `observation_id_col`, `time_col`, `ignore_cols`), normalização Unicode NFC de nomes de colunas e conformidade com o recorte da Onda 1 do MVP (`REGRESSION`, `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION` com `target_col: str`).
- [ ] Implementar a ingestão tabular determinística (`load_dataset`) para arquivos `.csv`/`.txt` (com delimitadores configuráveis, detecção automática ou múltiplos espaços em branco, e `has_header=True|False`) e estruturas em memória (`Mapping`, `ndarray` 2D, sequência de registros ou `DataFrame` via duck-typing), sem adicionar `pandas` como dependência obrigatória e sem executar imputação, remoção de linhas ou coerção destrutiva silenciosa.
- [ ] Garantir a imutabilidade física e lógica do `DatasetBundle` em memória (arrays colunares `numpy.ndarray` 1D com `flags.writeable = False` e mapeamentos somente-leitura `MappingProxyType`), preservando valores ausentes originais (`NaN` / `None`).
- [ ] Validar a consistência entre esquema e dados (`validate_dataset_schema`), garantindo existência de todas as colunas declaradas, presença de ao menos uma coluna preditora candidata (`feature_cols`), geração determinística ou validação de unicidade estrita de $N$ `ObservationId` (`CA-E1-01`) e cálculo reprodutível do `dataset_hash` via `experimental_ml.core.dataset_hash` (**ADR-007**).

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
| Dependências externas e representação em memória | Utilizar exclusivamente a biblioteca padrão do Python (`csv`, `io`, `types`, `pathlib`) e `numpy>=1.24.0`, armazenando colunas como `np.ndarray` 1D com `writeable=False` dentro de `MappingProxyType` | Mantém o projeto leve e autônomo conforme `pyproject.toml`, garante imutabilidade real em nível de buffer de memória e suporta `pandas.DataFrame` externo por *duck-typing* (`columns`, `__getitem__`, `to_numpy`) de forma idêntica ao `dataset_hash` do M1.2. | y |
| Tratamento de campos da Onda 2 no `DatasetSchemaSpec` (`MULTI_TARGET_REGRESSION`, `time_col`, `target_transform_spec`) | Declarar os campos opcionais na assinatura de `DatasetSchemaSpec` para estabilidade do contrato, suportando `time_col` na validação estrutural de colunas disjuntas e rejeitando `MULTI_TARGET_REGRESSION`, `target_col` não-string (sequência de múltiplos alvos) e `target_transform_spec != None` com `ConfigurationError` explícito da Onda 1 | Respeita o recorte estratégico da Seção 6.1 de `ARQUITETURA_E_CONTRATOS.md` (Onda 1 vs. Onda 2) sem exigir quebra de assinatura futura na dataclass `DatasetSchemaSpec`. | y |
| Geração determinística de `observation_ids` quando `observation_id_col=None` | Gerar tupla de `ObservationId` canônicos baseados no índice posicional de leitura (`ObservationId("obs_0")`, ..., `ObservationId(f"obs_{n-1}")`) | Cumpre `ARQUITETURA_E_CONTRATOS.md` Seção 3.1 e `CA-E1-01` ($N$ identificadores únicos, estáveis e não-nulos por observação). | y |
| Cálculo de `dataset_hash` em `load_dataset` | Delegar integralmente a `experimental_ml.core.dataset_hash(source, schema)` sem reimplementar lógica de hashing | Evita duplicação de responsabilidades com o `core` (M1.2) e garante conformidade estrita com o **ADR-007** tanto para arquivos em disco quanto para dados em memória. | y |
| Inferência de `ColumnSemanticType` na ingestão | Classificar descritivamente cada coluna em `NUMERIC_CONTINUOUS`, `NUMERIC_DISCRETE`, `CATEGORICAL`, `BOOLEAN`, `TEMPORAL` ou `IDENTIFIER` com base no `dtype`/valores e no papel declarado no esquema, sem alterar os valores brutos | Fornece os metadados estruturais de coluna (`ColumnDescriptor`) requeridos pelo `DatasetBundle` e prepara a base para o `profile_dataset` no Marco M2 sem realizar transformações de pré-processamento. | y |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Especificação Imutável de Esquema e Papéis de Colunas (`DatasetSchemaSpec`) ⭐ MVP

**User Story**: Como pesquisador configurando um experimento tabular, quero declarar explicitamente os papéis das variáveis (`target_col`, `task_type`, `group_col`, `observation_id_col`, `time_col`, `ignore_cols`) em uma estrutura imutável `DatasetSchemaSpec`, para que o framework valide a disjunção entre papéis e impeça que colunas de alvo, agrupamento, tempo ou identificadores vazem como atributos preditores.

**Why P1**: O esquema de papéis de colunas é o contrato de entrada obrigatório da Etapa 1 (`RF1.1`, `ARQUITETURA_E_CONTRATOS.md` Seção 3.1) e compõe o cálculo de `dataset_hash` (**ADR-007**).

**Acceptance Criteria**:

1. The system SHALL provide frozen, immutable data structures `DatasetSchemaSpec`, `ColumnDescriptor`, and `DatasetBundle`, as well as the canonical enumeration `ColumnSemanticType(StrEnum)` with members `"NUMERIC_CONTINUOUS"`, `"NUMERIC_DISCRETE"`, `"CATEGORICAL"`, `"BOOLEAN"`, `"TEMPORAL"`, and `"IDENTIFIER"`, in `experimental_ml.data`.
2. The system SHALL normalize all column names declared in `DatasetSchemaSpec` (`target_col`, `group_col`, `observation_id_col`, `time_col`, and elements of `ignore_cols`) using Unicode NFC (`unicodedata.normalize("NFC", ...)`), convert `ignore_cols` into a deduplicated immutable `tuple[str, ...]` preserving declaration order, and validate that `task_type` is a valid `TaskType` instance.
3. IF `target_col` (or any provided optional column name in `group_col`, `observation_id_col`, `time_col`, or `ignore_cols`) is empty, whitespace-only, or contains control/newline characters, THEN `DatasetSchemaSpec` SHALL raise a `ConfigurationError`.
4. IF `task_type` is `TaskType.MULTI_TARGET_REGRESSION`, or if `target_col` is a non-string sequence of multiple targets, or if `target_transform_spec` is not `None`, THEN `DatasetSchemaSpec` SHALL raise a `ConfigurationError` indicating that Wave 2 features are not enabled in Wave 1 MVP.
5. IF any column name is assigned to more than one structural role among `target_col`, `group_col`, `observation_id_col`, `time_col`, and `ignore_cols` (e.g., `target_col == group_col` or `target_col in ignore_cols`), THEN `DatasetSchemaSpec` SHALL raise a `ConfigurationError`.
6. WHEN `config_hash(schema)` is invoked on `DatasetSchemaSpec`, THEN the system SHALL produce a deterministic 64-character hexadecimal SHA-256 digest invariant to Unicode NFD/NFC representation of column names.

**Independent Test**: Instanciar `DatasetSchemaSpec` com configurações válidas da Onda 1, verificar congelamento (`FrozenInstanceError`), normalização NFC e `config_hash`, e comprovar que papéis sobrepostos, nomes vazios ou recursos da Onda 2 levantam `ConfigurationError`.

---

### P1: Ingestão Tabular Imutável em Memória e via Arquivos (`load_dataset` e `DatasetBundle`) ⭐ MVP

**User Story**: Como pesquisador, quero carregar bases de dados a partir de arquivos `.csv`/`.txt` (com ou sem cabeçalho e com delimitadores configuráveis ou espaços em branco) ou estruturas tabulares em memória sem que nenhuma linha, coluna ou valor ausente seja alterado silenciosamente, obtendo um `DatasetBundle` somente-leitura.

**Why P1**: Implementa `RF1.1`, `RF1.2` (parcial: dimensões, memória e `dataset_hash`), `RF1.7` (imutabilidade da base original) e `CA-E1-01`.

**Acceptance Criteria**:

1. WHEN `load_dataset(source, schema, *, delimiter=None, has_header=True, column_names=None, encoding="utf-8")` is called with a valid file path (`.csv`, `.txt`, `.tsv`) or in-memory tabular structure (`Mapping[str, Sequence]`, 2D `np.ndarray`, non-empty `Sequence[Mapping[str, Any]]`, or duck-typed `DataFrame` exposing `columns` and `__getitem__`), THEN the system SHALL return an immutable `DatasetBundle` without mutating the caller's input structure or file on disk.
2. WHEN loading a text file where `delimiter` is explicitly provided (e.g., `","`, `";"`, `"\t"`, `"|"`) or `delimiter=None` (auto-detecting comma/semicolon/tab/pipe or arbitrary whitespace sequences `r"\s+"` in `.txt` files), THEN `load_dataset` SHALL parse all rows deterministically and verify that every row has the exact same number of columns.
3. WHEN `has_header=False` is specified, THEN `load_dataset` SHALL assign `column_names` if provided, or generate canonical positional names `("col_0", "col_1", ..., f"col_{M-1}")` if `column_names=None`; IF `column_names` has length different from the number of columns $M$, THEN `load_dataset` SHALL raise a `DataIntegrityError`.
4. The system SHALL store tabular columns inside `DatasetBundle.columns` as a read-only `MappingProxyType[str, np.ndarray]` where every column array is 1D of length $N$ with `flags.writeable == False`, preserving missing values (`np.nan` in `float64` numeric columns and `None` in object/categorical/string columns) without performing silent imputation, row deletion, or scaling.
5. The system SHALL record in `DatasetBundle` the exact structural metadata: `schema: DatasetSchemaSpec`, `n_rows: int`, `n_cols: int`, `column_names: tuple[str, ...]`, `feature_cols: tuple[str, ...]` (all columns in `column_names` ordered as in the source, excluding `{target_col, group_col, observation_id_col, time_col} ∪ set(ignore_cols)`), `descriptors: Mapping[str, ColumnDescriptor]`, `observation_ids: tuple[ObservationId, ...]`, `dataset_hash: str`, `memory_bytes: int`, and `source_path: str | None`.
6. WHEN `load_dataset` computes `DatasetBundle.dataset_hash`, THEN the system SHALL delegate to `experimental_ml.core.dataset_hash(source, schema)` so that the hash before and after ingestion is identical (`CA-E1-01`, **ADR-007**).

**Independent Test**: Carregar arquivos `.csv` (vírgula e ponto-e-vírgula), `.txt` (delimitado por múltiplos espaços e com `has_header=False`), dicionários em memória, `ndarray` 2D e objeto `DataFrame` duck-typed; verificar que tentativas de mutação (`bundle.columns["x"][0] = 999` ou `bundle.columns["nova"] = ...`) levantam `ValueError`/`TypeError`, que valores ausentes permanecem intactos e que `bundle.dataset_hash == dataset_hash(source, schema)`.

---

### P1: Identificação de Observações (`ObservationId`) e Consistência Esquema-Dados (`validate_dataset_schema`) ⭐ MVP

**User Story**: Como pesquisador, quero que o carregamento valide rigorosamente a existência das colunas do esquema nos dados, a presença de preditores candidatos e a unicidade e completude de `observation_ids`, para impedir falhas silenciosas ou perda de rastreabilidade por observação nas etapas seguintes.

**Why P1**: Cumpre diretamente o critério obrigatório `CA-E1-01` (unicidade e não-nulidade dos $N$ `observation_id`) e previne bases degeneradas antes do diagnóstico e particionamento.

**Acceptance Criteria**:

1. WHEN `schema.observation_id_col` is `None`, THEN `load_dataset` SHALL deterministically generate $N$ unique `ObservationId` instances `("obs_0", "obs_1", ..., f"obs_{N-1}")` corresponding to the 0-based row positions.
2. WHEN `schema.observation_id_col` is specified, THEN `load_dataset` SHALL extract the values of that column, validate that no value is missing (`None`, `NaN`, or empty/whitespace string), convert each value into a valid `ObservationId`, and verify that all $N$ values are strictly unique (`len(set(observation_ids)) == N`).
3. IF `schema.observation_id_col` contains any missing/null value, invalid identifier characters, or duplicate values across rows, THEN `load_dataset` (and `validate_dataset_schema`) SHALL raise a `DataIntegrityError` detailing the offending index or duplicate identifier.
4. IF any column name declared in `DatasetSchemaSpec` (`target_col`, `group_col`, `observation_id_col`, `time_col`, or any element of `ignore_cols`) does not exist in the dataset's `column_names`, THEN `validate_dataset_schema` and `load_dataset` SHALL raise a `DataIntegrityError` listing the missing column(s).
5. IF the dataset has zero rows ($N = 0$), zero columns ($M = 0$), duplicate column names after NFC normalization, inconsistent column lengths, or zero remaining candidate predictor columns (`len(feature_cols) == 0`), THEN `load_dataset` and `validate_dataset_schema` SHALL raise a `DataIntegrityError`.
6. WHEN `DatasetBundle` is constructed, THEN the system SHALL populate `ColumnDescriptor` for each column with `name: str`, `index: int`, `role: str` (`"target"`, `"group"`, `"observation_id"`, `"time"`, `"ignored"`, or `"feature"`), `semantic_type: ColumnSemanticType`, `dtype_str: str`, `n_missing: int`, and `memory_bytes: int`.

**Independent Test**: Testar `load_dataset` com `observation_id_col=None` (verificando geração de `"obs_0"..f"obs_{N-1}"`) e com `observation_id_col` explícito (válido, com duplicatas e com nulos), testar colunas ausentes do esquema, colunas duplicadas no cabeçalho, dataset vazio ($N=0$) e dataset onde todas as colunas não-alvo estão em `ignore_cols` (`len(feature_cols) == 0`), comprovando o lançamento de `DataIntegrityError`.

---

### P2: Utilitários de Consulta Somente-Leitura e Extração de Subconjuntos por `ObservationId`

**User Story**: Como desenvolvedor dos módulos `data` (M2), `features` (M3) e `validation` (M2), quero funções puras de consulta sobre `DatasetBundle` (como seleção de matriz de atributos candidatos ou recorte de linhas por sequência de `ObservationId`) que retornem cópias ou visões somente-leitura, para manipular dados tabulares sem quebrar a imutabilidade do `DatasetBundle`.

**Why P2**: Facilita a integração limpa com `profile_dataset`, `sanitize_dataset` e `build_partition_plan` no Marco M2 mantendo a programação funcional (**ADR-008**).

**Acceptance Criteria**:

1. WHEN `get_column_array(bundle, col_name)` is called for an existing column, THEN the system SHALL return a read-only 1D `np.ndarray` (`flags.writeable == False`); IF `col_name` does not exist in `bundle.column_names`, THEN the system SHALL raise a `DataIntegrityError`.
2. WHEN `select_Rows_by_observation_ids` / `slice_bundle_by_observation_ids(bundle, observation_ids)` is called with a non-empty sequence of valid `ObservationId`s present in `bundle.observation_ids`, THEN the system SHALL return a new immutable `DatasetBundle` containing only the requested observations in the exact requested order, with recalculated `n_rows`, `descriptors`, and in-memory `dataset_hash`, while leaving the original `bundle` completely unchanged.
3. IF `slice_bundle_by_observation_ids` receives an empty sequence, duplicate `ObservationId`s, or an `ObservationId` not present in `bundle.observation_ids`, THEN the system SHALL raise a `DataIntegrityError`.

**Independent Test**: Extrair colunas via `get_column_array` e recortar um subconjunto de observações via `slice_bundle_by_observation_ids`, verificando que o novo `DatasetBundle` é imutável, preserva a ordem solicitada de `observation_ids`, recalcula `dataset_hash` e rejeita IDs inexistentes ou duplicados com `DataIntegrityError`.

---

## Edge Cases

- IF a `.csv` or `.txt` file path passed to `load_dataset` does not exist or is a directory, THEN the system SHALL raise `FileNotFoundError`.
- IF a text file has ragged rows (rows with different numbers of fields than the header or first row) or cannot be decoded with the specified `encoding`, THEN `load_dataset` SHALL raise a `DataIntegrityError`.
- IF numeric columns in text files contain standard missing tokens (`""`, `"NA"`, `"NaN"`, `"null"`, `"None"`, `"nan"`) alongside numeric values, THEN `load_dataset` SHALL parse the numeric values as `float64` and represent the missing entries as `np.nan` without raising a parsing error or dropping the row.
- IF a column contains mixed non-missing tokens that cannot be parsed as numbers or booleans, THEN `load_dataset` SHALL preserve the raw string tokens (normalized to Unicode NFC, with missing tokens mapped to `None`) in an immutable `object` dtype array and classify the column as `ColumnSemanticType.CATEGORICAL` (or `IDENTIFIER` / `TEMPORAL` according to its role).
- IF a caller passes a 2D `np.ndarray` without `column_names` and `has_header=True`, THEN `load_dataset` SHALL generate canonical column names `("col_0", ..., f"col_{M-1}")` so in-memory arrays can be ingested seamlessly when `schema` references those canonical names.

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
| DATA-07 | P1: Ingestão Tabular Imutável (`load_dataset` e `DatasetBundle`) | Specify | pending |
| DATA-08 | P1: Ingestão Tabular Imutável (`load_dataset` e `DatasetBundle`) | Specify | pending |
| DATA-09 | P1: Ingestão Tabular Imutável (`load_dataset` e `DatasetBundle`) | Specify | pending |
| DATA-10 | P1: Ingestão Tabular Imutável (`load_dataset` e `DatasetBundle`) | Specify | pending |
| DATA-11 | P1: Ingestão Tabular Imutável (`load_dataset` e `DatasetBundle`) | Specify | pending |
| DATA-12 | P1: Ingestão Tabular Imutável (`load_dataset` e `DatasetBundle`) | Specify | pending |
| DATA-13 | P1: Identificação (`ObservationId`) e Consistência Esquema-Dados | Specify | pending |
| DATA-14 | P1: Identificação (`ObservationId`) e Consistência Esquema-Dados | Specify | pending |
| DATA-15 | P1: Identificação (`ObservationId`) e Consistência Esquema-Dados | Specify | pending |
| DATA-16 | P1: Identificação (`ObservationId`) e Consistência Esquema-Dados | Specify | pending |
| DATA-17 | P1: Identificação (`ObservationId`) e Consistência Esquema-Dados | Specify | pending |
| DATA-18 | P1: Identificação (`ObservationId`) e Consistência Esquema-Dados | Specify | pending |
| DATA-19 | P2: Utilitários Somente-Leitura e Recorte por `ObservationId` | Specify | pending |
| DATA-20 | P2: Utilitários Somente-Leitura e Recorte por `ObservationId` | Specify | pending |

---

## Sources

- `engenharia_software/ARQUITETURA_E_CONTRATOS.md` Seção 1 (Princípio 2 — Imutabilidade dos Dados de Origem e Zero Transformação Silenciosa), Seção 2.3 (Nível 1 — `experimental_ml.data`), Seção 3.1 (Etapa 1: `DatasetSchemaSpec`, `DatasetBundle`, `load_dataset`), Seção 6.1 (Recorte Estratégico Onda 1 vs. Onda 2) e Seção 7 (`TA-M2.1` / `CA-E1-01`).
- `engenharia_software/ARQUITETURA_E_CONTRATOS.md` ADR-002 (Separação entre Saneamento Estrutural Pré-Partição e Transformação Parametrizada Intra-Fold), ADR-007 (Contrato Formal de Serialização Canônica e Distinção entre `config_hash` e `dataset_hash`) e ADR-008 (Paradigma Modular Baseado em Funções e Estruturas Imutáveis Sem OOP).
- `engenharia_software/ESPECIFICACAO_REQUISITOS.md` `RF1.1` (Ingestão, Cabeçalhos e Papéis das Variáveis), `RF1.2` (Diagnóstico Estrutural, Memória e `dataset_hash`), `RF1.3` (Tipagem Semântica por Coluna), `RF1.7` (Imutabilidade na Etapa 1), `CA-GER-02`, `CA-E1-01`, `RNF01`–`RNF07`.
- `REFERENCIAS_E_FUNDAMENTACAO.md` Seção 3.1 (Parnas, 1972 — Ocultamento de Informação e Transparência Referencial), Seção 4.1 (Kapoor & Narayanan, 2023; Heil et al., 2021 — Prevenção de Data Leakage e Imutabilidade Bruta), Seção 7.1 (Freire et al., 2008; REFORMS, 2024 — Proveniência Prospectiva e Retrospectiva) e Seção 8.1 (NIST FIPS 180-4; Unicode UAX #15 — Canonicalização e Hashing Estrutural).

---

## Success Criteria

- [ ] Enumeração `ColumnSemanticType` e estruturas imutáveis `DatasetSchemaSpec`, `ColumnDescriptor` e `DatasetBundle` definidas e exportadas em `experimental_ml.data`.
- [ ] Validação estrita de papéis disjuntos, nomes de colunas em Unicode NFC e fronteira Onda 1 vs. Onda 2 em `DatasetSchemaSpec`.
- [ ] Função pura `load_dataset` carregando arquivos `.csv`/`.txt` (com/sem cabeçalho e delimitadores configuráveis/auto-detectados, incluindo múltiplos espaços) e dados em memória (`dict`, `ndarray` 2D, lista de registros, `DataFrame` duck-typed) sem dependência obrigatória de `pandas`.
- [ ] Imutabilidade em memória garantida por arrays `numpy.ndarray` com `flags.writeable == False` e dicionários encapsulados em `MappingProxyType`, sem qualquer mutação silenciosa de valores ausentes ou tipos.
- [ ] Validação de consistência esquema-dados (`validate_dataset_schema`), geração/validação de $N$ `ObservationId` únicos e não-nulos (`CA-E1-01`), cálculo de `dataset_hash` delegado ao `core` (**ADR-007**) e utilitários de consulta (`get_column_array`, `slice_bundle_by_observation_ids`).
- [ ] Suíte de testes unitários `tests/unit/test_data_schemas.py` planejada com cobertura 1:1 para os requisitos `DATA-01` a `DATA-20`.

