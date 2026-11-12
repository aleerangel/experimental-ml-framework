# Design: m5-2-matrix-executor-checkpointing

## 1. Visão Geral da Arquitetura

O sub-marco M5.2 provê o motor de orquestração matricial e o mecanismo de checkpointing e retomada (*Checkpoint & Resume*), expandindo a capacidade unitária desenvolvida em M5.1 para a avaliação completa da grade cartesiana:
$$\text{Grade} = \mathcal{M} \times \mathcal{C} \times \mathcal{F}$$

A arquitetura organiza-se em quatro componentes desacoplados dentro de `src/experimental_ml/orchestration/`:
1. `matrix.py`: formulação determinística de descritores de células (`CellDescriptor`) e derivação de sementes via SHA-256 (`derive_cell_seed`, `build_cell_matrix`).
2. `state.py`: modelo imutável de estado global (`MatrixExecutionState`), codecs lossless (`to_dict` / `from_dict`) e persistência atômica (`save_execution_state`, `load_execution_state`).
3. `callbacks.py`: protocolo de observabilidade (`MatrixProgressCallback`) e implementação nula (`NullProgressCallback`).
4. `engine.py`: motores de execução matricial (`run_experiment_matrix`) e de retomada resiliente (`resume_experiment_matrix`).

```
+-----------------------------------------------------------------------------------------+
|                                    orchestration                                        |
|                                                                                         |
|  +--------------------+         +------------------------+      +--------------------+  |
|  |     matrix.py      |         |        state.py        |      |    callbacks.py    |  |
|  |  CellDescriptor    |         |  MatrixExecutionState  |      |  ProgressCallback  |  |
|  |  build_cell_matrix |         |  save/load state JSON  |      |  NullCallback      |  |
|  +---------+----------+         +-----------+------------+      +---------+----------+  |
|            |                                |                             |             |
|            +-----------------------+        |       +---------------------+             |
|                                    v        v       v                                   |
|                        +----------------------------------------+                       |
|                        |               engine.py                |                       |
|                        | run_experiment_matrix (sequential/par) |                       |
|                        | resume_experiment_matrix (checkpoint)  |                       |
|                        +--------------------+-------------------+                       |
|                                             |                                           |
|                                             v                                           |
|                        +----------------------------------------+                       |
|                        |   execute_single_cell (from M5.1)      |                       |
|                        |   save_cell_artifacts (from M5.1)      |                       |
|                        +----------------------------------------+                       |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Modelagem de Dados e Tipos

### 2.1 Descritor de Célula e Derivação de Semente (`matrix.py`)

```python
@dataclass(frozen=True, slots=True)
class CellDescriptor:
    """Descritor imutável de uma célula individual na grade matricial."""
    cell_id: CellId
    model_spec: ModelSpec
    scenario: FeatureScenario
    fold: FoldPartition
    cell_seed: int
```

- **ID Canônico**: `cell_id = CellId(f"cell_{model_id}__{scenario_id}__{fold_id}")`.
- **Derivação de Semente**:
  ```python
  def derive_cell_seed(master_seed: int, model_id: str, scenario_id: str, fold_id: str) -> int:
      raw = f"{master_seed}:{model_id}:{scenario_id}:{fold_id}".encode("utf-8")
      digest = hashlib.sha256(raw).digest()
      # Extrai 4 bytes e projeta em inteiro não-negativo de 31 bits
      seed = int.from_bytes(digest[:4], byteorder="big", signed=False) % 2147483647
      return seed
  ```
- **Formulação da Matriz**: `build_cell_matrix(model_specs, scenarios, partition_plan, master_seed)` itera no produto cartesiano e ordena deterministicamente por `(model_id, scenario_id, fold_id)`.

---

### 2.2 Estado Global da Matriz (`state.py`)

```python
@dataclass(frozen=True, slots=True)
class MatrixExecutionState:
    """Estado global imutável da execução matricial."""
    experiment_id: ExperimentId
    run_id: str
    created_at: str  # ISO 8601
    updated_at: str  # ISO 8601
    master_seed: int
    total_cells: int
    cell_statuses: Mapping[CellId, ExecutionStatus]
    completed_cells: int
    failed_cells: int
    cancelled_cells: int

    def with_cell_update(
        self,
        cell_id: CellId,
        status: ExecutionStatus,
        updated_at: str | None = None,
    ) -> MatrixExecutionState:
        """Gera uma nova instância imutável com status de célula atualizado e contadores recalculados."""
        ...
```

- **Persistência**: salva atomicamente em `{run_dir}/execution_state.json` via `write_json_atomic`.
- **Codecs**: `matrix_execution_state_to_dict` e `matrix_execution_state_from_dict`.

---

### 2.3 Protocolo de Observabilidade (`callbacks.py`)

```python
class MatrixProgressCallback(Protocol):
    """Protocolo desacoplado para notificações de progresso da execução matricial."""
    def on_matrix_start(self, total_cells: int) -> None: ...
    def on_cell_start(self, cell_id: CellId) -> None: ...
    def on_cell_completed(self, cell_result: CellResultRecord) -> None: ...
    def on_cell_failed(self, cell_result: CellResultRecord) -> None: ...
    def on_cell_skipped(self, cell_id: CellId) -> None: ...
    def on_matrix_completed(self, state: MatrixExecutionState) -> None: ...
```

---

## 3. Motores de Execução (`engine.py`)

### 3.1 `run_experiment_matrix`
1. Cria a estrutura de diretórios `{run_dir}/cells/` e `{run_dir}/predictions/`.
2. Se `overwrite == False` e `{run_dir}/execution_state.json` já existir, levanta `ConfigurationError`.
3. Constrói a lista ordenada de `CellDescriptor` via `build_cell_matrix`.
4. Inicializa `MatrixExecutionState` com todas as células como `PENDING` e persiste em disco.
5. Disparo das células:
   - Se `outer_n_jobs == 1`: laço sequencial síncrono.
   - Se `outer_n_jobs > 1`: distribui execução via `concurrent.futures.ThreadPoolExecutor(max_workers=outer_n_jobs)`.
6. Para cada célula executada:
   - Checa `cancellation_check()`: se ativado, marca pendentes como `CANCELLED` e interrompe agendamento.
   - Invoca `execute_single_cell(cell_desc.model_spec, cell_desc.scenario, cell_desc.fold, sanitized_view, partition_plan, ...)`.
   - Salva artefatos via `save_cell_artifacts(cell_result, pred_record, run_dir, overwrite=True)`.
   - Atualiza `MatrixExecutionState` com lock de thread para evitar *race conditions*.
   - Salva atomicamente o novo estado em `execution_state.json`.
   - Dispara callback correspondente (`on_cell_completed` ou `on_cell_failed`).
   - Se `status == FAILED` e `error_policy == FAIL_FAST`: re-lança exceção imediatamente após salvar estado.
7. Dispara `on_matrix_completed` e retorna o estado final consolidado.

### 3.2 `resume_experiment_matrix`
1. Verifica a existência de `{run_dir}/execution_state.json`. Se ausente, levanta `ConfigurationError`.
2. Carrega o estado existente via `load_execution_state(run_dir)`.
3. Reconstrói a grade matricial esperada.
4. Para cada célula na grade:
   - Se `cell_statuses[cell_id] == ExecutionStatus.COMPLETED`:
     - Verifica se `{run_dir}/cells/cell_{id}.json` existe no disco.
     - Se arquivo existir: célula confirmada como concluída; notifica `on_cell_skipped`.
     - Se arquivo ausente: marca status como `PENDING` para re-execução.
   - Se `cell_statuses[cell_id] == ExecutionStatus.FAILED`:
     - Se `retry_failed == True`: agenda para re-execução.
     - Se `retry_failed == False`: mantém como falha e pula.
   - Se `cell_statuses[cell_id] in (ExecutionStatus.PENDING, ExecutionStatus.CANCELLED)`:
     - Agenda para execução.
5. Executa as células agendadas exatamente pela mesma lógica de `run_experiment_matrix`.
6. Retorna o estado final consolidado.

---

## 4. Garantias Arquiteturais

1. **Anti-Leakage (`CA-E4B-01`)**: nenhuma informação vaza entre células ou entre folds; cada célula recebe sua própria fatia isolada de dados.
2. **Determinismo Numérico**: a semente derivada `cell_seed` é fixa e idêntica independentemente da ordem física de conclusão em execução paralela.
3. **Persistência Atômica (`ADR-008` / `STORE-01`)**: nenhum arquivo JSON é gravado de forma parcial; `write_json_atomic` garante fsync e substituição atômica via `os.replace`.
4. **Pureza de Runtime (`XCUT-02`)**: zero dependências obrigatórias além de `numpy>=1.24.0` e biblioteca padrão Python.
