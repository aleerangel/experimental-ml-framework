# Registro de Validação e Aceite — Marco M1.4

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M1.4 (`m1-4-datasets-schemas`)  
> **Data de Validação:** 04 de Novembro de 2026  
> **Commit de Implementação:** [`361d318`](https://github.com/alexandrerangel/experimental-ml-framework/commit/361d318)  
> **Ambiente Computacional:** Linux 6.17.5-arch1-1 (x86_64), Python 3.12.15, NumPy 2.5.4, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | `pip install -e ".[dev]"` com NumPy | Instalado e validado (`numpy 2.5.4`) | **APROVADO** |
| **Testes Unitários Automatizados** | 29 testes em `tests/unit/test_data_schemas.py` | 29 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 81 testes em `pytest tests/` | 81 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria independente | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Homologação Manual** | Roteiro `ACCEPTANCE.md` (8 capacidades) | Executada e homologada formalmente em 2026-11-04 | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte Unitária do Módulo Data (`tests/unit/test_data_schemas.py`)

Execução realizada no interpretador do ambiente virtual (`.venv/bin/pytest tests/unit/test_data_schemas.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.15, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 29 items

tests/unit/test_data_schemas.py::test_domain_structures_and_enum_immutable PASSED [  3%]
tests/unit/test_data_schemas.py::test_schema_spec_nfc_normalization_and_encapsulation PASSED [  6%]
tests/unit/test_data_schemas.py::test_schema_spec_rejects_empty_and_control_chars PASSED [ 10%]
tests/unit/test_data_schemas.py::test_schema_spec_blocks_wave2_features PASSED [ 13%]
tests/unit/test_data_schemas.py::test_schema_spec_enforces_disjoint_roles PASSED [ 17%]
tests/unit/test_data_schemas.py::test_schema_spec_config_hash_invariance PASSED [ 20%]
tests/unit/test_data_schemas.py::test_tabular_parsing_supported_delimiters_and_quotes PASSED [ 24%]
tests/unit/test_data_schemas.py::test_delimiter_sniffer_automatic_detection PASSED [ 27%]
tests/unit/test_data_schemas.py::test_delimiter_sniffer_ambiguity_raises_error PASSED [ 31%]
tests/unit/test_data_schemas.py::test_explicit_delimiter_overrides_detection PASSED [ 34%]
tests/unit/test_data_schemas.py::test_ragged_rows_raise_data_integrity_error PASSED [ 37%]
tests/unit/test_data_schemas.py::test_empty_or_zero_rows_file_raises_error PASSED [ 41%]
tests/unit/test_data_schemas.py::test_parsing_has_header_false_and_column_names PASSED [ 44%]
tests/unit/test_data_schemas.py::test_header_validation_empty_or_duplicate_names PASSED [ 48%]
tests/unit/test_data_schemas.py::test_column_descriptor_fields_and_roles PASSED [ 51%]
tests/unit/test_data_schemas.py::test_semantic_types_declared_vs_default_fallbacks PASSED [ 55%]
tests/unit/test_data_schemas.py::test_observation_ids_positional_generation PASSED [ 58%]
tests/unit/test_data_schemas.py::test_observation_ids_source_column_validation PASSED [ 62%]
tests/unit/test_data_schemas.py::test_dataset_schema_validation_structural_errors PASSED [ 65%]
tests/unit/test_data_schemas.py::test_load_dataset_sources_and_bundle_ownership PASSED [ 68%]
tests/unit/test_data_schemas.py::test_load_dataset_defensive_copies_isolation PASSED [ 72%]
tests/unit/test_data_schemas.py::test_bundle_numeric_columns_buffer_immutability PASSED [ 75%]
tests/unit/test_data_schemas.py::test_bundle_object_columns_scalar_immutability PASSED [ 79%]
tests/unit/test_data_schemas.py::test_load_dataset_preserves_missing_values PASSED [ 82%]
tests/unit/test_data_schemas.py::test_bundle_structural_metadata_completeness PASSED [ 86%]
tests/unit/test_data_schemas.py::test_dataset_hash_canonical_in_memory_digest PASSED [ 89%]
tests/unit/test_data_schemas.py::test_raw_source_hash_file_and_memory PASSED [ 93%]
tests/unit/test_data_schemas.py::test_get_column_array_view_and_copy PASSED [ 96%]
tests/unit/test_data_schemas.py::test_slice_bundle_by_observation_ids_ordering_and_hash PASSED [100%]

============================== 29 passed in 0.14s ==============================
```

### 2.2 Suíte Geral de Regressão da Base de Código (`pytest tests/ -v`)

```text
============================== 81 passed in 0.25s ==============================
```

---

## 3. Verificação Independente TLC

- **Comando**: `.agent/skills/tlc-spec-driven/scripts/validate_verification.py m1-4-datasets-schemas --strict`
- **Veredito**: `PASS` (29 de 29 critérios comprovados; 0 findings)
- **Subagente Verificador**: `bf692423-9258-4be6-824d-7b267ba7cbf2` (author != verifier)

---

## 4. Matriz de Conformidade com a Especificação (DATA-01 a DATA-29)

| Requisito | Descrição Sintética | Teste / Checagem | Status |
| :--- | :--- | :--- | :---: |
| **DATA-01** | Estruturas imutáveis `DatasetSchemaSpec`, `ColumnDescriptor`, `DatasetBundle` e enum `ColumnSemanticType` | `test_domain_structures_and_enum_immutable` (C1) | **APROVADO** |
| **DATA-02** | Normalização NFC de colunas, `ignore_cols` como tupla e encapsulamento de dicionários | `test_schema_spec_nfc_normalization_and_encapsulation` (C2) | **APROVADO** |
| **DATA-03** | Rejeição de nomes vazios, whitespace-only e caracteres de controle com `ConfigurationError` | `test_schema_spec_rejects_empty_and_control_chars` (C3) | **APROVADO** |
| **DATA-04** | Bloqueio de funcionalidades da Onda 2 (`MULTI_TARGET_REGRESSION`, múltiplos alvos, transformações) | `test_schema_spec_blocks_wave2_features` (C4) | **APROVADO** |
| **DATA-05** | Disjunção estrita de papéis de colunas com `ConfigurationError` | `test_schema_spec_enforces_disjoint_roles` (C5) | **APROVADO** |
| **DATA-06** | `config_hash(schema)` canônico invariante a NFD/NFC e ordenação de chaves | `test_schema_spec_config_hash_invariance` (C6) | **APROVADO** |
| **DATA-07** | Ingestão a partir de arquivos e memória retornando `DatasetBundle` com posse exclusiva | `test_load_dataset_sources_and_bundle_ownership` (C7) | **APROVADO** |
| **DATA-08** | Cópias defensivas na memória impedindo que mutações na fonte afetem o bundle | `test_load_dataset_defensive_copies_isolation` (C8) | **APROVADO** |
| **DATA-09** | Arrays numéricos e booleanos respaldados por buffers `bytes` imutáveis recusando `setflags` | `test_bundle_numeric_columns_buffer_immutability` (C9) | **APROVADO** |
| **DATA-10** | Colunas `object` restritas a escalares imutáveis com `writeable=False` | `test_bundle_object_columns_scalar_immutability` (C10) | **APROVADO** |
| **DATA-11** | Preservação de valores ausentes originais (`np.nan` em float, `None` em object) | `test_load_dataset_preserves_missing_values` (C11) | **APROVADO** |
| **DATA-12** | Registro completo de metadados estruturais, descritores, hashes e bytes de memória | `test_bundle_structural_metadata_completeness` (C12) | **APROVADO** |
| **DATA-13** | `dataset_hash` canônico idêntico entre CSV (CRLF/LF) e memória, e distinção int vs float | `test_dataset_hash_canonical_in_memory_digest` (C13) | **APROVADO** |
| **DATA-14** | `raw_source_hash` refletindo bytes do arquivo em disco ou estrutura em memória | `test_raw_source_hash_file_and_memory` (C14) | **APROVADO** |
| **DATA-15** | Suporte a delimitadores `,`, `;`, `\t`, `|`, múltiplos espaços e aspas RFC 4180 | `test_tabular_parsing_supported_delimiters_and_quotes` (C15) | **APROVADO** |
| **DATA-16** | Detecção automática de delimitadores inspecionando até 100 linhas ($M \ge 2$) | `test_delimiter_sniffer_automatic_detection` (C16) | **APROVADO** |
| **DATA-17** | Falha explícita sob ambiguidade ou inconsistência de delimitadores | `test_delimiter_sniffer_ambiguity_raises_error` (C17) | **APROVADO** |
| **DATA-18** | Sobrescrita manual por delimitador explícito desativando sniffer | `test_explicit_delimiter_overrides_detection` (C18) | **APROVADO** |
| **DATA-19** | Rejeição explícita de linhas irregulares (*ragged rows*) com indicação da linha e contagens | `test_ragged_rows_raise_data_integrity_error` (C19) | **APROVADO** |
| **DATA-20** | Rejeição de arquivos com zero bytes, somente espaços ou cabeçalho com zero linhas ($N = 0$) | `test_empty_or_zero_rows_file_raises_error` (C20) | **APROVADO** |
| **DATA-21** | `has_header=False` com atribuição de nomes ou geração sequencial `col_j` | `test_parsing_has_header_false_and_column_names` (C21) | **APROVADO** |
| **DATA-22** | Rejeição de nomes vazios ou duplicados no cabeçalho após normalização NFC | `test_header_validation_empty_or_duplicate_names` (C22) | **APROVADO** |
| **DATA-23** | Preenchimento de `ColumnDescriptor` com índices, papéis, tipo físico e contagem de nulos | `test_column_descriptor_fields_and_roles` (C23) | **APROVADO** |
| **DATA-24** | Tipagem semântica declarada (`is_declared=True`) vs fallbacks neutros transparentes | `test_semantic_types_declared_vs_default_fallbacks` (C24) | **APROVADO** |
| **DATA-25** | Geração posicional sequencial `obs_000000` quando `observation_id_col` é omitida | `test_observation_ids_positional_generation` (C25) | **APROVADO** |
| **DATA-26** | Validação estrita de não-nulidade e unicidade de `ObservationId` na fonte | `test_observation_ids_source_column_validation` (C26) | **APROVADO** |
| **DATA-27** | Validação estrutural de $N > 0$, $M > 0$, colunas do esquema e `len(feature_cols) >= 1` | `test_dataset_schema_validation_structural_errors` (C27) | **APROVADO** |
| **DATA-28** | `get_column_array` com view somente-leitura (`copy=False`) ou cópia mutável (`copy=True`) | `test_get_column_array_view_and_copy` (C28) | **APROVADO** |
| **DATA-29** | `slice_bundle_by_observation_ids` preservando ordem solicitada e recalculando hash | `test_slice_bundle_by_observation_ids_ordering_and_hash` (C29) | **APROVADO** |

---

## 5. Estado Atual da Homologação Manual

- **Situação**: **APROVADO** (Homologação manual formalmente aprovada pelo pesquisador/usuário em 2026-11-04 - user: "aprovado").
- **Próximos Passos**: Marco M1.4 formalmente concluído; disponibilização para a Fase 2 (M2 - Partições, Sanitização e Validação).
