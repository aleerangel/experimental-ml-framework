# m5-3-oof-consolidation-stage-gate Tasks (M5.3 Consolidação OOF e Portão de Estágio da Etapa 4)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m5-3-oof-consolidation-stage-gate/design.md`  
**Status**: Approved  
**Approved**: 2026-11-12 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/orchestration/ tests/unit/stages/ -v  
**Run integration**: .venv/bin/pytest tests/integration/orchestration/ -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| OOF Data Model & Storage (`src/experimental_ml/orchestration/oof.py`) | unit | 1:1 AC mapping: ConsolidatedOofPredictions immutability, to/from dict codecs, atomic save/load oof JSON | `tests/unit/orchestration/test_oof_storage.py` | `.venv/bin/pytest tests/unit/orchestration/test_oof_storage.py -v` |
| OOF Prediction Aggregation (`src/experimental_ml/orchestration/oof.py`) | unit | 1:1 AC mapping: observation_id sorting, single-fold preservation, multi-fold committee statistics, probability pooling, residuals | `tests/unit/orchestration/test_oof_aggregation.py` | `.venv/bin/pytest tests/unit/orchestration/test_oof_aggregation.py -v` |
| OOF Metrics Evaluation (`src/experimental_ml/orchestration/oof.py`) | unit | 1:1 AC mapping: POOLED_OOF task metrics, FOLD_AGGREGATION statistics via aggregate_fold_metrics, UNDEFINED_NAN resilience | `tests/unit/orchestration/test_oof_metrics.py` | `.venv/bin/pytest tests/unit/orchestration/test_oof_metrics.py -v` |
| Fault Tolerance & Partial Coverage (`src/experimental_ml/orchestration/oof.py`) | unit | 1:1 AC mapping: PARTIAL_COVERAGE status, missing observation warnings, 100% failure rejection | `tests/unit/orchestration/test_oof_fault_tolerance.py` | `.venv/bin/pytest tests/unit/orchestration/test_oof_fault_tolerance.py -v` |
| Stage Gate Etapa 4 (`src/experimental_ml/stages/stage_gates.py`) | unit | 1:1 AC mapping: upstream gates, execution_state validation, terminal statuses, physical artifact verification, cross-hashes consistency | `tests/unit/stages/test_stage_runs_gate.py` | `.venv/bin/pytest tests/unit/stages/test_stage_runs_gate.py -v` |
| Transversal Integration (`tests/integration/orchestration/test_oof_integration.py`) | integration | Public API exports, full matrix execution to OOF consolidation and verify_runs_gate, runtime purity (XCUT-02) | `tests/integration/orchestration/test_oof_integration.py` | `.venv/bin/pytest tests/integration/orchestration/test_oof_integration.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After tasks with unit tests in orchestration or stages | `.venv/bin/pytest tests/unit/orchestration/ tests/unit/stages/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Modelagem e Persistência de Predições OOF (`P1`)

Implementar a estrutura declarativa `ConsolidatedOofPredictions`, codecs lossless e persistência atômica sob `{run_dir}/oof/`.

```
T1
```

### Phase 2: Agregação Canônica e Comitê Out-of-Fold (`P2`)

Implementar `consolidate_oof_predictions` com ordenação canônica por `observation_id`, estimativa de comitê ($\hat{\mu}_i, \hat{\sigma}_i$), resíduos e probabilidades médias.

```
T1 --> T2
```

### Phase 3: Avaliação de Métricas Agrupadas e Agregações Inter-Folds (`P3`)

Implementar o cálculo de métricas com escopo `POOLED_OOF` e agregações inter-folds com escopo `FOLD_AGGREGATION`.

```
T2 --> T3
```

### Phase 4: Cobertura Parcial e Tolerância a Falhas (`P4`)

Implementar suporte a dobras faltantes em `FAULT_TOLERANT` com `PARTIAL_COVERAGE`, registro de observações ausentes e bloqueio de falha total.

```
T3 --> T4
```

### Phase 5: Portão de Estágio da Etapa 4 (`verify_runs_gate`) (`P5`)

Implementar o validador formal `verify_runs_gate` em `src/experimental_ml/stages/stage_gates.py`.

```
T1 --> T5
T4 --> T5
```

### Phase 6: Integração Transversal e API Pública (`P6`)

Expor APIs públicas em `orchestration` e `stages`, conectar consolidação ao ciclo matricial e implementar suíte de integração de ponta a ponta.

```
T5 --> T6
```

---

## Task Breakdown

### Phase 1: Modelagem e Persistência de Predições OOF

#### T1: Implementar ConsolidatedOofPredictions, Codecs e Persistência Atômica

**What**: Criar `src/experimental_ml/orchestration/oof.py` definindo a estrutura declarativa imutável `ConsolidatedOofPredictions` com validações de coerência vetorial e tipos em `__post_init__`. Implementar os codecs `oof_predictions_to_dict` e `oof_predictions_from_dict` garantindo fidelidade de tipos primitiva. Implementar as funções `save_oof_predictions` e `load_oof_predictions` para persistir atomicamente sob `{run_dir}/oof/oof_{model_id}__{scenario_id}.json` utilizando `write_json_atomic`. Criar testes unitários em `tests/unit/orchestration/test_oof_storage.py`.
**Where**: `src/experimental_ml/orchestration/oof.py`
**Depends on**: None
**Reuses**: `src/experimental_ml/orchestration/types.py`, `src/experimental_ml/core/storage.py`, `src/experimental_ml/metrics/types.py`
**Requirement**: ORCH-20

**Done when**:
- [x] `ConsolidatedOofPredictions` definido com frozen dataclass e slots
- [x] Codecs `oof_predictions_to_dict` e `oof_predictions_from_dict` com suporte bidirecional
- [x] `save_oof_predictions` grava atomicamente sob `{run_dir}/oof/`
- [x] `load_oof_predictions` restaura registros OOF com fidelidade exata
- [x] Testes unitários passam em `tests/unit/orchestration/test_oof_storage.py`
- [x] Gate rápido aprovado

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar ConsolidatedOofPredictions, codecs e persistencia atomica (ORCH-20)`

---

### Phase 2: Agregação Canônica e Comitê Out-of-Fold

#### T2: Implementar Agregação Canônica OOF e Estatísticas de Comitê

**What**: Implementar a lógica nuclear de `consolidate_oof_predictions` em `src/experimental_ml/orchestration/oof.py`. Agrupar os registros `PredictionRecord` das dobras de desenvolvimento de uma configuração `(model_id, scenario_id)` indexando por `observation_id`. Garantir a ordenação lexicográfica canônica obrigatória por `observation_id`. Para observações com avaliação única, fixar $\hat{\mu}_i = \hat{y}_i$ e preservar `y_std` se disponível. Para observações com múltiplas avaliações (ex: bootstrap ou validações repetidas), calcular a média pontual de comitê $\hat{\mu}_i$ e o desvio padrão amostral entre folds $\hat{\sigma}_i$. Para problemas de classificação, computar as probabilidades médias ponderadas entre folds. Calcular resíduos pontuais $e_i = y_i - \hat{\mu}_i$. Criar testes unitários em `tests/unit/orchestration/test_oof_aggregation.py`.
**Where**: `src/experimental_ml/orchestration/oof.py`
**Depends on**: T1
**Reuses**: `src/experimental_ml/orchestration/types.py`
**Requirement**: ORCH-15, ORCH-16

**Done when**:
- [x] `consolidate_oof_predictions` agrupa predições preservando valores reais
- [x] Ordenação canônica por `observation_id` garantida
- [x] Comitê $\hat{\mu}_i, \hat{\sigma}_i$ calculado corretamente para observações repetidas
- [x] Predição pontual e `y_std` preservados em partição única
- [x] Probabilidades médias calculadas em classificação
- [x] Testes unitários passam em `tests/unit/orchestration/test_oof_aggregation.py`
- [x] Gate rápido aprovado

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar agregacao canonica OOF e estatisticas de comite (ORCH-15, ORCH-16)`

---

### Phase 3: Avaliação de Métricas Agrupadas e Agregações Inter-Folds

#### T3: Implementar Métricas Agrupadas (POOLED_OOF) e Inter-Folds (FOLD_AGGREGATION)

**What**: Integrar em `consolidate_oof_predictions` a avaliação de métricas com separação estrita de escopo (`RF4.7`). Avaliar as métricas globais sobre os vetores completos de predições concatenadas out-of-fold com escopo `MetricEvaluationScope.POOLED_OOF` utilizando as funções de métrica do catálogo (`experimental_ml.metrics`). A partir dos `CellResultRecord` das células concluídas, agrupar métricas de cada dobra e calcular estatísticas inter-dobras (média, desvio, mediana, IQR) com escopo `AggregationScope.FOLD_AGGREGATION` através de `aggregate_fold_metrics`. Tratar indefinições numéricas e divisões por zero com `MetricStatus.UNDEFINED_NAN` sem interrupção de fluxo (ADR-005). Criar testes unitários em `tests/unit/orchestration/test_oof_metrics.py`.
**Where**: `src/experimental_ml/orchestration/oof.py`
**Depends on**: T2
**Reuses**: `src/experimental_ml/metrics/catalog.py`, `src/experimental_ml/metrics/aggregation.py`, `src/experimental_ml/metrics/types.py`
**Requirement**: ORCH-17, ORCH-18, ORCH-19

**Done when**:
- [x] Métricas agrupadas avaliadas com escopo `POOLED_OOF`
- [x] Agregações inter-dobras calculadas com escopo `FOLD_AGGREGATION`
- [x] Falhas numéricas capturadas com `MetricStatus.UNDEFINED_NAN`
- [x] `pooled_metrics` e `aggregated_metrics` persistidos separadamente
- [x] Testes unitários passam em `tests/unit/orchestration/test_oof_metrics.py`
- [x] Gate rápido aprovado

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar metricas pooled OOF e agregacoes inter-folds (ORCH-17, ORCH-18, ORCH-19)`

---

### Phase 4: Cobertura Parcial e Tolerância a Falhas

#### T4: Implementar Suporte a Falhas Parciais e Governança de Cobertura

**What**: Expandir `consolidate_oof_predictions` para gerenciar execuções que sofreram falhas parciais em folds sob a política `FAULT_TOLERANT`. Comparar as observações obtidas com o conjunto de observações esperado da partição (`target_observation_ids` ou conjunto esperado do plano). Caso folds tenham falhado mas ao menos uma dobra tenha concluído com sucesso, consolidar as observações disponíveis, atribuir razão de cobertura `coverage < 1.0`, fixar o status das métricas agregadas como `MetricStatus.PARTIAL_COVERAGE` e registrar a lista de `observation_id` ausentes na tupla `warnings`. Se 100% dos folds tiverem falhado para a configuração, levantar `DataIntegrityError`. Criar testes unitários em `tests/unit/orchestration/test_oof_fault_tolerance.py`.
**Where**: `src/experimental_ml/orchestration/oof.py`
**Depends on**: T3
**Reuses**: `src/experimental_ml/core/findings.py`, `src/experimental_ml/core/enums.py`
**Requirement**: ORCH-15, ORCH-21

**Done when**:
- [x] Cobertura parcial calculada para dobras faltantes em `FAULT_TOLERANT`
- [x] Status `PARTIAL_COVERAGE` atribuído às métricas afetadas
- [x] Lista de observações faltantes registrada em warnings
- [x] Falha em 100% dos folds rejeitada com `DataIntegrityError`
- [x] Testes unitários passam em `tests/unit/orchestration/test_oof_fault_tolerance.py`
- [x] Gate rápido aprovado

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(orchestration): implementar suporte a falhas parciais e governanca de cobertura OOF (ORCH-15, ORCH-21)`

---

### Phase 5: Portão de Estágio da Etapa 4 (verify_runs_gate)

#### T5: Implementar Portão de Estágio da Etapa 4 (verify_runs_gate)

**What**: Implementar a função validadora `verify_runs_gate(target: Path | str)` em `src/experimental_ml/stages/stage_gates.py`. Verificar o cumprimento dos portões de estágio upstream (`verify_preparation_gate`, `verify_partition_gate`, `verify_scenarios_gate`, `verify_models_gate`). Validar a existência e integridade do manifesto `{run_dir}/execution_state.json`. Rejeitar qualquer execução contendo células em estados não-terminais (`PENDING` ou `RUNNING`) com `ContractViolationError`. Realizar a auditoria física em disco: comprovar que para cada célula `COMPLETED` existem os arquivos `cells/cell_{cell_id}.json` e `predictions/pred_{cell_id}.json`, e que para cada célula `FAILED` existe o arquivo `cell_{cell_id}.json`. Comprovar que para cada configuração com células concluídas existe o arquivo `oof/oof_{model_id}__{scenario_id}.json`. Verificar o alinhamento de hashes cruzados (`partition_plan_id` e `dataset_hash`). Re-exportar `verify_runs_gate` na API pública de `experimental_ml.stages`. Criar testes unitários em `tests/unit/stages/test_stage_runs_gate.py`.
**Where**: `src/experimental_ml/stages/stage_gates.py`
**Depends on**: T1, T4
**Reuses**: `src/experimental_ml/stages/stage_gates.py`, `src/experimental_ml/orchestration/state.py`, `src/experimental_ml/orchestration/storage.py`, `src/experimental_ml/orchestration/oof.py`
**Requirement**: ORCH-21

**Done when**:
- [ ] Portões upstream validados
- [ ] Ausência de células `PENDING` ou `RUNNING` verificada
- [ ] Integridade de artefatos de células e predições em disco verificada
- [ ] Existência e integridade de arquivos OOF verificada
- [ ] Divergência de `partition_plan_id` ou `dataset_hash` rejeitada com `DataIntegrityError`
- [ ] Resumo estruturado retornado com sucesso em execuções válidas
- [ ] Testes unitários passam em `tests/unit/stages/test_stage_runs_gate.py`
- [ ] Gate rápido aprovado

**Tests**: unit  
**Gate**: quick  
**Commit**: `feat(stages): implementar portao de estagio da etapa 4 verify_runs_gate (ORCH-21)`

---

### Phase 6: Integração Transversal e API Pública

#### T6: Implementar Integração Transversal e API Pública

**What**: Atualizar `src/experimental_ml/orchestration/__init__.py` reexportando todos os novos símbolos públicos de consolidação OOF (`ConsolidatedOofPredictions`, `consolidate_oof_predictions`, `save_oof_predictions`, `load_oof_predictions`, `consolidate_matrix_oof`) na lista `__all__`. Implementar a função utilitária `consolidate_matrix_oof(run_dir, ...)` para consolidar automaticamente todas as configurações presentes no estado da matriz. Implementar suíte de testes de integração transversal em `tests/integration/orchestration/test_oof_integration.py` validando o encadeamento completo: execução de matriz experimental $\rightarrow$ consolidação automática de OOF $\rightarrow$ validação e aprovação pelo portão `verify_runs_gate`. Validar a pureza estrita de runtime (`XCUT-02`) assegurando que apenas a biblioteca padrão e `numpy>=1.24.0` sejam importados.
**Where**: `src/experimental_ml/orchestration/__init__.py`
**Depends on**: T1, T2, T3, T4, T5
**Reuses**: `src/experimental_ml/orchestration/engine.py`, `src/experimental_ml/orchestration/oof.py`, `src/experimental_ml/stages/stage_gates.py`
**Requirement**: ORCH-15 a ORCH-21

**Done when**:
- [ ] Símbolos públicos devidamente expostos em `__all__`
- [ ] `consolidate_matrix_oof` consolida todas as configurações da matriz
- [ ] Testes de integração ponta a ponta passam com sucesso
- [ ] Teste de isolamento de subprocesso comprova pureza de dependências (`XCUT-02`)
- [ ] Suíte completa do framework passa sem regressões: `.venv/bin/pytest tests/ -v`
- [ ] Full gate check aprovado

**Tests**: integration  
**Gate**: full  
**Commit**: `feat(orchestration): expor API publica OOF e implementar suite de integracao transversal (ORCH-15 a ORCH-21)`

---

## Checks

**C1** - save_oof_predictions grava atomicamente o arquivo JSON de predições OOF (ORCH-20, AC 1)  
Proof: run unit | tests/unit/orchestration/test_oof_storage.py::test_m53_03_01_save_oof_predictions_atomic PASSED

**C2** - load_oof_predictions desserializa o arquivo JSON em ConsolidatedOofPredictions (ORCH-20, AC 2)  
Proof: run unit | tests/unit/orchestration/test_oof_storage.py::test_m53_03_02_load_oof_predictions PASSED

**C3** - Codecs oof_predictions_to_dict e oof_predictions_from_dict preservam fidelidade exata (ORCH-20, AC 3)  
Proof: run unit | tests/unit/orchestration/test_oof_storage.py::test_m53_03_03_codecs_roundtrip_fidelity PASSED

**C4** - save_oof_predictions com overwrite=False rejeita sobrescrita de arquivo existente (ORCH-20, AC 4)  
Proof: run unit | tests/unit/orchestration/test_oof_storage.py::test_m53_03_04_save_oof_no_overwrite_protection PASSED

**C5** - consolidate_oof_predictions agrega PredictionRecord de folds de desenvolvimento em registro unico (ORCH-15, AC 1)  
Proof: run unit | tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_01_consolidate_aggregates_records PASSED

**C6** - consolidate_oof_predictions ordena observacoes canonicamente por observation_id (ORCH-15, AC 2)  
Proof: run unit | tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_02_canonical_sorting_by_obs_id PASSED

**C7** - Observacoes avaliadas em multiplas dobras calculam estatisticas de comite mu e sigma (ORCH-16, AC 3)  
Proof: run unit | tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_03_multi_fold_committee_statistics PASSED

**C8** - Observacoes avaliadas em dobra unica preservam predicao e y_std se presente (ORCH-16, AC 4)  
Proof: run unit | tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_04_single_fold_prediction_preservation PASSED

**C9** - Modelos de classificacao agrupam probabilidades medias entre folds (ORCH-16, AC 5)  
Proof: run unit | tests/unit/orchestration/test_oof_aggregation.py::test_m53_01_05_classification_probability_pooling PASSED

**C10** - POOLED_OOF calcula metricas sobre vetor global de predicoes concatenadas (ORCH-17, AC 1)  
Proof: run unit | tests/unit/orchestration/test_oof_metrics.py::test_m53_02_01_pooled_oof_metrics_evaluation PASSED

**C11** - FOLD_AGGREGATION calcula estatisticas inter-dobras (media, desvio, mediana, iqr) (ORCH-18, AC 2)  
Proof: run unit | tests/unit/orchestration/test_oof_metrics.py::test_m53_02_02_fold_aggregation_statistics PASSED

**C12** - Calculo de metricas trata divisao por zero e valores invalidos com UNDEFINED_NAN (ORCH-19, AC 3)  
Proof: run unit | tests/unit/orchestration/test_oof_metrics.py::test_m53_02_03_undefined_nan_resilience PASSED

**C13** - ConsolidatedOofPredictions armazena pooled_metrics e aggregated_metrics separadamente (ORCH-17, ORCH-18, AC 4)  
Proof: run unit | tests/unit/orchestration/test_oof_metrics.py::test_m53_02_04_metrics_scopes_distinction PASSED

**C14** - Dobras com falha em FAULT_TOLERANT marcam PARTIAL_COVERAGE sobre observacoes disponiveis (ORCH-15, AC 1)  
Proof: run unit | tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_01_partial_coverage_on_fold_failure PASSED

**C15** - Lista de observation_id ausentes e registrada em warnings de cobertura parcial (ORCH-15, AC 2)  
Proof: run unit | tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_02_missing_observations_warning PASSED

**C16** - Falha em 100% dos folds lanca DataIntegrityError ao tentar consolidar (ORCH-15, AC 3)  
Proof: run unit | tests/unit/orchestration/test_oof_fault_tolerance.py::test_m53_05_03_total_failure_raises_integrity_error PASSED

**C17** - verify_runs_gate verifica pre-requisitos upstream das etapas 1, 2, 3 e 4A (ORCH-21, AC 1)  
Proof: run unit | tests/unit/stages/test_stage_runs_gate.py::test_m53_04_01_upstream_gates_verification PASSED

**C18** - verify_runs_gate lanca DataIntegrityError se execution_state.json estiver ausente ou corrompido (ORCH-21, AC 2)  
Proof: run unit | tests/unit/stages/test_stage_runs_gate.py::test_m53_04_02_missing_or_corrupt_state_raises PASSED

**C19** - verify_runs_gate lanca ContractViolationError se houver celulas PENDING ou RUNNING (ORCH-21, AC 3)  
Proof: run unit | tests/unit/stages/test_stage_runs_gate.py::test_m53_04_03_non_terminal_cell_status_raises PASSED

**C20** - verify_runs_gate lanca DataIntegrityError se celula COMPLETED nao tiver artefato em disco (ORCH-21, AC 4)  
Proof: run unit | tests/unit/stages/test_stage_runs_gate.py::test_m53_04_04_missing_cell_artifact_raises PASSED

**C21** - verify_runs_gate lanca DataIntegrityError se dataset_hash ou partition_plan_id divergirem (ORCH-21, AC 5)  
Proof: run unit | tests/unit/stages/test_stage_runs_gate.py::test_m53_04_05_cross_hashes_mismatch_raises PASSED

**C22** - verify_runs_gate retorna resumo estruturado ao aprovar execucao valida (ORCH-21, AC 6)  
Proof: run unit | tests/unit/stages/test_stage_runs_gate.py::test_m53_04_06_valid_runs_gate_returns_summary PASSED

**C23** - API publica de OOF e verify_runs_gate devidamente exportada em orchestration e stages (ORCH-15 a ORCH-21)  
Proof: run integration | tests/integration/orchestration/test_oof_integration.py::test_m53_06_01_public_api_exports PASSED

**C24** - Ciclo ponta a ponta: matriz -> consolidacao OOF -> aprovacao por verify_runs_gate (ORCH-15 a ORCH-21)  
Proof: run integration | tests/integration/orchestration/test_oof_integration.py::test_m53_06_02_end_to_end_matrix_to_oof_gate PASSED

**C25** - Conformidade estrita de dependencias de runtime: apenas standard library e numpy (XCUT-02)  
Proof: run integration | tests/integration/orchestration/test_oof_integration.py::test_m53_06_03_runtime_purity_xcut_02 PASSED

---

## Handoff

- **Dispatched:** none
- **Completed:** T1, T2, T3, T4
- **In-progress:** Phase 5
- **Next step:** Execute T5
- **Blockers:** none
