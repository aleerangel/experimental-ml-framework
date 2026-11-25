# Roteiro de Aceite — Marco M8: Estabilização do MVP e Alinhamento Contratual

- **Marco:** `M8` (`m8-mvp-stabilization-contract-alignment`)
- **Status do Marco:** Planejado (Fase TLC: **Specify** — aguardando aprovação da `spec.md` pelo desenvolvedor antes de iniciar Design/Tasks/Execute)

---

## 1. Pré-requisitos

Este roteiro deverá ser executado pelo desenvolvedor **após** a aprovação da `spec.md`, implementação das tarefas do Marco `M8` e emissão de `verification.md: PASS` pelo Verificador Independente.

## 2. Passos de Validação pelo Consumidor (CLI e API Python)

### Passo 1 — Verificar Tabelas A e G e Comparações em Classificação via `expml init` + `quickrun`

```bash
rm -rf /tmp/m8_aceite_clf
.venv/bin/expml init --experiment-dir /tmp/m8_aceite_clf --task binary_classification
.venv/bin/expml quickrun --experiment-dir /tmp/m8_aceite_clf
.venv/bin/expml report export --experiment-dir /tmp/m8_aceite_clf
```

**O que inspecionar:**
1. O arquivo `/tmp/m8_aceite_clf/reports/tables/tbl_family_a.md` deve conter as linhas de caracterização do dataset (`n_rows`, `n_cols`, `memory_bytes`, etc.) e **não** a mensagem `"No data available"`.
2. O arquivo `/tmp/m8_aceite_clf/statistics/paired_comparisons.json` deve conter pelo menos 1 comparação pareada entre os 2 modelos gerados no template de classificação.

### Passo 2 — Verificar Interoperabilidade `run_experiment` (Python) → `expml` (CLI) e Diagnósticos da Tabela G

Executar um experimento via `run_experiment` com `RandomForestRegressor` e cenário dinâmico `TOP_K_RELEVANCE` salvando em `/tmp/m8_aceite_py` e, em seguida, validar via CLI:

```bash
.venv/bin/expml partition verify --experiment-dir /tmp/m8_aceite_py
.venv/bin/expml run verify --experiment-dir /tmp/m8_aceite_py
.venv/bin/expml report export --experiment-dir /tmp/m8_aceite_py
```

**O que inspecionar:**
1. Todos os comandos CLI acima devem terminar com código de saída `0`.
2. `/tmp/m8_aceite_py/reports/tables/tbl_family_g.md` deve listar os diagnósticos extraídos dos modelos ajustados nas células (`feature_importances`, `coefficients`, etc.).
3. `/tmp/m8_aceite_py/statistics/descriptive_metrics.json` deve apresentar `mean_kuncheva` preenchido com valor numérico (ex.: `1.0` quando a seleção de $k < N$ atributos é estável entre folds).
