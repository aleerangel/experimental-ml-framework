# Referências Bibliográficas e Fundamentação Teórico-Técnica — `experimental-ml-framework`

> **Documento:** Catálogo de Fundamentação Teórica, Metodológica, Estatística e Normativa  
> **Versão:** 1.2.0  
> **Data:** 31 de Outubro de 2026  
> **Natureza:** Documento Técnico de Arquitetura e Fundamentação  
> **Documentos Relacionados:** [`ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md) | [`ESPECIFICACAO_REQUISITOS.md`](./engenharia_software/ESPECIFICACAO_REQUISITOS.md) | [`ETAPA_ATUAL_ENGENHARIA.md`](./engenharia_software/ETAPA_ATUAL_ENGENHARIA.md) | [`README.md`](./README.md)

---

## 1. Introdução e Objetivo da Fundamentação

O `experimental-ml-framework` é especificado como uma biblioteca modular e ferramenta de linha de comando (`expml`) em Python, voltada à execução de experimentos de Aprendizado de Máquina (*Machine Learning* — ML) para tarefas de regressão e classificação, com suporte a comparação estatística, verificação de integridade e geração reprodutível de relatórios científicos.

O propósito deste documento é consolidar a **fundamentação teórica, metodológica, estatística e normativa** das decisões arquiteturais e metodológicas do projeto. O objetivo é assegurar a **defensabilidade acadêmica e técnica** das escolhas de arquitetura, explicitando a lógica de estruturação dos contratos, as evidências científicas e normas técnicas que os sustentam, bem como os limites operacionais de cada abordagem.

Para garantir rigor técnico e clareza conceitual, este catálogo adota três diretrizes editoriais:

1. **Diferenciação epistemológica:** Distingue-se rigorosamente dedução matemática ou analítica, consenso e evidência empírica da literatura, padrões normativos técnicos e heurísticas de engenharia de software.
2. **Declaração explícita de limitações:** Para cada referência citada, detalha-se o escopo suportado pela fonte e as adaptações requeridas pelo framework.
3. **Vinculação direta aos contratos:** Todas as justificativas são mapeadas para os critérios de aceitação, decisões de arquitetura (ADRs) e especificações funcionais descritas em [`ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md) e [`ESPECIFICACAO_REQUISITOS.md`](./engenharia_software/ESPECIFICACAO_REQUISITOS.md).

---

## 2. Escopo do Framework e Estado do Planejamento

* **Onda 1 (MVP Imediato — Contratos e Requisitos Especificados):**
  * **Etapa 1 (Ingestão e Diagnóstico):** Ingestão imutável de dados tabulares (`.csv`, `.txt` com/sem cabeçalho, `DataFrame`) e perfilamento diagnóstico automático (`DatasetProfile`), com separação entre anomalias confirmadas (`CONFIRMED_ISSUE`) e alertas heurísticos (`HEURISTIC_WARNING`).
  * **Etapa 2 (Cenários de Features):** Modo exploratório rotulado (`EXPLORATORY_FULL_DATA`), cenários de atributos fixos (`mode="FIXED"`) e cenários dinâmicos (`mode="DYNAMIC"` com filtro de colinearidade, Top-$K$ e ranking multi-critério recalibrados estritamente dentro de cada partição de treino).
  * **Etapa 3 (Configuração e Registro de Modelos):** Registro agnóstico de modelos externos (Scikit-Learn, XGBoost, modelos analíticos com `requires_fit=False`, funções customizadas e circuitos quânticos via `ModelDiagnostics`), pré-processamento desacoplado em duas camadas (Cenário e Modelo) com bloqueio de duplicação, e busca aninhada de hiperparâmetros (*Nested CV* via Grid e Random Search).
  * **Etapa 4 (Particionamento e Execução Matricial):** Geração e validação matemática de `PartitionPlan` compartilhado (*K-Fold*, *Stratified K-Fold*, *Group K-Fold* e *Holdout*), orquestração da matriz $M \times C \times F$ com tolerância a falhas, escrita em dois passos (`.tmp` + `os.replace`), rastreabilidade por `observation_id` e retomada verificada (*Checkpoint & Resume*).
  * **Etapa 5 (Consolidação e Comparação Estatística):** Consolidação descritiva, teste $t$ corrigido de Nadeau-Bengio, teste pareado de Wilcoxon, correções de multiplicidade de Holm-Bonferroni e Benjamini-Hochberg, análise multiobjetivo por Fronteira de Pareto e síntese textual padronizada via `StructuredConclusion`.
  * **Etapa 6 (Relatórios Científicos Desacoplados):** Exportação modular em Markdown e HTML com 7 famílias de tabelas e figuras científicas, rastreabilidade por artefato (`ArtifactProvenance`) e resumos criptográficos (`SHA-256`) preservados internamente para auditoria.
* **Onda 2 (Extensões do MVP — Requisitos Estruturados para Detalhamento):**
  * Regressão multialvo (`MULTI_TARGET_REGRESSION`, `target_col: Sequence[str]`).
  * Transformações reversíveis da variável-alvo (`TargetTransformSpec`).
  * Conjunto de candidatos não rotulados (`unlabeled_pool`) e funções de aquisição sequencial (`EI`, `UCB`/`LCB`, `Exploitation`, `Exploration`).
  * Reamostragem por *Bootstrap* ($B$ repetições com validação *Out-of-Bag* e incerteza de comitê) e estratégias cronológicas (*Temporal Split*).
  * Redução de dimensionalidade intra-fold (`PCA` em `select_features_in_fold`).
* **Evoluções Pós-MVP (Planejamento Futuro — Seção 6.2 de `ARQUITETURA_E_CONTRATOS.md`):**
  * Seletores *wrapper* (RFE), métodos embutidos ($L_1$/Lasso) e importância por permutação.
  * Otimização Bayesiana de hiperparâmetros (Optuna) e execução distribuída em clusters.
  * Testes estatísticos globais (Friedman + pós-testes de Nemenyi/Dunn) e testes formais de equivalência (TOST).

---

## 3. Arquitetura Modular e Separação de Responsabilidades

### 3.1. Decomposição Modular e Ocultamento de Decisões de Projeto

* **Decisões de Projeto:**
  * A especificação divide o sistema em **três camadas funcionais unidirecionais** (Camada 1: Definição e Triagem; Camada 2: Validação e Execução Matricial; Camada 3: Comparação Estatística e Publicação), suportadas por dois pacotes fundacionais transversais (`core` e `metrics`) ([Seção 2.1 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L57-L107)).
  * A estrutura organiza fisicamente os módulos em níveis de dependência (Nível 0 a Nível 7), prevenindo acoplamentos cíclicos ([Seção 2.3 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L138-L154)).
  * O projeto adota **funções puras e estruturas de dados imutáveis** (dataclasses com `frozen=True`) como diretriz de design, em vez de hierarquias de classes com estado interno mutável (**ADR-008**, [Seção 1 e Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L212-L218)).
* **Justificativa e Fundamentação Teórica:**
  * **Parnas (1972) — *On the Criteria to Be Used in Decomposing Systems into Modules*:** A decomposição modular fundamenta-se no princípio clássico do ocultamento de informação (*information hiding*). Parnas demonstra que a modularização eficaz isola decisões de projeto sujeitas a alteração (estruturas de dados, formatos de persistência, algoritmos específicos) atrás de interfaces bem delimitadas, em oposição a divisões baseadas apenas em fluxo procedural. No framework:
    * O módulo `metrics` opera sem dependência de estimadores ou modelos de aprendizado, concentrando-se no cálculo determinístico a partir dos vetores `y_true`, `y_pred` e `y_score`.
    * O módulo `validation` opera de forma desacoplada de pré-processamento e treinamento, restringindo-se à geração e validação de índices de partição.
    * O módulo `orchestration` gerencia o ciclo de vida e a tolerância a falhas sem manipular matrizes de atributos diretamente.
  * **Transparência Referencial e Prevenção de Efeitos Colaterais:** Em pipelines de Machine Learning, instâncias com estado mutável compartilhadas entre iterações podem introduzir vazamento de pesos e persistência acidental de dados entre dobras de validação cruzada. Ao restringir o fluxo a funções com entradas explícitas e retornos estruturados imutáveis (`fitted_params`, `SelectionResult`, `CellResultRecord`), reduz-se o risco de contaminação de estado entre execuções.
* **Evidência Específica na Fonte:**
  * Parnas (1972, p. 1056–1058) analisa projetos alternativos de um mesmo sistema e demonstra que a modularização orientada a ocultamento de decisões proporciona facilidade de modificação, desenvolvimento independente e testabilidade superior quando comparada a designs com compartilhamento amplo de estruturas internas.
* **Limitações e Fronteiras Técnicas:**
  * Os princípios de Parnas (1972) foram formulados para engenharia de software em geral, sem contemplar particularidades de fluxos estocásticos de Machine Learning.
  * Bibliotecas externas do ecossistema Python (como `scikit-learn` e `xgboost`) adotam orientação a objetos e estimadores com estado mutável (atributos alterados durante `fit()`). Essa condição é tratada nas fronteiras funcionais (`instantiate_fresh_model`, `fit_model`, `predict_model`), que instanciam estimadores limpos a cada dobra e extraem os resultados em estruturas imutáveis, encapsulando a mutabilidade externa.

### 3.2. Separação entre Interface de Linha de Comando (CLI) e Lógica de Domínio

* **Decisões de Projeto:**
  * A interface de linha de comando é isolada no pacote `src/experimental_ml/cli/`, utilizando a biblioteca padrão `argparse` e organizada em subcomandos (`data`, `features`, `models`, `partition`, `run`, `stats`, `report`) ([Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L156-L179)).
  * A especificação veda lógica de negócio nos adaptadores de comando (`cmd_*.py`): cada módulo converte argumentos de entrada, invoca as funções públicas da API e retorna códigos de saída padronizados (`0` para sucesso, `1` para falha de execução, `2` para violação de contrato ou validação impeditiva) ([RNF07 de `ESPECIFICACAO_REQUISITOS.md`](./engenharia_software/ESPECIFICACAO_REQUISITOS.md#L102)).
* **Justificativa e Fundamentação Técnica:**
  * **Separação de Mecanismo e Política e Padrão *Ports and Adapters*:** O terminal atua como um adaptador periférico de entrega. Toda a lógica de validação, execução e análise reside no núcleo funcional. Isso assegura que execuções via CLI, scripts Python ou pipelines de integração contínua apliquem exatamente os mesmos contratos e verificações metodológicas.
* **Limitações:**
  * A convenção dos códigos de retorno `0`, `1` e `2` decorre das práticas normativas de sistemas POSIX/Unix, constituindo uma escolha técnica de usabilidade em terminal Linux.

---

## 4. Metodologia Experimental e Prevenção Estrutural de Data Leakage

### 4.1. Taxonomia de Vazamento de Dados e Desenho Metodológico Preventivo

* **Decisões de Projeto:**
  * Princípio estruturante 3: Qualquer operação que envolva parametrização ou ajuste com base nas observações (imputação de valores ausentes, escalonamento, codificação categórica, seleção dinâmica de atributos e busca de hiperparâmetros) deve ser calibrada exclusivamente no conjunto de treino da partição externa corrente ([Princípio 3 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L40)).
  * A arquitetura estabelece distinção formal entre saneamento estrutural determinístico pré-partição (remoção de observações com alvo nulo e exclusão de colunas proibidas/constantes) e transformações estatísticas intra-fold (**ADR-002**, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L182-L184)).
  * O contrato define rotulagem mandatória para análises exploratórias (`scope = "EXPLORATORY_FULL_DATA"`), com bloqueio arquitetural que impede a utilização direta do resultado exploratório como conjunto de atributos de treino sem partição (`CA-E2-01`, [Seção 3.2 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L275-L279)).
* **Justificativa e Fundamentação Científica:**
  * **Kapoor & Narayanan (2023) — *Leakage and the Reproducibility Crisis in Machine-Learning-Based Science*:** Revisão sistemática sobre 329 artigos científicos em 17 campos quantitativos, identificando que o vazamento de dados (*data leakage*) constitui uma das causas centrais de falhas de reprodutibilidade em aplicações científicas de Machine Learning. Os autores sistematizam 8 modalidades de vazamento, apontando que o pré-processamento na base completa antes da partição e a seleção prévia de variáveis introduzem estimativas infladas de desempenho.
  * **Heil et al. (2021) — *Reproducibility Standards for Machine Learning in the Life Sciences*:** Diretrizes de reprodutibilidade em ciências da vida que exigem isolamento estrito dos dados de teste em relação a qualquer procedimento de ajuste de hiperparâmetros ou pré-processamento.
  * **scikit-learn Documentation — *Common Pitfalls and Recommended Practices*:** Documentação técnica demonstrando empiricamente que calcular parâmetros de escala ou ranqueamentos univariados na base completa antes da divisão de validação transfere informação da distribuição de teste para o modelo, distorcendo a avaliação de generalização.
* **Evidência Específica na Fonte:**
  * Kapoor & Narayanan (2023, p. 100804) relatam casos práticos em que modelos publicados com elevado desempenho preditivo tiveram seus ganhos descaracterizados quando reproduzidos com isolamento correto do pré-processamento e da seleção de atributos.
* **Limitações da Literatura e Soluções de Engenharia:**
  * A literatura científica identifica o problema e prescreve o isolamento metodológico, sem definir a arquitetura de software para aplicá-lo. O contrato em duas camadas definido no **ADR-002** e as verificações de `CA-E1-02` e `CA-E2-01` constituem mecanismos de software concebidos para prevenir essas violações estruturalmente.

---

## 5. Validação Cruzada, Particionamento e Otimização de Hiperparâmetros

### 5.1. Viés de Seleção e Validação Cruzada Aninhada (*Nested CV*)

* **Decisões de Projeto:**
  * A especificação restringe a busca de hiperparâmetros (Grid Search e Random Search) ao conjunto de treino da partição externa por meio de validação cruzada aninhada (*Nested Cross-Validation*), com exigência explícita de métrica e direção de otimização (**ADR-003**, [RF3.5 de `ESPECIFICACAO_REQUISITOS.md`](./engenharia_software/ESPECIFICACAO_REQUISITOS.md#L57); `CA-E3-02`, [Seção 3.3 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L340-L347)).
  * A ordem de execução intra-célula estabelece que, ao combinar seleção dinâmica de atributos e otimização de hiperparâmetros, o pré-processamento e o ranqueamento sejam recalibrados em cada dobra interna para a seleção de $\theta^*$, e reajustados no treino externo completo antes da avaliação de validação (**ADR-003**, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L185-L186)).
* **Justificativa e Fundamentação Teórica:**
  * **Cawley & Talbot (2010) — *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*:** Demonstram teórica e experimentalmente que a calibração de hiperparâmetros no mesmo laço de validação usado para reportar o desempenho final gera um viés de seleção otimista (*selection bias*). Os autores concluem que a validação cruzada aninhada (*Nested Cross-Validation*) é necessária para obter estimativas não viesadas do erro de generalização.
  * **Bergstra & Bengio (2012) — *Random Search for Hyper-Parameter Optimization*:** Demonstram que a busca aleatória apresenta eficiência superior à busca em grade em espaços com baixa dimensionalidade efetiva, sustentando a inclusão de ambas as estratégias na especificação do MVP.
* **Evidência Específica na Fonte:**
  * Cawley & Talbot (2010, p. 2079–2107) evidenciam que a magnitude do viés otimista provocado por validação não aninhada pode se equiparar ou superar as diferenças reais de desempenho entre classes distintas de algoritmos.
* **Limitações e Extensões do Projeto:**
  * Cawley & Talbot (2010) investigaram primordialmente o ajuste de parâmetros de regularização em máquinas de vetores de suporte (SVM). A aplicação desse princípio no ADR-003 estende a exigência de isolamento ao fluxo completo de seleção dinâmica de atributos no laço interno.

### 5.2. Particionamento Estruturado e Dependência Amostral

* **Decisões de Projeto:**
  * O particionamento agrupado (`GroupKFold`) é especificado como requisito para dados com dependência estrutural, incluindo verificação formal de disjunção de grupos entre treino e validação ($\text{Grupos}(\text{Train}_k) \cap \text{Grupos}(\text{Val}_k) = \emptyset$) e em relação ao *Holdout Final* (`CA-E4A-01` e `CA-COND-PART-01`, [Seção 3.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L369-L373)).
* **Justificativa e Fundamentação Científica:**
  * **Roberts et al. (2017) — *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*:** Estudo seminal que examina as limitações da validação cruzada aleatória tradicional (*random k-fold*) na presença de dependência estrutural entre observações (espacial, temporal ou hierárquica). Os autores demonstram que a distribuição aleatória de dados correlacionados entre treino e teste viola a suposição de independência (IID), resultando em subestimação do erro de generalização e incapacidade preditiva em novos grupos. A recomendação formal é o emprego de estratégias de bloqueio (*Grouped Cross-Validation*).
* **Evidência Específica na Fonte:**
  * Roberts et al. (2017, p. 913–929, DOI: 10.1111/ecog.02881) comprovam empiricamente que esquemas aleatórios superestimam o desempenho em dados com correlação intrínseca, enquanto esquemas agrupados refletem de forma mais precisa o desempenho em novas unidades amostrais.
* **Limitações e Adaptações de Engenharia:**
  * O artigo tem como foco principal modelagem ecológica e espacial. A extensão conceitual para dados com estruturas hierárquicas em outras áreas (como medições repetidas por unidade territorial ou identificador) segue a mesma fundamentação teórica. As condições de contorno algébricas, como a exigência de que o número de grupos únicos seja igual ou superior ao número de dobras ($G \ge K$), representam condições de viabilidade operacional estabelecidas no contrato `CA-COND-PART-01`.

---

## 6. Comparação Estatística de Modelos e Controle de Multiplicidade

### 6.1. Não-Independência de Dobras e Correção de Variância de Nadeau-Bengio

* **Decisões de Projeto:**
  * A especificação veda o tratamento de dobras de validação cruzada como amostras independentes sob testes $t$ clássicos ([Seção 3.5 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L468)).
  * O teste $t$ corrigido de Nadeau-Bengio é adotado como método padrão para comparações pareadas de métricas sob validação cruzada (**ADR-004**, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L188); `CA-E5-02`).
  * Para o caso de variância amostral nula ($s^2_d = 0$), o contrato define retorno de diferença zero e $p = 1{,}0$ com código de integridade dedicado, sem divisão por zero (**ADR-004**).
* **Justificativa e Fundamentação Teórica:**
  * **Nadeau & Bengio (2003) — *Inference for the Generalization Error*:** Trabalho que formaliza a razão pela qual testes inferenciais convencionais falham na avaliação comparativa de algoritmos de aprendizado. Em validação cruzada com $K$ dobras, os modelos ajustados compartilham $(K-2)/(K-1)$ dos dados de treinamento, introduzindo correlação positiva entre as diferenças de erro em cada partição. O teste $t$ pareado ingênuo desconsidera essa covariância, subestimando a variância real da diferença média e inflando a taxa de erro Tipo I (falsos positivos).
  * Nadeau e Bengio propõem a seguinte correção analítica para a variância da diferença média sob reamostragem:
    $$\sigma^2_{\text{corrigida}} = \left( \frac{1}{J} + \frac{n_{\text{val}}}{n_{\text{train}}} \right) s^2_d$$
    onde $J$ é o número de repetições/dobras, $n_{\text{val}}$ o tamanho da validação, $n_{\text{train}}$ o tamanho do treino e $s^2_d$ a variância amostral das diferenças observadas.
  * **Dietterich (1998) — *Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms*:** Demonstra previamente que o teste $t$ pareado convencional em $K$-fold atinge taxas elevadas de falso positivo e discute procedimentos aproximados.
* **Evidência Específica na Fonte:**
  * Nadeau & Bengio (2003, p. 239–281, DOI: 10.1023/A:1024068626366) mostram em simulações de Monte Carlo que a correção analítica reduz a taxa empírica de erro Tipo I para patamares substancialmente mais próximos do nível nominal $\alpha$, em contraste com taxas de rejeição indevida observadas no teste ingênuo.
* **Limitações Teóricas e Heurísticas de Engenharia:**
  * **Natureza aproximada:** O teste de Nadeau-Bengio constitui uma **aproximação analítica** baseada em premissas de simetria e normalidade aproximada das diferenças. O método mitiga substancialmente a distorção do erro Tipo I, mas não fornece garantia formal exata sob distribuições fortemente assimétricas ou amostras pequenas.
  * **Dobras de tamanhos desiguais:** A dedução original assume partições com tamanhos idênticos ($n_{\text{val}} / n_{\text{train}} = 1/(K-1)$). Sob estratégias como `GroupKFold`, o tamanho de cada partição pode oscilar. Para permitir a aplicação da correção nessas condições, a especificação adota a razão média efetiva $\overline{(n_{\text{val}} / n_{\text{train}})}$ e emite um alerta heurístico quando o coeficiente de variação dos tamanhos de dobra excede 20% (**ADR-004**). Esse limiar de 20% constitui uma heurística interna de engenharia adotada no projeto para alertar sobre desbalanceamentos acentuados, e não um resultado formal do artigo original de Nadeau & Bengio.

### 6.2. Cuidados Metodológicos no Teste de Wilcoxon e Limites Amostrais

* **Decisões de Projeto:**
  * O teste pareado de postos sinalizados de Wilcoxon é previsto como alternativa não-paramétrica para comparação de métricas, com descarte de diferenças nulas ($d_j = 0$) e alerta mandatório de baixo poder amostral para $J < 6$ (**ADR-004**, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L189); `CA-E5-01`).
* **Justificativa e Análise da Literatura:**
  * **Demšar (2006) — *Statistical Comparisons of Classifiers over Multiple Data Sets*:** Referência clássica na literatura de ML que recomenda testes baseados em postos (como Wilcoxon e Friedman) para comparação de classificadores.
  * **Distinção Metodológica Importante:** A recomendação formal de Demšar (2006) direciona-se à comparação de algoritmos avaliados em **múltiplos conjuntos de dados independentes** ($N \ge 10$ a $30$). Quando aplicado sobre dobras de validação cruzada em um *único conjunto de dados*, a premissa de observações independentes também é violada pela sobreposição do treino. A formulação não-paramétrica relaxa a exigência de normalidade das diferenças, mas **não elimina a dependência estatística gerada pela validação cruzada**.
  * **Justificativa da inclusão no framework:** O teste de Wilcoxon foi mantido como recurso complementar para cenários em que a distribuição das diferenças apresenta assimetria acentuada ou caudas pesadas. No entanto, sua utilização é vinculada a notas metodológicas em `evaluate_method_suitability`, esclarecendo a violação da premissa de independência.
  * **Dedução do Limite Amostral $J < 6$:** Para o teste de Wilcoxon pareado bicaudal com $J$ pares de diferenças não nulas, a probabilidade mínima associada à configuração mais extrema dos postos é dada por:
    $$p_{\text{mínimo}} = 2 \times \left( \frac{1}{2} \right)^J = \frac{1}{2^{J-1}}$$
    Para $J = 5$, o menor $p$-valor possível é $1/16 = 0{,}0625$. Portanto, adotando o nível de significância usual $\alpha = 0{,}05$, existe uma **impossibilidade combinatória de rejeitar a hipótese nula** com $J \le 5$ dobras, independentemente da magnitude da diferença observada. Essa limitação combinatória fundamenta a exigência de alerta preventivo definida no ADR-004.

### 6.3. Controle da Taxa de Falso Positivo em Comparações Múltiplas: FWER vs. FDR

* **Decisões de Projeto:**
  * A especificação disponibiliza os procedimentos de correção de multiplicidade de **Holm-Bonferroni** e **Benjamini-Hochberg** na Etapa 5B (`CA-E5-02`, [Seção 3.5 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L482)).
  * O contrato `ComparisonSpec` requer a declaração explícita da família de hipóteses e do tipo de controle aplicado (FWER ou FDR).
* **Justificativa e Fundamentação Teórica:**
  * **Holm (1979) — *A Simple Sequentially Rejective Multiple Test Procedure*:** Propõe o método sequencialmente rejeitador que controla a *Family-Wise Error Rate* (FWER). O procedimento ordena os $p$-valores observados $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$ e compara cada termo contra o limiar $\alpha / (m - i + 1)$. O método de Holm domina uniformemente a correção clássica de Bonferroni ($p_i \le \alpha / m$), garantindo maior poder estatístico enquanto mantém o controle estrito da probabilidade de cometer ao menos um erro Tipo I na família de testes.
  * **Benjamini & Hochberg (1995) — *Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing*:** Formalizam o critério de *False Discovery Rate* (FDR), definido como a proporção esperada de falsas descobertas entre as hipóteses rejeitadas. Em matrizes experimentais com elevado número de combinações (Modelo $\times$ Cenário), o controle rigoroso de FWER pode reduzir excessivamente o poder estatístico. O procedimento de Benjamini-Hochberg (BH) ajusta os $p$-valores ordenados por $p_{(i)} \times m / i$ (mantendo monotonicidade), equilibrando a identificação de efeitos relevantes com o controle proporcional de falsos positivos.
* **Evidência Específica na Fonte:**
  * Benjamini & Hochberg (1995, p. 289–300) demonstram analiticamente que o método assegura $\text{E}[\text{FDR}] \le \frac{m_0}{m} q^* \le q^*$, oferecendo suporte estatístico para comparações em cenários exploratórios com múltiplas hipóteses.
* **Limitações:**
  * O procedimento de Benjamini-Hochberg pressupõe independência ou dependência do tipo PRDS (*Positive Regression Dependency on Subsets*) entre as estatísticas de teste. Em comparações entre múltiplos modelos avaliados nas mesmas partições, dependências empíricas complexas podem se manifestar, limitação documentada nas especificações da Etapa 5.

### 6.4. Não-Significância Estatística e a Questão da Equivalência

* **Decisões de Projeto:**
  * A especificação define que valores de $p \ge \alpha$ não autorizam a inferência de equivalência ou igualdade de desempenho. Nessas condições, o componente `StructuredConclusion` emite a classificação `INCONCLUSIVE_NO_SIGNIFICANT_DIFFERENCE` ([Princípio 4 de `ESPECIFICACAO_REQUISITOS.md`](./engenharia_software/ESPECIFICACAO_REQUISITOS.md#L20); `CA-E5-03`, [Seção 3.5 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L486-L489)).
* **Justificativa Epistemológica e Estatística:**
  * **Distinção conceitual:** A metodologia do framework estabelece separação entre três conceitos:
    1. *Sumarização descritiva:* Apresentação das métricas observadas (médias, medianas e dispersão entre as dobras).
    2. *Teste de significância de hipótese nula (NHST):* Avaliação da hipótese de que a diferença entre os modelos é diferente de zero ($H_0: \mu_d = 0$).
    3. *Teste de equivalência:* Verificação formal de que a diferença reside dentro de uma margem predefinida de indiferença prática ($[-\Delta, +\Delta]$).
  * Conforme enfatizado por Altman & Bland (1995), a ausência de evidência não constitui evidência de ausência. A não rejeição de $H_0$ ($p \ge \alpha$) pode refletir apenas poder amostral insuficiente (como em esquemas com $J \le 5$ dobras) ou dispersão elevada, e não a paridade real entre os algoritmos.
  * O estabelecimento formal de equivalência requer testes específicos (como o procedimento TOST — *Two One-Sided Tests*; Schuirmann, 1987; Lakens, 2017), cujo planejamento está previsto para etapas posteriores ao MVP devido à necessidade de definição de margens substantivas ($\pm \Delta$) pelo usuário.

---

## 7. Reprodutibilidade, Rastreabilidade e Integridade de Experimentos

### 7.1. Reprodutibilidade Científica, Determinismo e Rastreabilidade

* **Decisões de Projeto:**
  * A especificação estabelece três níveis formais de reprodução ([Seção 5 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L611-L615)):
    * *Nível 1 (Reprodução de Apresentação):* Reconstrução de figuras e tabelas a partir de artefatos de resultados persistidos em disco, sem reexecução de inferência ou retreinamento.
    * *Nível 2 (Reprodução Analítica):* Reavaliação de hipóteses estatísticas e Fronteira de Pareto a partir de predições individuais salvas, sem retreinar modelos.
    * *Nível 3 (Reexecução Experimental):* Repetição do ciclo completo de treinamento sob o mesmo particionamento e derivação determinística de sementes.
  * O modelo de dados define o manifesto `ArtifactProvenance`, associando cada artefato gerado aos parâmetros, dados e identificadores de execução ([Seção 4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L557-L565)).
* **Justificativa e Fundamentação Científica:**
  * **Heil et al. (2021) — *Reproducibility Standards for Machine Learning in the Life Sciences*:** Trabalho de consenso na *Nature Methods* que formaliza os pilares de reprodutibilidade em ML, preconizando que código, sementes aleatórias, dados particionados e dependências computacionais sejam disponibilizados de forma auditável.
  * **REFORMS (Kapoor et al., 2024) — *Consensus-based Recommendations for Machine-learning-based Science*:** Diretrizes de consenso publicadas na *Science Advances* com 19 autores de referência. O checklist REFORMS prescreve que relatórios científicos distingam dados factuais medidos de alegações subjetivas, princípio adotado no desenho do gerador de relatórios e de `StructuredConclusion`.
  * **Freire et al. (2008) — *Provenance for Computational Tasks: A Survey*:** Artigo que fundamenta os dois eixos de proveniência adotados no framework:
    * *Proveniência Prospectiva:* O plano de execução e especificações estruturadas (`DatasetSchemaSpec`, `PreparationPlan`, `PartitionPlan`, `scenarios.json`, `models.json`).
    * *Proveniência Retrospectiva:* O registro histórico detalhado da execução real (`execution_state.json`, `CellResultRecord`, `TimingBreakdown`, `PredictionRecord`).
* **Limitações Técnicas e Determinismo:**
  * A literatura e a prática computacional indicam que a reprodutibilidade idêntica bit a bit em ponto flutuante é de difícil garantia entre arquiteturas de hardware distintas (ex.: x86 vs. ARM) ou bibliotecas de álgebra linear diferentes (OpenBLAS, MKL), devido à não-associatividade de operações aritméticas sob concorrência. O framework foca em determinismo algorítmico e rastreabilidade metodológica, documentando essa limitação técnica no ADR-007.

### 7.2. Geração Determinística de Sementes com `SeedSequence`

* **Decisões de Projeto:**
  * A especificação adota o mecanismo `numpy.random.SeedSequence` para derivar sementes de forma hierárquica e determinística a partir de uma semente mestre para cada dobra, célula $(m, c, f)$ e busca de hiperparâmetros (**ADR-007**, [M1.2 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L679); `CA-GER-02`).
* **Justificativa Técnica:**
  * **NumPy Documentation — *Parallel and Independent Random Number Generation with SeedSequence*:** A implementação moderna de geradores pseudoaleatórios em NumPy baseia-se em `SeedSequence` para fornecer fluxos estatisticamente independentes sem colisão no espaço de amostragem.
  * Práticas legadas baseadas em adições ad-hoc (como `seed + fold_id`) podem introduzir correlações no espaço de estados dos geradores, comprometendo a independência estocástica em execuções paralelas. O uso de `SeedSequence.spawn` viabiliza derivação de sequências descorrelacionadas mesmo em processamento paralelo.

---

## 8. Canonicalização, Serialização e Integridade no Sistema de Arquivos

### 8.1. Canonicalização de Objetos Heterogêneos em Machine Learning

* **Decisões de Projeto:**
  * O ADR-007 estabelece um contrato formal de serialização canônica para geração de hashes determinísticos de configurações (`config_hash`) e dados tabulares (`dataset_hash`) (**ADR-007**, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L199-L214)).
  * A especificação adota normalização Unicode na forma **NFC** (`unicodedata.normalize("NFC", s)`).
  * O contrato trata explicitamente casos de contorno em ponto flutuante IEEE 754: conversão de zero negativo (`-0.0`) para positivo (`0.0`) e mapeamento determinístico de valores especiais (`NaN`, `+Inf`, `-Inf`) para tokens canônicos.
  * Os resumos criptográficos são mantidos em arquivos internos de auditoria e omitidos das visualizações finais de relatório (`CA-E6-02`).
* **Justificativa, Fundamentação Normativa e Extensões Técnicas:**
  * **NIST FIPS PUB 180-4 (2015) — *Secure Hash Standard (SHS)*:** Especifica a função criptográfica de espalhamento **SHA-256**, adotada no framework para verificação de integridade e identificação de artefatos por conteúdo (*content-addressing*). A função de hash assegura detecção de corrupção ou alteração acidental; a comprovação de linhagem decorre do encadeamento no manifesto `ArtifactProvenance`.
  * **Unicode Consortium UAX #15 — *Unicode Normalization Forms*:** Especifica que sequências de texto equivalentes podem possuir diferentes fluxos de bytes em UTF-8 (formas compostas e decompostas). Sem a normalização canônica NFC (*Normalization Form C*), strings semanticamente idênticas produzem representações binárias distintas e hashes divergentes.
  * **RFC 8785 (2020) — *JSON Canonicalization Scheme (JCS)*:** Padrão IETF para canonicalização determinística de documentos JSON.
  * **Limitações do JCS em Machine Learning e Justificativa do ADR-007:**  
    A RFC 8785 foi concebida para o ecossistema JSON web tradicional (RFC 8259). Em computação científica e Machine Learning, o padrão apresenta restrições:
    1. *Valores Especiais IEEE 754:* O JCS proíbe expressamente `NaN`, `+Infinity` e `-Infinity`. Em pipelines de dados, `NaN` representa valores ausentes legítimos ou métricas indefinidas.
    2. *Diferença entre Inteiro e Ponto Flutuante:* O JCS colapsa `1.0` em `1`. Em Machine Learning, diferenciar um escalar contínuo de um contador discreto possui relevância semântica.
    3. *Normalização Unicode de Conteúdo:* A RFC 8785 não impõe normalização NFC ao texto original; ela apenas ordena chaves lexicograficamente em UTF-16.
    Essas restrições fundamentam o desenvolvimento do esquema de serialização do **ADR-007**, que estende as regras de canonicalização para compatibilidade com estruturas NumPy e valores científicos.
  * **Ocultamento de hashes na camada de apresentação:** A especificação orienta a omissão de sequências hexadecimais de hash nas tabelas finais de apresentação para preservar a clareza e legibilidade dos relatórios acadêmicos, mantendo os registros nos metadados de execução (`run_meta.json`).

### 8.2. Escrita Atômica em Dois Passos e Integridade no Sistema de Arquivos

* **Decisões de Projeto:**
  * A persistência de artefatos é especificada mediante escrita em dois passos: gravação em arquivo temporário no mesmo diretório (`<nome>.tmp.<pid>`), validação de integridade e substituição atômica via `os.replace` (`CA-GER-01`, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L177)).
* **Justificativa Técnica e Limitações Físicas:**
  * **POSIX.1-2017 (`rename(2)`) & Python Documentation (`os.replace`):** A chamada de sistema `rename(2)` em plataformas POSIX garante que a atualização da entrada de diretório ocorra de forma atômica. Processos concorrentes não observam arquivos corrompidos ou parcialmente gravados; havendo interrupção antes do término, o arquivo pré-existente permanece intacto.
  * **Limitação de Ponto de Montagem:** A atomicidade de `rename(2)` restringe-se a operações no **mesmo sistema de arquivos e mesmo ponto de montagem**. Por essa razão, a especificação exige a gravação do arquivo temporário no mesmo diretório de destino, prevenindo erros de link cruzado entre dispositivos (`EXDEV`).
  * **Atomicidade de Diretório vs. Durabilidade Física:** A atomicidade de visibilidade proporcionada por `os.replace` assegura consistência lógica contra interrupções de processo, mas não garante por si só durabilidade física em disco contra queda de energia do hardware (o que exigiria sincronização explícita com `fsync(2)` nos descritores do arquivo e do diretório pai).

---

## 9. Verificação Formal da Máquina de Estados com TLA+ e TLC

### 9.1. Model Checking com TLA+ e TLC na Orquestração da Execução Matricial

* **Decisões de Projeto:**
  * A orquestração da matriz experimental é modelada como uma **máquina de estados finita por célula** $(m, c, f)$, com transições entre os estados `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` e `CANCELLED` ([Seção 3.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L382-L393)).
  * O mecanismo de retomada verificada (*Checkpoint & Resume*) prevê a preservação de resultados persistidos e o bloqueio de retomadas inconsistentes sob alteração de dados ou parâmetros (`CA-E4B-02`, [Seção 3.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L400-L402)).
  * A especificação formal `MatrixExecutionAndResume.tla` está prevista como artefato de verificação do Marco M5, destinada a validar formalmente as propriedades de segurança e vivacidade do protocolo de orquestração sob execução concorrente.
* **Justificativa Teórica em Métodos Formais:**
  * **Lamport (2002) — *Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers*:** Apresenta a lógica temporal de ações (TLA+) e o verificador explícito de modelos TLC. TLA+ permite descrever formalmente sistemas de transição de estados. O model checker TLC realiza uma busca exaustiva no espaço de estados alcançáveis da especificação matemática, verificando:
    * *Invariantes de Segurança (Safety):* Assegura que estados inválidos não são atingidos (ex.: células `COMPLETED` não são sobrescritas em retomada; transições inválidas como `COMPLETED -> RUNNING` são inalcançáveis; células com falha não registram métricas como execução bem-sucedida).
    * *Propriedades de Vivacidade (Liveness):* Assegura que o sistema progride até uma condição terminal válida (ex.: sob condições de justiça, toda célula iniciada em `RUNNING` alcança um estado terminal `COMPLETED`, `FAILED` ou `CANCELLED`).
* **Distinção Conceitual e Limitações:**
  * **Distinção entre verificação formal e especificação funcional:** Registra-se que TLA+ e TLC constituem ferramentas de métodos formais e verificação de concorrência, não se confundindo com metodologias de desenvolvimento orientadas a especificações em linguagem natural (*Spec-Driven Development*).
  * **Fronteira da Prova Formal:** O model checking com TLC valida matematicamente que o **modelo conceitual abstrato** do protocolo é livre de deadlocks e violações de invariantes no espaço explorado. Contudo, **a verificação do modelo TLA+ não constitui prova formal do código em Python**. Falhas de implementação, particularidades do interpretador CPython ou falhas no sistema operacional permanecem fora do escopo do model checker, o que requer a validação complementar por meio de testes unitários e de integração descritos na documentação de engenharia.

---

## 10. Matriz Consolidada de Fundamentação das Decisões

A tabela a seguir consolida a relação entre as decisões de projeto, os documentos de origem, as justificativas técnicas, as fontes bibliográficas ou normativas, as evidências reportadas e as limitações identificadas:

| Decisão de Projeto / Especificação | Documento de Origem | Justificativa Técnica no Projeto | Fonte(s) de Suporte | Evidência Apresentada na Fonte | Limitações da Referência no Contexto do Projeto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D1: Arquitetura Agnóstica sem Estimadores Próprios** | `ARQUITETURA` L38; `SRS` L17 (ADR-001) | Permitir comparação justa de algoritmos heterogêneos sob as mesmas partições e métricas, sem acoplamento a bibliotecas específicas. | Princípio de escopo e RNF02 (Independência de Domínio) | — | Decisão de arquitetura de software e escopo do projeto; não demanda validação empírica externa. |
| **D2: Imutabilidade da Base Bruta e Zero Transformação Silenciosa** | `ARQUITETURA` L39; `SRS` L18, L37 (RF1.7) | Preservar a integridade física da fonte de dados e assegurar que toda limpeza seja declarada no `PreparationPlan`. | Heil et al. (2021); REFORMS (2024) | Estudos de caso demonstram que limpezas ad-hoc silenciosas introduzem vieses e dificultam a reprodutibilidade. | As fontes estabelecem o princípio de transparência de dados; o contrato funcional com `DatasetProfile` e `SanitizedDatasetView` é próprio do projeto. |
| **D3: Prevenção Estrutural de Data Leakage (Fit só no Treino Externo)** | `ARQUITETURA` L40, L182 (ADR-002); `SRS` L19, L46 (RF2.4) | Eliminar o vazamento de informações da validação/teste para as etapas de imputação, padronização e seleção de atributos. | Kapoor & Narayanan (2023); scikit-learn Pitfalls; Heil et al. (2021) | Revisão em 329 artigos comprovando que vazamento no pré-processamento esteve presente em centenas de estudos, inflando o desempenho. | A literatura prova o problema e a necessidade de isolamento; a arquitetura de duas camadas (Cenário vs. Modelo) é a resposta de engenharia do projeto. |
| **D4: Validação Cruzada Aninhada (*Nested CV*) e Ordem Canônica Intra-Célula** | `ARQUITETURA` L185 (ADR-003), L346; `SRS` L57 (RF3.5) | Mitigar o viés otimista na seleção de hiperparâmetros e assegurar avaliação imparcial da seleção dinâmica de atributos. | Cawley & Talbot (2010); Bergstra & Bengio (2012) | Demonstração matemática e empírica de que o erro de validação usado para calibrar $\theta$ é otimista, sendo mandatória a separação entre laço interno e externo. | Cawley & Talbot tratam de regularização em SVMs; a extensão do isolamento para a seleção dinâmica de atributos no laço interno é uma decisão arquitetural do framework. |
| **D5: Particionamento Agrupado (`GroupKFold`) com Isolamento de Grupos** | `ARQUITETURA` L366, L372; `SRS` L64 (RF4.1); `CA-COND-PART-01` | Evitar que observações correlacionadas da mesma entidade habitem treino e teste simultaneamente, superestimando o desempenho. | Roberts et al. (2017) | Simulações demonstram que validação aleatória em dados com dependência de grupo infla artificialmente o desempenho e subestima erros reais em novas entidades. | Foco original em ecologia/autocorrelação espacial; a regra algébrica $G \ge K$ e adaptações a outros domínios são condições algébricas estabelecidas no contrato. |
| **D6: Teste $t$ Corrigido de Nadeau-Bengio para Comparações Pareadas** | `ARQUITETURA` L188 (ADR-004), L468; `SRS` L77 (RF5.2); `CA-E5-02` | Corrigir a subestimação da variância causada pela sobreposição de dados de treino entre dobras de validação cruzada. | Nadeau & Bengio (2003); Dietterich (1998) | Dedução teórica de que a variância é subestimada pelo fator de sobreposição, restaurando a taxa de erro Tipo I ao nível nominal $\alpha$. | O artigo assume dobras de tamanhos idênticos; o uso da razão média efetiva e o alerta para CV > 20% em folds desiguais são extensões heurísticas adotadas no projeto. |
| **D7: Emprego do Teste de Wilcoxon com Alerta Amostral para $J < 6$** | `ARQUITETURA` L189 (ADR-004); `SRS` L77 (RF5.2); `CA-E5-01` | Fornecer inferência não-paramétrica para métricas não-normais, alertando sobre a impossibilidade combinatória de significância em dobras reduzidas. | Demšar (2006); dedução combinatória elementar | Demšar formaliza o Wilcoxon como padrão para ML; a combinatória prova que o menor $p$-valor bicaudal para $J=5$ é $0{,}0625 > 0{,}05$. | Demšar preconiza Wilcoxon para múltiplos datasets independentes, não para dobras de CV correlacionadas (limitação documentada no framework). |
| **D8: Controle de Falso Positivo: Holm-Bonferroni (FWER) e Benjamini-Hochberg (FDR)** | `ARQUITETURA` L482; `SRS` L79 (RF5.4); `CA-E5-02` | Permitir controle contra descobertas espúrias decorrentes de múltiplas comparações entre pares de modelos e cenários. | Holm (1979); Benjamini & Hochberg (1995) | Prova analítica de que Holm controla a FWER com maior poder que Bonferroni, e BH controla o FDR evitando hiperconservadorismo. | BH assume formalmente independência ou dependência positiva (PRDS) entre testes, premissa que nem sempre se sustenta estritamente em dobras de CV. |
| **D9: Proibição de Inferir Equivalência a Partir de Não-Significância ($p \ge \alpha$)** | `ARQUITETURA` L486, L489; `SRS` L20; `CA-E5-03` | Evitar a armadilha estatística de aceitar $H_0$ como prova de igualdade quando há apenas ausência de poder estatístico. | Altman & Bland (1995); Schuirmann (1987); Lakens (2017) | Literatura conceitual demonstrando que ausência de evidência não é prova de ausência de efeito; necessidade de testes formais (TOST). | Decisão de integridade metodológica; testes formais de equivalência (TOST) estão planejados para etapas posteriores ao MVP. |
| **D10: Serialização Canônica e Hashes de Integridade (SHA-256 e NFC)** | `ARQUITETURA` L199–L214 (ADR-007); `SRS` L32, L90; `CA-GER-02` | Permitir verificação de integridade bit a bit contra mutações acidentais e ancoragem de linhagem (*provenance*). | NIST FIPS 180-4; Unicode UAX #15; RFC 8785 (JCS) | Padrões normativos que definem o algoritmo SHA-256, equivalência canônica de strings e ordenação determinística de propriedades. | A RFC 8785 não suporta NaN/Inf nem diferencia 1 de 1.0; o projeto define especificação canônica própria extensível para tipos NumPy e científicos. |
| **D11: Hashes como Metadados Internos Ocultos ao Usuário Final** | `ARQUITETURA` L211–L213 (ADR-007); `SRS` L90 (RF6.4); `CA-E6-02` | Evitar poluição visual em tabelas e relatórios científicos, mantendo os hashes em arquivos de auditoria. | Decisão contextual de ergonomia de uso | — | Decisão orientada à clareza de leitura acadêmica (RNF07); sem necessidade de fundamentação teórica externa. |
| **D12: Persistência Atômica via Escrita Segura em Dois Passos** | `ARQUITETURA` L177, L401; `CA-GER-01` | Garantir que interrupções de processo não deixem artefatos JSON ou Parquet corrompidos em disco. | POSIX.1-2017 (`rename(2)`); Python Documentation (`os.replace`) | Especificação normativa POSIX comprovando que `rename` garante atomicidade de visibilidade no mesmo sistema de arquivos. | A atomicidade do ponteiro de diretório não garante durabilidade física em disco sem chamadas síncronas de gravação (`fsync`). |
| **D13: Rastreabilidade por Proveniência Retrospectiva (`ArtifactProvenance`)** | `ARQUITETURA` L557–L565; `SRS` L89 (RF6.3); `CA-E6-02` | Permitir que qualquer figura ou tabela exportada seja vinculada sem ambiguidade aos dados, partições e células geradoras. | Freire et al. (2008); Heil et al. (2021) | Artigos seminais de proveniência em computação científica definindo ontologias de grafos de linhagem retrospectiva para auditoria. | O projeto adota manifesto próprio em JSON em vez de ontologias mais complexas (como W3C PROV-O). |
| **D14: Desacoplamento entre Apresentação, Análise e Execução (Níveis 1–3 de Reprodução)** | `ARQUITETURA` L42, L495, L611–L615; `SRS` L21, L87; `CA-E6-01` | Possibilitar reestilização de tabelas/figuras ou reanálise estatística sem impor o custo computacional de retreinar modelos. | Freire et al. (2008); Peng (2011) | Obras de referência em ciência computacional demonstrando as vantagens de armazenar artefatos intermediários tipados em disco. | O desacoplamento exige armazenamento em disco de predições completas por observação, demandando formatos colunares eficientes (Parquet). |
| **D15: Verificação Formal da Máquina de Estados Matricial via TLA+/TLC** | `ARQUITETURA` L383–L393; Planejamento de Verificação | Provar ausência de deadlocks, corridas e corrupção de estado no modelo do orquestrador antes do código Python. | Lamport (2002) — *Specifying Systems* | Model checker TLC explora exaustivamente o grafo de estados atingíveis, provando invariantes de segurança e vivacidade. | Modela o comportamento abstrato do protocolo; não substitui testes de software do interpretador Python ou drivers de sistema operacional. |

---

## 11. Referências Bibliográficas e Normativas Completas

1. **ALTMAN, Douglas G.; BLAND, J. Martin.** Statistics notes: Absence of evidence is not evidence of absence. *BMJ*, v. 311, n. 7003, p. 485, 1995. DOI: [10.1136/bmj.311.7003.485](https://doi.org/10.1136/bmj.311.7003.485).
2. **BENJAMINI, Yoav; HOCHBERG, Yosef.** Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing. *Journal of the Royal Statistical Society: Series B (Methodological)*, v. 57, n. 1, p. 289–300, 1995. DOI: [10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x).
3. **BERGSTRA, James; BENGIO, Yoshua.** Random Search for Hyper-Parameter Optimization. *Journal of Machine Learning Research*, v. 13, n. 10, p. 281–305, 2012. URL: [https://jmlr.org/papers/v13/bergstra12a.html](https://jmlr.org/papers/v13/bergstra12a.html).
4. **CAWLEY, Gavin C.; TALBOT, Nicola L. C.** On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. *Journal of Machine Learning Research*, v. 11, n. 70, p. 2079–2107, 2010. URL: [https://jmlr.org/papers/v11/cawley10a.html](https://jmlr.org/papers/v11/cawley10a.html).
5. **DEMŠAR, Janez.** Statistical Comparisons of Classifiers over Multiple Data Sets. *Journal of Machine Learning Research*, v. 7, n. 1, p. 1–30, 2006. URL: [https://jmlr.org/papers/v7/demsar06a.html](https://jmlr.org/papers/v7/demsar06a.html).
6. **DIETTERICH, Thomas G.** Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms. *Neural Computation*, v. 10, n. 7, p. 1895–1923, 1998. DOI: [10.1162/089976698300017197](https://doi.org/10.1162/089976698300017197).
7. **FREIRE, Juliana; KOOP, David; SANTOS, Emanuele; SILVA, Cláudio T.** Provenance for Computational Tasks: A Survey. *Computing in Science & Engineering*, v. 10, n. 3, p. 11–21, 2008. DOI: [10.1109/MCSE.2008.79](https://doi.org/10.1109/MCSE.2008.79).
8. **HEIL, Benjamin J. et al.** Reproducibility standards for machine learning in the life sciences. *Nature Methods*, v. 18, n. 10, p. 1132–1135, 2021. DOI: [10.1038/s41592-021-01256-7](https://doi.org/10.1038/s41592-021-01256-7).
9. **HOLM, Sture.** A Simple Sequentially Rejective Multiple Test Procedure. *Scandinavian Journal of Statistics*, v. 6, n. 2, p. 65–70, 1979. URL: [https://www.jstor.org/stable/4615733](https://www.jstor.org/stable/4615733).
10. **IEEE; THE OPEN GROUP.** *The Open Group Base Specifications Issue 7, 2018 edition (POSIX.1-2017) — System Interfaces: rename()*. IEEE Std 1003.1-2017, 2018. URL: [https://pubs.opengroup.org/onlinepubs/9699919799/functions/rename.html](https://pubs.opengroup.org/onlinepubs/9699919799/functions/rename.html).
11. **KAPOOR, Sayash; NARAYANAN, Arvind.** Leakage and the reproducibility crisis in machine-learning-based science. *Patterns*, v. 4, n. 9, p. 100804, 2023. DOI: [10.1016/j.patter.2023.100804](https://doi.org/10.1016/j.patter.2023.100804).
12. **KAPOOR, Sayash et al.** REFORMS: Consensus-based Recommendations for Machine-learning-based Science. *Science Advances*, v. 10, n. 18, p. eadk3452, 2024. DOI: [10.1126/sciadv.adk3452](https://doi.org/10.1126/sciadv.adk3452).
13. **LAKENS, Daniël.** Equivalence Testing for Psychological Research: A Tutorial. *Advances in Methods and Practices in Psychological Science*, v. 1, n. 2, p. 259–269, 2017. DOI: [10.1177/2515245918770963](https://doi.org/10.1177/2515245918770963).
14. **LAMPORT, Leslie.** *Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers*. Boston: Addison-Wesley, 2002. ISBN: 0-321-14306-X. URL: [https://lamport.azurewebsites.net/tla/book.html](https://lamport.azurewebsites.net/tla/book.html).
15. **NADEAU, Claude; BENGIO, Yoshua.** Inference for the Generalization Error. *Machine Learning*, v. 52, n. 3, p. 239–281, 2003. DOI: [10.1023/A:1024068626366](https://doi.org/10.1023/A:1024068626366).
16. **NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST).** *Secure Hash Standard (SHS)*. Federal Information Processing Standards Publication (FIPS PUB) 180-4, Gaithersburg: NIST, 2015. DOI: [10.6028/NIST.FIPS.180-4](https://doi.org/10.6028/NIST.FIPS.180-4).
17. **NUMPY DEVELOPERS.** *Parallel and Independent Random Number Generation with SeedSequence*. NumPy Reference Documentation, v. 1.26/2.0, 2024. URL: [https://numpy.org/doc/stable/reference/random/parallel.html](https://numpy.org/doc/stable/reference/random/parallel.html).
18. **PARNAS, David L.** On the Criteria To Be Used in Decomposing Systems into Modules. *Communications of the ACM*, v. 15, n. 12, p. 1053–1058, 1972. DOI: [10.1145/361598.361623](https://doi.org/10.1145/361598.361623).
19. **PENG, Roger D.** Reproducible Research in Computational Science. *Science*, v. 334, n. 6060, p. 1226–1227, 2011. DOI: [10.1126/science.1213847](https://doi.org/10.1126/science.1213847).
20. **PYTHON SOFTWARE FOUNDATION.** *os.replace(src, dst) — Miscellaneous operating system interfaces*. Python 3 Standard Library Documentation, 2024. URL: [https://docs.python.org/3/library/os.html#os.replace](https://docs.python.org/3/library/os.html#os.replace).
21. **ROBERTS, David R. et al.** Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, v. 40, n. 8, p. 913–929, 2017. DOI: [10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881).
22. **RUNDGREN, Anders; BACON, Grant; WEST, Mike.** *JSON Canonicalization Scheme (JCS)*. Request for Comments (RFC) 8785, Internet Engineering Task Force (IETF), 2020. DOI: [10.17487/RFC8785](https://doi.org/10.17487/RFC8785).
23. **SCHUIRMANN, Donald J.** A comparison of the Two One-Sided Tests Procedure and the Power Approach for assessing the equivalence of average bioavailability. *Journal of Pharmacokinetics and Biopharmaceutics*, v. 15, n. 6, p. 657–680, 1987. DOI: [10.1007/BF01068419](https://doi.org/10.1007/BF01068419).
24. **SCIKIT-LEARN DEVELOPERS.** *Common pitfalls and recommended practices*. scikit-learn documentation, 2024. URL: [https://scikit-learn.org/stable/common_pitfalls.html](https://scikit-learn.org/stable/common_pitfalls.html).
25. **UNICODE CONSORTIUM.** *Unicode Standard Annex #15: Unicode Normalization Forms*. UAX #15, Version 15.1.0, 2023. URL: [https://www.unicode.org/reports/tr15/](https://www.unicode.org/reports/tr15/).
