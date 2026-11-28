# M11.3 — Caracterização Estatística Ampliada dos Datasets e `dataset_meta_features`

- **Status**: Approved (`AD-039`, `AD-040`, `XCUT-02`) — Fase TLC: **Specify**
**Approved**: 2026-11-28 - user: "aprovado"
- **Milestone**: `M11.3` (`m11-3-dataset-characterization`)
- **Branch**: `feat/m11-3-dataset-characterization`
- **Related Validation Finding**: `VAL-ENH-007`

---

## Problem Statement

O perfilamento (`data/profiling.py`) e a exploração de atributos (`features/stats.py`, `features/exploration.py`) ainda não calculam momentos de forma (`skewness`, excesso de `kurtosis` de Fisher, `outlier_rate_iqr`), nem métricas estruturais opt-in como razão amostras/atributos ($n/p$), dimensionalidade intrínseca via SVD, entropia normalizada do alvo, VIF, *Distance Correlation* e indicador exploratório de linearidade, além de não exportarem um bloco padronizado `dataset_meta_features` para futura análise *cross-experiment* na Onda 2.

---

## Architectural Decision (`AD-039`, `AD-040`, `XCUT-02`)

- **Núcleo em NumPy puro (`XCUT-02`):** Todas as métricas estatísticas permanecem em Python + NumPy puro sem dependência de `scipy`.
- **Métricas leves vs. opt-in (`AD-040`):** `skewness`, excesso de `kurtosis` (Fisher) e `outlier_rate_iqr` são calculados no perfil básico de `NumericDistributionStats`. Métricas estruturais pesadas (`VIF`, *Distance Correlation*, `intrinsic_dim_ratio_95` via SVD $\ge 95\%$ em matriz padronizada, `linearity_score` via OLS $R^2$ em regressão e Ridge/LDA NumPy em classificação, `samples_to_features_ratio` e `target_entropy_norm`) e a exportação de `dataset_meta_features.json` + tabela no relatório são estritamente **opt-in (`False` por padrão)** via `extended_stats: bool = False` e `export_meta_features: bool = False`.
- **Sem *data leakage* (`XCUT-01`):** Toda caracterização ampliada permanece estritamente rotulada em `EXPLORATORY_FULL_DATA` e nunca dispara seleção automática pré-split.

---

## Requirements (EARS Notation)

### M113-01 — Momentos Leves e Perfil Estrutural Opt-In (`data/profiling.py`)
- **WHEN** `compute_numeric_distribution_stats` processa valores numéricos válidos, **THE SYSTEM SHALL** calcular `skewness`, excesso de `kurtosis` (Fisher) e `outlier_rate_iqr` em NumPy puro (retornando `None` quando $n < 3$, $n < 4$ ou variância zero para momentos). **WHEN** `profile_dataset` recebe `extended_stats=True`, **THE SYSTEM SHALL** preencher `samples_to_features_ratio`, `intrinsic_dim_ratio_95` e `target_entropy_norm` em `DatasetProfile` (mantendo `None` quando `extended_stats=False`).

### M113-02 — VIF, *Distance Correlation* e Linearidade Exploratória (`features/stats.py`, `features/exploration.py`)
- **WHEN** `extended_stats=True` é informado a `explore_features` (ou os helpers em `features/stats.py` são chamados diretamente), **THE SYSTEM SHALL** calcular em NumPy puro `compute_vif` (via `np.linalg.pinv`), `compute_distance_correlation` (Székely et al., 2007) e `compute_linearity_score` (OLS $R^2$ para regressão; acurácia balanceada Ridge/LDA NumPy para classificação) sob `scope='EXPLORATORY_FULL_DATA'`, sem alterar `SanitizedDatasetView`.

### M113-03 — Exportação Opt-In de `dataset_meta_features` e Relatório (`reporting/`, `pipeline.py`)
- **WHEN** `run_experiment(..., export_meta_features=True)` é executado, **THE SYSTEM SHALL** persistir `dataset_meta_features.json` no diretório do experimento, carregá-lo em `LoadedExperimentData` e renderizar a tabela `Caracterização Estatística Ampliada (Meta-Features)` em `report.md` e `report.html` em `pt-BR`. **WHEN** `export_meta_features=False` e `extended_stats=False`, **THE SYSTEM SHALL** preservar custo zero sem gravar `dataset_meta_features.json` nem exibir a seção no relatório.

---

## Out of Scope
- Motor de *Meta-Learning / Algorithm Selection* multi-dataset (Onda 2).
- Ajuste MLE iterativo multi-distribuição para $P(Y)$ (Onda 2).
- Seleção automática de atributos pré-split baseada em VIF ou *Distance Correlation* (`XCUT-01`).

---

## User Stories

1. **Como pesquisador**, quero que `NumericDistributionStats` informe assimetria, curtose e taxa de *outliers* IQR, e quero poder ativar explicitamente (`extended_stats=True`, `export_meta_features=True`) o cálculo de VIF, *Distance Correlation*, SVD, linearidade e a exportação de `dataset_meta_features.json` + tabela no relatório para compreender a complexidade estrutural do meu dataset.

---

## Assumptions & Open Questions

### Assumptions
- Para SVD (`intrinsic_dim_ratio_95`), `VIF` e `linearity_score` exploratórios, colunas numéricas constantes são ignoradas e eventuais `NaN` são imputados localmente pela média apenas dentro do cálculo exploratório, sem modificar `SanitizedDatasetView`.
- Documentação em `docs/guia/03_interpretando_resultados.md` explica quando ativar `extended_stats=True` e `export_meta_features=True`.

### Open Questions
Open questions: none (`AD-040` deliberada pelo desenvolvedor em 2026-11-28).

---

## Requirement Traceability

| Requisito | Origem | Critério de Verificação |
| :--- | :--- | :--- |
| M113-01 | `VAL-ENH-007`, `AD-040` | `C1`: `NumericDistributionStats` calcula momentos leves e `profile_dataset(extended_stats=True)` preenche indicadores SVD/razão/entropia |
| M113-02 | `VAL-ENH-007`, `XCUT-02` | `C2`: `compute_vif`, `compute_distance_correlation` e `compute_linearity_score` em NumPy puro integram `explore_features(extended_stats=True)` |
| M113-03 | `VAL-ENH-007`, `AD-040` | `C3`: `run_experiment(export_meta_features=True)` grava `dataset_meta_features.json` e exibe tabela `pt-BR` no relatório sem efeitos quando `False` |
