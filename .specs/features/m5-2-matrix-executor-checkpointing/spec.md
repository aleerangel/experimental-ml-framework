# Feature: m5-2-matrix-executor-checkpointing

**Approved**: 2026-11-12 - user: "aprovado"

## Problem Statement

Na Etapa 4B (Execução Matricial e Persistência) do `experimental-ml-framework`, os experimentos exigem a avaliação completa de uma grade cartesiana tridimensional de células de execução:
$$\mathcal{M} \times \mathcal{C} \times \mathcal{F}$$
onde $\mathcal{M}$ é o conjunto de modelos declarados no catálogo, $\mathcal{C}$ é o conjunto de cenários de features aprovados, e $\mathcal{F}$ é o conjunto de partições/folds de validação definidos no plano de particionamento.

O sub-marco anterior (M5.1) estabeleceu os contratos individuais, estruturas de dados imutáveis e o executor funcional atômico de uma única célula (`execute_single_cell`). No entanto, o framework ainda não possui:
1. Um formulador determinístico da grade matricial de células que ordene a sequência de execução e derive sementes criptograficamente isoladas para cada célula a partir de uma semente mestra (`master_seed`).
2. Um gerenciador declarativo e imutável de estado global da matriz (`MatrixExecutionState`), capaz de rastrear em tempo real a transição de status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`) e contadores agregados de cada célula.
3. Um motor de execução matricial (`run_experiment_matrix`) com salvamento atômico incremental de artefatos por célula e gravação periódica do estado global em `execution_state.json`.
4. Suporte a paralelismo controlado de células externas (`outer_n_jobs`), permitindo acelerar a execução concorrente sem corromper o estado global ou sofrer conflitos de escrita.
5. Um mecanismo resiliente de retomada (*Checkpoint & Resume* via `resume_experiment_matrix`), que inspeciona o diretório de execução, verifica a integridade dos artefatos gravados e pula células já concluídas sem recomputação desnecessária.
6. Suporte a cancelamento e interrupção graciosa (*graceful shutdown*), persistindo o estado atualizado das células pendentes como canceladas caso a execução seja interrompida.
7. Observabilidade desacoplada por meio de callbacks de progresso (`MatrixProgressCallback`), viabilizando a integração com a CLI e UIs sem dependências pesadas de runtime (`XCUT-02`).

Este sub-marco M5.2 provê a infraestrutura central de orquestração em larga escala do framework, pavimentando o caminho para a consolidação out-of-fold e portões de estágio (M5.3) e para o comando de terminal `expml run` (M5.4).

## Out of Scope

- Consolidação out-of-fold de predições (`consolidate_oof_predictions`) e agregação global de métricas — escopo do Sub-marco M5.3.
- Portão de estágio formal `verify_runs_gate` em `experimental_ml.stages` — escopo do Sub-marco M5.3.
- Interface de linha de comando `expml run ...` e formatação de saída em terminal — escopo do Sub-marco M5.4.
- Análise estatística comparativa (Nadeau-Bengio, Wilcoxon pareado, controle FDR/FWER) — escopo do Marco M6.
- Inclusão de novas dependências obrigatórias de runtime além de `numpy>=1.24.0` (`XCUT-02`).

## Assumptions & Open Questions

**Open questions:** none - a arquitetura e os contratos para orquestração matricial foram estabelecidos na SRS (RF4.1 a RF4.4) e no documento de arquitetura.

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Ordenação canônica da grade matricial | Ordenação lexicográfica determinística por `(model_id, scenario_id, fold_id)` | Assegura reprodutibilidade estrita da sequência de execução e rastreabilidade visual consistente |
| Derivação determinística de semente por célula | `SHA-256(master_seed:model_id:scenario_id:fold_id) % (2**31 - 1)` | Garante independência estatística entre células e total reprodutibilidade do comportamento estocástico |
| Localização do manifesto de estado de execução | `{run_dir}/execution_state.json` | Padrão arquitetural centralizado para fácil inspeção, persistência atômica e retomada resiliente |
| Política de paralelismo em `outer_n_jobs` | `outer_n_jobs = 1` executa sequencialmente; `outer_n_jobs > 1` executa via pool de threads de I/O / workers concorrentes | Evita deadlocks e sobrecarga de CPU, respeitando ambientes com recursos restritos e permitindo paralelismo |
| Validação de células concluídas na retomada (*Resume*) | Uma célula só é considerada `COMPLETED` se constar no estado e ambos os arquivos `cell_{id}.json` e `pred_{id}.json` existirem e forem válidos | Protege contra estado corrompido ou arquivos apagados manualmente entre reinicializações |
| Pureza de runtime (`XCUT-02`) | Biblioteca padrão (`concurrent.futures`, `json`, `pathlib`, `hashlib`, `time`) e `numpy>=1.24.0` exclusivamente | Mantém o núcleo do orquestrador leve e portável sem amarras a frameworks complexos |

## User Stories

### US-M52-01 (Priority: P1) — Formulação da Grade Cartesiana e Derivação de Sementes
As an experimental ML researcher,  
I want to generate the deterministic Cartesian grid of experimental cells and derive unique cell seeds,  
So that the full combination of models, scenarios, and folds is ordered predictably and executes with reproducible randomness.

#### Acceptance Criteria
- **AC-M52-01-01**: When building the execution matrix via `build_cell_matrix`, the system SHALL produce a deterministic sequence of `CellDescriptor` objects representing the Cartesian product $\mathcal{M} \times \mathcal{C} \times \mathcal{F}$.
- **AC-M52-01-02**: The generated cells SHALL be sorted canonically by `(model_id, scenario_id, fold_id)`.
- **AC-M52-01-03**: Each `CellDescriptor` SHALL contain a canonical `cell_id` structured as `cell_{model_id}__{scenario_id}__{fold_id}` and a derived integer `cell_seed`.
- **AC-M52-01-04**: When deriving `cell_seed` via `derive_cell_seed`, identical input parameters SHALL always produce the identical 31-bit integer, and different parameters SHALL produce distinct seeds.

### US-M52-02 (Priority: P1) — Estado de Execução da Matriz e Codecs
As an experimental ML researcher,  
I want an immutable and serializable data structure to represent the global progress of the matrix execution,  
So that execution status, counts, and cell transitions can be tracked in memory and saved to disk losslessly.

#### Acceptance Criteria
- **AC-M52-02-01**: The system SHALL provide `MatrixExecutionState` as an immutable frozen dataclass recording `experiment_id`, `run_id`, `created_at`, `updated_at`, `master_seed`, `total_cells`, `cell_statuses`, `completed_cells`, `failed_cells`, and `cancelled_cells`.
- **AC-M52-02-02**: When serializing `MatrixExecutionState` via `matrix_execution_state_to_dict`, the system SHALL generate a JSON-compliant dictionary preserving all metadata and cell status mappings.
- **AC-M52-02-03**: When deserializing via `matrix_execution_state_from_dict`, the system SHALL reconstruct an equivalent `MatrixExecutionState` with matching values and types (round-trip fidelity).
- **AC-M52-02-04**: The system SHALL provide `save_execution_state` and `load_execution_state` to atomically write and read `{run_dir}/execution_state.json`.

### US-M52-03 (Priority: P1) — Motor de Execução Matricial e Checkpointing Incremental
As an experimental ML researcher,  
I want to execute the matrix of experimental cells with incremental atomic checkpointing,  
So that individual cell results and predictions are immediately written to disk and global state is updated after each cell.

#### Acceptance Criteria
- **AC-M52-03-01**: When executing the matrix via `run_experiment_matrix` with `outer_n_jobs = 1`, the system SHALL execute all cells in canonical sequential order.
- **AC-M52-03-02**: Upon completion of each individual cell, the system SHALL immediately write `cell_{id}.json` and `pred_{id}.json` atomically.
- **AC-M52-03-03**: Upon completion of each individual cell, the system SHALL immediately update and atomically flush `{run_dir}/execution_state.json`.
- **AC-M52-03-04**: If a cell fails under `ErrorPolicy.FAULT_TOLERANT`, the system SHALL record the cell status as `FAILED`, write its `cell_{id}.json` artifact with error details, and continue executing remaining cells.
- **AC-M52-03-05**: If a cell fails under `ErrorPolicy.FAIL_FAST`, the system SHALL immediately halt execution and re-raise the exception after persisting the latest state.

### US-M52-04 (Priority: P2) — Paralelismo Configurável de Células
As an experimental ML researcher,  
I want to execute cells concurrently across multiple workers when `outer_n_jobs > 1`,  
So that execution time on multi-core systems is reduced while maintaining thread safety and deterministic outputs.

#### Acceptance Criteria
- **AC-M52-04-01**: When `outer_n_jobs > 1`, `run_experiment_matrix` SHALL dispatch cell executions concurrently across worker threads/processes.
- **AC-M52-04-02**: Concurrent updates to `execution_state.json` SHALL be thread-safe, preventing corrupted writes or race conditions.
- **AC-M52-04-03**: The final set of generated artifacts and recorded metrics SHALL be identical in content to sequential execution with the same seed.

### US-M52-05 (Priority: P1) — Mecanismo de Checkpoint e Retomada Idempotente
As an experimental ML researcher,  
I want to resume an interrupted matrix run without recomputing completed cells,  
So that crashed or paused long-running experiments can recover smoothly.

#### Acceptance Criteria
- **AC-M52-05-01**: When invoking `resume_experiment_matrix` on an existing `run_dir`, the system SHALL load `{run_dir}/execution_state.json` and verify the integrity of persisted cell artifacts.
- **AC-M52-05-02**: All cells whose status is `COMPLETED` with valid disk artifacts SHALL be skipped without re-execution.
- **AC-M52-05-03**: Cells whose status is `PENDING`, or `FAILED` when `retry_failed = True`, SHALL be executed and persisted.
- **AC-M52-05-04**: When all remaining cells finish, the system SHALL update `execution_state.json` to reflect the final state.

### US-M52-06 (Priority: P2) — Interrupção Graciosa e Observabilidade
As an experimental ML researcher,  
I want graceful cancellation and real-time progress callbacks during matrix execution,  
So that experiment execution can be monitored and safely terminated without corrupting data.

#### Acceptance Criteria
- **AC-M52-06-01**: The system SHALL accept an optional `MatrixProgressCallback` protocol notifying observers on cell start, cell completion, and matrix completion.
- **AC-M52-06-02**: When a cancellation request is signaled, `run_experiment_matrix` SHALL halt further dispatch of pending cells, record pending cells as `CANCELLED`, and atomically persist `execution_state.json`.

---

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Component | Description |
| :--- | :--- | :--- | :--- |
| ORCH-09 | AC-M52-01-01, AC-M52-01-02, AC-M52-01-03, AC-M52-01-04 | `orchestration.matrix` | Formulação determinística da grade $M \times C \times F$ e derivação de sementes |
| ORCH-10 | AC-M52-02-01, AC-M52-02-02, AC-M52-02-03, AC-M52-02-04 | `orchestration.state` | Estado global `MatrixExecutionState`, serialização e persistência atômica |
| ORCH-11 | AC-M52-03-01, AC-M52-03-02, AC-M52-03-03, AC-M52-03-04, AC-M52-03-05 | `orchestration.engine` | Motor sequencial com checkpoint incremental e tolerância a falhas |
| ORCH-12 | AC-M52-04-01, AC-M52-04-02, AC-M52-04-03 | `orchestration.engine` | Paralelismo concorrente configurável (`outer_n_jobs > 1`) thread-safe |
| ORCH-13 | AC-M52-05-01, AC-M52-05-02, AC-M52-05-03, AC-M52-05-04 | `orchestration.engine` | Mecanismo de retomada resiliente (*Checkpoint & Resume*) |
| ORCH-14 | AC-M52-06-01, AC-M52-06-02 | `orchestration.engine` | Observabilidade por callbacks e cancelamento gracioso |
