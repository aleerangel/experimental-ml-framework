# 3. Relatório de Integração entre Módulos (`03-integracao.md`)

**Dimensão:** B — Integração entre Módulos (`INT-01` a `INT-08`)  
**Sonda Executada:** [integration_probe.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/probes/integration_probe.py)

---

## 1. Fluxo Funcional Ponta a Ponta entre `data`, `metrics` e `core` (`INT-01`)

A sonda executou um fluxo real sem mocks combinando ingestão tabular, fatiamento por `ObservationId`, extração de vetores somente-leitura, cálculo de métricas, agregação multi-fold e ranqueamento de configurações:

1. `load_dataset(data, DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION))` $\rightarrow$ `DatasetBundle` com $N = 6$ observações (`obs_000000` .. `obs_000005`).
2. `slice_bundle_by_observation_ids(bundle, fold1_ids)` e `slice_bundle_by_observation_ids(bundle, fold2_ids)` $\rightarrow$ 2 sub-bundles de $N = 3$ observações cada.
3. `get_column_array(b_k, "y", copy=False)` $\rightarrow$ vetores `float64` com `flags.writeable == False`.
4. `compute_metric("rmse", y_k, y_pred_k)` $\rightarrow$ `MetricValue` válidos para dois modelos candidatos (`model_a` com erro $0.0$, `model_b` com erro $0.5$).
5. `aggregate_fold_metrics` $\rightarrow$ `AggregatedMetricValue` (`mean=0.0` vs. `mean=0.5`, `status=MetricStatus.VALID`).
6. `rank_configurations` $\rightarrow$ `[("model_a", rank=1, "VALID"), ("model_b", rank=2, "VALID")]`.

**Resultado (`INT-01`):** **`CONFORME`** — o fluxo ponta a ponta entre `core`, `data` e `metrics` opera de forma integrada. Contudo, constatou-se em `TEST-04` que a suíte oficial `tests/` não possuía nenhum teste combinando `data` e `metrics` (registrado como `AUD-F-013`).

---

## 2. Compatibilidade de Identificadores e Enumerações na Fronteira (`INT-02`)

* **`TaskType`:** O enum `TaskType` de `experimental_ml.core.enums` é compartilhado sem duplicação entre `DatasetSchemaSpec.task_type` (`data`) e `MetricSpec.supported_tasks` (`metrics`). A verificação `bundle.schema.task_type in METRICS_CATALOG["rmse"].supported_tasks` retorna `True`.
* **Degradação de tipo de `ObservationId` em `slice_bundle_by_observation_ids` (`AUD-F-006`):**
  * Em `load_dataset`, todos os elementos de `bundle.observation_ids` são instâncias de `ObservationId` (`initial_is_obs_id: true`).
  * Porém, quando `slice_bundle_by_observation_ids(bundle, ["obs_000001", "obs_000000"])` recebe strings Python comuns (`list[str]`) — exatamente como demonstrado no exemplo do `README.md` (linha 322) —, a igualdade `str == ObservationId` permite localizar os índices em `bundle_obs_index`, mas a linha [query.py:143](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/query.py#L143) faz `observation_ids=tuple(observation_ids)` sem converter os elementos para `ObservationId(oid)` (nem reter os objetos `ObservationId` originais de `bundle.observation_ids`).
  * Como resultado, `sliced.observation_ids` passa a conter objetos `str` puros (`sliced_with_plain_str_types: ["str", "str"]`, `isinstance(oid, ObservationId) == False`), violando a anotação de tipo `tuple[ObservationId, ...]` de `DatasetBundle`.

**Resultado (`INT-02`):** **`NÃO CONFORME`** (Achado `AUD-F-006`).

---

## 3. Consistência da Hierarquia de Exceções `ExperimentalMLError` (`INT-03`)

Foram testadas 9 chamadas inválidas nas fronteiras públicas de `core`, `metrics` e `data`:

| Chamada de Fronteira | Exceção Levantada | Herda de `ExperimentalMLError`? | Diagnóstico |
| :--- | :--- | :---: | :--- |
| `ObservationId("")` / `ObservationId("a\nb")` | `ValueError` | **Não** | `core.types` usa `ValueError` padrão |
| `derive_seeds(42, 0)` / `derive_seeds("bad", 2)` | `ValueError` / `TypeError` | **Não** | `core.seeds` usa `ValueError`/`TypeError` padrão |
| `config_hash(object())` | `TypeError` | **Não** | `core.hashing` usa `TypeError` padrão |
| `compute_metric("unknown", [1.0], [1.0])` | `ConfigurationError` | **Sim** | Conforme |
| `compute_metric("rmse", [], [])` | `DataIntegrityError` | **Sim** | Conforme |
| `DatasetSchemaSpec(target_col="", ...)` | `ConfigurationError` | **Sim** | Conforme |
| `load_dataset({"x": [2**63], "y": [1.0]}, schema)` | **`OverflowError`** | **Não** | **Defeito (`AUD-F-007`)** |

### Análise de Impacto na Fronteira de Erros
1. **Escape de `OverflowError` em `load_dataset` (`AUD-F-007`):** Em [loader.py:135](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/loader.py#L135), a conversão `np.array(int_vals, dtype=np.int64)` para inteiros Python fora do intervalo de 64 bits com sinal ($[-2^{63}, 2^{63}-1]$) levanta `OverflowError: Python int too large to convert to C long` sem capturá-lo e convertê-lo em `DataIntegrityError`.
2. **Exceções nativas em `core` (`AUD-F-003`):** Enquanto `metrics` e `data` padronizaram `ConfigurationError` e `DataIntegrityError` (subclasses de `ExperimentalMLError`), `core` (`types.py`, `seeds.py`, `hashing.py`) levanta `ValueError` e `TypeError` nativos. Caso o orquestrador futuro (`ErrorPolicy`) capture apenas `ExperimentalMLError` para erros de domínio, falhas em `ObservationId` ou `OverflowError` escaparão como erros não tratados.

**Resultado (`INT-03`):** **`NÃO CONFORME`** (Achado `AUD-F-007`).

---

## 4. Consistência de Hashing entre Formatos e Estruturas (`INT-04`, `INT-07`)

A sonda comparou os três hashes de `DatasetBundle` carregando exatamente o mesmo conteúdo tabular (`x=[1.0, 3.0], y=[2.0, 4.0]`) a partir de quatro fontes distintas:

| Fonte de Dados | `bundle.dataset_hash` | `bundle.raw_source_hash` | `bundle.schema_hash` |
| :--- | :--- | :--- | :--- |
| CSV com LF (`\n`) | `e5613b67...754113c` | `60601336...9d592fd1` | `879f2a6f...fcf753498` |
| CSV com CRLF (`\r\n`) | `e5613b67...754113c` | `9d3d59f6...219599f369` | `879f2a6f...fcf753498` |
| TSV com LF (`\t`) | `e5613b67...754113c` | `b890...` (específico TSV) | `879f2a6f...fcf753498` |
| `dict` em memória `{"x": ..., "y": ...}` | `e5613b67...754113c` | `e5613b67...754113c` | `879f2a6f...fcf753498` |
| `dict` em memória `{"y": ..., "x": ...}` | **`bc3a2ae8...0d9ec22f8`** | `bc3a2ae8...0d9ec22f8` | `879f2a6f...fcf753498` |

### Constatações Técnicas (`INT-04`, `INT-07`)
1. **Invariância entre CSV (LF/CRLF), TSV e `dict` com mesma ordem de colunas:** Confirmada (`e5613b677476b4dec1adecee6b4b747695fbc37fc71b62c6e8865ceb0754113c`).
2. **Sensibilidade à ordem das chaves do dicionário (`dict_xy != dict_yx`):** `bundle.dataset_hash` muda quando a ordem das colunas muda, o que está de acordo com a especificação aprovada do M1.4 (`spec.md` Goal 5: *"Ordem das Colunas: Faz parte da identidade estrutural e canônica do dataset"*), mas **contradiz** o texto de `ARQUITETURA_E_CONTRATOS.md` (linhas 250 e 743) e `README.md` (linha 103), que afirmam que `dataset_hash` é *"invariante a quebras de linha e ordenação de chaves"* (registrado como `AUD-F-010`).
3. **Relação entre `bundle.dataset_hash`, `bundle.raw_source_hash` e `core.dataset_hash` (`INT-07`):**
   * `bundle.dataset_hash == core.dataset_hash(bundle.columns, bundle.schema)` (`True`).
   * `bundle.raw_source_hash == core.dataset_hash(csv_path, bundle.schema)` (`True`), que combina os bytes brutos do arquivo em disco com `config_hash(schema)`.
   * **Omissão de `observation_ids` em `dataset_hash` (`AUD-F-005`):** Ao fatiar `bundle_disk` para manter apenas a segunda linha (`ObservationId("obs_000001")`, valores `x=[3.0], y=[4.0]`), o `sliced.dataset_hash` resultante é **idêntico** ao de um dataset novo de 1 linha (`ObservationId("obs_000000")`, valores `x=[3.0], y=[4.0]`), apesar de `sliced.observation_ids == ('obs_000001',)` diferir de `fresh_1row.observation_ids == ('obs_000000',)`. Isso ocorre porque `core.dataset_hash(bundle.columns, bundle.schema)` não inclui `bundle.observation_ids` no cálculo do hash, contrariando `ARQUITETURA_E_CONTRATOS.md` (linhas 210 e 707).

---

## 5. Determinismo Inter-Processos sob `PYTHONHASHSEED` Distintos (`INT-05`)

A sonda executou subprocessos Python isolados com `PYTHONHASHSEED=0` e `PYTHONHASHSEED=12345`, computando `config_hash` (com `dict` e `set`), `bundle.dataset_hash`, `bundle.raw_source_hash`, `bundle.schema_hash`, `sliced.dataset_hash`, `derive_seeds` e `spawn_child_seeds`.

* **Resultado (`INT-05`):** **`CONFORME`** (`identical: true` em todos os hashes e sequências de sementes).

---

## 6. Preservação de Imutabilidade na Fronteira `data` $\rightarrow$ `metrics` (`INT-06`)

As views somente-leitura retornadas por `get_column_array(bundle, col, copy=False)` foram passadas diretamente como `y_true` e `y_pred`/`y_score`/`y_prob` para **todas as 15 métricas** de `METRICS_CATALOG`:
* Nenhuma métrica tentou modificar os arrays de entrada in-place (`any_writeable_after: false`).
* O digest SHA-256 dos bytes de todas as colunas permaneceu 100% inalterado antes e depois da execução das 15 métricas (`digests_unchanged: true`).

* **Resultado (`INT-06`):** **`CONFORME`**.

---

## 7. Compatibilidade de Tipos Físicos (`int64`, `bool`, `object`) com `metrics` (`INT-08`)

1. **Colunas `int64` e `bool` em métricas de regressão e classificação numérica:**
   * `int64` em regressão (`rmse`): convertido de forma transparente para `float64` em `validate_numeric_arrays` (`status: VALID`).
   * `bool` em classificação (`accuracy`, `balanced_accuracy`, `precision`, `recall`, `f1`, `roc_auc`, `log_loss`): em Python/NumPy, `False == 0` e `True == 1`, de modo que `pos_label=1` (padrão de `precision`, `recall`, `f1`) casa com `True` em arrays `bool` (`status: VALID`).
2. **Rótulos textuais (`dtype=object`, ex.: `["no", "yes"]`) em `precision`, `recall` e `f1` com `average="binary"` (`AUD-F-011`):**
   * `load_dataset` permite colunas-alvo categóricas de texto (`dtype=object`, ex.: `["no", "yes"]`) em `TaskType.BINARY_CLASSIFICATION`.
   * Enquanto `accuracy`, `balanced_accuracy`, `roc_auc` e `log_loss` extraem dinamicamente as classes presentes via `_extract_classes(yt, yp)` (onde `classes[1]` é a classe positiva no caso binário), as funções `precision`, `recall` e `f1` em modo `average="binary"` utilizam `pos_label: Any = 1` fixo como padrão ([classification.py:185](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/metrics/classification.py#L185)).
   * Quando chamadas via `compute_metric("precision", y_str, y_str)` sem informar `pos_label="yes"`, `(yt == 1)` e `(yp == 1)` avaliam tudo como `False`, resultando silenciosamente em `tp + fp == 0` $\rightarrow$ `MetricStatus.UNDEFINED_NAN` (`W_METRIC_ZERO_PREDICTIONS`), mesmo para uma predição binária perfeita!
   * Esse comportamento assimétrico entre `{accuracy, balanced_accuracy, roc_auc, log_loss}` (que funcionam com quaisquer rótulos binários) e `{precision, recall, f1}` (que exigem rótulos `{0, 1}`/`{False, True}` ou passagem explícita de `pos_label`) representa um risco de integração para os estágios de avaliação automatizada (M4/M5).

* **Resultado (`INT-08`):** **`CONFORME COM RESSALVA`** (Registrado como risco de integração `AUD-F-011`).
