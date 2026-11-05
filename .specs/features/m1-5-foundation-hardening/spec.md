# M1.5 — Revisão do Plano e Saneamento da Fundação M1 (m1-5-foundation-hardening) Specification

**Approved**: 2026-11-05 - user: "A especificação de m1-5-foundation-hardening foi revisada. A estrutura geral, os achados, as prioridades e as decisões técnicas estão aprovados."

## Problem Statement

A Auditoria Geral de Integridade do Projeto (`m1-integrity-review`) avaliou os marcos M1.1 a M1.4 no commit `6acf6f8` e emitiu o parecer `NÃO APTO` para o início imediato do Marco M2 em razão de 6 achados de severidade `ALTO` (Faixa P0: `AUD-F-001`, `AUD-F-004`, `AUD-F-005`, `AUD-F-006`, `AUD-F-008`, `AUD-F-009`), além de inconsistências moderadas selecionadas da Faixa P1 (`AUD-F-002`, `AUD-F-007`, `AUD-F-010`, `AUD-F-013`). Antes de iniciar o Marco M2, é necessário revisar tecnicamente o plano de correções e executar o saneamento transversal da fundação M1 com cobertura de testes unitários, de regressão e de integração, mantendo rastreabilidade integral de todos os 16 achados (`AUD-F-001` a `AUD-F-016`).

## Goals

- [ ] Revisar e formalizar o plano de correções da auditoria M1 (`P0.1` a `P0.6`, `P1` selecionados e encaminhamento explícito dos itens `ADIADO`), preservando os identificadores e prioridades originais de `.specs/features/m1-integrity-review/reports/07-plano-correcoes.md` sem modificar os artefatos da auditoria original.
- [ ] Eliminar a colisão de concatenação em `core.dataset_hash` (`P0.1` / `AUD-F-004`) e incorporar `observation_ids` de forma canônica à identidade de `DatasetBundle.dataset_hash` via `core.dataset_hash` preservando estritamente a direção arquitetural `data -> core` (`P0.5` / `AUD-F-005`).
- [ ] Centralizar a detecção de `NaN` e valores ausentes em função única reutilizável (`is_nan_scalar` / `is_missing_scalar`) contemplando `float` nativo e `numpy.floating` (`np.float16`, `np.float32`, `np.float64`) em todos os caminhos de ingestão, contagem, validação e hashing (`P0.2` / `AUD-F-008`).
- [ ] Garantir a validação estrita, conversão e preservação de instâncias `ObservationId` em `slice_bundle_by_observation_ids` (`P0.3` / `AUD-F-006`), a política de *whitelist* de escalares imutáveis e semântica unificada de ausentes em colunas `dtype=object` (`P0.4` / `AUD-F-009`) e a conversão de `OverflowError` em `DataIntegrityError` para inteiros fora dos limites de `int64` (`P1` / `AUD-F-007`).
- [ ] Corrigir os exemplos executáveis e a árvore de diretórios do `README.md`, a contagem de símbolos em `ETAPA_ATUAL_ENGENHARIA.md` e a documentação de `dataset_hash` em `ARQUITETURA_E_CONTRATOS.md` (`P0.6` / `AUD-F-001`, `P1` / `AUD-F-002`, `AUD-F-010`), adicionando suíte de testes de integração entre `core`, `data` e `metrics` (`P1` / `AUD-F-013`).

## Out of Scope

Explicitamente excluídos para evitar ampliação indevida de escopo (*scope creep*).

| Feature | Reason |
| --- | --- |
| Implementação de funcionalidades do Marco M2 (`DatasetProfile`, `PreparationPlan`, `SanitizedDatasetView`, `PartitionPlan`, CLI `data`/`partition`) | Atividade exclusivamente corretiva sobre a fundação M1 antes da abertura do M2 |
| Alteração dos relatórios ou resultados em `.specs/features/m1-integrity-review/` | Restrição mandatória de preservação do registro histórico da auditoria original |
| Alterações de `__slots__`, normalização NFC e caracteres de controle em `DomainIdentifier` (`AUD-F-003`) | Mantido como item separado (`ADIADO`) para não misturar refatoração da classe base de identificadores com o saneamento P0 |
| Definição da política de classe positiva para rótulos binários textuais (`AUD-F-011`) | Encaminhado formalmente (`ADIADO`) para a fase Specify do Marco M2 antes de `profile_dataset` e `PreparationPlan` |
| Fabricação retroativa de `.specs/features/m1-1-setup-cli-smoke/verification.md` (`AUD-F-012`) | Vedado fabricar evidência retroativa para simular verificação histórica que não ocorreu em `2026-10-31` |
| Alteração dos scripts do TLC (`AUD-F-014`), micro-higiene fora do escopo (`AUD-F-015`) e instalação de Python 3.10/3.11 no host (`AUD-F-016`) | Mantidos no encaminhamento de baixa prioridade (`ADIADO`) definido no plano original |

---

## Assumptions & Open Questions

Todas as decisões de revisão técnica do plano de correções estão confirmadas e registradas abaixo.

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Delimitação estrutural e compatibilidade em `core.dataset_hash` (`P0.1` / `AUD-F-004`) | Prefixar flag de presença de `schema` (`\x00`/`\x01`), flag e contagem/comprimentos de `observation_ids` (`\x00`/`\x01`), tag `b"TABULAR"`, contagem de colunas `<Q` e comprimento `<Q` de cada nome de coluna UTF-8 NFC antes dos fluxos binários das colunas, além de tags de tipo escalar no ramo `object`; a mudança da representação canônica altera os valores numéricos de hashes anteriores sem exigir retrocompatibilidade com digests antigos | Elimina colisões de fronteira entre nomes de colunas, metadados opcionais e tipos escalares distintos em colunas `object`, garantindo determinismo, separação de tipos e consistência entre formatos | y |
| Política de normalização Unicode NFC em nomes de colunas vs. `observation_ids` no hashing (`HARD-01..03`) | Nomes de colunas e strings de dados são normalizados em NFC tanto no domínio (`DatasetSchemaSpec`, `load_dataset`) quanto em `core.dataset_hash`; já os elementos de `observation_ids` são serializados no hashing com sua representação `str(oid).encode("utf-8")` exata do domínio sem aplicar normalização NFC exclusiva no hashing (enquanto `AUD-F-003` permanece `ADIADO`, evitando que dois `ObservationId` distintos no domínio colidam no hash) | Garante consistência estrita com a identidade efetivamente utilizada pelo domínio sem antecipar `AUD-F-003` | y |
| Centralização de detecção de `NaN` e ausentes (`P0.2` / `AUD-F-008`) | Definir `is_nan_scalar(val)` e `is_missing_scalar(val)` em `experimental_ml.core.hashing` (e exportar em `experimental_ml.core`), cobrindo `float` nativo e `np.floating` (`float16`, `float32`, `float64`, `longdouble`) e excluindo `bool`/`np.bool_`, reutilizando-as em `core/hashing.py`, `data/loader.py`, `data/query.py` e `data/validation.py` | Respeita a direção arquitetural $L_1 (\text{data}) \rightarrow L_0 (\text{core})$ e elimina duplicação de lógica entre módulos | y |
| Contrato de `slice_bundle_by_observation_ids` (`P0.3` / `AUD-F-006`) | Rejeitar `str`/`bytes` passados diretamente como sequência, validar cada item aceitando `ObservationId` ou `str` válida (convertida via `ObservationId(item)` com captura de `ValueError` para `DataIntegrityError`), rejeitar outros tipos (`int`, `None`, etc.) com `DataIntegrityError`, validar duplicatas e pertinência ao bundle e retornar `tuple[ObservationId, ...]` | Garante que entradas inválidas levantem `DataIntegrityError` e que `DatasetBundle.observation_ids` preserve instâncias tipadas de `ObservationId` na ordem solicitada | y |
| Whitelist de escalares imutáveis e semântica de ausentes em colunas `dtype=object` (`P0.4` / `AUD-F-009`) | Tratar `None`, `float` NaN e `np.floating` NaN como o mesmo estado de ausência (convertidos para `None` em colunas `object`, `np.nan` em `float64` e marcador nulo `b"\x00"` no hashing); aceitar apenas `str`/`np.str_`/`DomainIdentifier`/`StrEnum` (materializados como `str` NFC no array físico preservando a informação semântica de `DatasetSchemaSpec` e `ColumnDescriptor`), `bytes` exato/`np.bytes_` (`bytes`), `bool`/`np.bool_` (`bool`), `int` exato/`np.integer` (`int`) e `float` exato/`np.floating` (`float`); rejeitar contêineres, objetos personalizados, subclasses de primitivos com `__dict__` e tipos especiais (`Decimal`, `Fraction`, `complex`) com `DataIntegrityError` | Impede mutação pós-carga de elementos internos do `DatasetBundle`, unifica a semântica de valores ausentes entre ingestão, validação e hashing e preserva os metadados semânticos do schema | y |
| Direção arquitetural `data -> core` na composição de `DatasetBundle.dataset_hash` (`P0.5` / `AUD-F-005`) | Manter `core` sem qualquer dependência de classes de `data`, com assinatura `core.dataset_hash(data_or_path, schema=None, *, observation_ids=None)`; `load_dataset` e `slice_bundle_by_observation_ids` delegam passando explicitamente `bundle.columns`, `bundle.schema` e `observation_ids=bundle.observation_ids`, garantindo `bundle.dataset_hash == core.dataset_hash(bundle.columns, bundle.schema, observation_ids=bundle.observation_ids)` | Preserva estritamente a fronteira arquitetural $L_1 \rightarrow L_0$ sem acoplamento reverso de `core` para `DatasetBundle` | y |
| Investigação histórica de `AUD-F-012` sem fabricação retroativa | Documentar que o ciclo original de `m1-1-setup-cli-smoke` (`d77cc48`, `2026-10-31`) gerou `proofs.md` antes da adoção de `verification.md`, corrigir a menção incorreta no `README.md:104` e não criar arquivo `verification.md` retroativo em `m1-1-setup-cli-smoke/` | Cumpre estritamente a diretriz de não fabricar evidências retroativas nem simular verificação que não ocorreu no marco original | y |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Saneamento de Hashing Canônico e Detecção Unificada de Ausentes (`P0.1`, `P0.2`, `P0.5`) ⭐ MVP

**User Story**: Como engenheiro do framework experimental, quero que o cálculo de `dataset_hash` e a detecção de valores ausentes/`NaN` sejam estruturalmente inequívocos, centralizados e sensíveis aos `observation_ids` passados explicitamente a `core.dataset_hash`, preservando a direção arquitetural `data -> core` e garantindo reprodutibilidade criptográfica e contagem exata de ausentes em todos os tipos flutuantes NumPy.

**Why P1**: Resolve três achados bloqueantes de severidade `ALTO` (`AUD-F-004`, `AUD-F-005`, `AUD-F-008`) que afetam diretamente os contratos de diagnóstico e preparação de dados do Marco M2.

**Acceptance Criteria**:

1. WHEN `core.dataset_hash` serializes in-memory tabular data (`Mapping`, `DataFrame`, 2D `np.ndarray`, or `Sequence[Mapping]`) THEN the system SHALL prefix the presence flag of `schema`, the presence flag and framed items of `observation_ids`, the tabular tag, the column count `<Q`, and the UTF-8 byte length `<Q` of each NFC-normalized column name before its column stream so that `dataset_hash({"ab": [1.0], "c": [2.0]}) != dataset_hash({"a": [1.0], "bc": [2.0]})` and equivalent tabular contents across supported inputs produce identical deterministic digests across processes (`HARD-01`, `AUD-F-004`).
2. WHEN `core.dataset_hash` serializes an `object` column THEN the system SHALL serialize missing values (`None` or any floating `NaN` via `is_missing_scalar`) as `b"\x00"` and prefix each non-null element with a distinct scalar type tag (`str`, `bytes`, `bool`, `int`, `float`) and payload so that distinct scalar types with identical textual representations (`"1"`, `1`, `1.0`, `True`, `b"1"`) produce different hashes (`HARD-02`, `AUD-F-004`).
3. WHEN `core.dataset_hash(data_or_path, schema=None, *, observation_ids=None)` is called with `observation_ids` THEN the system SHALL incorporate the ordered sequence of identifiers into the canonical SHA-256 digest using each identifier's exact domain string representation (`str(oid).encode("utf-8")` prefixed by count `<Q` and byte length `<Q`, without introducing a hashing-only NFC normalization on `observation_ids` while `AUD-F-003` is deferred and without importing `DatasetBundle` in `core`) (`HARD-03`, `AUD-F-005`).
4. WHEN two `DatasetBundle` instances have identical column values and `schema` but distinct `observation_ids` sequences (including after `slice_bundle_by_observation_ids` when `observation_id_col=None`) THEN `load_dataset` and `slice_bundle_by_observation_ids` SHALL produce distinct `dataset_hash` values by delegating to `core.dataset_hash(bundle.columns, bundle.schema, observation_ids=bundle.observation_ids)` so that `bundle.dataset_hash == core.dataset_hash(bundle.columns, bundle.schema, observation_ids=bundle.observation_ids)` always holds (`HARD-04`, `AUD-F-005`).
5. The system SHALL provide centralized scalar missingness functions `is_nan_scalar(val)` and `is_missing_scalar(val)` in `experimental_ml.core.hashing` (re-exported in `experimental_ml.core`) that return `True` for Python `float("nan")`, `np.float16(np.nan)`, `np.float32(np.nan)`, `np.float64(np.nan)`, and any `np.floating` NaN, and `False` for finite numbers, `±Inf`, `bool`, `np.bool_`, `int`, `str`, and `bytes` (`HARD-05`, `AUD-F-008`).
6. WHEN `load_dataset`, `slice_bundle_by_observation_ids`, `assign_or_validate_observation_ids`, or `core.dataset_hash` inspects scalar values for missingness THEN the system SHALL invoke `is_missing_scalar` / `is_nan_scalar` from `experimental_ml.core.hashing` without independent `isinstance(..., float) and math.isnan(...)` checks, accurately counting `np.float16(np.nan)` and `np.float32(np.nan)` in `ColumnDescriptor.n_missing` (`HARD-06`, `AUD-F-008`).

**Independent Test**: Executar testes unitários em `tests/unit/test_core.py` e `tests/unit/test_data_schemas.py` verificando ausência de colisão em nomes de colunas, separação entre tipos escalares com mesma representação textual, diferenciação de `dataset_hash` por `observation_ids` via `core.dataset_hash(bundle.columns, bundle.schema, observation_ids=bundle.observation_ids)` e contagem de `n_missing` para `float`, `np.float16`, `np.float32` e `np.float64`.

---

### P1: Saneamento de Contratos de Dados, Imutabilidade `object` e Limites `int64` (`P0.3`, `P0.4`, `AUD-F-007`) ⭐ MVP

**User Story**: Como consumidor do módulo `experimental_ml.data`, quero que `slice_bundle_by_observation_ids` preserve estritamente instâncias `ObservationId`, que colunas `dtype=object` apliquem semântica unificada de ausentes e aceitem apenas escalares imutáveis da *whitelist* preservando a semântica declarada no schema, e que inteiros fora de `int64` levantem `DataIntegrityError`, para garantir integridade de tipos, imutabilidade pós-carga e conformidade com a hierarquia `ExperimentalMLError`.

**Why P1**: Resolve os achados bloqueantes `AUD-F-006` e `AUD-F-009` (`ALTO`) e o defeito de fronteira `AUD-F-007` (`MODERADO`).

**Acceptance Criteria**:

1. WHEN `slice_bundle_by_observation_ids` is called with valid `ObservationId` or `str` elements present in `bundle.observation_ids` THEN the system SHALL validate each identifier and return a `DatasetBundle` whose `observation_ids` is a `tuple` of `ObservationId` instances (never plain `str`) in the exact caller-requested order (`HARD-07`, `AUD-F-006`).
2. IF `slice_bundle_by_observation_ids` receives a bare `str` or `bytes` instead of a sequence, an empty sequence, a non-`str`/`ObservationId` element (such as `int` or `None`), an invalid `ObservationId` string (empty or containing control whitespace), a duplicate identifier, or an identifier absent from `bundle.observation_ids` THEN the system SHALL raise `DataIntegrityError` (`HARD-08`, `AUD-F-006`).
3. WHEN `load_dataset` coerces a column to `dtype=object` THEN the system SHALL treat `None`, native `float` NaN, and `np.floating` NaN as the same missingness state (normalizing all of them to `None` in the `object` array, counting them in `ColumnDescriptor.n_missing`, and hashing them identically) and SHALL accept only `str`/`np.str_`/`DomainIdentifier`/`StrEnum` (materialized as NFC-normalized `str` in the physical array while preserving `DatasetSchemaSpec.column_semantic_types` and `ColumnDescriptor.semantic_type`/`role`), exact `bytes`/`np.bytes_` (stored as `bytes`), `bool`/`np.bool_` (stored as `bool`), exact `int`/`np.integer` within `int64` bounds (stored as `int`), and exact `float`/`np.floating` (stored as `float`) (`HARD-09`, `AUD-F-009`).
4. IF `load_dataset` encounters a mutable container (`list`, `dict`, `set`, `bytearray`, `memoryview`), a custom or mutable object (`types.SimpleNamespace`, arbitrary class instance), a user-defined subclass of a primitive scalar with mutable `__dict__`, or a non-tabular special numeric type (`complex`, `Decimal`, `Fraction`) in an `object` column THEN the system SHALL raise `DataIntegrityError` identifying the offending type and row index (`HARD-10`, `AUD-F-009`).
5. IF `load_dataset` encounters an integer value outside the signed 64-bit range $[ -2^{63}, 2^{63} - 1 ]$ (either in a numeric column or in a mixed `object` column) THEN the system SHALL catch `OverflowError` and raise `DataIntegrityError` (`HARD-11`, `AUD-F-007`).

**Independent Test**: Executar testes unitários em `tests/unit/test_data_schemas.py` cobrindo fatiamento por `Sequence[str]` e entradas inválidas, equivalência de `None`/`float("nan")`/`np.float32(np.nan)` em colunas `object`, preservação de `ColumnDescriptor.semantic_type` ao materializar `DomainIdentifier`/`StrEnum`, *whitelist* vs. objetos mutáveis/subclasses em colunas `object` e limites exatos $[-2^{63}, 2^{63}-1]$ vs. $\ge 2^{63}$ e $< -2^{63}$.

---

### P1: Correção Documental, Testes de Integração e Governança de Fechamento (`P0.6`, `AUD-F-002`, `AUD-F-010`, `AUD-F-013`) ⭐ MVP

**User Story**: Como pesquisador e auditor do projeto, quero que todos os exemplos do `README.md` executem sem erros, que a documentação arquitetural reflita exatamente os contratos implementados, que exista uma suíte dedicada de testes de integração entre `core`, `data` e `metrics`, e que todos os 16 achados da auditoria tenham seu estado final (`RESOLVIDO` ou `ADIADO`) comprovado por verificação independente, para liberar com segurança o início do Marco M2.

**Why P1**: Resolve `AUD-F-001` (`ALTO`), `AUD-F-002`, `AUD-F-010` e `AUD-F-013` (`MODERADO`) e cumpre as condições formais de encerramento da auditoria.

**Acceptance Criteria**:

1. WHEN every fenced `python` code block in `README.md` is executed in an isolated Python subprocess THEN the system SHALL exit with code `0` without exceptions, using the real public signatures and attributes (`is_better` with valid/undefined `MetricValue`, `spec.rtol`, `DatasetSchemaSpec(..., column_semantic_types=...)`, and `len(bundle.feature_cols)`) (`HARD-12`, `AUD-F-001`).
2. The documentation in `README.md`, `engenharia_software/ARQUITETURA_E_CONTRATOS.md`, and `engenharia_software/ETAPA_ATUAL_ENGENHARIA.md` SHALL accurately reflect the on-disk directory tree (`core/types.py`, `core/findings.py`, without non-existent `core/exceptions.py`, `core/identifiers.py`, or `m1-1-setup-cli-smoke/verification.md`), the 13 exported symbols in `experimental_ml.data.__all__`, and the sensitivity of tabular `dataset_hash` to column order and `observation_ids` (`HARD-13`, `AUD-F-002`, `AUD-F-010`).
3. The test suite SHALL include `tests/integration/test_m1_foundation_integration.py` exercising end-to-end ingestion (`load_dataset`), schema validation (`DatasetSchemaSpec`), `ObservationId` preservation across slicing (`slice_bundle_by_observation_ids`), metric computation and multi-fold aggregation/ranking (`compute_metric`, `aggregate_fold_metrics`, `rank_configurations`), cross-process hash determinism (`PYTHONHASHSEED`), and automated execution of all `README.md` Python blocks (`HARD-14`, `AUD-F-013`).
4. The engineering records in `.specs/features/m1-5-foundation-hardening/` SHALL document the revised remediation plan, the historical investigation of `AUD-F-012` (without fabricating retroactive evidence in `m1-1-setup-cli-smoke/`), the explicit status of all 16 audit findings (`10 RESOLVIDO`, `6 ADIADO` with target milestone/rationale), the independent verification report (`verification.md`), and the final readiness verdict (`APTO` for M2) in `RESULTS.md` (`HARD-15`).

**Independent Test**: Executar `.venv/bin/pytest tests/ -v` (incluindo `tests/integration/test_m1_foundation_integration.py`) e os validadores do TLC (`validate_spec.py`, `validate_tasks.py`, `check_proofs.py`, `validate_verification.py`).

---

## Edge Cases

- IF a 2D `np.ndarray` of `dtype=np.float16` or `dtype=np.float32` containing `np.nan` is loaded via `load_dataset` THEN the system SHALL record the exact count of `NaN` values in `ColumnDescriptor.n_missing` and convert them to `np.nan` in the `float64` buffer (`HARD-06`).
- IF an `object` column contains a mix of `None`, `float("nan")`, and `np.float32(np.nan)` THEN `load_dataset` SHALL normalize all three to `None`, count all three in `ColumnDescriptor.n_missing`, and produce an identical `dataset_hash` to the same column containing `None` in all three positions (`HARD-09`).
- IF `slice_bundle_by_observation_ids(bundle, "obs_000000")` is called with a bare `str` instead of a non-string `Sequence` THEN the system SHALL raise `DataIntegrityError` rather than iterating over characters `'o'`, `'b'`, `'s'`, ... (`HARD-08`).
- IF a user-defined subclass of `str` or `int` (e.g., `class MutableStr(str): pass` with an attached attribute) is passed in an `object` column THEN the system SHALL reject it with `DataIntegrityError` (`HARD-10`).
- WHEN boundary integers $-2^{63}$ (`-9223372036854775808`) and $2^{63}-1$ (`9223372036854775807`) are passed to `load_dataset` THEN the system SHALL accept them as `int64`, whereas $-2^{63}-1$ and $2^{63}$ SHALL raise `DataIntegrityError` (`HARD-11`).

---

## Implicit-Requirement Dimensions Sweep

| Dimension | Resolution for `m1-5-foundation-hardening` |
| --- | --- |
| Input validation & bounds | Coberto por `HARD-05..11` (validação de `NaN` multi-dtype, `ObservationId` em fatiamento, *whitelist* de escalares em colunas `object` e limites $[-2^{63}, 2^{63}-1]$ para `int64`). |
| Failure / partial-failure states | Coberto por `HARD-08`, `HARD-10`, `HARD-11` (todas as falhas de validação/fronteira levantam `DataIntegrityError` dentro da hierarquia `ExperimentalMLError`, sem construir `DatasetBundle` parcial). |
| Idempotency / retry / duplicate handling | Coberto por `HARD-01..04` e `HARD-08` (determinismo idempotente de `dataset_hash` entre processos e rejeição estrita de `ObservationId` duplicados no fatiamento). |
| State-transition integrity | Coberto por `HARD-07` e `HARD-09` (preservação de imutabilidade pós-carga em colunas `object`, preservação de semântica no `ColumnDescriptor` e preservação de `ObservationId` após `slice_bundle_by_observation_ids`). |
| Remaining dimensions (Auth, Concurrency, Data expiry, Observability, External calls) | `N/A because` o framework opera 100% offline em memória/arquivos locais de processo único sem autenticação, rede ou persistência com expiração (`RNF03`). |

---

## Revisão do Plano de Correções e Destino dos 16 Achados (`07-plano-correcoes.md`)

| Achado | Prioridade Original | Severidade / Categoria | Decisão na Revisão Técnica (`m1-5-foundation-hardening`) | Estado Alvo na Atividade |
| :--- | :---: | :---: | :--- | :---: |
| **`AUD-F-004`** | **P0.1** | `ALTO` / `DEFEITO` | Incluído (`HARD-01`, `HARD-02`): prefixar contagem de colunas `<Q`, comprimento `<Q` de cada nome de coluna NFC, flags de presença de `schema`/`observation_ids` e tags de tipo escalar em colunas `object` em `core/hashing.py` (alterando valores numéricos de hashes antigos com determinismo total no novo contrato). | `RESOLVIDO` |
| **`AUD-F-008`** | **P0.2** | `ALTO` / `DEFEITO` | Incluído (`HARD-05`, `HARD-06`): centralizar `is_nan_scalar` e `is_missing_scalar` em `core/hashing.py` e reutilizar em `loader.py`, `query.py`, `validation.py` e `hashing.py`. | `RESOLVIDO` |
| **`AUD-F-006`** | **P0.3** | `ALTO` / `DEFEITO` | Incluído (`HARD-07`, `HARD-08`): validar/converter elementos `str`/`ObservationId` em `slice_bundle_by_observation_ids`, rejeitar entradas inválidas com `DataIntegrityError` e retornar `tuple[ObservationId, ...]`. | `RESOLVIDO` |
| **`AUD-F-009`** | **P0.4** | `ALTO` / `RISCO` | Incluído (`HARD-09`, `HARD-10`): substituir *blacklist* por *whitelist* explícita de escalares imutáveis materializados em `loader.py`, unificando `None`/`float` NaN/`np.floating` NaN como `None` e preservando a semântica da coluna em `ColumnDescriptor`. | `RESOLVIDO` |
| **`AUD-F-005`** | **P0.5** | `ALTO` / `RISCO` | Incluído (`HARD-03`, `HARD-04`): manter direção `data -> core` com assinatura `core.dataset_hash(data_or_path, schema=None, *, observation_ids=None)` e delegar a partir de `load_dataset` e `slice_bundle_by_observation_ids` passando `bundle.columns`, `bundle.schema` e `observation_ids=bundle.observation_ids`. | `RESOLVIDO` |
| **`AUD-F-001`** | **P0.6** | `ALTO` / `DEFEITO` | Incluído (`HARD-12`): corrigir blocos Python 3 e 4 do `README.md` com as assinaturas e atributos reais. | `RESOLVIDO` |
| **`AUD-F-007`** | **P1.1** | `MODERADO` / `DEFEITO` | Incluído (`HARD-11`): capturar `OverflowError` em inteiros fora de `int64` em `loader.py` e levantar `DataIntegrityError`. | `RESOLVIDO` |
| **`AUD-F-002`** | **P1.3** | `MODERADO` / `DEFEITO` | Incluído (`HARD-13`): corrigir árvore de diretórios do `README.md` (`core/types.py`, `core/findings.py`, remoção de `m1-1/verification.md`) e contagem de 13 símbolos em `ETAPA_ATUAL_ENGENHARIA.md`. | `RESOLVIDO` |
| **`AUD-F-010`** | **P1.3** | `MODERADO` / `RISCO` | Incluído (`HARD-13`): alinhar `ARQUITETURA_E_CONTRATOS.md` e `README.md` quanto à sensibilidade de `dataset_hash` à ordem das colunas e aos `observation_ids`. | `RESOLVIDO` |
| **`AUD-F-013`** | **P1.6** | `MODERADO` / `MELHORIA` | Incluído (`HARD-14`): criar `tests/integration/test_m1_foundation_integration.py` cobrindo o fluxo integrado `core` + `data` + `metrics` e a execução dos blocos Python do `README.md`. | `RESOLVIDO` |
| **`AUD-F-003`** | P1.2 | `MODERADO` / `RISCO` | Encaminhado separadamente (`HARD-15`): mantido fora do escopo de código desta atividade para avaliação própria sem misturar alterações em `DomainIdentifier` com as correções P0. | `ADIADO` |
| **`AUD-F-011`** | P1.4 | `MODERADO` / `RISCO` | Encaminhado para o Specify do Marco M2 (`HARD-15`): a política de classe positiva para rótulos binários textuais será definida antes da implementação de `profile_dataset` e `PreparationPlan`. | `ADIADO` |
| **`AUD-F-012`** | P1.5 | `MODERADO` / `RISCO` | Investigado no histórico git (`d77cc48`, `d9b7bd3`, `c0ca71c`): `m1-1-setup-cli-smoke` concluiu antes da adoção de `verification.md`; vedada fabricação retroativa de evidência; menção incorreta no `README.md` corrigida via `AUD-F-002`. | `ADIADO` |
| **`AUD-F-014`** | P2.2 | `BAIXO` / `MELHORIA` | Mantido no encaminhamento de baixa prioridade do plano original (comportamento conhecido de `validate_verification.py` frente ao avanço de `HEAD`). | `ADIADO` |
| **`AUD-F-015`** | P2.1 | `BAIXO` / `MELHORIA` | Mantido no encaminhamento de baixa prioridade do plano original (micro-higiene de `_ALLOWED_AGG_SCOPES` e `assert` interno). | `ADIADO` |
| **`AUD-F-016`** | P2.3 | `BAIXO` / `LIMITAÇÃO DOCUMENTADA` | Mantido como limitação documentada de ambiente local (binários Python 3.10 e 3.11 ausentes no host). | `ADIADO` |

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| HARD-01 | P1: Saneamento de Hashing e Ausentes (`AUD-F-004` colunas, NFC e determinismo entre formatos) | Tasks | In Tasks |
| HARD-02 | P1: Saneamento de Hashing e Ausentes (`AUD-F-004` tipos escalares e ausentes em `object`) | Tasks | In Tasks |
| HARD-03 | P1: Saneamento de Hashing e Ausentes (`AUD-F-005` `core.dataset_hash` com `observation_ids` e direção `data -> core`) | Tasks | In Tasks |
| HARD-04 | P1: Saneamento de Hashing e Ausentes (`AUD-F-005` delegação de `DatasetBundle.dataset_hash`) | Tasks | In Tasks |
| HARD-05 | P1: Saneamento de Hashing e Ausentes (`AUD-F-008` `is_nan_scalar` / `is_missing_scalar`) | Tasks | In Tasks |
| HARD-06 | P1: Saneamento de Hashing e Ausentes (`AUD-F-008` unificação em `data` e `core`) | Tasks | In Tasks |
| HARD-07 | P1: Contratos de Dados e Imutabilidade (`AUD-F-006` preservação de `ObservationId`) | Tasks | In Tasks |
| HARD-08 | P1: Contratos de Dados e Imutabilidade (`AUD-F-006` validação e `DataIntegrityError`) | Tasks | In Tasks |
| HARD-09 | P1: Contratos de Dados e Imutabilidade (`AUD-F-009` *whitelist*, semântica de ausentes e preservação semântica no schema) | Tasks | In Tasks |
| HARD-10 | P1: Contratos de Dados e Imutabilidade (`AUD-F-009` rejeição de mutáveis/subclasses/especiais) | Tasks | In Tasks |
| HARD-11 | P1: Contratos de Dados e Imutabilidade (`AUD-F-007` captura de `OverflowError` em `int64`) | Tasks | In Tasks |
| HARD-12 | P1: Documentação, Integração e Governança (`AUD-F-001` blocos Python do `README.md`) | Tasks | In Tasks |
| HARD-13 | P1: Documentação, Integração e Governança (`AUD-F-002` e `AUD-F-010` alinhamento documental) | Tasks | In Tasks |
| HARD-14 | P1: Documentação, Integração e Governança (`AUD-F-013` suíte `test_m1_foundation_integration.py`) | Tasks | In Tasks |
| HARD-15 | P1: Documentação, Integração e Governança (Rastreabilidade dos 16 achados, `verification.md` e parecer final `APTO`) | Tasks | In Tasks |

**Coverage:** 15 total, 15 mapped to tasks, 0 unmapped

---

## Sources

- `.specs/features/m1-integrity-review/reports/06-achados.md` - Registro consolidado dos 16 achados da Auditoria Geral de Integridade do M1
- `.specs/features/m1-integrity-review/reports/07-plano-correcoes.md` - Plano de correções priorizadas (P0, P1, P2)
- `.specs/features/m1-integrity-review/reports/08-parecer.md` - Parecer de prontidão para o M2 e regra de decisão
- `engenharia_software/ARQUITETURA_E_CONTRATOS.md` - Contratos arquiteturais do Marco M1 e ADRs (`ADR-005`, `ADR-007`, `ADR-008`)

---

## Success Criteria

- [ ] Todos os 6 achados P0 (`AUD-F-001`, `AUD-F-004`, `AUD-F-005`, `AUD-F-006`, `AUD-F-008`, `AUD-F-009`) e os 4 achados P1 selecionados (`AUD-F-002`, `AUD-F-007`, `AUD-F-010`, `AUD-F-013`) estão `RESOLVIDOS` e cobertos por testes automatizados que falhariam sem a correção.
- [ ] Os 6 achados fora do escopo de implementação imediata (`AUD-F-003`, `AUD-F-011`, `AUD-F-012`, `AUD-F-014`, `AUD-F-015`, `AUD-F-016`) estão formalmente documentados como `ADIADO` com justificativa e encaminhamento explícito.
- [ ] A suíte completa do projeto (`pytest tests/ -v`), incluindo `tests/integration/test_m1_foundation_integration.py` e a execução dos 4 blocos Python do `README.md`, passa 100% sem erros.
- [ ] Os relatórios originais em `.specs/features/m1-integrity-review/` permanecem intactos (`0` bytes de diff).
- [ ] O verificador independente (`author != verifier`) audita o código e os testes de cada achado e emite `verification.md` com veredito `PASS`, habilitando a transição formal do projeto para **`APTO`** ao início do Marco M2.
