# 5. Matriz de Conformidade, Documentação e Rastreabilidade (`05-rastreabilidade.md`)

**Dimensão:** E — Documentação e Rastreabilidade (`DOC-01` a `DOC-07`)  
**Sonda Executada:** [docs_and_traceability_probe.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/probes/docs_and_traceability_probe.py)

---

## 1. Execução Empírica dos Blocos de Código Python do `README.md` (`DOC-01`)

Todos os **4 blocos `python`** da seção "Uso Programático em Python" do [README.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/README.md#L224-L323) foram extraídos e executados em subprocessos isolados:

| Bloco | Linhas (`README.md`) | Escopo Demonstrado | Exit Code | Resultado / Erro em Tempo de Execução |
| :---: | :---: | :--- | :---: | :--- |
| 1 | `L224-L229` | `experimental_ml.__version__` | `0` | **PASSA** (`0.1.0.dev0`) |
| 2 | `L232-L259` | `experimental_ml.core` | `0` | **PASSA** |
| 3 | `L262-L289` | `experimental_ml.metrics` | **`1`** | **FALHA (`AUD-F-001`)**: `is_better(cand_a=rmse_val, cand_b=None, direction=spec.direction)` levanta `ConfigurationError: Unsupported candidate type <class 'NoneType'>` (`is_better` exige `MetricValue \| AggregatedMetricValue`). Além disso, o comentário na linha 280 cita `spec.tolerance_rtol`, mas o atributo real em `MetricSpec` é `spec.rtol`. |
| 4 | `L292-L323` | `experimental_ml.data` | **`1`** | **FALHA (`AUD-F-001`)**: `DatasetSchemaSpec(..., semantic_types={...})` levanta `TypeError: DatasetSchemaSpec.__init__() got an unexpected keyword argument 'semantic_types'` (o parâmetro real é `column_semantic_types`). Além disso, o comentário na linha 314 cita `bundle.n_features`, mas o atributo real em `DatasetBundle` é `bundle.feature_cols`. |

**Resultado (`DOC-01`):** **`NÃO CONFORME`** (Achado `AUD-F-001`).

---

## 2. Correspondência entre a Árvore de Diretórios do `README.md` e o Disco (`DOC-02`)

A comparação automatizada entre a árvore documentada em [README.md:100-152](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/README.md#L100-L152) e o sistema de arquivos identificou quatro divergências:

1. **`src/experimental_ml/core/exceptions.py` (`README.md:122`):** **Inexistente em disco** (as exceções residem em `src/experimental_ml/core/findings.py`).
2. **`src/experimental_ml/core/identifiers.py` (`README.md:125`):** **Inexistente em disco** (os identificadores residem em `src/experimental_ml/core/types.py`).
3. **`src/experimental_ml/core/types.py`:** **Existente em disco**, mas omitido da árvore de `core/` no `README.md` (embora `types.py` apareça em `metrics/` e `data/`).
4. **`.specs/features/m1-1-setup-cli-smoke/verification.md` (`README.md:104`):** O comentário na linha 104 afirma que `m1-1-setup-cli-smoke/` contém `verification.md`, mas esse arquivo **não existe** em disco (`AUD-F-012`).

**Resultado (`DOC-02`):** **`NÃO CONFORME`** (Achados `AUD-F-002` e `AUD-F-012`).

---

## 3. Consistência de Contagens, Versões e Símbolos Públicos (`DOC-03`, `DOC-04`)

* **Versão do pacote (`0.1.0.dev0`) e contagens de testes (`81` total = `12` smoke + `18` core + `22` metrics + `29` data):** Consistentes em `README.md`, `ARQUITETURA_E_CONTRATOS.md`, `ESPECIFICACAO_REQUISITOS.md`, `ETAPA_ATUAL_ENGENHARIA.md` e `.specs/STATE.md`.
* **Importabilidade dos símbolos públicos (`DOC-04`):** Todos os símbolos exportados em `experimental_ml.core` (`26`), `experimental_ml.metrics` (`27`) e `experimental_ml.data` (`13`) são importáveis sem erros.
* **Divergência de contagem em `ETAPA_ATUAL_ENGENHARIA.md` (`DOC-03` / `AUD-F-002`):** A linha 87 de [ETAPA_ATUAL_ENGENHARIA.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/engenharia_software/ETAPA_ATUAL_ENGENHARIA.md#L87) afirma que `src/experimental_ml/data/__init__.py` faz *"re-exportação de 7 símbolos públicos centrais com `__all__`"*, quando na realidade `experimental_ml.data.__all__` exporta **13 símbolos** (`ColumnSemanticType`, `DatasetSchemaSpec`, `validate_schema_spec`, `ColumnDescriptor`, `DatasetBundle`, `SUPPORTED_DELIMITERS`, `detect_delimiter`, `parse_tabular_text`, `assign_or_validate_observation_ids`, `derive_column_descriptor`, `validate_dataset_schema`, `load_dataset`, `get_column_array`, `slice_bundle_by_observation_ids`).

---

## 4. Contradições Documentais e Semânticas de Hashing (`DOC-05`)

Foram identificadas três contradições diretas entre a documentação arquitetural e o comportamento real/especificado:

1. **Ordem de colunas em `dataset_hash` (`AUD-F-010`):**
   * `ARQUITETURA_E_CONTRATOS.md` (linhas 250 e 743) e `README.md` (linha 94) afirmam que `dataset_hash` é *"invariante a quebras de linha e ordenação de chaves"*.
   * Contudo, a especificação aprovada do M1.4 (`m1-4-datasets-schemas/spec.md`, Goal 5) determinou que a **ordem das colunas faz parte da identidade** do dataset, e `core.dataset_hash` itera na ordem de `data.keys()`, produzindo hashes diferentes para `{"x": ..., "y": ...}` e `{"y": ..., "x": ...}` (conforme provado em `INT-04`).
2. **Papel de `observation_ids` em `dataset_hash` (`AUD-F-005`):**
   * `ARQUITETURA_E_CONTRATOS.md` (linhas 210 e 707) exige *"Distinção de `dataset_hash` quando dois arrays possuem mesmos bytes brutos mas nomes de colunas, `dtypes` ou `observation_ids` distintos"*.
   * Na implementação, `core.dataset_hash(bundle.columns, bundle.schema)` não recebe `bundle.observation_ids`, de modo que dois `DatasetBundle` com mesmas colunas e `observation_ids` distintos (quando `observation_id_col=None`) geram o mesmo `dataset_hash`.
3. **Semântica de `core.dataset_hash(path, schema)` vs. `DatasetBundle` (`AUD-F-010`):**
   * O `ADR-007` define `dataset_hash(path, schema)` para arquivos em disco como o SHA-256 dos bytes brutos do arquivo concatenado ao `config_hash(schema)`. No M1.4, esse valor passou a ser armazenado em `bundle.raw_source_hash`, enquanto `bundle.dataset_hash` armazena `core.dataset_hash(bundle.columns, schema)`. Assim, `core.dataset_hash(csv_path, schema) != load_dataset(csv_path, schema).dataset_hash`.

---

## 5. Matriz Completa de Rastreabilidade do Marco M1 (`DOC-06`)

| ID Requisito / Critério | Descrição Resumida | Módulo / Arquivo Implementado | Teste(s) de Verificação (`tests/`) | Status Real Verificado na Auditoria |
| :--- | :--- | :--- | :--- | :--- |
| **`TA-M1.1`** | Setup `.venv`, `pyproject.toml` (Hatchling), CLI `expml` (`--version`, `--help`, exit `2`) e smoke tests | `pyproject.toml`, `src/experimental_ml/cli/main.py` | `tests/test_smoke.py` (12 testes) | **`CONFORME`** (`12/12 passed`; ressalva de governança `AUD-F-012` por ausência de `m1-1/verification.md`) |
| **`TA-M1.2` / `CA-GER-02`** | Identificadores imutáveis, enums, `derive_seeds`, `config_hash` e `dataset_hash` (ADR-007) | `src/experimental_ml/core/{types,enums,findings,seeds,hashing}.py` | `tests/unit/test_core.py` (18 testes) | **`PARCIALMENTE CONFORME`** (`18/18 passed`, mas com achados `AUD-F-003` em `DomainIdentifier`, `AUD-F-004` colisão de nomes em `dataset_hash` e `AUD-F-005` omissão de `observation_ids`) |
| **`TA-M1.3` / `CA-GER-03` / `CA-COND-REG-01` / `CA-COND-CLAS-01`** | 15 métricas vetorizadas em `float64`, `METRICS_CATALOG`, propagação estrita de `UNDEFINED_NAN`, `is_better`, `aggregate_fold_metrics`, `rank_configurations` | `src/experimental_ml/metrics/{types,validation,regression,classification,catalog,aggregation}.py` | `tests/unit/test_metrics.py` (22 testes) | **`CONFORME COM RESSALVA`** (`22/22 passed`, 100% precisão e invariantes ADR-005; ressalva `AUD-F-011` para `pos_label=1` padrão em alvos binários string) |
| **`TA-M1.4` / `CA-E1-01` (parcial)** | `DatasetSchemaSpec`, `ColumnSemanticType`, `ColumnDescriptor`, `DatasetBundle`, `load_dataset` RFC 4180, `get_column_array`, `slice_bundle_by_observation_ids` | `src/experimental_ml/data/{schema,types,parsing,validation,loader,query}.py` | `tests/unit/test_data_schemas.py` (29 testes) | **`PARCIALMENTE CONFORME`** (`29/29 passed`, buffers C imutáveis numéricos operantes; achados `AUD-F-006`, `AUD-F-007`, `AUD-F-008`, `AUD-F-009`) |
| **`RF1.1`** | Ingestão `.csv`/`.txt`/`.tsv` e memória, delimitadores, cabeçalho e papéis univariados | `src/experimental_ml/data/{schema,parsing,loader}.py` | `test_data_schemas.py` | **`CONFORME`** (Onda 1) |
| **`RF1.2`** | Metadados estruturais (`n_rows`, `n_cols`, `memory_bytes`) e hashes tripartites | `src/experimental_ml/data/{types,loader}.py` | `test_data_schemas.py` | **`PARCIALMENTE CONFORME`** (fundação M1.4 concluída com ressalvas `AUD-F-004`/`AUD-F-005`; `DatasetProfile` alocado ao M2) |
| **`RF1.3`** | Tipos físicos e semânticos (`ColumnDescriptor`, `ColumnSemanticType`) e contagem de ausentes | `src/experimental_ml/data/{types,validation,loader}.py` | `test_data_schemas.py` | **`PARCIALMENTE CONFORME`** (`AUD-F-008`: `np.float32(np.nan)` não contabilizado em `n_missing`) |
| **`RF1.7`** | Imutabilidade física da Etapa 1 e isolamento de memória | `src/experimental_ml/data/{types,loader,query}.py` | `test_data_schemas.py` | **`PARCIALMENTE CONFORME`** (`AUD-F-009`: *blacklist* estreita em colunas `object` permite objetos mutáveis) |
| **`RNF01`** | Determinismo e controle de sementes (`SeedSequence`) | `src/experimental_ml/core/{seeds,hashing}.py` | `test_core.py` + `integration_probe.py` (`INT-05`) | **`CONFORME`** |
| **`RNF02`** | Independência de domínio (zero termos florestais no código-fonte) | `src/experimental_ml/` | Inspeção textual completa em `src/` | **`CONFORME`** (`0` ocorrências de termos de domínio em `src/`) |
| **`RNF03`** | Execução 100% offline | `src/experimental_ml/` | Execução em sandbox sem rede | **`CONFORME`** |
| **`RNF04`** | Vetorização numérica e escalabilidade | `src/experimental_ml/{metrics,data}/` | `quality_and_perf_probe.py` (`QUAL-04`) | **`CONFORME`** (escalonamento linear verificado) |
| **`RNF05`** | Testabilidade e rigor matemático | `tests/` | `81 passed` + `12/12` mutações mortas | **`PARCIALMENTE CONFORME`** (ausência de testes de integração entre módulos `AUD-F-013`) |
| **`RNF06`** | Compatibilidade verificada empiricamente (`Python >= 3.10`) | `pyproject.toml` | `Python 3.12.15` verificado; `3.10`/`3.11` ausentes no host | **`NÃO VERIFICÁVEL`** para `3.10`/`3.11`; **`CONFORME`** para `3.12` |
| **`RNF07`** | CLI modularizada e API clara com diagnósticos instrutivos | `src/experimental_ml/cli/main.py`, `core/findings.py` | `test_smoke.py`, `test_core.py` | **`PARCIALMENTE CONFORME`** (exemplos do `README.md` com erro `AUD-F-001`) |

---

## 6. Auditoria dos Registros de Governança (`DOC-07`)

| Entrega | `spec.md` | `SPEC.md` | `tasks.md` | `proofs.md` | `verification.md` | `ACCEPTANCE.md` | `RESULTS.md` | Status de Governança |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `m1-1-setup-cli-smoke` | Sim | Sim | Sim | Sim | **Não (`AUD-F-012`)** | Sim | Sim | **Incompleto** (`validate_verification.py` falha) |
| `m1-2-core` | Sim | Sim | Sim | Sim | Sim | Sim | Sim | Completo |
| `m1-3-metrics` | Sim | Sim | Sim | Sim | Sim | Sim | Sim | Completo |
| `m1-4-datasets-schemas` | Sim | Sim | Sim | Sim | Sim | Sim | Sim | Completo |
