# M8 — Estabilização do MVP e Alinhamento Contratual Tasks

**Spec**: `.specs/features/m8-mvp-stabilization-contract-alignment/spec.md`
**Design**: `.specs/features/m8-mvp-stabilization-contract-alignment/design.md`
**Status**: Approved
**Approved**: 2026-11-26 - user: "concordo"

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `pyproject.toml`, `docs/engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Domain / Algorithms (`features/stats.py`, `tuning/`, `models/`) | unit | 1:1 para critérios `AC-M8-02`, `AC-M8-03`, `AC-M8-06` + edge cases | `tests/unit/**/*.py` | `.venv/bin/pytest tests/unit/ -q` |
| Orchestration / Reporting (`reporting/`, `orchestration/`, `pipeline.py`) | unit + integration | Cobertura de `AC-M8-01`, `AC-M8-04`, `AC-M8-05`, `AC-M8-07` | `tests/unit/**/*.py`, `tests/integration/*.py` | `.venv/bin/pytest tests/ -q` |
| CLI (`cli/cmd_stats.py`, `cli/cmd_init.py`) | unit + integration | Flags, códigos de saída `0`/`1`/`2` e interoperabilidade | `tests/unit/cli/*.py`, `tests/integration/*.py` | `.venv/bin/pytest tests/ -q` |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | Após tarefas unitárias isoladas | `.venv/bin/pytest tests/unit/ -q` |
| Full | Após tarefas com impacto em integração ou CLI | `.venv/bin/pytest tests/ -q` |
| Build | Ao concluir todas as tarefas | `.venv/bin/pytest tests/ -v` |

**Build**: `.venv/bin/pytest tests/ -q`

---

## Execution Plan

### Phase 1 — Correções Independentes (`T1`, `T2`, `T3`, `T7`)
```
T1 (Tabelas A/G)
T2 (Categóricas None)
T3 (cell_<m>__<s>__<f>.json + hashes resume + lock) --> T4 (Nested CV ADR-003)
T3 --> T5 (run_experiment)
T5 --> T6 (Kuncheva + Pareto CLI)
T7 (expml init classificação + validate_verification.py)
```

### Phase 2 — Alinhamento Intra-Fold, Fachada e CLI (`T4`, `T5`, `T6`)
- Executar `T4` e `T5` após `T3`, e `T6` após `T5`.

---

## Task Breakdown

### T1: Corrigir extração da Tabela A (`dataset_profile["summary"]`) e carregar diagnósticos de células para Tabela G (`reporting/loader.py`, `reporting/tables.py`)
- [x] Implement & test T1
**Where**: `src/experimental_ml/reporting/loader.py`, `src/experimental_ml/reporting/tables.py`, `tests/unit/test_reporting_tables.py`
**Depends on**: none
**Tests**: Testes unitários para `tbl_family_a` com estrutura aninhada `"summary"` (preservando retrocompatibilidade plana) e `tbl_family_g` com diagnósticos carregados de `runs/cells/*.json`.
**Gate**: `.venv/bin/pytest tests/unit/test_reporting_tables.py -v`

### T2: Filtrar `None` e `NaN` pairwise em colunas categóricas de `compute_correlation_ratio` e `compute_cramers_v` (`features/stats.py`)
- [x] Implement & test T2
**Where**: `src/experimental_ml/features/stats.py`, `tests/unit/features/test_stats.py`
**Depends on**: none
**Tests**: Testes unitários com arrays `dtype=object` contendo `None` e `np.nan` misturados com strings em `compute_correlation_ratio` e `compute_cramers_v`.
**Gate**: `.venv/bin/pytest tests/unit/features/test_stats.py -v`

### T3: Normalizar gravação/leitura de células para `cell_<m>__<s>__<f>.json` sem fallback legado (`AD-029` / `D2`), adicionar `scenarios_hash`/`models_hash` em `MatrixExecutionState` e proteger `_ACTIVE_INSTANCES` com `threading.Lock` (`orchestration/`, `models/execution.py`)
- [x] Implement & test T3
**Where**: `src/experimental_ml/orchestration/storage.py`, `src/experimental_ml/orchestration/state.py`, `src/experimental_ml/orchestration/engine.py`, `src/experimental_ml/stages/stage_gates.py`, `src/experimental_ml/models/execution.py`, `tests/unit/orchestration/test_cell_codecs.py`, `tests/unit/orchestration/test_matrix_resume.py`
**Depends on**: none
**Tests**: Testes de nomenclatura única `cell_<m>__<s>__<f>.json` (sem `cell_cell_`), rejeição de retomada com alteração de `scenarios_hash`/`models_hash` e segurança concorrente de `_ACTIVE_INSTANCES`.
**Gate**: `.venv/bin/pytest tests/ -q`

### T4: Alinhar seleção dinâmica intra-subfold e Camada 1 no Nested CV ao `ADR-003` (`AD-028` / `D1`) e propagar estratificação, agrupamento e temporalidade para `split_inner_folds`
- [ ] Implement & test T4
**Where**: `src/experimental_ml/tuning/partitioning.py`, `src/experimental_ml/tuning/engine.py`, `src/experimental_ml/orchestration/execution.py`, `tests/unit/test_tuning_engine.py`
**Depends on**: T3
**Tests**: Teste metodológico provando que `select_features_in_fold` no Nested CV não acessa `y_in_val`, teste de refit no fold externo completo e testes de estratificação/grupos/ordem em `split_inner_folds`.
**Gate**: `.venv/bin/pytest tests/ -q`

### T5: Garantir paridade completa de artefatos em disco e propagação de `seed` para instâncias clonadas na fachada `run_experiment` (`pipeline.py`)
- [ ] Implement & test T5
**Where**: `src/experimental_ml/pipeline.py`, `tests/unit/test_pipeline_facade.py`
**Depends on**: T3
**Tests**: Teste de integração executando `run_experiment` seguido de `expml partition verify`, `expml run verify`, `expml stats compute` e `expml report export`, além de determinismo com instância `RandomForestRegressor()` sem `random_state` pré-definido.
**Gate**: `.venv/bin/pytest tests/ -q`

### T6: Passar `n_total_candidates_per_config` para `consolidate_descriptive` em `cmd_stats.py` e `pipeline.py`, e ler `"pareto_objectives"` múltiplos em `cmd_stats.py`
- [ ] Implement & test T6
**Where**: `src/experimental_ml/cli/cmd_stats.py`, `src/experimental_ml/pipeline.py`, `tests/unit/cli/test_cli_stats.py`
**Depends on**: T5
**Tests**: Teste verificando `mean_kuncheva == 1.0` (não `None`) quando $0 < k < N_{\text{total}}$ via CLI e fachada, e Pareto com 2 objetivos via `stats_config.json`.
**Gate**: `.venv/bin/pytest tests/ -q`

### T7: Incluir segundo modelo default nos templates de classificação de `expml init` (`cli/cmd_init.py`) e corrigir o caminho de `PROCESSO_DE_ACEITE_DE_MARCOS.md` em `validate_verification.py`
- [ ] Implement & test T7
**Where**: `src/experimental_ml/cli/cmd_init.py`, `.agent/skills/tlc-spec-driven/scripts/validate_verification.py`, `.agents/skills/tlc-spec-driven/scripts/validate_verification.py`, `tests/unit/test_usability_cli_and_facade.py`
**Depends on**: none
**Tests**: Teste executando `expml init --task binary_classification` + `expml quickrun` verificando `>= 1` comparação pareada e teste do script `validate_verification.py`.
**Gate**: `.venv/bin/pytest tests/ -q`

---

## Checks

**Run m8_unit**: `.venv/bin/pytest tests/unit/reporting/test_reporting_tables.py tests/unit/features/test_stats.py tests/unit/orchestration/test_cell_codecs.py tests/unit/orchestration/test_matrix_resume.py tests/unit/tuning/test_tuning_execution.py -v`
**Run m8_e2e**: `.venv/bin/pytest tests/integration/ -v`

**C1** - `tbl_family_a` e `tbl_family_g` contêm linhas reais a partir de `dataset_profile.json` e `runs/cells/*.json` (`M8-01`, `M8-02`, `AC-M8-01`)
Proof: run m8_unit | test_family_a_and_g_populated_from_real_artifacts PASSED

**C2** - `compute_correlation_ratio` e `compute_cramers_v` não lançam `TypeError` quando entradas categóricas possuem `None` (`M8-03`, `AC-M8-02`)
Proof: run m8_unit | test_categorical_stats_ignore_none_values PASSED

**C3** - `select_features_in_fold` no Nested CV não acessa `y_in_val` dos folds internos durante a busca de hiperparâmetros (`M8-04`, `AC-M8-03`)
Proof: run m8_unit | test_nested_tuning_dynamic_selection_isolated_per_inner_fold PASSED

**C4** - Diretório gerado por `run_experiment` passa em `expml partition verify`, `expml run verify` e `expml report export`, e propaga `seed` em instâncias (`M8-05`, `AC-M8-04`)
Proof: run m8_e2e | test_run_experiment_cli_interoperability_and_seed_propagation PASSED

**C5** - `mean_kuncheva` é numérico ($\neq \text{None}$) quando $k < N_{\text{candidatos}}$ via CLI/fachada (`M8-06`, `AC-M8-05`)
Proof: run m8_e2e | test_cli_stats_kuncheva_and_multiobjective_pareto PASSED

**C6** - `resume=True` rejeita alteração em `scenarios.json` ou `models.json` via `scenarios_hash`/`models_hash` (`M8-07`, `AC-M8-06`)
Proof: run m8_unit | test_resume_rejects_modified_scenarios_or_models_hash PASSED

**C7** - Artefatos de célula gravados e lidos exclusivamente como `runs/cells/cell_<m>__<s>__<f>.json` sem fallback `cell_cell_` (`M8-07`, `AC-M8-07`)
Proof: run m8_unit | test_canonical_cell_filename_without_legacy_prefix PASSED

---

## Handoff

- **Feature**: `m8-mvp-stabilization-contract-alignment`
- **Phase / Task**: `Design` e `Tasks` elaborados; aguardando aprovação das tarefas (`tasks.md`) pelo desenvolvedor antes de iniciar `T1`.
- **In-progress**: none
- **Next step**: Aprovação de `tasks.md` pelo desenvolvedor para iniciar `Execute` (`T1`–`T7`).
