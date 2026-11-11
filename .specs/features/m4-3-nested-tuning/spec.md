# Feature: m4-3-nested-tuning

**Approved**: 2026-11-11 - user: "aprovado"

## Problem Statement

Na arquitetura do `experimental-ml-framework`, a otimização de hiperparâmetros (Etapa 3B / **RF3.5**) deve operar sob um regime estrito de validação cruzada aninhada (*Nested Cross-Validation* / **ADR-003** e **CA-E4B-01**):
1. **Confinamento Intra-Fold:** Toda busca de hiperparâmetros (Grid Search, Random Search ou configuração fixa) deve ser executada **exclusivamente dentro do conjunto de treinamento da partição externa** ($X_{\text{train}}, y_{\text{train}}$), sem qualquer acesso ou vazamento de dados do conjunto de avaliação externa ($X_{\text{val}}, y_{\text{val}}$ ou *holdout*).
2. **Avaliação Aninhada Multi-Fold:** Os candidatos a hiperparâmetros são avaliados dividindo $X_{\text{train}}, y_{\text{train}}$ em partições internas ($K_{\text{inner}} \ge 2$), garantindo que a métrica de seleção reflita o desempenho de generalização interno e não o sobreajuste de treino.
3. **Tratamento Rigoroso de `UNDEFINED_NAN` (ADR-005):** Caso um candidato resulte em `UNDEFINED_NAN` na métrica de otimização em qualquer dobra interna, sua pontuação agregada deve receber `UNDEFINED_NAN`, impedindo que ele vença um candidato válido. Se todos os candidatos falharem ou gerarem `UNDEFINED_NAN`, o sistema deve lançar `TuningOptimizationError`, impedindo que a célula prossiga com parâmetros inválidos ou convertidos arbitrariamente para zero.
4. **Determinismo e Rastreabilidade Completa:** A amostragem no Random Search e a ordenação no Grid Search devem ser 100% determinísticas sob uma semente explícita, e todas as tentativas avaliadas (*trials*) devem ser registradas em estruturas imutáveis contendo parâmetros, pontuações internas por fold e status de execução.
5. **Pureza de Runtime (XCUT-02):** A infraestrutura de busca e particionamento interno deve depender estritamente de `numpy>=1.24.0` e do motor `experimental_ml.metrics`, sem dependência mandatória de frameworks externos de tuning (Optuna, Scikit-Learn GridSearchCV, Ray Tune).

## Out of Scope

- Persistência em disco de `models.json` e subcomandos da CLI `expml models` — escopo do Sub-marco M4.4.
- Orquestração matricial da matriz experimental $(M \times C \times F)$ — escopo do Marco M5 (`orchestration`).
- Métodos avançados de tuning bayesiano (ex.: TPE, Gaussian Processes) — alocados como extensões para a Onda 2 (`CUSTOM_TUNER`).
- Novas dependências de runtime além de `numpy>=1.24.0` (`XCUT-02`).

## Assumptions & Open Questions

**Open questions:** none - os padrões e requisitos de Nested CV já foram formalizados na SRS (RF3.5) e na Arquitetura (Seção 3.3.4, ADR-003 e ADR-005).

| Assumption / Question | Chosen default | Rationale |
| :--- | :--- | :--- |
| Localização do pacote | `src/experimental_ml/tuning/` | Alinhado com a Seção 2.3 da Arquitetura (Nível 3 de dependências, Camada 1 / Etapa 3B) |
| Tipos de busca suportados no MVP | `FIXED`, `GRID_SEARCH`, `RANDOM_SEARCH` | Cobre 100% dos requisitos de referência e estudos de bancada do framework |
| Estratégia padrão de CV interna | K-Fold padrão interno particionando os índices $0 \dots N_{\text{train}}-1$ | Simples, determinístico e livre de vazamento sob arrays NumPy puros |
| Critério de desempate entre candidatos idênticos | Menor índice do candidato na lista ordenada de tentativas | Garante seleção 100% determinística e reproduzível |
| Exceção para falha total de otimização | `TuningOptimizationError` herdando de `ContractViolationError` | Mantém compatibilidade com a hierarquia de exceções do `core` |

## User Stories

### US-M43-01 (Priority: P1) — Hyperparameter Tuning Types and Declarative Search Specs
As an experimental ML researcher,  
I want declarative specifications and immutable structures for hyperparameter search spaces,  
So that I can configure fixed parameters, grid search, or random search with budgets and target metrics in a verifiable schema.

### US-M43-02 (Priority: P1) — Search Specification Declarative Validation
As a pipeline validator,  
I want `validate_search_spec` to inspect the search specification against catalog metrics and parameter constraints,  
So that malformed parameter grids, conflicting directions, or invalid internal folds are caught before execution begins.

### US-M43-03 (Priority: P1) — Deterministic Candidate Generation
As an experiment runner,  
I want deterministic generation of hyperparameter candidate combinations for both grid and random search,  
So that candidate exploration is entirely reproducible given a configuration and random seed.

### US-M43-04 (Priority: P1) — Intra-Fold Inner Partitioning (Anti-Leakage)
As a methodologist,  
I want internal cross-validation splitting to operate strictly on the training partition indices of the outer fold,  
So that no evaluation, test, or holdout observations are ever partitioned or exposed during tuning (`CA-E4B-01`).

### US-M43-05 (Priority: P1) — Nested Tuning Execution and Metric Optimization
As an experiment runner,  
I want `run_nested_tuning` to evaluate each candidate across internal folds using fresh model instances and compute aggregated metrics,  
So that the optimal parameter configuration $\theta^*$ is selected objectively according to the declared metric and direction.

### US-M43-06 (Priority: P1) — Strict Handling of Undefined Metrics and Total Failure
As a data integrity auditor,  
I want candidates producing `UNDEFINED_NAN` to be disqualified and `TuningOptimizationError` raised if all candidates fail,  
So that undefined metrics never propagate as winning parameters or get silently coerced to zero (`ADR-005`).

### US-M43-07 (Priority: P2) — Public API Exports and Runtime Purity
As a software engineer,  
I want `experimental_ml.tuning` to export its public API cleanly and enforce single runtime dependency (`numpy>=1.24.0`),  
So that the tuning subsystem remains pure, modular, and fully integrated with `experimental_ml.models` (`XCUT-01`, `XCUT-02`).

## Acceptance Criteria

### Criteria for US-M43-01 (Tuning Types and Specs)
- **AC-M43-01-01 (Ubiquitous):** The system SHALL define `SearchStrategy` as a closed `str, Enum` with members `FIXED`, `GRID_SEARCH`, `RANDOM_SEARCH`, and `CUSTOM_TUNER`.
- **AC-M43-01-02 (Ubiquitous):** The system SHALL define `HyperparameterSearchSpec` as an immutable frozen dataclass with slots containing `search_strategy: SearchStrategy`, `param_grid: MappingProxyType[str, tuple[Any, ...]]`, `optimization_metric: str`, `direction: MetricDirection`, `n_iter: int | None`, `inner_cv_folds: int`, `seed: int | None`, and `description: str`.
- **AC-M43-01-03 (Ubiquitous):** The system SHALL define `TuningTrialRecord` as an immutable frozen dataclass with slots containing `trial_index: int`, `params: MappingProxyType[str, Any]`, `fold_scores: tuple[float, ...]`, `mean_score: float`, `status: MetricStatus`, and `error_message: str | None`.
- **AC-M43-01-04 (Ubiquitous):** The system SHALL define `TuningResult` as an immutable frozen dataclass with slots containing `best_params: MappingProxyType[str, Any]`, `best_score: float`, `best_trial_index: int`, `trials: tuple[TuningTrialRecord, ...]`, `search_strategy: SearchStrategy`, and `optimization_metric: str`.

### Criteria for US-M43-02 (Declarative Search Validation)
- **AC-M43-02-01 (Event-driven):** WHEN `validate_search_spec` is invoked with a valid `HyperparameterSearchSpec`, THEN the system SHALL return the validated spec without raising errors.
- **AC-M43-02-02 (Unwanted-behavior):** IF `inner_cv_folds < 2` or `inner_cv_folds` is not a positive integer, THEN `validate_search_spec` SHALL raise `ConfigurationError`.
- **AC-M43-02-03 (Unwanted-behavior):** IF `optimization_metric` is empty, not a registered metric in `METRICS_CATALOG`, or has an incompatible direction declared, THEN `validate_search_spec` SHALL raise `ConfigurationError`.
- **AC-M43-02-04 (Unwanted-behavior):** IF `search_strategy` is `RANDOM_SEARCH` and `n_iter` is not a positive integer ($n_{\text{iter}} \le 0$ or `None`), THEN `validate_search_spec` SHALL raise `ConfigurationError`.

### Criteria for US-M43-03 (Deterministic Candidate Generation)
- **AC-M43-03-01 (Event-driven):** WHEN candidate generation is requested for `GRID_SEARCH`, THEN the system SHALL produce the full Cartesian product of parameter values in deterministic lexicographical order.
- **AC-M43-03-02 (Event-driven):** WHEN candidate generation is requested for `RANDOM_SEARCH` with an explicit `seed`, THEN the system SHALL sample exactly `n_iter` parameter combinations deterministically and reproducibly.
- **AC-M43-03-03 (Event-driven):** WHEN candidate generation is requested for `FIXED`, THEN the system SHALL produce exactly one candidate parameter set using the declared parameter mappings.

### Criteria for US-M43-04 (Inner Fold Partitioning)
- **AC-M43-04-01 (Event-driven):** WHEN inner partitioning is executed on training array $X_{\text{train}}$ of length $N$, THEN the system SHALL partition indices $0 \dots N-1$ into $K_{\text{inner}}$ disjoint folds where $\text{Train}_{\text{inner}} \cap \text{Val}_{\text{inner}} = \emptyset$ for each inner split.
- **AC-M43-04-02 (State-driven):** WHILE performing inner partitioning, the system SHALL ensure that no observations outside of $X_{\text{train}}$ or $y_{\text{train}}$ are referenced, partitioned, or evaluated (`CA-E4B-01`).
- **AC-M43-04-03 (Unwanted-behavior):** IF $N < K_{\text{inner}}$, THEN the system SHALL raise `ContractViolationError` due to insufficient observations for inner cross-validation.

### Criteria for US-M43-05 (Nested Tuning Execution)
- **AC-M43-05-01 (Event-driven):** WHEN `run_nested_tuning` is called with valid inputs, THEN the system SHALL evaluate each candidate across all $K_{\text{inner}}$ folds, creating fresh model instances via `instantiate_fresh_model` for every combination of candidate and fold.
- **AC-M43-05-02 (Event-driven):** WHEN evaluating candidates, THEN the system SHALL compute internal fold metrics using `experimental_ml.metrics` and aggregate fold scores as the arithmetic mean over inner validation sets.
- **AC-M43-05-03 (State-driven):** WHILE selecting the winning candidate $\theta^*$, the system SHALL select the candidate with the highest mean score when `direction=MAXIMIZE` and lowest mean score when `direction=MINIMIZE`, resolving exact ties by choosing the candidate with the lowest trial index.

### Criteria for US-M43-06 (Handling Undefined Metrics & Failure)
- **AC-M43-06-01 (State-driven):** WHILE aggregating inner fold scores, IF any inner fold produces `MetricStatus.UNDEFINED_NAN` or non-finite values, THEN the candidate's trial status SHALL be marked as `UNDEFINED_NAN` and disqualified from beating any valid candidate (`ADR-005`).
- **AC-M43-06-02 (Unwanted-behavior):** IF all evaluated candidates fail, encounter exceptions, or produce `UNDEFINED_NAN`, THEN `run_nested_tuning` SHALL raise `TuningOptimizationError` without silently returning zero scores (`ADR-005`).
- **AC-M43-06-03 (Ubiquitous):** The system SHALL ensure that `TuningOptimizationError` inherits from `ContractViolationError` and preserves error details from failed trials.

### Criteria for US-M43-07 (Public API and Runtime Purity)
- **AC-M43-07-01 (Ubiquitous):** The system SHALL export all tuning specs, enums, exceptions, and `run_nested_tuning` via `src/experimental_ml/tuning/__init__.py`.
- **AC-M43-07-02 (Ubiquitous):** The system SHALL enforce single runtime dependency (`numpy>=1.24.0`), with zero mandatory third-party optimization framework imports in the tuning subsystem (`XCUT-02`).

## Requirement Traceability

| Requirement ID | Acceptance Criterion | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| TUN-01 | AC-M43-01-01, AC-M43-01-02, AC-M43-01-03, AC-M43-01-04 | Unit tests on frozen dataclasses, slots, and immutability (`test_tuning_types.py`) | pending |
| TUN-02 | AC-M43-02-01, AC-M43-02-02, AC-M43-02-03, AC-M43-02-04 | Unit tests on `validate_search_spec` constraint enforcement (`test_tuning_validation.py`) | pending |
| TUN-03 | AC-M43-03-01, AC-M43-03-02, AC-M43-03-03 | Unit tests on candidate generation for grid, random, and fixed search (`test_tuning_candidates.py`) | pending |
| TUN-04 | AC-M43-04-01, AC-M43-04-02, AC-M43-04-03 | Unit tests on internal fold index splitting and sample size validation (`test_tuning_partitioning.py`) | pending |
| TUN-05 | AC-M43-05-01, AC-M43-05-02, AC-M43-05-03 | Unit tests on `run_nested_tuning` multi-fold execution, metric dispatch, and direction tie-breaking (`test_tuning_execution.py`) | pending |
| TUN-06 | AC-M43-06-01, AC-M43-06-02, AC-M43-06-03 | Unit tests verifying `UNDEFINED_NAN` disqualification and `TuningOptimizationError` on total failure (`test_tuning_failures.py`) | pending |
| TUN-07 | AC-M43-07-01, AC-M43-07-02 | Subprocess test asserting `numpy>=1.24.0` purity and end-to-end integration (`test_tuning_integration.py`) | pending |
