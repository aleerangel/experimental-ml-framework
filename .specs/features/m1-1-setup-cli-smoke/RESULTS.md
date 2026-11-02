# Registro de Validação e Aceite — Marco M1.1

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M1.1 (`m1-1-setup-cli-smoke`)  
> **Data de Validação:** 31 de Outubro de 2026 (atualizado em 02 de Novembro de 2026)  
> **Commit de Implementação:** [`0840603`](https://github.com/alexandrerangel/experimental-ml-framework/commit/0840603)  
> **Commit de Integração na Main:** [`9ed7e01`](https://github.com/alexandrerangel/experimental-ml-framework/commit/9ed7e01)  
> **Ambiente Computacional:** Linux 6.17.5-arch1-1 (x86_64), Python 3.12.15, Hatchling 1.27.0, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Empacotamento** | `pip install -e ".[dev]"` | Executado com sucesso no `.venv` | **APROVADO** |
| **Suíte de Fumaça Automatizada** | 12 testes em `tests/test_smoke.py` | 12 testes aprovados (100%) | **APROVADO** |
| **Interfaces de Linha de Comando (CLI)** | `--version`, `--help`, código 2 | Testado via subprocesso em `test_smoke.py` | **APROVADO** |
| **Homologação Manual** | Roteiro `ACCEPTANCE.md` | Testes automatizados cobrem a CLI; homologação manual não executada | **PENDENTE DE HOMOLOGAÇÃO MANUAL** |

---

## 2. Evidências de Testes Automatizados

Execução realizada no interpretador do ambiente virtual (`.venv/bin/pytest tests/test_smoke.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.15, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collected 12 items

tests/test_smoke.py::test_pyproject_metadata PASSED                      [  8%]
tests/test_smoke.py::test_package_version PASSED                         [ 16%]
tests/test_smoke.py::test_dev_dependencies PASSED                        [ 25%]
tests/test_smoke.py::test_cli_entrypoint_registered PASSED               [ 33%]
tests/test_smoke.py::test_editable_install_and_cli_on_path PASSED        [ 41%]
tests/test_smoke.py::test_cli_version_flag PASSED                        [ 50%]
tests/test_smoke.py::test_cli_help_flag PASSED                           [ 58%]
tests/test_smoke.py::test_cli_invalid_argument PASSED                    [ 66%]
tests/test_smoke.py::test_cli_dependencies_pure_stdlib PASSED            [ 75%]
tests/test_smoke.py::test_smoke_discovery PASSED                         [ 83%]
tests/test_smoke.py::test_version_non_empty PASSED                       [ 91%]
tests/test_smoke.py::test_cli_observable_outcomes PASSED                 [100%]

============================== 12 passed in 0.11s ==============================
```

- **Evidência Mecânica Registrada:** Arquivo [`.specs/features/m1-1-setup-cli-smoke/proofs.md`](./proofs.md).

---

## 3. Verificações Manuais de Aceitação do Consumidor

| Verificação do Roteiro ACCEPTANCE.md | Evidência Existente | Status |
| :--- | :--- | :---: |
| `which expml` localiza o executável | Coberto pelo teste `test_editable_install_and_cli_on_path` | **Comprovado por Automação** |
| `expml --version` imprime `expml 0.1.0.dev0` | Coberto pelo teste `test_cli_version_flag` | **Comprovado por Automação** |
| `expml --help` imprime texto de ajuda (exit 0) | Coberto pelo teste `test_cli_help_flag` | **Comprovado por Automação** |
| `expml` sem argumentos exibe ajuda (exit 0) | Coberto pelo teste `test_cli_observable_outcomes` | **Comprovado por Automação** |
| `expml --flag-invalida` imprime erro (exit 2) | Coberto pelo teste `test_cli_invalid_argument` | **Comprovado por Automação** |
| Importação programática via interpretador Python | Coberto pelo teste `test_package_version` | **Comprovado por Automação** |
| Homologação manual do roteiro de aceitação | Procedimento documentado em `ACCEPTANCE.md` | **PENDENTE DE HOMOLOGAÇÃO MANUAL** |

---

## 4. Problemas e Defeitos Encontrados

- **Problemas Detectados:** Nenhum defeito funcional ou inconsistência técnica identificada.
- **Ressalvas Técnicas:** Nenhuma. A CLI opera com zero dependências externas de terceiros, conforme exigido pela especificação.

---

## 5. Decisão Final de Aceite do Marco M1.1

- **Veredito de Engenharia:** **IMPLEMENTAÇÃO VERIFICADA POR TESTES AUTOMATIZADOS**
- **Veredito de Homologação Manual:** **PENDENTE DE HOMOLOGAÇÃO MANUAL**
- **Justificativa:** Os 12 critérios técnicos automatizados foram atendidos e validados no commit `0840603` e preservados em `9ed7e01`. Conforme o processo de aceite de marcos, a decisão final permanece pendente até a execução da homologação manual.

