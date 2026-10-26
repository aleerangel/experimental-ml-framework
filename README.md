# experimental-ml-framework

Harness experimental agnóstico para pesquisa científica em Machine Learning (regressão e classificação). O projeto provê infraestrutura para ingestão, gestão de cenários de atributos, validação cruzada estrita sem vazamento de dados, orquestração matricial de experimentos, inferência estatística rigorosa e exportação de tabelas e gráficos para publicação.

---

## Progresso do Projeto

A evolução do projeto segue um ciclo de vida estruturado em 5 fases:

- [x] **Fase 1: Auditoria Técnica e Baseline**
  - [x] Auditoria do código e dados de origem (`prognose_florestal`).
  - [x] Catalogação dos resultados de referência ($R^2$, RMSE, MAE, KTA, HHL).
  - [x] Identificação de vulnerabilidades (acoplamentos a domínio, duplicações de código, distorções métricas).
- [ ] **Fase 2: Engenharia de Requisitos e Escopo**
  - [x] Definição da premissa arquitetural (ADR-001: framework não implementa modelos de ML internamente).
  - [x] Entrevista de levantamento de escopo macro com o pesquisador.
  - [x] Especificação de Requisitos de Software formalizada ([`ESPECIFICACAO_REQUISITOS.md`](engenharia_software/ESPECIFICACAO_REQUISITOS.md)).
  - [ ] Detalhamento dos testes estatísticos e relatórios diagnósticos.
- [ ] **Fase 3: Design da API e Contratos**
  - [ ] Definição dos protocolos de interface (`EstimatorProtocol`, `TransformerProtocol`).
  - [ ] Especificação da API dos módulos centrais (`data`, `features`, `validation`, `benchmark`, `metrics`, `statistics`, `reporting`).
  - [ ] Especificação dos testes de aceitação antes da codificação.
- [ ] **Fase 4: Implementação Guiada por Testes (TDD)**
  - [ ] Configuração do ambiente e empacotamento (`pyproject.toml`, `pytest`, linter).
  - [ ] Implementação do módulo `data` e `validation`.
  - [ ] Implementação de `features` e `ScenarioManager`.
  - [ ] Implementação de `metrics` (regressão e classificação).
  - [ ] Implementação de `statistics` (Nadeau-Bengio, Wilcoxon, correções de multiplicidade).
  - [ ] Implementação de `tuning` e `benchmark` matricial com execução paralela (`n_jobs`).
  - [ ] Implementação de `reporting` (tabelas LaTeX/Markdown, gráficos e texto explicativo).
- [ ] **Fase 5: Verificação Experimental**
  - [ ] Reprodução do baseline científico do projeto de origem com paridade matemática.
  - [ ] Validação de notebooks tutoriais guiados.

---

## Estrutura de Módulos Planejada

| Módulo | Responsabilidade Principal |
| :--- | :--- |
| `data` | Ingestão (.csv, .txt, DataFrame), checagem estrutural e alertas pedagógicos. |
| `features` | Análise de correlações, informação mútua, multicolinearidade e gestão de cenários (`ScenarioManager`). |
| `validation` | Estratégias de particionamento (K-Fold, Stratified, GroupKFold) com garantia de zero vazamento. |
| `models` | Protocolo de compatibilidade para modelos externos (Scikit-Learn, PyTorch, quânticos, analíticos). |
| `tuning` | Busca de hiperparâmetros (Grid/Random Search) aninhada e segura contra vazamento. |
| `benchmark` | Orquestração da matriz $\text{Modelos} \times \text{Cenários} \times \text{Folds}$ com suporte a `n_jobs`. |
| `metrics` | Cálculo vetorizado de métricas de regressão e classificação (pontuais e out-of-fold). |
| `statistics` | Testes de hipótese (Nadeau-Bengio, Wilcoxon, Holm-Bonferroni, FDR) e síntese textual. |
| `reporting` | Exportação de tabelas (LaTeX `booktabs`, Markdown, CSV) e gráficos em alta resolução (300 DPI). |

---

## Documentação de Engenharia

Os documentos técnicos de acompanhamento e especificação estão centralizados no diretório [`engenharia_software/`](engenharia_software/):

- [`engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`](engenharia_software/ETAPA_ATUAL_ENGENHARIA.md): Registro do estado atual do ciclo de vida e decisões arquiteturais.
- [`engenharia_software/ESPECIFICACAO_REQUISITOS.md`](engenharia_software/ESPECIFICACAO_REQUISITOS.md): Especificação completa dos requisitos funcionais (RF01-RF24) e não-funcionais (RNF01-RNF07).
