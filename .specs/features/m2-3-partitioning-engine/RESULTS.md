# Registro de Validação e Aceite — Marco M2.3 (Partitioning Engine)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M2.3 (`m2-3-partitioning-engine`)  
> **Data de Validação:** 07 de Novembro de 2026  
> **Commit de Implementação:** [`d7f5595`](https://github.com/alexandrerangel/experimental-ml-framework/commit/d7f5595)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via `tomllib` e ambiente `.venv` | **APROVADO** |
| **Testes Unitários Automatizados** | 15 testes em `tests/unit/validation/` | 15 testes aprovados (100%) | **APROVADO** |
| **Testes de Integração e Invariantes** | 3 testes em `tests/integration/test_validation_integration.py` | 3 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 151 testes em `pytest tests/` | 151 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria independente | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (4 capacidades) | Executado com sucesso via interfaces públicas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Particionamento Unitária e Integração

Execução no ambiente `.venv` (`.venv/bin/pytest tests/unit/validation/ tests/integration/test_validation_integration.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 18 items

tests/unit/validation/test_engine.py::test_part_01_kfold_cv_only PASSED  [  5%]
tests/unit/validation/test_engine.py::test_part_06_holdout_separation PASSED [ 11%]
tests/unit/validation/test_engine.py::test_holdout_only_regime PASSED    [ 16%]
tests/unit/validation/test_engine.py::test_missing_column_raises_configuration_error PASSED [ 22%]
tests/unit/validation/test_splitters.py::test_kfold_split_disjointness_and_coverage PASSED [ 27%]
tests/unit/validation/test_splitters.py::test_part_02_stratified_kfold_proportions PASSED [ 33%]
tests/unit/validation/test_splitters.py::test_holdout_split_proportions_and_disjointness PASSED [ 38%]
tests/unit/validation/test_splitters.py::test_part_03_group_kfold_disjointness PASSED [ 44%]
tests/unit/validation/test_splitters.py::test_part_04_temporal_monotonicity PASSED [ 50%]
tests/unit/validation/test_splitters.py::test_part_05_bootstrap_oob PASSED [ 55%]
tests/unit/validation/test_types.py::test_t1_enums_and_coercion PASSED   [ 61%]
tests/unit/validation/test_types.py::test_part_10_config_boundary_validation PASSED [ 66%]
tests/unit/validation/test_types.py::test_part_08_partition_plan_plan_id PASSED [ 72%]
tests/unit/validation/test_validators.py::test_part_07_validate_partition_plan_invariants PASSED [ 77%]
tests/unit/validation/test_validators.py::test_validator_group_and_temporal_invariants PASSED [ 83%]
tests/integration/test_validation_integration.py::test_part_09_immutability_and_determinism PASSED [ 88%]
tests/integration/test_validation_integration.py::test_validation_end_to_end_with_sanitized_dataset_view PASSED [ 94%]
tests/integration/test_validation_integration.py::test_architectural_import_direction_validation PASSED [100%]

============================== 18 passed in 0.17s ==============================
```

### 2.2 Suíte Completa de Regressão

Execução no ambiente `.venv` (`.venv/bin/pytest tests/ -q`):

```text
151 passed in 1.16s
```

---

## 3. Conformidade com Decisões Arquiteturais

1. **ADR-001 (Zero External Runtime Dependencies beyond NumPy):**
   - Dependência de execução estritamente restrita a `numpy>=1.24.0` e biblioteca padrão de Python.
2. **ADR-002 (Zero Data Leakage / Pre-partition Sanitization):**
   - Disjunção matemática comprovada a priori: $\text{Train}_k \cap \text{Val}_k = \emptyset$, $(\text{Train}_k \cup \text{Val}_k) \cap \text{Holdout} = \emptyset$.
   - Prevenção de vazamento temporal ($\max(\text{Time}) \le \min(\text{Time})$) e agrupado ($\text{Groups}(Train) \cap \text{Groups}(Val) = \emptyset$).
3. **Decisão D7 (Separação de Holdout e Confinamento de CV):**
   - `holdout_ids` são extraídos primeiro e os folds de validação cruzada operam exclusivamente sobre `development_ids`.
4. **Decisão D8 e ADR-007 (Identificação Canônica SHA-256 e Determinismo):**
   - `plan_id` de 64 caracteres calculado via digest SHA-256 sobre configurações e identificadores canônicos, invariante a timestamps voláteis.
5. **ADR-008 (Contratos Imutáveis e Validação Matemática):**
   - `PartitionPlan`, `FoldPartition` e `PartitionConfig` são dataclasses congeladas com slots (`frozen=True, slots=True`).
   - `validate_partition_plan` audita e garante todos os invariantes antes do retorno do plano.

---

## 4. Decisão Formal de Aceite

Com base na aprovação de 100% dos testes unitários e de integração, na verificação independente das 10 checagens (C1 a C10) sem findings pendentes e na execução com sucesso do roteiro de validação `ACCEPTANCE.md`:

**Decisão**: **APROVADO**
