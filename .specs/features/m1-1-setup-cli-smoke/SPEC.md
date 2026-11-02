# Marco M1.1 — Setup Inicial, Empacotamento, CLI Base e Testes de Fumaça

> **Registro de Especificação do Marco (SPEC.md)**  
> **Identificador do Marco:** M1.1 (`m1-1-setup-cli-smoke`)  
> **Status:** Concluído / Implementado  
> **Aprovação da Especificação:** `**Approved**: 2026-10-31 - user: "A fase SPECIFY da feature m1-1-setup-cli-smoke foi aprovada."`  
> **Documento Detalhado EARS:** [`spec.md`](./spec.md)  
> **Roteiro de Validação:** [`ACCEPTANCE.md`](./ACCEPTANCE.md)  
> **Evidências e Decisão de Aceite:** [`RESULTS.md`](./RESULTS.md)

---

## 1. Propósito e Problema Abordado

O marco **M1.1** estabelece a infraestrutura inicial de engenharia do repositório `experimental-ml-framework`, fornecendo:
1. Configuração padronizada de empacotamento moderno em Python conforme os padrões PEP 517, PEP 518 e PEP 621.
2. Layout físico do código-fonte estruturado sob `src/experimental_ml/` para prevenir contaminação acidental de importações durante desenvolvimento.
3. Ponto de entrada executável da interface de linha de comando (`expml`), construído exclusivamente sobre a biblioteca padrão (`argparse`) e desacoplado dos submódulos funcionais ainda não implementados.
4. Suíte inicial de testes de fumaça executável via `pytest` para verificar a integridade da instalação, metadados do pacote e o comportamento observável dos processos da CLI.

---

## 2. Escopo Efetivamente Definido

### Incluído no Marco M1.1
- **Empacotamento:** Arquivo `pyproject.toml` com build-backend `hatchling.build`, nome de distribuição `experimental-ml-framework`, `requires-python = ">=3.10"` e versão inicial `0.1.0.dev0`.
- **Dependências de Desenvolvimento:** Grupo opcional `dev = ["pytest>=7.0.0"]` em `[project.optional-dependencies]`.
- **Estrutura de Código:** Layout `src/` com pacote `src/experimental_ml/__init__.py` exportando `__version__ = "0.1.0.dev0"`.
- **Interface de Terminal (CLI Base):** Ponto de entrada registrado em `[project.scripts]` apontando para `expml = "experimental_ml.cli.main:main"` em `src/experimental_ml/cli/main.py`.
- **Comportamento da CLI:**
  - Opção `--version`: Exibe nome e versão do pacote e encerra com código `0`.
  - Opção `--help` / `-h`: Exibe informações de uso e opções disponíveis, encerrando com código `0`.
  - Invocação vazia (`expml`): Exibe uso padrão e encerra com código `0`.
  - Argumentos inválidos (ex.: `expml --opcao-inexistente`): Exibe erro em `stderr` e encerra com código `2` (RNF07).
- **Testes de Fumaça:** Arquivo `tests/test_smoke.py` com testes automatizados executáveis via `pytest`.

### Não Incluído (Fora de Escopo)
- Módulo funcional `core` (pertence formalmente ao Marco M1.2).
- Módulo funcional `metrics` (pertence formalmente ao Marco M1.3).
- Subcomandos funcionais da CLI (`expml data`, `expml features`, `expml run`, etc. — pertencem aos Marcos M2 a M7).
- Algoritmos ou modelos de Machine Learning (ADR-001 e ADR-008).

---

## 3. Requisitos Rastreáveis e Critérios de Conclusão

| ID | Requisito | Critério de Conclusão |
| :--- | :--- | :--- |
| **M1.1-01** | Declaração PEP 517/621 | `pyproject.toml` configurado com `hatchling.build`, `requires-python >=3.10` e metadados válidos. |
| **M1.1-02** | Layout de Pacotes | `src/experimental_ml/__init__.py` define `__version__ = "0.1.0.dev0"`. |
| **M1.1-03** | Instalação Editável | `pip install -e ".[dev]"` instala o pacote com sucesso no ambiente virtual `.venv`. |
| **M1.1-04** | Registro do Executável | Comando `expml` acessível diretamente no terminal através do `PATH` do `.venv`. |
| **M1.1-05** | Opção `--version` | `expml --version` imprime `expml 0.1.0.dev0` e retorna código `0`. |
| **M1.1-06** | Opção `--help` | `expml --help` e `expml` sem argumentos imprimem ajuda e retornam código `0`. |
| **M1.1-07** | Tratamento de Erros CLI | Flag inexistente imprime mensagem de erro em `stderr` e retorna código `2`. |
| **M1.1-08** | Isolamento de Dependências | `cli/main.py` utiliza apenas biblioteca padrão e não importa submódulos inexistentes. |
| **M1.1-09** | Suíte de Fumaça | `pytest tests/test_smoke.py` descobre e aprova 100% dos testes automatizados (12 testes). |

