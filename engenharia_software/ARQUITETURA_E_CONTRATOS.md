# Especificação Arquitetural, Contratos Conceituais e Modelo de Dados — `experimental-ml-framework`

> **Documento:** Arquitetura de Software, Contratos de Módulos, Modelo de Dados e Recorte de MVP  
> **Versão:** 1.0.0  
> **Data:** 27 de Outubro de 2026  
> **Status:** Consolidado e Aprovado (Fases 2 e 3)  
> **Documentos Relacionados:** [`ESPECIFICACAO_REQUISITOS.md`](./ESPECIFICACAO_REQUISITOS.md) | [`ETAPA_ATUAL_ENGENHARIA.md`](./ETAPA_ATUAL_ENGENHARIA.md)

---

## Sumário

1. [Visão Geral da Arquitetura e Princípios Diretores](#1-visão-geral-da-arquitetura-e-princípios-diretores)
2. [Grafo de Dependências e Fluxo Operacional das 6 Etapas](#2-grafo-de-dependências-e-fluxo-operacional-das-6-etapas)
3. [Especificação Detalhada dos Contratos por Etapa](#3-especificação-detalhada-dos-contratos-por-etapa)
   - [3.1 Etapa 1: Entrada, Triagem e Diagnóstico Estrutural da Base](#31-etapa-1-entrada-triagem-e-diagnóstico-estrutural-da-base)
   - [3.2 Etapa 2: Exploração de Relações e Cenários de Features](#32-etapa-2-exploração-de-relações-e-cenários-de-features)
   - [3.3 Etapa 3: Registro de Modelos, Circuitos, Pré-processamento e Hiperparâmetros](#33-etapa-3-registro-de-modelos-circuitos-pré-processamento-e-hiperparâmetros)
   - [3.4 Etapa 4: Particionamento, Validação e Execução Matricial](#34-etapa-4-particionamento-validação-e-execução-matricial)
   - [3.5 Etapa 5: Consolidação dos Resultados e Julgamento Estatístico](#35-etapa-5-consolidação-dos-resultados-e-julgamento-estatístico)
   - [3.6 Etapa 6: Relatórios Científicos, Visualizações e Pacote de Reprodutibilidade](#36-etapa-6-relatórios-científicos-visualizações-e-pacote-de-reprodutibilidade)
4. [Modelo de Dados do Experimento e Rastreabilidade](#4-modelo-de-dados-do-experimento-e-rastreabilidade)
5. [Estrutura do Pacote de Reprodutibilidade em Disco](#5-estrutura-do-pacote-de-reprodutibilidade-em-disco)
6. [Recorte Estratégico: MVP Essencial vs. Evoluções Posteriores](#6-recorte-estratégico-mvp-essencial-vs-evoluções-posteriores)
7. [Ordem de Implementação (Marcos M1–M7) e Testes de Aceitação](#7-ordem-de-implementação-marcos-m1m7-e-testes-de-aceitação)
8. [Protocolo de Reprodução Agnóstica do Experimento de Referência (`prognose_florestal`)](#8-protocolo-de-reprodução-agnóstica-do-experimento-de-referência-prognose_florestal)

---

## 1. Visão Geral da Arquitetura e Princípios Diretores

O `experimental-ml-framework` é projetado como um **harness científico agnóstico** voltado à experimentação controlada em Aprendizado de Máquina (regressão e classificação). Sua arquitetura obedece a sete princípios estruturantes:

1. **Agnosticismo de Modelos e Bibliotecas (ADR-001):** O núcleo do framework não implementa algoritmos preditivos próprios; ele orquestra modelos externos (clássicos, redes neurais, circuitos/resolvedores quânticos, equações analíticas e biométricas) por meio de contratos e adaptadores padronizados.
2. **Imutabilidade dos Dados de Origem e Zero Transformação Silenciosa:** A base original nunca é alterada durante a triagem ou exploração. Nenhuma imputação, codificação, remoção ou escalonamento ocorre sem configuração explícita ou ciência documentada do pesquisador.
3. **Prevenção Estrutural contra Vazamento de Dados (*Zero Data Leakage by Design*):** Qualquer operação que aprenda parâmetros a partir dos dados (imputação, escalonamento, codificação baseada em frequência, seleção dinâmica de atributos e otimização de hiperparâmetros) é ajustada exclusivamente dentro dos dados de treinamento de cada partição (*fold*) externa.
4. **Orientação Pedagógica e Transparência Metodológica:** Problemas estruturais confirmados são separados de alertas heurísticos. Limitações do desenho experimental, pressupostos estatísticos não atendidos e falhas parciais são reportados explicitamente, sem mascarar erros nem fabricar conclusões não sustentadas pelas evidências.
5. **Desacoplamento entre Execução, Julgamento Estatístico e Apresentação:** Os resultados brutos da execução matricial (Etapa 4) são persistidos de modo que análises estatísticas (Etapa 5) e relatórios/gráficos (Etapa 6) possam ser reexecutados, reconfigurados ou reestilizados sem retreinar modelos.
6. **Extensibilidade Aberta/Fechada (*Open/Closed Principle*):** Novos leitores de dados, estratégias de seleção de atributos, adaptadores de modelos, métodos de busca de hiperparâmetros, esquemas de particionamento, testes estatísticos e exportadores de relatórios podem ser adicionados via protocolos sem alterar o núcleo experimental.
7. **Rastreabilidade e Linhagem Ponta a Ponta:** Cada métrica agregada, resultado estatístico, tabela ou figura mantém referência explícita aos identificadores do experimento, do plano de particionamento, das células de execução e das observações que lhe deram origem.

---

## 2. Grafo de Dependências e Fluxo Operacional das 6 Etapas

O fluxo experimental organiza-se como um **Grafo Direcionado Acíclico (DAG)** dividido em três macrocamadas:

1. **Camada de Definição e Triagem (Etapas 1, 2 e 3):** Opera sem treinamento de modelos finais. Diagnostica os dados, explora relações entre variáveis, define cenários de atributos e registra especificações de modelos e espaços de busca.
2. **Camada de Particionamento e Execução (Etapa 4):** Gera e valida o plano de particionamento independente e executa a matriz experimental $(\text{Modelos} \times \text{Cenários} \times \text{Partições})$ com isolamento de estado, tolerância a falhas e persistência incremental.
3. **Camada de Inferência e Publicação (Etapas 5 e 6):** Consome os artefatos persistidos da Etapa 4 para consolidar métricas, realizar testes de hipóteses estatísticas, avaliar compromissos multiobjetivo e renderizar relatórios científicos e pacotes de reprodutibilidade.

```mermaid
flowchart TD
    subgraph Camada_1["1. Camada de Definição e Triagem (Sem Treinamento de Modelos)"]
        E1["Etapa 1: Entrada e Diagnóstico<br/>Módulo: data & diagnostics"]
        E2["Etapa 2: Exploração e Cenários<br/>Módulo: features & scenarios"]
        E3["Etapa 3: Registro de Modelos e Tuning<br/>Módulo: models & tuning"]
    end

    subgraph Camada_2["2. Camada de Validação e Execução Matricial"]
        E4A["Etapa 4A: Plano de Particionamento<br/>Módulo: validation"]
        E4B["Etapa 4B: Orquestrador da Matriz<br/>Módulo: orchestration & storage"]
    end

    subgraph Camada_3["3. Camada de Julgamento Estatístico e Publicação"]
        E5["Etapa 5: Consolidação e Estatística<br/>Módulo: metrics & statistics"]
        E6["Etapa 6: Relatórios e Reprodutibilidade<br/>Módulo: reporting & packaging"]
    end

    E1 -->|"DatasetBundle + DatasetProfile + PreparationPlan"| E2
    E1 -->|"DatasetBundle (obs_id, target, group)"| E4A
    E1 -->|"PreparationPlan (regras declaradas)"| E4B
    E2 -->|"ScenarioRegistry (Cenários Fixos e Dinâmicos)"| E4B
    E3 -->|"ModelRegistry (ModelSpecs + Adapters + SearchSpecs)"| E4B
    E4A -->|"PartitionPlan (Imutável e Validado)"| E4B
    E4B -->|"MatrixRunStore (Células, Predições OOF, Tempos, Diagnósticos)"| E5
    E1 -.->|"Diagnóstico Inicial da Base"| E6
    E2 -.->|"Especificação e Exploração de Cenários"| E6
    E3 -.->|"Catálogo de Modelos e Configurações"| E6
    E4A -.->|"Especificação das Partições"| E6
    E4B -.->|"Histórico de Execuções, Falhas e Diagnósticos"| E6
    E5 -->|"StatisticalJudgmentReport + MultiObjectiveSummary"| E6
```

### Regras de Dependência entre Módulos e Layout Físico (`src/experimental_ml/`)

Para eliminar qualquer possibilidade de dependência circular (especialmente no uso de métricas durante o *tuning* na Etapa 3, na avaliação de células na Etapa 4 e nos testes estatísticos na Etapa 5), a arquitetura física divide-se em **10 pacotes internos com ordem topológica estrita**:

1. **`core` (Nível 0 — Fundação):** Identificadores tipados, enumerações, protocolos base, política hierárquica de sementes (`SeedSequence`), utilitários de hash (`SHA-256`), serialização JSON determinística e hierarquia de exceções/alertas. Não depende de nenhum outro pacote do framework.
2. **`metrics` (Nível 1 — Motor de Métricas):** Cálculo vetorizado de métricas de regressão, classificação e alinhamento (incluindo KTA quando aplicável), metadados de direção (`MAXIMIZE` / `MINIMIZE`) e escopo (`PER_FOLD`, `FOLD_AGGREGATION`, `POOLED_OOF`, `FINAL_HOLDOUT`). Depende apenas de `core`.
3. **`data` (Nível 1 — Ingestão, Diagnóstico e Saneamento):** `DatasetBundle`, `DatasetProfile`, `DiagnosticFinding`, `PreparationPlan` e `SanitizedDatasetView`. Depende apenas de `core`.
4. **`validation` (Nível 2 — Particionamento):** `PartitionPlan`, estratégias de divisão (`KFold`, `StratifiedKFold`, `GroupKFold`, `TemporalSplit`, `Holdout`) e validador matemático de invariantes de partição. Depende de `core` e `data`.
5. **`features` (Nível 2 — Exploração e Cenários):** `ExploratoryFeatureReport`, `FixedFeatureScenario`, `DynamicFeatureScenario`, `ScenarioRegistry` e protocolo `FeatureSelectionStrategy` (incluindo filtro de colinearidade, Top-$K$ univariado e ranking ponderado multi-critério). Depende de `core`, `data` e `metrics`.
6. **`models` (Nível 2 — Especificação e Adaptadores de Modelos):** `ModelSpec`, `ModelCapabilities`, `ModelAdapter` (clássicos, analíticos/biométricos com `requires_fit=False`, circuitos/resolvedores quânticos), `ModelDiagnostics` e `TwoLayerPreprocessingPipeline`. Depende de `core`.
7. **`tuning` (Nível 3 — Otimização Aninhada):** `HyperparameterSearchSpec` e executores de busca (`Fixed`, `GridSearch`, `RandomSearch`) operando estritamente sobre partições internas do conjunto de treino externo. Depende de `core`, `metrics`, `validation`, `features` e `models`.
8. **`orchestration` (Nível 4 — Execução Matricial e Persistência):** `MatrixOrchestrator`, máquina de estados de `ExecutionCell`, isolamento de falhas (`FAULT_TOLERANT` / `FAIL_FAST`), controle de paralelismo em dois níveis, `CellResultRecord` e `MatrixRunStore` (*checkpoint/resume*). Depende de `core`, `metrics`, `data`, `validation`, `features`, `models` e `tuning`.
9. **`statistics` (Nível 5 — Consolidação e Julgamento Estatístico):** `DescriptiveConsolidator`, `MethodSuitabilityEvaluator`, testes de hipóteses (Nadeau-Bengio, Wilcoxon, correções de Holm-Bonferroni e Benjamini-Hochberg), tamanho de efeito, relevância prática, `MultiObjectiveSummary` (Fronteira de Pareto) e `ConclusionSynthesizer`. Depende de `core`, `metrics`, `validation` e `orchestration` (leitura de `MatrixRunStore`).
10. **`reporting` (Nível 6 — Relatórios, Tabelas, Figuras e Pacote de Reprodutibilidade):** `ReportContentSelector`, `TableBuilder`, `FigureSpecBuilder`, renderizadores (CSV, Markdown, HTML, LaTeX `booktabs`, PNG/SVG/PDF), `ArtifactProvenance` e `ReproducibilityPackager`. Consome em modo somente-leitura os artefatos de todos os níveis anteriores.

---

### Decisões Arquiteturais Complementares (ADRs 002 a 006)

* **ADR-002 (Separação entre Saneamento Estrutural Pré-Partição e Transformação Parametrizada Intra-Fold):**
  * Operações determinísticas que definem o universo amostral válido sem estimar parâmetros da distribuição (ex.: remoção de linhas com `target` ausente, exclusão de colunas proibidas/constantes e coerção básica de tipos declarada no `PreparationPlan`) geram uma `SanitizedDatasetView` com `observation_ids` imutáveis *antes* do `PartitionPlan`.
  * Operações parametrizadas que aprendem estatísticas dos dados (imputação por média/mediana/moda, codificação de categorias, seleção dinâmica de atributos e escalonamento) são organizadas em exatamente **duas camadas intra-fold**: **Camada 1 (Cenário)** e **Camada 2 (Específica do Modelo)**, ajustadas exclusivamente no treino de cada partição.
* **ADR-003 (Ordem Canônica Intra-Célula e Prevenção de Vazamento no Nested Tuning):**
  * Quando uma célula combina `DynamicFeatureScenario` e `HyperparameterSearchSpec` (`GRID_SEARCH` ou `RANDOM_SEARCH`), a transformação e a seleção dinâmica de atributos são ajustadas **dentro de cada fold interno** da validação cruzada de hiperparâmetros para avaliar os candidatos sem vazamento interno. Após selecionar $\theta^*$, o pipeline `(Camada 1 -> Seleção Dinâmica -> Camada 2 -> Modelo(\theta^*))` é reajustado sobre o conjunto de treino externo completo daquele *fold*, registrando os atributos finais selecionados, e avaliado uma única vez sobre o conjunto de validação externo.
* **ADR-004 (Regras Matemáticas e Condições de Contorno para Testes Estatísticos):**
  * **Nadeau-Bengio (2003):** Exige $J \ge 2$ partições de validação cruzada pareadas. Quando a razão $n_{\text{val}, j} / n_{\text{train}, j}$ variar entre *folds* (ex.: `GroupKFold`), utiliza a razão média efetiva $\overline{(n_{\text{val}} / n_{\text{train}})}$ sobre os *folds* válidos e emite alerta metodológico caso o coeficiente de variação do tamanho dos *folds* supere $20\%$. Se a variância das diferenças for nula ($s^2_d = 0$), retorna diferença nula sem divisão por zero.
  * **Wilcoxon Pareado:** Trata diferenças nulas ($d_j = 0$) explicitamente (método de Pratt/Wilcoxon) e emite alerta obrigatório de baixo poder estatístico quando $J < 6$ (dado que o menor $p$-valor bicaudal atingível para $J=5$ é $0.0625 > 0.05$).
* **ADR-005 (Desacoplamento do Motor de Métricas e Semântica Estrita de `UNDEFINED_NAN`):**
  * O pacote `metrics` situa-se no Nível 1 da arquitetura para atender simultaneamente ao `tuning` (Etapa 3), ao fechamento de cada `ExecutionCell` (Etapa 4) e à consolidação estatística (Etapa 5) sem dependências circulares.
  * **Semântica de `MetricStatus.UNDEFINED_NAN`:**
    1. *Proibição de Coerção para Zero:* Um `MetricValue` indefinido possui `value = float("nan")` e `status = MetricStatus.UNDEFINED_NAN`. É proibido convertê-lo silenciosamente em `0.0`.
    2. *No Tuning (`tuning`):* Se um candidato $\theta_i$ produzir `UNDEFINED_NAN` na métrica de otimização em qualquer *fold* interno, sua agregação recebe `UNDEFINED_NAN` e ele jamais pode vencer um candidato `VALID`. Se todos os candidatos do espaço de busca produzirem `UNDEFINED_NAN`, o *tuner* lança `TuningOptimizationError`, marcando a célula como `FAILED`.
    3. *Na Agregação entre Folds (`FOLD_AGGREGATION`):* Reporta `coverage = valid_folds / total_folds`. Se `valid_folds == total_folds`, retorna `VALID`; se $0 < \text{valid\_folds} < \text{total\_folds}$, retorna `PARTIAL_COVERAGE` (calculando estatísticas condicionais sobre os *folds* válidos com `MethodologicalWarning` obrigatório); se `valid_folds == 0`, retorna `UNDEFINED_NAN`.
    4. *Em Rankings, Comparações e Pareto (`statistics`):* Configurações com `UNDEFINED_NAN` na métrica analisada recebem status `UNRANKABLE`, são excluídas da Fronteira de Pareto e listadas separadamente como não avaliáveis.
* **ADR-006 (Persistência Escalável com Fallback Determinístico):**
  * O armazenamento de partições e predições individuais (`splits` e `predictions`) suporta Parquet quando motores colunares (`pyarrow`/`fastparquet`) estiverem presentes no ambiente e provê *fallback* automático e transparente para formato tabular nativo comprimido (`.csv.gz` / `.npz` acompanhado de metadados de esquema em `.json`), garantindo operação 100% autônoma.
* **ADR-007 (Contrato Formal de Serialização Canônica e Distinção entre `config_hash` e `dataset_hash`):**
  * **`config_hash(obj) -> str` (Objetos de Configuração e Metadados):** Produz digest `SHA-256` hexadecimal minúsculo (64 caracteres) sobre bytes UTF-8 de uma representação JSON canônica determinística:
    1. *Strings e Unicode:* Normalização obrigatória **Unicode NFC** (`unicodedata.normalize("NFC", s)`) antes da codificação UTF-8 (`ensure_ascii=False`).
    2. *Tipos Escalares:* Booleanos (`bool`, `np.bool_`) são verificados antes de `int` e serializados como `true`/`false`; inteiros (`int`, `np.integer`) em base 10; flutuantes (`float`, `np.floating`) convertidos para IEEE 754 `float64`, com `-0.0` normalizado para `0.0` e finitos formatados via `repr(float(x))`.
    3. *Valores Especiais:* `None` $\rightarrow$ `null`; `NaN`, `+Inf` e `-Inf` (incluindo quaisquer variantes de *payload* de `NaN`) são normalizados para objetos canônicos `{"__float_special__": "NaN" | "+Inf" | "-Inf"}`.
    4. *Coleções e Objetos Aninhados:* `Mapping` com chaves NFC ordenadas lexicograficamente por *code points* UTF-8 e separadores compactos `(",", ":")`; `tuple` $\rightarrow$ `{"__type__": "tuple", "items": [...]}`; `set`/`frozenset` $\rightarrow$ `{"__type__": "set", "items": [...]}` ordenado pelos hashes canônicos de seus itens; `Enum` e `dataclass` com qualificador explícito `{"__type__": Cls.__qualname__, ...}`.
  * **`dataset_hash(data, schema) -> str` (Dados Tabulares e Arrays):** Calcula `SHA-256` em fluxo binário sem materializar JSON gigante: concatena o `config_hash` do esquema ordenado de colunas e `observation_ids` com os buffers binários por coluna em *little-endian* (`<f8` para flutuantes com `-0.0 -> +0.0` e `NaN` normalizado para quiet NaN `0x7ff8000000000000`; `<i8` para inteiros; `|u1` para booleanos; marcador de nulo `\x00` vs `\x01` + tamanho `<Q` + UTF-8 NFC para texto/categorias).
  * *Escopo e Limitação Declarada:* O contrato garante reprodutibilidade de hashes para os mesmos valores lógicos sob IEEE 754, mas não elimina diferenças numéricas a montante geradas por bibliotecas externas não-determinísticas (ex.: reduções paralelas em GPU/BLAS).

---

## 3. Especificação Detalhada dos Contratos por Etapa

---

### 3.1 Etapa 1: Entrada, Triagem e Diagnóstico Estrutural da Base

#### Responsabilidade
Carregar a base de dados preservando sua integridade original, mapear papéis das variáveis (`target`, `group`, `observation_id`, `time_index`, `ignore_cols`), executar um diagnóstico exploratório completo e registrar o plano explícito de preparação.

#### Entradas Conceituais
* Fonte de dados (`.csv`, `.txt` com delimitadores configuráveis/detectáveis ou `DataFrame` em memória).
* Especificação de papéis de colunas (`DatasetSchemaSpec`):
  * `target_col`: variável resposta (contínua para regressão; discreta/categórica para classificação).
  * `task_type`: `REGRESSION` | `BINARY_CLASSIFICATION` | `MULTICLASS_CLASSIFICATION`.
  * `group_col` *(opcional)*: variável de agrupamento hierárquico/espacial/indivíduo.
  * `observation_id_col` *(opcional)*: identificador único estável por observação (gerado de forma determinística caso omitido).
  * `time_col` *(opcional)*: variável de ordenação cronológica.
  * `ignore_cols` *(opcional)*: colunas informativas ou proibidas que não devem entrar como preditores.

#### Saídas Conceituais (Contratos)
1. **`DatasetBundle`:**
   * Referência somente-leitura aos dados originais.
   * Hash criptográfico (`SHA-256`) da fonte de dados e esquema de colunas.
   * Vetor de identificadores estáveis de observação (`observation_ids`).
2. **`DatasetProfile`:**
   * **Resumo Estrutural:** número de linhas, número de colunas, tamanho em bytes e estimativa de memória RAM.
   * **Tipagem Semântica por Coluna:** distinção entre numérica contínua, numérica discreta, categórica nominal/ordinal, booleana, temporal e identificador.
   * **Qualidade e Completude:** contagem e proporção de valores ausentes por coluna; quantidade e índices de linhas duplicadas; identificação de colunas constantes (variância zero) ou quase-constantes; detecção heurística de possíveis identificadores (cardinalidade próxima a $N$).
   * **Estatísticas Descritivas Numéricas:** média, mediana, desvio-padrão, mínimo, máximo, quartis ($Q_1, Q_2, Q_3$), amplitude e intervalo interquartil (IQR).
   * **Diagnóstico de Escala e Amplitude:** comparação de ordens de grandeza entre atributos numéricos para sinalizar disparidades de escala.
   * **Estatísticas Categóricas:** cardinalidade, frequências absolutas e proporções relativas de cada categoria.
   * **Perfil da Variável-Alvo:**
     * *Regressão:* distribuição empírica, assimetria, valores extremos e presença de nulos.
     * *Classificação:* frequências absolutas e relativas por classe, razão de desbalanceamento e alerta para classes raras.
   * **Perfil da Variável de Agrupamento (quando presente):** número total de grupos, distribuição de observações por grupo (mínimo, mediana, máximo) e identificação de grupos com número reduzido de amostras.
   * **Lista Classificada de Achados (`DiagnosticFinding`):** separação estrita entre:
     * `CONFIRMED_ISSUE`: problema estrutural objetivo (ex.: valores ausentes no `target`, atributo constante, coluna categórica sem codificação para modelo numérico).
     * `HEURISTIC_WARNING`: alerta metodológico ou estatístico que requer avaliação do pesquisador, sem impor correção obrigatória (ex.: possível coluna de ID, desbalanceamento moderado, grupos pequenos, diferença de escala).
3. **`PreparationPlan`:**
   * Declaração explícita das decisões de pré-processamento tomadas pelo pesquisador (imputação de ausentes, codificação de variáveis categóricas, exclusão de colunas ou observações inválidas).
   * Documenta qualquer estratégia padrão adotada, garantindo que nenhuma transformação que aprenda parâmetros seja executada na Etapa 1.

---

### 3.2 Etapa 2: Exploração de Relações e Cenários de Features

#### Responsabilidade
Oferecer análises exploratórias sobre as relações entre os atributos e com a variável-alvo, e permitir a definição, inspeção e versionamento de **Cenários de Features** (fixos e dinâmicos), assegurando a distinção entre exploração e seleção experimental formal.

#### Entradas Conceituais
* `DatasetBundle`, `DatasetProfile` e `PreparationPlan`.
* Definições manuais de cenários ou regras parametrizadas de seleção de atributos.

#### Saídas Conceituais (Contratos)
1. **`ExploratoryFeatureReport`:**
   * Explicitamente marcado com o metadado `scope = EXPLORATORY_FULL_DATA`.
   * **Relações Atributo-Alvo:** correlações lineares (Pearson), monotônicas (Spearman), dependências não lineares (Informação Mútua compatível com regressão ou classificação) e medidas de associação compatíveis com o tipo de variável.
   * **Relações Atributo-Atributo (Redundância):** matrizes de correlação/associação entre preditores e pares que excedem limiares configuráveis de multicolinearidade.
   * **Avisos Metodológicos Integrados:** registro explícito de que (a) correlação não implica causalidade, (b) baixa correlação univariada não descarta relevância em interações multivariadas, e (c) estatísticas calculadas sobre a base completa não devem ser usadas para selecionar atributos de forma enviesada antes da divisão treino/validação.
2. **`FeatureScenario` (Hierarquia de Contratos):**
   * Campos comuns obrigatórios: `scenario_id`, `name`, `description`, `scientific_justification`, `preprocessing_config` (pré-processamento geral associado ao cenário).
   * **`FixedFeatureScenario`:**
     * Define uma lista estática e explícita de atributos (`selected_features: list[str]`), escolhida *a priori* por conhecimento de domínio ou baseline. Permanece idêntica em todas as partições.
   * **`DynamicFeatureScenario`:**
     * Define um pipeline/regra parametrizada de seleção (`selection_strategy: FeatureSelectionStrategy`, `strategy_params: dict`) — como redução de multicolinearidade, seleção por relevância ou Top-$K$.
     * **Garantia Invariante:** Não produz uma lista única global na Etapa 2; sua regra é executada exclusivamente sobre os dados de treino de cada *fold* durante a Etapa 4.
3. **`ScenarioRegistry`:**
   * Catálogo imutável e comparável dos cenários registrados para o experimento, permitindo inspeção pré-execução.

#### Ponto de Extensão (`FeatureSelectionStrategy`)
* Contrato `fit_select(X_train, y_train, random_state) -> SelectionResult`, retornando a lista ordenada de atributos selecionados naquele *fold*, os escores/estatísticas calculados no treino e os parâmetros aplicados.

---

### 3.3 Etapa 3: Registro de Modelos, Circuitos, Pré-processamento e Hiperparâmetros

#### Responsabilidade
Registrar modelos heterogêneos sob um contrato unificado de orquestração, configurar o pré-processamento específico de cada família algorítmica, definir espaços de busca de hiperparâmetros e especificar a coleta de metadados e diagnósticos internos.

#### Entradas Conceituais
* Instância ou fábrica do modelo/algoritmo, metadados descritivos, requisitos de pré-processamento específico e especificação opcional de busca de hiperparâmetros.

#### Saídas Conceituais (Contratos)
1. **`ModelSpec`:**
   * `model_id`: identificador único e estável no experimento.
   * `display_name`: nome de apresentação para tabelas e gráficos.
   * `family`: categoria metodológica (`CLASSICAL_ML`, `NEURAL_NETWORK`, `QUANTUM_CIRCUIT`, `QUANTUM_SOLVER`, `ANALYTICAL_EQUATION`, `BIOMETRIC_MODEL`, `BASELINE`, `CUSTOM`).
   * `description` e `scientific_justification`.
   * `technology_info`: biblioteca principal, versão, backend de execução (CPU, GPU, simulador quântico, QPU).
   * `random_seed_policy`: como a semente é propagada ou indicação de algoritmo determinístico/estocástico.
   * `capabilities` (`ModelCapabilities`):
     * `requires_fit: bool` (permite `False` para equações analíticas prontas).
     * `supports_predict: bool`.
     * `supports_predict_proba: bool` (para classificação).
     * `supports_decision_function: bool`.
     * `supports_sample_weight: bool`.
     * `supports_internal_parallelism_control: bool`.
     * `expected_input_types`: restrições de tipo, escala, ausência de nulos ou dimensionalidade.
2. **`ModelAdapter` (Contrato de Execução e Isolamento):**
   * `clone_fresh(seed) -> ModelInstance`: instancia um objeto completamente novo e isolado para cada execução, impedindo contaminação de pesos, estados internos ou parâmetros entre *folds*, cenários ou tentativas de *tuning*.
   * `fit(model_instance, X_train, y_train, **fit_kwargs) -> FitDiagnostics` (no-op transparente quando `requires_fit == False`).
   * `predict(model_instance, X_eval) -> ndarray`.
   * `predict_proba(model_instance, X_eval) -> ndarray | None`.
   * `extract_diagnostics(model_instance, phase) -> ModelDiagnostics`: extrai metadados internos específicos da família algorítmica sem obrigar um esquema rígido global:
     * *Quânticos / HHL:* número de qubits, profundidade do circuito, contagem de portas, número de *shots*, backend, fidelidade de estado, número de condição, diagnósticos do resolvedor.
     * *Redes Neurais:* épocas executadas, curvas de perda de treino/validação interna, critério de parada atingido.
     * *Analíticos / Biométricos:* equação funcional, coeficientes ajustados ou fixos, parâmetros calibrados.
     * *Clássicos:* importância de atributos, suporte de vetores, profundidade de árvores, número de iterações até convergência.
3. **`TwoLayerPreprocessingPipeline`:**
   * **Camada 1 (Cenário):** transformações vinculadas aos atributos do cenário.
   * **Camada 2 (Específica do Modelo):** transformações exigidas pela tecnologia do modelo (ex.: normalização angular para portas de rotação quântica, padronização $Z$-score para redes neurais/SVM, conversão para `ndarray` numérico denso).
   * **Validador de Pipeline:**
     * Garante que ambas as camadas sejam ajustadas (`fit`) exclusivamente nos dados de treino da partição.
     * Detecta e impede duplicação acidental de transformações equivalentes entre a Camada 1 e a Camada 2 (salvo quando explicitamente forçada).
     * Verifica compatibilidade entre a saída da Camada 2 e `expected_input_types` do `ModelSpec`, emitindo mensagens claras em caso de incompatibilidade.
4. **`HyperparameterSearchSpec`:**
   * `search_type`: `FIXED` (sem busca), `GRID_SEARCH`, `RANDOM_SEARCH` ou `CUSTOM_TUNER`.
   * `param_space`: grade discreta ou distribuições parametrizadas.
   * `budget`: número máximo de avaliações/amostras e política de amostragem.
   * `optimization_metric`: métrica explícita definida pelo pesquisador.
   * `direction`: `MAXIMIZE` | `MINIMIZE`.
   * `inner_cv_strategy`: esquema de validação cruzada interna restrita exclusivamente ao conjunto de treinamento da partição externa (*Nested Cross-Validation*).

---

### 3.4 Etapa 4: Particionamento, Validação e Execução Matricial

#### Responsabilidade
Gerar e validar o plano de particionamento independente, garantir que todas as configurações comparadas compartilhem exatamente as mesmas partições, orquestrar a execução da matriz $(\text{Modelos} \times \text{Cenários} \times \text{Partições})$ com tolerância a falhas, controle de paralelismo e persistência com retomada (*resume*), e coletar predições, tempos e diagnósticos granulares.

#### Entradas Conceituais
* `DatasetBundle`, `PreparationPlan`, `ScenarioRegistry`, `ModelRegistry`.
* `ValidationConfig`: estratégia de particionamento externo, configuração opcional de *Holdout Final* e parâmetros do orquestrador (política de erro, paralelismo, diretório de persistência).

#### Saídas Conceituais (Contratos)
1. **`PartitionPlan`:**
   * `partition_plan_id` e hash criptográfico das divisões.
   * `evaluation_regime`:
     * `CROSS_VALIDATION_ONLY`
     * `HOLDOUT_ONLY`
     * `DEVELOPMENT_CV_PLUS_FINAL_HOLDOUT`
   * `cv_strategy`: `K_FOLD`, `STRATIFIED_K_FOLD`, `GROUP_K_FOLD`, `STRATIFIED_GROUP_K_FOLD`, `TEMPORAL_SPLIT`, etc.
   * `folds`: lista de partições contendo os `observation_id` exatos de `train` e `val` para cada `fold_id`.
   * `holdout_ids` *(quando aplicável)*: conjunto de `observation_id` estritamente isolado durante toda a exploração, seleção de atributos e ajuste de hiperparâmetros.
   * **Validador Pré-Execução de Partições:** verifica matematicamente antes de qualquer treino:
     * Interseção nula entre treino e validação em cada *fold* ($\text{Train}_k \cap \text{Val}_k = \emptyset$).
     * Interseção nula entre base de desenvolvimento e *Holdout Final*.
     * Isolamento estrito de grupos quando `group_col` for utilizado ($\text{Grupos}(\text{Train}_k) \cap \text{Grupos}(\text{Val}_k) = \emptyset$).
     * Ordem cronológica estrita em estratégias temporais ($\max(t_{\text{train}}) < \min(t_{\text{val}})$).
2. **`MatrixOrchestrator` e Máquina de Estados por Célula (`ExecutionCell`):**
   * Cada combinação $(m, c, f)$ recebe um `cell_id` único e transita pelos estados:
     ```mermaid
     stateDiagram-v2
         [*] --> PENDING
         PENDING --> RUNNING : Início da execução
         RUNNING --> COMPLETED : Sucesso e persistência validada
         RUNNING --> FAILED : Exceção / Falha de convergência / Memória
         PENDING --> CANCELLED : Interrupção pelo usuário / Fail-fast
         RUNNING --> CANCELLED : Interrupção externa
         FAILED --> PENDING : Reexecução seletiva solicitada
         CANCELLED --> PENDING : Retomada (Resume)
     ```
   * **Política de Tratamento de Falhas (`ErrorPolicy`):**
     * `FAULT_TOLERANT` (padrão para matrizes experimentais): captura a exceção, registra `error_type`, `error_message`, `traceback` e fase em que ocorreu (`PREPROCESSING`, `FEATURE_SELECTION`, `HYPERPARAMETER_TUNING`, `MODEL_FIT`, `PREDICTION`, `METRIC_COMPUTATION`), marca a célula como `FAILED` (jamais convertendo para métrica zero) e prossegue com as demais células independentes.
     * `FAIL_FAST` (modo depuração): interrompe imediatamente a bateria ao encontrar a primeira falha.
   * **Controle de Paralelismo em Dois Níveis (`ParallelismConfig`):**
     * `outer_n_jobs`: número de células executadas simultaneamente pelo orquestrador.
     * `inner_model_threads`: limite de threads internas por modelo (evitando *oversubscription* de CPU quando bibliotecas já paralelizam internamente).
   * **Pausa, Persistência Incremental e Retomada (`Checkpoint & Resume`):**
     * Ao concluir cada célula, seu registro e suas predições são persistidos atomicamente em disco.
     * Na retomada, o orquestrador valida a compatibilidade do `dataset_hash`, do `partition_plan_id`, das configurações de cenários/modelos e das versões relevantes, pulando as células `COMPLETED` e executando apenas as `PENDING`, `FAILED` (se solicitado) ou `CANCELLED`.
3. **`CellResultRecord`:**
   * Identificadores: `experiment_id`, `partition_plan_id`, `model_id`, `scenario_id`, `fold_id`, `phase` (`DEV_CV` ou `FINAL_HOLDOUT`).
   * Estado final (`status`), avisos e informações de erro (se `FAILED`).
   * Lista exata de `selected_features` utilizadas naquela célula (fundamental para auditar cenários dinâmicos).
   * Configuração efetiva de hiperparâmetros selecionada e resumo das tentativas da busca interna.
   * **Tempos Desagregados (`TimingBreakdown`):**
     * `preprocessing_time_s`
     * `feature_selection_time_s`
     * `tuning_time_s`
     * `circuit_compilation_time_s` *(quando aplicável e reportado pelo adaptador)*
     * `fit_time_s` (treinamento final do modelo selecionado)
     * `predict_time_s` (inferência sobre a partição de avaliação)
     * `evaluation_time_s` (cálculo de métricas)
   * **Métricas da Célula:** dicionário tipado com o valor de cada métrica calculada sobre aquela partição específica.
   * **Diagnósticos do Modelo (`ModelDiagnostics`):** metadados internos exportados pelo adaptador naquela execução.
   * **Referência para Predições Individuais (`PredictionArtifactRef`):** ponteiro para o armazenamento estruturado sob demanda (*lazy loading*), contendo para cada `observation_id` avaliado:
     * *Regressão:* `observation_id`, `y_true`, `y_pred`, `residual` ($y_{\text{true}} - y_{\text{pred}}$).
     * *Classificação:* `observation_id`, `y_true`, `y_pred_class`, e, quando disponíveis, `class_probabilities` ou `decision_scores`.
4. **Consolidação Out-of-Fold (`OOFconsolidationPolicy`):**
   * Quando a estratégia de particionamento garante que cada observação seja avaliada exatamente uma vez fora do treino (ex.: $K$-Fold convencional), o sistema permite consolidar o vetor completo *out-of-fold* indexado por `observation_id`.
   * Em esquemas com janelas sobrepostas ou múltiplas avaliações por observação, cada predição mantém seu vínculo estrito com `fold_id` sem fusão implícita indevida.
   * Toda métrica distingue explicitamente seu escopo de agregação:
     * `PER_FOLD`: valor individual no *fold* $k$.
     * `FOLD_AGGREGATION`: estatística agregada (média, desvio-padrão, mediana, IQR) calculada sobre os $K$ valores `PER_FOLD`.
     * `POOLED_OOF`: métrica calculada globalmente sobre o conjunto consolidado de predições *out-of-fold*.
     * `FINAL_HOLDOUT`: métrica calculada sobre o conjunto de *holdout* isolado.

---

### 3.5 Etapa 5: Consolidação dos Resultados e Julgamento Estatístico

#### Responsabilidade
Consolidar descritivamente os resultados da Etapa 4 e realizar comparações estatísticas, análises de tamanho de efeito, relevância prática e compromissos multiobjetivo (desempenho preditivo, estabilidade e custo computacional), produzindo conclusões estruturadas e auditáveis sem declarar vencedores arbitrários.

#### Arquitetura Interna em Três Subcamadas Independentes
1. **Subcamada 5A — Consolidação Descritiva e Cobertura (`DescriptiveConsolidator`):**
   * Reúne resultados por configuração `(model_id, scenario_id)`, verifica a completude dos *folds*, calcula estatísticas descritivas de desempenho, estabilidade de seleção de atributos e custos de tempo/recursos.
2. **Subcamada 5B — Motor de Inferência Estatística, Efeito e Multiobjetivo (`StatisticalInferenceEngine`):**
   * Recomenda e executa métodos estatísticos compatíveis com o desenho experimental, verifica pressupostos, calcula tamanhos de efeito, intervalos de incerteza, correções para múltiplas comparações, avaliações de relevância prática e fronteiras de Pareto.
3. **Subcamada 5C — Gerador de Conclusões Estruturadas e Rastreáveis (`ConclusionSynthesizer`):**
   * Traduz os campos tipados de 5A e 5B em conclusões estruturadas e texto explicativo em linguagem natural, vinculado estritamente aos números e limitações registradas.

#### Entradas Conceituais
* `MatrixRunStore` e `PartitionPlan`.
* **`ComparisonSpec` (Plano de Comparações definido pelo pesquisador):**
  * `comparison_scope`:
    * `MODELS_WITHIN_SCENARIO`: compara modelos fixando um cenário.
    * `SCENARIOS_WITHIN_MODEL`: compara cenários fixando um modelo.
    * `FULL_CONFIGURATIONS`: compara pares específicos `(Modelo, Cenário)`.
    * `AGAINST_BASELINE`: compara configurações elegíveis contra uma referência explícita `(baseline_model_id, baseline_scenario_id)`.
    * `ALL_PAIRWISE`: todas as combinações elegíveis par a par.
    * `PLANNED_HYPOTHESES`: contrastes planejados pelo pesquisador (ex.: ganho de incluir determinado grupo de variáveis).
  * `metrics_of_interest`: lista de métricas com direção explícita (`MINIMIZE` para RMSE/MAE/LogLoss; `MAXIMIZE` para $R^2$/Acurácia/F1/AUC).
  * `practical_relevance_thresholds` *(opcional)*: diferença mínima de relevância prática ($\Delta_{\text{min}}$) ou margem de equivalência/não-inferioridade definida pelo pesquisador para cada métrica.
  * `hypothesis_family_spec`: definição de quais comparações compõem uma mesma família de hipóteses para ajuste de multiplicidade.
  * `multi_objective_criteria` *(opcional)*: dimensões a equilibrar (ex.: erro preditivo vs. tempo de inferência/treino vs. estabilidade) e regra explícita de decisão (se o pesquisador desejar um ranking composto).

#### Regras de Adequação Metodológica e Incompletude
* **Seletor e Verificador de Métodos Estatísticos (`MethodSuitabilityEvaluator`):**
  * Avalia o regime de particionamento (`CROSS_VALIDATION` vs `SINGLE_HOLDOUT`), o número de partições efetivas ($J$), a estrutura de dependência entre partições (sobreposição dos conjuntos de treino na validação cruzada) e o pareamento das observações/partições.
  * Apresenta os métodos candidatos aplicáveis (ex.: teste $t$ corrigido de Nadeau-Bengio para validação cruzada, Wilcoxon pareado, testes em nível de predição para *holdout* único, testes globais para múltiplas configurações e procedimentos de correção como Holm-Bonferroni ou Benjamini-Hochberg), explicando:
    * Por que o método é adequado àquela estrutura;
    * Quais pressupostos foram verificados nos dados (ex.: simetria das diferenças, tamanho mínimo de amostra/partições, poder estatístico para $J \le 5$);
    * Quais pressupostos não são verificáveis automaticamente.
  * Proíbe tratar *folds* de validação cruzada como amostras independentes sem considerar a correlação induzida pela sobreposição de treino, e proíbe inventar variabilidade entre *folds* quando houver apenas um *holdout*.
* **Política para Resultados Incompletos (`IncompleteComparisonPolicy`):**
  * Nunca descarta silenciosamente *folds* falhos nem substitui falhas por valores numéricos arbitrários.
  * Registra explicitamente quais configurações e *folds* falharam, diferenciando falha de execução (`FAILED`), ausência de dado e indefinição matemática (ex.: divisão por zero em métrica).
  * Caso exista um subconjunto comum de partições válidas onde o pareamento seja preservado, pode apresentar a análise restrita a esse subconjunto **exclusivamente como análise condicional/alternativa**, documentando a perda de cobertura e o risco de viés caso a falha não seja aleatória.

#### Saídas Conceituais (Contratos)
1. **`StatisticalJudgmentReport`:**
   * **Contexto Experimental:** `comparison_id`, `experiment_id`, `partition_plan_id`, configurações comparadas, métrica e direção de otimização.
   * **Resumo Descritivo Pareado:** valores por *fold*, médias, desvios-padrão, medianas, IQRs, métricas *pooled OOF* e cobertura de execução (`completed_folds / total_folds`).
   * **Resultado Inferencial:**
     * Hipótese nula ($H_0$) e alternativa ($H_1$) testadas.
     * Método estatístico aplicado e parâmetros.
     * Diferença observada ($\Delta$) e identificação de qual configuração obteve melhor valor observado (respeitando a direção da métrica).
     * Estatística do teste (quando aplicável), $p$-valor original e $p$-valor ajustado (com identificação da família de hipóteses e método de correção).
     * Tamanho de efeito padronizado e em unidades originais da métrica.
     * Intervalo de confiança ou medida de incerteza compatível com o método.
   * **Validade Metodológica:** pressupostos verificados, pressupostos assumidos, alertas de baixo poder amostral, status de completude e limitações.
   * **Avaliação de Relevância Prática:** comparação da diferença observada e de seu intervalo de incerteza frente ao limiar $\Delta_{\text{min}}$ configurado pelo pesquisador (distinguindo claramente: *diferença estatisticamente significativa*, *diferença praticamente relevante*, *inconclusivo* e *evidência de equivalência quando testada formalmente*).
   * **Estabilidade e Custo Computacional:** variabilidade entre *folds*, estabilidade dos atributos selecionados (para cenários dinâmicos) e comparação dos tempos desagregados.
   * **Análise Multiobjetivo (`MultiObjectiveSummary`):** relação de dominância entre configurações e identificação das configurações pertencentes à **Fronteira de Pareto** (ex.: precisão vs. tempo de execução vs. parcimônia de atributos).
   * **Conclusão Estruturada (`StructuredConclusion`):** objeto tipado contendo `observed_leader`, `statistical_evidence_status`, `effect_magnitude_summary`, `practical_relevance_status`, `cost_tradeoff_summary`, `methodological_caveats` e `narrative_text` (texto explicativo auditável em que cada sentença referencia os campos numéricos correspondentes).

---

### 3.6 Etapa 6: Relatórios Científicos, Visualizações e Pacote de Reprodutibilidade

#### Responsabilidade
Consumir em modo somente-leitura os artefatos estruturados das Etapas 1 a 5 para construir tabelas, figuras, relatórios científicos completos e pacotes portáveis de reprodutibilidade e auditoria, sem recalcular silenciosamente resultados experimentais.

#### Arquitetura Interna em Quatro Subcamadas Desacopladas
1. **Seleção de Conteúdo (`ReportContentSelector`):** filtra quais etapas, cenários, modelos, métricas, comparações e diagnósticos farão parte da exportação (ex.: visão completa de laboratório vs. recorte enxuto para artigo ou relatório de IC).
2. **Construção de Artefatos Abstratos (`TableBuilder` & `FigureSpecBuilder`):** transforma os objetos estruturados das Etapas 1–5 em representações intermediárias independentes de formato (`TableModel` e `PlotSpecification`), acopladas ao seu manifesto de proveniência (`ArtifactProvenance`).
3. **Renderização de Formatos (`FormatRenderers`):** exporta `TableModel` para CSV, Markdown e LaTeX (`booktabs`), `PlotSpecification` para PNG (300 DPI), SVG e PDF, e compõe o Relatório Científico Completo em Markdown e HTML (extensível para LaTeX/PDF).
4. **Empacotamento e Auditoria (`ReproducibilityPackager`):** organiza a árvore de diretórios do experimento, calcula hashes de integridade, valida referências relativas e gera pacotes compartilháveis (completos ou reduzidos/sem dados sensíveis).

#### Catálogo das 7 Famílias de Tabelas e Visualizações Suportadas
* **Família A — Caracterização e Qualidade dos Dados (Etapa 1):**
  * *Tabelas:* resumo estrutural; tipos, ausentes e duplicatas; estatísticas descritivas numéricas; frequências categóricas e balanço de classes; alertas confirmados vs. heurísticos e plano de preparação.
  * *Visualizações:* histogramas/distribuições; frequências de classes/categorias; matrizes de correlação/associação; mapa de valores ausentes; distribuição de observações por grupo.
* **Família B — Cenários de Atributos (Etapa 2):**
  * *Tabelas:* composição e justificativa de cada cenário; métodos e parâmetros de seleção; contagem e diferenças de atributos; atributos selecionados por *fold* e índices de estabilidade.
  * *Visualizações:* matriz de presença/ausência de atributos por cenário; frequência de seleção de cada atributo ao longo dos *folds*; relações atributo-alvo (com selo explícito quando exploratórias).
* **Família C — Modelos, Circuitos e Configurações (Etapa 3):**
  * *Tabelas:* catálogo de modelos registrados, famílias, tecnologias e versões; espaços de busca e hiperparâmetros selecionados por *fold*; camadas de pré-processamento; diagnósticos internos.
  * *Visualizações:* superfície/histórico de otimização de hiperparâmetros; curvas de aprendizado de redes neurais; comparações entre configurações.
* **Família D — Desempenho Preditivo (Etapa 4 e 5A):**
  * *Tabelas:* métricas por modelo e cenário (por *fold*, agregadas e *pooled OOF*); comparação com *baselines*; resultados separados de validação cruzada vs. *holdout* final; mapa de cobertura e execuções incompletas.
  * *Visualizações:* comparação de métricas com barras de dispersão/incerteza; dispersão Observado vs. Predito (1:1) e distribuição/diagnóstico de resíduos (regressão); curvas ROC, Precisão-Revocação, matrizes de confusão e calibração (classificação).
* **Família E — Comparações Estatísticas e Relevância Prática (Etapa 5B):**
  * *Tabelas:* diferenças observadas ($\Delta$), estatísticas de teste, $p$-valores originais e ajustados, tamanhos de efeito, intervalos de incerteza, avaliação de relevância prática/equivalência e limitações metodológicas.
  * *Visualizações:* gráficos de diferenças pareadas com intervalos de confiança; matrizes de comparação entre configurações; gráficos de tamanho de efeito.
* **Família F — Estabilidade e Custo Computacional (Etapa 4 e 5):**
  * *Tabelas:* tempos desagregados (preparação, busca, compilação, treino, inferência, avaliação); uso de recursos; variabilidade entre partições; taxa de sucesso/falha.
  * *Visualizações:* *trade-off* desempenho vs. tempo de execução; **Fronteira de Pareto** para objetivos definidos; variação das métricas ao longo dos *folds*.
* **Família G — Artefatos Específicos de Famílias de Modelos (Extensível via Adaptadores):**
  * Tabelas, diagramas e arquivos próprios exportados opcionalmente pelos adaptadores (métricas e estrutura de circuitos quânticos/HHL, equações e coeficientes biométricos, importância de variáveis de modelos clássicos, histórico de épocas de redes neurais).

#### Distinção Epistemológica no Relatório Completo
O relatório separa explicitamente três naturezas de informação:
1. **Declarações do Pesquisador:** objetivo científico, justificativas de cenários, escolhas de métricas e limiares de relevância prática.
2. **Fatos Computacionais Registrados:** hashes, versões, partições, hiperparâmetros selecionados, métricas calculadas, tempos medidos, estatísticas de teste e falhas ocorridas.
3. **Interpretações Derivadas e Condicionadas:** conclusões explicativas geradas a partir dos testes estatísticos e das regras configuradas, sempre acompanhadas de suas condições de validade e limitações.

---

## 4. Modelo de Dados do Experimento e Rastreabilidade

O modelo de dados garante que qualquer resultado ou figura possa ser rastreado até as observações e configurações que o produziram.

```mermaid
erDiagram
    EXPERIMENT_MANIFEST ||--|| DATASET_BUNDLE : "avalia (dataset_hash)"
    EXPERIMENT_MANIFEST ||--|| PREPARATION_PLAN : "aplica"
    EXPERIMENT_MANIFEST ||--|| PARTITION_PLAN : "fixa (partition_plan_id)"
    EXPERIMENT_MANIFEST ||--|{ FEATURE_SCENARIO : "registra (scenario_id)"
    EXPERIMENT_MANIFEST ||--|{ MODEL_SPEC : "registra (model_id)"
    PARTITION_PLAN ||--|{ PARTITION_SPLIT : "contem (fold_id / holdout)"
    FEATURE_SCENARIO ||--|{ EXECUTION_CELL : "compoe"
    MODEL_SPEC ||--|{ EXECUTION_CELL : "compoe"
    PARTITION_SPLIT ||--|{ EXECUTION_CELL : "compoe"
    EXECUTION_CELL ||--o| CELL_RESULT_RECORD : "persiste (cell_id)"
    CELL_RESULT_RECORD ||--|{ OBSERVATION_PREDICTION : "indexa (observation_id)"
    CELL_RESULT_RECORD ||--o| MODEL_DIAGNOSTICS : "anexa"
    CELL_RESULT_RECORD }|--|{ STATISTICAL_COMPARISON : "alimenta (comparison_id)"
    STATISTICAL_COMPARISON ||--|| STRUCTURED_CONCLUSION : "sintetiza"
    STATISTICAL_COMPARISON ||--|{ ARTIFACT_PROVENANCE : "origina (artifact_id)"
```

### Garantias de Rastreabilidade (`ArtifactProvenance`)
Cada tabela exportada (`.csv`, `.md`, `.tex`) e cada figura (`.png`, `.svg`, `.pdf`) possui um registro de proveniência associado no manifesto contendo:
* `artifact_id` e hash `SHA-256` do arquivo gerado.
* `experiment_id` e `partition_plan_id`.
* Lista de `model_ids`, `scenario_ids`, `fold_ids`, `cell_ids` e `comparison_ids` utilizados.
* Métrica, escopo de agregação (`PER_FOLD`, `FOLD_AGGREGATION`, `POOLED_OOF`, `FINAL_HOLDOUT`) e teste estatístico aplicado.
* Parâmetros visuais/formatação e versão do gerador.

Isso permite regenerar qualquer figura ou tabela com novo estilo visual ou formato documental a partir dos dados já persistidos, distinguindo claramente no histórico do pacote uma **regeneração de apresentação** de uma **reexecução experimental**.

---

## 5. Estrutura do Pacote de Reprodutibilidade em Disco

Cada experimento é organizado em um diretório autocontido com referências exclusivamente relativas (portável entre máquinas e sistemas operacionais):

```text
experiments/run_<experiment_id>/
├── manifest.json                 # Identificação do experimento, objetivo, autor, timestamps e nível de reprodutibilidade
├── data/
│   ├── dataset_descriptor.json   # Esquema, papéis das colunas, hash SHA-256, procedência e política de licença/privacidade
│   └── dataset_profile.json      # Resultado completo do diagnóstico exploratório da Etapa 1
├── configuration/
│   ├── preparation_plan.json     # Regras explícitas de pré-processamento geral
│   ├── scenarios.json            # Cenários fixos e regras de cenários dinâmicos + justificativas científicas
│   ├── models.json               # Modelos registrados, famílias, capacidades, pré-processamento específico e espaços de busca
│   └── exploratory_features.json # Relatório exploratório da Etapa 2 (marcado como exploratório)
├── partitions/
│   ├── partition_plan.json       # Estratégia, parâmetros, semente e validação de integridade das partições
│   └── splits.parquet            # Mapeamento observation_id -> fold_id / train / val / holdout
├── runs/
│   ├── execution_state.json      # Estado global da matriz (COMPLETED, FAILED, PENDING, CANCELLED) para checkpoint/resume
│   └── cells/
│       └── cell_<m>_<c>_<f>.json # CellResultRecord: features selecionadas no fold, hiperparâmetros, métricas, tempos, erros
├── predictions/
│   └── pred_<m>_<c>_<f>.parquet  # Predições individuais por observation_id, valores reais, resíduos e probabilidades
├── artifacts/
│   └── model_<m>_<c>_<f>/        # Diagnósticos e artefatos específicos exportados pelo adaptador (quântico, biométrico, neural)
├── statistics/
│   ├── descriptive_summary.json  # Consolidações por fold, agregadas e pooled OOF + cobertura
│   ├── comparisons.json          # Resultados dos testes estatísticos, tamanhos de efeito, incerteza e relevância prática
│   ├── multi_objective.json      # Análise de custo vs desempenho e Fronteira de Pareto
│   └── conclusions.json          # Objetos StructuredConclusion auditáveis
├── tables/                       # Tabelas exportadas (.csv, .md, .tex)
├── figures/                      # Figuras exportadas (.png, .svg, .pdf) + configurações de geração
├── reports/                      # Relatórios científicos consolidados (report.md, report.html)
└── reproducibility/
    ├── environment.json          # Versão do Python, SO, CPU/GPU, versões exatas das bibliotecas e backends
    ├── seeds.json                # Registro hierárquico de todas as sementes aleatórias utilizadas
    ├── artifact_provenance.json  # Linhagem de cada tabela e figura até os registros de origem
    ├── checksums.sha256          # Hashes de integridade de todos os arquivos do pacote
    └── REPRODUCE.md              # Instruções automáticas de reprodução e declaração de dependências externas/dados privados
```

### Níveis Explícitos de Reprodutibilidade Suportados
1. **Nível 1 — Reprodução de Apresentação e Relatório (`REPORT_REGENERATION`):** Regenera tabelas, figuras e relatórios a partir de `statistics/`, `runs/` e `predictions/` sem reexecutar modelos nem testes.
2. **Nível 2 — Reprodução Analítica e Estatística (`STATISTICAL_REANALYSIS`):** Recalcula a Etapa 5 (novas comparações, métricas ou limiares de relevância prática) e a Etapa 6 a partir das predições e células já persistidas na Etapa 4.
3. **Nível 3 — Reexecução Experimental Compatível (`EXPERIMENTAL_REEXECUTION`):** Reexecuta o treinamento e avaliação da matriz na Etapa 4 usando o mesmo `PartitionPlan`, configurações e sementes, documentando eventuais fontes de não-determinismo de hardware ou backends externos.

---

## 6. Recorte Estratégico: MVP Essencial vs. Evoluções Posteriores

A construção será guiada por TDD (Fase 4), priorizando um **MVP Essencial** que implemente os contratos definitivos das 6 etapas ponta a ponta, permitindo adicionar as extensões posteriores como *plugins* sem refatoração arquitetural.

### 6.1 Escopo do MVP Essencial (Primeira Entrega Funcional Completa)

| Etapa | Componentes Essenciais do MVP |
| :--- | :--- |
| **Etapa 1**<br/>(`data`) | • Ingestão de `.csv`, `.txt` (delimitadores configuráveis/detectáveis) e `DataFrame` com cálculo de hash `SHA-256` e geração/validação de `observation_id`.<br/>• `DatasetProfile` completo: dimensões, uso de memória, tipos de colunas, ausentes, duplicatas, constantes, possíveis IDs, estatísticas descritivas numéricas, frequências categóricas, diagnóstico de escala/amplitude, perfil do `target` (regressão e classificação) e perfil de `group`.<br/>• Separação entre `CONFIRMED_ISSUE` e `HEURISTIC_WARNING`.<br/>• `PreparationPlan` explícito (imputação por média/mediana/moda/constante, codificação *One-Hot* e *Ordinal*, escalonamento *Standard* e *MinMax*, remoção explícita de colunas/linhas). |
| **Etapa 2**<br/>(`features`) | • `ExploratoryFeatureReport` com Pearson, Spearman, Informação Mútua (regressão e classificação) e detecção de pares colineares.<br/>• `FixedFeatureScenario` (lista manual com nome, descrição e justificativa científica).<br/>• `DynamicFeatureScenario` ajustado exclusivamente no treino de cada *fold* (estratégias iniciais: filtro de multicolinearidade, seleção Top-$K$ por correlação/informação mútua e ranking ponderado multi-critério em percentis).<br/>• Registro dos atributos selecionados por *fold* e cálculo de estabilidade da seleção entre partições. |
| **Etapa 3**<br/>(`models` & `tuning`) | • Contrato `ModelSpec`, `ModelCapabilities` e `ModelAdapter` com isolamento de instância (`clone_fresh`).<br/>• Adaptadores iniciais:<br/>  1. **Estimadores padrão Scikit-Learn / XGBoost** (regressão e classificação com `predict` e `predict_proba`);<br/>  2. **Modelos Analíticos / Equações Biométricas** (`requires_fit=False` ou com calibração customizada);<br/>  3. **Adaptador Customizado / Quântico / HHL** com suporte à exportação de `ModelDiagnostics` estruturados.<br/>• Pipeline de pré-processamento em 2 camadas (Cenário + Modelo) com validação de entrada e bloqueio de duplicação acidental.<br/>• Busca de hiperparâmetros aninhada (*Nested CV* no treino externo): configuração fixa, **Grid Search** e **Random Search** com métrica e direção explícitas. |
| **Etapa 4**<br/>(`validation` & `orchestration`) | • `PartitionPlan` imutável e validado antes da execução.<br/>• Estratégias iniciais: **K-Fold**, **Stratified K-Fold**, **Group K-Fold**, **Temporal Split** (corte cronológico / janela expansiva sem vazamento futuro) e **Holdout Simples**, operando nos 3 regimes (somente CV, somente Holdout, ou CV na base de desenvolvimento + Holdout Final isolado).<br/>• `MatrixOrchestrator` com máquina de estados por célula, modos `FAULT_TOLERANT` e `FAIL_FAST`, paralelismo multi-core (`outer_n_jobs`) e controle de threads internas (`inner_model_threads`).<br/>• Persistência incremental em disco e retomada verificada (*Checkpoint & Resume*).<br/>• Registro de tempos desagregados, diagnósticos do modelo e armazenamento de predições/resíduos indexados por `observation_id` (*out-of-fold* e *holdout*). |
| **Etapa 5**<br/>(`metrics` & `statistics`) | • **Métricas de Regressão e Alinhamento:** $R^2$, RMSE, RMSE relativo (%), MAE, MAPE, correlação de Pearson, Viés Médio (*Mean Bias Error*) e KTA (*Kernel Target Alignment* para avaliação de kernels/matrizes).<br/>• **Métricas de Classificação:** Acurácia, Acurácia Balanceada, Precisão, Revocação, F1-Score (macro/weighted), ROC-AUC e Log-Loss.<br/>• Escopos explícitos: `PER_FOLD`, `FOLD_AGGREGATION`, `POOLED_OOF` e `FINAL_HOLDOUT`.<br/>• Escopos de comparação: modelos em um cenário, cenários em um modelo, combinações completas, contra *baseline*, par a par e hipóteses planejadas.<br/>• Verificador de adequação metodológica e tratamento transparente de *folds* incompletos.<br/>• Métodos estatísticos iniciais: **Teste $t$ corrigido de Nadeau-Bengio**, **Teste pareado de Wilcoxon** (com verificação de pressupostos e alerta para $J \le 5$), correções de **Holm-Bonferroni** e **Benjamini-Hochberg**.<br/>• Cálculo de tamanho de efeito, intervalos de incerteza, avaliação de limiares de relevância prática, **Fronteira de Pareto** (desempenho vs. tempo/estabilidade) e gerador de `StructuredConclusion` auditável. |
| **Etapa 6**<br/>(`reporting` & `packaging`) | • Geração do pacote estruturado completo do experimento com manifesto, somas de verificação (`SHA-256`) e linhagem (`ArtifactProvenance`).<br/>• Relatório Científico Completo em **Markdown** e **HTML**.<br/>• Exportação modular de todas as famílias essenciais de tabelas em **CSV, Markdown e LaTeX (`booktabs`)**.<br/>• Exportação modular dos gráficos essenciais das Famílias A–G em **PNG (300 DPI), SVG e PDF**.<br/>• Regeneração de relatórios, tabelas e figuras a partir dos resultados persistidos sem retreino, e exportação de pacote reduzido/compartilhável sem caminhos absolutos. |

---

### 6.2 Evoluções Posteriores (Pós-MVP, Plugáveis via Contratos Existentes)

1. **Dados e Pré-processamento:** Leitores nativos para bancos SQL/Parquet de grande volume; imputadores multivariados iterativos/KNN; codificadores baseados em estatísticas regularizadas do alvo (*Target Encoding* aninhado por *fold*).
2. **Seleção de Atributos:** Seletores *Wrapper* (RFE), *Embedded* ($L_1$/Lasso) e importância por permutação (*Permutation Importance*) integrados ao protocolo `FeatureSelectionStrategy`.
3. **Modelos e Otimização:** Adaptadores especializados com gerenciamento nativo de GPU/épocas para PyTorch/TensorFlow; otimização Bayesiana (Optuna) via protocolo `TunerStrategy`.
4. **Particionamento e Execução:** Estratégias avançadas de séries temporais com *gap/purge* (*PurgedWindowSplit*), *StratifiedGroupKFold* e execução distribuída em clusters.
5. **Estatística Avançada:** Testes globais multi-configuração (Friedman + pós-testes de Nemenyi/Dunn), testes formais de equivalência (TOST) e testes específicos para comparação em *holdout* único (McNemar e *bootstrap* pareado de predições).
6. **Publicação:** Compilação direta de relatórios completos para PDF via motor LaTeX local e templates pré-configurados para normas de periódicos específicos.

---

## 7. Ordem de Implementação (Marcos M1–M7) e Testes de Aceitação

A ordem de implementação obedece estritamente à ordenação topológica do grafo de dependências e prioriza a mitigação precoce dos **maiores riscos científicos** (vazamento de dados, mutação silenciosa, contaminação de estado entre modelos, perda de pareamento entre *folds* e inferência estatística inválida).

| Marco | Módulos Incluídos | Riscos Científicos Mitigados | Testes de Aceitação Objetivos (Critérios de Aprovação) |
| :--- | :--- | :--- | :--- |
| **M1 — Fundação, Contratos Base e Motor de Métricas** | `core`, `metrics` | • Indefinição de direção de otimização;<br/>• Distorções numéricas em métricas (ex.: arredondamentos indevidos);<br/>• Falta de determinismo em sementes e hashes;<br/>• Coerção indevida de `NaN` para `0.0`. | • **TA-M1.1 (`M1.1`):** Ambiente virtual instalado, compatibilidade de versões verificada empiricamente e *smoke tests* aprovados.<br/>• **TA-M1.2 (`M1.2`):** Determinismo de `SeedManager`, distinção formal e testes de `config_hash` e `dataset_hash` (Unicode NFC, `-0.0`, `NaN`/`Inf`, coleções aninhadas).<br/>• **TA-M1.3 (`M1.3`):** Exatidão das 15 métricas com tolerâncias específicas (`rtol`/`atol`) por família, casos degenerados retornando `MetricStatus.UNDEFINED_NAN` e bloqueio de seleção/ranking para `UNDEFINED_NAN`. |
| **M2 — Ingestão Imutável, Diagnóstico e Particionamento Auditado** | `data`, `validation` | • Mutação silenciosa da base original;<br/>• Vazamento de grupos ou futuro temporal;<br/>• Inconsistência de partições entre modelos. | • **TA-M2.1 (Imutabilidade):** Verificar via hash `SHA-256` e inspeção de memória que o `DataFrame` original permanece bit a bit inalterado após `DatasetProfile` e `PreparationPlan`.<br/>• **TA-M2.2 (Diagnóstico):** Detecção exata de nulos no alvo (`CONFIRMED_ISSUE`) separada de alertas heurísticos (`HEURISTIC_WARNING` como colunas de alta cardinalidade, grupos pequenos e disparidade de escala).<br/>• **TA-M2.3 (Zero Leakage de Partição):** Asserção matemática em `KFold`, `StratifiedKFold`, `GroupKFold`, `TemporalSplit` e `Holdout` provando: $\text{Train}_k \cap \text{Val}_k = \emptyset$, $\text{Grupos}(\text{Train}_k) \cap \text{Grupos}(\text{Val}_k) = \emptyset$, $\max(t_{\text{train}}) < \min(t_{\text{val}})$ e isolamento total do `holdout_ids`. |
| **M3 — Exploração e Cenários de Features sem Vazamento** | `features` | • Seleção de atributos contaminada por dados de validação/teste;<br/>• Instabilidade oculta de cenários dinâmicos. | • **TA-M3.1 (Rótulo Exploratório):** Garantir que `ExploratoryFeatureReport` carregue `scope = EXPLORATORY_FULL_DATA` e não possa ser convertido silenciosamente em seleção pré-partição.<br/>• **TA-M3.2 (Prova de Zero Leakage na Seleção Dinâmica):** Inserir observações sintéticas extremas exclusivamente no conjunto de validação de um *fold* e provar que o resultado de `DynamicFeatureScenario.fit_select(X_train, y_train)` é **idêntico** com ou sem a presença dessas observações na validação.<br/>• **TA-M3.3:** Registro exato das colunas selecionadas por *fold* e cálculo do índice de estabilidade de seleção entre *folds*. |
| **M4 — Adaptadores de Modelos, Pré-processamento em 2 Camadas e Nested Tuning** | `models`, `tuning` | • Contaminação de pesos/estado entre *folds*;<br/>• Transformação estatística ajustada fora do treino;<br/>• Duplicação acidental de escalonamento;<br/>• Vazamento da validação externa na escolha de hiperparâmetros. | • **TA-M4.1 (Isolamento de Instância):** Treinar um modelo com estado mutável em um *fold*, clonar via `clone_fresh` para o próximo *fold* e provar que nenhum peso/atributo ajustado anterior persiste.<br/>• **TA-M4.2 (Modelos Analíticos):** Executar equação biométrica/analítica com `requires_fit=False` sem invocar etapa de ajuste artificial.<br/>• **TA-M4.3 (Zero Leakage em 2 Camadas e Bloqueio de Duplicação):** Provar que média/desvio do `StandardScaler` na Camada 1/2 correspondem estritamente a `X_train`, e que configurar padronização idêntica nas duas camadas dispara erro/bloqueio de duplicação.<br/>• **TA-M4.4 (Nested Tuning Estrito):** Provar que `GridSearch` e `RandomSearch` subdividem apenas `X_train, y_train` do *fold* externo e nunca acessam `X_val, y_val` durante a escolha de $\theta^*$. |
| **M5 — Orquestrador Matricial, Tolerância a Falhas e Checkpoint/Resume** | `orchestration` | • Aborto completo de experimento longo por falha em uma célula;<br/>• Conversão silenciosa de falha em métrica zero;<br/>• Retomada inconsistente após alteração de dados/configuração. | • **TA-M5.1 (Sincronia de Partições):** Provar que todas as células $(m, c, f)$ executadas referenciam o mesmo `partition_plan_id` e avaliam exatamente os mesmos `observation_id` em cada *fold* $f$.<br/>• **TA-M5.2 (Isolamento de Falha):** Injetar um modelo que lança exceção no *fold* 2; verificar que em modo `FAULT_TOLERANT` a célula $(m, c, 2)$ fica com estado `FAILED` e metadados do erro, sem valor numérico zero nas métricas, enquanto as demais células concluem com `COMPLETED`.<br/>• **TA-M5.3 (Persistência e Resume Verificado):** Interromper uma matriz com 50% das células concluídas, retomar a partir do disco e provar que apenas os 50% restantes são executados, produzindo resultado final idêntico a uma execução ininterrupta; tentar retomar após alterar o dataset ou `PartitionPlan` e verificar bloqueio de incompatibilidade. |
| **M6 — Consolidação e Julgamento Estatístico Rigoroso** | `statistics` | • Subestimação de variância em validação cruzada;<br/>• Descarte silencioso de *folds* falhos;<br/>• Confusão entre $p \ge \alpha$ e equivalência;<br/>• Afirmações textuais não sustentadas pelos números. | • **TA-M6.1 (Exatidão Estatística):** Validar o teste $t$ corrigido de Nadeau-Bengio, o teste de Wilcoxon pareado e os ajustes de Holm-Bonferroni e Benjamini-Hochberg contra vetores analíticos de referência.<br/>• **TA-M6.2 (Cobertura Incompleta):** Avaliar comparação onde um modelo falhou em 1 *fold*; verificar que a comparação principal reporta incompletude e que qualquer análise em subconjunto comum aparece marcada como condicional.<br/>• **TA-M6.3 (Pareto e Conclusões Rastreáveis):** Validar a identificação da Fronteira de Pareto (erro vs. tempo) e verificar que toda afirmação em `StructuredConclusion` referencia campos numéricos existentes sem declarar equivalência a partir de $p \ge 0.05$. |
| **M7 — Relatórios Científicos, Proveniência e Reprodução de Referência** | `reporting`, integração ponta a ponta | • Recálculo oculto na camada de visualização;<br/>• Perda de linhagem entre tabela/gráfico e execução;<br/>• Caminhos absolutos quebrando portabilidade. | • **TA-M7.1 (Somente-Leitura e Regeneração Nível 1):** Gerar relatórios (Markdown/HTML), tabelas (CSV/MD/LaTeX `booktabs`) e figuras (PNG/SVG/PDF) a partir de um diretório persistido na Etapa 4/5 com os adaptadores de modelos desabilitados, provando que nenhum modelo é retreinado.<br/>• **TA-M7.2 (Linhagem e Portabilidade):** Verificar que cada arquivo gerado possui entrada válida em `artifact_provenance.json` e `checksums.sha256`, e que mover o diretório do experimento para outro caminho mantém todas as referências internas válidas.<br/>• **TA-M7.3 (Reprodução `prognose_florestal`):** Cumprimento integral do protocolo da Seção 8. |

---

### 7.1 Especificação Refinada do Marco M1 (Sub-entregas `M1.1`, `M1.2` e `M1.3`)

O Marco M1 é dividido em **três entregas sequenciais e independentemente verificáveis**. Nenhuma entrega seguinte inicia antes que todos os testes da entrega anterior estejam passando.

#### Entrega M1.1 — Configuração do Projeto, Verificação de Compatibilidade e *Smoke Tests*
* **Diagnóstico Real do Ambiente Hospedeiro:**
  * A inspeção direta do sistema confirmou dois interpretadores instalados: `/usr/bin/python3.14` (`Python 3.14.8`, com `pip 26.0.1` e `venv`) e `/usr/bin/python3.12` (`Python 3.12.15`, com `venv`).
  * Nenhum pacote científico (`numpy`, `scipy`, `pandas`, `scikit-learn`, `pytest`, `matplotlib`) está instalado no Python global do sistema operacional, e não há `.venv` pré-existente no diretório do projeto.
* **Regra de Compatibilidade:**
  * O `pyproject.toml` declarará `requires-python = ">=3.12"` (cobrindo os interpretadores 3.12 e 3.14 presentes na máquina), mas **uma versão de Python e de dependência só será registrada como efetivamente suportada após a instalação real no `.venv` local e aprovação da suíte de testes**.
* **Escopo da Entrega M1.1:**
  * Criação do `.venv`, arquivo `pyproject.toml`, estrutura de pacotes `src/experimental_ml/` e `tests/test_smoke.py` validando importação, metadados de versão e disponibilidade real de `numpy`, `scipy` e `pytest`.

#### Entrega M1.2 — Contratos, Implementação e Testes de `experimental_ml.core`
* **Escopo:**
  * Identificadores tipados imutáveis (`ExperimentId`, `PartitionPlanId`, `ScenarioId`, `ModelId`, `CellId`, `ComparisonId`, `ArtifactId`, `ObservationId`).
  * Enumerações fundamentais (`TaskType`, `ExecutionStatus`, `FindingSeverity`, `MetricDirection`, `AggregationScope`, `MetricStatus`, `ErrorPolicy`).
  * `SeedManager` hierárquico determinístico baseado em `numpy.random.SeedSequence`.
  * `config_hash` e `dataset_hash` seguindo estritamente o contrato de serialização canônica do **ADR-007**.
  * Hierarquia de exceções e alertas (`FrameworkError`, `ConfigurationError`, `DataIntegrityError`, `LeakageViolationError`, `TuningOptimizationError`, `MethodologicalWarning`).
* **Testes Obrigatórios (`tests/unit/test_core.py`):**
  * Invariância de `config_hash` à ordem de chaves de dicionários e à ordem de inserção em `set`/`frozenset`.
  * Equivalência de `config_hash` entre strings Unicode em forma decomposta (NFD) e composta (NFC).
  * Distinção estrita de `config_hash` entre `True` e `1`, `False` e `0`, `1` (`int`) e `1.0` (`float`), e `[1, 2]` (`list`) vs. `(1, 2)` (`tuple`).
  * Equivalência de `config_hash` e `dataset_hash` entre `-0.0` e `+0.0`, e entre diferentes *payloads* binários de `NaN`, mantendo distinção entre `NaN`, `+Inf`, `-Inf` e `None`.
  * Distinção de `dataset_hash` quando dois arrays possuem mesmos bytes brutos mas nomes de colunas, `dtypes` ou `observation_ids` distintos.

#### Entrega M1.3 — Contratos, Implementação e Testes de `experimental_ml.metrics`
* **Escopo:**
  * Objetos `MetricValue`, `AggregatedMetricValue`, `MetricSpec` e `MetricRegistry`.
  * Implementação das regras de propagação, agregação e comparação de `MetricStatus.UNDEFINED_NAN` (**ADR-005**).
  * Implementação vetorizada das 15 métricas do MVP (8 de regressão/alinhamento e 7 de classificação).
* **Critérios de Tolerância Numérica Específicos por Família (`tests/unit/test_metrics.py`):**

| Família de Métricas | Métricas Incluídas | Tolerância Relativa (`rtol`) | Tolerância Absoluta (`atol`) | Casos de Teste e Degenerescências Obrigatórias |
| :--- | :--- | :---: | :---: | :--- |
| **Erros em Escala Direta (Regressão)** | `MAE`, `RMSE`, `MBE` (Viés Médio) | `1e-12` | `1e-12` | Vetores analíticos conhecidos; erro nulo ($\hat{y} = y \Rightarrow 0.0$); propriedade de homocedasticidade de escala ($\text{RMSE}(c y, c \hat{y}) = \|c\| \text{RMSE}(y, \hat{y})$ com `atol=0.0`). |
| **Razões Adimensionais e Alinhamento** | `R2`, `RMSE_rel_pct`, `MAPE`, `Pearson`, `KTA` | `1e-10` | `1e-12` | Predição perfeita ($R^2=1, \text{Pearson}=1, \text{KTA}=1$); modelo constante igual à média ($R^2=0$); **casos degenerados:** variância zero em $y$ ou $\hat{y}$ (`R2`, `Pearson`), média nula $\bar{y}=0$ (`RMSE_rel_pct`), $y_i=0$ (`MAPE`), matriz de Gram nula $\|K\|_F=0$ (`KTA`) $\rightarrow$ todos devem retornar `MetricStatus.UNDEFINED_NAN` e `isnan(value)`. |
| **Proporções Discretas (Classificação)** | `Accuracy`, `Balanced_Accuracy`, `Precision`, `Recall`, `F1` (macro/weighted) | `1e-14` | `1e-15` | Matrizes de confusão analíticas conhecidas (binária e multiclasse); **casos degenerados:** classe sem predições positivas ($TP+FP=0$ em `Precision`) ou classe ausente no conjunto avaliado ($TP+FN=0$ em `Recall` / `Balanced_Accuracy`) $\rightarrow$ retorno explícito de `MetricStatus.UNDEFINED_NAN` com alerta metodológico, sem coerção silenciosa para `0.0`. |
| **Probabilísticas e Ordenação (Classificação)** | `ROC_AUC`, `Log_Loss` | `1e-9` | `1e-11` | Probabilidades bem calibradas, uniformes e invertidas; tratamento de probabilidades extremas $\{0, 1\}$ com *clipping* numérico documentado ($\epsilon = 10^{-15}$) no `Log_Loss`; **casos degenerados:** apenas uma classe presente em `y_true` para `ROC_AUC` ou probabilidades fora de $[0, 1]$ / não somando $1$ $\rightarrow$ `UNDEFINED_NAN` ou `DataIntegrityError` conforme o contrato. |

* **Testes de Propagação de `UNDEFINED_NAN`:**
  * Verificar que o comparador de candidatos (`is_better(cand_a, cand_b, direction)`) jamais seleciona um `MetricValue` com `UNDEFINED_NAN` sobre um `VALID`, independentemente de `direction` ser `MAXIMIZE` ou `MINIMIZE`.
  * Verificar que `aggregate_fold_metrics` produz `VALID` quando $K/K$ *folds* são válidos, `PARTIAL_COVERAGE` (com `MethodologicalWarning`) quando $0 < k < K$ são válidos, e `UNDEFINED_NAN` quando $0/K$ são válidos.
  * Verificar que o ordenador de ranking marca configurações `UNDEFINED_NAN` como `UNRANKABLE`, separadas das configurações válidas.

#### Comandos Reprodutíveis de Instalação, Execução de Testes e Qualidade (Critério de Conclusão do M1)
```bash
# 1. Criação do ambiente virtual e instalação em modo editável com dependências de teste
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"

# 2. Verificação empírica das versões instaladas no ambiente
.venv/bin/python -c "import sys, numpy, scipy, pytest; print(sys.version); print('numpy:', numpy.__version__, 'scipy:', scipy.__version__, 'pytest:', pytest.__version__)"

# 3. Gate da Entrega M1.1 (Smoke tests)
.venv/bin/pytest tests/test_smoke.py -v

# 4. Gate da Entrega M1.2 (Testes unitários do core)
.venv/bin/pytest tests/unit/test_core.py -v

# 5. Gate da Entrega M1.3 e Conclusão do Marco M1 (Suíte completa M1)
.venv/bin/pytest tests/ -v --tb=short
```
*(Nota: O avanço para o Marco M2 é bloqueado até que os gates 3, 4 e 5 executem com 100% de aprovação e zero falhas).*

---

## 8. Protocolo de Reprodução Agnóstica do Experimento de Referência (`prognose_florestal`)

Para comprovar o critério de aceitação **CA02**, o experimento original de prognose florestal será reproduzido **sem que nenhuma linha do núcleo do `experimental-ml-framework` contenha termos, colunas ou regras de engenharia florestal**. Toda a especificidade do domínio será fornecida externamente pelo script do pesquisador usando exclusivamente os contratos públicos das 6 etapas:

1. **Etapa 1 (Ingestão e Diagnóstico):**
   * O script de verificação carrega a base tabular do inventário via `DatasetLoader`, declarando genericamente `target_col`, `group_col` (identificador da parcela/unidade amostral para evitar vazamento espacial/ longitudinal) e `ignore_cols` (identificadores administrativos).
   * O `DatasetProfile` audita a base e o `PreparationPlan` registra explicitamente as regras de saneamento.
2. **Etapa 2 (Exploração e Cenários de Atributos):**
   * O `ExploratoryFeatureReport` calcula as correlações de Pearson, Spearman, Informação Mútua e matriz de colinearidade.
   * Os cenários experimentais do estudo original (atributos completos, subconjuntos biométricos de domínio e subconjuntos selecionados por ranking multi-critério / redução de colinearidade) são registrados no `ScenarioRegistry` como instâncias de `FixedFeatureScenario` e `DynamicFeatureScenario`.
3. **Etapa 3 (Modelos Clássicos, Equação Biométrica de Clutter e Resolvedor Quântico HHL):**
   * **Modelos Clássicos:** Regressores Scikit-Learn e XGBoost registrados via `SklearnModelAdapter` com seus respectivos espaços de busca (`HyperparameterSearchSpec`) ou configurações de referência.
   * **Modelo Biométrico (Clutter):** Registrado como modelo analítico/biométrico externo via `CallableAnalyticalAdapter` / `CustomModelAdapter` (corrigindo a falha histórica onde `clutter.py` duplicava código do XGBoost), exportando seus coeficientes ajustados via `ModelDiagnostics`.
   * **Modelo Quântico / Resolvedor HHL:** Registrado via adaptador externo que encapsula o circuito/resolvedor linear quântico, declarando na Camada 2 de pré-processamento a normalização/condicionamento matricial exigido e exportando em `ModelDiagnostics` a fidelidade de estado (referência de $1.000000000000$), número de condição ($\kappa$), profundidade do circuito e número de qubits.
4. **Etapa 4 (Particionamento Agrupado e Execução Matricial):**
   * O `PartitionPlan` é gerado com `GroupKFold` sobre a coluna de grupo declarada, provando matematicamente interseção nula de parcelas entre treino e validação ($\text{Grupos}(\text{Train}_k) \cap \text{Grupos}(\text{Val}_k) = \emptyset$).
   * O `MatrixOrchestrator` executa todas as combinações $(\text{Modelos} \times \text{Cenários} \times \text{Folds})$, salvando predições *out-of-fold*, resíduos e diagnósticos quânticos/biométricos.
5. **Etapa 5 (Métricas Sem Distorção e Julgamento Estatístico):**
   * O motor `metrics` calcula $R^2$, RMSE, RMSE (%), MAE, MAPE, Pearson, Viés Médio e KTA em ponto flutuante de dupla precisão (eliminando distorções como `math.ceil` identificadas na auditoria da Fase 1).
   * O módulo `statistics` executa as comparações formais entre os modelos clássicos, biométrico e quântico (Nadeau-Bengio, Wilcoxon, Holm-Bonferroni e Benjamini-Hochberg), avaliando também o compromisso entre erro preditivo e tempo de execução.
6. **Etapa 6 (Relatório e Artefatos de Publicação):**
   * O módulo `reporting` exporta automaticamente as tabelas LaTeX (`booktabs`), Markdown e CSV, os gráficos de dispersão 1:1, resíduos com bandas $\pm 2\sigma$, comparativos de métricas e diagnósticos HHL, além do pacote completo de reprodutibilidade com `checksums.sha256`.


