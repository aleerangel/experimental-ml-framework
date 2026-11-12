"""Matrix execution and checkpoint/resume engine for experimental-ml-framework.

Complies with ORCH-11, ORCH-12, ORCH-13, ORCH-14, STORE-01, and XCUT-02.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import threading
from typing import Callable, Sequence

from experimental_ml.core.findings import ConfigurationError
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

    initial_statuses = {desc.cell_id: ExecutionStatus.PENDING for desc in descriptors}
    state = MatrixExecutionState(
        experiment_id=exp_id,
        run_id=r_id,
        created_at=now_iso,
        updated_at=now_iso,
        master_seed=master_seed,
        total_cells=len(descriptors),
        cell_statuses=initial_statuses,
    )
    save_execution_state(state, dest_run_dir, overwrite=True)

    callback = progress_callback or NullProgressCallback()
    callback.on_matrix_start(len(descriptors))

    state_lock = threading.Lock()

    for idx, desc in enumerate(descriptors):
        # 1. Cancellation check
        if cancellation_check is not None and cancellation_check():
            with state_lock:
                for rem_desc in descriptors[idx:]:
                    state = state.with_cell_update(rem_desc.cell_id, ExecutionStatus.CANCELLED)
                save_execution_state(state, dest_run_dir, overwrite=True)
            callback.on_matrix_completed(state)
            return state

        # 2. Notify cell start
        callback.on_cell_start(desc.cell_id)

        # 3. Execute cell
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
            # Under FAIL_FAST, record failure in state, save, and re-raise
            with state_lock:
                state = state.with_cell_update(desc.cell_id, ExecutionStatus.FAILED)
                save_execution_state(state, dest_run_dir, overwrite=True)
            raise exc

        # 4. Save cell artifacts immediately
        save_cell_artifacts(
            cell_result=cell_result,
            prediction_record=pred_record,
            run_dir=dest_run_dir,
            overwrite=True,
        )

        # 5. Update and flush global execution state
        with state_lock:
            state = state.with_cell_update(desc.cell_id, cell_result.status)
            save_execution_state(state, dest_run_dir, overwrite=True)

        # 6. Notify completion / failure
        if cell_result.status == ExecutionStatus.COMPLETED:
            callback.on_cell_completed(cell_result)
        else:
            callback.on_cell_failed(cell_result)

    callback.on_matrix_completed(state)
    return state
