# Roteiro de Validação e Aceitação — Marco M1.1

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M1.1 (`m1-1-setup-cli-smoke`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e consumidores da CLI do framework.  
> **Pré-requisito:** Python `>=3.10` e Git instalados.

---

## 1. Preparação do Ambiente e Instalação

Execute os passos a seguir a partir da raiz do repositório:

```bash
# 1. Criação do ambiente virtual isolado (.venv)
python3 -m venv .venv

# 2. Ativação do ambiente virtual
source .venv/bin/activate

# 3. Atualização do pip
pip install --upgrade pip

# 4. Instalação do pacote em modo editável com grupo de dependências dev
pip install -e ".[dev]"
```

- **Resultado Esperado:** Instalação finalizada com sucesso sem advertências de compilação ou dependências ausentes.
- **Identificação de Falha:** Erro durante a resolução do build-backend `hatchling.build` ou falha ao compilar metadados.

---

## 2. Roteiro de Testes Manuais de Aceitação (Perspectiva do Consumidor)

### 2.1 Verificação da Disponibilidade do Executável no PATH

```bash
which expml
```

- **Resultado Esperado:** Caminho absoluto do binário apontando para o `.venv` ativo (ex.: `/home/.../.venv/bin/expml`).
- **Critério de Falha:** Comando não encontrado (`command not found`).

---

### 2.2 Verificação da Versão via CLI (`--version`)

```bash
expml --version
```

- **Resultado Esperado:**
  - Saída padrão (`stdout`): `expml 0.1.0.dev0`
  - Código de saída (`exit code`): `0`
- **Critério de Falha:** Código diferente de 0, versão divergente ou stack trace em stderr.

---

### 2.3 Exibição de Ajuda via CLI (`--help` e Invocação Vazia)

```bash
# Teste A: com flag explícita
expml --help

# Teste B: com flag curta
expml -h

# Teste C: sem argumentos
expml
```

- **Resultado Esperado:**
  - Exibição de texto explicativo contendo descrição do framework, uso (`usage: expml [-h] [--version]`) e listagem de opções.
  - Código de saída (`exit code`): `0` para todas as 3 invocações.
- **Critério de Falha:** Código diferente de 0 ou ausência da descrição de opções.

---

### 2.4 Rejeição de Argumentos Inválidos (Código de Saída 2 — RNF07)

```bash
expml --parametro-invalido-xyz
```

- **Resultado Esperado:**
  - Mensagem de erro em `stderr` indicando argumento não reconhecido: `expml: error: unrecognized arguments: --parametro-invalido-xyz`
  - Código de saída (`exit code`): exatamente `2`.
- **Critério de Falha:** Código de saída `0`, `1` ou ausência de mensagem em stderr.

---

### 2.5 Acesso Programático via Python

```bash
python -c "import experimental_ml; print('Versao importada:', experimental_ml.__version__)"
```

- **Resultado Esperado:**
  - Saída: `Versao importada: 0.1.0.dev0`
  - Código de saída: `0`
- **Critério de Falha:** `ImportError` ou atributo `__version__` inexistente/vazio.

---

## 3. Roteiro de Testes Automatizados (Suíte de Fumaça)

Execute a suíte de testes de fumaça via `pytest`:

```bash
pytest tests/test_smoke.py -v
```

- **Resultado Esperado:**
  - Descoberta e aprovação de 12 testes automatizados:
    1. `test_pyproject_metadata`: validação estática de metadados PEP 621.
    2. `test_package_version`: validação de `__version__`.
    3. `test_dev_dependencies`: presença de `pytest>=7.0.0` no pyproject.
    4. `test_cli_entrypoint_registered`: console_scripts configurado para `expml`.
    5. `test_editable_install_and_cli_on_path`: presença do binário executável.
    6. `test_cli_version_flag`: saída e código 0 para `--version`.
    7. `test_cli_help_flag`: saída e código 0 para `--help`.
    8. `test_cli_invalid_argument`: saída e código 2 para flag inválida.
    9. `test_cli_dependencies_pure_stdlib`: análise AST garantindo ausência de dependências de submódulos não escritos.
    10. `test_smoke_discovery`: capacidade de descoberta do pytest.
    11. `test_version_non_empty`: integridade do valor semântico de versão.
    12. `test_cli_observable_outcomes`: validação em subprocesso isolado.
  - Veredito: `12 passed in <tempo>s` (100% de sucesso).
- **Critério de Falha:** Qualquer teste reprovado (`FAILED`) ou com erro (`ERROR`).

---

## 4. Matriz de Critérios de Aprovação do Marco

| Item | Descrição do Teste | Tipo | Responsável | Critério de Aceite |
| :--- | :--- | :--- | :--- | :--- |
| **AC-M1.1-1** | Instalação editável via pip | Integração | Consumidor | `pip install -e ".[dev]"` conclui com código 0 |
| **AC-M1.1-2** | Executável `expml` no PATH | Usabilidade | Consumidor | Comando responde no terminal |
| **AC-M1.1-3** | Opção `--version` exibe versão | Usabilidade / Funcional | Consumidor | Imprime `0.1.0.dev0` e exit code 0 |
| **AC-M1.1-4** | Opção `--help` exibe ajuda | Usabilidade / Funcional | Consumidor | Imprime help e exit code 0 |
| **AC-M1.1-5** | Argumento inválido retorna 2 | Robustez / RNF07 | Consumidor | Erro em stderr e exit code 2 |
| **AC-M1.1-6** | Suíte `tests/test_smoke.py` | Automatizado | Runner / Pytest | 12/12 testes aprovados |

