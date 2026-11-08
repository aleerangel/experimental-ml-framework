# Registro de Validação e Aceite — Marco M2.5 (CLI End-to-End Acceptance)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M2.5 (`m2-5-cli-end-to-end`)  
> **Data de Validação:** 07 de Novembro de 2026  
> **Commit de Implementação:** [`da0ba88`](https://github.com/alexandrerangel/experimental-ml-framework/commit/da0ba88)  
> **Commit de Verificação:** [`5b67ef6`](https://github.com/alexandrerangel/experimental-ml-framework/commit/5b67ef6)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Ponto de Entrada CLI** | Ponto de entrada binário `expml` registrado via `pyproject.toml` | Executado diretamente via `.venv/bin/expml` e subprocessos | **APROVADO** |
| **Testes Unitários Automatizados** | 13 testes unitários cobrindo despachante, erros, perfilamento e partição | 13 testes unitários aprovados (100%) | **APROVADO** |
| **Testes de Integração e Homologação** | 1 teste de integração por subprocesso com reprodutibilidade determinística | 1 teste aprovado com equivalência bit a bit | **APROVADO** |
| **Pureza Arquitetural (`CLI-10`)** | Zero imports de `numpy` ou `hashlib` em `src/experimental_ml/cli/` | Verificado via AST traversal nos 4 módulos CLI | **APROVADO** |
| **Higiene de Saída (`CLI-11`)** | Zero digests hexadecimais de 64 caracteres em stdout e stderr | Verificado por expressão regular em todos os fluxos | **APROVADO** |
| **Testes de Regressão Geral** | 176 testes em `pytest tests/` | 176 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `check_proofs.py` e Verificador Independente subagente | Aprovado com veredito `PASS` (10/10 checks) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (5 subcomandos e cenários de erro) | Executado e validado ponta a ponta | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Verificação de Provas Automatizadas (`check_proofs.py`)

```text
HEAD: 5b67ef6
Tree: clean
Shell: /bin/sh
Result: 10 pass, 0 fail
```

### 2.2 Suíte de Testes Unitários e de Integração da CLI

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 14 items

tests/unit/cli/test_cli_main.py::test_cli_09_base_cli_compatibility_and_help PASSED [  7%]
tests/unit/cli/test_cli_main.py::test_cli_06_domain_error_handling_and_exit_code_2 PASSED [ 14%]
tests/unit/cli/test_cli_main.py::test_cli_10_architectural_pure_cli_no_numpy_no_hashlib PASSED [ 21%]
tests/unit/cli/test_cli_main.py::test_cli_11_no_hash_digests_in_output PASSED [ 28%]
tests/unit/cli/test_cmd_data.py::test_cli_01_data_profile_success PASSED [ 35%]
tests/unit/cli/test_cmd_data.py::test_cli_03_data_sanitize_incomplete_plan_rejected PASSED [ 42%]
tests/unit/cli/test_cmd_data.py::test_cli_02_data_sanitize_ready_plan PASSED [ 50%]
tests/unit/cli/test_cmd_data.py::test_cli_08_data_profile_force_flag_behavior PASSED [ 57%]
tests/unit/cli/test_cmd_partition.py::test_cli_04_partition_build_success PASSED [ 64%]
tests/unit/cli/test_cmd_partition.py::test_cli_04_partition_build_seed_override PASSED [ 71%]
tests/unit/cli/test_cmd_partition.py::test_cli_05_partition_verify_clean_and_tampered PASSED [ 78%]
tests/unit/cli/test_cmd_partition.py::test_cli_07_upstream_gate_missing_blocked PASSED [ 85%]
tests/unit/cli/test_cmd_partition.py::test_cli_08_partition_build_force_flag_behavior PASSED [ 92%]
tests/integration/test_cli_end_to_end_integration.py::test_cli_12_end_to_end_subprocess_acceptance_scenario PASSED [100%]

============================== 14 passed in 1.45s ==============================
```

### 2.3 Regressão Global do Repositório

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
collected 176 items

============================= 176 passed in 2.55s ==============================
```

---

## 3. Conclusão da Fase

Todas as diretrizes do marco **M2.5** e do macro-marco **M2 (Stage 1 Data Pipeline)** foram rigorosamente atendidas. A camada CLI fornece orquestração desacoplada, tratamento uniforme de erros sem vazamento de tracebacks ou hashes criptográficos, e reprodutibilidade com garantia de invariantes e determinismo bit a bit.
