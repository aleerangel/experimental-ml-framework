# Registro de Validação e Aceite — Marco M2.1 (Stage 1 Dataset Profiling)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M2.1 (`m2-diagnostics-partitioning`)  
> **Data de Validação:** 06 de Novembro de 2026  
> **Commit de Implementação:** [`8e9d63a`](https://github.com/alexandrerangel/experimental-ml-framework/commit/8e9d63a)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via `tomllib` e ambiente `.venv` | **APROVADO** |
| **Testes Unitários Automatizados** | 13 testes em `tests/unit/data/test_profiling.py` | 13 testes aprovados (100%) | **APROVADO** |
| **Testes de Integração e Invariantes** | 5 testes em `tests/integration/test_profiling_integration.py` | 5 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 114 testes em `pytest tests/` | 114 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria independente | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (5 capacidades) | Executado com sucesso via interfaces públicas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Profiling Unitária e Integração

Execução no ambiente `.venv` (`.venv/bin/pytest tests/unit/data/test_profiling.py tests/integration/test_profiling_integration.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 18 items

tests/unit/data/test_profiling.py::test_prof_11_profile_config_threshold_validation PASSED [  5%]
tests/unit/data/test_profiling.py::test_profiling_models_immutability_and_slots PASSED [ 11%]
tests/unit/data/test_profiling.py::test_prof_02_numeric_distribution_statistics PASSED [ 16%]
tests/unit/data/test_profiling.py::test_prof_03_categorical_distribution_and_frequencies PASSED [ 22%]
tests/unit/data/test_profiling.py::test_prof_12_fully_missing_column_handling PASSED [ 27%]
tests/unit/data/test_profiling.py::test_prof_04_duplicate_rows_detection PASSED [ 33%]
tests/unit/data/test_profiling.py::test_prof_05_target_profile_regression_and_classification PASSED [ 38%]
tests/unit/data/test_profiling.py::test_prof_06_group_profile_statistics PASSED [ 44%]
tests/unit/data/test_profiling.py::test_prof_07_catalog_findings_and_canonical_ordering PASSED [ 50%]
tests/unit/data/test_profiling.py::test_prof_08_severity_separation_heuristics_vs_issues PASSED [ 55%]
tests/unit/data/test_profiling.py::test_prof_09_binary_target_unmapped_and_class_count PASSED [ 61%]
tests/unit/data/test_profiling.py::test_prof_01_structural_profile_and_column_profiles PASSED [ 66%]
tests/unit/data/test_profiling.py::test_prof_10_immutability_and_determinism PASSED [ 72%]
tests/integration/test_profiling_integration.py::test_prof_10_immutability_and_determinism PASSED [ 77%]
tests/integration/test_profiling_integration.py::test_end_to_end_profiling_on_complex_dataset PASSED [ 83%]
tests/integration/test_profiling_integration.py::test_architectural_import_direction_xcut_01 PASSED [ 88%]
tests/integration/test_profiling_integration.py::test_single_runtime_dependency_xcut_02 PASSED [ 94%]
tests/integration/test_profiling_integration.py::test_exported_symbols_count_xcut_04 PASSED [100%]

============================== 18 passed in 0.32s ==============================
```

### 2.2 Suíte Completa de Regressão

Execução de todos os 114 testes do framework (`.venv/bin/pytest tests/ -v`):
- **114 passed** em 1.45s com 0 falhas, 0 avisos e 0 quebras de contrato anterior.

---

## 3. Rastreabilidade dos Requisitos Funcionais e Arquiteturais

| Requisito | Descrição | Status | Evidência de Verificação |
| :--- | :--- | :---: | :--- |
| **`PROF-01`** | Perfil estrutural e estatísticas de ausentes | `CONFORME` | `test_prof_01_structural_profile_and_column_profiles` |
| **`PROF-02`** | Métricas de distribuição numérica com `ddof=1` | `CONFORME` | `test_prof_02_numeric_distribution_statistics` |
| **`PROF-03`** | Frequências categóricas, ordenação e desempate | `CONFORME` | `test_prof_03_categorical_distribution_and_frequencies` |
| **`PROF-04`** | Detecção de linhas duplicadas sem `observation_id` | `CONFORME` | `test_prof_04_duplicate_rows_detection` |
| **`PROF-05`** | Perfilamento especializado do alvo (regressão e classificação) | `CONFORME` | `test_prof_05_target_profile_regression_and_classification` |
| **`PROF-06`** | Estatísticas de agrupamento com `group_col` | `CONFORME` | `test_prof_06_group_profile_statistics` |
| **`PROF-07`** | Emissão e ordenação canônica dos 15 achados do catálogo | `CONFORME` | `test_prof_07_catalog_findings_and_canonical_ordering` |
| **`PROF-08`** | Separação estrita de severidade (`CONFIRMED_ISSUE` vs `HEURISTIC_WARNING`) | `CONFORME` | `test_prof_08_severity_separation_heuristics_vs_issues` |
| **`PROF-09`** | Mutua exclusividade em alvo binário não mapeado vs contagem inválida | `CONFORME` | `test_prof_09_binary_target_unmapped_and_class_count` |
| **`PROF-10`** | Imutabilidade do `DatasetBundle` e determinismo funcional | `CONFORME` | `test_prof_10_immutability_and_determinism` |
| **`PROF-11`** | Validação de limiares em `ProfileConfig` | `CONFORME` | `test_prof_11_profile_config_threshold_validation` |
| **`PROF-12`** | Tratamento tolerante a colunas 100% ausentes | `CONFORME` | `test_prof_12_fully_missing_column_handling` |
| **`XCUT-01`** | Direção de importação (`core` ← `data`, sem `validation`/`cli`) | `CONFORME` | `test_architectural_import_direction_xcut_01` |
| **`XCUT-02`** | Dependência de runtime única (`numpy>=1.24.0`) | `CONFORME` | `test_single_runtime_dependency_xcut_02` |
| **`XCUT-03`** | Zero regressão de performance em relação a M1 | `CONFORME` | Execução completa em < 1.5s |
| **`XCUT-04`** | Contagem exata de símbolos públicos exportados (17 símbolos) | `CONFORME` | `test_exported_symbols_count_xcut_04` |
| **`XCUT-05`** | Normalização Unicode NFC e imutabilidade estrutural | `CONFORME` | `test_profiling_models_immutability_and_slots` |

---

## 4. Decisão Final de Aceite

> **DECISÃO: APROVADO**
>
> A entrega do sub-marco M2.1 cumpre integralmente os requisitos funcionais PROF-01 a PROF-12, os contratos de arquitetura transversal XCUT-01 a XCUT-05 e os critérios de validação operacional documentados no Roteiro de Aceitação.
