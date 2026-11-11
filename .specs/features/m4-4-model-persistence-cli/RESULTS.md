# Registro de Validação e Aceite — Marco M4.4 (Persistência de Modelos, Portão de Validação e CLI)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M4.4 (`m4-4-model-persistence-cli`)  
> **Data de Validação:** 11 de Novembro de 2026  
> **Commit de Implementação:** [`7dd8556`](https://github.com/alexandrerangel/experimental-ml-framework/commit/7dd8556)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) e CLI nativa | Validado via subprocesso isolado no ambiente `.venv` (`XCUT-02`, `CLI-10`) | **APROVADO** |
| **Testes Unitários Automatizados** | 18 testes em `tests/unit/models/`, `stages/` e `cli/` (C1 a C18) | 18 testes de modelos aprovados (100% de sucesso) | **APROVADO** |
| **Testes de Integração e Invariantes** | 3 testes em `tests/integration/models/` (C19 a C21) | 3 testes de integração e CLI aprovados (100% de sucesso) | **APROVADO** |
| **Testes de Regressão Geral** | 342 testes em `pytest tests/` | 342 testes aprovados (100% de sucesso em 4.98s) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria independente | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (7 capacidades + cenário E2E) | Executado com sucesso via interfaces públicas e CLI | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Testes do Subsistema de Modelos (Unitários e Integração M4.4)

Execução realizada no ambiente virtual `.venv` (`.venv/bin/pytest tests/unit/models/test_models_codecs.py tests/unit/models/test_models_resolution.py tests/unit/models/test_models_storage.py tests/unit/stages/test_models_stage_gate.py tests/unit/cli/test_cli_models_validate.py tests/unit/cli/test_cli_models_verify.py tests/integration/models/test_models_cli_integration.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 21 items

tests/unit/models/test_models_codecs.py::test_m44_01_01_models_catalog_dataclass PASSED [  4%]
tests/unit/models/test_models_codecs.py::test_m44_01_02_models_catalog_to_dict PASSED [  9%]
tests/unit/models/test_models_codecs.py::test_m44_01_03_models_catalog_from_dict PASSED [ 14%]
tests/unit/models/test_models_resolution.py::test_m44_02_01_resolve_builtin_baselines PASSED [ 19%]
tests/unit/models/test_models_resolution.py::test_m44_02_02_resolve_dotted_import_path PASSED [ 23%]
tests/unit/models/test_models_resolution.py::test_m44_02_03_resolve_invalid_reference_raises PASSED [ 28%]
tests/unit/models/test_models_storage.py::test_m44_03_01_save_and_load_roundtrip PASSED [ 33%]
tests/unit/models/test_models_storage.py::test_m44_03_02_save_overwrite_guard PASSED [ 38%]
tests/unit/models/test_models_storage.py::test_m44_03_03_load_missing_or_corrupt PASSED [ 42%]
tests/unit/stages/test_models_stage_gate.py::test_m44_04_01_verify_models_gate_valid PASSED [ 47%]
tests/unit/stages/test_models_stage_gate.py::test_m44_04_02_verify_models_gate_missing_or_empty PASSED [ 52%]
tests/unit/stages/test_models_stage_gate.py::test_m44_04_03_verify_models_gate_unmet_precondition PASSED [ 57%]
tests/unit/cli/test_cli_models_validate.py::test_m44_05_01_models_validate_success PASSED [ 61%]
tests/unit/cli/test_cli_models_validate.py::test_m44_05_02_models_validate_overwrite_error PASSED [ 66%]
tests/unit/cli/test_cli_models_validate.py::test_m44_05_03_models_validate_invalid_input PASSED [ 71%]
tests/unit/cli/test_cli_models_verify.py::test_m44_06_01_models_verify_success PASSED [ 76%]
tests/unit/cli/test_cli_models_verify.py::test_m44_06_02_models_verify_gate_failure PASSED [ 80%]
tests/unit/cli/test_cli_models_verify.py::test_m44_06_03_models_verify_missing_dir PASSED [ 85%]
tests/integration/models/test_models_cli_integration.py::test_m44_07_01_cli_parser_registration PASSED [ 90%]
tests/integration/models/test_models_cli_integration.py::test_m44_07_02_cli_import_purity PASSED [ 95%]
tests/integration/models/test_models_cli_integration.py::test_m44_07_03_e2e_cli_subprocess PASSED [100%]

============================== 21 passed in 0.54s ==============================
```

### 2.2 Suíte de Regressão Global

Execução de todos os 342 testes automatizados do framework (`.venv/bin/pytest tests/ -v`):

```text
============================= 342 passed in 4.98s ==============================
```

---

## 3. Julgamento da Verificação Independente TLC

- **Documento de Auditoria:** `.specs/features/m4-4-model-persistence-cli/verification.md`
- **Papel:** Verificador Independente (`author != verifier`).
- **Veredito:** `PASS`
- **Resultados de Checks:** 21 checks auditados (`C1` a `C21`), todos com status `Holds: yes`.
- **Achados (*Findings*):** `None`
- **Sondagens Adicionais do Verificador:**
  - Corrupção de JSON sintático e arquivos incompletos: captura estrita e deterministicamente tipada (`JSONDecodeError` e `ConfigurationError`).
  - Omissão de campos mandatórios em `model_spec_from_dict`: validação estrita gerando `ConfigurationError`.
  - Salvaguarda de sobrescrita atômica em `save_models_catalog`: garantia contra deleção/sobrescrita não autorizada (`overwrite=False`).
  - Pré-condição do portão de modelos (`verify_models_gate`): verificação obrigatória de que a Etapa 1 está concluída e com status `READY`.
  - Pureza da CLI (`cmd_models.py`): inspeção estática AST e validação dinâmica em subprocesso isolado comprovando zero dependências pesadas carregadas em `sys.modules`.

---

## 4. Execução do Roteiro de Aceitação do Consumidor (`ACCEPTANCE.md`)

O roteiro operacional de aceitação foi executado utilizando **exclusivamente as interfaces públicas** da biblioteca e os pontos de entrada CLI:

| Seção do Roteiro | Capacidade Avaliada | Resultado Observado | Status |
| :--- | :--- | :--- | :---: |
| **Seção 1** | Exportações Públicas e CLI Help | 6 símbolos de persistência/código exportados em `models.__all__`, portão em `stages` e CLI help funcional | **APROVADO** |
| **Seção 2.1** | Modelo ModelsCatalog e Codecs (`MPC-01`) | Dataclass imutável com slots, MappingProxyType, serialização/desserialização sem perda | **APROVADO** |
| **Seção 2.2** | Resolução de Fábricas (`MPC-02`) | Baselines nativos canônicos resolvidos, formato `module:qualname` suportado, erros lançando `ConfigurationError` | **APROVADO** |
| **Seção 2.3** | Armazenamento Atômico (`MPC-03`) | Escrita atômica com arquivo temporário, guarda contra sobrescrita e recarregamento íntegro | **APROVADO** |
| **Seção 2.4** | Portão de Modelos (`MPC-04`) | Exigência da Etapa 1 em READY, rejeição de catálogo vazio ou ausente, validação estrutural | **APROVADO** |
| **Seção 2.5** | CLI `models validate` (`MPC-05`) | Validação e escrita atômica em `configuration/models.json`, saída estruturada, código 0 (sucesso) e código 2 (erro) | **APROVADO** |
| **Seção 2.6** | CLI `models verify` (`MPC-06`) | Verificação não-interativa do portão de modelos com códigos 0 e 2 | **APROVADO** |
| **Seção 2.7** | Pureza de Importação (`MPC-07`) | AST e runtime comprovam zero módulos proibidos no topo de `cmd_models.py` (`CLI-10`) | **APROVADO** |
| **Seção 3** | Cenário Integrado Ponta a Ponta | Script bash E2E simulando criação de experimento, validação, verificação e proteção de sobrescrita executado com êxito | **APROVADO** |

---

## 5. Análise de Rastreabilidade de Requisitos

| Requisito | Descrição Resumida | Critérios de Aceite | Evidência Comprobatória | Status |
| :--- | :--- | :--- | :--- | :---: |
| `MPC-01` | Modelo ModelsCatalog e Codecs JSON | AC-M44-01-01 a 03 | `test_models_codecs.py` (C1 a C3) | **APROVADO** |
| `MPC-02` | Resolução Declarativa de Fábricas de Estimadores | AC-M44-02-01 a 03 | `test_models_resolution.py` (C4 a C6) | **APROVADO** |
| `MPC-03` | Persistência Atômica e Carregamento de Catálogo | AC-M44-03-01 a 03 | `test_models_storage.py` (C7 a C9) | **APROVADO** |
| `MPC-04` | Portão de Estágio de Modelos (`verify_models_gate`) | AC-M44-04-01 a 03 | `test_models_stage_gate.py` (C10 a C12) | **APROVADO** |
| `MPC-05` | Subcomando CLI `expml models validate` | AC-M44-05-01 a 03 | `test_cli_models_validate.py` (C13 a C15) | **APROVADO** |
| `MPC-06` | Subcomando CLI `expml models verify` | AC-M44-06-01 a 02 | `test_cli_models_verify.py` (C16 a C18) | **APROVADO** |
| `MPC-07` | Registro na CLI, Pureza de Importação e Suíte E2E | AC-M44-07-01 a 02 | `test_models_cli_integration.py` (C19 a C21) | **APROVADO** |

---

## 6. Decisão Formal de Aceite do Marco

Com base nas evidências coletadas e na verificação independente:
1. Todos os 7 requisitos funcionais (`MPC-01` a `MPC-07`) e seus 19 critérios de aceitação foram rigorosamente implementados e verificados.
2. A suíte de testes automatizados do marco M4.4 conta com 21 testes aprovados (18 unitários e 3 de integração) sem qualquer regressão na suíte global do projeto (342 testes aprovados).
3. A verificação formal pelo protocolo TLC (`validate_verification.py --strict`) atesta 0 erros e 0 avisos.
4. O roteiro de validação operacional do consumidor (`ACCEPTANCE.md`) foi executado e homologado com êxito exclusivo via API pública e comandos CLI.
5. As restrições de arquitetura (`CLI-06` a `CLI-11`, `STORE-03`, `STORE-05`, `XCUT-01`, `XCUT-02`) foram integralmente respeitadas.

**Decisão:** **APROVADO**
