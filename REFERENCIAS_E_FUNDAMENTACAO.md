# Referências Bibliográficas e Fundamentação Teórico-Técnica — `experimental-ml-framework`

> **Documento:** Catálogo de Fundamentação Teórica, Metodológica, Estatística e Normativa  
> **Versão:** 1.0.0  
> **Data:** 31 de Outubro de 2026  
> **Documentos Relacionados:** [`ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md) | [`ESPECIFICACAO_REQUISITOS.md`](./engenharia_software/ESPECIFICACAO_REQUISITOS.md) | [`ETAPA_ATUAL_ENGENHARIA.md`](./engenharia_software/ETAPA_ATUAL_ENGENHARIA.md) | [`README.md`](./README.md)

---

## 1. Introdução e Objetivo da Fundamentação

O `experimental-ml-framework` é uma biblioteca modular e ferramenta de linha de comando (`expml`) em Python concebida para a condução, auditoria, comparação estatística e publicação reprodutível de experimentos de Aprendizado de Máquina (*Machine Learning* — ML) em regressão e classificação.

O propósito deste documento é centralizar a fundamentação teórica, metodológica, estatística e normativa de cada decisão arquitetural do projeto. O objetivo é assegurar a **defensabilidade acadêmica e técnica** das escolhas realizadas, permitindo que pesquisadores, orientadores, revisores e desenvolvedores compreendam não apenas a estrutura do sistema, mas as evidências científicas, os padrões da indústria e as justificativas de engenharia que sustentam seus contratos.

Para evitar generalizações indevidas, este documento segue diretrizes estritas:
1. **Diferenciação epistemológica:** Distingue-se evidência empírica formal, recomendação de consenso da comunidade, padrão técnico normativo e decisão contextual de engenharia de software.
2. **Declaração explícita de limitações:** Para cada trabalho citado, documenta-se o que a fonte efetivamente sustenta e quais aspectos da decisão decorrem de escolhas operacionais próprias do framework.
3. **Mapeamento direto aos contratos:** Toda referência é vinculada às decisões e seções de [`ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md) e [`ESPECIFICACAO_REQUISITOS.md`](./engenharia_software/ESPECIFICACAO_REQUISITOS.md).

---

## 2. Escopo e Estado do Planejamento

Para garantir que a fundamentação reflita a realidade do projeto, distingue-se rigorosamente o estado das funcionalidades:

* **Onda 1 (MVP Imediato — Contratos Completos e Inegociáveis):**
  * Ingestão imutável de dados tabulares (`.csv`, `.txt` com/sem cabeçalho, `DataFrame`) e perfilamento diagnóstico com separação estrita entre `CONFIRMED_ISSUE` e `HEURISTIC_WARNING` (Etapa 1).
  * Exploração rotulada (`EXPLORATORY_FULL_DATA`) e cenários de atributos fixos (`mode="FIXED"`) e dinâmicos (`mode="DYNAMIC"` com filtro de colinearidade, Top-$K$ e ranking multi-critério ajustados por partição) (Etapa 2).
  * Registro agnóstico de modelos externos (Scikit-Learn, XGBoost, modelos analíticos/biométricos com `requires_fit=False`, funções customizadas e circuitos quânticos via `ModelDiagnostics`), pré-processamento em duas camadas (Cenário e Modelo) com bloqueio de duplicação, e busca de hiperparâmetros aninhada (*Nested CV* via Grid e Random Search) (Etapa 3).
  * Geração e validação matemática de `PartitionPlan` compartilhado (*K-Fold*, *Stratified K-Fold*, *Group K-Fold* e *Holdout*), execução matricial com tolerância a falhas, escrita em dois passos (`.tmp` + `os.replace`), rastreabilidade por `observation_id` e retomada verificada (*Checkpoint & Resume*) (Etapa 4).
  * Consolidação descritiva, teste $t$ corrigido de Nadeau-Bengio, teste pareado de Wilcoxon, ajustes de Holm-Bonferroni e Benjamini-Hochberg, análise multiobjetivo por Fronteira de Pareto e síntese textual rastreável via `StructuredConclusion` (Etapa 5).
  * Relatórios científicos desacoplados (Markdown/HTML), 7 famílias de tabelas e figuras modulares, linhagem por artefato (`ArtifactProvenance`) e hashes técnicos de integridade (`SHA-256`) ocultos na apresentação ao usuário (Etapa 6).
* **Onda 2 (Extensões do MVP — Requisitos Aprovados aguardando fechamento de casos de contorno):**
  * Regressão multialvo (`MULTI_TARGET_REGRESSION`, `target_col: Sequence[str]`).
  * Transformações reversíveis na variável-alvo (`TargetTransformSpec`).
  * Conjunto de candidatos não rotulados (`unlabeled_pool`) e funções de aquisição sequencial (`EI`, `UCB`/`LCB`, `Exploitation`, `Exploration`).
  * Reamostragem por *Bootstrap* ($B$ repetições com validação *Out-of-Bag* e incerteza de comitê) e estratégias cronológicas (*Temporal Split*).
  * Redução de dimensionalidade intra-fold (`PCA` em `select_features_in_fold`).
* **Evoluções Pós-MVP (Seção 6.2 de `ARQUITETURA_E_CONTRATOS.md`):**
  * Seletores *wrapper* (RFE), métodos embutidos ($L_1$/Lasso) e importância por permutação.
  * Otimização Bayesiana (Optuna) e execução distribuída em clusters.
  * Testes estatísticos globais (Friedman + Nemenyi/Dunn) e testes formais de equivalência (TOST).

---

## 3. Arquitetura Modular e Separação de Responsabilidades

### 3.1. Princípio da Decomposição Modular e Ocultamento de Decisões de Projeto

* **Decisões do Framework:**
  * Divisão do sistema em **três camadas arquiteturais unidirecionais** (Camada 1: Definição e Triagem; Camada 2: Validação e Execução Matricial; Camada 3: Comparação Estatística e Publicação) apoiadas por dois pacotes fundacionais transversais (`core` e `metrics`) ([Seção 2.1 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L57-L107)).
  * Organização física dos módulos em níveis estritos de dependência (Nível 0 a Nível 7) para impedir ciclos de importação ([Seção 2.3 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L138-L154)).
  * Adoção de **funções modulares puras e estruturas de dados imutáveis** em vez de hierarquias de classes de serviço ou objetos mutáveis com estado (**ADR-008**, [Seção 1 e Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L212-L218)).
* **Fundamentação Teórica e Técnica:**
  * **Parnas (1972) — *On the Criteria to Be Used in Decomposing Systems into Modules*:** Estabelece o princípio fundamental de que a modularização de sistemas deve ser guiada pelo ocultamento de decisões de projeto (*information hiding*) e pela independência entre módulos com interfaces bem definidas, em oposição à divisão baseada puramente em etapas de processamento procedurais. No framework, cada módulo encapsula uma responsabilidade que pode evoluir ou falhar independentemente (ex.: o módulo `metrics` desconhece algoritmos de aprendizado; o módulo `validation` desconhece a lógica de modelos e métricas).
  * **Transparência Referencial e Prevenção de Efeitos Colaterais:** A escolha por evitar herança e classes de serviço mutáveis (**ADR-008**) fundamenta-se no princípio de que funções que recebem dados e retornam novos registros explícitos (`fitted_params`, `SelectionResult`) eliminam variáveis de instância compartilhadas que frequentemente causam vazamento acidental de pesos e contaminação de estado entre partições (*folds*).
* **Evidência Específica na Fonte:**
  * Parnas (1972, p. 1056–1058) demonstra comparativamente que a decomposição baseada em segredos de projeto e interfaces limpas proporciona facilidade de modificação, desenvolvimento independente e testabilidade superior quando comparada a sistemas onde estruturas de dados globais ou representações internas transitam livremente entre componentes.
* **Limitações da Fundamentação:**
  * Parnas (1972) formulou seus princípios no contexto de engenharia de software geral, sem focar nas especificidades de pipelines científicos de Machine Learning.
  * O framework ainda integra estimadores de bibliotecas externas (como `scikit-learn` e `xgboost`), que são internamente orientados a objetos e mutáveis. O ADR-008 isola essa mutabilidade nas fronteiras funcionais (`instantiate_fresh_model`, `fit_model`, `predict_model`), mas não extingue a natureza de objeto das bibliotecas subjacentes.

### 3.2. Separação Estrita entre Interface de Linha de Comando (CLI) e Lógica de Domínio

* **Decisões do Framework:**
  * CLI modularizada em `src/experimental_ml/cli/` baseada em `argparse` da biblioteca padrão, organizada por subcomandos (`data`, `features`, `models`, `partition`, `run`, `stats`, `report`) ([Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L156-L179)).
  * Proibição absoluta de lógica de negócio nos módulos `cmd_*.py`: cada subcomando atua estritamente como adaptador de argumentos de entrada, delega a computação às funções públicas dos módulos científicos e traduz os resultados para códigos de saída padronizados (`0` para sucesso, `1` para falha de execução, `2` para erro de validação/bloqueio) ([RNF07 de `ESPECIFICACAO_REQUISITOS.md`](./engenharia_software/ESPECIFICACAO_REQUISITOS.md#L102)).
* **Fundamentação Técnica:**
  * **Princípio da Separação de Mecanismo e Política (*Separation of Mechanism and Policy*) e Padrão *Ports and Adapters* (Arquitetura Hexagonal):** A interface de usuário (seja terminal, script Python ou notebook) deve ser tratada como um mero mecanismo de entrega. A lógica científica reside exclusivamente no núcleo funcional, permitindo que os experimentos sejam operados via scripts automatizados ou via CLI sem duplicação de validações ou regras metodológicas.
* **Limitações:**
  * A convenção de códigos de saída `0`, `1` e `2` segue a prática padrão POSIX/Unix e utilitários GNU, sendo uma decisão contextual de engenharia de software e usabilidade no ecossistema de terminal Linux.

---

## 4. Metodologia Experimental e Prevenção Estrutural de Data Leakage

### 4.1. Taxonomia de Vazamento de Dados e o Princípio de Construção Imune (*Leakage-Free by Design*)

* **Decisões do Framework:**
  * Princípio estruturante 3: Qualquer operação que estime parâmetros a partir de observações (imputação, escalonamento, codificação de categorias, seleção dinâmica de atributos e otimização de hiperparâmetros) deve ser calibrada estritamente com os dados de treino da partição externa em execução ([Princípio 3 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L40)).
  * Separação mandatória entre saneamento estrutural determinístico pré-partição (remoção de observações com alvo nulo e exclusão de colunas proibidas/constantes) e transformações estatísticas parametrizadas intra-fold (**ADR-002**, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L182-L184)).
  * Rotulagem exploratória explícita (`scope = "EXPLORATORY_FULL_DATA"`) na Etapa 2, com bloqueio arquitetural contra a conversão automática do relatório exploratório em seleção formal pré-partição (`CA-E2-01`, [Seção 3.2 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L275-L279)).
* **Fundamentação Científica e Empírica:**
  * **Kapoor & Narayanan (2023) — *Leakage and the Reproducibility Crisis in Machine-Learning-Based Science*:** Realizam uma revisão sistemática abrangendo 329 artigos científicos em 17 campos quantitativos, comprovando que o vazamento de dados é uma das causas primárias da crise de reprodutibilidade em ciência baseada em ML. Os autores propõem uma taxonomia de 8 tipos de vazamento, destacando que *pré-processar dados antes da partição* e *selecionar atributos utilizando o conjunto de dados completo* geram métricas de desempenho artificialmente infladas que desmoronam na aplicação prática.
  * **Heil et al. (2021) — *Reproducibility Standards for Machine Learning in the Life Sciences*:** Estabelecem diretrizes para prevenção de vazamento de dados em ciências biológicas e médicas, exigindo a separação estrita e auditável entre o ajuste de pré-processamento e os dados de avaliação.
  * **scikit-learn Documentation — *Common Pitfalls and Recommended Practices*:** Documenta empiricamente que estimar média e desvio-padrão (padronização), calcular frequências de classes ou realizar seleções univariadas na base inteira transfere informação da distribuição de teste para o modelo, invalidando as garantias estatísticas da validação cruzada.
* **Evidência Específica na Fonte:**
  * Kapoor & Narayanan (2023, p. 100804) demonstram através de um estudo de caso reprodutivo em predição de conflitos civis que modelos complexos de ML, apontados na literatura como altamente superiores a modelos estatísticos tradicionais, perdiam toda a sua suposta superioridade e empatavam com regressões logísticas clássicas assim que o vazamento de dados no pré-processamento era corrigido.
* **Limitações da Fundamentação:**
  * As fontes comprovam que o vazamento ocorre com frequência alarmante e demonstram suas consequências epistemológicas devastadoras. No entanto, a literatura científica não prescreve a implementação de software específica adotada no framework (o contrato em duas camadas do ADR-002 e os critérios `CA-E1-02` e `CA-E2-01`). Essa implementação representa a resposta de engenharia do projeto para fazer cumprir mecanicamente as recomendações teóricas.

---

## 5. Validação Cruzada, Particionamento e Otimização de Hiperparâmetros

### 5.1. Viés de Seleção e a Necessidade de Validação Cruzada Aninhada (*Nested CV*)

* **Decisões do Framework:**
  * Confinamento da busca de hiperparâmetros (Grid Search e Random Search) exclusivamente dentro do conjunto de treinamento da partição externa por meio de validação cruzada aninhada (*Nested Cross-Validation*), com exigência explícita da métrica e direção de otimização (**ADR-003**, [RF3.5 de `ESPECIFICACAO_REQUISITOS.md`](./engenharia_software/ESPECIFICACAO_REQUISITOS.md#L57); `CA-E3-02`, [Seção 3.3 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L340-L347)).
  * Ordem canônica intra-célula: quando uma célula combina cenário dinâmico e busca de hiperparâmetros, o pré-processamento e a seleção dinâmica de atributos são reajustados dentro de cada dobra interna (*inner fold*) para a escolha de $\theta^*$, e reajustados no treino externo completo antes da avaliação final na partição de validação externa (**ADR-003**, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L185-L186)).
* **Fundamentação Teórica e Empírica:**
  * **Cawley & Talbot (2010) — *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*:** Demonstram analítica e empiricamente que o processo de seleção de modelos e ajuste de hiperparâmetros é suscetível a sobreajuste (*over-fitting in model selection*). Se o mesmo laço de validação cruzada for utilizado para selecionar os hiperparâmetros e reportar o erro de generalização final, a estimativa resultante apresentará um **viés de seleção substancialmente otimista**. Os autores provam que o protocolo de *Nested Cross-Validation* (ou *Double Cross-Validation*) é estritamente necessário para obter estimativas não tendenciosas do erro de generalização.
  * **Bergstra & Bengio (2012) — *Random Search for Hyper-Parameter Optimization*:** Demonstram teórica e empiricamente que a busca aleatória de hiperparâmetros (*Random Search*) é mais eficiente que a busca em grade (*Grid Search*) para otimizar modelos em espaços de parâmetros onde apenas um subconjunto de hiperparâmetros possui dimensão efetiva relevante, fundamentando o suporte nativo a ambos os métodos no MVP da Etapa 3B.
* **Evidência Específica na Fonte:**
  * Cawley & Talbot (2010, p. 2079–2107) comprovam que a magnitude do viés otimista induzido pela escolha de hiperparâmetros sem validação aninhada é frequentemente **da mesma ordem de grandeza ou superior às diferenças de desempenho entre diferentes famílias de algoritmos**, levando pesquisadores a declarar falsas superioridades metodológicas.
* **Limitações da Fundamentação:**
  * Cawley & Talbot (2010) concentram-se no ajuste de hiperparâmetros e seleção de modelos baseada em regularização (SVMs). A extensão implementada no ADR-003 — que impõe a execução do pipeline completo de seleção dinâmica de atributos (Camada 1) dentro de cada dobra interna da busca de hiperparâmetros — decorre logicamente do mesmo princípio, mas constitui uma decisão de composição de contratos própria deste framework.

### 5.2. Particionamento Estruturado e Prevenção de Falso Otimismo por Dependência Amostral

* **Decisões do Framework:**
  * Suporte nativo e obrigatório ao particionamento agrupado (`GroupKFold`), com validação matemática pré-execução comprovando disjunção total de grupos entre treino e validação ($\text{Grupos}(\text{Train}_k) \cap \text{Grupos}(\text{Val}_k) = \emptyset$) e entre treino e *Holdout Final* (`CA-E4A-01` e `CA-COND-PART-01`, [Seção 3.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L369-L373)).
* **Fundamentação Científica:**
  * **Roberts et al. (2017) — *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*:** Artigo fundamental em ecologia quantitativa e modelagem ambiental que demonstra as falhas graves da validação cruzada aleatória tradicional (*random k-fold*) quando aplicada a dados estruturados. Os autores evidenciam que a presença de autocorrelação espacial, temporal ou estruturas hierárquicas (amostras pertencentes à mesma unidade amostral, parcela florestal, paciente ou sensor) viola a premissa de observações independentes e identicamente distribuídas (IID). A validação cruzada aleatória permite que amostras altamente correlacionadas habitem simultaneamente o treino e o teste, resultando em subestimação severa do erro preditivo e incapacidade de generalização. Os autores prescrevem formalmente o uso de estratégias de bloqueio (*Block Cross-Validation* / *Grouped Cross-Validation*).
* **Evidência Específica na Fonte:**
  * Roberts et al. (2017, p. 913–929, DOI: 10.1111/ecog.02881) comprovam empiricamente através de simulações e dados reais que a validação cruzada aleatória superestima a acurácia de predição em até centenas de por cento em dados estruturados, enquanto esquemas bloqueados refletem fidedignamente o erro em novas entidades espaciais/temporais.
* **Limitações da Fundamentação:**
  * Roberts et al. (2017) focam em dados espaciais e ecológicos. A aplicação a inventários florestais (como no caso de referência `prognose_florestal` onde parcelas contêm múltiplas medições repetidas) é diretamente sustentada pela fonte, mas a imposição da pré-condição $G \ge K$ (número de grupos maior ou igual ao número de dobras) é uma regra de contorno algébrico implementada pelo framework.

---

## 6. Comparação Estatística de Modelos e Controle de Multiplicidade

### 6.1. O Problema da Não-Independência de Folds e a Correção de Variância de Nadeau-Bengio

* **Decisões do Framework:**
  * Proibição expressa de tratar dobras de validação cruzada como amostras independentes em testes $t$ de Student convencionais ([Seção 3.5 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L468)).
  * Adoção mandatória do **teste $t$ corrigido de Nadeau-Bengio** para comparações pareadas sob validação cruzada (**ADR-004**, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L188); `CA-E5-02`).
  * Tratamento analítico do caso de variância das diferenças nula ($s^2_d = 0$) retornando diferença nula e $p = 1.0$ sem divisão por zero (**ADR-004**).
* **Fundamentação Teórica:**
  * **Nadeau & Bengio (2003) — *Inference for the Generalization Error*:** Artigo seminal que demonstra teoricamente a razão pela qual testes inferenciais clássicos falham ao avaliar algoritmos de aprendizado. Em validação cruzada de $K$ dobras, cada partição de teste é avaliada por um modelo treinado em dados que se sobrepõem em $(K-2)/(K-1)$ dos dados de treinamento. Essa sobreposição maciça induz uma correlação positiva estrita entre os erros observados nas diferentes dobras. Aplicar um teste $t$ pareado convencional ignorando essa dependência subestima drasticamente a variância do erro de generalização, inflando a taxa de erro Tipo I (falsos positivos, declarando significância onde há mero ruído amostral).
  * Nadeau e Bengio derivam formalmente a correção da variância para o estimador reamostrado:
    $$\sigma^2_{\text{corrigida}} = \left( \frac{1}{J} + \frac{n_{\text{val}}}{n_{\text{train}}} \right) s^2_d$$
    onde $J$ é o número de repetições/dobras e $s^2_d$ é a variância amostral das diferenças observadas.
  * **Dietterich (1998) — *Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms*:** Demonstra previamente que o teste $t$ pareado padrão sobre dobras de CV possui taxa de erro Tipo I inaceitavelmente elevada e analisa as limitações empíricas de testes aproximados.
* **Evidência Específica na Fonte:**
  * Nadeau & Bengio (2003, p. 239–281, DOI: 10.1023/A:1024068626366) comprovam analiticamente e por simulações de Monte Carlo que, enquanto o teste $t$ convencional atinge taxas de erro Tipo I nominais de 5% rejeitando a hipótese nula em mais de 20% a 50% das vezes em dados nulos, o teste $t$ corrigido restaura o controle do nível de significância próximo ao valor nominal $\alpha$.
* **Limitações da Fundamentação e Extensões do Projeto:**
  * **Folds de tamanhos desiguais:** O artigo original de Nadeau & Bengio (2003) deduz a fórmula sob a premissa de que a razão $n_{\text{val}} / n_{\text{train}}$ é constante em todas as dobras (como ocorre no $K$-Fold simples). No entanto, sob estratégias como `GroupKFold`, o número de amostras em cada grupo varia, fazendo com que a razão $n_{\text{val}, j} / n_{\text{train}, j}$ varie entre as dobras. O framework adota como decisão de engenharia a **razão média efetiva** $\overline{(n_{\text{val}} / n_{\text{train}})}$ e emite alerta metodológico se o coeficiente de variação dos tamanhos de dobra exceder 20% (**ADR-004**). Essa adaptação heurística é uma decisão interna do projeto e não está no artigo de 2003.

### 6.2. Cuidados Metodológicos na Transposição do Teste de Wilcoxon e Limites Amostrais

* **Decisões do Framework:**
  * Oferta do **teste pareado de Wilcoxon** (*Wilcoxon signed-rank test*) como alternativa não-paramétrica para comparação de métricas, com tratamento explícito de diferenças nulas ($d_j = 0$) e **alerta obrigatório de baixo poder amostral quando $J < 6$** (**ADR-004**, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L189); `CA-E5-01`).
* **Análise Crítica da Literatura e Distinção Epistemológica:**
  * **Demšar (2006) — *Statistical Comparisons of Classifiers over Multiple Data Sets*:** Trabalho clássico de referência para comparações estatísticas em Machine Learning. Demšar recomenda formalmente o teste de Wilcoxon pareado e testes baseados em postos (como o teste de Friedman e pós-testes de Nemenyi) para comparar algoritmos.
  * **Atenção Metodológica Mandatória:** O trabalho de Demšar (2006) preconiza o teste de Wilcoxon para comparações de classificadores avaliados em **múltiplos conjuntos de dados independentes** ($N \ge 10$ a $30$ bases distintas). A aplicação do teste de Wilcoxon sobre $J$ dobras de validação cruzada em um *único conjunto de dados* incorre no mesmo problema de violação de independência apontado por Nadeau & Bengio (2003) e Dietterich (1998), uma vez que as diferenças entre os modelos nas dobras compartilham amostras de treino correlacionadas.
  * **Como o framework posiciona essa limitação:** O framework não adota cegamente o Wilcoxon como árbitro supremo da validação cruzada. Ele o implementa como alternativa robusta a distribuições não-normais de diferenças, mas documenta a limitação em `evaluate_method_suitability` e impede sua aplicação isolada sem o alerta ao pesquisador.
  * **Justificativa do Limite Amostral $J < 6$:** O teste de Wilcoxon pareado bicaudal com $J$ pares de diferenças não nulas tem como menor $p$-valor possível (quando todas as diferenças têm o mesmo sinal):
    $$p_{\text{mínimo}} = 2 \times \left( \frac{1}{2} \right)^J = \frac{1}{2^{J-1}}$$
    Para $J = 5$, o menor $p$-valor atingível é $1/16 = 0{,}0625$. Portanto, sob o nível de significância convencional $\alpha = 0{,}05$, é **matematicamente impossível** rejeitar a hipótese nula com $J \le 5$ dobras, independentemente de quão superior seja um modelo. Essa dedução aritmética elementar fundamenta o alerta impeditivo embutido no ADR-004.

### 6.3. Controle da Taxa de Falso Positivo em Comparações Múltiplas: FWER vs. FDR

* **Decisões do Framework:**
  * Disponibilização dos métodos de correção de multiplicidade de **Holm-Bonferroni** e **Benjamini-Hochberg** na Etapa 5B (`CA-E5-02`, [Seção 3.5 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L482)).
  * Exigência de que a estrutura `ComparisonSpec` defina a família de hipóteses analisada e de que o relatório informe se o controle aplicado é de FWER ou FDR.
* **Fundamentação Teórica:**
  * **Holm (1979) — *A Simple Sequentially Rejective Multiple Test Procedure*:** Introduz o método sequencialmente rejeitador de Bonferroni (Holm-Bonferroni) para controle rigoroso da taxa de erro por família (*Family-Wise Error Rate* — FWER). O método ordena os $p$-valores brutos $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$ e compara cada $p_{(i)}$ contra $\alpha / (m - i + 1)$. O método de Holm é estritamente mais poderoso que a correção clássica de Bonferroni ($p_i \le \alpha / m$) sob quaisquer circunstâncias, mantendo o controle exato da probabilidade de cometer ao menos um erro Tipo I em toda a família de testes.
  * **Benjamini & Hochberg (1995) — *Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing*:** Estabelecem o conceito revolucionário da Taxa de Falsas Descobertas (*False Discovery Rate* — FDR), definida como a proporção esperada de erros Tipo I entre todas as hipóteses rejeitadas. Em matrizes experimentais com dezenas de comparações entre combinações (Modelo $\times$ Cenário), controlar a FWER via Bonferroni ou Holm torna-se excessivamente conservador, destruindo o poder estatístico do experimento. O procedimento de Benjamini-Hochberg (BH) ajusta os $p$-valores ordenados por $p_{(i)} \times m / i$ (com ajuste monotônico cumulativo), equilibrando a descoberta de efeitos reais com o controle proporcional de falsos positivos.
* **Evidência Específica na Fonte:**
  * Benjamini & Hochberg (1995, p. 289–300) provam matematicamente que o procedimento garante $\text{E}[\text{FDR}] \le \frac{m_0}{m} q^* \le q^*$, assegurando poder estatístico superior em comparações científicas em larga escala.
* **Limitações da Fundamentação:**
  * O procedimento de Benjamini-Hochberg assume formalmente independência ou dependência positiva (PRDS — *Positive Regression Dependency on Subsets*) entre as estatísticas de teste. Em comparações par a par de múltiplos modelos que competem sobre as mesmas dobras, correlações arbitrárias complexas podem emergir, aspecto que o framework documenta nas notas metodológicas da Etapa 5.

### 6.4. Proibição de Inferir Equivalência a Partir de Não-Significância Estatística

* **Decisões do Framework:**
  * Princípio metodológico: Quando $p \ge \alpha$, o framework proíbe declarar equivalência ou paridade de desempenho entre modelos. O objeto `StructuredConclusion` emite obrigatoriamente o status `INCONCLUSIVE_NO_SIGNIFICANT_DIFFERENCE` ([Princípio 4 de `ESPECIFICACAO_REQUISITOS.md`](./engenharia_software/ESPECIFICACAO_REQUISITOS.md#L20); `CA-E5-03`, [Seção 3.5 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L486-L489)).
* **Fundamentação Epistemológica e Estatística:**
  * Princípio basilar da inferência de Neyman-Pearson e Fisher: *"Ausência de evidência não é evidência de ausência"* (Altman & Bland, 1995). A não-rejeição de $H_0$ ($p \ge 0{,}05$) pode decorrer unicamente de baixo poder amostral (como amostras pequenas de dobras, $J \le 5$) ou variância elevada entre as dobras, jamais provando que a diferença real entre os algoritmos seja nula. Afirmar equivalência exige testes formais de equivalência (como TOST — *Two One-Sided Tests*), previstos apenas para evoluções pós-MVP.

---

## 7. Reprodutibilidade, Rastreabilidade e Integridade de Experimentos

### 7.1. Distinção entre Reprodutibilidade Numérica, Experimental e Rastreabilidade

* **Decisões do Framework:**
  * Estabelecimento de três níveis formais de reprodutibilidade ([Seção 5 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L611-L615)):
    * *Nível 1 (Reprodução de Apresentação):* Regeneração de tabelas e figuras a partir de resultados persistidos em disco sem execução de código de modelo.
    * *Nível 2 (Reprodução Analítica):* Recálculo de testes estatísticos e Fronteira de Pareto a partir de predições persistidas sem retreinamento.
    * *Nível 3 (Reexecução Experimental):* Reexecução do treinamento com mesmo particionamento e controle hierárquico de sementes.
  * Manifesto de proveniência por artefato (`ArtifactProvenance`), vinculando cada figura ou tabela aos dados brutos, células e hashes geradores ([Seção 4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L557-L565)).
* **Fundamentação Científica:**
  * **Heil et al. (2021) — *Reproducibility Standards for Machine Learning in the Life Sciences*:** Publicação de consenso na *Nature Methods* que define padrões de reprodutibilidade em ML. Os autores separam os níveis de reprodutibilidade científica e enfatizam que publicações sérias devem fornecer não apenas código, mas a rastreabilidade total das sementes, versões de bibliotecas, configurações exatas de hiperparâmetros e dados particionados.
  * **REFORMS (Kapoor et al., 2024) — *Consensus-based Recommendations for Machine-learning-based Science*:** Iniciativa de consenso publicada na *Science Advances* com 19 autores de referência internacional. O checklist REFORMS formaliza diretrizes em 8 áreas: desenho do estudo, transparência de dados, prevenção de vazamento, reprodutibilidade de código, métricas apropriadas e apresentação de resultados sem alegações exageradas.
  * **Freire et al. (2008) — *Provenance for Computational Tasks: A Survey*:** Artigo fundamental em informática científica que formaliza a distinção entre:
    * *Proveniência Prospectiva (Prospective Provenance):* O fluxo computacional, plano de execução ou especificação de pipeline planejado para gerar um produto de dados (no framework: `DatasetSchemaSpec`, `PreparationPlan`, `PartitionPlan`, `scenarios.json`, `models.json`).
    * *Proveniência Retrospectiva (Retrospective Provenance):* O registro histórico do que efetivamente ocorreu durante uma execução específica, incluindo sementes derivadas, parâmetros ajustados, tempos medidos por subetapa e falhas (no framework: `execution_state.json`, `CellResultRecord`, `TimingBreakdown`, `PredictionRecord`).
* **Evidência Específica na Fonte:**
  * REFORMS (2024, p. eadk3452, DOI: 10.1126/sciadv.adk3452) prescreve que relatórios científicos devem separar explicitamente reivindicações do pesquisador, dados factuais observados e inferências estatísticas derivadas, estrutura que foi transcrita diretamente para a Seção 3.6 de `ARQUITETURA_E_CONTRATOS.md`.
* **Limitações da Fundamentação:**
  * A literatura adverte que a reprodutibilidade numérica exata (*bit-a-bit reproducibility*) é inviável no longo prazo através de plataformas de hardware distintas devido a operações em ponto flutuante não-associativas sob paralelismo concorrente (reduções em BLAS multithread ou operações em GPU/TPU). O framework declara formalmente essa limitação em seu ADR-007.

### 7.2. Geração Determinística de Sementes com `SeedSequence`

* **Decisões do Framework:**
  * Derivação hierárquica e determinística de sementes aleatórias para cada dobra, célula $(m, c, f)$ e busca de hiperparâmetros a partir de uma única semente mestre via `numpy.random.SeedSequence` (**ADR-007**, [M1.2 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L679); `CA-GER-02`).
* **Fundamentação Técnica:**
  * **NumPy Documentation — *Parallel and Independent Random Number Generation with SeedSequence*:** A implementação moderna do gerador PCG64 em NumPy utiliza o algoritmo `SeedSequence` para derivar fluxos estatisticamente independentes e sem colisão de estado para fluxos paralelos a partir de uma semente inteira arbitrária. Métodos legados de geração de sementes baseados em adição simples (`seed + fold_id`) introduzem correlações no espaço de estados dos geradores pseudoaleatórios, violando a independência estocástica das simulações.

---

## 8. Canonicalização, Serialização e Integridade Criptográfica

### 8.1. O Desafio da Canonicalização de Objetos Heterogêneos em Machine Learning

* **Decisões do Framework:**
  * Contrato formal de serialização canônica para hashing de configurações e metadados (`config_hash`) e de dados tabulares (`dataset_hash`) (**ADR-007**, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L199-L214)).
  * Normalização Unicode obrigatória na forma **NFC** (`unicodedata.normalize("NFC", s)`).
  * Normalização explícita de casos de contorno em ponto flutuante IEEE 754: conversão de zero negativo (`-0.0`) para positivo (`0.0`) e mapeamento determinístico de valores especiais (`NaN`, `+Inf`, `-Inf`) para tokens estruturados canônicos.
* **Fundamentação Técnica e Normativa:**
  * **NIST FIPS PUB 180-4 (2015) — *Secure Hash Standard (SHS)*:** Especifica a função de espalhamento criptográfico seguro **SHA-256**, utilizada universalmente pelo framework para geração de resumos criptográficos (*hashes*) de 256 bits (64 caracteres hexadecimais). O SHA-256 oferece resistência a colisões e resistência a pré-imagem adequadas para verificação de integridade de dados contra corrupção acidental ou alteração de estado.
  * **Unicode Consortium UAX #15 — *Unicode Normalization Forms*:** Especifica que sequências de caracteres de texto podem ser representadas em múltiplos fluxos de bytes equivalentes (ex.: `é` como caractere pré-composto U+00E9 ou como caractere base `e` U+0065 seguido do diacrítico combinante U+0301). Sem normalização canônica NFC (*Normalization Form C*), dois arquivos ou strings contendo o mesmo texto produzem bytes distintos e, consequentemente, hashes SHA-256 completamente divergentes.
  * **RFC 8785 (2020) — *JSON Canonicalization Scheme (JCS)*:** Padrão da Internet (IETF) que define a canonicalização determinística de documentos JSON para hashing e assinaturas criptográficas, prescrevendo ordenação de chaves em dicionários e supressão de espaços em branco insignificantes.
* **Análise Crítica e Justificativa de Engenharia do ADR-007:**
  * **Por que o framework não adota a RFC 8785 (JCS) de forma pura?**  
    A RFC 8785 foi concebida para o subconjunto padrão do JSON web (RFC 8259). No contexto de Machine Learning e computação científica, o JSON padrão falha em representar elementos matemáticos indispensáveis:
    1. *Valores Especiais IEEE 754:* O JSON padrão e a RFC 8785 proíbem expressamente `NaN`, `+Infinity` e `-Infinity`. Em pipelines de dados de ML, `NaN` representa valores ausentes legítimos ou métricas indefinidas.
    2. *Diferença entre Inteiro e Ponto Flutuante:* O padrão ECMAScript/JCS formata `1.0` como `1`, colapsando a distinção de tipos escalares. Em ML, diferenciar uma contagem inteira de uma probabilidade contínua é semanticamente obrigatório.
    3. *Normalização Unicode:* A RFC 8785 não impõe normalização NFC no texto original; ela exige apenas que as chaves sejam comparadas por unidades de código UTF-16.
  * Essa lacuna do padrão web justifica a decisão de engenharia documentada no **ADR-007**, que estende a canonicalização para cobrir tipos NumPy, tuplas, conjuntos e mapeamentos seguros para IEEE 754.

### 8.2. Escrita Atômica em Dois Passos e Integridade no Sistema de Arquivos

* **Decisões do Framework:**
  * Toda persistência de artefato em disco utiliza escrita segura em dois passos: gravação completa dos dados em arquivo temporário no mesmo diretório (`<nome>.tmp.<pid>`), validação de integridade e substituição via `os.replace` (`CA-GER-01`, [Seção 2.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L177)).
* **Fundamentação Técnica e Limitações:**
  * **POSIX.1-2017 (`rename(2)`) & Python Documentation (`os.replace`):** A chamada de sistema `rename(2)` garante visibilidade atômica em sistemas POSIX: o arquivo de destino nunca é observado em estado parcialmente escrito ou vazio por processos concorrentes. Se a substituição falhar, o arquivo original permanece intacto.
  * **Limitação Técnica Importante:** A atomicidade do `rename` é garantida exclusivamente quando o arquivo temporário e o destino residem no **mesmo sistema de arquivos / ponto de montagem** (motivo pelo qual o framework exige a gravação do temporário dentro do mesmo diretório do experimento). Além disso, a atomicidade de visibilidade na tabela de diretórios não é equivalente a **durabilidade física em disco** contra queda súbita de energia (o que exigiria chamadas explícitas a `fsync(2)` nos descritores de arquivo e diretório pai).

---

## 9. Verificação Formal e Máquinas de Estados

### 9.1. O Papel do Model Checking com TLA+ e TLC na Validação de Pipelines Longos

* **Decisões do Framework:**
  * Modelação formal da execução matricial como uma **máquina de estados por célula** $(m, c, f)$ transitando deterministicamente entre `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` e `CANCELLED` ([Seção 3.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L382-L393)).
  * Mecanismo de retomada verificada (*Checkpoint & Resume*) com preservação de resultados já persistidos e bloqueio de retomadas inconsistentes sob alteração de base ou configuração (`CA-E4B-02`, [Seção 3.4 de `ARQUITETURA_E_CONTRATOS.md`](./engenharia_software/ARQUITETURA_E_CONTRATOS.md#L400-L402)).
* **Fundamentação Teórica em Métodos Formais:**
  * **Lamport (2002) — *Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers*:** Apresenta a linguagem formal TLA+ (*Temporal Logic of Actions*) e o verificador explícito de modelos TLC (*Model Checker*). TLA+ permite descrever concorrentemente sistemas de estados finitos e infinitos por meio de predicados lógicos e ações sobre o estado seguinte. O model checker TLC explora exaustivamente o grafo de estados alcançáveis do sistema, verificando formalmente:
    * *Invariantes de Segurança (Safety):* "Nada de ruim acontece" (ex.: nenhuma célula `COMPLETED` é sobrescrita silenciosamente por uma retomada; nenhuma transição inválida `COMPLETED -> RUNNING` é permitida; células com erro nunca exibem métrica zero).
    * *Propriedades de Vivacidade (Liveness):* "Algo de bom eventualmente acontece" (ex.: toda célula em execução termina em um estado terminal `COMPLETED`, `FAILED` ou `CANCELLED`).
* **Desmistificação Conceitual: TLC vs. SDD (*Spec-Driven Development*):**
  * É fundamental registrar que **TLA+ e TLC são ferramentas de métodos formais e verificação de sistemas concorrentes/distribuídos**, não sendo equivalentes ao conceito ágil/processual de *Spec-Driven Development* (desenvolvimento orientado a especificações em linguagem natural ou markdown).
  * O uso de TLC no projeto aplica-se com rigor na prova formal de invariantes da máquina de estados do orquestrador (`MatrixExecutionAndResume.tla`), garantindo que condições de corrida e inconsistências de interrupção em execuções paralelas multi-core (`outer_n_jobs > 1`) sejam descartadas antes da implementação do código Python.

---

## 10. Matriz Consolidada de Fundamentação das Decisões

A tabela a seguir estabelece o mapeamento explícito entre as decisões do framework, os documentos de origem, as justificativas, as referências científicas/técnicas, a evidência encontrada e as limitações declaradas:

| Decisão Arquitetural / Metodológica | Documento de Origem | Justificativa no Projeto | Referência(s) de Suporte | Evidência Apresentada na Fonte | Limitações da Referência |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D1: Framework Agnóstico sem Implementação de Modelos Próprios** | `ARQUITETURA` L38; `SRS` L17 (ADR-001) | Permitir comparação justa e imparcial de algoritmos heterogêneos sob as mesmas partições e métricas, sem acoplamento a bibliotecas específicas. | Contexto do projeto / RNF02 (Independência de Domínio) | — | Decisão puramente contextual de escopo e desenho arquitetural; não exige validação empírica externa. |
| **D2: Imutabilidade da Base Bruta e Zero Transformação Silenciosa** | `ARQUITETURA` L39; `SRS` L18, L37 (RF1.7) | Preservar a integridade física da fonte de dados e assegurar que toda limpeza seja declarada no `PreparationPlan`. | Heil et al. (2021); REFORMS (2024) | Estudos de caso demonstram que limpezas ad-hoc silenciosas introduzem vieses e impedem auditoria independente de resultados. | As fontes estabelecem o princípio de transparência de dados, mas o contrato funcional de `DatasetProfile` e `SanitizedDatasetView` é próprio do projeto. |
| **D3: Prevenção Estrutural de Data Leakage (Fit só no Treino Externo)** | `ARQUITETURA` L40, L182 (ADR-002); `SRS` L19, L46 (RF2.4) | Eliminar o vazamento de informações da validação/teste para as etapas de imputação, padronização e seleção de atributos. | Kapoor & Narayanan (2023); scikit-learn Pitfalls; Heil et al. (2021) | Meta-pesquisa comprovando que vazamento no pré-processamento esteve presente em centenas de artigos publicados, inflando drasticamente a acurácia. | A literatura prova a existência do problema e a necessidade de isolamento; a arquitetura de duas camadas (Cenário vs. Modelo) é a resposta de software do projeto. |
| **D4: Validação Cruzada Aninhada (*Nested CV*) e Ordem Canônica Intra-Célula** | `ARQUITETURA` L185 (ADR-003), L346; `SRS` L57 (RF3.5) | Impedir viés otimista na seleção de hiperparâmetros e assegurar que a seleção de atributos dinâmica seja avaliada de forma imparcial. | Cawley & Talbot (2010); Bergstra & Bengio (2012) | Demonstração matemática e empírica de que o erro de validação usado para calibrar $\theta$ é otimista, sendo mandatória a separação entre laço interno e externo. | Cawley & Talbot tratam de regularização e hiperparâmetros; a integração da seleção dinâmica de atributos na dobra interna é extensão lógica do framework. |
| **D5: Particionamento Agrupado (`GroupKFold`) com Isolamento de Grupos** | `ARQUITETURA` L366, L372; `SRS` L64 (RF4.1); `CA-COND-PART-01` | Evitar que observações correlacionadas da mesma entidade habitem treino e teste simultaneamente, superestimando o desempenho. | Roberts et al. (2017) | Simulações demonstram que validação aleatória em dados com dependência de grupo infla artificialmente o desempenho e subestima erros reais em novas entidades. | Foco original em ecologia/autocorrelação espacial; a regra algébrica $G \ge K$ e adaptações a outros domínios são regras de contorno do projeto. |
| **D6: Proibição de Testes Paramétricos Ingênuos e Adoção do Teste $t$ Corrigido de Nadeau-Bengio** | `ARQUITETURA` L188 (ADR-004), L468; `SRS` L77 (RF5.2); `CA-E5-02` | Corrigir a subestimação da variância causada pela sobreposição de dados de treino entre dobras de validação cruzada. | Nadeau & Bengio (2003); Dietterich (1998) | Dedução teórica de que a variância é subestimada pelo fator de sobreposição, restaurando a taxa de erro Tipo I ao nível nominal $\alpha$. | O artigo assume dobras de tamanhos idênticos; o uso da razão média efetiva e o alerta para CV > 20% em folds desiguais são extensões heurísticas do projeto. |
| **D7: Emprego do Teste de Wilcoxon com Alerta Amostral para $J < 6$** | `ARQUITETURA` L189 (ADR-004); `SRS` L77 (RF5.2); `CA-E5-01` | Fornecer inferência não-paramétrica para métricas não-normais, alertando sobre a impossibilidade matemática de significância em dobras reduzidas. | Demšar (2006); dedução aritmética combinatória básica | Demšar formaliza o Wilcoxon como padrão para ML; a combinatória prova que o menor $p$-valor bicaudal para $J=5$ é $0{,}0625 > 0{,}05$. | Demšar recomenda Wilcoxon para múltiplos conjuntos de dados independentes, não para dobras de CV correlacionadas (limitação documentada no projeto). |
| **D8: Controle de Falso Positivo: Holm-Bonferroni (FWER) e Benjamini-Hochberg (FDR)** | `ARQUITETURA` L482; `SRS` L79 (RF5.4); `CA-E5-02` | Permitir controle rigoroso contra descobertas espúrias decorrentes de múltiplas comparações entre pares de modelos e cenários. | Holm (1979); Benjamini & Hochberg (1995) | Prova analítica de que Holm controla estritamente a FWER com maior poder que Bonferroni, e BH controla o FDR evitando hiperconservadorismo. | BH assume formalmente independência ou dependência positiva (PRDS) entre os testes, premissa que nem sempre se sustenta em dobras de CV. |
| **D9: Proibição de Inferir Equivalência a Partir de Não-Significância ($p \ge \alpha$)** | `ARQUITETURA` L486, L489; `SRS` L20; `CA-E5-03` | Evitar a armadilha estatística clássica de aceitar $H_0$ como prova de igualdade quando há apenas ausência de poder estatístico. | Altman & Bland (1995); princípios fundamentais de Neyman-Pearson | Artigos conceituais em medicina e bioestatística demonstrando os perigos de tratar ausência de evidência como prova de ausência de efeito. | Decisão de integridade conceitual; testes formais de equivalência (TOST) estão planejados apenas para o pós-MVP. |
| **D10: Serialização Canônica e Hashes de Integridade (SHA-256 e NFC)** | `ARQUITETURA` L199–L214 (ADR-007); `SRS` L32, L90; `CA-GER-02` | Permitir verificação de integridade bit a bit contra mutações acidentais e ancoragem de linhagem (*provenance*). | NIST FIPS 180-4; Unicode UAX #15; RFC 8785 (JCS) | Padrões normativos que definem o algoritmo SHA-256, equivalência canônica de strings e ordenação determinística de propriedades. | A RFC 8785 não suporta NaN/Inf nem diferencia 1 de 1.0; o framework desenvolve especificação canônica própria extensível para NumPy. |
| **D11: Hashes como Metadados Internos Ocultos ao Usuário Final** | `ARQUITETURA` L211–L213 (ADR-007); `SRS` L90 (RF6.4); `CA-E6-02` | Evitar confusão visual e poluição técnica em tabelas científicas e relatórios acadêmicos, mantendo os hashes em arquivos de auditoria. | Decisão contextual de usabilidade e diretriz do orientador | — | Decisão orientada à ergonomia de uso e pedagogia (RNF07); sem necessidade de bibliografia externa. |
| **D12: Persistência Atômica via Escrita Segura em Dois Passos** | `ARQUITETURA` L177, L401; `CA-GER-01` | Garantir que interrupções e quedas de processo não deixem artefatos JSON ou Parquet truncados ou ilegíveis em disco. | POSIX.1-2017 (`rename(2)`); Python Documentation (`os.replace`) | Especificação normativa POSIX comprovando que `rename` garante atomicidade de visibilidade no mesmo sistema de arquivos. | A atomicidade do ponteiro de diretório não garante durabilidade em disco físico sem chamadas síncronas de gravação (`fsync`). |
| **D13: Rastreabilidade por Proveniência Retrospectiva (`ArtifactProvenance`)** | `ARQUITETURA` L557–L565; `SRS` L89 (RF6.3); `CA-E6-02` | Permitir que qualquer figura ou tabela exportada seja vinculada sem ambiguidade aos dados, partições e células geradoras. | Freire et al. (2008); Heil et al. (2021) | Artigos seminais de proveniência em computação científica definindo ontologias de grafos de linhagem retrospectiva para auditoria. | O framework implementa manifesto próprio em JSON em vez de adotar ontologias pesadas e complexas (como W3C PROV-O). |
| **D14: Desacoplamento entre Apresentação, Análise e Execução (Níveis 1–3 de Reprodução)** | `ARQUITETURA` L42, L495, L611–L615; `SRS` L21, L87; `CA-E6-01` | Possibilitar reestilização de tabelas/figuras ou reanálise estatística sem impor o custo computacional de retreinar modelos. | Freire et al. (2008); Peng (2011) | Obras de referência em ciência computacional demonstrando as vantagens de armazenar artefatos intermediários tipados em disco. | O desacoplamento exige armazenamento em disco de predições completas por observação, demandando formatos eficientes (Parquet). |
| **D15: Verificação Formal da Máquina de Estados Matricial via TLA+/TLC** | `ARQUITETURA` L383–L393; Planejamento de Verificação | Provar matematicamente ausência de deadlocks, corridas e corrupção de estado no orquestrador antes do código Python. | Lamport (2002) — *Specifying Systems* | Model checker TLC explora exaustivamente o grafo de estados atingíveis, provando invariantes de segurança e vivacidade. | Modela o comportamento abstrato do protocolo; não detecta bugs de implementação direta no interpretador Python ou drivers de disco. |

---

## 11. Lacunas Bibliográficas e Decisões Justificadas por Engenharia

Nem toda decisão em um projeto de software científico possui ou exige respaldo em artigos acadêmicos. A auditoria identificou decisões que constituem **escolhas legítimas de engenharia de software** ou **heurísticas internas** que devem ser compreendidas como tal, sem necessidade de citações artificiais:

1. **Limiar Heurístico de Coeficiente de Variação (CV > 20%) para Tamanho de Folds (ADR-004):**  
   * *Status:* Decisão pragmática do projeto. Não há artigo científico que prescreva a fronteira exata de 20% para a variação de tamanho de dobras no teste de Nadeau-Bengio. A justificativa técnica apoia-se no fato de que distorções extremas na razão $n_{\text{val}} / n_{\text{train}}$ desequilibram os pesos de cada dobra na fórmula original. Deve ser declarada no código como parâmetro de configuração com justificativa geométrica, e não como teorema formal.
2. **Formato e Estrutura dos Arquivos de Pacote (`manifest.json`, `dataset_profile.json`, etc.):**  
   * *Status:* Decisão de desenho de software fundamentada no princípio de portabilidade e formatos abertos (JSON e Parquet). Dispensa referências bibliográficas além das especificações dos formatos de arquivo.
3. **Códigos de Saída da CLI (`0`, `1`, `2`):**  
   * *Status:* Convenção de engenharia e usabilidade em sistemas operacionais Unix-like, baseada no comportamento do módulo `argparse` do Python e utilitários de shell.
4. **Tolerâncias Numéricas por Família (`rtol` e `atol` da Seção 7.2 de `ARQUITETURA_E_CONTRATOS.md`):**  
   * *Status:* Derivação matemática e computacional baseada na precisão de máquina da aritmética IEEE 754 de dupla precisão (`float64`, $\varepsilon \approx 2{,}22 \times 10^{-16}$). A sustentação dessa decisão não decorre de artigos de revisão, mas de asserções em testes unitários automatizados contra valores conhecidos calculados analiticamente e implementações canônicas de referência da biblioteca `scipy.stats`.

---

## 12. Referências Bibliográficas Completas

Abaixo estão listadas todas as referências bibliográficas, normativas e técnicas que fundamentam a concepção do framework, organizadas em ordem alfabética segundo a norma ABNT NBR 6023:2018 (com padrão compatível IEEE e inclusão de links persistentes e identificadores DOI):

1. **ALTMAN, Douglas G.; BLAND, J. Martin.** Statistics notes: Absence of evidence is not evidence of absence. *BMJ*, v. 311, n. 7003, p. 485, 1995. DOI: [10.1136/bmj.311.7003.485](https://doi.org/10.1136/bmj.311.7003.485).
2. **BENJAMINI, Yoav; HOCHBERG, Yosef.** Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing. *Journal of the Royal Statistical Society: Series B (Methodological)*, v. 57, n. 1, p. 289–300, 1995. DOI: [10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x).
3. **BERGSTRA, James; BENGIO, Yoshua.** Random Search for Hyper-Parameter Optimization. *Journal of Machine Learning Research*, v. 13, n. 10, p. 281–305, 2012. URL: [https://jmlr.org/papers/v13/bergstra12a.html](https://jmlr.org/papers/v13/bergstra12a.html).
4. **CAWLEY, Gavin C.; TALBOT, Nicola L. C.** On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. *Journal of Machine Learning Research*, v. 11, n. 70, p. 2079–2107, 2010. URL: [https://jmlr.org/papers/v11/cawley10a.html](https://jmlr.org/papers/v11/cawley10a.html).
5. **DEMŠAR, Janez.** Statistical Comparisons of Classifiers over Multiple Data Sets. *Journal of Machine Learning Research*, v. 7, n. 1, p. 1–30, 2006. URL: [https://jmlr.org/papers/v7/demsar06a.html](https://jmlr.org/papers/v7/demsar06a.html).
6. **DIETTERICH, Thomas G.** Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms. *Neural Computation*, v. 10, n. 7, p. 1895–1923, 1998. DOI: [10.1162/089976698300017197](https://doi.org/10.1162/089976698300017197).
7. **FREIRE, Juliana; KOOP, David; SANTOS, Emanuele; SILVA, Cláudio T.** Provenance for Computational Tasks: A Survey. *Computing in Science & Engineering*, v. 10, n. 3, p. 11–21, 2008. DOI: [10.1109/MCSE.2008.79](https://doi.org/10.1109/MCSE.2008.79).
8. **HEIL, Benjamin J. et al.** Reproducibility standards for machine learning in the life sciences. *Nature Methods*, v. 18, n. 10, p. 1132–1135, 2021. DOI: [10.1038/s41592-021-01256-7](https://doi.org/10.1038/s41592-021-01256-7).
9. **HOLM, Sture.** A Simple Sequentially Rejective Multiple Test Procedure. *Scandinavian Journal of Statistics*, v. 6, n. 2, p. 65–70, 1979. URL: [https://www.jstor.org/stable/4615733](https://www.jstor.org/stable/4615733).
10. **KAPOOR, Sayash; NARAYANAN, Arvind.** Leakage and the reproducibility crisis in machine-learning-based science. *Patterns*, v. 4, n. 9, p. 100804, 2023. DOI: [10.1016/j.patter.2023.100804](https://doi.org/10.1016/j.patter.2023.100804).
11. **KAPOOR, Sayash et al.** REFORMS: Consensus-based Recommendations for Machine-learning-based Science. *Science Advances*, v. 10, n. 18, p. eadk3452, 2024. DOI: [10.1126/sciadv.adk3452](https://doi.org/10.1126/sciadv.adk3452).
12. **LAMPORT, Leslie.** *Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers*. Boston: Addison-Wesley, 2002. ISBN: 0-321-14306-X. URL: [https://lamport.azurewebsites.net/tla/book.html](https://lamport.azurewebsites.net/tla/book.html).
13. **NADEAU, Claude; BENGIO, Yoshua.** Inference for the Generalization Error. *Machine Learning*, v. 52, n. 3, p. 239–281, 2003. DOI: [10.1023/A:1024068626366](https://doi.org/10.1023/A:1024068626366).
14. **NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST).** *Secure Hash Standard (SHS)*. Federal Information Processing Standards Publication (FIPS PUB) 180-4, Gaithersburg: NIST, 2015. DOI: [10.6028/NIST.FIPS.180-4](https://doi.org/10.6028/NIST.FIPS.180-4).
15. **PARNAS, David L.** On the Criteria To Be Used in Decomposing Systems into Modules. *Communications of the ACM*, v. 15, n. 12, p. 1053–1058, 1972. DOI: [10.1145/361598.361623](https://doi.org/10.1145/361598.361623).
16. **PENG, Roger D.** Reproducible Research in Computational Science. *Science*, v. 334, n. 6060, p. 1226–1227, 2011. DOI: [10.1126/science.1213847](https://doi.org/10.1126/science.1213847).
17. **ROBERTS, David R. et al.** Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, v. 40, n. 8, p. 913–929, 2017. DOI: [10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881).
18. **RUNDGREN, Anders; BACON, Grant; WEST, Mike.** *JSON Canonicalization Scheme (JCS)*. Request for Comments (RFC) 8785, Internet Engineering Task Force (IETF), 2020. DOI: [10.17487/RFC8785](https://doi.org/10.17487/RFC8785).
19. **SCIKIT-LEARN DEVELOPERS.** *Common pitfalls and recommended practices*. scikit-learn documentation, 2024. URL: [https://scikit-learn.org/stable/common_pitfalls.html](https://scikit-learn.org/stable/common_pitfalls.html).
20. **UNICODE CONSORTIUM.** *Unicode Standard Annex #15: Unicode Normalization Forms*. UAX #15, Version 15.1.0, 2023. URL: [https://www.unicode.org/reports/tr15/](https://www.unicode.org/reports/tr15/).

