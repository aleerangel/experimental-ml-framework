# Experimental ML Framework (`experimental-ml`)

![Python](https://img.shields.io/badge/Python-%3E%3D3.10-blue)
![NumPy](https://img.shields.io/badge/Runtime-Pure%20Python%20%2B%20NumPy-green)
![Version](https://img.shields.io/badge/Version-0.1.0.dev0-informational)
![Status](https://img.shields.io/badge/MVP-Auditado%20%26%20Congelado-brightgreen)

Framework científico agnóstico para condução, auditoria e publicação de experimentos em Aprendizado de Máquina (*Machine Learning* — ML) sobre dados tabulares. Projetado em Python padrão e NumPy (`XCUT-02`), o projeto prioriza a integridade metodológica, o determinismo numérico e a reprodutibilidade integral de resultados científicos.

Um dos principais objetivos do framework é **democratizar o acesso à pesquisa científica rigorosa para novos pesquisadores, especialmente alunos de Iniciação Científica (IC)**, reduzindo barreiras técnicas e prevenindo armadilhas metodológicas comuns. Este projeto foi desenvolvido durante a Iniciação Científica na **Universidade Federal do Espírito Santo (UFES)**, no âmbito do **Projeto QUAIS (*Quantum Artificial Intelligence for Science*)**, em parceria com o **Instituto Kunumi**.

---

## Motivação Científica e Problemas Endereçados

A pesquisa experimental em ML frequentemente padece de vulnerabilidades metodológicas sutis que comprometem a validade de conclusões empíricas. O `experimental-ml` atua como infraestrutura de protocolo para mitigar estruturalmente:

- **Vazamento de dados (*data leakage*):** pré-processamento, imputação ou seleção de atributos ajustados fora da partição de treino.
- **Mutações silenciosas:** alterações implícitas na base bruta (remoção de linhas ou coerção de tipos) sem registro auditável.
- **Otimismo em hiperparâmetros:** ausência de validação cruzada aninhada (*Nested CV*), inflando métricas reportadas.
- **Inferência estatística frágil:** comparações baseadas em médias simples sem testes de hipótese pareados, sem controle de multiplicidade ou confundindo ausência de significância com equivalência prática.
- **Acoplamento entre execução e relato:** necessidade de reexecutar rotinas computacionais onerosas apenas para ajustar tabelas, figuras ou formatos de artigos.

---

## Instalação e Fluxo Básico (`expml`)

```bash
pip install -e .
```

Execute todo o pipeline científico das **6 etapas** diretamente pelo terminal:

```bash
expml data profile --input dados.csv --target alvo --task binary_classification --output-dir exp_dir
expml data sanitize --exp-dir exp_dir --allow-unresolved
expml features scenarios --exp-dir exp_dir --scenarios-json cenarios.json
expml models validate --exp-dir exp_dir --models-json modelos.json
expml partition build --exp-dir exp_dir --strategy stratified_kfold --n-splits 5 --seed 42
expml run start --exp-dir exp_dir --metrics accuracy f1
expml stats run --exp-dir exp_dir --primary-metric accuracy
expml report export --exp-dir exp_dir --mode FULL_PACKAGE --output-dir pacote_final
```

---

## Mapa de Documentação

### Para Pesquisadores (Uso Prático e Metodologia)
- **[Portal do Pesquisador](docs/README.md):** Visão geral e trilha pedagógica completa em 4 níveis.
- **[Início Rápido (5 Passos)](docs/guia/01_inicio_rapido.md):** Instalação, fluxo CLI mínimo e exemplo Python executável.
- **[Tutorial das 6 Etapas](docs/guia/02_tutorial_6_etapas.md):** Guia passo a passo da preparação ao empacotamento, com portões de estágio e garantias anti-leakage.
- **Scientific Cookbook (Receitas Avançadas):**
  - [Modelos Analíticos (`requires_fit=False`) vs. Treinados](docs/cookbook/01_modelos_analiticos_vs_treinados.md)
  - [Métricas Quânticas (`KTA`) e Probabilísticas (`ROC-AUC`, `Log-Loss`)](docs/cookbook/02_metricas_quanticas_e_probabilisticas.md)
  - [Validação Cruzada Agrupada (`GroupKFold`) com Holdout Isolado](docs/cookbook/03_validacao_cruzada_agrupada_holdout.md)
  - [Otimização Multiobjetivo na Fronteira de Pareto](docs/cookbook/04_otimizacao_pareto_multiobjetivo.md)
  - [Pacotes Herméticos e Auditoria SHA-256 para Conferências](docs/cookbook/05_pacotes_reprodutibilidade_conferencias.md)

### Referência Técnica
- **[Catálogo da API Python Pública](docs/referencia/api_python.md):** Assinaturas e contratos dos 11 pacotes públicos exportados.
- **[Catálogo Completo da CLI `expml`](docs/referencia/cli_catalogo.md):** Comandos, subcomandos e convenção oficial de códigos de saída (`0`, `1`, `2`).

### Engenharia, Arquitetura e Fundamentação
- **[Arquitetura e Contratos](engenharia_software/ARQUITETURA_E_CONTRATOS.md):** Camadas, contratos formais, portões e plano de marcos.
- **[Especificação de Requisitos](engenharia_software/ESPECIFICACAO_REQUISITOS.md):** Requisitos funcionais, não funcionais e critérios de aceite.
- **[Estado Atual de Engenharia](engenharia_software/ETAPA_ATUAL_ENGENHARIA.md):** Registro do estágio atual de evolução do projeto.
- **[Processo de Aceite de Marcos](engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md):** Governança de homologação e auditoria independente.
- **[Referências e Fundamentação](REFERENCIAS_E_FUNDAMENTACAO.md):** Base bibliográfica, decisões arquiteturais (ADRs) e estatística.

---

## Estrutura do Repositório

```text
experimental-ml-framework/
├── .specs/                              # Governança TLC Spec-Driven
│   ├── STATE.md                         # Decisões arquiteturais ativas e registro de handoff
│   └── features/                        # Especificações, tarefas, provas e verificações por submarco
├── docs/                                # Documentação do Pesquisador, Cookbook e Referências
│   ├── README.md                        # Índice central e trilha pedagógica
│   ├── guia/                            # Início rápido e tutorial das 6 etapas
│   ├── cookbook/                        # Receitas científicas avançadas
│   └── referencia/                      # Catálogos de API Python e CLI expml
├── engenharia_software/                 # Documentação de Engenharia de Software
│   ├── ESPECIFICACAO_REQUISITOS.md      # Especificação formal de requisitos (SRS)
│   ├── ARQUITETURA_E_CONTRATOS.md       # Arquitetura em camadas, contratos e modelo de dados
│   ├── PROCESSO_DE_ACEITE_DE_MARCOS.md  # Governança e critérios formais de aceite
│   └── ETAPA_ATUAL_ENGENHARIA.md        # Estado atual e roadmap detalhado
├── src/
│   └── experimental_ml/                 # Pacote da biblioteca (layout src/)
│       ├── cli/                         # Interface de linha de comando (Nível 7)
│       ├── core/                        # Núcleo transversal de domínio, hashes e sementes (Nível 0)
│       ├── data/                        # Ingestão, esquemas, diagnóstico e saneamento (Nível 1)
│       ├── features/                    # Exploração, cenários e seleção de features (Nível 2)
│       ├── metrics/                     # Catálogo e cálculo de métricas vetorizadas (Nível 1)
│       ├── models/                      # Contratos de modelos, pré-processamento e catálogo (Nível 4)
│       ├── orchestration/               # Execução matricial, checkpoint e consolidação OOF (Nível 4)
│       ├── reporting/                   # Relatórios, tabelas, figuras e reprodutibilidade (Nível 6)
│       ├── stages/                      # Portões de validação e integridade de etapas (Nível 3)
│       ├── statistics/                  # Consolidação, inferência pareada, Pareto e síntese (Nível 5)
│       ├── tuning/                      # Particionamento interno e Nested CV (Nível 3)
│       └── validation/                  # Particionamento compartilhado e validação matemática (Nível 2)
├── tests/                               # Suíte de testes automatizados (595 verificações)
│   ├── integration/                     # Testes de integração transversal e subprocessos
│   ├── test_smoke.py                    # Testes de fumaça da CLI e metadados de empacotamento
│   └── unit/                            # Testes unitários e de integridade documental
├── pyproject.toml                       # Configuração de build (Hatchling) e dependências
├── README.md                            # Apresentação executiva e mapa de navegação
└── REFERENCIAS_E_FUNDAMENTACAO.md       # Fundamentação teórica, bibliografia e ADRs
```

---

## Licença

Este projeto é software livre distribuído sob os termos da **Licença MIT**, desenvolvido por **Alexandre Rangel**. Para detalhes completos, consulte o arquivo [`LICENSE`](LICENSE).
