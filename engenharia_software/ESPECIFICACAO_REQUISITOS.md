# Especificação de Requisitos de Software (SRS) — `experimental-ml-framework`

> **Documento:** Especificação Completa de Requisitos de Software (Fases 1 a 6 do Ciclo Experimental)  
> **Versão:** 2.0.0  
> **Data:** 27 de Outubro de 2026  
> **Status:** Consolidado e Aprovado  
> **Documentos Relacionados:** [`ARQUITETURA_E_CONTRATOS.md`](./ARQUITETURA_E_CONTRATOS.md) | [`ETAPA_ATUAL_ENGENHARIA.md`](./ETAPA_ATUAL_ENGENHARIA.md)

---

## 1. Visão Geral, Propósito e Diretrizes Científicas

### 1.1 Objetivo do Sistema
O `experimental-ml-framework` é um **harness científico agnóstico e pedagógico** para condução, auditoria e publicação de experimentos em Aprendizado de Máquina (regressão e classificação). Seu propósito é democratizar a pesquisa rigorosa para estudantes de Iniciação Científica (IC), pós-graduandos e pesquisadores, fornecendo um fluxo estruturado de 6 etapas que previne erros metodológicos por construção, preserva a rastreabilidade integral dos dados às conclusões e gera artefatos prontos para publicação acadêmica.

### 1.2 Princípios Metodológicos Inegociáveis
1. **Orquestração Agnóstica (ADR-001):** O framework não implementa algoritmos preditivos internamente; ele integra modelos heterogêneos (clássicos, redes neurais, circuitos/resolvedores quânticos, equações analíticas e biométricas) por meio de adaptadores e contratos explícitos.
2. **Proibição de Mutações Silenciosas:** Nenhuma transformação de dados (imputação, codificação, remoção de linhas/colunas, escalonamento) ocorre automaticamente nos bastidores sem configuração explícita ou ciência documentada do pesquisador.
3. **Zero Vazamento de Dados (*Zero Data Leakage*):** Toda operação que aprende parâmetros a partir dos dados (pré-processamento, seleção dinâmica de atributos, busca de hiperparâmetros e treinamento) é ajustada estritamente nos dados de treino de cada partição externa.
4. **Honestidade Estatística e Epistemológica:** O framework não declara vencedores automáticos baseados apenas em médias simples, não trata ausência de significância estatística como prova de equivalência, não assume que correlação implica causalidade e jamais descarta ou mascara falhas de execução como valores zero.
5. **Independência entre Execução e Apresentação:** Gerar novos relatórios, recalcular testes estatísticos ou alterar formatos de tabelas e estilos de figuras não exige retreinar os modelos.

---

## 2. Requisitos Funcionais Detalhados por Etapa do Ciclo Experimental

---

### Etapa 1: Entrada, Triagem e Diagnóstico Estrutural da Base (`data` & `diagnostics`)

* **RF1.1 (Ingestão e Papéis das Variáveis):** Suportar carregamento de arquivos `.csv`, `.txt` (com delimitadores configuráveis ou detectáveis) e objetos `DataFrame`, permitindo declarar a variável-alvo (`target`), tipo de tarefa (`REGRESSION`, `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION`), e opcionalmente variável de agrupamento (`group`), identificador de observação (`observation_id`), variável temporal (`time_col`) e colunas ignoradas (`ignore_cols`).
* **RF1.2 (Diagnóstico Estrutural e de Memória):** Reportar número de observações, número de colunas, tamanho da base e estimativa de consumo de memória RAM, além de calcular hash de integridade (`SHA-256`) da base original.
* **RF1.3 (Tipagem e Qualidade dos Dados):** Identificar os tipos de dados por coluna (numérica, categórica, booleana, temporal), quantidade e proporção de valores ausentes por coluna, linhas duplicadas, colunas constantes (variância zero) e possíveis colunas identificadoras.
* **RF1.4 (Estatísticas Descritivas e Escalas):** Calcular para atributos numéricos média, mediana, desvio-padrão, mínimo, máximo e quartis, além de diagnosticar diferenças relevantes de escala e ordem de grandeza entre preditores. Para variáveis categóricas, calcular frequências absolutas e proporções relativas.
* **RF1.5 (Perfil do Alvo e de Grupos):** Apresentar a distribuição dos atributos e da variável-alvo (com frequências absolutas e relativas de classes e alerta de desbalanceamento em classificação). Quando houver variável de agrupamento, reportar quantidade de grupos, distribuição de observações por grupo e grupos com poucas amostras.
* **RF1.6 (Distinção entre Problemas Confirmados e Alertas Heurísticos):** Separar estruturalmente problemas confirmados de compatibilidade/integridade (`CONFIRMED_ISSUE`) de alertas heurísticos (`HEURISTIC_WARNING`), sem assumir que toda anomalia heurística exige correção.
* **RF1.7 (Imutabilidade e Plano Explícito de Preparação):** Garantir que a Etapa 1 seja estritamente exploratória e não altere a base original. Quando houver valores ausentes, variáveis categóricas ou incompatibilidades, informar o problema, explicar implicações e permitir que o pesquisador configure explicitamente o plano de tratamento (`PreparationPlan`), que será ajustado apenas dentro do treino de cada partição na Etapa 4.

---

### Etapa 2: Exploração de Relações e Cenários de Features (`features` & `scenarios`)

* **RF2.1 (Análise Exploratória de Relações):** Fornecer análises exploratórias de relações entre preditores e entre preditores e variável-alvo (correlações lineares e monotônicas, associações categóricas, redundância/multicolinearidade e indícios de relações não lineares como Informação Mútua), rotulando explicitamente qualquer análise feita na base completa como exploratória e orientando que correlação $\neq$ causalidade e que baixa correlação univariada não implica irrelevância multivariada.
* **RF2.2 (Criação Manual de Cenários Fixos):** Permitir que o pesquisador crie cenários fixos (`FixedFeatureScenario`) declarando identificador, nome, descrição/justificativa científica e a lista explícita de atributos que permanecerá constante em todas as partições.
* **RF2.3 (Criação Guiada e Cenários Dinâmicos):** Oferecer estratégias configuráveis e extensíveis para definição de cenários orientados a dados (`DynamicFeatureScenario`), como redução de multicolinearidade, seleção por relevância e seleção Top-$K$ compatíveis com a tarefa.
* **RF2.4 (Prevenção de Vazamento na Seleção de Atributos):** Executar qualquer seleção de atributos dependente dos valores observados exclusivamente dentro dos dados de treino de cada partição externa durante a Etapa 4, sem consultar validação ou teste.
* **RF2.5 (Rastreabilidade e Estabilidade de Seleção):** Registrar o método, os parâmetros e a lista exata de atributos selecionados em cada *fold*, permitindo inspecionar, comparar cenários fixos e dinâmicos e medir a estabilidade da seleção entre partições.

---

### Etapa 3: Registro de Modelos, Circuitos, Pré-processamento e Hiperparâmetros (`models` & `tuning`)

* **RF3.1 (Metadados e Identidade de Modelos):** Registrar para cada modelo um identificador único e estável, nome de exibição, família/categoria (clássico, rede neural, circuito/resolvedor quântico, baseline analítico, equação biométrica, customizado), descrição/justificativa científica, biblioteca/versão, configuração inicial, política de semente aleatória e capacidades declaradas (`ModelCapabilities`).
* **RF3.2 (Contrato de Adaptadores e Modelos Analíticos):** Integrar modelos externos por meio de adaptadores (`ModelAdapter`) que traduzam as particularidades de cada biblioteca para o contrato comum, permitindo que modelos analíticos sem etapa de treinamento (`requires_fit=False`) participem naturalmente sem simular um `fit` artificial.
* **RF3.3 (Isolamento de Instâncias):** Garantir que cada execução em cada *fold*, cenário ou tentativa de otimização utilize uma instância limpa e isolada do modelo (`clone_fresh`), prevenindo contaminação de pesos ou estado interno.
* **RF3.4 (Pré-processamento em Duas Camadas Auditadas):** Separar o **pré-processamento do cenário** do **pré-processamento específico do modelo** (ex.: escalonamento para intervalo específico, padronização, conversão para `ndarray` ou codificação para circuito quântico), ajustando ambos apenas no treino da partição, prevenindo duplicação acidental de transformações e validando a compatibilidade entre a saída do pré-processamento e a entrada esperada pelo modelo.
* **RF3.5 (Espaço de Busca e Otimização Aninhada de Hiperparâmetros):** Permitir declarar configuração fixa, Grid Search, Random Search (com espaço, orçamento e política de amostragem configuráveis) e extensão para novos métodos, exigindo definição explícita da métrica de otimização e de sua direção (`MAXIMIZE` / `MINIMIZE`), executando toda a busca estritamente dentro do conjunto de treinamento da partição externa (*Nested CV*) e registrando todas as tentativas avaliadas.
* **RF3.6 (Coleta Extensível de Metadados e Diagnósticos Internos):** Prever mecanismo opcional e estruturado para que modelos e adaptadores exportem diagnósticos específicos (ex.: qubits, profundidade, portas, *shots*, backend e diagnósticos HHL em modelos quânticos; épocas e histórico em redes neurais; equação e coeficientes em modelos analíticos/biométricos; importância de atributos em modelos clássicos), diferenciando claramente metadados de configuração, métricas calculadas pelo framework e diagnósticos produzidos pelo modelo.

---

### Etapa 4: Particionamento, Validação e Execução Matricial (`validation` & `orchestration`)

* **RF4.1 (Estratégias de Particionamento e Regimes de Avaliação):** Suportar K-Fold, Stratified K-Fold, Group K-Fold (e variantes agrupadas), estratégias temporais e Holdout, operando em três regimes configuráveis: (1) somente validação cruzada, (2) somente *holdout*, ou (3) validação cruzada na base de desenvolvimento seguida de avaliação final em *holdout* independente e intocado.
* **RF4.2 (Plano de Particionamento Imutável e Compartilhado):** Gerar, validar (ausência de sobreposição treino/validação, integridade de grupos, ordem temporal) e persistir um `PartitionPlan` independente antes da execução dos modelos, garantindo que todos os modelos e cenários comparados utilizem exatamente as mesmas partições externas.
* **RF4.3 (Orquestração com Máquina de Estados e Tratamento de Falhas):** Coordenar cada célula $(m, c, f)$ com identificador próprio e estado explícito (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`). Oferecer política configurável de erro (`FAULT_TOLERANT` vs `FAIL_FAST`), isolando falhas com registro de exceção/contexto sem converter falhas em métrica zero nem descartá-las silenciosamente.
* **RF4.4 (Controle de Paralelismo em Dois Níveis):** Permitir configurar o número de execuções simultâneas no orquestrador (`outer_n_jobs`) e controlar/limitar o paralelismo interno das bibliotecas de modelos (`inner_model_threads`) para evitar sobrecarga por paralelismo aninhado.
* **RF4.5 (Pausa, Persistência Incremental e Retomada Verificada):** Persistir incrementalmente o estado da matriz e os resultados de cada célula concluída, permitindo interromper e retomar experimentos longos após validar que dados, plano de particionamento, configurações e versões permanecem compatíveis.
* **RF4.6 (Registro Granular de Tempos, Predições e Resíduos por Observação):** Coletar por célula: configuração efetiva, atributos utilizados no *fold*, tempos desagregados (preparação, busca de hiperparâmetros, compilação de circuito, treino final, inferência e avaliação), métricas e predições individuais associadas a identificadores estáveis de observação (`observation_id`) — incluindo valores reais, predições, resíduos em regressão e probabilidades/escores em classificação — com armazenamento escalável sob demanda.
* **RF4.7 (Consolidação Out-of-Fold e Distinção de Escopo de Métricas):** Consolidar predições *out-of-fold* quando a estratégia de particionamento permitir consolidação unívoca, preservando a separação de janelas em esquemas temporais, e identificar explicitamente se cada métrica foi calculada por *fold* (`PER_FOLD`), agregada entre *folds* (`FOLD_AGGREGATION`), sobre predições consolidadas (`POOLED_OOF`) ou no *holdout* (`FINAL_HOLDOUT`).

---

### Etapa 5: Consolidação dos Resultados e Julgamento Estatístico (`metrics` & `statistics`)

* **RF5.1 (Flexibilidade de Escopo de Comparações):** Permitir comparar modelos dentro de um cenário, cenários para um mesmo modelo, combinações completas `(Modelo, Cenário)`, configurações contra um *baseline*, todas contra todas (par a par) e hipóteses planejadas, mantendo desempenho preditivo, estabilidade de seleção e custo computacional em dimensões separadas.
* **RF5.2 (Adequação Metodológica e Verificação de Pressupostos):** Apresentar e aplicar métodos estatísticos compatíveis com a estrutura real dos dados e das partições (reconhecendo a dependência entre *folds* na validação cruzada, como no teste $t$ corrigido de Nadeau-Bengio, o pareamento no Wilcoxon e a unicidade do *holdout*), explicando por que cada método é apropriado, verificando pressupostos testáveis e alertando sobre pressupostos não verificáveis e limitações amostrais.
* **RF5.3 (Tratamento Transparente de Comparações Incompletas):** Identificar configurações e partições com resultados ausentes ou falhos, distinguir falhas de execução de indefinições numéricas, preservar o pareamento original e somente apresentar análises sobre subconjuntos comuns de *folds* como alternativas condicionais explicitamente justificadas.
* **RF5.4 (Inferência Completa, Tamanho de Efeito, Relevância Prática e Multiplicidade):** Reportar diferença observada respeitando a direção de cada métrica, tamanho de efeito, intervalos de incerteza, $p$-valores originais e ajustados por família de hipóteses (ex.: Holm-Bonferroni, Benjamini-Hochberg), avaliação contra limiares de relevância prática ou margens de equivalência configuradas pelo pesquisador, e estabilidade entre partições.
* **RF5.5 (Análise Multiobjetivo e Fronteira de Pareto):** Avaliar simultaneamente qualidade preditiva, estabilidade e custo computacional, identificando compromissos e configurações na **Fronteira de Pareto**, gerando classificação geral apenas quando o pesquisador definir explicitamente a regra de decisão.
* **RF5.6 (Objeto Estatístico Tipado e Conclusões Explicativas Rastreáveis):** Produzir um objeto estruturado (`StatisticalJudgmentReport`) desacoplado da interface e gerar conclusões explicativas em linguagem natural estritamente rastreáveis aos resultados numéricos, diferenciando melhor resultado observado, significância estatística, magnitude/relevância prática e limitações metodológicas.

---

### Etapa 6: Relatórios Científicos, Visualizações e Pacote de Reprodutibilidade (`reporting` & `packaging`)

* **RF6.1 (Relatório Científico Completo e Artefatos Modulares):** Gerar relatórios consolidados (inicialmente em Markdown e HTML, extensível a LaTeX/PDF) e exportar modularmente tabelas (`.csv`, `.md`, `.tex` em padrão `booktabs`), figuras (`.png` a 300 DPI, `.svg`, `.pdf`) e dados estruturados (`.json`, `.parquet`) sem necessidade de retreinar modelos.
* **RF6.2 (Cobertura das 7 Famílias de Tabelas e Visualizações):** Produzir artefatos para: (A) Caracterização e qualidade dos dados, (B) Cenários de atributos e estabilidade de seleção, (C) Modelos, configurações e otimização, (D) Desempenho preditivo (regressão e classificação, CV e *holdout*), (E) Comparações estatísticas, tamanhos de efeito e relevância prática, (F) Estabilidade e custo computacional (incluindo Fronteira de Pareto), e (G) Artefatos específicos exportados por adaptadores de famílias de modelos (quânticos, biométricos, redes neurais, clássicos).
* **RF6.3 (Rastreabilidade e Linhagem de Artefatos):** Registrar para cada tabela e figura seu manifesto de proveniência (`ArtifactProvenance`), vinculando-a ao experimento, plano de particionamento, modelos, cenários, partições, métricas, testes estatísticos e arquivos de origem, permitindo regenerar apresentações sem reexecutar experimentos.
* **RF6.4 (Pacote de Reprodutibilidade, Auditoria e Portabilidade):** Organizar o diretório do experimento (`manifest`, `data`, `configuration`, `partitions`, `runs`, `predictions`, `statistics`, `tables`, `figures`, `reports`, `artifacts`, `reproducibility`) com hashes de integridade, registro de ambiente/versões/sementes, distinção explícita dos níveis de reprodução, referências exclusivamente relativas e opção de exportar pacote reduzido/compartilhável sem dados sensíveis ou sob restrição de licença.

---

## 3. Requisitos Não Funcionais (RNF)

* **RNF01 (Determinismo e Controle de Sementes):** Propagação explícita e auditável de sementes pseudoaleatórias em todas as operações estocásticas, documentando limitações quando backends externos ou hardware não garantirem determinismo bit a bit.
* **RNF02 (Independência de Domínio):** Nenhuma coluna, métrica ou regra de negócio específica de um domínio aplicado (ex.: inventário florestal) deve estar codificada de forma fixa no núcleo do framework.
* **RNF03 (Autossuficiência 100% Offline):** Execução integralmente local, sem dependência obrigatória de serviços em nuvem, servidores externos ou conexão à internet.
* **RNF04 (Eficiência Computacional e Armazenamento Escalável):** Vetorização numérica via NumPy/SciPy e carregamento sob demanda (*lazy loading*) de predições e artefatos volumosos para não esgotar a memória RAM em matrizes grandes.
* **RNF05 (Testabilidade e Rigor Matemático):** Cobertura de testes automatizados (`pytest`) validando invariantes de vazamento zero, cálculos de métricas, testes de hipóteses estatísticas, isolamento de falhas e retomada de execução.
* **RNF06 (Compatibilidade Verificada Empiricamente):** Suporte ao ecossistema Python moderno (interpretadores $\ge 3.12$ presentes no ambiente de desenvolvimento, incluindo `Python 3.12` e `Python 3.14`), sendo que nenhuma versão de Python ou biblioteca de terceiros é declarada como suportada sem verificação empírica via suíte de testes no ambiente virtual (`.venv`).
* **RNF07 (Ergonomia Pedagógica):** API fluente para scripts Python e Jupyter Notebooks, acompanhada de diagnósticos e alertas redigidos de forma clara e instrutiva.

---

## 4. Critérios de Aceitação do MVP (Ground Truth)

* **CA01 (Execução Ponta a Ponta das 6 Etapas):** Executar o fluxo completo desde a triagem de `.csv`/`.txt` (Etapa 1), exploração e cenários fixos/dinâmicos (Etapa 2), registro de modelos clássicos, analíticos e quânticos com tuning aninhado (Etapa 3), execução matricial com `PartitionPlan` compartilhado e retomada (Etapa 4), julgamento estatístico com Nadeau-Bengio/Wilcoxon e análise de Pareto (Etapa 5), até a geração do pacote completo de relatórios e artefatos rastreáveis (Etapa 6).
* **CA02 (Reprodução Científica de Referência):** Reproduzir com fidelidade metodológica e paridade numérica os experimentos de referência originados no projeto `prognose_florestal`, utilizando exclusivamente as interfaces agnósticas do `experimental-ml-framework`.
