# Registro de Validação e Aceite — Marco M2.2 (Preparation Plan & Sanitized Dataset View)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M2.2 (`m2-2-preparation-plan-sanitization`)  
> **Data de Validação:** 07 de Novembro de 2026  
> **Commit de Implementação:** [`e39bb1e`](https://github.com/alexandrerangel/experimental-ml-framework/commit/e39bb1e)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via `tomllib` e ambiente `.venv` | **APROVADO** |
| **Testes Unitários Automatizados** | 16 testes em `tests/unit/data/test_preparation.py` | 16 testes aprovados (100%) | **APROVADO** |
| **Testes de Integração e Invariantes** | 3 testes em `tests/integration/test_preparation_integration.py` | 3 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 133 testes em `pytest tests/` | 133 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria independente | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (3 capacidades) | Executado com sucesso via interfaces públicas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Preparação Unitária e Integração

Execução no ambiente `.venv` (`.venv/bin/pytest tests/unit/data/test_preparation.py tests/integration/test_preparation_integration.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 19 items

tests/unit/data/test_preparation.py::test_t1_preparation_rule_immutability_and_slots PASSED [  5%]
tests/unit/data/test_preparation.py::test_t1_unresolved_finding_immutability_and_slots PASSED [ 10%]
tests/unit/data/test_preparation.py::test_t1_preparation_plan_immutability_and_slots PASSED [ 15%]
tests/unit/data/test_preparation.py::test_t1_sanitized_dataset_view_immutability_and_slots PASSED [ 21%]
tests/unit/data/test_preparation.py::test_t2_admissibility_valid_rules PASSED [ 26%]
tests/unit/data/test_preparation.py::test_prep_03_invalid_rule_admissibility_and_configuration_error PASSED [ 31%]
tests/unit/data/test_preparation.py::test_prep_01_ready_plan_canonical_order PASSED [ 36%]
tests/unit/data/test_preparation.py::test_prep_02_incomplete_plan_unresolved_findings PASSED [ 42%]
tests/unit/data/test_preparation.py::test_t3_duplicate_rule_and_dict_coercion PASSED [ 47%]
tests/unit/data/test_preparation.py::test_prep_05_binding_validation_and_status_check PASSED [ 52%]
tests/unit/data/test_preparation.py::test_prep_08_binary_target_mapping_and_encoding PASSED [ 57%]
tests/unit/data/test_preparation.py::test_prep_09_empty_dataset_or_features_raises_integrity_error PASSED [ 63%]
tests/unit/data/test_preparation.py::test_t4_drop_rows_and_order_preservation PASSED [ 68%]
tests/unit/data/test_preparation.py::test_prep_04_sanitize_dataset_structural_rules PASSED [ 73%]
tests/unit/data/test_preparation.py::test_prep_06_sanitized_view_contract_and_dataset_hash PASSED [ 78%]
tests/unit/data/test_preparation.py::test_prep_07_bit_identical_deferred_and_accepted_columns PASSED [ 84%]
tests/integration/test_preparation_integration.py::test_prep_10_immutability_and_determinism PASSED [ 89%]
tests/integration/test_preparation_integration.py::test_end_to_end_preparation_pipeline PASSED [ 94%]
tests/integration/test_preparation_integration.py::test_architectural_import_direction_data_preparation PASSED [100%]

============================== 19 passed in 0.23s ==============================
```

### 2.2 Suíte Completa de Regressão

Execução no ambiente `.venv` (`.venv/bin/pytest tests/ -q`):

```text
133 passed in 1.20s
```

---

## 3. Conformidade com Decisões Arquiteturais

1. **ADR-001 (Zero External Runtime Dependencies beyond NumPy):**
   - Nenhuma biblioteca externa adicionada. Dependências limitadas estritamente a `numpy>=1.24.0` e a biblioteca padrão (`dataclasses`, `types`, `hashlib`, `json`).
2. **ADR-002 (Zero Data Leakage / Pre-partition Sanitization):**
   - Apenas transformações estruturais pré-partição (`DROP_ROWS`, `EXCLUDE_COLUMN`, `MAP_BINARY_TARGET`) são executadas.
   - Variáveis sob `DEFER_INTRA_FOLD` e `ACCEPT_AS_IS` são mantidas 100% bit a bit idênticas ao bundle original, para ajuste e aprendizado de parâmetros exclusivamente no treino de cada fold na Etapa 4B.
3. **ADR-007 / ADR-008 (Hashing Determinístico e Imutabilidade):**
   - O `DatasetBundle` original permanece intocado (`bundle.dataset_hash` idêntico antes e depois).
   - A `SanitizedDatasetView` encapsula arrays somente-leitura (`writeable = False`), tuplas imutáveis e mapeamentos via `MappingProxyType`, calculando deterministicamente seu próprio `dataset_hash` via `core.dataset_hash(...)`.
