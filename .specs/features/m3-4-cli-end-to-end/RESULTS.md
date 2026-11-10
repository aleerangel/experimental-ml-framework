# Registro de Validação e Aceite — Marco M3.4 (CLI de Features e Homologação Ponta a Ponta)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M3.4 (`m3-4-cli-end-to-end`)  
> **Data de Validação:** 10 de Novembro de 2026  
> **Commit de Implementação:** [`196d734`](https://github.com/alexandrerangel/experimental-ml-framework/commit/196d734)  
> **Commit de Verificação:** [`e418c20`](https://github.com/alexandrerangel/experimental-ml-framework/commit/e418c20)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Ponto de Entrada e Ajuda da CLI** | `expml features --help` exibindo subcomandos `explore`, `scenarios` e `verify` | Validado via `main()` e subprocesso com saída formatada e código 0 | **APROVADO** |
| **Exploração de Features (`FEAT-02`)** | `expml features explore` salvando `reports/exploratory_features.json` com `EXPLORATORY_FULL_DATA` | Relatório gerado atomicamente e validado contra visão saneada | **APROVADO** |
| **Proteção contra Sobrescrita (`FEAT-03`)** | Bloqueio de sobrescrita sem `--force` (código 2); permissão com `--force` | Comprovado por testes unitários e casos de borda | **APROVADO** |
| **Catálogo de Cenários (`FEAT-04`)** | Validação contra esquema saneado e salvamento em `configuration/scenarios.json` | Validado com cenários `FIXED` e `DYNAMIC`, carimbo de `dataset_hash` | **APROVADO** |
| **Rejeição sem Traceback (`FEAT-05`)** | Código 2 e stderr amigável para features desconhecidas ou vazamento de alvo | Comprovado com rejeição de colunas inexistentes e vazamentos protegidos | **APROVADO** |
| **Portão de Etapa (`FEAT-06`)** | `expml features verify` validando integridade de arquivo, hash e conteúdo | Validado via `verify_scenarios_gate` (código 0 para válido, código 2 para violação) | **APROVADO** |
| **Pureza de Runtime (`FEAT-07` / `CLI-10`)** | `sys.modules` limpo sem `numpy` ou `hashlib` em invocações rápidas de CLI | Verificado via AST traversal e processo Python limpo isolado | **APROVADO** |
| **Pipeline Fim a Fim (`FEAT-08`)** | Homologação ponta a ponta multi-etapa integrando Etapa 1 e Etapa 2 | Testado via subprocessos em diretório isolado com saída higienizada | **APROVADO** |
| **Testes de Regressão Geral** | 236 testes em `pytest tests/` | 236 testes aprovados (100%) em 6.84s | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e julgamento independente (`author != verifier`) | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (todos os subcomandos e validações) | Executado ponta a ponta via CLI com sucesso | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Verificação de Provas Automatizadas (`check_proofs.py`)

Execução pelo script determinístico do protocolo TLC Spec-Driven:

```text
HEAD: e418c20
Tree: clean
Shell: /bin/sh
Result: 8 pass, 0 fail
```

### 2.2 Suíte de Testes Unitários de Features CLI

Execução no ambiente `.venv` (`.venv/bin/pytest tests/unit/cli/test_cmd_features.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 7 items

tests/unit/cli/test_cmd_features.py::test_feat_01_features_help PASSED   [ 14%]
tests/unit/cli/test_cmd_features.py::test_feat_02_features_explore_success PASSED [ 28%]
tests/unit/cli/test_cmd_features.py::test_feat_03_features_explore_overwrite_protection PASSED [ 42%]
tests/unit/cli/test_cmd_features.py::test_feat_04_features_scenarios_success PASSED [ 57%]
tests/unit/cli/test_cmd_features.py::test_feat_05_features_scenarios_rejection PASSED [ 71%]
tests/unit/cli/test_cmd_features.py::test_feat_06_features_verify_gate PASSED [ 85%]
tests/unit/cli/test_cmd_features.py::test_feat_07_cli_purity PASSED      [100%]

============================== 7 passed in 0.40s ===============================
```

### 2.3 Suíte de Integração Ponta a Ponta Multi-Etapa

Execução no ambiente `.venv` (`.venv/bin/pytest tests/integration/features/test_features_cli_integration.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 1 item

tests/integration/features/test_features_cli_integration.py::test_feat_08_end_to_end_cli_pipeline PASSED [100%]

============================== 1 passed in 1.63s ===============================
```

### 2.4 Suíte Completa de Regressão Global

Execução no ambiente `.venv` (`.venv/bin/pytest tests/ -v`):

```text
============================= 236 passed in 6.84s ==============================
```

---

## 3. Conformidade com Decisões Arquiteturais e Invariantes

1. **CLI-06 / CLI-07 (Composição Hierárquica de Subparsers e Despacho Modular):**
   - Os subcomandos `explore`, `scenarios` e `verify` estão organizados sob o grupo `expml features`, delegando de forma desacoplada para os tratadores em `src/experimental_ml/cli/cmd_features.py`.
2. **CLI-08 / CLI-11 (Higiene de Terminal e Padronização de Códigos de Saída):**
   - Retornos padronizados: `0` para sucesso, `2` para erros de domínio ou argumentos inválidos (`ExperimentalMLError`), e `1` para erros não previstos. Mensagens de erro são limpas, formatadas em `stderr` com o prefixo `Error:`, e sem tracebacks ou digests hexadecimais brutos SHA-256 de 64 caracteres.
3. **CLI-09 (Proteção contra Perda Acidental de Dados):**
   - Tentativas de sobrescrever `reports/exploratory_features.json` ou `configuration/scenarios.json` existentes são estritamente rejeitadas a menos que a flag `--force` seja informada explicitamente pelo usuário.
4. **CLI-10 / ADR-008 (Pureza de Runtime e Inicialização Rápida):**
   - A árvore AST dos módulos CLI não contém importações no topo de `numpy` ou `hashlib`. Em processo Python limpo, invocações de consulta como `expml --help` ou `expml features --help` mantêm `sys.modules` livre dessas bibliotecas.
5. **ADR-002 / SCN-08 (Validação Formal de Portão de Cenários):**
   - O subcomando `expml features verify` executa `verify_scenarios_gate`, conferindo existência física, hash criptográfico de correspondência com a visão saneada e validade estrutural dos cenários contra o esquema da base.
6. **STORE-03 / STORE-06 (Persistência Atômica e Imutabilidade):**
   - Gravação dos relatórios e catálogos através de escritas atômicas (`write_json_atomic`), prevenindo corrupção por encerramento abrupto de processos.

---

## 4. Julgamento da Verificação Independente (`verification.md`)

- **Veredito:** `PASS`
- **Auditado por:** Sub-agente verificador independente (`author != verifier`).
- **Achados impeditivos:** Nenhum (`None`).
- **Avaliação de Checks C1..C8:** Todos os 8 testes selecionados comprovam formalmente seus critérios de aceitação sem asserções frouxas.
- **Provas com dados e casos de borda inéditos:** 8 baterias de testes independentes executadas com sucesso cobrindo diretórios inexistentes, verificação em diretório vazio, arquivos de cenário ausentes, JSON malformado primitivo, dicionário encapsulado `{"scenarios": [...]}`, duplicidade de identificadores de cenários, vazamento da coluna alvo `target` e inclusão do identificador de observações `id`.

---

## 5. Validação Prática de Aceite pelo Consumidor (`ACCEPTANCE.md`)

Todos os passos do roteiro operacional `ACCEPTANCE.md` foram testados e executados via linha de comando no terminal:
- Consulta de ajuda: `expml features --help` (código 0).
- Análise exploratória: `expml features explore` gerando `reports/exploratory_features.json` com `EXPLORATORY_FULL_DATA` (código 0).
- Proteção de sobrescrita: rejeição sem `--force` (código 2) e sobrescrita com `--force` (código 0).
- Validação de catálogo: `expml features scenarios` salvando `configuration/scenarios.json` (código 0).
- Rejeições diagnósticas sem traceback: colunas desconhecidas e vazamento de alvo bloqueados com código 2.
- Verificação de portão: `expml features verify` com sucesso (código 0) e falha em diretório inválido (código 2).
- Pureza de runtime: `sys.modules` limpo comprovado via script de subprocesso.
- Integração de ponta a ponta: encadeamento completo Etapa 1 -> Etapa 2 -> Etapa 3 sem violação de invariantes.

---

## 6. Decisão Formal de Aceite

> **Decisão:** **`APROVADO`**  
>
> **Justificativa:** Todos os critérios de aceitação funcionais (FEAT-01 a FEAT-06), transversais (FEAT-07, FEAT-08) e diretrizes de usabilidade e arquitetura da CLI (`CLI-06` a `CLI-11`, `ADR-002`, `ADR-008`) foram formalmente comprovados por testes automatizados, verificação independente e homologação operacional ponta a ponta sem qualquer pendência impeditiva. Conclui-se com êxito a Etapa 2 (Feature Engineering & Scenarios) do projeto.
