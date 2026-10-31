# m1-1-setup-cli-smoke Specification

**Approved**: [written when the user approves - YYYY-MM-DD - user: "their words"]

## Problem Statement

O repositório `experimental-ml-framework` possui documentação de requisitos, arquitetura e contratos consolidados, porém não dispõe de arquivos de configuração de empacotamento, layout de pacotes, ponto de entrada de linha de comando ou suíte de testes de fumaça executável. Sem essa infraestrutura básica de empacotamento em Python, não é possível instalar o pacote em modo editável, executar testes automatizados via `pytest` ou invocar o comando de terminal `expml`.

## Goals

- [ ] Configurar o empacotamento padrão do projeto com `pyproject.toml` baseado em Hatchling (`hatchling.build`).
- [ ] Estruturar o layout físico em `src/experimental_ml/` e `src/experimental_ml/cli/`.
- [ ] Registrar e disponibilizar o comando CLI executável `expml` com suporte às opções `--version` e `--help` (`-h`).
- [ ] Fornecer teste de fumaça inicial em `tests/test_smoke.py` com descoberta e execução aprovada via `pytest`.
- [ ] Habilitar a instalação editável (`pip install -e .` e `pip install -e ".[dev]"`).

## Out of Scope

| Feature | Reason |
| --- | --- |
| Módulo funcional `core` (identificadores, `derive_seeds`, `config_hash`, `dataset_hash`, enums) | Pertence formalmente à sub-entrega M1.2. |
| Módulo funcional `metrics` (catálogo de métricas, `UNDEFINED_NAN`, funções vetorizadas) | Pertence formalmente à sub-entrega M1.3. |
| Subcomandos funcionais por etapa (`expml data`, `features`, `models`, `partition`, `run`, `stats`, `report`) | Pertencem aos Marcos M2 a M7; a CLI no M1.1 limita-se ao despachante base e opções `--version` e `--help`. |
| Implementação ou encapsulamento de modelos preditivos externos | Vedações arquiteturais permanentes do framework (ADR-001 e ADR-008). |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Build-backend | `hatchling.build` | Padrão moderno em projetos Python, compatível nativamente com layout `src/` e metadados padronizados. | y |
| Nome do pacote e distribuição | Distribuição: `experimental-ml-framework`; Pacote importável: `experimental_ml`; CLI: `expml` | Alinhado com `README.md`, `ESPECIFICACAO_REQUISITOS.md` e `ARQUITETURA_E_CONTRATOS.md`. | y |
| Versão de Python declarada | `requires-python = ">=3.10"` | Mantém a meta de compatibilidade de especificação do RNF06 sem afirmar suporte empírico ainda não testado. | y |
| Versão inicial do pacote | `0.1.0.dev0` | Convenção PEP 440 para desenvolvimento ativo anterior ao primeiro release. | y |
| Código de saída da CLI para erro de argumentos | Código de saída `2` | Padrão da biblioteca `argparse` e alinhado ao RNF07 (`0` sucesso, `1` falha, `2` erro de validação/argumento). | y |
| Grupo de dependências de teste | `[project.optional-dependencies]` com chave `dev = ["pytest>=7.0.0"]` | Permite instalação enxuta do núcleo sem dependências obrigatórias de desenvolvimento em ambientes mínimos. | y |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Configuração Inicial de Empacotamento e Layout de Código ⭐ MVP

**User Story**: Como desenvolvedor do framework, quero configurar o empacotamento com `pyproject.toml` e layout `src/experimental_ml/`, para que o projeto possa ser instalado em modo editável e importado de forma determinística.

**Why P1**: É o alicerce obrigatório de engenharia sem o qual nenhum código Python ou módulo subsequente pode ser testado ou instalado.

**Acceptance Criteria**:

1. The system SHALL define `pyproject.toml` specifying `hatchling.build` as the build backend, `experimental-ml-framework` as the distribution name, and declared `requires-python = ">=3.10"`.
2. The system SHALL declare the source code layout rooted at `src/experimental_ml/` exposing a top-level `__init__.py` with `__version__ = "0.1.0.dev0"`.
3. The system SHALL declare an optional development dependency group `dev` containing `pytest>=7.0.0` in `pyproject.toml`.
4. The system SHALL register the console script entrypoint `expml = "experimental_ml.cli.main:main"` in `pyproject.toml`.
5. WHEN installing the package via `pip install -e ".[dev]"` in a virtual environment, THEN the system SHALL install without errors and make the executable command `expml` directly functional on PATH outside direct python module execution.

**Independent Test**: Executar `pip install -e ".[dev]"` em um ambiente virtual e verificar que tanto `python -c "import experimental_ml; print(experimental_ml.__version__)"` quanto a invocação direta de `expml --version` executam com sucesso.

---

### P1: Ponto de Entrada da Interface de Linha de Comando (CLI Base) ⭐ MVP

**User Story**: Como usuário ou pesquisador, quero executar o comando `expml` no terminal com as opções `--version` e `--help`, para inspecionar a versão instalada e obter instruções de uso sem acoplamento a submódulos não implementados.

**Why P1**: Estabelece o ponto de entrada da interface do framework conforme o requisito RNF07 e o Marco M1.1, sem violar a independência em relação aos marcos futuros.

**Acceptance Criteria**:

1. WHEN executed with the `--version` flag (`expml --version`), THEN the system SHALL output the current package version to stdout and exit with code 0.
2. WHEN executed with the `--help` or `-h` flag (`expml --help`), THEN the system SHALL output a usage summary with available options to stdout and exit with code 0.
3. IF executed with an unrecognized or invalid argument, THEN the system SHALL print an error description to stderr and exit with code 2.
4. The system SHALL implement `src/experimental_ml/cli/main.py` using only the Python standard library (`argparse`) without importing unwritten modules (`core`, `metrics`, `data`).

**Independent Test**: Executar `expml --version`, verificar código de saída `0` e string de versão; executar `expml --help`, verificar código de saída `0`; executar `expml --invalid-flag` e verificar código de saída `2`.

---

### P1: Teste de Fumaça com Pytest ⭐ MVP

**User Story**: Como desenvolvedor, quero executar uma suíte mínima de testes de fumaça com `pytest`, para garantir que o pacote é importável e a CLI é invocável em qualquer ambiente de desenvolvimento.

**Why P1**: Valida empiricamente a integridade da instalação e serve como gate de aceitação automatizado para o Marco M1.1 (`TA-M1.1`).

**Acceptance Criteria**:

1. The system SHALL provide `tests/test_smoke.py` containing automated smoke tests for module import and CLI entrypoint invocation.
2. WHEN running `pytest tests/test_smoke.py`, THEN the test runner SHALL discover and execute tests that verify `experimental_ml.__version__` is a non-empty string.
3. WHEN running `pytest tests/test_smoke.py`, THEN the test runner SHALL assert observable CLI outcomes: verifying that `--help` exits with code 0 containing usage instructions, `--version` exits with code 0 containing the declared package version, and an invalid argument exits with code 2 printing an error message to stderr.

**Independent Test**: Executar `pytest tests/test_smoke.py -v` e observar 100% de aprovação dos testes de fumaça validando os comportamentos observáveis da CLI.

---

## Edge Cases

- IF `expml` is invoked without arguments, THEN the system SHALL print the standard help message and exit with code 0.
- IF an unrecognized argument is passed to `expml`, THEN the system SHALL print an argument error message to stderr and exit with code 2.
- The system SHALL ensure that `src/experimental_ml/cli/main.py` handles CLI execution without raising `ImportError` when modules `core`, `metrics` or `data` do not exist.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| SETUP-01 | P1: Configuração Inicial de Empacotamento | Specify | Pending |
| SETUP-02 | P1: Configuração Inicial de Empacotamento | Specify | Pending |
| SETUP-03 | P1: Configuração Inicial de Empacotamento | Specify | Pending |
| SETUP-04 | P1: Configuração Inicial de Empacotamento | Specify | Pending |
| SETUP-05 | P1: Configuração Inicial de Empacotamento | Specify | Pending |
| CLI-01 | P1: Ponto de Entrada da CLI Base | Specify | Pending |
| CLI-02 | P1: Ponto de Entrada da CLI Base | Specify | Pending |
| CLI-03 | P1: Ponto de Entrada da CLI Base | Specify | Pending |
| CLI-04 | P1: Ponto de Entrada da CLI Base | Specify | Pending |
| SMOKE-01 | P1: Teste de Fumaça com Pytest | Specify | Pending |
| SMOKE-02 | P1: Teste de Fumaça com Pytest | Specify | Pending |
| SMOKE-03 | P1: Teste de Fumaça com Pytest | Specify | Pending |

---

## Sources

- `ARQUITETURA_E_CONTRATOS.md` Seção 2.4 e 7.1 - Define o layout `src/experimental_ml/cli/`, o subcomando de entrada `expml` e o escopo da entrega M1.1 (`TA-M1.1`).
- `ESPECIFICACAO_REQUISITOS.md` RNF06 e RNF07 - Define `requires-python = ">=3.10"`, códigos de saída padrão e ergonomia da CLI.
- `ETAPA_ATUAL_ENGENHARIA.md` Seção 3 - Marco M1.1 detalhando configuração, esqueleto da CLI e smoke tests.

---

## Success Criteria

- [ ] O arquivo `pyproject.toml` é válido e aceito pelo instalador `pip` com backend `hatchling.build`.
- [ ] A instalação editável `pip install -e ".[dev]"` é executada com sucesso.
- [ ] O comando de linha de comando `expml --version` retorna `0.1.0.dev0` com código de saída 0.
- [ ] O comando de linha de comando `expml --help` exibe a mensagem de ajuda com código de saída 0.
- [ ] A execução de `pytest tests/test_smoke.py` conclui com 100% de sucesso e zero falhas.

