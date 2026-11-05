# 4. Relatório de Qualidade da Implementação e Estratégia de Testes (`04-qualidade-e-testes.md`)

**Dimensões:** C — Qualidade da Implementação (`QUAL-01` a `QUAL-06`) e D — Estratégia de Testes e Confiabilidade do TLC (`TEST-01` a `TEST-08`)  
**Sondas Executadas:** [quality_and_perf_probe.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/probes/quality_and_perf_probe.py) | [testing_and_tlc_probe.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/probes/testing_and_tlc_probe.py)

---

## Parte I — Dimensão C: Qualidade da Implementação (`QUAL-01` a `QUAL-06`)

### 1. Varredura AST de Higiene e Estado (`QUAL-01`)

A inspeção AST automatizada sobre todos os 21 arquivos em `src/experimental_ml/` produziu os seguintes resultados:

* **`except:` nu (sem tipo de exceção):** `0` ocorrências (`bare_excepts: []`).
* **Argumentos padrão mutáveis (`list`, `dict`, `set`):** `0` ocorrências (`mutable_defaults: []`).
* **Exceções capturadas com `continue` (`swallowed_excepts`):** `1` ocorrência intencional em [parsing.py:101](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/parsing.py#L101) (`except DataIntegrityError: continue` dentro do loop de candidatos do sniffer de delimitadores `detect_delimiter`, que ao final levanta `DataIntegrityError` se zero ou $>1$ delimitadores forem consistentes).
* **Uso de `assert` em tempo de execução (`runtime_asserts`):** `1` ocorrência em [loader.py:317](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/loader.py#L317) (`assert source_path_str is not None` no ramo `if is_file_source:`, usado para estreitamento de tipo estático; sob `python -O`, a asserção é removida, mas `source_path_str` já é garantidamente `str` quando `is_file_source == True`).
* **Coleções de nível de módulo não congeladas (`mutable_globals`):** `2` ocorrências internas:
  * `_ALLOWED_AGG_SCOPES = {...}` (`set` mutável em [aggregation.py:21](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/metrics/aggregation.py#L21), recomendável converter para `frozenset`).
  * `_SPECS: dict[str, MetricSpec] = {...}` (dicionário interno em [catalog.py:31](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/metrics/catalog.py#L31) que respalda `METRICS_CATALOG = MappingProxyType(_SPECS)`).

**Resultado (`QUAL-01`):** **`CONFORME COM RESSALVA`** (Registrada melhoria de higiene `AUD-F-015` para `frozenset` e substituição de `assert` por verificação explícita).

---

### 2. Anotações de Tipo em Interfaces Públicas (`QUAL-02`)

* **Total de funções públicas inspecionadas via AST:** `41` funções públicas em `src/experimental_ml/`.
* **Funções públicas sem anotação de parâmetro ou de retorno:** `0` (`missing_annotations: []`).
* **Divergência entre tipo anotado e valor em tempo de execução:** Em `slice_bundle_by_observation_ids` ([query.py:143](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/query.py#L143)), a assinatura declara `observation_ids: Sequence[ObservationId]` e `DatasetBundle.observation_ids: tuple[ObservationId, ...]`, mas quando o chamador passa `Sequence[str]` (como no `README.md`), o `DatasetBundle` resultante armazena `tuple[str, ...]` sem instanciar `ObservationId` (`AUD-F-006`).

**Resultado (`QUAL-02`):** **`NÃO CONFORME`** (Achado `AUD-F-006`).

---

### 3. Sonda de Casos Extremos e Fronteiras Numéricas/Textuais (`QUAL-03`)

A sonda executou 6 testes adversariais de casos extremos, revelando quatro defeitos/fragilidades:

| Caso Extremo Testado | Comportamento Esperado | Comportamento Observado | Achado |
| :--- | :--- | :--- | :---: |
| Colisão de nomes de colunas em `core.dataset_hash`: `{"ab": [1.0], "c": [2.0]}` vs. `{"a": [1.0], "bc": [2.0]}` | Hashes distintos | **Hashes idênticos** (`57aaec7f...6532f93e`) — `hashing.py:209` concatena `col_name.encode("utf-8")` sem delimitador nem tamanho | **`AUD-F-004` (`ALTO`)** |
| `np.float32(np.nan)` em `ndarray` 2D carregado por `load_dataset` | `ColumnDescriptor.n_missing == 1` | **`n_missing == 0`** (enquanto `np.isnan(bundle.columns["col_0"]).sum() == 1`), pois `_is_missing_token` testa `isinstance(v, float)` e `np.float32` não herda de `float` | **`AUD-F-008` (`ALTO`)** |
| Inteiro $\ge 2^{63}$ (`2**63`) em `load_dataset` | Levantar `DataIntegrityError` | Levanta **`OverflowError`** não tratado (`Python int too large to convert to C long`) em `loader.py:135` | **`AUD-F-007` (`MODERADO`)** |
| Byte nulo `\x00` e Unicode NFD em `ObservationId` (`ObservationId("obs_\x00_1")`, `ObservationId("obs_e\u0301")`) | Rejeitar controles ASCII `< 32` e normalizar NFC | Aceita `\x00` (`domain_identifier_accepts_null_byte: true`) e não normaliza NFD $\rightarrow$ NFC (`domain_identifier_normalizes_nfc: false`) | **`AUD-F-003` (`MODERADO`)** |
| Chaves duplicadas após normalização NFC em `dict` (`{"e\u0301": ..., "\u00e9": ...}`) | Levantar `DataIntegrityError` | Levanta `DataIntegrityError` (detectado por `len(parsed_col_names) != len(set)`), porém `raw_columns_dict` sobrescreve os valores antes da validação | Conforme |

**Resultado (`QUAL-03`):** **`NÃO CONFORME`** (Achados `AUD-F-004`, `AUD-F-008`, `AUD-F-007`, `AUD-F-003`).

---

### 4. Desempenho e Escalabilidade Empírica (`QUAL-04`)

O benchmark avaliou o tempo de execução de `load_dataset` (em memória e via arquivo CSV) e `dataset_hash` para $N = 10.000$ vs. $N = 100.000$ linhas $\times 20$ colunas numéricas:

| Operação | $N = 10.000 \times 20$ | $N = 100.000 \times 20$ | Razão $T(100\text{k}) / T(10\text{k})$ | Complexidade Empírica |
| :--- | :---: | :---: | :---: | :---: |
| `load_dataset` (em memória `dict`) | `0.0892 s` | `0.9143 s` | **`10.25x`** | $\mathcal{O}(N \cdot M)$ linear |
| `dataset_hash` (em memória) | `0.0009 s` | `0.0108 s` | **`12.00x`** | $\mathcal{O}(N \cdot M)$ linear |
| `load_dataset` (arquivo CSV em disco) | `0.1871 s` | `2.3985 s` | **`12.82x`** | $\mathcal{O}(N \cdot M)$ linear |

* **Observação de eficiência:** Embora o escalonamento seja estritamente linear ($\sim 10\text{x}$–$12.8\text{x}$ para aumento de $10\text{x}$ no volume), `_coerce_column_values` em [loader.py:58-146](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/loader.py#L58-L146) converte arrays NumPy já tipados em listas Python (`list(source[orig_k])`) e itera elemento a elemento em Python antes de reconstruir o `np.ndarray`. Para matrizes de milhões de linhas em marcos futuros, um caminho vetorizado direto para entradas `np.ndarray` evitaria o overhead de *boxing/unboxing* de escalares Python.

**Resultado (`QUAL-04`):** **`CONFORME`** (escalonamento linear verificado).

---

### 5. Sonda Adversarial de Imutabilidade (`QUAL-05`)

Foram executados 5 ataques diretos de mutação sobre as estruturas imutáveis do Marco M1:

1. **Reativação de escrita em coluna numérica (`arr.setflags(write=True)`):** **Bloqueado** (`ValueError: cannot set WRITEABLE flag to True of this array`), pois o array é respaldado por buffer `bytes` imutável via `np.frombuffer`.
2. **Inserção/alteração de chave em `bundle.columns` ou `bundle.descriptors`:** **Bloqueado** (`TypeError: 'mappingproxy' object does not support item assignment`).
3. **Reativação de escrita e objetos mutáveis em coluna `dtype=object` (`AUD-F-009`):**
   * **Ataque 3a (Bypass da blacklist de tipos mutáveis):** Em [loader.py:153](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/loader.py#L153), a validação usa uma *blacklist* restrita `isinstance(v, (list, dict, set, bytearray))` em vez de uma *whitelist* de escalares imutáveis (`str`, `int`, `float`, `bool`, `bytes`, `None`). Ao passar instâncias de `types.SimpleNamespace(val="initial_1")` (ou qualquer objeto mutável customizado), `load_dataset` aceita a coluna e permite mutar `ns1.val = "mutated_after_load"` in-place dentro do `DatasetBundle` sem alterar `bundle.dataset_hash` (`object_col_mutable_container_bypass: true`)!
   * **Ataque 3b (`setflags(write=True)` em coluna `object`):** Diferentemente das colunas numéricas, `arr = np.empty(n, dtype=object)` possui memória própria (`OWNDATA = True`), de modo que `get_column_array(bundle_obj, "cat", copy=False).setflags(write=True)` **tem sucesso** (`object_col_setflags_write_true_succeeded: true`). Nota: este último ponto foi documentado como limitação conhecida da C-API do NumPy para `dtype=object` na especificação de M1.4 (`DATA-10`), mas o bypass da *blacklist* (Ataque 3a) é um defeito de validação facilmente corrigível via *whitelist*.
4. **Injeção de atributo mutável em `DomainIdentifier` (`AUD-F-003`):** `oid.injected_attr = ["mutable_state"]` **tem sucesso** (`domain_identifier_has_mutable_dict: true`) por ausência de `__slots__ = ()` em `DomainIdentifier` e suas subclasses.

**Resultado (`QUAL-05`):** **`NÃO CONFORME`** (Achados `AUD-F-009` e `AUD-F-003`).

---

### 6. Compatibilidade com Interpretadores Python no Host (`QUAL-06`)

* `python3.12` (`/usr/bin/python3.12` — `Python 3.12.15`): **Verificado empiricamente** via `.venv` (`81 passed`).
* `python3.14` (`/usr/bin/python3.14` — `Python 3.14.8`): Instalado no sistema operacional sem `numpy`/`pytest` (uso restrito à stdlib).
* `python3.10` e `python3.11`: **`NÃO VERIFICÁVEL`** neste host (binários ausentes no sistema operacional), conforme já ressalvado em `ESPECIFICACAO_REQUISITOS.md` (`RNF06`).

---

## Parte II — Dimensão D: Estratégia de Testes e Confiabilidade do TLC (`TEST-01` a `TEST-08`)

### 7. Cobertura de Linhas por Arquivo (`TEST-01`, `TEST-02`)

A execução de `pytest tests/` sob rastreamento de linhas (`trace.Trace`) registrou **cobertura global de `83.7%`** (`2.240 / 2.676` linhas executáveis):

| Arquivo (`src/experimental_ml/`) | Linhas Executáveis | Linhas Cobertas | Cobertura (%) | Principais Caminhos Não Cobertos |
| :--- | :---: | :---: | :---: | :--- |
| `metrics/catalog.py` | 207 | 205 | `99.0%` | Ramo `task` já como `TaskType` enum em `list_metrics` |
| `core/findings.py` | 35 | 34 | `97.1%` | Completo |
| `core/types.py` | 21 | 20 | `95.2%` | Completo |
| `core/enums.py` | 36 | 34 | `94.4%` | `StrEnum.__str__` |
| `metrics/aggregation.py` | 193 | 180 | `93.3%` | Guardas defensivas de tipos inválidos |
| `data/query.py` | 87 | 81 | `93.1%` | Fatiamento de coluna `dtype=object` com `None`/`NaN` (`L103-106`) |
| `core/hashing.py` | 166 | 149 | `89.8%` | Referência circular (`L75`), `DataFrame.to_numpy` (`L160`), `ndarray` 2D direto em `_hash_in_memory_tabular` (`L205-210`) |
| `data/schema.py` | 108 | 97 | `89.8%` | Guardas de tipos inválidos em `DatasetSchemaSpec` (`L75-80`) |
| `data/validation.py` | 137 | 122 | `89.1%` | Defaults semânticos para `time_col`, `group_col` e classificação `bool` (`L94-107`) |
| `metrics/types.py` | 118 | 105 | `89.0%` | Validações `__post_init__` de `MetricValue` e `AggregatedMetricValue` |
| `data/parsing.py` | 157 | 137 | `87.3%` | Delimitador inválido manual, erros de I/O de leitura |
| `cli/main.py` | 28 | 23 | `82.1%` | Chamada direta de `main(["--version"])` em processo |
| `data/loader.py` | 233 | 189 | `81.1%` | Coluna booleana com nulos (`L94-103`), `DataFrame` duck-typed (`L221-224`) |
| `metrics/validation.py` | 54 | 43 | `79.6%` | Conversão `TypeError` e squeeze `(n, 1)` |
| `core/seeds.py` | 23 | 18 | `78.3%` | Rejeição de `bool` como semente (`isinstance(..., bool)`) |
| `metrics/regression.py` | 360 | 282 | `78.3%` | Ramos defensivos de overflow pós-cálculo (`not math.isfinite(val)`) |
| `data/types.py` | 70 | 53 | `75.7%` | Guardas `__post_init__` de `ColumnDescriptor` e `DatasetBundle` |
| `metrics/classification.py` | 615 | 445 | `72.4%` | Ramos multiclasse `weighted` com suporte zero e validações de forma 2D inválidas |

---

### 8. Ensaio de Mutação Controlada em Cópia Efêmera (`TEST-03`)

Foram injetadas **12 mutações semânticas** em `/tmp/m1-audit-mut/` (4 em `core`, 4 em `metrics`, 3 em `data`, 1 em `cli`), executando-se a suíte completa de 81 testes contra cada mutante e removendo `/tmp/m1-audit-mut/` ao final (`tmp_dir_cleaned: true`):

| ID | Módulo | Arquivo Alvo | Mutação Semântica Aplicada | Status |
| :--- | :--- | :--- | :--- | :---: |
| `MUT-01` | `core` | `core/hashing.py` | Desativar normalização `-0.0 -> 0.0` em `_canonical_transform` | **`KILLED`** |
| `MUT-02` | `core` | `core/hashing.py` | Desativar normalização Unicode NFC em `_canonical_transform` | **`KILLED`** |
| `MUT-03` | `core` | `core/seeds.py` | Retornar tupla constante `42` em `derive_seeds` | **`KILLED`** |
| `MUT-04` | `core` | `core/types.py` | Permitir string vazia em `DomainIdentifier.__new__` | **`KILLED`** |
| `MUT-05` | `metrics` | `metrics/regression.py` | Inverter sinal do MBE (`yt - yp` em vez de `yp - yt`) | **`KILLED`** |
| `MUT-06` | `metrics` | `metrics/regression.py` | Retornar `VALID` ($0.0$) em vez de `UNDEFINED_NAN` quando $SS_{\text{tot}} = 0$ em `r2` | **`KILLED`** |
| `MUT-07` | `metrics` | `metrics/aggregation.py` | Tratar candidato `UNDEFINED_NAN` como superior em `is_better` | **`KILLED`** |
| `MUT-08` | `metrics` | `metrics/catalog.py` | Alterar `compare_by_abs=True` para `False` em `mbe` | **`KILLED`** |
| `MUT-09` | `data` | `data/loader.py` | Substituir `np.frombuffer` por array comum com `writeable=False` | **`KILLED`** |
| `MUT-10` | `data` | `data/query.py` | Ordenar `observation_ids` em `slice_bundle_by_observation_ids` | **`KILLED`** |
| `MUT-11` | `data` | `data/validation.py` | Permitir `ObservationId` duplicados na coluna identificadora | **`KILLED`** |
| `MUT-12` | `cli` | `cli/main.py` | Alterar `prog="expml"` no parser da CLI | **`KILLED`** |

* **Escore de mutação sobre invariantes especificados:** **`100.0%` (`12/12 KILLED`)**. Os testes existentes são altamente eficazes para proteger os contratos que foram explicitamente testados; as falhas encontradas na auditoria (`AUD-F-004`, `AUD-F-006`, `AUD-F-008`, `AUD-F-009`) residem em interações entre módulos e casos de contorno ausentes da suíte.

---

### 9. Testes de Integração, Isolamento e Ordem de Execução (`TEST-04`, `TEST-05`)

* **Ausência de testes de integração entre `data` e `metrics` (`TEST-04` / `AUD-F-013`):**
  * Nenhum dos 4 arquivos em `tests/` importa simultaneamente `experimental_ml.data` e `experimental_ml.metrics` (`count_combining_data_and_metrics: 0`). Não existe diretório `tests/integration/`.
* **Independência de ordem e isolamento (`TEST-05`):**
  * Ordem direta (`test_smoke` $\rightarrow$ `test_core` $\rightarrow$ `test_metrics` $\rightarrow$ `test_data_schemas`): `81 passed in 0.27s` (`exit 0`).
  * Ordem reversa (`test_data_schemas` $\rightarrow$ `test_metrics` $\rightarrow$ `test_core` $\rightarrow$ `test_smoke`): `81 passed in 0.22s` (`exit 0`).

---

### 10. Auditoria dos Validadores e Mecanismos do TLC (`TEST-06`, `TEST-07`, `TEST-08`)

A sonda executou `validate_spec.py --strict`, `validate_tasks.py --strict` e `validate_verification.py --strict` sobre os 4 marcos concluídos (`m1-1` a `m1-4`), além de `check_proofs.py` em um clone efêmero `/tmp/m1-audit-clone/`:

| Marco | `validate_spec.py --strict` | `validate_tasks.py --strict` | `validate_verification.py --strict` (no repo atual) | `check_proofs.py` + `validate_verification.py` (no clone com proofs atualizados) |
| :--- | :---: | :---: | :---: | :---: |
| `m1-1-setup-cli-smoke` | `0 errors, 0 warnings` (exit `0`) | `0 errors, 3 warnings` (`Tests: none` em T1–T3, exit `1` sob `--strict`) | **FALHA (exit `1`)**: `no verification.md` | **FALHA (exit `1`)**: `no verification.md` (apesar de `12 pass, 0 fail` em `check_proofs.py`) |
| `m1-2-core` | `0 errors, 0 warnings` (exit `0`) | `0 errors, 2 warnings` (`Tests: none` em T1, T7, exit `1` sob `--strict`) | **FALHA (exit `1`)**: `proofs.md was written at c0ca71c and HEAD is 64bcdce` | **PASSA (exit `0`)**: `18 pass, 0 fail` e `0 errors` |
| `m1-3-metrics` | `0 errors, 0 warnings` (exit `0`) | `0 errors, 0 warnings` (exit `0`) | **FALHA (exit `1`)**: `proofs.md was written at 1b649a6 and HEAD is 64bcdce` | **PASSA (exit `0`)**: `22 pass, 0 fail` e `0 errors` |
| `m1-4-datasets-schemas` | `0 errors, 0 warnings` (exit `0`) | `0 errors, 0 warnings` (exit `0`) | **FALHA (exit `1`)**: `proofs.md was written at 12073c7 and HEAD is 64bcdce` | **PASSA (exit `0`)**: `29 pass, 0 fail` e `0 errors` |

### Achados de Governança e Confiabilidade dos Validadores TLC (`TEST-06..08`)
1. **Ausência de `verification.md` em `m1-1-setup-cli-smoke` (`AUD-F-012`):** O diretório `.specs/features/m1-1-setup-cli-smoke/` possui `spec.md`, `SPEC.md`, `tasks.md`, `proofs.md`, `ACCEPTANCE.md` e `RESULTS.md`, mas **não possui `verification.md`**. Por isso, `check_commit.py` emite em todo commit o aviso `After the last commit of m1-1-setup-cli-smoke the feature is not done`, e `validate_verification.py m1-1-setup-cli-smoke` falha com código de saída `1`.
2. **Acoplamento de `validate_verification.py` ao `HEAD` volátil do repositório (`AUD-F-014`):** Em [validate_verification.py:288](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.agent/skills/tlc-spec-driven/scripts/validate_verification.py#L288), o validador compara o `**HEAD**` gravado em `proofs.md` com `git rev-parse --short HEAD` do repositório atual. Assim que qualquer commit subsequente é realizado (como o próprio commit que adiciona `verification.md`, o merge do PR ou o avanço para o marco seguinte), `validate_verification.py` passa a falhar retroativamente para todas as features concluídas (`proofs.md was written at <old> and HEAD is <current>`), embora no clone efêmero todas as 81 provas de `m1-2`, `m1-3` e `m1-4` continuem passando 100%.
3. **Limitação estrutural de `check_proofs.py` (`sees`)**: `check_proofs.py` verifica apenas se as palavras após `|` aparecem na saída do comando pytest (`PASSED`) e se o código de saída é `0`; ele não analisa a AST do teste para confirmar se o teste realmente exercita o requisito sem o julgamento complementar do agente Verifier.

