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
  - [x] Formalização dos contratos conceituais de entrada, saída, invariantes e pontos de extensão de cada módulo.
  - [x] Definição do modelo de dados do experimento, máquina de estados e árvore de diretórios do pacote de reprodutibilidade.
  - [x] Separação estratégica entre o **MVP Essencial** e as **Evoluções Posteriores Plugáveis**.
  - [x] Consolidação formal em [`ARQUITETURA_E_CONTRATOS.md`](engenharia_software/ARQUITETURA_E_CONTRATOS.md).
- [ ] **Fase 4: Implementação Guiada por Testes (TDD) do MVP (Marcos M1–M7)**
  - [ ] **M1 (`core` + `metrics`):**
    - [ ] **M1.1:** Configuração do projeto (`pyproject.toml`, `.venv`), verificação empírica de compatibilidade e *smoke tests*.
    - [ ] **M1.2:** Contratos, implementação e testes de `core` (IDs, enums, `SeedManager`, `config_hash`, `dataset_hash`, exceções/alertas).
    - [ ] **M1.3:** Contratos, implementação e testes de `metrics` (`MetricValue`, `UNDEFINED_NAN` e 15 métricas com tolerâncias específicas por família).
  - [ ] **M2 (`data` + `validation`):** Ingestão somente-leitura (`.csv`/`.txt` com ou sem cabeçalho, `unlabeled_pool`, alvo único/multivariado), `DatasetProfile`, `PreparationPlan` (`TargetTransformSpec`) e `PartitionPlan` auditado (`KFold`, `StratifiedKFold`, `GroupKFold`, `Bootstrap`, `TemporalSplit`, `Holdout`).
  - [ ] **M3 (`features`):** `ExploratoryFeatureReport`, `FixedFeatureScenario` e `DynamicFeatureScenario` ajustado por *fold* (seleção e redução de dimensionalidade) com índice de estabilidade.
  - [ ] **M4 (`models` + `tuning`):** `ModelSpec`, `ModelAdapter` com `clone_fresh` e incerteza preditiva, pré-processamento em 2 camadas (incluindo kernels pré-computados) e *Nested Search* (`Fixed`, `GridSearch`, `RandomSearch`).
  - [ ] **M5 (`orchestration`):** `MatrixOrchestrator`, isolamento de falhas (`FAULT_TOLERANT` / `FAIL_FAST`), paralelismo em 2 níveis, agregação de comitê e persistência com *checkpoint/resume*.
  - [ ] **M6 (`statistics`):** Consolidação, adequação metodológica, Nadeau-Bengio, Wilcoxon, Holm-Bonferroni, Benjamini-Hochberg, relevância prática, Fronteira de Pareto, funções de aquisição sequencial e `StructuredConclusion`.
  - [ ] **M7 (`reporting`):** Relatórios completos (MD/HTML), 7 famílias de tabelas (CSV/MD/LaTeX `booktabs`) e figuras (PNG/SVG/PDF), manifesto de proveniência e pacote de reprodutibilidade.
- [ ] **Fase 5: Verificação Experimental**
  - [ ] Reprodução do baseline científico do projeto de origem com paridade matemática e conceitual.
  - [ ] Validação de scripts e notebooks tutoriais guiados.

---

## Arquitetura em Camadas e Pipeline Operacional (6 Etapas)

| Etapa do Pipeline | Camada Arquitetural | Módulos (`src/experimental_ml/`) | Responsabilidade Central |
| :--- | :--- | :--- | :--- |
| **Etapa 1** | Camada 1: Definição e Triagem | `data` | Ingestão imutável (`.csv`, `.txt`, `DataFrame`), perfil diagnóstico completo (problemas confirmados vs. alertas heurísticos) e plano explícito de preparação. |
| **Etapa 2** | Camada 1: Definição e Triagem | `features` | Análise exploratória de relações e gerenciamento de cenários de atributos fixos (`FixedFeatureScenario`) e dinâmicos ajustados por *fold* (`DynamicFeatureScenario`). |
| **Etapa 3** | Camada 1: Definição e Triagem | `models`, `tuning` | Registro de modelos heterogêneos via `ModelAdapter`, pré-processamento em duas camadas, otimização aninhada (*Nested CV*) e extração de diagnósticos internos. |
| **Etapa 4** | Camada 2: Validação e Execução Matricial | `validation`, `orchestration` | Geração e validação do `PartitionPlan` compartilhado, execução matricial com tolerância a falhas, controle de paralelismo, *checkpoint/resume* e predições *out-of-fold*. |
| **Etapa 5** | Camada 3: Julgamento Estatístico e Publicação | `statistics` (com `metrics`) | Consolidação descritiva, avaliação de adequação de testes estatísticos, tamanho de efeito, relevância prática, análise multiobjetivo (Fronteira de Pareto e funções de aquisição) e conclusões rastreáveis. |
| **Etapa 6** | Camada 3: Julgamento Estatístico e Publicação | `reporting` | Geração somente-leitura de relatórios científicos (Markdown/HTML), 7 famílias de tabelas e figuras modulares, manifesto de proveniência e pacote de reprodutibilidade. |

*(Os módulos `core` e `metrics` formam a fundação transversal utilizada pelas três camadas).*

---

## Documentação de Engenharia

Os documentos técnicos de acompanhamento e especificação estão centralizados no diretório [`engenharia_software/`](engenharia_software/):

- [`engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`](engenharia_software/ETAPA_ATUAL_ENGENHARIA.md): Registro do estado atual do ciclo de vida da engenharia.
- [`engenharia_software/ESPECIFICACAO_REQUISITOS.md`](engenharia_software/ESPECIFICACAO_REQUISITOS.md): Especificação completa dos requisitos funcionais e não-funcionais das 6 etapas (SRS v2.0).
- [`engenharia_software/ARQUITETURA_E_CONTRATOS.md`](engenharia_software/ARQUITETURA_E_CONTRATOS.md): Arquitetura em camadas, pipeline operacional de 6 etapas, dependências entre módulos, contratos conceituais, modelo de dados, pacote de reprodutibilidade e recorte de MVP.
