# experimental-ml-framework

Framework experimental agnóstico para pesquisa científica em Machine Learning, com suporte a tarefas de regressão e classificação. Oferece infraestrutura modular para ingestão e preparação de dados, configuração e comparação de conjuntos de atributos, execução reprodutível de experimentos, validação cruzada com prevenção de vazamento de dados, análise estatística dos resultados e geração de tabelas e visualizações prontas para publicação científica.

---

## Progresso do Projeto

A evolução do projeto segue um ciclo de vida estruturado em 5 fases:

- [x] **Fase 1: Auditoria Técnica e Baseline**
  - [x] Auditoria do código e dados de origem (`prognose_florestal`).
  - [x] Catalogação dos resultados de referência ($R^2$, RMSE, MAE, KTA, HHL).
  - [x] Identificação de vulnerabilidades (acoplamentos a domínio, duplicações de código, distorções métricas).
- [x] **Fase 2: Engenharia de Requisitos das 6 Etapas do Ciclo Experimental**
  - [x] Definição da premissa arquitetural (ADR-001: framework atua como orquestrador agnóstico e não implementa modelos de ML internamente).
  - [x] Especificação da Etapa 1 (Entrada, triagem diagnóstica somente-leitura, problemas confirmados vs. alertas heurísticos e plano explícito de preparação).
  - [x] Especificação da Etapa 2 (Exploração rotulada de relações, cenários fixos e cenários dinâmicos ajustados por *fold* com rastreabilidade de estabilidade).
  - [x] Especificação da Etapa 3 (Registro de modelos via adaptadores, suporte a equações analíticas sem `fit`, pré-processamento em 2 camadas, *tuning* aninhado e diagnósticos internos).
  - [x] Especificação da Etapa 4 (`PartitionPlan` compartilhado, CV e *Holdout* isolado, orquestração resiliente a falhas, paralelismo em 2 níveis, *checkpoint/resume*, tempos desagregados e predições *out-of-fold*).
  - [x] Especificação da Etapa 5 (Consolidação descritiva, seleção metodológica de testes estatísticos, tratamento de incompletude, tamanho de efeito, relevância prática, Fronteira de Pareto e conclusões explicativas rastreáveis).
  - [x] Especificação da Etapa 6 (Relatório científico completo, 7 famílias de tabelas e figuras modulares, manifesto de proveniência por artefato e pacote portável de reprodutibilidade).
  - [x] Consolidação formal na [`ESPECIFICACAO_REQUISITOS.md`](engenharia_software/ESPECIFICACAO_REQUISITOS.md) (v2.0).
- [x] **Fase 3: Arquitetura Geral, Contratos Conceituais, Modelo de Dados e Recorte de MVP**
  - [x] Definição da arquitetura em três camadas, do pipeline operacional de dados em 6 etapas e das dependências entre módulos.
  - [x] Adoção do paradigma modular procedural/funcional (sem orientação a objetos) e especificação da CLI modularizada (`expml`, ADR-008).
  - [x] Formalização dos contratos conceituais de entrada, saída, invariantes e pontos de extensão de cada módulo.
  - [x] Definição do modelo de dados do experimento, máquina de estados e árvore de diretórios do pacote de reprodutibilidade.
  - [x] Separação estratégica entre o **MVP Essencial** e as **Evoluções Posteriores Plugáveis**.
  - [x] Consolidação formal em [`ARQUITETURA_E_CONTRATOS.md`](engenharia_software/ARQUITETURA_E_CONTRATOS.md).
- [ ] **Fase 4: Implementação Guiada por Testes (TDD) do MVP (Marcos M1–M7)**
  - [ ] **M1 (`core` + `metrics` + `cli` base):**
    - [ ] **M1.1:** Configuração do projeto (`pyproject.toml`, `.venv`), esqueleto da CLI modularizada (`expml`), verificação empírica de compatibilidade e *smoke tests*.
    - [ ] **M1.2:** Contratos, implementação funcional e testes de `core` (IDs, constantes/enums, `derive_seeds`, `config_hash`, `dataset_hash`, validações/alertas).
    - [ ] **M1.3:** Contratos, implementação funcional e testes de `metrics` (`MetricValue`, `METRICS_CATALOG`, `UNDEFINED_NAN` e 15 funções de métricas com tolerâncias específicas por família).
  - [ ] **M2 (`data` + `validation` + CLI `data`/`partition`):** Funções de ingestão somente-leitura (`.csv`/`.txt` com ou sem cabeçalho, `unlabeled_pool`, alvo único/multivariado), `profile_dataset`, `create_preparation_plan` (`TargetTransformSpec`) e `build_partition_plan` auditado (`kfold_split`, `stratified_kfold_split`, `group_kfold_split`, `bootstrap_split`, `temporal_split`, `holdout_split`).
  - [ ] **M3 (`features` + CLI `features`):** `explore_features`, validação de cenários (`FIXED` e `DYNAMIC`) e `select_features_in_fold` ajustado por *fold* (seleção e redução de dimensionalidade) com índice de estabilidade.
  - [ ] **M4 (`models` + `tuning` + CLI `models`):** `ModelSpec`, funções `instantiate_fresh_model`, `fit_model`, `predict_model` com incerteza preditiva, pré-processamento funcional em 2 camadas (incluindo roteamento sem vazamento para funções externas de kernel pré-computado) e `run_nested_tuning` (`fixed`, `grid_search`, `random_search`).
  - [ ] **M5 (`orchestration` + CLI `run`):** `run_experiment_matrix` e `resume_experiment_matrix`, isolamento de falhas (`FAULT_TOLERANT` / `FAIL_FAST`), paralelismo em 2 níveis, agregação de comitê e persistência com *checkpoint/resume*.
  - [ ] **M6 (`statistics` + CLI `stats`):** Funções de consolidação, adequação metodológica, Nadeau-Bengio, Wilcoxon, Holm-Bonferroni, Benjamini-Hochberg, relevância prática, Fronteira de Pareto, funções de aquisição sequencial e `synthesize_conclusions`.
  - [ ] **M7 (`reporting` + CLI `report`):** Funções de geração de relatórios completos (MD/HTML), 7 famílias de tabelas (CSV/MD/LaTeX `booktabs`) e figuras (PNG/SVG/PDF), manifesto de proveniência e pacote de reprodutibilidade.
- [ ] **Fase 5: Verificação Experimental**
  - [ ] Reprodução do baseline científico do projeto de origem com paridade matemática e conceitual.
  - [ ] Validação de scripts e notebooks tutoriais guiados.

---

## Arquitetura em Camadas e Pipeline Operacional (6 Etapas)

| Etapa do Pipeline | Camada Arquitetural | Módulos (`src/experimental_ml/`) | Subcomando CLI | Responsabilidade Central (Funções Modulares, Sem OOP) |
| :--- | :--- | :--- | :--- | :--- |
| **Etapa 1** | Camada 1: Definição e Triagem | `data` | `expml data` | Ingestão imutável (`load_dataset`), perfil diagnóstico completo (`profile_dataset`: problemas confirmados vs. alertas heurísticos) e plano explícito de preparação (`create_preparation_plan`). |
| **Etapa 2** | Camada 1: Definição e Triagem | `features` | `expml features` | Análise exploratória de relações (`explore_features`) e gerenciamento de cenários fixos (`mode="FIXED"`) e dinâmicos ajustados por *fold* (`select_features_in_fold`). |
| **Etapa 3** | Camada 1: Definição e Triagem | `models`, `tuning` | `expml models` | Especificação e execução isolada de modelos (`instantiate_fresh_model`, `fit_model`, `predict_model`), pré-processamento funcional em duas camadas, otimização aninhada (`run_nested_tuning`) e extração de diagnósticos. |
| **Etapa 4** | Camada 2: Validação e Execução Matricial | `validation`, `orchestration` | `expml partition` / `expml run` | Geração e validação do `PartitionPlan` compartilhado (`build_partition_plan`), execução matricial (`run_experiment_matrix`) com tolerância a falhas, controle de paralelismo, *checkpoint/resume* e predições *out-of-fold*. |
| **Etapa 5** | Camada 3: Julgamento Estatístico e Publicação | `statistics` (com `metrics`) | `expml stats` | Consolidação descritiva, avaliação de adequação de testes estatísticos, tamanho de efeito, relevância prática, análise multiobjetivo (`compute_pareto_frontier` e funções de aquisição) e conclusões rastreáveis. |
| **Etapa 6** | Camada 3: Julgamento Estatístico e Publicação | `reporting` | `expml report` | Geração somente-leitura de relatórios científicos (Markdown/HTML), 7 famílias de tabelas e figuras modulares, manifesto de proveniência e pacote de reprodutibilidade (`build_reproducibility_package`). |

*(Os módulos `core` e `metrics` formam a fundação transversal de funções puras utilizada pelas três camadas, e `cli` provê a interface modularizada de linha de comando).*

---

## Documentação de Engenharia

Os documentos técnicos de acompanhamento e especificação estão centralizados no diretório [`engenharia_software/`](engenharia_software/):

- [`engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`](engenharia_software/ETAPA_ATUAL_ENGENHARIA.md): Registro do estado atual do ciclo de vida da engenharia.
- [`engenharia_software/ESPECIFICACAO_REQUISITOS.md`](engenharia_software/ESPECIFICACAO_REQUISITOS.md): Especificação completa dos requisitos funcionais e não-funcionais das 6 etapas (SRS v2.0).
- [`engenharia_software/ARQUITETURA_E_CONTRATOS.md`](engenharia_software/ARQUITETURA_E_CONTRATOS.md): Arquitetura em camadas, pipeline operacional de 6 etapas, dependências entre módulos, contratos conceituais, modelo de dados, pacote de reprodutibilidade e recorte de MVP.
