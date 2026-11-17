# Documentação do Pesquisador — `experimental-ml`

Bem-vindo ao portal oficial de documentação do **Experimental ML Framework (`experimental-ml`)**, um framework científico em Python puro e NumPy projetado para experimentos rigorosos, reprodutíveis e livres de *data leakage* (vazamento de dados).

---

## Trilha de Aprendizado em 4 Níveis

A documentação foi organizada progressivamente do uso imediato até a referência técnica exaustiva:

1. **Nível 1 — Início Rápido (`5 passos`)**: [Início Rápido](guia/01_inicio_rapido.md)  
   Execute seu primeiro experimento completo em minutos utilizando comandos CLI de uma linha ou um script Python autocontido.
2. **Nível 2 — Tutorial Metodológico (`6 Etapas Oficiais`)**: [Tutorial Passo a Passo das 6 Etapas](guia/02_tutorial_6_etapas.md)  
   Compreenda a fundamentação matemática, os portões de estágio (*stage gates*) e os invariantes anti-vazamento desde a ingestão tabular até o pacote de reprodutibilidade.
3. **Nível 3 — Guias Práticos (`9 Cenários Avançados`)**:  
   Protocolos prontos para cenários experimentais exigentes:
   - [Guia Prático 1: Modelos Analíticos/Biométricos (`requires_fit=False`) vs. Modelos Treinados](guias_praticos/01_modelos_analiticos_vs_treinados.md)
   - [Guia Prático 2: Métricas Quânticas (`KTA`) e Probabilísticas (`ROC-AUC`, `Log-Loss`)](guias_praticos/02_metricas_quanticas_e_probabilisticas.md)
   - [Guia Prático 3: Validação Cruzada Agrupada (`GroupKFold`) com Isolamento Estrito de Holdout](guias_praticos/03_validacao_cruzada_agrupada_holdout.md)
   - [Guia Prático 4: Otimização Multiobjetivo na Fronteira de Pareto](guias_praticos/04_otimizacao_pareto_multiobjetivo.md)
   - [Guia Prático 5: Pacotes Herméticos de Reprodutibilidade e Auditoria SHA-256 para Conferências](guias_praticos/05_pacotes_reprodutibilidade_conferencias.md)
   - [Guia Prático 6: Variações do Mesmo Algoritmo — Ablação de LS-SVM em Prognose Florestal](guias_praticos/06_ablacao_variantes_algoritmo_lssvm.md)
   - [Guia Prático 7: Cenários de Features Fixos vs. Dinâmicos e Estabilidade](guias_praticos/07_cenarios_features_estabilidade.md)
   - [Guia Prático 8: Fluxo Desacoplado para Jupyter Notebooks e Relatórios sem Retreino](guias_praticos/08_fluxo_desacoplado_jupyter_relatorios.md)
   - [Guia Prático 9: Inferência Estatística na Prática (Nadeau-Bengio, Wilcoxon e Multiplicidade)](guias_praticos/09_inferencia_estatistica_na_pratica.md)
4. **Nível 4 — Catálogos de Referência Técnica**:
   - [Referência da API Python Pública](referencia/api_python.md) (11 pacotes públicos)
   - [Catálogo Completo da CLI `expml`](referencia/cli_catalogo.md) (comandos, opções e códigos de saída)
5. **Notebooks Interativos (`notebooks/`)**:
   - [01 — Tour pelas 6 Etapas](../notebooks/01_tour_6_etapas.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/01_tour_6_etapas.ipynb)
   - [02 — Ablação LS-SVM em Prognose Florestal](../notebooks/02_ablacao_lssvm_prognose_florestal.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/02_ablacao_lssvm_prognose_florestal.ipynb)
   - [03 — Validação Agrupada e Bloqueios Anti-Vazamento](../notebooks/03_validacao_agrupada_e_prevencao_leakage.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/03_validacao_agrupada_e_prevencao_leakage.ipynb)
   - [04 — Pós-Experimento Somente-Leitura (LaTeX, SVG e Pacote)](../notebooks/04_pos_experimento_relatorios_artigo.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aleerangel/experimental-ml-framework/blob/main/notebooks/04_pos_experimento_relatorios_artigo.ipynb)

---

## Documentação Complementar de Engenharia

- [Arquitetura e Contratos Técnicos](engenharia_software/ARQUITETURA_E_CONTRATOS.md)
- [Especificação de Requisitos](engenharia_software/ESPECIFICACAO_REQUISITOS.md)
- [Fundamentação Teórica e Referências Bibliográficas](REFERENCIAS_E_FUNDAMENTACAO.md)
- [Página Principal do Repositório](../README.md)
