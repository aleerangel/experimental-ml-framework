# Roteiro de Validação e Aceitação — Marco M5.4 (CLI Run End-to-End)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M5.4 (`m5-4-cli-run-end-to-end`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e integradores da interface de linha de comando `expml run` do `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente da interface de linha de comando** (`expml run`) e suas exportações públicas.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e as exportações públicas da CLI estão íntegras:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e comandos da CLI
expml --version
expml --help
expml run --help

# 3. Verificação de pureza de runtime no nível de módulo (CLI-10)
python -c "
import sys
import experimental_ml.cli.main
import experimental_ml.cli.cmd_run
forbidden = ['numpy', 'scipy', 'pandas', 'sklearn', 'torch', 'qiskit', 'pyarrow']
loaded = [p for p in forbidden if p in sys.modules]
assert not loaded, f'Módulos proibidos carregados no nível de módulo: {loaded}'
print('Conformidade com CLI-10 validada com sucesso!')
"

# 4. Verificação de pureza de runtime na execução (XCUT-02)
python -c "
import sys
import experimental_ml.orchestration
forbidden = ['scipy', 'pandas', 'sklearn', 'torch', 'qiskit', 'pyarrow']
loaded = [p for p in forbidden if p in sys.modules]
assert not loaded, f'Dependências proibidas em runtime: {loaded}'
print('Conformidade com XCUT-02 validada com sucesso!')
"
```

---

## 2. Roteiro de Testes de Aceitação por Capacidade

### 2.1 Execução de Matriz Experimental via Terminal (`expml run start`)

Valida o disparo da matriz experimental completa a partir de um diretório de experimento configurado (etapas 1 a 4A prontas):

```bash
# Execução da matriz com consolidação automática de OOF e 2 workers
expml run start --experiment-dir /caminho/do/experimento -j 2

# Verificação esperada:
# - Código de saída: 0
# - Mensagem: "Experiment matrix execution completed"
# - Artefatos gerados:
#     {run_dir}/execution_state.json
#     {run_dir}/cells/cell_*.json
#     {run_dir}/predictions/pred_*.json
#     {run_dir}/oof/oof_*.json
```

---

### 2.2 Inspeção Somente-Leitura de Progresso (`expml run status`)

Valida a consulta rápida do progresso sem modificar o disco:

```bash
expml run status --run-dir /caminho/do/experimento/runs

# Verificação esperada:
# - Código de saída: 0
# - Exibição de total de células, percentual de conclusão e contagem por status
# - Preservação estrita dos arquivos em disco (mtime inalterado)
```

---

### 2.3 Retomada Resiliente de Execução (`expml run resume`)

Valida a capacidade de retomar uma execução parcialmente concluída ou interrompida sem recomputar células válidas:

```bash
expml run resume --run-dir /caminho/do/experimento/runs --retry-failed

# Verificação esperada:
# - Código de saída: 0
# - Células concluídas são ignoradas
# - Células pendentes ou falhas são reexecutadas
```

---

### 2.4 Auditoria Formal da Etapa 4 (`expml run verify`)

Valida o portão de estágio Stage 4:

```bash
expml run verify --run-dir /caminho/do/experimento/runs

# Verificação esperada:
# - Código de saída: 0
# - Saída: "Stage 4 execution gate verified successfully: Status: READY"
```

---

### 2.5 Tratamento Padronizado de Erros e Supressão de Hashes (`CLI-06`, `CLI-11`)

```bash
# 1. Diretório inexistente deve encerrar com código 2 e mensagem sem traceback:
expml run start --experiment-dir /diretorio_inexistente
# Saída esperada em stderr: "Error: ..." (código 2, sem Traceback)

# 2. Execução sem --force sobre pasta existente deve ser rejeitada com código 2:
expml run start --experiment-dir /caminho/do/experimento
# Saída esperada em stderr: "Error: Run directory ... already contains execution_state.json. Use --force to overwrite."

# 3. Supressão de hashes criptográficos:
# Nenhuma saída em stdout ou stderr exibe digests hexadecimais brutos de 64 caracteres.
```

---

## 3. Critérios Formais de Aceite (Definição de Pronto - DoD)

Para homologação do Marco M5.4, os seguintes critérios são mandatórios:
- [x] Todas as 22 verificações (C1 a C22) comprovadas e aprovadas sem regressão.
- [x] Suíte de testes automatizados com 460/460 testes aprovados na suíte global.
- [x] Relatório do Verificador Independente com veredito `PASS` e zero `findings` abertos.
- [x] Conformidade total com `CLI-06` (códigos 0, 1, 2 e sem traceback em erros de domínio).
- [x] Conformidade total com `CLI-10` (zero importações pesadas no escopo de módulo da CLI).
- [x] Conformidade total com `CLI-11` (supressão total de hashes criptográficos na saída).
- [x] Conformidade total com `XCUT-02` (runtime dependente exclusivamente de `numpy>=1.24.0` e biblioteca padrão).
