# Documentação do Pesquisador — `experimental-ml`

Bem-vindo ao portal oficial do **Experimental ML Framework (`experimental-ml`)**, um framework científico em Python puro e NumPy projetado para democratizar experimentos rigorosos, reprodutíveis e livres de *data leakage* (vazamento de dados).

---

## Por Onde Começar?

| Seu Objetivo Agora | Nível | Onde Ir |
| :--- | :---: | :--- |
| Tenho um `.csv` e quero rodar modelos em 10 linhas (sem JSON nem terminal complexo) | **Básico** | [Começando do Zero](guia/00_comecando_do_zero.md) ou [Notebook 01](../notebooks/01_primeiro_experimento_do_zero.ipynb) |
| Já rodei o básico e quero entender quando usar o controle granular | **Intermediário** | [Início Rápido: Básico vs. Granular](guia/01_inicio_rapido.md) |
| Quero estruturar um estudo completo (TCC, IC ou artigo) com rigor nas 6 etapas | **Intermediário / Avançado** | [Tutorial das 6 Etapas](guia/02_tutorial_6_etapas.md) e [Interpretando Resultados](guia/03_interpretando_resultados.md) |
| Preciso de casos especiais (`GroupKFold`, LS-SVM/kernels quânticos, Pareto, LaTeX) | **Avançado** | [Guias Práticos (`01..09`)](#jornada-4--recursos-avançados) |
| Sou colaborador de código / mantenedor do framework | **Desenvolvedor** | [Engenharia e Arquitetura](#jornada-5--desenvolvimento-e-engenharia-interna) |

---

## Navegação por Jornadas de Utilização

### Jornada 1 — Primeiro Experimento
- `[Básico]` **[Começando do Zero](guia/00_comecando_do_zero.md)** — Preparação do ambiente (Colab/`venv`), formato de `.csv`, 10 linhas em Python (`run_experiment`) e alternativa CLI em 2 comandos (`expml init` + `expml quickrun`).
- `[Básico]` **[Notebook 01: Primeiro Experimento do Zero](../notebooks/01_primeiro_experimento_do_zero.ipynb)** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/01_primeiro_experimento_do_zero.ipynb)
- `[Básico]` **[Notebook 02: Classificação e Grupos na Prática](../notebooks/02_classificacao_e_grupos_na_pratica.ipynb)** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/02_classificacao_e_grupos_na_pratica.ipynb)
- `[Intermediário]` **[Início Rápido: Básico vs. Controle Granular](guia/01_inicio_rapido.md)** — Quando sair do modo básico para o modo granular e exemplo completo em Python.

### Jornada 2 — Construindo Experimentos
- `[Intermediário]` **[Tutorial Passo a Passo das 6 Etapas](guia/02_tutorial_6_etapas.md)** — O mínimo obrigatório vs. opções avançadas em cada uma das 6 etapas.
- `[Intermediário]` **[Notebook 03: Tour Completo pelas 6 Etapas](../notebooks/03_tour_6_etapas.ipynb)** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/03_tour_6_etapas.ipynb)
- `[Avançado]` **[Schemas JSON da CLI `expml`](referencia/cli_schemas_json.md)** — Modelos exatos para uso granular pela linha de comando.
- `[Avançado]` **[Catálogo Completo da CLI `expml`](referencia/cli_catalogo.md)** — Todos os comandos, opções e códigos de saída (`0`, `1`, `2`).
- `[Avançado]` **[Guia Prático 3: Validação Cruzada Agrupada (`GroupKFold`) e Holdout](guias_praticos/03_validacao_cruzada_agrupada_holdout.md)** *(veja também o [Notebook 02](../notebooks/02_classificacao_e_grupos_na_pratica.ipynb))*

### Jornada 3 — Interpretando Resultados Científicos
- `[Básico → Avançado]` **[Interpretando Resultados Científicos](guia/03_interpretando_resultados.md)** — Leitura básica de métricas + guia estatístico completo com citações bibliográficas para artigos e TCCs.
- `[Avançado]` **[Guia Prático 9: Inferência Estatística na Prática](guias_praticos/09_inferencia_estatistica_na_pratica.md)** *(exemplos visuais de saída no [Notebook 04](../notebooks/04_avancado_variantes_lssvm_prognose_florestal.ipynb))*

### Jornada 4 — Recursos Avançados
- `[Avançado]` **[Referência da API Python Pública](referencia/api_python.md)** — Os 11 pacotes públicos exportados.
- `[Avançado]` **[Guia Prático 1: Modelos Analíticos (`requires_fit=False`) vs. Treinados](guias_praticos/01_modelos_analiticos_vs_treinados.md)**
- `[Avançado]` **[Guia Prático 2: Métricas Quânticas (`KTA`) e Probabilísticas (`ROC-AUC`, `Log-Loss`)](guias_praticos/02_metricas_quanticas_e_probabilisticas.md)**
- `[Avançado]` **[Guia Prático 4: Otimização Multiobjetivo na Fronteira de Pareto](guias_praticos/04_otimizacao_pareto_multiobjetivo.md)**
- `[Avançado]` **[Guia Prático 5: Pacotes Herméticos e Auditoria SHA-256 para Conferências](guias_praticos/05_pacotes_reprodutibilidade_conferencias.md)**
- `[Avançado]` **[Guia Prático 6: Variações do Mesmo Algoritmo — LS-SVM em Prognose Florestal](guias_praticos/06_ablacao_variantes_algoritmo_lssvm.md)**
- `[Avançado]` **[Guia Prático 7: Cenários de Features Fixos vs. Dinâmicos e Estabilidade](guias_praticos/07_cenarios_features_estabilidade.md)**
- `[Avançado]` **[Guia Prático 8: Fluxo Desacoplado para Jupyter Notebooks e Relatórios sem Retreino](guias_praticos/08_fluxo_desacoplado_jupyter_relatorios.md)**
- `[Avançado]` **[Notebook 04: Vitrine Avançada — Variantes do LS-SVM em Prognose Florestal](../notebooks/04_avancado_variantes_lssvm_prognose_florestal.ipynb)** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/04_avancado_variantes_lssvm_prognose_florestal.ipynb)

### Jornada 5 — Desenvolvimento e Engenharia Interna
- [Arquitetura e Contratos Técnicos](engenharia_software/ARQUITETURA_E_CONTRATOS.md)
- [Especificação de Requisitos](engenharia_software/ESPECIFICACAO_REQUISITOS.md)
- [Estado Atual de Engenharia](engenharia_software/ETAPA_ATUAL_ENGENHARIA.md)
- [Processo de Aceite de Marcos](engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md)
- [Fundamentação Teórica e Referências Bibliográficas](REFERENCIAS_E_FUNDAMENTACAO.md)
- [Página Principal do Repositório](../README.md)
