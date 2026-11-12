"""Unit tests for matrix checkpoint and resume mechanism (M5.2).

Covers C22 to C26 (ORCH-13).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from experimental_ml.core.enums import ExecutionStatus, TaskType
from experimental_ml.core.findings import ConfigurationError
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
from experimental_ml.orchestration.engine import (
    resume_experiment_matrix,
    run_experiment_matrix,
)
from experimental_ml.orchestration.state import (
    MatrixExecutionState,
    load_execution_state,
    save_execution_state,
)
from experimental_ml.orchestration.storage import load_cell_artifacts
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
    # 2 folds
    f0 = FoldPartition(fold_index=0, train_ids=obs[:2], val_ids=obs[2:])
    f1 = FoldPartition(fold_index=1, train_ids=obs[2:], val_ids=obs[:2])

    partition_plan = PartitionPlan(
        plan_id=PartitionPlanId("plan_resume"),
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
        scenario_id=ScenarioId("sc_f"),
        name="Fixed F",
        description="Fixed F",
        scientific_justification="Test",
        mode=ScenarioMode.FIXED,
        selected_features=("x",),
    )

    return view, partition_plan, [m1], [s1]


class ResumeTrackingCallback(MatrixProgressCallback):
    def __init__(self) -> None:
        self.started: list[CellId] = []
        self.completed: list[CellId] = []
        self.skipped: list[CellId] = []
        self.failed: list[CellId] = []

    def on_matrix_start(self, total_cells: int) -> None:
        pass

    def on_cell_start(self, cell_id: CellId) -> None:
        self.started.append(cell_id)

    def on_cell_completed(self, cell_result: CellResultRecord) -> None:
        self.completed.append(cell_result.cell_id)

    def on_cell_failed(self, cell_result: CellResultRecord) -> None:
        self.failed.append(cell_result.cell_id)

    def on_cell_skipped(self, cell_id: CellId) -> None:
        self.skipped.append(cell_id)

    def on_matrix_completed(self, state: MatrixExecutionState) -> None:
        pass


def test_m52_05_01_resume_loads_and_verifies(tmp_path: Path):
    """C22: resume_experiment_matrix loads existing execution_state.json and verifies artifacts (ORCH-13, AC 1)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_missing_state"

    # Must raise ConfigurationError if directory does not have execution_state.json
    with pytest.raises(ConfigurationError, match="does not exist"):
        resume_experiment_matrix(
            run_dir=run_dir,
            model_specs=models,
            scenarios=scenarios,
            partition_plan=plan,
            sanitized_view=view,
        )


def test_m52_05_02_resume_skips_completed_cells(tmp_path: Path):
    """C23: resume_experiment_matrix skips verified COMPLETED cells without re-computation (ORCH-13, AC 2)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_skip_completed"

    # 1. Run matrix completely (2 cells)
    run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
    )

    # 2. Resume on already-completed run
    cb = ResumeTrackingCallback()
    state = resume_experiment_matrix(
        run_dir=run_dir,
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        metrics=("rmse",),
        progress_callback=cb,
    )

    assert state.total_cells == 2
    assert state.completed_cells == 2
    assert len(cb.skipped) == 2  # Both cells skipped!
    assert len(cb.started) == 0  # No cells re-executed!


def test_m52_05_03_resume_reexecutes_missing_artifacts(tmp_path: Path):
    """C24: resume_experiment_matrix re-executes corrupted or missing COMPLETED cells (ORCH-13, AC 1)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_missing_art"

    run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
    )

    # Delete artifact of fold 0 manually
    c0_file = run_dir / "cells" / "cell_cell_dummy_mean__sc_f__fold_0.json"
    assert c0_file.exists()
    c0_file.unlink()

    # Resume must detect missing artifact and re-execute fold 0, but skip fold 1
    cb = ResumeTrackingCallback()
    state = resume_experiment_matrix(
        run_dir=run_dir,
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        metrics=("rmse",),
        progress_callback=cb,
    )

    assert state.completed_cells == 2
    assert cb.skipped == [CellId("cell_dummy_mean__sc_f__fold_1")]
    assert cb.started == [CellId("cell_dummy_mean__sc_f__fold_0")]
    assert c0_file.exists()  # Restored!


def test_m52_05_04_resume_executes_pending_cells(tmp_path: Path):
    """C25: resume_experiment_matrix executes PENDING cells to completion (ORCH-13, AC 3)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_pending_resume"

    # Simulate an interrupted run after first cell
    canceled = False
    class StopAfterFirst(ResumeTrackingCallback):
        def on_cell_completed(self, cell_result: CellResultRecord) -> None:
            super().on_cell_completed(cell_result)
            nonlocal canceled
            canceled = True

    cb_first = StopAfterFirst()
    run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
        cancellation_check=lambda: canceled,
        progress_callback=cb_first,
    )

    mid_state = load_execution_state(run_dir)
    assert mid_state.completed_cells == 1
    assert mid_state.cancelled_cells == 1

    # Resume
    cb = ResumeTrackingCallback()
    resumed_state = resume_experiment_matrix(
        run_dir=run_dir,
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        metrics=("rmse",),
        progress_callback=cb,
    )

    assert resumed_state.total_cells == 2
    assert resumed_state.completed_cells == 2
    assert resumed_state.cancelled_cells == 0
    assert cb.skipped == [CellId("cell_dummy_mean__sc_f__fold_0")]
    assert cb.started == [CellId("cell_dummy_mean__sc_f__fold_1")]


def test_m52_05_05_resume_retries_failed_cells(tmp_path: Path):
    """C26: resume_experiment_matrix retries FAILED cells when retry_failed=True (ORCH-13, AC 3)."""
    view, plan, _, scenarios = _build_test_env()
    run_dir = tmp_path / "run_retry_failed"

    attempt = 0
    def flaky_factory(seed: int | None = None):
        nonlocal attempt
        attempt += 1
        class Flaky:
            def fit(self, X, y):
                # Fail on first attempt, succeed on later attempts
                if attempt <= 2:
                    raise RuntimeError("Temporary glitch")
            def predict(self, X):
                return [25.0] * len(X)
        return Flaky()

    flaky_model = ModelSpec(
        model_id=ModelId("flaky_model"),
        display_name="Flaky Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=flaky_factory,
        description="Flaky",
        scientific_justification="Test",
    )

    # 1. Initial run: both folds fail
    run_experiment_matrix(
        model_specs=[flaky_model],
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
        error_policy=ErrorPolicy.FAULT_TOLERANT,
    )

    state_fail = load_execution_state(run_dir)
    assert state_fail.failed_cells == 2
    assert state_fail.completed_cells == 0

    # 2. Resume with retry_failed=True: should retry and succeed
    resumed = resume_experiment_matrix(
        run_dir=run_dir,
        model_specs=[flaky_model],
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        metrics=("rmse",),
        retry_failed=True,
    )

    assert resumed.completed_cells == 2
    assert resumed.failed_cells == 0
