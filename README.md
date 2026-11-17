# Experimental ML Framework (`experimental-ml`)

![Python](https://img.shields.io/badge/Python-%3E%3D3.10-blue)
![NumPy](https://img.shields.io/badge/Runtime-Pure%20Python%20%2B%20NumPy-green)
![Version](https://img.shields.io/badge/Version-0.1.0.dev0-informational)
![Status](https://img.shields.io/badge/MVP-Auditado%20%26%20Congelado-brightgreen)

Framework científico agnóstico para condução, auditoria e publicação de experimentos em Aprendizado de Máquina (*Machine Learning* — ML) sobre dados tabulares. Projetado em Python padrão e NumPy (`XCUT-02`), garante prevenção estrutural contra *data leakage*, isolamento determinístico de partições, tolerância a falhas, inferência estatística pareada rigorosa (Nadeau-Bengio / Wilcoxon) e empacotamento portátil de reprodutibilidade.

---

## Instalação

```bash
pip install -e .
```

---

## Fluxo Básico via CLI (`expml`)

Execute todo o pipeline científico das **6 etapas** diretamente pelo terminal:

```bash
expml data profile --input dados.csv --target alvo --task binary_classification --output-dir exp_dir
expml data sanitize --exp-dir exp_dir --allow-unresolved
expml features scenarios --exp-dir exp_dir --scenarios-json cenarios.json
expml models validate --exp-dir exp_dir --models-json modelos.json
expml partition build --exp-dir exp_dir --strategy stratified_kfold --n-splits 5 --seed 42
expml run start --exp-dir exp_dir --metrics accuracy f1
expml stats run --exp-dir exp_dir --primary-metric accuracy
expml report export --exp-dir exp_dir --mode FULL_PACKAGE --output-dir pacote_final
```

---

## Mapa de Documentação

| Área | Documento | Conteúdo Principal |
| :--- | :--- | :--- |
| **Guia do Pesquisador** | [Portal de Documentação](docs/README.md) | Índice unificador e trilha de aprendizado em 4 níveis |
| **Início Rápido** | [Início Rápido (5 Passos)](docs/guia/01_inicio_rapido.md) | Instalação, fluxo CLI mínimo e exemplo Python executável |
| **Tutorial Completo** | [Tutorial das 6 Etapas](docs/guia/02_tutorial_6_etapas.md) | Metodologia detalhada, invariantes anti-leakage e portões |
| **Scientific Cookbook** | [Modelos Analíticos vs. Treinados](docs/cookbook/01_modelos_analiticos_vs_treinados.md) | Uso de `requires_fit=False` e isolamento por dobra |
| **Scientific Cookbook** | [Métricas Quânticas e Probabilísticas](docs/cookbook/02_metricas_quanticas_e_probabilisticas.md) | Kernels pré-computados (`KTA`), `ROC-AUC` e `Log-Loss` |
| **Scientific Cookbook** | [Validação Agrupada e Holdout](docs/cookbook/03_validacao_cruzada_agrupada_holdout.md) | `GroupKFold` com isolamento estrito em `CV_AND_HOLDOUT` |
| **Scientific Cookbook** | [Otimização Pareto Multiobjetivo](docs/cookbook/04_otimizacao_pareto_multiobjetivo.md) | Fronteira de Pareto entre métrica, latência e estabilidade |
| **Scientific Cookbook** | [Pacotes para Conferências](docs/cookbook/05_pacotes_reprodutibilidade_conferencias.md) | Modos `FULL_PACKAGE`/`REDUCED_NO_RAW_DATA` e SHA-256 |
| **Referência Técnica** | [API Python Pública](docs/referencia/api_python.md) | Catálogo dos 11 pacotes públicos exportados |
| **Referência Técnica** | [Catálogo da CLI `expml`](docs/referencia/cli_catalogo.md) | Comandos, opções e códigos de saída (`0`, `1`, `2`) |
| **Engenharia** | [Arquitetura e Contratos](engenharia_software/ARQUITETURA_E_CONTRATOS.md) | Camadas, contratos formais, portões e plano de marcos |
| **Engenharia** | [Especificação de Requisitos](engenharia_software/ESPECIFICACAO_REQUISITOS.md) | Requisitos funcionais, não funcionais e critérios de aceite |
| **Engenharia** | [Estado Atual de Engenharia](engenharia_software/ETAPA_ATUAL_ENGENHARIA.md) | Registro do estágio atual de evolução do projeto |
| **Engenharia** | [Processo de Aceite de Marcos](engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md) | Governança de homologação e auditoria independente |
| **Fundamentação** | [Referências e Fundamentação](REFERENCIAS_E_FUNDAMENTACAO.md) | Base bibliográfica, decisões arquiteturais (ADRs) e estatística |
