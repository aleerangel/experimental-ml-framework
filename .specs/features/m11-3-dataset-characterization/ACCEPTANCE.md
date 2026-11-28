# Roteiro de Aceite do Consumidor — Submarco M11.3 (`VAL-ENH-007`)

- **Submarco:** `M11.3` (`m11-3-dataset-characterization`)
- **Branch:** `feat/m11-3-dataset-characterization`
- **Critério:** Validação pelo pesquisador usando exclusivamente interfaces públicas (`run_experiment` e artefatos/relatórios gerados).

---

## 1. Pré-requisitos
- Ambiente virtual `.venv` com dependências instaladas (`pip install -e ".[dev]"`).

## 2. Passos de Validação
1. **Comportamento padrão (opt-in desativado):**
   - Executar `run_experiment(..., output_dir=...)` sem `extended_stats=True` nem `export_meta_features=True`.
   - Confirmar que `dataset_profile.json` já registra `skewness`, `kurtosis` e `outlier_rate_iqr` em `numeric_stats`, mas não gera `dataset_meta_features.json` nem exibe a tabela de Meta-Features no relatório.
2. **Ativação explícita (`export_meta_features=True`):**
   - Executar `run_experiment(..., export_meta_features=True)`.
   - Confirmar a criação de `dataset_meta_features.json` na raiz do experimento (`scope: "EXPLORATORY_FULL_DATA"`) com `samples_to_features_ratio`, `intrinsic_dim_ratio_95`, `max_vif`, `mean_vif`, `mean_distance_correlation_target` e `linearity_score`, além da tabela `Caracterização Estatística Ampliada (Meta-Features)` em `report.md` e `report.html`.

## 3. Critério de Aprovação
- [ ] Passos 1 e 2 validados sem execução pesada oculta e sem alteração do particionamento ou métricas `DEV_CV`.
