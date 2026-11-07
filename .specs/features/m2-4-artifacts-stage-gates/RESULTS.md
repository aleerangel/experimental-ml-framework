# Registro de Validação e Aceite — Marco M2.4 (Artifacts Persistence & Stage Gates)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M2.4 (`m2-4-artifacts-stage-gates`)  
> **Data de Validação:** 07 de Novembro de 2026  
> **Commit de Implementação:** [`01cc165`](https://github.com/alexandrerangel/experimental-ml-framework/commit/01cc165)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Dependência de runtime restrita a `numpy>=1.24.0` e biblioteca padrão Python | Validado no ambiente `.venv` com `gzip`, `csv`, `json` | **APROVADO** |
| **Testes Unitários Automatizados** | 9 testes unitários em `tests/unit/core/`, `tests/unit/data/`, `tests/unit/validation/`, `tests/unit/stages/` | 9 testes unitários aprovados (100%) | **APROVADO** |
| **Testes de Integração e Invariantes** | 2 testes em `tests/integration/test_artifacts_stage_gates_integration.py` | 2 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 162 testes em `pytest tests/` | 162 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria independente | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (4 capacidades) | Executado com sucesso via interfaces públicas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Persistência e Portões de Etapa (Unitária e Integração)

Execução no ambiente `.venv` (`.venv/bin/pytest tests/unit/core/test_storage.py tests/unit/data/test_codecs.py tests/unit/validation/test_splits_storage.py tests/unit/stages/test_stage_gates.py tests/integration/test_artifacts_stage_gates_integration.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 11 items

tests/unit/core/test_storage.py::test_store_01_atomic_write_and_failure_cleanup PASSED [  9%]
tests/unit/core/test_storage.py::test_store_07_overwrite_protection_configuration_error PASSED [ 18%]
tests/unit/core/test_storage.py::test_storage_converts_numpy_scalars_and_enums PASSED [ 27%]
tests/unit/data/test_codecs.py::test_store_02_lossless_codecs_roundtrip PASSED [ 36%]
tests/unit/validation/test_splits_storage.py::test_store_04_splits_csv_gz_deterministic PASSED [ 45%]
tests/unit/validation/test_splits_storage.py::test_partition_plan_codec_roundtrip PASSED [ 54%]
tests/unit/validation/test_splits_storage.py::test_splits_schema_writer PASSED [ 63%]
tests/unit/stages/test_stage_gates.py::test_store_05_hash_divergence_and_incomplete_plan_rejection PASSED [ 72%]
tests/unit/stages/test_stage_gates.py::test_store_06_splits_tampering_and_mismatch_rejection PASSED [ 81%]
tests/integration/test_artifacts_stage_gates_integration.py::test_store_03_experiment_directory_layout PASSED [ 90%]
tests/integration/test_artifacts_stage_gates_integration.py::test_architectural_import_direction_artifacts_stage_gates PASSED [100%]

============================== 11 passed in 0.28s ==============================
```

### 2.2 Suíte Completa de Regressão

Execução no ambiente `.venv` (`.venv/bin/pytest tests/ -q`):

```text
162 passed in 1.06s
```

---

## 3. Conformidade com Decisões Arquiteturais e Requisitos

1. **STORE-01 (Escrita Atômica de JSON):**
   - Implementado em `src/experimental_ml/core/storage.py` com escrita prévia em arquivo temporário no mesmo diretório, flush, `os.fsync`, renomeação atômica via `os.replace` e limpeza estrita em caso de exceção.
2. **STORE-02 (Codecs Lossless Bidirecionais):**
   - Implementados em `src/experimental_ml/data/codecs.py` e `src/experimental_ml/validation/codecs.py`. Garantem conformidade com RFC 8259 (sem `NaN`/`Infinity`) e conversão idempotente para tipos primitivos.
3. **STORE-03 (Layout Padronizado de Diretório):**
   - Conformidade com a topologia canônica (`data/`, `configuration/`, `partitions/`) comprovada por testes de integração e verificada por `verify_preparation_gate` e `verify_partition_gate`.
4. **STORE-04 (Compressão Determinística de Splits):**
   - Implementado em `src/experimental_ml/validation/storage.py` com `gzip.GzipFile(..., mtime=0.0)`, gerando bytes idênticos em sucessivas execuções e mapeamento transparente de observações por fold e holdout.
5. **STORE-05 e STORE-06 (Portões de Validação de Integridade e Rejeição de Adulterações):**
   - Implementados em `src/experimental_ml/stages/stage_gates.py`. Bloqueiam avanço caso `preparation_plan.json` não esteja `READY` (`ContractViolationError`), ou se houver divergência criptográfica de hashes de dataset ou contradição entre `splits.csv.gz` e `partition_plan.json` (`DataIntegrityError`).
6. **STORE-07 (Política de Não-Sobrescrita):**
   - Toda escrita de artefato recusa sobrescrever arquivos existentes disparando `ConfigurationError`, exceto sob passagem explícita de `overwrite=True`.

---

## 4. Decisão Formal de Aceite

Com base na aprovação de 100% dos testes unitários e de integração, na verificação independente das 7 checagens (C1 a C7) sem findings pendentes e na conformidade com o roteiro de aceitação `ACCEPTANCE.md`:

**Decisão**: **APROVADO**
