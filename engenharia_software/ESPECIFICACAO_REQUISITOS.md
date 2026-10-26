# Especificação de Requisitos de Software (SRS) — `experimental-ml-framework`

> **Documento:** Documento de Especificação de Requisitos  
> **Versão:** 1.0.0  
> **Data:** 26 de Outubro de 2026  
> **Status:** Aprovado e Consolidado na Fase 2  

---

## 1. Visão Geral e Propósito

### 1.1 Objetivo do Produto
O `experimental-ml-framework` é um **harness científico agnóstico e pedagógico** desenvolvido para democratizar a experimentação científica rigorosa em Machine Learning. Ele atua como um guia metodológico para estudantes de Iniciação Científica (IC), pós-graduandos e pesquisadores, protegendo-os ativamente contra falhas metodológicas comuns (como vazamento de dados e testes estatísticos inapropriados) e automatizando a geração de artefatos de publicação científica.

### 1.2 Persona do Usuário
* **Perfil:** Estudantes de Iniciação Científica e pesquisadores de diversas áreas aplicadas (ex.: ciências agrárias, biológicas, exatas e engenharias) que precisam aplicar Machine Learning com rigor metodológico, mesmo sem background profundo prévio em engenharia de software de ML.
* **Forma de Interação:**
  * Scripts Python puros, expressivos e fluentes com baixa barreira de entrada (`import experimental_ml ...`).
  * Jupyter Notebooks guiados com explicações passo a passo de cada etapa experimental.

### 1.3 Limites do Escopo
* **Dentro do Escopo:**
  * Ingestão e validação estrutural de dados tabulares.
  * Suporte a problemas de **Regressão** e **Classificação** (binária e multiclasse).
  * Gestão e comparação declarativa de cenários de atributos (*Feature Scenarios*).
  * Validação cruzada estrita (incluindo dados hierárquicos/agrupados).
  * Busca e auxílio na otimização de hiperparâmetros (Grid Search / Random Search sem vazamento).
  * Orquestração matricial: $\text{Modelos} \times \text{Cenários} \times \text{Folds}$.
  * Inferência estatística formal (Nadeau-Bengio, Wilcoxon, Holm-Bonferroni, Benjamini-Hochberg) com relatórios em linguagem natural e matrizes numéricas.
  * Exportação de artefatos prontos para publicação científica (tabelas LaTeX/Markdown e gráficos).
  * Execução 100% autossuficiente e offline, com paralelismo multi-core local.
* **Fora do Escopo:**
  * Modelos de ML embutidos no framework (o framework é estritamente o *harness*).
  * Deploy em produção, servidores de inferência, APIs REST, Docker de serving e microsserviços.
  * Plataformas de tracking em nuvem obrigatórias (W&B, Neptune, etc.).

---

## 2. Requisitos Funcionais (RF)

### Módulo: Dados e Ingestão (`data`)
* **RF01:** Suportar ingestão de datasets tabulares a partir de arquivos `.csv`, `.txt` (com detecção flexível de separadores: vírgula, ponto-e-vírgula, tabulação e espaço) e objetos `pandas.DataFrame`.
* **RF02:** Permitir a definição explícita de: coluna(s) alvo (*target*), identificadores de grupo/cluster (*group_id*), e colunas proibidas/metadados (*ignore_cols*).
* **RF03:** Validar integridade estrutural básica: detecção de valores nulos no alvo, colunas de variância zero (constantes) e tipos de dados incompatíveis.
* **RF04 (Alerta Pedagógico):** Emitir avisos visíveis no terminal e registrá-los no relatório final caso detecte estruturas de agrupamento ou riscos metodológicos, sem abortar forçadamente a execução do usuário.

### Módulo: Engenharia e Cenários de Atributos (`features`)
* **RF05:** Calcular correlações lineares e monotônicas (Pearson, Spearman) entre variáveis preditoras e a variável resposta.
* **RF06:** Avaliar dependências não lineares via Informação Mútua (compatível com alvos contínuos para regressão e discretos para classificação).
* **RF07:** Detectar multicolinearidade excessiva entre preditores ($|r| \ge \text{limiar}$) e sugerir descarte de atributos redundantes.
* **RF08:** Gerenciar cenários declarativos de atributos (`ScenarioManager`): registrar, nomear, documentar e versionar conjuntos distintos de features para comparação experimental.

### Módulo: Particionamento e Validação Cruzada (`validation`)
* **RF09:** Suportar estratégias de particionamento robustas: K-Fold padrão, StratifiedKFold, GroupKFold, StratifiedGroupKFold, GroupShuffleSplit e TimeSeriesSplit.
* **RF10:** Garantir a asserção matemática obrigatória de *Zero Data Leakage* (interseção nula de grupos/instâncias entre conjuntos de treino e teste em cada fold).
* **RF11:** Executar pré-processamento (normalização, imputação, padronização) estritamente dentro de cada fold de treino, aplicando a transformação resultante no conjunto de teste.

### Módulo: Modelos e Otimização (`models` / `tuning`)
* **RF12 (Contrato Agnóstico):** Aceitar qualquer modelo externo (Scikit-Learn, PyTorch, XGBoost, Qiskit, PennyLane, equações matemáticas proprietárias) via contrato unificado:
  * `fit(X, y)`
  * `predict(X) -> ndarray`
  * `predict_proba(X) -> ndarray` (opcional para classificação, com *fallback* automático).
* **RF13:** Fornecer módulo de auxílio na busca de hiperparâmetros (Grid Search / Random Search) que opere de forma aninhada (*nested cross-validation*) garantindo ausência de vazamento de dados.

### Módulo: Orquestração e Benchmark (`benchmark`)
* **RF14:** Orquestrar de forma automatizada a execução da matriz experimental:
  $$\text{Modelos} \times \text{Cenários de Features} \times \text{Folds}$$
* **RF15:** Suportar execução concorrente em múltiplos núcleos de processamento (`n_jobs`) de forma nativa e segura.

### Módulo: Métricas de Avaliação (`metrics`)
* **RF16 (Regressão):** Calcular métricas de regressão pontuais e out-of-fold: $R^2$, RMSE, RMSE relativo (%), MAE, MAPE, correlação de Pearson e Viés Médio (*Mean Bias Error*).
* **RF17 (Classificação):** Calcular métricas de classificação pontuais e out-of-fold: Acurácia, Acurácia Balanceada, Precisão, Revocação (Recall), F1-Score (macro/weighted), AUC-ROC e Log-Loss (quando probabilidades estiverem disponíveis).

### Módulo: Inferência Estatística Rigorosa (`statistics`)
* **RF18:** Aplicar o teste t corrigido de **Nadeau & Bengio (2003)** para corrigir a subestimação da variância causada pela dependência dos folds na validação cruzada:
  $$\sigma^2_{NB} = \sigma^2 \left( \frac{1}{J} + \frac{n_{\text{teste}}}{n_{\text{treino}}} \right)$$
* **RF19:** Aplicar o teste pareado de **Wilcoxon** com emissão de alerta metodológico formal de poder estatístico quando $J \le 5$.
* **RF20:** Aplicar procedimentos de controle de erro tipo I para comparações múltiplas: **Holm-Bonferroni** (FWER) e **Benjamini-Hochberg** (FDR).
* **RF21 (Interpretação Dupla):** Produzir simultaneamente:
  1. Matrizes numéricas formais ($p$-valores originais e ajustados, matriz de vitórias/empates/derrotas).
  2. Síntese textual em linguagem natural com a interpretação formal dos testes de hipóteses estatísticas (pronta para a seção de Resultados e Discussão de artigos científicos).

### Módulo: Relatórios e Publicação (`reporting`)
* **RF22:** Gerar tabelas formatadas em múltiplos formatos científicos: console rico, CSV, Markdown e LaTeX (`table` com convenções `booktabs`).
* **RF23:** Gerar e salvar gráficos científicos em alta resolução (300 DPI) para regressão, classificação e diagnósticos estatísticos.
* **RF24:** Organizar todos os artefatos de saída em diretório estruturado e versionado por execução (`experiments/run_<timestamp>/`).

---

## 3. Requisitos Não Funcionais (RNF)

* **RNF01 (Determinismo e Reprodutibilidade):** Todas as rotinas que utilizem amostragem ou permutações devem receber semente pseudoaleatória controlada (`random_state`).
* **RNF02 (Independência de Domínio):** Zero referências hardcoded a variáveis florestais ou de qualquer domínio específico no núcleo do framework.
* **RNF03 (Autossuficiência 100% Offline):** O framework deve ser completamente funcional sem acesso à internet ou dependência de serviços externos em nuvem.
* **RNF04 (Eficiência e Vetorização):** Cálculos numéricos e métricas implementados de forma estritamente vetorizada com NumPy e SciPy, banindo laços `for` interpretados no cálculo matricial.
* **RNF05 (Testabilidade e Qualidade):** Cobertura de testes unitários automatizados com `pytest` cobrindo todas as formulações matemáticas e testes de hipóteses.
* **RNF06 (Compatibilidade):** Suporte nativo a ambientes Python $\ge 3.10$.
* **RNF07 (Ergonomia Pedagógica):** Nomes de classes e métodos transparentes e legíveis; mensagens de alerta no terminal estruturadas de forma didática e explicativa.

---

## 4. Critério de Aceitação Inicial (Ground Truth)

* **CA01:** O framework deve ser capaz de reproduzir os experimentos originais de referência da pesquisa `prognose_florestal` (com algoritmos clássicos, métricas $R^2$, RMSE, MAE e testes estatísticos) de forma agnóstica, com código declarativo reduzido e paridade matemática exata dos resultados validados.
