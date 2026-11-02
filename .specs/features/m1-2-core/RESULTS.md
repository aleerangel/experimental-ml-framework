# Registro de Validação e Aceite — Marco M1.2

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M1.2 (`m1-2-core`)  
> **Data de Validação:** 31 de Outubro de 2026 (atualizado em 02 de Novembro de 2026)  
> **Commit de Implementação:** [`479ee8d`](https://github.com/alexandrerangel/experimental-ml-framework/commit/479ee8d)  
> **Commit de Documentação:** [`966a9b5`](https://github.com/alexandrerangel/experimental-ml-framework/commit/966a9b5)  
> **Commit de Integração na Main:** [`9ed7e01`](https://github.com/alexandrerangel/experimental-ml-framework/commit/9ed7e01)  
> **Ambiente Computacional:** Linux 6.17.5-arch1-1 (x86_64), Python 3.12.15, NumPy 2.5.4, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | `pip install -e ".[dev]"` com NumPy | Instalado e validado (`numpy 2.5.4`) | **APROVADO** |
| **Testes Unitários Automatizados** | 18 testes em `tests/unit/test_core.py` | 18 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 30 testes em `pytest tests/` | 30 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Homologação Manual** | Roteiro `ACCEPTANCE.md` (6 itens + cenário) | Executada e aprovada conforme roteiro | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte Unitária do Módulo Core (`tests/unit/test_core.py`)

Execução realizada no interpretador do ambiente virtual (`.venv/bin/pytest tests/unit/test_core.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.15, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collected 18 items

tests/unit/test_core.py::test_identifier_types_immutable PASSED          [  5%]
tests/unit/test_core.py::test_identifier_validation_non_empty PASSED     [ 11%]
tests/unit/test_core.py::test_identifier_invalid_value_error PASSED      [ 16%]
tests/unit/test_core.py::test_task_type_and_execution_status_enums PASSED [ 22%]
tests/unit/test_core.py::test_finding_metric_aggregation_enums PASSED    [ 27%]
tests/unit/test_core.py::test_metric_status_and_error_policy_enums PASSED [ 33%]
tests/unit/test_core.py::test_derive_seeds_returns_tuple PASSED          [ 38%]
tests/unit/test_core.py::test_derive_seeds_determinism PASSED            [ 44%]
tests/unit/test_core.py::test_spawn_child_seeds_validation PASSED        [ 50%]
tests/unit/test_core.py::test_config_hash_sha256_format PASSED           [ 55%]
tests/unit/test_core.py::test_config_hash_unicode_and_key_order PASSED   [ 61%]
tests/unit/test_core.py::test_config_hash_strict_types PASSED            [ 66%]
tests/unit/test_core.py::test_config_hash_special_floats PASSED          [ 72%]
tests/unit/test_core.py::test_dataset_hash_file_and_schema PASSED        [ 77%]
tests/unit/test_core.py::test_dataset_hash_in_memory PASSED              [ 83%]
tests/unit/test_core.py::test_dataset_hash_file_not_found PASSED         [ 88%]
tests/unit/test_core.py::test_make_finding_and_make_warning PASSED       [ 94%]
tests/unit/test_core.py::test_core_exceptions_and_finding_immutability PASSED [100%]

============================== 18 passed in 0.19s ==============================
```

- **Evidência Mecânica Registrada:** Arquivo [`.specs/features/m1-2-core/proofs.md`](./proofs.md).

### 2.2 Relatório do Verificador Independente TLC

- **Arquivo:** [`.specs/features/m1-2-core/verification.md`](./verification.md).
- **Veredito:** `PASS` (`author != verifier`).
- **Validação de Portão:** `python3 .agent/skills/tlc-spec-driven/scripts/validate_verification.py m1-2-core` finalizado com **0 erros e 0 avisos**.

---

## 3. Verificações Manuais de Aceitação do Consumidor

| Verificação do Roteiro ACCEPTANCE.md | Evidência Existente | Status |
| :--- | :--- | :---: |
| 2.1 Identificadores imutáveis e sanitizados | Coberto por `test_identifier_*` | **Comprovado por Automação** |
| 2.2 Enumerações canônicas e JSON nativo | Coberto por `test_*_enums` | **Comprovado por Automação** |
| 2.3 Derivação determinística de sementes | Coberto por `test_derive_seeds_*` | **Comprovado por Automação** |
| 2.4 Hashing canônico ADR-007 (`config_hash`) | Coberto por `test_config_hash_*` | **Comprovado por Automação** |
| 2.5 Hashing estrutural (`dataset_hash`) | Coberto por `test_dataset_hash_*` | **Comprovado por Automação** |
| 2.6 Diagnósticos e exceções formais | Coberto por `test_make_finding_*` | **Comprovado por Automação** |
| 3. Cenário integrado de ML | Executado e aprovado | **APROVADO** |
| Homologação manual do roteiro | Executada e confirmada sem divergências | **APROVADO** |

---

## 4. Problemas e Defeitos Encontrados

- **Problemas Detectados:** Nenhum defeito funcional ou quebra de contrato identificada.
- **Conformidade Arquitetural:** 100% de conformidade com ADR-002, ADR-007, ADR-008 e RNF01/RNF06/RNF07.

---

## 5. Decisão Final de Aceite do Marco M1.2

- **Veredito de Engenharia:** **IMPLEMENTAÇÃO CONCLUÍDA E VERIFICADA**
- **Veredito de Homologação Manual:** **APROVADO**
- **Decisão Final:** **APROVADO**
- **Justificativa:** Os 18 critérios de aceitação automatizados (CORE-01 a CORE-18) foram implementados, testados e verificados de forma independente. O roteiro de validação do consumidor (`ACCEPTANCE.md`) foi executado e aprovado, confirmando os comportamentos das interfaces públicas e o cenário integrado.

