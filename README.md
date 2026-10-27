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
  - [x] Definição do Grafo Direcionado Acíclico (DAG) de dependências entre as 6 etapas.
  - [x] Formalização dos contratos conceituais de entrada, saída, invariantes e pontos de extensão de cada módulo.
  - [x] Definição do modelo de dados do experimento, máquina de estados e árvore de diretórios do pacote de reprodutibilidade.
  - [x] Separação estratégica entre o **MVP Essencial** e as **Evoluções Posteriores Plugáveis**.
  - [x] Consolidação formal em [`ARQUITETURA_E_CONTRATOS.md`](engenharia_software/ARQUITETURA_E_CONTRATOS.md).
- [ ] **Fase 4: Implementação Guiada por Testes (TDD) do MVP**
  - [ ] Configuração do empacotamento e suíte de testes (`pyproject.toml`, `src/`, `tests/`).
  - [ ] Etapa 1: Módulo `data` e `diagnostics` (`DatasetBundle`, `DatasetProfile`, `PreparationPlan`).
  - [ ] Etapa 2: Módulo `features` e `scenarios` (`ExploratoryFeatureReport`, `FixedScenario`, `DynamicScenario`).
  - [ ] Etapa 3: Módulo `models` e `tuning` (`ModelSpec`, `ModelAdapter`, pipeline de 2 camadas e *Nested Search*).
  - [ ] Etapa 4: Módulo `validation`, `orchestration` e `metrics` (`PartitionPlan`, `MatrixOrchestrator`, persistência e *resume*).
  - [ ] Etapa 5: Módulo `statistics` (consolidação, Nadeau-Bengio, Wilcoxon, Holm-Bonferroni, Benjamini-Hochberg, Pareto e síntese estruturada).
  - [ ] Etapa 6: Módulo `reporting` e `packaging` (tabelas CSV/MD/LaTeX, figuras PNG/SVG/PDF, relatórios completos e pacote de reprodutibilidade).
- [ ] **Fase 5: Verificação Experimental**
  - [ ] Reprodução do baseline científico do projeto de origem com paridade matemática e conceitual.
  - [ ] Validação de scripts e notebooks tutoriais guiados.

---

## Arquitetura por Etapa do Ciclo Experimental

| Etapa | Módulos | Responsabilidade Central |
| :--- | :--- | :--- |
| **Etapa 1** | `data`, `diagnostics` | Ingestão imutável (`.csv`, `.txt`, `DataFrame`), perfil diagnóstico completo (problemas confirmados vs. alertas heurísticos) e plano explícito de preparação. |
| **Etapa 2** | `features`, `scenarios` | Análise exploratória de relações e gerenciamento de cenários de atributos fixos (`FixedScenario`) e dinâmicos ajustados por *fold* (`DynamicScenario`). |
| **Etapa 3** | `models`, `tuning` | Registro de modelos heterogêneos via `ModelAdapter`, pré-processamento em duas camadas, otimização aninhada (*Nested CV*) e extração de diagnósticos internos. |
| **Etapa 4** | `validation`, `orchestration` | Geração e validação do `PartitionPlan` compartilhado (CV e *Holdout* isolado), execução matricial com tolerância a falhas, controle de paralelismo, *checkpoint/resume* e predições *out-of-fold*. |
| **Etapa 5** | `metrics`, `statistics` | Cálculo de métricas, avaliação de adequação de testes estatísticos, tamanho de efeito, relevância prática, análise multiobjetivo (Fronteira de Pareto) e conclusões rastreáveis. |
| **Etapa 6** | `reporting`, `packaging` | Geração desacoplada de relatórios científicos (Markdown/HTML), 7 famílias de tabelas e figuras modulares, manifesto de proveniência e pacote de reprodutibilidade. |

---

## Documentação de Engenharia

Os documentos técnicos de acompanhamento e especificação estão centralizados no diretório [`engenharia_software/`](engenharia_software/):

- [`engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`](engenharia_software/ETAPA_ATUAL_ENGENHARIA.md): Registro do estado atual do ciclo de vida da engenharia.
- [`engenharia_software/ESPECIFICACAO_REQUISITOS.md`](engenharia_software/ESPECIFICACAO_REQUISITOS.md): Especificação completa dos requisitos funcionais e não-funcionais das 6 etapas (SRS v2.0).
- [`engenharia_software/ARQUITETURA_E_CONTRATOS.md`](engenharia_software/ARQUITETURA_E_CONTRATOS.md): Arquitetura geral, grafo de dependências, contratos conceituais, modelo de dados, pacote de reprodutibilidade e recorte de MVP.
