# Experimental ML Framework

Framework experimental agnóstico para pesquisa científica em Aprendizado de Máquina (*Machine Learning* — ML), voltado a tarefas de regressão e classificação sobre dados tabulares.

O projeto fornece infraestrutura modular, determinística e pedagógica para condução, auditoria e publicação de experimentos científicos, priorizando a integridade metodológica, a prevenção ativa de vazamento de dados e a reprodutibilidade integral dos resultados.

---

## 1. Sobre o Projeto

### Propósito e Problema Abordado

A pesquisa experimental em Aprendizado de Máquina frequentemente enfrenta desafios metodológicos que comprometem a validade e a comparabilidade dos resultados publicados:
- **Vazamento de dados (*data leakage*):** ajuste acidental de transformações de pré-processamento, imputações ou seleção de atributos fora do laço interno de treino de cada partição.
- **Mutações silenciosas:** alterações não declaradas ou automáticas nos dados brutos de entrada (como descarte de linhas com valores ausentes ou coerção arbitrária de tipos).
- **Viés de seleção de hiperparâmetros:** ausência de validação cruzada aninhada (*Nested CV*), resultando em estimativas de erro superotimistas.
- **Inferência estatística frágil:** declaração de modelos vencedores baseada em médias simples, sem testes pareados adequados, sem correção de comparações múltiplas ou confundindo ausência de significância estatística ($p \ge \alpha$) com equivalência entre algoritmos.
- **Acoplamento entre execução e apresentação:** necessidade de reexecutar experimentos onerosos apenas para reformatar tabelas ou recalcular testes estatísticos.

O `experimental-ml-framework` aborda esses problemas estruturando o ciclo experimental em **6 etapas operacionais** regidas por contratos estritos de entrada, saída e invariantes matemáticas, projetados para impedir falhas metodológicas por construção.

### Objetivos Principais

- **Prevenção estrutural de vazamento:** todo ajuste de parâmetros (pré-processamento, seleção de atributos e calibração de modelos) ocorre estritamente nos dados de treino de cada partição externa (**ADR-002**).
- **Zero mutações silenciosas:** a base de dados original é estritamente imutável. Toda sanitização ou imputação exige declaração explícita em um plano auditável de preparação.
- **Arquitetura agnóstica sem estimadores próprios (ADR-001):** o framework não reescreve algoritmos de ML internamente; recebe modelos e funções externas (Scikit-Learn, XGBoost, modelos analíticos sem `fit`, funções customizadas e circuitos quânticos) através de contratos funcionais uniformes.
- **Rastreabilidade e proveniência retrospectiva:** vinculação ponta a ponta entre a base de dados original, identificadores imutáveis de partição, sementes determinísticas e previsões por observação.
- **Independência entre camadas:** a geração de relatórios científicos, figuras e tabelas opera de forma somente-leitura sobre os artefatos persistidos, sem exigir retreinamento de modelos.

---

## 2. Estado de Desenvolvimento

O projeto encontra-se atualmente na **Fase 4: Implementação Guiada por Testes (TDD) do MVP**, utilizando a metodologia de desenvolvimento orientado por especificações (*TLC Spec-Driven Development*).

- **Marco M1.1 (`m1-1-setup-cli-smoke`): CONCLUÍDO.**  
  Disponibiliza a configuração inicial de empacotamento em Python, a árvore modular do projeto, o ponto de entrada da interface de linha de comando (`expml`) e a suíte de testes de fumaça.
- **Marco M1.2 (`core`): PRÓXIMO MARCO.**  
  Implementação dos contratos conceituais fundamentais, gerador hierárquico determinístico de sementes (`numpy.random.SeedSequence`), serialização canônica e funções de hashing (`config_hash` e `dataset_hash` conforme **ADR-007**).
- **Marcos M2 a M7: PLANEJADOS.**  
  O motor funcional completo (ingestão de dados, particionamento, execução matricial, cálculo de métricas, comparação estatística e geração de relatórios) está especificado e será implementado incrementalmente nos marcos subsequentes.

---

## 3. Funcionalidades Disponíveis

Na versão atual da branch `main`, as seguintes capacidades estão implementadas e operacionais:

- **Empacotamento Padronizado (PEP 517 / PEP 621):** Configuração declarativa via `pyproject.toml` baseada no build backend Hatchling.
- **Instalação Editável:** Suporte a instalação via `pip install -e ".[dev]"` em ambientes virtuais Python `>=3.10`.
- **Acesso Programático à Versão:** O pacote raiz expõe a constante pública de versão via `experimental_ml.__version__` (`0.1.0.dev0`).
- **Interface de Linha de Comando (`expml`):** Ponto de entrada executável registrado no ambiente (`PATH`), desenvolvido exclusivamente sobre a biblioteca padrão (`argparse`) sem dependências externas adicionais:
  - Opção `--version`: Exibe o identificador do executável e a versão instalada, finalizando com código de saída `0`.
  - Opção `--help` (ou `-h`): Apresenta o sumário descritivo de opções e instruções de uso, finalizando com código de saída `0`.
  - Execução sem argumentos: Exibe as instruções de uso e finaliza com código de saída `0`.
  - Tratamento de argumentos inválidos: Exibe mensagem de erro descritiva em `stderr` e finaliza com código de saída `2` (seguindo as convenções de integridade do requisito `RNF07`).
- **Suíte Automatizada de Testes de Fumaça:** 12 asserções automatizadas em `tests/test_smoke.py`, cobrindo integridade do pacote, análise estática de dependências da CLI e comportamento observável de processos.

---

## 4. Tecnologias e Estrutura do Projeto

### Tecnologias Utilizadas

- **Linguagem:** Python (suporte declarado `>=3.10`; verificado no interpretador local `Python 3.12.15`).
- **Build Backend:** [Hatchling](https://hatch.pypa.io/latest/) (`hatchling.build`).
- **Testes Automatizados:** [Pytest](https://docs.pytest.org/) (`pytest>=7.0.0`).
- **Biblioteca Padrão:** Utilização estrita de módulos padrão (`argparse`, `tomllib`, `ast`, `subprocess`, `sys`) na infraestrutura da CLI base.

### Estrutura de Diretórios

```
experimental-ml-framework/
├── .specs/                          # Especificações formais e tarefas (TLC Spec-Driven)
│   ├── STATE.md                     # Registro de decisões arquiteturais de projeto e handoff
│   └── features/
│       └── m1-1-setup-cli-smoke/    # Artefatos da entrega M1.1 (spec.md, tasks.md, proofs.md)
├── engenharia_software/             # Documentação técnica central de engenharia
│   ├── ESPECIFICACAO_REQUISITOS.md  # Especificação formal de requisitos (SRS v2.0)
│   ├── ARQUITETURA_E_CONTRATOS.md   # Arquitetura em camadas, contratos e modelo de dados
│   └── ETAPA_ATUAL_ENGENHARIA.md    # Estado atual do ciclo de vida e roadmap detalhado
├── src/
│   └── experimental_ml/             # Código-fonte da biblioteca (layout src/)
│       ├── __init__.py              # Raiz do pacote (exposição de __version__)
│       └── cli/                     # Interface de linha de comando
│           ├── __init__.py
│           └── main.py              # Ponto de entrada e parser principal (expml)
├── tests/                           # Suíte de testes automatizados
│   └── test_smoke.py                # Testes de fumaça da instalação e da CLI
├── pyproject.toml                   # Configuração de build, dependências e metadados
├── README.md                        # Porta de entrada do repositório
└── REFERENCIAS_E_FUNDAMENTACAO.md   # Fundamentação teórica e referências normativas (25 fontes)
```

---

## 5. Instalação

### Pré-requisitos

- **Python:** Versão `>= 3.10` instalada no sistema operacional.
- **Git:** Para clonar o repositório.

### Instruções Passo a Passo

1. **Clonar o repositório:**
   ```bash
   git clone https://github.com/alexandrerangel/experimental-ml-framework.git
   cd experimental-ml-framework
   ```

2. **Criar e ativar o ambiente virtual isolado (`.venv`):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   *(No Windows: `.venv\Scripts\activate`)*

3. **Atualizar o gerenciador `pip`:**
   ```bash
   pip install --upgrade pip
   ```

4. **Instalar o pacote em modo editável com as ferramentas de teste:**
   ```bash
   pip install -e ".[dev]"
   ```

Após esse procedimento, o comando `expml` estará acessível diretamente no terminal dentro do ambiente virtual ativo.

---

## 6. Como Utilizar

### Comandos da Interface de Linha de Comando (`expml`)

Com o ambiente virtual ativado, execute os comandos abaixo para verificar o funcionamento da interface:

#### Verificar a versão instalada:
```bash
expml --version
```


#### Exibir a mensagem de ajuda e opções:
```bash
expml --help
```


#### Invocação sem argumentos:
```bash
expml
```
Imprime as informações de utilização e finaliza com código de saída `0`.

#### Teste de validação de argumentos inválidos:
```bash
expml --opcao-invalida
```

### Uso Programático em Python

É possível verificar a disponibilidade e metadados do pacote diretamente via interpretador Python:

```python
import experimental_ml

print(experimental_ml.__version__)
# Saída: 0.1.0.dev0
```

---

## 7. Testes

O projeto utiliza o **Pytest** para automação de testes e garantia de integridade.

### Execução da Suíte de Fumaça

Para executar os testes de fumaça em modo detalhado, utilize o comando:

```bash
pytest tests/test_smoke.py -v
```

### Comportamento Verificado

A suíte valida deterministicamente:
- Declaração de build backend e metadados em `pyproject.toml`.
- Exposição correta de `__version__ = "0.1.0.dev0"` no pacote raiz.
- Ausência de importações de módulos não escritos na CLI (`core`, `metrics`, `data`).
- Resposta e códigos de saída da CLI para `--version` (código `0`), `--help` (código `0`), invocação vazia (código `0`) e flags inválidas (código `2`).
- Disponibilidade do executável `expml` no ambiente de execução.

**Resultado esperado:**
```
tests/test_smoke.py::test_pyproject_metadata PASSED
tests/test_smoke.py::test_package_version PASSED
tests/test_smoke.py::test_dev_dependencies PASSED
tests/test_smoke.py::test_cli_entrypoint_registered PASSED
tests/test_smoke.py::test_editable_install_and_cli_on_path PASSED
tests/test_smoke.py::test_cli_version_flag PASSED
tests/test_smoke.py::test_cli_help_flag PASSED
tests/test_smoke.py::test_cli_invalid_argument PASSED
tests/test_smoke.py::test_cli_dependencies_pure_stdlib PASSED
tests/test_smoke.py::test_smoke_discovery PASSED
tests/test_smoke.py::test_version_non_empty PASSED
tests/test_smoke.py::test_cli_observable_outcomes PASSED

============================== 12 passed in 0.11s ==============================
```

---

## 8. Roadmap

O desenvolvimento do MVP é organizado em marcos progressivos guiados por testes (TDD). A tabela a seguir distingue o que já foi implementado do que está planejado:

| Marco | Escopo e Responsabilidade | Estado |
| :--- | :--- | :---: |
| **M1.1** | **Configuração e CLI Base:** `pyproject.toml`, layout `src/experimental_ml/`, comando `expml` (`--version`, `--help`) e suíte de fumaça. | **Concluído** |
| **M1.2** | **Contratos e Funções de Core:** Tipos de IDs imutáveis, constantes/enums, gerador hierárquico `derive_seeds` (`SeedSequence`) e funções canônicas `config_hash`/`dataset_hash` (ADR-007). | **Próximo Marco** |
| **M1.3** | **Motor de Métricas:** Catálogo `METRICS_CATALOG`, regras estritas para `MetricStatus.UNDEFINED_NAN` (ADR-005) e 15 funções de métricas vetorizadas com tolerâncias justificadas. | Planejado |
| **M2** | **Ingestão e Particionamento:** Ingestão imutável (`data`), perfilamento diagnóstico (`profile_dataset`), plano explícito de preparação e `PartitionPlan` compartilhado e auditado (`validation`). | Planejado |
| **M3** | **Cenários de Features:** Modo exploratório rotulado (`EXPLORATORY_FULL_DATA`), cenários fixos e seleção dinâmica ajustada estritamente no treino de cada partição (`features`). | Planejado |
| **M4** | **Modelos e Tuning:** Registro de modelos heterogêneos (`models`), pré-processamento em duas camadas com bloqueio de duplicação e busca aninhada de hiperparâmetros (`tuning`). | Planejado |
| **M5** | **Execução Matricial:** Orquestração da matriz $M \times C \times F$ (`orchestration`), tolerância a falhas sem mascaramento, persistência atômica e retomada verificada (*Checkpoint & Resume*). | Planejado |
| **M6** | **Estatística Rigorosa:** Consolidação descritiva, teste $t$ corrigido de Nadeau-Bengio, Wilcoxon pareado, controle de FWER/FDR (Holm/BH), Fronteira de Pareto e conclusões estruturadas (`statistics`). | Planejado |
| **M7** | **Relatórios e Reprodutibilidade:** Relatórios desacoplados em Markdown/HTML, 7 famílias de tabelas/figuras, manifesto `ArtifactProvenance` e pacote portátil de reprodutibilidade (`reporting`). | Planejado |

---

## 9. Documentação Técnica

Para aprofundamento nos detalhes de engenharia, requisitos, arquitetura e fundamentação científica, consulte os documentos disponíveis no repositório:

| Documento | Descrição |
| :--- | :--- |
| [`engenharia_software/ESPECIFICACAO_REQUISITOS.md`](engenharia_software/ESPECIFICACAO_REQUISITOS.md) | **Especificação de Requisitos de Software (SRS v2.0):** Requisitos funcionais das 6 etapas, requisitos não-funcionais e critérios de aceitação objetivos da Onda 1 e Onda 2. |
| [`engenharia_software/ARQUITETURA_E_CONTRATOS.md`](engenharia_software/ARQUITETURA_E_CONTRATOS.md) | **Arquitetura, Contratos e Modelo de Dados:** Arquitetura em camadas, pipeline operacional de dados, contratos funcionais de cada módulo, modelo de dados do experimento e árvore do pacote de reprodutibilidade. |
| [`engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`](engenharia_software/ETAPA_ATUAL_ENGENHARIA.md) | **Registro de Estado da Engenharia:** Situação atual do projeto no ciclo de vida de desenvolvimento e roadmap detalhado de implementação. |
| [`REFERENCIAS_E_FUNDAMENTACAO.md`](REFERENCIAS_E_FUNDAMENTACAO.md) | **Fundamentação Teórico-Técnica e Bibliografia:** Justificativas científicas, matemáticas e normativas para as decisões de projeto (ADRs), com catálogo de 25 referências bibliográficas. |
| [`.specs/features/m1-1-setup-cli-smoke/`](.specs/features/m1-1-setup-cli-smoke/) | **Artefatos TLC da Entrega M1.1:** Especificação (`spec.md`), plano atômico de tarefas (`tasks.md`) e registro de verificação independente (`proofs.md`). |

---

## Licença

Este projeto é distribuído sob os termos da licença MIT (conforme declarado em [`pyproject.toml`](pyproject.toml)).
