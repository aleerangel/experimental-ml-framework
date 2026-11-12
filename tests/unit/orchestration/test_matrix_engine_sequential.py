"""Unit tests for sequential matrix execution engine and checkpointing (M5.2).

Covers C11 to C17 (ORCH-11, ORCH-14).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from experimental_ml.core.enums import ExecutionStatus, TaskType
from experimental_ml.core.types import (
    ExperimentId,
    ModelId,
    ObservationId,
    PartitionPlanId,
    ScenarioId,
)
from experimental_ml.data import (
    ColumnSemanticType,
    DatasetSchemaSpec,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features.scenarios import FeatureScenario, ScenarioMode
from experimental_ml.models import (
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    resolve_estimator_factory,
)
from experimental_ml.orchestration.callbacks import MatrixProgressCallback
from experimental_ml.orchestration.engine import run_experiment_matrix
from experimental_ml.orchestration.state import MatrixExecutionState, load_execution_state
from experimental_ml.orchestration.types import (
    CellId,
    CellResultRecord,
    ErrorPolicy,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _build_test_env():
    raw_data = {
        "x": [1.0, 2.0, 3.0, 4.0],
        "y": [10.0, 20.0, 30.0, 40.0],
    }
    schema = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        column_semantic_types={
            "x": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "y": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
    )
    bundle = load_dataset(raw_data, schema)
    profile = profile_dataset(bundle)
    plan_prep = create_preparation_plan(profile, rules=[])
    view = sanitize_dataset(bundle, profile, plan_prep)

    obs = view.observation_ids
    f0 = FoldPartition(fold_index=0, train_ids=obs[:2], val_ids=obs[2:])
    f1 = FoldPartition(fold_index=1, train_ids=obs[2:], val_ids=obs[:2])

    partition_plan = PartitionPlan(
        plan_id=PartitionPlanId("plan_seq"),
        source_dataset_hash=view.dataset_hash,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=obs,
        holdout_ids=(),
        folds=(f0, f1),
        config=PartitionConfig(
            strategy=PartitionStrategy.KFOLD,
            regime=EvaluationRegime.CV_ONLY,
            n_splits=2,
            master_seed=42,
        ),
    )

    m1 = ModelSpec(
        model_id=ModelId("dummy_mean"),
        display_name="Mean Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Mean",
        scientific_justification="Test",
    )

    s1 = FeatureScenario(
        scenario_id=ScenarioId("sc_fixed"),
        name="Fixed Sc",
        description="Fixed Sc",
        scientific_justification="Test",
        mode=ScenarioMode.FIXED,
        selected_features=("x",),
    )

    return view, partition_plan, [m1], [s1]


class RecordingCallback(MatrixProgressCallback):
    def __init__(self) -> None:
        self.events: list[str] = []
        self.started_cells: list[CellId] = []
        self.completed_cells: list[CellId] = []
        self.failed_cells: list[CellId] = []

    def on_matrix_start(self, total_cells: int) -> None:
        self.events.append(f"matrix_start:{total_cells}")

    def on_cell_start(self, cell_id: CellId) -> None:
        self.events.append(f"cell_start:{cell_id}")
        self.started_cells.append(cell_id)

    def on_cell_completed(self, cell_result: CellResultRecord) -> None:
        self.events.append(f"cell_completed:{cell_result.cell_id}")
        self.completed_cells.append(cell_result.cell_id)

    def on_cell_failed(self, cell_result: CellResultRecord) -> None:
        self.events.append(f"cell_failed:{cell_result.cell_id}")
        self.failed_cells.append(cell_result.cell_id)

    def on_cell_skipped(self, cell_id: CellId) -> None:
        self.events.append(f"cell_skipped:{cell_id}")

    def on_matrix_completed(self, state: MatrixExecutionState) -> None:
        self.events.append(f"matrix_completed:{state.completed_cells}/{state.total_cells}")


def test_m52_03_01_sequential_execution_order(tmp_path: Path):
    """C11: run_experiment_matrix executes all cells in sequential canonical order (ORCH-11, AC 1)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_order"

    cb = RecordingCallback()
    state = run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
        outer_n_jobs=1,
        progress_callback=cb,
    )

    assert state.total_cells == 2
    assert state.completed_cells == 2
    assert cb.started_cells == [
        CellId("cell_dummy_mean__sc_fixed__fold_0"),
        CellId("cell_dummy_mean__sc_fixed__fold_1"),
    ]


def test_m52_03_02_atomic_artifacts_written(tmp_path: Path):
    """C12: run_experiment_matrix atomically writes cell and pred artifacts immediately (ORCH-11, AC 2)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_artifacts"

    run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
    )

    cell_0 = run_dir / "cells" / "cell_cell_dummy_mean__sc_fixed__fold_0.json"
    pred_0 = run_dir / "predictions" / "pred_cell_dummy_mean__sc_fixed__fold_0.json"
    cell_1 = run_dir / "cells" / "cell_cell_dummy_mean__sc_fixed__fold_1.json"
    pred_1 = run_dir / "predictions" / "pred_cell_dummy_mean__sc_fixed__fold_1.json"

    assert cell_0.exists()
    assert pred_0.exists()
    assert cell_1.exists()
    assert pred_1.exists()


def test_m52_03_03_incremental_state_flushed(tmp_path: Path):
    """C13: run_experiment_matrix incrementally updates execution_state.json per cell (ORCH-11, AC 3)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_state_flush"

    run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
    )

    loaded_state = load_execution_state(run_dir)
    assert loaded_state.total_cells == 2
    assert loaded_state.completed_cells == 2
    assert loaded_state.failed_cells == 0


def test_m52_03_04_fault_tolerant_continues(tmp_path: Path):
    """C14: run_experiment_matrix FAULT_TOLERANT records FAILED and continues matrix (ORCH-11, AC 4)."""
    view, plan, _, scenarios = _build_test_env()
    run_dir = tmp_path / "run_fault"

    # Failing model
    def failing_factory(seed: int | None = None):
        class Broken:
            def fit(self, X, y):
                raise RuntimeError("Simulated model training explosion")
            def predict(self, X):
                return [0.0]
        return Broken()

    broken_model = ModelSpec(
        model_id=ModelId("broken_model"),
        display_name="Broken Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=failing_factory,
        description="Fails",
        scientific_justification="Test",
    )
    good_model = ModelSpec(
        model_id=ModelId("good_model"),
        display_name="Good Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Good",
        scientific_justification="Test",
    )

    # 2 models x 1 scenario x 2 folds = 4 cells
    # broken_model runs first (alphabetical), then good_model
    cb = RecordingCallback()
    state = run_experiment_matrix(
        model_specs=[broken_model, good_model],
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
        error_policy=ErrorPolicy.FAULT_TOLERANT,
        progress_callback=cb,
    )

    assert state.total_cells == 4
    assert state.failed_cells == 2  # broken_model on fold 0 and fold 1
    assert state.completed_cells == 2  # good_model succeeded!
    assert len(cb.failed_cells) == 2
    assert len(cb.completed_cells) == 2


def test_m52_03_05_fail_fast_halts(tmp_path: Path):
    """C15: run_experiment_matrix FAIL_FAST halts execution and re-raises exception (ORCH-11, AC 5)."""
    view, plan, _, scenarios = _build_test_env()
    run_dir = tmp_path / "run_fail_fast"

    def failing_factory(seed: int | None = None):
        class Broken:
            def fit(self, X, y):
                raise RuntimeError("Fatal explosion")
            def predict(self, X):
                return [0.0]
        return Broken()

    broken_model = ModelSpec(
        model_id=ModelId("broken_model"),
        display_name="Broken",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=failing_factory,
        description="Fails",
        scientific_justification="Test",
    )

    with pytest.raises(RuntimeError, match="Fatal explosion"):
        run_experiment_matrix(
            model_specs=[broken_model],
            scenarios=scenarios,
            partition_plan=plan,
            sanitized_view=view,
            run_dir=run_dir,
            error_policy=ErrorPolicy.FAIL_FAST,
        )

    # State file must still exist and record the failure
    state = load_execution_state(run_dir)
    assert state.failed_cells == 1


def test_m52_03_06_progress_callback_events(tmp_path: Path):
    """C16: MatrixProgressCallback receives cell lifecycle events (ORCH-14, AC 1)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_cb"

    cb = RecordingCallback()
    run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
        progress_callback=cb,
    )

    assert cb.events[0] == "matrix_start:2"
    assert "cell_start:cell_dummy_mean__sc_fixed__fold_0" in cb.events
    assert "cell_completed:cell_dummy_mean__sc_fixed__fold_0" in cb.events
    assert cb.events[-1] == "matrix_completed:2/2"


def test_m52_03_07_cancellation_marks_cancelled(tmp_path: Path):
    """C17: run_experiment_matrix cancellation marks pending cells CANCELLED and flushes state (ORCH-14, AC 2)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_cancel"

    call_count = 0
    def should_cancel() -> bool:
        nonlocal call_count
        call_count += 1
        # Cancel after the first cell has been checked/executed
        return call_count > 1

    cb = RecordingCallback()
    state = run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
        cancellation_check=should_cancel,
        progress_callback=cb,
    )

    # 2 cells total: first cell completed, second cell was cancelled
    assert state.total_cells == 2
    assert state.completed_cells == 1
    assert state.cancelled_cells == 1

    loaded = load_execution_state(run_dir)
    assert loaded.cancelled_cells == 1
    c1 = CellId("cell_dummy_mean__sc_fixed__fold_1")
    assert loaded.cell_statuses[c1] == ExecutionStatus.CANCELLED
