# Experimental ML Framework 

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

## As 6 Etapas de Utilização

1. **Etapa 1 — Entrada, Triagem e Saneamento (`expml data`):** Ingestão imutável da base tabular (com suporte e detecção automática para delimitadores, vírgula decimal, `quotechar` e *encoding*), diagnóstico estrutural e aplicação de regras determinísticas pré-partição.
2. **Etapa 2 — Exploração e Cenários de Features (`expml features`):** Análise exploratória rotulada e definição de cenários fixos ou dinâmicos executados estritamente dentro de cada dobra.
3. **Etapa 3 — Modelos, Pré-processamento e Tuning (`expml models`):** Registro declarativo de modelos heterogêneos, pré-processamento em 2 camadas sem duplicação e *Nested CV*.
4. **Etapa 4 — Particionamento (4A) e Execução Matricial (4B) (`expml partition`, `expml run`):** Divisão compartilhada determinística e execução tolerante a falhas com checkpoint/retomada.
5. **Etapa 5 — Consolidação e Estatística (`expml stats`):** Agregação descritiva sem coerção silenciosa para zero, testes pareados, multiplicidade e fronteira de Pareto.
6. **Etapa 6 — Relatórios e Reprodutibilidade (`expml report`):** Geração somente-leitura de tabelas (`CSV`/`Markdown`/`LaTeX`), gráficos e pacote portátil com checksums SHA-256.

---

## Instalação e Fluxo Básico (`expml`)

```bash
# Na pasta do repositório
pip install -e .

# Ou, a partir do .venv de outro projeto seu:
pip install -e /caminho/para/experimental-ml-framework
```

Execute todo o pipeline científico das **6 etapas** diretamente pelo terminal:

```bash
# Modo rápido em 2 comandos (cria exemplo pronto e executa as 6 etapas)
expml init --output-dir exp_dir --task regression
expml quickrun --experiment-dir exp_dir
```

Ou execute etapa por etapa com controle granular:

```bash
expml data profile --data dados.csv --schema schema.json --output-dir exp_dir
expml data sanitize --experiment-dir exp_dir --rules regras.json
expml features scenarios --experiment-dir exp_dir --scenarios cenarios.json
expml models validate --experiment-dir exp_dir --models modelos.json
expml partition build --experiment-dir exp_dir --config particao.json --seed 42
expml run start --experiment-dir exp_dir --error-policy fault_tolerant
expml stats run --experiment-dir exp_dir
expml report export --experiment-dir exp_dir --mode full_package --output-dir pacote_final
```

---

## Mapa de Documentação

### Para Pesquisadores (Uso Prático e Metodologia)
- **[Portal do Pesquisador](docs/README.md):** Navegação organizada pelas 5 Jornadas de Utilização.
- **[Começando do Zero](docs/guia/00_comecando_do_zero.md):** Exemplo de 10 linhas em Python (`run_experiment`) ou 2 comandos CLI, sem pré-requisitos de JSON/frameworks.
- **[Início Rápido (5 Passos)](docs/guia/01_inicio_rapido.md):** Instalação, fluxo CLI mínimo e exemplo Python executável.
- **[Tutorial das 6 Etapas](docs/guia/02_tutorial_6_etapas.md):** Guia passo a passo da preparação ao empacotamento, com portões de estágio e garantias anti-leakage.
- **[Interpretando Resultados Científicos](docs/guia/03_interpretando_resultados.md):** Guia prático de métricas, cobertura, testes pareados, Pareto e não-equivalência.
- **Guias Práticos (Cenários Avançados):**
  - [Modelos Analíticos (`requires_fit=False`) vs. Treinados](docs/guias_praticos/01_modelos_analiticos_vs_treinados.md)
  - [Métricas Quânticas (`KTA`) e Probabilísticas (`ROC-AUC`, `Log-Loss`)](docs/guias_praticos/02_metricas_quanticas_e_probabilisticas.md)
  - [Validação Cruzada Agrupada (`GroupKFold`) com Holdout Isolado](docs/guias_praticos/03_validacao_cruzada_agrupada_holdout.md)
  - [Otimização Multiobjetivo na Fronteira de Pareto](docs/guias_praticos/04_otimizacao_pareto_multiobjetivo.md)
  - [Pacotes Herméticos e Auditoria SHA-256 para Conferências](docs/guias_praticos/05_pacotes_reprodutibilidade_conferencias.md)
  - [Variações do Mesmo Algoritmo (LS-SVM em Prognose Florestal)](docs/guias_praticos/06_variantes_algoritmo_lssvm.md)
  - [Cenários de Features Fixos vs. Dinâmicos e Estabilidade](docs/guias_praticos/07_cenarios_features_estabilidade.md)
  - [Fluxo Desacoplado para Jupyter Notebooks e Relatórios sem Retreino](docs/guias_praticos/08_fluxo_desacoplado_jupyter_relatorios.md)
  - [Inferência Estatística na Prática e Controle de Multiplicidade](docs/guias_praticos/09_inferencia_estatistica_na_pratica.md)
- **Notebooks Interativos (`notebooks/`):**
  - [01 — Primeiro Experimento do Zero (Básico)](notebooks/01_primeiro_experimento_do_zero.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/01_primeiro_experimento_do_zero.ipynb)
  - [02 — Classificação e Grupos na Prática (Básico)](notebooks/02_classificacao_e_grupos_na_pratica.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/02_classificacao_e_grupos_na_pratica.ipynb)
  - [03 — Tour Completo pelas 6 Etapas (Intermediário)](notebooks/03_tour_6_etapas.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/03_tour_6_etapas.ipynb)
  - [04 — Vitrine Avançada: Variantes do LS-SVM em Prognose Florestal](notebooks/04_avancado_variantes_lssvm_prognose_florestal.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/04_avancado_variantes_lssvm_prognose_florestal.ipynb)

### Referência Técnica
- **[Schemas JSON da CLI `expml`](docs/referencia/cli_schemas_json.md):** Modelos exatos de `schema.json`, `rules.json`, `scenarios.json`, `models.json` e `partition.json`.
- **[Catálogo da API Python Pública](docs/referencia/api_python.md):** Fachada `run_experiment` e contratos dos 11 subpacotes públicos exportados.
- **[Catálogo Completo da CLI `expml`](docs/referencia/cli_catalogo.md):** Comandos, subcomandos e convenção oficial de códigos de saída (`0`, `1`, `2`).

### Engenharia, Arquitetura e Fundamentação
- **[Arquitetura e Contratos](docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md):** Camadas, contratos formais, portões e plano de marcos.
- **[Especificação de Requisitos](docs/engenharia_software/ESPECIFICACAO_REQUISITOS.md):** Requisitos funcionais, não funcionais e critérios de aceite.
- **[Estado Atual de Engenharia](docs/engenharia_software/ETAPA_ATUAL_ENGENHARIA.md):** Registro do estágio atual de evolução do projeto.
- **[Processo de Aceite de Marcos](docs/engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md):** Governança de homologação e auditoria independente.
- **[Referências e Fundamentação](docs/REFERENCIAS_E_FUNDAMENTACAO.md):** Base bibliográfica, decisões arquiteturais (ADRs) e estatística.

---

## Estrutura do Repositório

```text
experimental-ml-framework/
├── .specs/                              # Governança TLC Spec-Driven
│   ├── STATE.md                         # Decisões arquiteturais ativas e registro de handoff
│   └── features/                        # Especificações, tarefas, provas e verificações por submarco
├── docs/                                # Documentação completa do projeto
│   ├── README.md                        # Índice central e trilha pedagógica
│   ├── guia/                            # Início rápido e tutorial das 6 etapas
│   ├── guias_praticos/                  # Guias práticos para cenários avançados
│   ├── referencia/                      # Catálogos de API Python e CLI expml
│   ├── engenharia_software/             # SRS, arquitetura, contratos e aceite de marcos
│   └── REFERENCIAS_E_FUNDAMENTACAO.md   # Fundamentação teórica, bibliografia e ADRs
├── notebooks/                           # Notebooks Jupyter interativos (.ipynb)
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
└── README.md                            # Apresentação executiva e mapa de navegação
```

---

## Licença

Este projeto é software livre distribuído sob os termos da **Licença MIT**, desenvolvido por **Alexandre Rangel**. Para detalhes completos, consulte o arquivo [`LICENSE`](LICENSE).
