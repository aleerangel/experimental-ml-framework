# Registro de Validação e Aceite — Marco M5.3 (Consolidação OOF e Portão da Etapa 4)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M5.3 (`m5-3-oof-consolidation-stage-gate`)  
> **Data de Validação:** 12 de Novembro de 2026  
> **Commit de Implementação:** [`9083fdc`](https://github.com/alexandrerangel/experimental-ml-framework/commit/9083fdc)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.5.4, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via subprocesso isolado no ambiente `.venv` (`XCUT-02`) | **APROVADO** |
| **Testes Unitários de OOF e Portões** | 24 testes unitários cobrindo C1 a C22 | 24 testes unitários específicos aprovados (100% de sucesso) | **APROVADO** |
| **Testes de Integração e Invariantes** | 3 testes em `tests/integration/orchestration/test_oof_integration.py` (C23 a C25) | 3 testes de integração transversal aprovados | **APROVADO** |
| **Testes de Regressão Global** | 438 testes em `pytest tests/` | 438 testes aprovados (100% de sucesso) | **APROVADO** |
| **Verificação Independente TLC** | Auditoria por subagente independente (`author != verifier`) | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Sondagem Adversarial Independente** | 3 cenários adversariais (variância nula, artefatos faltantes, cobertura fracionária) | Todos os 3 testes adversariais aprovados | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Testes do Marco M5.3

Execução realizada no ambiente virtual `.venv` (`.venv/bin/pytest tests/unit/orchestration/test_oof* tests/unit/stages/test_stage_runs_gate.py tests/integration/orchestration/test_oof_integration.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 27 items

tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_01_consolidate_aggregates_records PASSED [  3%]
tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_02_canonical_sorting_by_obs_id PASSED [  7%]
tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_03_multi_fold_committee_statistics PASSED [ 11%]
tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_04_single_fold_prediction_preservation PASSED [ 14%]
tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_05_classification_probability_pooling PASSED [ 18%]
tests/unit/orchestration/test_oof_aggregation.py::test_oof_empty_records_rejection PASSED [ 22%]
tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_01_partial_coverage_on_fold_failure PASSED [ 25%]
tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_02_missing_observations_warning PASSED [ 29%]
tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_03_total_failure_raises_integrity_error PASSED [ 33%]
tests/unit/orchestration/test_oof_metrics.py::test_m53_02_01_pooled_oof_metrics_evaluation PASSED [ 37%]
tests/unit/orchestration/test_oof_metrics.py::test_m53_02_02_fold_aggregation_statistics PASSED [ 40%]
tests/unit/orchestration/test_oof_metrics.py::test_m53_02_03_undefined_nan_resilience PASSED [ 44%]
tests/unit/orchestration/test_oof_metrics.py::test_m53_02_04_metrics_scopes_distinction PASSED [ 48%]
tests/unit/orchestration/test_oof_storage.py::test_m53_03_01_save_oof_predictions_atomic PASSED [ 51%]
tests/unit/orchestration/test_oof_storage.py::test_m53_03_02_load_oof_predictions PASSED [ 55%]
tests/unit/orchestration/test_oof_storage.py::test_m53_03_03_codecs_roundtrip_fidelity PASSED [ 59%]
tests/unit/orchestration/test_oof_storage.py::test_m53_03_04_save_oof_no_overwrite_protection PASSED [ 62%]
tests/unit/orchestration/test_oof_storage.py::test_oof_invariants_validation PASSED [ 66%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_01_upstream_gates_verification PASSED [ 70%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_02_missing_or_corrupt_state_raises PASSED [ 74%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_03_non_terminal_cell_status_raises PASSED [ 77%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_04_missing_cell_artifact_raises PASSED [ 81%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_05_cross_hashes_mismatch_raises PASSED [ 85%]
tests/unit/stages/test_stage_runs_gate.py::test_m53_04_06_valid_runs_gate_returns_summary PASSED [ 88%]
tests/integration/orchestration/test_oof_integration.py::test_m53_06_01_public_api_exports PASSED [ 92%]
tests/integration/orchestration/test_oof_integration.py::test_m53_06_02_end_to_end_matrix_to_oof_gate PASSED [ 96%]
tests/integration/orchestration/test_oof_integration.py::test_m53_06_03_runtime_purity_xcut_02 PASSED [100%]

============================== 27 passed in 1.84s ==============================
```

### 2.2 Suíte de Regressão Global

```text
438 passed in 5.66s
```

---

## 3. Registro do Verificador Independente

- **Veredito:** `PASS`
- **Sondagens Realizadas:**
  1. Comitê com contagens mistas e variância nula ($\hat{\sigma}_i = 0.0$).
  2. Rejeição de portão quando artefato físico `oof_*.json` ou `cell_*.json` é deletado.
  3. Cálculo fracionário de cobertura (`coverage = 0.2`) e avisos detalhados sob `FAULT_TOLERANT`.
- **Apontamentos:** Nenhum (`None`). Todos os 25 critérios C1 a C25 sustentam suas garantias formais.

---

## 4. Decisão Formal de Aceite

O Marco M5.3 cumpre integralmente os requisitos arquiteturais, as premissas de rastreabilidade (ORCH-15 a ORCH-21) e as restrições transversais (`XCUT-02`, `STORE-01`, `ADR-008`).

**Decisão:** `APROVADO`
