# Schemas JSON da CLI `expml` (Jornada 2)

Ao utilizar os comandos granulares da CLI (`expml data`, `features`, `models`, `partition`, `stats`), você pode gerar todos os arquivos automaticamente com `expml init --output-dir <pasta>` e apenas editá-los. Abaixo está a especificação exata de cada arquivo JSON.

---

## 1. `schema.json` (Usado por `expml data profile`)

```json
{
  "target_col": "alvo",
  "task_type": "REGRESSION",
  "group_col": null,
  "time_col": null,
  "ignore_cols": []
}
```
- `task_type`: `"REGRESSION"`, `"BINARY_CLASSIFICATION"` ou `"MULTICLASS_CLASSIFICATION"`.

---

## 2. `rules.json` (Opcional em `expml data sanitize`)

Se não houver achados críticos no diagnóstico, você pode omitir `--rules` ou passar uma lista vazia `[]`. Quando houver regras:
```json
[
  {
    "finding_code": "MISSING_TARGET",
    "column": "alvo",
    "kind": "DROP_ROWS",
    "parameters": {}
  }
]
```

---

## 3. `scenarios.json` (Usado por `expml features scenarios`)

```json
[
  {
    "scenario_id": "todas_features",
    "name": "Todas as Features",
    "description": "Conjunto completo de variáveis preditoras",
    "scientific_justification": "Cenário inicial sem seleção",
    "mode": "FIXED",
    "selected_features": ["x1", "x2"]
  }
]
```
- `mode`: `"FIXED"` (usa `selected_features`) ou `"DYNAMIC"` (usa `strategy_name`, ex.: `"TOP_K_RELEVANCE"` ou `"VARIANCE_THRESHOLD"`, e `strategy_params`).

---

## 4. `models.json` (Usado por `expml models validate`)

```json
[
  {
    "model_id": "baseline_media",
    "display_name": "Baseline Média",
    "family": "BASELINE",
    "estimator_factory": "DUMMY_BASELINE_MEAN",
    "parameters": {"strategy": "mean"},
    "capabilities": {"requires_fit": true},
    "description": "Preditor pela média",
    "scientific_justification": "Referência mínima"
  }
]
```
- **`estimator_factory`** aceita:
  - Identificadores embutidos: `"DUMMY_BASELINE_MEAN"`, `"DUMMY_BASELINE_MEDIAN"`, `"DUMMY_BASELINE_MOST_FREQUENT"`, `"ANALYTICAL_BIOMETRIC"`.
  - Caminho Python importável no formato `"modulo:ClasseOuFabrica"` (ex.: `"meu_pacote.modelos:MeuRegressor"`).

---

## 5. `partition.json` (Usado por `expml partition build`)

```json
{
  "strategy": "KFOLD",
  "regime": "CV_ONLY",
  "n_splits": 5,
  "master_seed": 42
}
```
- `strategy`: `"KFOLD"`, `"STRATIFIED_KFOLD"`, `"GROUP_KFOLD"`, `"TEMPORAL"`, `"HOLDOUT"`.
- `regime`: `"CV_ONLY"`, `"HOLDOUT_ONLY"`, `"CV_AND_HOLDOUT"`.

---

## 6. `stats_config.json` (Opcional em `expml stats run`)

```json
{
  "metrics_of_interest": ["rmse"],
  "metric_directions": {"rmse": "MINIMIZE"},
  "comparison_scope": "ALL_PAIRWISE",
  "alpha": 0.05
}
```
