# M11.4 — Fechamento Onda 1: Pareto/Planned Pairs em `run_experiment`, Cache Nested CV / `ProcessPoolExecutor` e Sincronização Documental

- **Status**: Approved (`VAL-ENH-004`, `VAL-QUAL-004`, Categoria 5) — Fase TLC: **Specify**
**Approved**: 2026-11-28 - user: "aprovado"
- **Milestone**: `M11.4` (`m11-4-wave1-polish`)
- **Branch**: `feat/m11-4-wave1-polish`
- **Related Validation Findings**: `VAL-ENH-004`, `VAL-QUAL-004`

---

## Problem Statement

1. **`VAL-ENH-004`:** A CLI (`cmd_stats.py`) já suporta `pareto_objectives` e `planned_pairs` em `stats_config.json`, mas a fachada Python `run_experiment` em `pipeline.py` ainda fixa `ComparisonScope.ALL_PAIRWISE` e 2 objetivos rígidos de Pareto (`primary_metric` + `fit_mean_s`).
2. **Desempenho (Categoria 5):** No Nested CV (`tuning/engine.py`), cada candidato de hiperparâmetro recalcula o pré-processamento e a seleção dinâmica sobre os mesmos sub-folds internos; e `orchestration/engine.py` suporta apenas `ThreadPoolExecutor`, limitando estimadores em Python puro presos ao GIL.
3. **`VAL-QUAL-004`:** `docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md` e `docs/referencia/api_python.md` ainda contêm divergências pontuais de nomenclatura e símbolos omitidos pós-`M8`–`M11.3`.

---

## Requirements (EARS Notation)

### M114-01 — Pareto Customizável e `PLANNED_PAIRS` em `run_experiment` (`VAL-ENH-004`)
- **WHEN** `run_experiment` recebe `comparison_scope`, `planned_pairs` ou `pareto_objectives` explícitos, **THE SYSTEM SHALL** repassá-los para `ComparisonSpec` e `MultiObjectiveSpec` exatamente como na CLI, preservando `ALL_PAIRWISE` e `(primary_metric, fit_mean_s)` como padrão quando omitidos.

### M114-02 — Cache Intra-Célula no Nested CV e `ProcessPoolExecutor` Opt-In (Categoria 5)
- **WHEN** `execute_nested_cv` avalia múltiplos candidatos de hiperparâmetros sobre o mesmo sub-fold interno, **THE SYSTEM SHALL** cachear `(X_in_train_trans, X_in_val_trans)` por `inner_fold_idx`, evitando recomputar Camada 1, seleção dinâmica e Camada 2 sem alterar os valores numéricos.
- **WHEN** `run_experiment_matrix` ou `resume_experiment_matrix` recebe `execution_backend="process"` (padrão `"thread"`) com `outer_n_jobs > 1`, **THE SYSTEM SHALL** executar as células independentes via `ProcessPoolExecutor` mantendo a mesma persistência em disco.

### M114-03 — Sincronização Documental (`VAL-QUAL-004`)
- **THE SYSTEM SHALL** alinhar `docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md` (códigos de achados, enums de particionamento, artefatos JSON em disco) e `docs/referencia/api_python.md` (símbolos públicos de `M8`–`M11.3`), atualizando `VAL-ENH-004` e `VAL-QUAL-004` em `REGISTRO_DE_VALIDACAO_DO_MVP.md`.

---

## Out of Scope
- Novos recursos da Onda 2 (Friedman/Nemenyi, Meta-Learning, Predição Conforme, QML).

---

## User Stories

1. **Como pesquisador**, quero passar `comparison_scope=ComparisonScope.PLANNED_PAIRS`, `planned_pairs` e `pareto_objectives` diretamente para `run_experiment`, ter Nested CV mais rápido sem recalcular pré-processamento por candidato e poder optar por `execution_backend="process"`, além de consultar documentação 100% alinhada ao código.

---

## Assumptions & Open Questions

### Assumptions
- Para `ProcessPoolExecutor`, as funções/fábricas de estimadores passadas pelo usuário precisam ser serializáveis via `pickle` (funções de módulo ou classes importáveis), mantendo `"thread"` como padrão seguro para lambdas/funções locais.

### Open Questions
Open questions: none (escopo solicitado diretamente pelo usuário em 2026-11-28).

---

## Requirement Traceability

| Requisito | Origem | Critério de Verificação |
| :--- | :--- | :--- |
| M114-01 | `VAL-ENH-004` | `C1`: `run_experiment` respeita `comparison_scope`, `planned_pairs` e `pareto_objectives` customizados |
| M114-02 | Categoria 5 | `C2`: Cache intra-célula no Nested CV reduz chamadas de pré-processamento/seleção com resultado idêntico e `execution_backend="process"` executa via `ProcessPoolExecutor` |
| M114-03 | `VAL-QUAL-004` | `C3`: `ARQUITETURA_E_CONTRATOS.md`, `api_python.md` e `REGISTRO_DE_VALIDACAO_DO_MVP.md` sincronizados sem regressão na suíte |
