# Marco M1.2 — Core: Tipos, Enums, Sementes, Hashing e Diagnósticos

> **Registro de Especificação do Marco (SPEC.md)**  
> **Identificador do Marco:** M1.2 (`m1-2-core`)  
> **Camada Arquitetural:** Nível 0 (Fundação transversal às Etapas 1–6)  
> **Status:** Implementado  
> **Aprovação da Especificação:** `**Approved**: 2026-10-31 - user: "avança"`  
> **Documento Detalhado EARS:** [`spec.md`](./spec.md)  
> **Roteiro de Validação:** [`ACCEPTANCE.md`](./ACCEPTANCE.md)  
> **Evidências e Decisão de Aceite:** [`RESULTS.md`](./RESULTS.md)

---

## 1. Propósito e Problema Abordado

O marco **M1.2** implementa os componentes transversais de base do `experimental-ml-framework`:
1. **Identificadores de domínio imutáveis:** Subtipos de `str` (`ExperimentId`, `ModelId`, etc.) com validação contra strings vazias, em branco ou caracteres de controle.
2. **Enumerações:** `TaskType`, `ExecutionStatus`, `FindingSeverity`, `MetricDirection`, `AggregationScope`, `MetricStatus` e `ErrorPolicy`, com comparação direta a strings e serialização JSON.
3. **Derivação determinística de sementes:** Funções `derive_seeds` e `spawn_child_seeds` baseadas em `numpy.random.SeedSequence` para reprodutibilidade de fluxos estocásticos (RNF01, ADR-007).
4. **Serialização e hashing (`config_hash` e `dataset_hash`):** Regras de hashing do ADR-007 (Unicode NFC, ordenação de chaves por bytes UTF-8, distinção de tipos `bool`, `int` e `float`, normalização de `-0.0 -> 0.0`, `NaN` e `+/-Inf`, e distinção entre `tuple` e `list`).
5. **Diagnósticos e exceções:** Estrutura imutável `Finding`, construtores `make_finding` e `make_warning`, e hierarquia de exceções (`ExperimentalMLError`, `ContractViolationError`, `DataIntegrityError`, `ConfigurationError`).
6. **Organização funcional (ADR-008):** Funções puras e estruturas de dados imutáveis, sem classes com estado interno mutável.

---

## 2. Escopo Efetivamente Definido

### Incluído no Marco M1.2
- **Dependência:** Inclusão de `numpy>=1.24.0` em `dependencies` no `pyproject.toml`.
- **Módulo `experimental_ml.core`:**
  - `types.py`: `ExperimentId`, `PartitionPlanId`, `ScenarioId`, `ModelId`, `CellId`, `ComparisonId`, `ArtifactId`, `ObservationId`.
  - `enums.py`: `TaskType`, `ExecutionStatus`, `FindingSeverity`, `MetricDirection`, `AggregationScope`, `MetricStatus`, `ErrorPolicy`.
  - `findings.py`: `Finding`, `make_finding`, `make_warning`, `ExperimentalMLError`, `ContractViolationError`, `DataIntegrityError`, `ConfigurationError`.
  - `seeds.py`: `derive_seeds(master_seed, count)`, `spawn_child_seeds(parent_seed, count)`.
  - `hashing.py`: `config_hash(obj)`, `dataset_hash(data_or_path, schema=None)`.
  - `__init__.py`: Re-exportação com declaração formal de `__all__`.
- **Testes Unitários:** Suíte `tests/unit/test_core.py` cobrindo 18 critérios de aceitação.

### Não Incluído (Fora de Escopo)
- Módulo funcional `metrics` (catálogo de métricas, `UNDEFINED_NAN`, funções vetorizadas — Marco M1.3).
- Ingestão de datasets e perfilamento (`data` — Marco M2).
- Planos de partição e divisão de dobras (`validation` — Marco M2).
- Cenários de atributos e modelos (`features`, `models` — Marcos M3 e M4).

---

## 3. Matriz de Requisitos Rastreáveis (CORE-01 a CORE-18)

| ID | Descrição do Requisito EARS | Critério de Conclusão |
| :--- | :--- | :--- |
| **CORE-01** | Identificadores como tipos imutáveis de string | Todos os 8 tipos herdam de `str` e são instanciáveis. |
| **CORE-02** | Sanitização e validação de não-vazio | Construtores removem whitespace nas bordas e validam preenchimento. |
| **CORE-03** | Rejeição de strings vazias, quebras e não-strings | Dispara `ValueError`/`TypeError` para `""`, `"   "`, `\n`, `\r`, `\t`, inteiros. |
| **CORE-04** | Membros canônicos de `TaskType` e `ExecutionStatus` | Define membros exatos com igualdade a strings e serialização JSON. |
| **CORE-05** | Membros de `FindingSeverity`, `MetricDirection` e `AggregationScope` | Define membros canônicos conforme ADR-002 e ADR-007. |
| **CORE-06** | Membros de `MetricStatus`, `ErrorPolicy` e JSON | Define membros exatos e suporta `json.dumps` sem custom encoder. |
| **CORE-07** | Derivação de sementes via `SeedSequence` | `derive_seeds` retorna tupla de inteiros a partir da semente mestre. |
| **CORE-08** | Determinismo estrito de sementes | Mesma semente mestre e contagem geram tupla de inteiros idêntica. |
| **CORE-09** | Geração e validação de sementes filhas | `spawn_child_seeds` gera fluxos independentes e rejeita `count < 1`. |
| **CORE-10** | Digest SHA-256 de `config_hash` | Retorna digest hexadecimal minúsculo com 64 caracteres. |
| **CORE-11** | Normalização NFC e ordenação de chaves | Equivalência entre NFC e NFD; ordenação lexicográfica por bytes UTF-8. |
| **CORE-12** | Distinção estrita de tipos escalares e coleções | `True != 1`, `False != 0`, `1 != 1.0`, `list != tuple`, ordenação de `set`. |
| **CORE-13** | Normalização de float `-0.0`, `NaN` e `Inf` | `-0.0 == 0.0`, `NaN` canônico e detecção de referência circular. |
| **CORE-14** | Hashing de arquivos em disco com esquema | Digest SHA-256 de bytes brutos combinado deterministicamente com esquema. |
| **CORE-15** | Hashing binário de dados tabulares em memória | Sensível a valores, nomes de colunas, dtypes e ordenação de linhas. |
| **CORE-16** | Rejeição de arquivo inexistente | `dataset_hash` lança `FileNotFoundError` para caminhos inválidos. |
| **CORE-17** | Construtores de diagnósticos `make_finding` e `make_warning` | Cria registros `Finding` com severidades `CONFIRMED_ISSUE` e `HEURISTIC_WARNING`. |
| **CORE-18** | Hierarquia de exceções e imutabilidade de `Finding` | Subclasses de `ExperimentalMLError` e atributos de `Finding` congelados. |

