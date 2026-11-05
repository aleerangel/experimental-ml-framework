# 1. Especificação e Critérios da Auditoria (`01-especificacao-criterios.md`)

**Referência Canônica:** [spec.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/spec.md) | [SPEC.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/SPEC.md) | [ACCEPTANCE.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/ACCEPTANCE.md)

---

## 1. Objetivo e Escopo

Esta auditoria avalia de forma transversal, empírica e independente a fundação construída no Marco M1 (`M1.1 — setup-cli-smoke`, `M1.2 — core`, `M1.3 — metrics`, `M1.4 — datasets-schemas`) antes do início do Marco M2 (`Diagnóstico Estrutural, Sanitização e Particionamento Auditado`).

A avaliação abrange seis dimensões técnicas (`A`–`F`) e um protocolo transversal (`AUD`), totalizando **48 critérios objetivos e verificáveis** (`C1`–`C48`).

---

## 2. Matriz dos 48 Critérios Objetivos por Dimensão

### Protocolo e Isolamento (`AUD`)

| ID | Check | Critério Objetivo Verificável |
| :--- | :--- | :--- |
| `AUD-01` | `C1` | Linha de base registrada com hash `HEAD`, `git status --porcelain`, versões de Python/NumPy/pytest e resultado dos 81 testes. |
| `AUD-02` | `C2` | `git diff` vazio sobre `src/`, `tests/`, `pyproject.toml`, `README.md`, `engenharia_software/`, `.agent/` e `.specs/features/m1-{1,2,3,4}-*/`. |
| `AUD-03` | `C3` | Todo achado registrado com ID `AUD-F-NNN`, dimensão, categoria, severidade, evidência reprodutível, impacto e recomendação. |
| `AUD-04` | `C4` | Sondas destrutivas ou mutantes executadas apenas em `/tmp/m1-audit-*` e removidas ao final. |

### Dimensão A — Integridade Arquitetural (`ARCH`)

| ID | Check | Critério Objetivo Verificável |
| :--- | :--- | :--- |
| `ARCH-01` | `C5` | Grafo AST completo de `import`/`from ... import` em `src/experimental_ml/` comparado com a Seção 2.3 de `ARQUITETURA_E_CONTRATOS.md`. |
| `ARCH-02` | `C6` | Verificação da hierarquia de níveis ($L_0 = \{\text{core}\}$, $L_1 = \{\text{metrics}, \text{data}\}$, $L_2 = \{\text{cli}\}$), ausência de ciclos e separação de responsabilidades. |
| `ARCH-03` | `C7` | Verificação de que `core` não importa `metrics`/`data`/`cli` e de que `metrics` e `data` não se importam mutuamente. |
| `ARCH-04` | `C8` | Classificação de todas as classes em `src/experimental_ml/` segundo o ADR-008 (`Enum`, `Exception`, `frozen dataclass` com `slots=True` ou `str` imutável) e inspeção de `__slots__`/`__dict__`. |
| `ARCH-05` | `C9` | Inspeção de lógica duplicada entre módulos (normalização Unicode, validação finita/NaN, coerção de arrays, hashing de dados em memória vs. `DatasetBundle`). |
| `ARCH-06` | `C10` | Rastreamento de todos os símbolos exportados em `__all__` para identificar abstrações órfãs ou não referenciadas. |
| `ARCH-07` | `C11` | Comparação sistemática entre assinaturas, tipos e semântica documentados em `ARQUITETURA_E_CONTRATOS.md` e o código real. |

### Dimensão B — Integração entre Módulos (`INT`)

| ID | Check | Critério Objetivo Verificável |
| :--- | :--- | :--- |
| `INT-01` | `C12` | Execução de fluxo ponta a ponta: `load_dataset` $\rightarrow$ `get_column_array` $\rightarrow$ `compute_metric` $\rightarrow$ `aggregate_fold_metrics` $\rightarrow$ `rank_configurations`. |
| `INT-02` | `C13` | Identidade de tipos e invariantes de `ObservationId` e `TaskType` ao atravessar `core`, `data` e `metrics` (incluindo `slice_bundle_by_observation_ids`). |
| `INT-03` | `C14` | Verificação de herança `ExperimentalMLError` em todas as exceções levantadas por `core`, `metrics` e `data` sob entradas inválidas. |
| `INT-04` | `C15` | Comparação empírica de `dataset_hash`, `raw_source_hash` e `schema_hash` entre CSV (LF/CRLF), TSV e `dict` em memória. |
| `INT-05` | `C16` | Determinismo entre processos independentes com `PYTHONHASHSEED=0` e `PYTHONHASHSEED=12345` para hashes, sementes e fatiamentos. |
| `INT-06` | `C17` | Preservação de `flags.writeable == False` e integridade de bytes ao passar `get_column_array(copy=False)` para todas as 15 métricas de `METRICS_CATALOG`. |
| `INT-07` | `C18` | Verificação da relação formal entre `bundle.dataset_hash`, `bundle.raw_source_hash`, `bundle.schema_hash` e chamadas diretas a `core.dataset_hash` e `core.config_hash`. |
| `INT-08` | `C19` | Compatibilidade de colunas `int64` e `bool` extraídas de `DatasetBundle` com funções de métricas de regressão e classificação. |

### Dimensão C — Qualidade da Implementação (`QUAL`)

| ID | Check | Critério Objetivo Verificável |
| :--- | :--- | :--- |
| `QUAL-01` | `C20` | Varredura AST de `src/experimental_ml/` buscando `except:` nu, exceções engolidas, defaults mutáveis, `assert` em tempo de execução, globais mutáveis e imports não utilizados. |
| `QUAL-02` | `C21` | Verificação de anotações de tipo completas em funções públicas e aderência das estruturas retornadas em tempo de execução. |
| `QUAL-03` | `C22` | Sonda de casos extremos: entradas vazias, tamanhos discrepantes, `NaN`, `np.float32(np.nan)`, `±Inf`, Unicode NFD, IDs duplicados, inteiros $\ge 2^{63}$ e colisões de nomes em hashes. |
| `QUAL-04` | `C23` | Benchmark empírico de escalabilidade ($N = 10.000$ vs. $N = 100.000$ linhas $\times 20$ colunas) para `load_dataset` e `dataset_hash`. |
| `QUAL-05` | `C24` | Sonda adversarial de imutabilidade sobre `DatasetBundle`, `DatasetSchemaSpec`, `ColumnDescriptor`, `MetricValue`, `AggregatedMetricValue`, `Finding` e `DomainIdentifier`. |
| `QUAL-06` | `C25` | Verificação de compatibilidade com interpretadores Python no host frente ao requisito `RNF06` (Python 3.10, 3.11 e 3.12). |

### Dimensão D — Estratégia de Testes e Confiabilidade do TLC (`TEST`)

| ID | Check | Critério Objetivo Verificável |
| :--- | :--- | :--- |
| `TEST-01` | `C26` | Cobertura de linhas por arquivo em `src/experimental_ml/` medida via `trace`/`sys.settrace` durante `pytest tests/`. |
| `TEST-02` | `C27` | Inventário de funções públicas e caminhos de erro testados vs. não testados. |
| `TEST-03` | `C28` | Ensaio de mutação controlada com $\ge 12$ mutações semânticas em cópia efêmera `/tmp/m1-audit-mut/` e cálculo de taxa de detecção. |
| `TEST-04` | `C29` | Quantificação de testes de integração entre pacotes (`data` + `metrics`) em `tests/`. |
| `TEST-05` | `C30` | Independência de ordem e isolamento dos 81 testes (execução individual, ordem direta e ordem reversa). |
| `TEST-06` | `C31` | Execução de `validate_spec.py --strict`, `validate_tasks.py --strict` e `validate_verification.py --strict` sobre `m1-1`..`m1-4`. |
| `TEST-07` | `C32` | Execução de `check_proofs.py` sobre cópia efêmera de `m1-1`..`m1-4` em `/tmp/m1-audit-clone/`. |
| `TEST-08` | `C33` | Auditoria estática do código-fonte dos scripts validadores em `.agent/skills/tlc-spec-driven/scripts/`. |

### Dimensão E — Documentação e Rastreabilidade (`DOC`)

| ID | Check | Critério Objetivo Verificável |
| :--- | :--- | :--- |
| `DOC-01` | `C34` | Execução real em subprocesso de todos os blocos `python` do `README.md`. |
| `DOC-02` | `C35` | Comparação exata entre a árvore de diretórios do `README.md` e os arquivos existentes em disco. |
| `DOC-03` | `C36` | Verificação cruzada de contagens de testes, versões e status de marcos em todos os documentos de engenharia e governança. |
| `DOC-04` | `C37` | Verificação de importabilidade real de todos os símbolos públicos listados como implementados na documentação. |
| `DOC-05` | `C38` | Identificação de afirmações contraditórias entre documentos ou entre documentação e implementação. |
| `DOC-06` | `C39` | Matriz completa de conformidade e rastreabilidade (`RF`/`RNF`/`CA`/`TA-M1.*`) com evidências verificadas. |
| `DOC-07` | `C40` | Auditoria de completude e consistência dos artefatos de governança (`.specs/STATE.md`, `.specs/features/m1-*/`). |

### Dimensão F — Prontidão para o Segundo Marco (`READY`)

| ID | Check | Critério Objetivo Verificável |
| :--- | :--- | :--- |
| `READY-01` | `C41` | Avaliação de prontidão dos contratos de `DatasetBundle`, `ColumnDescriptor`, `DatasetSchemaSpec` e `ObservationId` para M2 (`DatasetProfile`, `PreparationPlan`, `SanitizedDatasetView`, `PartitionPlan`). |
| `READY-02` | `C42` | Avaliação de `Finding`, `FindingSeverity` e `make_finding`/`make_warning` frente a `DiagnosticFinding` (`CONFIRMED_ISSUE` vs. `HEURISTIC_WARNING`). |
| `READY-03` | `C43` | Avaliação de `derive_seeds`, `spawn_child_seeds`, `config_hash`, `dataset_hash` e `PartitionPlanId` para particionamento determinístico (`TA-M2.2`, `TA-M2.3`). |
| `READY-04` | `C44` | Avaliação da CLI em `src/experimental_ml/cli/main.py` para subcomandos hierárquicos (`expml data`, `expml partition`). |
| `READY-05` | `C45` | Plano de correções priorizadas (`07-plano-correcoes.md`) em três faixas de prioridade. |
| `READY-06` | `C46` | Parecer final (`08-parecer.md` e `RESULTS.md`) aplicando a regra objetiva de decisão (`APTO` / `APTO COM RESSALVAS` / `NÃO APTO`). |
| `READY-07` | `C47` | Consistência de severidades e categorias em `06-achados.md`. |
| `READY-08` | `C48` | Verificação independente de 100% dos achados `CRÍTICO`/`ALTO` e $\ge 20\%$ dos demais achados pelo agente Verifier. |

---

## 3. Regra Objetiva de Decisão do Parecer Final (`READY-06`)

* **`NÃO APTO`:** Existência de $\ge 1$ achado de severidade **`CRÍTICO`** (qualquer categoria) **ou** $\ge 1$ achado classificado como **`DEFEITO`** de severidade **`ALTO`** sem correção aplicada antes do início do M2.
* **`APTO COM RESSALVAS`:** Zero achados `CRÍTICO` e zero `DEFEITO` `ALTO`, mas existência de achados `ALTO` classificados como `RISCO`/`MELHORIA` ou achados `MODERADO` com plano de tratamento explícito antes ou no início do M2.
* **`APTO`:** Zero achados de severidade `CRÍTICO`, `ALTO` ou `MODERADO`.

