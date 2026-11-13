"""Matrix execution and checkpoint/resume engine for experimental-ml-framework.

Complies with ORCH-11, ORCH-12, ORCH-13, ORCH-14, STORE-01, and XCUT-02.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import threading
from typing import Callable, Sequence

from experimental_ml.core.findings import ConfigurationError, DataIntegrityError
from experimental_ml.core.types import ExperimentId
from experimental_ml.data.preparation import SanitizedDatasetView
from experimental_ml.features.scenarios import FeatureScenario
from experimental_ml.models.spec import ModelSpec
from experimental_ml.orchestration.callbacks import (
    MatrixProgressCallback,
    NullProgressCallback,
)
from experimental_ml.orchestration.execution import execute_single_cell
from experimental_ml.orchestration.matrix import (
    CellDescriptor,
    build_cell_matrix,
)
from experimental_ml.orchestration.state import (
    MatrixExecutionState,
    load_execution_state,
    save_execution_state,
)
from experimental_ml.orchestration.storage import (
    save_cell_artifacts,
)
from experimental_ml.orchestration.types import (
    CellId,
    CellResultRecord,
    ErrorPolicy,
    ExecutionStatus,
    PredictionRecord,
)
from experimental_ml.validation.types import PartitionPlan


def _generate_run_id() -> str:
    """Generate a default unique run ID with UTC timestamp."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"run_{ts}"


def run_experiment_matrix(
    model_specs: Sequence[ModelSpec],
    scenarios: Sequence[FeatureScenario],
    partition_plan: PartitionPlan,
    sanitized_view: SanitizedDatasetView,
    run_dir: Path | str,
    *,
    metrics: Sequence[str] = (),
    master_seed: int = 42,
    outer_n_jobs: int = 1,
    error_policy: ErrorPolicy = ErrorPolicy.FAULT_TOLERANT,
    progress_callback: MatrixProgressCallback | None = None,
    cancellation_check: Callable[[], bool] | None = None,
    experiment_id: ExperimentId | None = None,
    run_id: str | None = None,
    overwrite: bool = False,
    auto_consolidate_oof: bool = True,
) -> MatrixExecutionState:
    """Execute the full experimental cell matrix with atomic incremental checkpointing.

    Args:
        model_specs: Models to evaluate.
        scenarios: Feature scenarios to evaluate.
        partition_plan: Partition plan defining validation folds.
        sanitized_view: Pre-partition sanitized dataset view.
        run_dir: Destination directory for artifacts and execution_state.json.
        metrics: Metrics to evaluate on each validation fold.
        master_seed: Master random seed.
        outer_n_jobs: Parallelism level (1 = sequential, >1 = worker pool).
        error_policy: FAULT_TOLERANT or FAIL_FAST.
        progress_callback: Observer for execution events.
        cancellation_check: Optional callable checked before starting each cell;
            if returns True, stops execution and marks unstarted cells as CANCELLED.
        experiment_id: Optional experiment identifier (defaults to "exp_matrix").
        run_id: Optional run identifier (defaults to generated timestamp).
        overwrite: If False, raises ConfigurationError if run_dir already has execution_state.json.

    Returns:
        Consolidated MatrixExecutionState representing the execution outcome.

    Raises:
        ConfigurationError: If run_dir exists and overwrite=False, or arguments invalid.
        Exception: If error_policy is FAIL_FAST and a cell fails.
    """
    dest_run_dir = Path(run_dir).resolve()
    cells_dir = dest_run_dir / "cells"
    preds_dir = dest_run_dir / "predictions"
    state_file = dest_run_dir / "execution_state.json"

    if state_file.exists() and not overwrite:
        raise ConfigurationError(
            f"Run directory '{dest_run_dir}' already contains execution_state.json and overwrite is False"
        )

    cells_dir.mkdir(parents=True, exist_ok=True)
    preds_dir.mkdir(parents=True, exist_ok=True)

    descriptors = build_cell_matrix(
        model_specs=model_specs,
        scenarios=scenarios,
        partition_plan=partition_plan,
        master_seed=master_seed,
    )

    exp_id = experiment_id or ExperimentId("exp_matrix")
    r_id = run_id or _generate_run_id()
    now_iso = datetime.now(timezone.utc).isoformat()
    plan_id = str(getattr(partition_plan, "partition_plan_id", None) or getattr(partition_plan, "plan_id", ""))
    view_hash = str(getattr(sanitized_view, "dataset_hash", ""))

    initial_statuses = {desc.cell_id: ExecutionStatus.PENDING for desc in descriptors}
    state = MatrixExecutionState(
        experiment_id=exp_id,
        run_id=r_id,
        created_at=now_iso,
        updated_at=now_iso,
        master_seed=master_seed,
        total_cells=len(descriptors),
        cell_statuses=initial_statuses,
        source_dataset_hash=view_hash,
        partition_plan_id=plan_id,
    )
    save_execution_state(state, dest_run_dir, overwrite=True)

    callback = progress_callback or NullProgressCallback()
    callback.on_matrix_start(len(descriptors))

    state_lock = threading.RLock()

    def _execute_single_cell_worker(desc: CellDescriptor) -> None:
        nonlocal state
        callback.on_cell_start(desc.cell_id)

        try:
            cell_result, pred_record = execute_single_cell(
                model_spec=desc.model_spec,
                scenario=desc.scenario,
                fold=desc.fold,
                sanitized_view=sanitized_view,
                partition_plan=partition_plan,
                metrics=metrics,
                error_policy=error_policy,
                cell_seed=desc.cell_seed,
                cell_id=desc.cell_id,
            )
        except Exception as exc:
            with state_lock:
                state = state.with_cell_update(desc.cell_id, ExecutionStatus.FAILED)
                save_execution_state(state, dest_run_dir, overwrite=True)
            raise exc

        save_cell_artifacts(
            cell_result=cell_result,
            prediction_record=pred_record,
            run_dir=dest_run_dir,
            overwrite=True,
        )

        with state_lock:
            state = state.with_cell_update(desc.cell_id, cell_result.status)
            save_execution_state(state, dest_run_dir, overwrite=True)

        if cell_result.status == ExecutionStatus.COMPLETED:
            callback.on_cell_completed(cell_result)
        else:
            callback.on_cell_failed(cell_result)

    def _parallel_worker(desc: CellDescriptor) -> None:
        nonlocal state
        if cancellation_check is not None and cancellation_check():
            with state_lock:
                state = state.with_cell_update(desc.cell_id, ExecutionStatus.CANCELLED)
                save_execution_state(state, dest_run_dir, overwrite=True)
            return
        _execute_single_cell_worker(desc)

    if outer_n_jobs <= 1:
        for idx, desc in enumerate(descriptors):
            if cancellation_check is not None and cancellation_check():
                with state_lock:
                    for rem_desc in descriptors[idx:]:
                        state = state.with_cell_update(rem_desc.cell_id, ExecutionStatus.CANCELLED)
                    save_execution_state(state, dest_run_dir, overwrite=True)
                callback.on_matrix_completed(state)
                return state
            _execute_single_cell_worker(desc)
    else:
        with ThreadPoolExecutor(max_workers=outer_n_jobs) as executor:
            future_to_desc = {
                executor.submit(_parallel_worker, desc): desc
                for desc in descriptors
            }
            for future in as_completed(future_to_desc):
                try:
                    future.result()
                except Exception as exc:
                    if error_policy == ErrorPolicy.FAIL_FAST:
                        for f in future_to_desc:
                            f.cancel()
                        raise exc

    callback.on_matrix_completed(state)

    if auto_consolidate_oof and state.completed_cells > 0:
        from experimental_ml.orchestration.oof import consolidate_matrix_oof

        try:
            consolidate_matrix_oof(
                dest_run_dir,
                task_type=sanitized_view.schema.task_type,
                target_observation_ids=tuple(sanitized_view.observation_ids),
                overwrite=True,
            )
        except Exception:
            pass

    return state


def resume_experiment_matrix(
    run_dir: Path | str,
    model_specs: Sequence[ModelSpec],
    scenarios: Sequence[FeatureScenario],
    partition_plan: PartitionPlan,
    sanitized_view: SanitizedDatasetView,
    *,
    metrics: Sequence[str] = (),
    outer_n_jobs: int = 1,
    error_policy: ErrorPolicy = ErrorPolicy.FAULT_TOLERANT,
    retry_failed: bool = True,
    progress_callback: MatrixProgressCallback | None = None,
    cancellation_check: Callable[[], bool] | None = None,
    auto_consolidate_oof: bool = True,
) -> MatrixExecutionState:
    """Resume an existing experiment matrix execution, skipping verified completed cells.

    Inspects {run_dir}/execution_state.json, verifies physical disk artifacts for cells
    marked as COMPLETED, and executes any remaining PENDING or (optionally) FAILED cells.

    Args:
        run_dir: Directory containing execution_state.json and cell artifacts.
        model_specs: Models to evaluate.
        scenarios: Feature scenarios to evaluate.
        partition_plan: Partition plan defining validation folds.
        sanitized_view: Pre-partition sanitized dataset view.
        metrics: Metrics to evaluate on validation folds.
        outer_n_jobs: Parallelism level (1 = sequential, >1 = worker pool).
        error_policy: FAULT_TOLERANT or FAIL_FAST.
        retry_failed: If True, re-executes previously failed cells.
        progress_callback: Observer for execution events.
        cancellation_check: Optional callable to request graceful cancellation.

    Returns:
        Updated MatrixExecutionState after executing remaining cells.

    Raises:
        ConfigurationError: If execution_state.json does not exist.
    """
    dest_run_dir = Path(run_dir).resolve()
    state_file = dest_run_dir / "execution_state.json"
    if not state_file.exists():
        raise ConfigurationError(
            f"Cannot resume execution: '{state_file}' does not exist"
        )

    state = load_execution_state(dest_run_dir)

    # 1. Global state identity validation against provided partition plan and dataset (ACH-M5-02)
    plan_id = str(getattr(partition_plan, "partition_plan_id", None) or getattr(partition_plan, "plan_id", ""))
    view_hash = str(getattr(sanitized_view, "dataset_hash", ""))

    if not state.source_dataset_hash or state.source_dataset_hash != view_hash:
        raise DataIntegrityError(
            f"Cannot resume execution: dataset hash mismatch. "
            f"State expects '{state.source_dataset_hash}', got '{view_hash}'"
        )
    if not state.partition_plan_id or state.partition_plan_id != plan_id:
        raise DataIntegrityError(
            f"Cannot resume execution: partition plan mismatch. "
            f"State expects '{state.partition_plan_id}', got '{plan_id}'"
        )

    descriptors = build_cell_matrix(
        model_specs=model_specs,
        scenarios=scenarios,
        partition_plan=partition_plan,
        master_seed=state.master_seed,
    )

    cells_dir = dest_run_dir / "cells"
    preds_dir = dest_run_dir / "predictions"

    # 2. Cell-level identity validation before modifying state or executing anything (ACH-M5-02)
    from experimental_ml.core.storage import read_json

    for desc in descriptors:
        current_status = state.cell_statuses.get(desc.cell_id, ExecutionStatus.PENDING)
        cell_file = cells_dir / f"cell_{desc.cell_id}.json"

        if current_status == ExecutionStatus.COMPLETED and cell_file.exists():
            try:
                c_dict = read_json(cell_file)
            except Exception as exc:
                raise DataIntegrityError(
                    f"Cannot resume execution: cell artifact '{cell_file.name}' is unreadable: {exc}"
                ) from exc

            c_plan_id = c_dict.get("partition_plan_id")
            if c_plan_id and str(c_plan_id) != plan_id:
                raise DataIntegrityError(
                    f"Cannot resume execution: cell artifact '{cell_file.name}' belongs to "
                    f"partition plan '{c_plan_id}', expected '{plan_id}'"
                )

    callback = progress_callback or NullProgressCallback()
    callback.on_matrix_start(len(descriptors))

    # 3. Reconcile statuses and verify physical artifacts
    for desc in descriptors:
        current_status = state.cell_statuses.get(desc.cell_id, ExecutionStatus.PENDING)
        cell_file = cells_dir / f"cell_{desc.cell_id}.json"

        if current_status == ExecutionStatus.COMPLETED:
            if not cell_file.exists():
                # Missing artifact: reset to PENDING
                state = state.with_cell_update(desc.cell_id, ExecutionStatus.PENDING)
        elif current_status == ExecutionStatus.FAILED:
            if retry_failed:
                state = state.with_cell_update(desc.cell_id, ExecutionStatus.PENDING)
        elif current_status in (ExecutionStatus.CANCELLED, ExecutionStatus.RUNNING):
            state = state.with_cell_update(desc.cell_id, ExecutionStatus.PENDING)

    save_execution_state(state, dest_run_dir, overwrite=True)

    # 2. Partition into skipped and to-run
    cells_to_run: list[CellDescriptor] = []
    for desc in descriptors:
        st = state.cell_statuses.get(desc.cell_id)
        if st == ExecutionStatus.COMPLETED:
            callback.on_cell_skipped(desc.cell_id)
        else:
            cells_to_run.append(desc)

    if not cells_to_run:
        callback.on_matrix_completed(state)
        return state

    # 3. Execute remaining cells
    state_lock = threading.RLock()

    def _execute_single_cell_worker(desc: CellDescriptor) -> None:
        nonlocal state
        callback.on_cell_start(desc.cell_id)

        try:
            cell_result, pred_record = execute_single_cell(
                model_spec=desc.model_spec,
                scenario=desc.scenario,
                fold=desc.fold,
                sanitized_view=sanitized_view,
                partition_plan=partition_plan,
                metrics=metrics,
                error_policy=error_policy,
                cell_seed=desc.cell_seed,
                cell_id=desc.cell_id,
            )
        except Exception as exc:
            with state_lock:
                state = state.with_cell_update(desc.cell_id, ExecutionStatus.FAILED)
                save_execution_state(state, dest_run_dir, overwrite=True)
            raise exc

        save_cell_artifacts(
            cell_result=cell_result,
            prediction_record=pred_record,
            run_dir=dest_run_dir,
            overwrite=True,
        )

        with state_lock:
            state = state.with_cell_update(desc.cell_id, cell_result.status)
            save_execution_state(state, dest_run_dir, overwrite=True)

        if cell_result.status == ExecutionStatus.COMPLETED:
            callback.on_cell_completed(cell_result)
        else:
            callback.on_cell_failed(cell_result)

    def _parallel_worker(desc: CellDescriptor) -> None:
        nonlocal state
        if cancellation_check is not None and cancellation_check():
            with state_lock:
                state = state.with_cell_update(desc.cell_id, ExecutionStatus.CANCELLED)
                save_execution_state(state, dest_run_dir, overwrite=True)
            return
        _execute_single_cell_worker(desc)

    if outer_n_jobs <= 1:
        for idx, desc in enumerate(cells_to_run):
            if cancellation_check is not None and cancellation_check():
                with state_lock:
                    for rem_desc in cells_to_run[idx:]:
                        state = state.with_cell_update(rem_desc.cell_id, ExecutionStatus.CANCELLED)
                    save_execution_state(state, dest_run_dir, overwrite=True)
                callback.on_matrix_completed(state)
                return state
            _execute_single_cell_worker(desc)
    else:
        with ThreadPoolExecutor(max_workers=outer_n_jobs) as executor:
            future_to_desc = {
                executor.submit(_parallel_worker, desc): desc
                for desc in cells_to_run
            }
            for future in as_completed(future_to_desc):
                try:
                    future.result()
                except Exception as exc:
                    if error_policy == ErrorPolicy.FAIL_FAST:
                        for f in future_to_desc:
                            f.cancel()
                        raise exc

    callback.on_matrix_completed(state)

    if auto_consolidate_oof and state.completed_cells > 0:
        from experimental_ml.orchestration.oof import consolidate_matrix_oof

        try:
            consolidate_matrix_oof(
                dest_run_dir,
                task_type=sanitized_view.schema.task_type,
                target_observation_ids=tuple(sanitized_view.observation_ids),
                overwrite=True,
            )
        except Exception:
            pass

    return state
