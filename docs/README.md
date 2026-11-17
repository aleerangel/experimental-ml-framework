# Documentação do Pesquisador — `experimental-ml`

Bem-vindo ao portal oficial do **Experimental ML Framework (`experimental-ml`)**, um framework científico em Python puro e NumPy projetado para democratizar experimentos rigorosos, reprodutíveis e livres de *data leakage* (vazamento de dados).

---

## Navegação por Jornadas de Utilização

### Jornada 1 — Primeiro Experimento (Começando do Zero)
- **[Começando do Zero (10 Linhas em Python ou 2 Comandos CLI)](guia/00_comecando_do_zero.md)** — Para quem só sabe o básico de ML (sem experiência prévia com frameworks, JSON ou terminal).
- **[Início Rápido (5 Passos)](guia/01_inicio_rapido.md)** — Fluxo operacional completo com script executável.
- **[Notebook 01: Tour pelas 6 Etapas](../notebooks/01_tour_6_etapas.ipynb)** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/01_tour_6_etapas.ipynb)

### Jornada 2 — Construindo Experimentos
- **[Tutorial Passo a Passo das 6 Etapas](guia/02_tutorial_6_etapas.md)** — Preparação, features, modelos, particionamento, execução, estatística e relatórios.
- **[Schemas JSON da CLI `expml`](referencia/cli_schemas_json.md)** — Modelos exatos dos arquivos `schema.json`, `rules.json`, `scenarios.json`, `models.json`, `partition.json` e `stats_config.json`.
- **[Catálogo Completo da CLI `expml`](referencia/cli_catalogo.md)** — Todos os comandos, opções e códigos de saída (`0`, `1`, `2`).
- **[Guia Prático 3: Validação Cruzada Agrupada (`GroupKFold`) e Holdout](guias_praticos/03_validacao_cruzada_agrupada_holdout.md)**
- **[Notebook 03: Validação Agrupada e Bloqueios Anti-Vazamento](../notebooks/03_validacao_agrupada_e_prevencao_leakage.ipynb)** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/03_validacao_agrupada_e_prevencao_leakage.ipynb)

### Jornada 3 — Interpretando Resultados Científicos
- **[Guia Prático de Interpretação de Resultados](guia/03_interpretando_resultados.md)** — Como ler métricas (`RMSE`, `MBE`, `ROC-AUC`), cobertura, Nadeau-Bengio/Wilcoxon, Cohen's $d$, Pareto e não-equivalência ($p \ge \alpha$).
- **[Guia Prático 9: Inferência Estatística na Prática](guias_praticos/09_inferencia_estatistica_na_pratica.md)**
- **[Notebook 04: Pós-Experimento Somente-Leitura (LaTeX, SVG e Pacote)](../notebooks/04_pos_experimento_relatorios_artigo.ipynb)** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/04_pos_experimento_relatorios_artigo.ipynb)

### Jornada 4 — Recursos Avançados
- **[Referência da API Python Pública](referencia/api_python.md)** — Os 11 pacotes públicos exportados.
- **Guias Práticos Especializados:**
  - [Guia Prático 1: Modelos Analíticos (`requires_fit=False`) vs. Treinados](guias_praticos/01_modelos_analiticos_vs_treinados.md)
  - [Guia Prático 2: Métricas Quânticas (`KTA`) e Probabilísticas (`ROC-AUC`, `Log-Loss`)](guias_praticos/02_metricas_quanticas_e_probabilisticas.md)
  - [Guia Prático 4: Otimização Multiobjetivo na Fronteira de Pareto](guias_praticos/04_otimizacao_pareto_multiobjetivo.md)
  - [Guia Prático 5: Pacotes Herméticos e Auditoria SHA-256 para Conferências](guias_praticos/05_pacotes_reprodutibilidade_conferencias.md)
  - [Guia Prático 6: Variações do Mesmo Algoritmo — Ablação LS-SVM em Prognose Florestal](guias_praticos/06_ablacao_variantes_algoritmo_lssvm.md)
  - [Guia Prático 7: Cenários de Features Fixos vs. Dinâmicos e Estabilidade](guias_praticos/07_cenarios_features_estabilidade.md)
  - [Guia Prático 8: Fluxo Desacoplado para Jupyter Notebooks e Relatórios sem Retreino](guias_praticos/08_fluxo_desacoplado_jupyter_relatorios.md)
- **[Notebook 02: Ablação LS-SVM em Prognose Florestal](../notebooks/02_ablacao_lssvm_prognose_florestal.ipynb)** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/02_ablacao_lssvm_prognose_florestal.ipynb)

### Jornada 5 — Desenvolvimento e Engenharia Interna
- [Arquitetura e Contratos Técnicos](engenharia_software/ARQUITETURA_E_CONTRATOS.md)
- [Especificação de Requisitos](engenharia_software/ESPECIFICACAO_REQUISITOS.md)
- [Estado Atual de Engenharia](engenharia_software/ETAPA_ATUAL_ENGENHARIA.md)
- [Processo de Aceite de Marcos](engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md)
- [Fundamentação Teórica e Referências Bibliográficas](REFERENCIAS_E_FUNDAMENTACAO.md)
- [Página Principal do Repositório](../README.md)
