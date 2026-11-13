# Registro de Validação e Aceite — Marco M5.4 (CLI Run End-to-End)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M5.4 (`m5-4-cli-run-end-to-end`)  
> **Data de Validação:** 12 de Novembro de 2026  
> **Commit de Implementação:** [`58d3406`](https://github.com/alexandrerangel/experimental-ml-framework/commit/58d3406)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.5.4, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via subprocesso isolado no ambiente `.venv` (`XCUT-02`, `CLI-10`) | **APROVADO** |
| **Testes Unitários de CLI** | 19 testes unitários cobrindo C1 a C19 | 19 testes específicos aprovados (100% de sucesso) | **APROVADO** |
| **Testes de Integração e Invariantes** | 3 testes em `tests/integration/cli/test_run_e2e.py` (C20 a C22) | 3 testes transversais de ciclo completo aprovados | **APROVADO** |
| **Testes de Regressão Global** | 460 testes em `pytest tests/` | 460 testes aprovados (100% de sucesso) | **APROVADO** |
| **Verificação Independente TLC** | Auditoria por subagente independente (`author != verifier`) | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Sondagem Adversarial Independente** | 3 cenários adversariais (limiares de workers, falha de portão upstream, célula pendente em resume) | Todos os 3 testes adversariais aprovados | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Testes do Marco M5.4

Execução realizada no ambiente virtual `.venv` (`.venv/bin/pytest tests/unit/cli/test_cli_run.py tests/integration/cli/test_run_e2e.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 22 items

tests/unit/cli/test_cli_run.py::test_m54_01_01_cli_run_help_and_subparsers PASSED [  4%]
tests/unit/cli/test_cli_run.py::test_m54_01_02_run_start_args_parsing PASSED [  9%]
tests/unit/cli/test_cli_run.py::test_m54_01_03_run_resume_args_parsing PASSED [ 13%]
tests/unit/cli/test_cli_run.py::test_m54_01_04_run_status_args_parsing PASSED [ 18%]
tests/unit/cli/test_cli_run.py::test_m54_01_05_run_verify_args_parsing PASSED [ 22%]
tests/unit/cli/test_cli_run.py::test_m54_02_01_run_start_default_execution PASSED [ 27%]
tests/unit/cli/test_cli_run.py::test_m54_02_02_run_start_custom_run_dir PASSED [ 31%]
tests/unit/cli/test_cli_run.py::test_m54_02_03_run_start_parallel_dispatch PASSED [ 36%]
tests/unit/cli/test_cli_run.py::test_m54_02_04_run_start_fail_fast PASSED [ 40%]
tests/unit/cli/test_cli_run.py::test_m54_02_05_run_start_no_oof PASSED   [ 45%]
tests/unit/cli/test_cli_run.py::test_m54_02_06_run_start_overwrite_protection PASSED [ 50%]
tests/unit/cli/test_cli_run.py::test_m54_03_01_run_resume_skips_completed PASSED [ 54%]
tests/unit/cli/test_cli_run.py::test_m54_03_02_run_resume_retry_failed PASSED [ 59%]
tests/unit/cli/test_cli_run.py::test_m54_03_03_run_status_read_only PASSED [ 63%]
tests/unit/cli/test_cli_run.py::test_m54_03_04_run_status_missing_state_returns_2 PASSED [ 68%]
tests/unit/cli/test_cli_run.py::test_m54_04_01_run_verify_valid_gate PASSED [ 72%]
tests/unit/cli/test_cli_run.py::test_m54_04_02_run_verify_corrupted_gate_returns_2 PASSED [ 77%]
tests/unit/cli/test_cli_run.py::test_m54_04_03_domain_errors_exit_code_2_no_traceback PASSED [ 81%]
tests/unit/cli/test_cli_run.py::test_m54_04_04_hash_suppression_cli_11 PASSED [ 86%]
tests/integration/cli/test_run_e2e.py::test_m54_05_01_e2e_cli_pipeline_lifecycle PASSED [ 90%]
tests/integration/cli/test_run_e2e.py::test_m54_05_02_e2e_cli_crash_recovery PASSED [ 95%]
tests/integration/cli/test_run_e2e.py::test_m54_05_03_cli_runtime_purity_xcut_02 PASSED [100%]

============================== 22 passed in 3.45s ==============================
```

### 2.2 Suíte de Regressão Global

```text
460 passed in 9.42s
```

---

## 3. Registro do Verificador Independente

- **Veredito:** `PASS`
- **Sondagens Realizadas:**
  1. Validação de limites de workers com `-j 0` e `-j -2` (tratado com `ConfigurationError` e código 2 sem traceback).
  2. Falha de portão upstream antes de `run start` e diretório inexistente em `run verify` (código 2 sem stacktrace).
  3. Retomada de célula em estado `PENDING` sem `--retry-failed` (conclusão com sucesso e aprovação no portão).
- **Apontamentos:** Nenhum (`None`). Todas as 22 verificações C1 a C22 sustentam suas garantias formais.

---

## 4. Decisão Formal de Aceite

O Sub-marco M5.4 cumpre integralmente os requisitos de interface de terminal (ORCH-22 a ORCH-28) e as diretrizes arquiteturais (`CLI-06` a `CLI-11`, `XCUT-02`). Conclui-se formalmente o **Marco M5 (Orquestração e Execução Matricial)** do framework.

**Decisão:** `APROVADO`
