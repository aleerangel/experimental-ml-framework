# 6. Registro Consolidado de Achados e Riscos (`06-achados.md`)

**Escopo:** Consolidação de todos os achados identificados nas Dimensões A a F da Auditoria Geral de Integridade do Marco M1 (`M1.1` a `M1.4`).  
**Categorias de Classificação:** `DEFEITO` | `RISCO` | `MELHORIA` | `LIMITAÇÃO DOCUMENTADA`  
**Níveis de Severidade:** `CRÍTICO` | `ALTO` | `MODERADO` | `BAIXO`

---

## 1. Resumo Quantitativo por Severidade e Categoria

| Severidade \ Categoria | `DEFEITO` | `RISCO` | `MELHORIA` | `LIMITAÇÃO DOCUMENTADA` | **Total** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`CRÍTICO`** | `0` | `0` | `0` | `0` | **`0`** |
| **`ALTO`** | **`4`** (`AUD-F-001`, `AUD-F-004`, `AUD-F-006`, `AUD-F-008`) | **`2`** (`AUD-F-005`, `AUD-F-009`) | `0` | `0` | **`6`** |
| **`MODERADO`** | **`2`** (`AUD-F-002`, `AUD-F-007`) | **`4`** (`AUD-F-003`, `AUD-F-010`, `AUD-F-011`, `AUD-F-012`) | **`1`** (`AUD-F-013`) | `0` | **`7`** |
| **`BAIXO`** | `0` | `0` | **`2`** (`AUD-F-014`, `AUD-F-015`) | **`1`** (`AUD-F-016`) | **`3`** |
| **Total** | **`6`** | **`6`** | **`3`** | **`1`** | **`16`** |

---

## 2. Detalhamento Completo dos Achados (`AUD-F-001` a `AUD-F-016`)

### `AUD-F-001` — Blocos de exemplo em Python no `README.md` falham em tempo de execução (`metrics` e `data`)
* **Dimensão:** `DOC` (`DOC-01`, `ARCH-07`)
* **Categoria:** `DEFEITO`
* **Severidade:** `ALTO`
* **Localização:** [README.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/README.md#L280-L315)
* **Evidência Reprodutível:**
  * Comando: `.venv/bin/python .specs/features/m1-integrity-review/probes/docs_and_traceability_probe.py`
  * No Bloco 3 (`README.md:283`): `is_better(cand_a=rmse_val, cand_b=None, direction=spec.direction)` levanta `ConfigurationError: Unsupported candidate type <class 'NoneType'>`, e a linha 280 cita o atributo inexistente `spec.tolerance_rtol` (o atributo real em `MetricSpec` é `spec.rtol`).
  * No Bloco 4 (`README.md:303-308`): `DatasetSchemaSpec(..., semantic_types={...})` levanta `TypeError: DatasetSchemaSpec.__init__() got an unexpected keyword argument 'semantic_types'` (o nome real do campo é `column_semantic_types`), e a linha 314 cita `bundle.n_features` (o atributo real em `DatasetBundle` é `bundle.feature_cols`).
* **Impacto:** O ponto de entrada oficial do repositório instrui consumidores a invocarem assinaturas e atributos que quebram imediatamente ao serem copiados e executados.
* **Justificativa da Severidade:** `ALTO` — inviabiliza o uso direto da documentação pública recém-atualizada dos módulos `metrics` e `data`.
* **Recomendação:** Corrigir os blocos 3 e 4 do `README.md` antes do início do M2 e incluir um teste automatizado que execute todos os blocos `python` do `README.md`.

---

### `AUD-F-002` — Árvore de diretórios do `README.md` e contagem em `ETAPA_ATUAL_ENGENHARIA.md` divergem dos arquivos reais
* **Dimensão:** `DOC` (`DOC-02`, `DOC-03`)
* **Categoria:** `DEFEITO`
* **Severidade:** `MODERADO`
* **Localização:** [README.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/README.md#L104-L126) e [ETAPA_ATUAL_ENGENHARIA.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/engenharia_software/ETAPA_ATUAL_ENGENHARIA.md#L87)
* **Evidência Reprodutível:**
  * `README.md:122` e `125` listam `src/experimental_ml/core/exceptions.py` e `src/experimental_ml/core/identifiers.py`, que não existem em disco, omitindo `src/experimental_ml/core/types.py`.
  * `README.md:104` afirma que `.specs/features/m1-1-setup-cli-smoke/` possui `verification.md`, que não existe em disco.
  * `ETAPA_ATUAL_ENGENHARIA.md:87` afirma que `experimental_ml.data` re-exporta 7 símbolos em `__all__`, quando na verdade exporta 13 símbolos.
* **Impacto:** Induz desenvolvedores e auditores a procurarem módulos inexistentes em `core/` e subestima a superfície pública de `data`.
* **Justificativa da Severidade:** `MODERADO` — erro documental factual sem falha em tempo de execução do código, mas que afeta a navegabilidade arquitetural.
* **Recomendação:** Atualizar a árvore em `README.md` (`core/types.py`, `core/findings.py`) e a contagem em `ETAPA_ATUAL_ENGENHARIA.md` (13 símbolos em `data/__init__.py`).

---

### `AUD-F-003` — `DomainIdentifier` e suas 8 subclasses não declaram `__slots__ = ()`, aceitam controles ASCII `< 32` e não normalizam NFC
* **Dimensão:** `ARCH` / `QUAL` (`ARCH-04`, `QUAL-03`, `QUAL-05`)
* **Categoria:** `RISCO`
* **Severidade:** `MODERADO`
* **Localização:** [types.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/core/types.py#L6-L50)
* **Evidência Reprodutível:**
  * Comando: `.venv/bin/python -c "from experimental_ml.core import ObservationId; o = ObservationId('obs_\x00_1'); o.mut = [1]; print(hasattr(o, '__dict__'), o.mut)"` $\rightarrow$ `True [1]`.
  * `ObservationId("obs_e\u0301") == ObservationId("obs_\u00e9")` $\rightarrow$ `False` quando instanciado diretamente via `core.types`.
* **Impacto:** Permite anexar estado mutável arbitrário a qualquer identificador de domínio (violando o ADR-008), aumenta o consumo de memória por instância em vetores de `observation_ids` e permite discrepância entre `ObservationId` criado via `assign_or_validate_observation_ids` (que faz NFC) e `ObservationId` instanciado diretamente pelo consumidor.
* **Justificativa da Severidade:** `MODERADO` — não corrompe fluxos que não atribuem atributos dinâmicos, mas enfraquece a garantia estrutural de imutabilidade do Nível 0 (`core`).
* **Recomendação:** Adicionar `__slots__ = ()` em `DomainIdentifier` e em todas as 8 subclasses, aplicar `unicodedata.normalize("NFC", stripped)` em `DomainIdentifier.__new__` e rejeitar qualquer caractere de controle ASCII (`ord(c) < 32` ou `ord(c) == 127`).

---

### `AUD-F-004` — Colisão de hash por concatenação sem delimitador de nomes de colunas em `_hash_in_memory_tabular`
* **Dimensão:** `ARCH` / `QUAL` (`ARCH-05`, `QUAL-03`)
* **Categoria:** `DEFEITO`
* **Severidade:** `ALTO`
* **Localização:** [hashing.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/core/hashing.py#L205-L218)
* **Evidência Reprodutível:**
  * Comando:
    ```bash
    .venv/bin/python -c "from experimental_ml.core import dataset_hash; print(dataset_hash({'ab': [1.0], 'c': [2.0]}) == dataset_hash({'a': [1.0], 'bc': [2.0]}))"
    ```
  * Saída: `True` (ambos produzem `284795...` ou `57aaec7f7b2eb3672df197fd56a0c3433399664a01e320c92a2caceb6532f93e` com o mesmo schema).
  * Causa raiz: as linhas 209 e 216 fazem `for col_name in col_names: hasher.update(col_name.encode("utf-8"))` sem gravar a quantidade de colunas nem o comprimento (`struct.pack("<Q", len(b))`) de cada nome de coluna antes dos bytes UTF-8.
* **Impacto:** Dois datasets com esquemas de colunas distintos (`["ab", "c"]` vs. `["a", "bc"]`) e mesmos valores nas posições correspondentes produzem exatamente o mesmo `dataset_hash`, violando a exigência de canonicidade e resistência a colisões estruturais do `ADR-007` e `CA-GER-02`.
* **Justificativa da Severidade:** `ALTO` — defeito algorítmico direto na função central de integridade `core.dataset_hash` usada por `DatasetBundle` e pelos futuros módulos do M2 (`PreparationPlan`, `SanitizedDatasetView`, `PartitionPlan`).
* **Recomendação:** Em `_hash_in_memory_tabular`, preceder a lista de nomes de colunas com `struct.pack("<Q", len(col_names))` e preceder cada nome de coluna com `struct.pack("<Q", len(col_bytes))` (exatamente como já é feito para strings de dados na linha 194).

---

### `AUD-F-005` — `bundle.dataset_hash` não incorpora `observation_ids`, gerando mesmo hash para subconjuntos com IDs distintos
* **Dimensão:** `INT` / `ARCH` (`INT-07`, `ARCH-07`)
* **Categoria:** `RISCO`
* **Severidade:** `ALTO`
* **Localização:** [loader.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/loader.py#L323) e [query.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/query.py#L130)
* **Evidência Reprodutível:**
  * Comando:
    ```bash
    .venv/bin/python -c "from experimental_ml.core import TaskType, ObservationId; from experimental_ml.data import DatasetSchemaSpec, load_dataset, slice_bundle_by_observation_ids; s = DatasetSchemaSpec(target_col='y', task_type=TaskType.REGRESSION); b = load_dataset({'x': [1.0, 3.0], 'y': [2.0, 4.0]}, s); b_slice = slice_bundle_by_observation_ids(b, [ObservationId('obs_000001')]); b_fresh = load_dataset({'x': [3.0], 'y': [4.0]}, s); print(b_slice.observation_ids, b_fresh.observation_ids, b_slice.dataset_hash == b_fresh.dataset_hash)"
    ```
  * Saída: `('obs_000001',) ('obs_000000',) True`.
* **Impacto:** No Marco M2, `SanitizedDatasetView` (que remove linhas com `target` nulo preservando os `observation_ids` originais) e `PartitionPlan` (cujo `partition_plan_id` e validação de pareamento dependem do vínculo entre `dataset_hash` e `observation_ids`, conforme `ARQUITETURA_E_CONTRATOS.md` linhas 210, 374, 382 e 707) não conseguirão distinguir pelo `dataset_hash` dois recortes com os mesmos valores numéricos mas `observation_ids` posicionais diferentes quando `observation_id_col=None`.
* **Justificativa da Severidade:** `ALTO` (classificado como `RISCO` conforme regra de exceção da `spec.md`, pois `m1-4/spec.md` especificou `core.dataset_hash(bundle.columns, schema)` enquanto `ARQUITETURA_E_CONTRATOS.md:210,707` exige distinção por `observation_ids`).
* **Recomendação:** Antes de iniciar o M2, definir e incorporar `observation_ids` (ou um campo explícito no cálculo de `bundle.dataset_hash` / `SanitizedDatasetView.dataset_hash`) para cumprir o invariante da Seção 7.1 (`ARQUITETURA_E_CONTRATOS.md:707`).

---

### `AUD-F-006` — `slice_bundle_by_observation_ids` degrada `ObservationId` para `str` comum quando recebe `Sequence[str]`
* **Dimensão:** `INT` / `QUAL` (`INT-02`, `QUAL-02`)
* **Categoria:** `DEFEITO`
* **Severidade:** `ALTO`
* **Localização:** [query.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/query.py#L143)
* **Evidência Reprodutível:**
  * Comando:
    ```bash
    .venv/bin/python -c "from experimental_ml.core import TaskType, ObservationId; from experimental_ml.data import DatasetSchemaSpec, load_dataset, slice_bundle_by_observation_ids; b = load_dataset({'x': [1.0, 2.0], 'y': [3.0, 4.0]}, DatasetSchemaSpec(target_col='y', task_type=TaskType.REGRESSION)); sub = slice_bundle_by_observation_ids(b, ['obs_000001']); print([type(i).__name__ for i in sub.observation_ids], isinstance(sub.observation_ids[0], ObservationId))"
    ```
  * Saída: `['str'] False`.
* **Impacto:** Quebra o contrato de tipo `DatasetBundle.observation_ids: tuple[ObservationId, ...]` sempre que o consumidor passa strings simples (como demonstrado no próprio `README.md:321`). No Marco M2, validações em `PartitionPlan` que checarem `isinstance(oid, ObservationId)` falharão após um `slice_bundle_by_observation_ids`.
* **Justificativa da Severidade:** `ALTO` — defeito de integridade de tipo na fronteira entre `data` e o futuro módulo `validation` (M2).
* **Recomendação:** Em `slice_bundle_by_observation_ids`, construir `observation_ids=tuple(bundle.observation_ids[i] for i in indices)` (ou converter via `ObservationId(obs)`), garantindo que `sub.observation_ids` contenha sempre instâncias de `ObservationId`.

---

### `AUD-F-007` — Inteiros fora do intervalo `int64` ($\ge 2^{63}$) em `load_dataset` levantam `OverflowError` não tratado em vez de `DataIntegrityError`
* **Dimensão:** `INT` / `QUAL` (`INT-03`, `QUAL-03`)
* **Categoria:** `DEFEITO`
* **Severidade:** `MODERADO`
* **Localização:** [loader.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/loader.py#L135)
* **Evidência Reprodutível:**
  * Comando:
    ```bash
    .venv/bin/python -c "from experimental_ml.core import TaskType; from experimental_ml.data import DatasetSchemaSpec, load_dataset; load_dataset({'x': [2**63], 'y': [1.0]}, DatasetSchemaSpec(target_col='y', task_type=TaskType.REGRESSION))"
    ```
  * Saída: `OverflowError: Python int too large to convert to C long`.
* **Impacto:** Escapa da hierarquia `ExperimentalMLError` (`DataIntegrityError`) ao carregar IDs numéricos grandes ou inteiros de 64 bits sem sinal (`uint64` $\ge 2^{63}$).
* **Justificativa da Severidade:** `MODERADO` — ocorre apenas para inteiros $\ge 2^{63}$ ou $<-2^{63}$, mas viola o contrato de exceções de `load_dataset`.
* **Recomendação:** Capturar `OverflowError` em `np.array(int_vals, dtype=np.int64)` e levantar `DataIntegrityError` descritivo.

---

### `AUD-F-008` — Valores `np.float32(np.nan)` não são contabilizados como ausentes em `ColumnDescriptor.n_missing` nem em `_hash_column_binary`
* **Dimensão:** `ARCH` / `QUAL` (`ARCH-05`, `QUAL-03`)
* **Categoria:** `DEFEITO`
* **Severidade:** `ALTO`
* **Localização:** [loader.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/loader.py#L69) (`L69`, `L141`, `L151`), [query.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/query.py#L106) e [hashing.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/core/hashing.py#L189)
* **Evidência Reprodutível:**
  * Comando:
    ```bash
    .venv/bin/python -c "import numpy as np; from experimental_ml.core import TaskType; from experimental_ml.data import DatasetSchemaSpec, load_dataset; a = np.array([[np.float32(np.nan), np.float32(1.0)], [np.float32(2.0), np.float32(3.0)]], dtype=np.float32); b = load_dataset(a, DatasetSchemaSpec(target_col='col_1', task_type=TaskType.REGRESSION), has_header=False); print('n_missing:', b.descriptors['col_0'].n_missing, 'isnan:', int(np.isnan(b.columns['col_0']).sum()))"
    ```
  * Saída: `n_missing: 0 isnan: 1`.
* **Impacto:** Em Python/NumPy, `isinstance(np.float32(np.nan), float)` é **`False`** (pois `np.float32` herda de `np.floating`, enquanto apenas `np.float64` herda de `float`). Quando o usuário carrega um `ndarray` ou `DataFrame` com colunas `float32` contendo `NaN`, `ColumnDescriptor.n_missing` reporta `0` valores ausentes apesar de o array conter `NaN`! Isso compromete diretamente o Marco M2 (`profile_dataset` e detecção de `CONFIRMED_ISSUE` para valores ausentes).
* **Justificativa da Severidade:** `ALTO` — corrompe silenciosamente a contagem de valores ausentes (`n_missing`) que será a base do diagnóstico de qualidade (`DatasetProfile`) no Marco M2.
* **Recomendação:** Substituir `isinstance(v, float) and math.isnan(v)` por `isinstance(v, (float, np.floating)) and math.isnan(float(v))` em `loader.py`, `query.py`, `validation.py` e `hashing.py`.

---

### `AUD-F-009` — Colunas `dtype=object` em `DatasetBundle` usam *blacklist* estreita e permitem objetos mutáveis e `setflags(write=True)`
* **Dimensão:** `QUAL` (`QUAL-05`)
* **Categoria:** `RISCO`
* **Severidade:** `ALTO`
* **Localização:** [loader.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/loader.py#L149-L164)
* **Evidência Reprodutível:**
  * Comando:
    ```bash
    .venv/bin/python -c "import types; from experimental_ml.core import TaskType; from experimental_ml.data import DatasetSchemaSpec, load_dataset; ns = types.SimpleNamespace(v='a'); b = load_dataset({'cat': [ns, ns], 'y': [1.0, 2.0]}, DatasetSchemaSpec(target_col='y', task_type=TaskType.REGRESSION)); ns.v = 'mutated'; print(b.columns['cat'][0].v)"
    ```
  * Saída: `mutated` (o conteúdo interno de `DatasetBundle` foi alterado após a criação sem mudar `bundle.dataset_hash`).
* **Impacto:** Como `_coerce_column_values` verifica apenas `elif isinstance(v, (list, dict, set, bytearray)):`, qualquer objeto mutável fora dessas 4 classes (`SimpleNamespace`, objetos customizados, `Decimal`/containers) passa sem erro e permite mutação silenciosa pós-ingestão.
* **Justificativa da Severidade:** `ALTO` — viola a garantia de posse exclusiva e imutabilidade de escalares em colunas `object` (`DATA-10` / `RF1.7`).
* **Recomendação:** Substituir a *blacklist* na linha 153 de `loader.py` por uma *whitelist* explícita de escalares imutáveis permitidos em colunas `object`: `isinstance(v, (str, bytes, int, float, bool, np.number, np.bool_))`.

---

### `AUD-F-010` — Contradição documental sobre invariância de `dataset_hash` à ordem de colunas e relação com `ADR-007`
* **Dimensão:** `DOC` / `ARCH` (`DOC-05`, `ARCH-07`, `INT-04`)
* **Categoria:** `RISCO`
* **Severidade:** `MODERADO`
* **Localização:** [ARQUITETURA_E_CONTRATOS.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/engenharia_software/ARQUITETURA_E_CONTRATOS.md#L250) (`L209`, `L250`, `L743`) e [README.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/README.md#L94)
* **Evidência Reprodutível:**
  * `ARQUITETURA_E_CONTRATOS.md:250` e `743` afirmam que `dataset_hash` é *"invariante a quebras de linha CRLF/LF e ordenação de chaves"*.
  * Na execução real (`INT-04`), `load_dataset({"x": [1.0, 3.0], "y": [2.0, 4.0]}, schema).dataset_hash != load_dataset({"y": [2.0, 4.0], "x": [1.0, 3.0]}, schema).dataset_hash`, pois `m1-4/spec.md` (Goal 5) definiu que a ordem das colunas faz parte da identidade do dataset.
* **Impacto:** Gera ambiguidade contratual sobre se a reordenação de colunas em memória deve ou não alterar `dataset_hash`.
* **Justificativa da Severidade:** `MODERADO` — o comportamento do código segue a especificação aprovada do M1.4, mas o texto de `ARQUITETURA_E_CONTRATOS.md` e `README.md` afirma o oposto.
* **Recomendação:** Atualizar `ARQUITETURA_E_CONTRATOS.md` (`L209`, `L250`, `L743`) e `README.md` (`L94`) para refletir que a ordem das colunas compõe a identidade de `dataset_hash` (apenas `config_hash` é invariante à ordem de chaves) e que `ADR-007` distingue `raw_source_hash` (bytes do arquivo) de `dataset_hash` (conteúdo tabular canônico).

---

### `AUD-F-011` — Assimetria em `precision`, `recall` e `f1` (`pos_label=1` fixo) quando a coluna-alvo binária possui rótulos textuais (`dtype=object`)
* **Dimensão:** `INT` (`INT-08`, `READY-01`)
* **Categoria:** `RISCO`
* **Severidade:** `MODERADO`
* **Localização:** [classification.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/metrics/classification.py#L185) (`L185`, `L307`, `L429`)
* **Evidência Reprodutível:**
  * Comando:
    ```bash
    .venv/bin/python -c "from experimental_ml.metrics import compute_metric; print(compute_metric('accuracy', ['no', 'yes'], ['no', 'yes']).status, compute_metric('precision', ['no', 'yes'], ['no', 'yes']).status)"
    ```
  * Saída: `VALID UNDEFINED_NAN` (`W_METRIC_ZERO_PREDICTIONS` porque `pos_label=1` não ocorre em `['no', 'yes']`).
* **Impacto:** Enquanto `load_dataset` aceita alvos binários textuais (`["no", "yes"]`) e `accuracy`, `balanced_accuracy`, `roc_auc` e `log_loss` inferem as 2 classes automaticamente, `precision`, `recall` e `f1` retornam `UNDEFINED_NAN` a menos que `pos_label` seja informado manualmente ou que a coluna-alvo seja codificada para `{0, 1}` no `PreparationPlan` / `SanitizedDatasetView` do Marco M2.
* **Justificativa da Severidade:** `MODERADO` — risco de integração entre `data` (Etapa 1) e `metrics` (Etapas 3–5) caso o `PreparationPlan` no M2 não exija codificação canônica de alvos binários textuais ou inferência explícita de `pos_label`.
* **Recomendação:** Definir explicitamente na especificação do M2 (`DatasetProfile` / `PreparationPlan` / `SanitizedDatasetView`) se variáveis-alvo binárias com `dtype=object` geram um `CONFIRMED_ISSUE` exigindo mapeamento explícito de classe positiva para `{0, 1}`, ou se `precision`/`recall`/`f1` devem inferir `classes[1]` quando `pos_label` não coincidir com `{0, 1}` e os rótulos não forem numéricos.

---

### `AUD-F-012` — Ausência de `verification.md` no diretório de governança `.specs/features/m1-1-setup-cli-smoke/`
* **Dimensão:** `TEST` / `DOC` (`TEST-06`, `DOC-07`)
* **Categoria:** `RISCO`
* **Severidade:** `MODERADO`
* **Localização:** `.specs/features/m1-1-setup-cli-smoke/`
* **Evidência Reprodutível:**
  * Comando: `.venv/bin/python .agent/skills/tlc-spec-driven/scripts/validate_verification.py m1-1-setup-cli-smoke --strict`
  * Saída: `ERROR m1-1-setup-cli-smoke: no verification.md - the feature is not done until a fresh Verifier (author != verifier) writes its findings` (exit code `1`).
* **Impacto:** Faz com que os scripts `validate_verification.py` e `check_commit.py` do TLC reportem continuamente que `m1-1-setup-cli-smoke` está inacabada, além de contradizer o comentário do `README.md:104`.
* **Justificativa da Severidade:** `MODERADO` — lacuna formal nos registros de governança do primeiro sub-marco.
* **Recomendação:** Gerar e registrar `verification.md` para `m1-1-setup-cli-smoke` no lote de saneamento pré-M2.

---

### `AUD-F-013` — Ausência de testes de integração entre `experimental_ml.data` e `experimental_ml.metrics` na suíte oficial `tests/`
* **Dimensão:** `TEST` (`TEST-04`)
* **Categoria:** `MELHORIA`
* **Severidade:** `MODERADO`
* **Localização:** `tests/`
* **Evidência Reprodutível:**
  * Comando: `.venv/bin/python .specs/features/m1-integrity-review/probes/testing_and_tlc_probe.py` (`TEST-04`: `count_combining_data_and_metrics: 0`).
* **Impacto:** A suíte de 81 testes testa `core`, `metrics` e `data` isoladamente, deixando de detectar regressões nas fronteiras entre pacotes (como `AUD-F-006` e `AUD-F-011`).
* **Justificativa da Severidade:** `MODERADO` — melhoria recomendada na estratégia de testes antes de expandir para os módulos de nível superior no M2.
* **Recomendação:** Criar `tests/integration/test_m1_foundation_integration.py` cobrindo o fluxo integrado `load_dataset` $\rightarrow$ `slice_bundle_by_observation_ids` $\rightarrow$ `get_column_array` $\rightarrow$ `compute_metric` $\rightarrow$ `aggregate_fold_metrics` $\rightarrow$ `rank_configurations` e a execução dos blocos do `README.md`.

---

### `AUD-F-014` — `validate_verification.py` invalida `proofs.md` de features já concluídas sempre que `HEAD` avança
* **Dimensão:** `TEST` (`TEST-06`, `TEST-08`)
* **Categoria:** `MELHORIA`
* **Severidade:** `BAIXO`
* **Localização:** [validate_verification.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.agent/skills/tlc-spec-driven/scripts/validate_verification.py#L284-L290)
* **Evidência Reprodutível:**
  * `validate_verification.py m1-2-core` falha com `ERROR m1-2-core: proofs.md was written at c0ca71c and HEAD is ...` porque `HEAD` avançou nos commits subsequentes.
* **Impacto:** Impede que `validate_verification.py` seja executado em CI para verificar features históricas sem reexecutar `check_proofs.py` para todas as features a cada novo commit.
* **Justificativa da Severidade:** `BAIXO` — comportamento de design do script TLC (voltado ao fechamento imediato da feature no `HEAD`), sem impacto no código de produção.
* **Recomendação:** Documentar que `validate_verification.py <feature>` avalia o `HEAD` corrente (ou atualizar o script no futuro para aceitar que `proofs.md` seja ancestral de `HEAD` quando nenhum arquivo fora de `.specs/` mudou para aquela feature).

---

### `AUD-F-015` — Pequenos pontos de higiene de código (`_ALLOWED_AGG_SCOPES` como `set` mutável e `assert` em `loader.py:317`)
* **Dimensão:** `QUAL` (`QUAL-01`)
* **Categoria:** `MELHORIA`
* **Severidade:** `BAIXO`
* **Localização:** [aggregation.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/metrics/aggregation.py#L21) e [loader.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/src/experimental_ml/data/loader.py#L317)
* **Evidência Reprodutível:**
  * Em `aggregation.py:21`, `_ALLOWED_AGG_SCOPES = {...}` é um `set` mutável em nível de módulo.
  * Em `loader.py:317`, `assert source_path_str is not None` usa `assert` em código de produção.
* **Impacto:** Cosmético/higiene; não causa falha funcional.
* **Justificativa da Severidade:** `BAIXO`.
* **Recomendação:** Converter `_ALLOWED_AGG_SCOPES` para `frozenset` e substituir `assert` por verificação condicional explícita.

---

### `AUD-F-016` — Interpretadores Python 3.10 e 3.11 ausentes no host local para verificação empírica de `RNF06`
* **Dimensão:** `QUAL` (`QUAL-06`, `AUD-04`)
* **Categoria:** `LIMITAÇÃO DOCUMENTADA`
* **Severidade:** `BAIXO`
* **Localização:** [RESULTS.md (M1.1)](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-1-setup-cli-smoke/RESULTS.md) e [ESPECIFICACAO_REQUISITOS.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/engenharia_software/ESPECIFICACAO_REQUISITOS.md#L101)
* **Evidência Reprodutível:**
  * Comando: `which python3.10 python3.11` $\rightarrow$ ausentes no host; apenas `Python 3.12.15` (`.venv`) e `Python 3.14.8` (sistema) estão presentes.
* **Impacto:** A compatibilidade com Python 3.10 e 3.11 é preservada estaticamente (`from __future__ import annotations`, `StrEnum` compatível em `core/enums.py`), mas não pode ser testada empiricamente neste host local.
* **Justificativa da Severidade:** `BAIXO` — limitação ambiental previamente documentada e aceita no Marco M1.1.
* **Recomendação:** Manter registrada como limitação ambiental até a configuração de matriz multi-versão em CI.
