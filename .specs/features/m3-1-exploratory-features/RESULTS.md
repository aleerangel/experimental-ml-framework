# Registro de Validação e Aceite — Marco M3.1 (Exploratory Feature Relations Report)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M3.1 (`m3-1-exploratory-features`)  
> **Data de Validação:** 10 de Novembro de 2026  
> **Commit de Implementação:** [`b757812`](https://github.com/alexandrerangel/experimental-ml-framework/commit/b757812)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via subprocess e ambiente `.venv` | **APROVADO** |
| **Testes Unitários Automatizados** | 13 testes em `tests/unit/features/` | 13 testes aprovados (100%) | **APROVADO** |
| **Testes de Integração e Invariantes** | 2 testes em `tests/integration/features/` | 2 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 208 testes em `pytest tests/` | 208 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria independente | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (4 capacidades) | Executado com sucesso via interfaces públicas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Features Unitária e Integração

Execução no ambiente `.venv` (`.venv/bin/pytest tests/unit/features/ tests/integration/features/ -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 15 items

tests/unit/features/test_exploration.py::test_exp_01_mandatory_scope_and_warnings PASSED [  6%]
tests/unit/features/test_exploration.py::test_exp_06_predictor_redundancy_and_sorting PASSED [ 13%]
tests/unit/features/test_exploration.py::test_exp_08_input_validation PASSED [ 20%]
tests/unit/features/test_exploration.py::test_classification_feature_associations PASSED [ 26%]
tests/unit/features/test_feature_types.py::test_scope_and_warnings_constants PASSED [ 33%]
tests/unit/features/test_feature_types.py::test_association_measure_immutability_and_validation PASSED [ 40%]
tests/unit/features/test_feature_types.py::test_redundancy_pair_immutability_and_validation PASSED [ 46%]
tests/unit/features/test_feature_types.py::test_report_scope_enforcement PASSED [ 53%]
tests/unit/features/test_feature_types.py::test_exp_07_roundtrip_serialization PASSED [ 60%]
tests/unit/features/test_stats.py::test_exp_02_pearson_and_spearman_continuous PASSED [ 66%]
tests/unit/features/test_stats.py::test_exp_03_correlation_ratio_eta PASSED [ 73%]
tests/unit/features/test_stats.py::test_exp_04_cramers_v PASSED          [ 80%]
tests/unit/features/test_stats.py::test_exp_05_degeneracy_and_undefined_nan PASSED [ 86%]
tests/integration/features/test_features_integration.py::test_exp_08_end_to_end_pipeline PASSED [ 93%]
tests/integration/features/test_features_integration.py::test_xcut_02_runtime_purity_subprocess PASSED [100%]

============================== 15 passed in 0.21s ==============================
```

### 2.2 Suíte Completa de Regressão

Execução no ambiente `.venv` (`.venv/bin/pytest tests/ -q`):

```text
208 passed in 2.52s
```

---

## 3. Conformidade com Decisões Arquiteturais

1. **XCUT-02 (Zero External Runtime Dependencies beyond NumPy):**
   - Nenhuma biblioteca estatística externa (`scipy`, `sklearn`, `statsmodels`) utilizada no módulo de features. Validado via teste de isolamento em subprocesso (`test_xcut_02_runtime_purity_subprocess`).
2. **CA-E2-01 / RF2.1 (Rotulagem Exploratória Mandatória e Prevenção de Data Leakage):**
   - `ExploratoryFeatureReport` exige imutavelmente `scope = "EXPLORATORY_FULL_DATA"` e incorpora os 3 avisos metodológicos mandatórios, impedindo seu uso como critério de seleção automatizada pré-partição.
3. **ADR-005 / CA-GER-03 (Tratamento Rigoroso de Degenerescência):**
   - Variância zero, colunas constantes e divisões por zero retornam `(nan, MetricStatus.UNDEFINED_NAN)` sem exceções não tratadas e sem substituição silenciosa por `0.0`.
4. **ADR-007 / ADR-008 (Hashing Determinístico e Imutabilidade):**
   - `ExploratoryFeatureReport`, `AssociationMeasure` e `RedundancyPair` são imutáveis (`frozen=True`, `slots=True`, `MappingProxyType`), preservando o `dataset_hash` da visão e serializando deterministicamente para JSON RFC 8259.
