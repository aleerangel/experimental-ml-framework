# Registro de Validação e Aceite — Marco M6.1 (Consolidação Descritiva, Cobertura e Adequação Metodológica)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M6.1 (`m6-1-descriptive-consolidation-suitability`)  
> **Data de Validação:** 16 de Novembro de 2026  
> **Commit de Implementação / Prova:** [`d005a27`](https://github.com/alexandrerangel/experimental-ml-framework/commit/d005a27)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.5.4, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via subprocesso isolado no ambiente `.venv` (`XCUT-02`) | **APROVADO** |
| **Testes Unitários de Estatística Descritiva** | 31 testes unitários cobrindo C1 a C26 | 31 testes unitários específicos aprovados (100% de sucesso) | **APROVADO** |
| **Testes de Integração e Invariantes** | 3 testes em `tests/integration/statistics/test_statistics_integration.py` (C27 a C29) | 3 testes de integração transversal e isolamento de runtime aprovados | **APROVADO** |
| **Testes de Regressão Global** | 505 testes em `pytest tests/` | 505 testes aprovados (100% de sucesso) | **APROVADO** |
| **Verificação Independente TLC** | Auditoria por subagente independente (`author != verifier`) | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Sondagem Adversarial Independente** | 3 cenários adversariais (cobertura nula, variância de fold único, isolamento de holdout) | Todos os 3 testes adversariais aprovados | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Testes do Marco M6.1

Execução realizada no ambiente virtual `.venv` (`.venv/bin/pytest tests/unit/statistics/ tests/integration/statistics/ -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 34 items

tests/unit/statistics/test_statistics_types.py::test_m61_01_domain_dataclasses_frozen_immutability PASSED [  2%]
tests/unit/statistics/test_statistics_types.py::test_m61_01_configuration_summary_collection_immutability PASSED [  5%]
tests/unit/statistics/test_statistics_types.py::test_m61_01_configuration_summary_validation PASSED [  8%]
tests/unit/statistics/test_statistics_types.py::test_m61_01_aggregated_metric_stats_validations PASSED [ 11%]
tests/unit/statistics/test_statistics_types.py::test_m61_01_method_suitability_report_validation PASSED [ 14%]
tests/unit/statistics/test_statistics_types.py::test_m61_01_pairwise_eligibility_report_validation PASSED [ 17%]
tests/unit/statistics/test_statistics_types.py::test_m61_01_incomplete_comparison_policy_enum PASSED [ 20%]
tests/unit/statistics/test_statistics_types.py::test_m61_01_coverage_status_enum PASSED [ 23%]
tests/unit/statistics/test_statistics_types.py::test_m61_01_types_module_all_export PASSED [ 26%]
tests/unit/statistics/test_stage5_entry.py::test_m61_02_valid_runs_summary_passes_validation PASSED [ 29%]
tests/unit/statistics/test_stage5_entry.py::test_m61_02_cancelled_cells_recognized_as_terminal PASSED [ 32%]
tests/unit/statistics/test_stage5_entry.py::test_m61_02_non_terminal_cells_raise_contract_violation PASSED [ 35%]
tests/unit/statistics/test_stage5_entry.py::test_m61_02_tampered_execution_state_raises_contract_violation PASSED [ 38%]
tests/unit/statistics/test_consolidation.py::test_m61_03_per_configuration_fold_accounting PASSED [ 41%]
tests/unit/statistics/test_consolidation.py::test_m61_03_coverage_status_classification PASSED [ 44%]
tests/unit/statistics/test_consolidation.py::test_m61_03_sample_statistics_with_sample_variance PASSED [ 47%]
tests/unit/statistics/test_consolidation.py::test_m61_03_single_fold_variance_handling PASSED [ 50%]
tests/unit/statistics/test_consolidation.py::test_m61_03_zero_valid_metrics_resilience PASSED [ 52%]
tests/unit/statistics/test_consolidation.py::test_m61_03_partial_fold_failures_accounting PASSED [ 55%]
tests/unit/statistics/test_consolidation.py::test_m61_03_feature_stability_jaccard PASSED [ 58%]
tests/unit/statistics/test_consolidation.py::test_m61_03_oof_pooled_metrics_preservation PASSED [ 61%]
tests/unit/statistics/test_consolidation.py::test_m61_03_deterministic_sorting_invariants PASSED [ 64%]
tests/unit/statistics/test_suitability.py::test_m61_04_cv_suitability_evaluation PASSED [ 67%]
tests/unit/statistics/test_suitability.py::test_m61_04_holdout_only_suitability_evaluation PASSED [ 70%]
tests/unit/statistics/test_suitability.py::test_m61_04_cv_plus_holdout_suitability_evaluation PASSED [ 73%]
tests/unit/statistics/test_suitability.py::test_m61_04_training_overlap_ratio_calculation PASSED [ 76%]
tests/unit/statistics/test_suitability.py::test_m61_04_wilcoxon_sample_size_diagnostics PASSED [ 79%]
tests/unit/statistics/test_suitability.py::test_m61_04_pairwise_eligibility_both_valid PASSED [ 82%]
tests/unit/statistics/test_suitability.py::test_m61_04_pairwise_eligibility_require_complete_policy PASSED [ 85%]
tests/unit/statistics/test_suitability.py::test_m61_04_pairwise_eligibility_use_common_folds_policy PASSED [ 88%]
tests/unit/statistics/test_suitability.py::test_m61_04_pairwise_eligibility_zero_overlap_or_no_coverage PASSED [ 91%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_public_api_exports PASSED [ 94%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_end_to_end_lifecycle PASSED [ 97%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_runtime_purity_xcut02 PASSED [100%]

============================== 34 passed in 0.31s ==============================
```

### 2.2 Suíte de Regressão Global

```text
505 passed in 6.42s
```

---

## 3. Registro do Verificador Independente

- **Veredito:** `PASS`
- **Sondagens Realizadas:**
  1. Cobertura nula (`CoverageStatus.NO_COVERAGE`) preservando configurações sem inventar métricas.
  2. Tratamento rigoroso de fold único (`std = None`, sem variância artificialmente nula).
  3. Isolamento completo entre dobras de desenvolvimento ($J = \text{len}(\text{folds})$) e partição de holdout final no regime `CV_AND_HOLDOUT`.
- **Apontamentos:** Nenhum (`None`). Todos os 29 critérios de aceitação C1 a C29 sustentam suas garantias formais.

---

## 4. Decisão Formal de Aceite

O Marco M6.1 cumpre integralmente os requisitos arquiteturais, as premissas de rastreabilidade (STAT-01 a STAT-07) e as restrições transversais (`XCUT-02`, `RNF02`).

**Decisão:** `APROVADO`
