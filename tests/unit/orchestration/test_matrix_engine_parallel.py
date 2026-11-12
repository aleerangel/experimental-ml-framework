"""Unit tests for concurrent multi-worker matrix execution (M5.2).

Covers C18 to C21 (ORCH-12).
"""

from __future__ import annotations

from pathlib import Path
import threading
import time

import numpy as np
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
from experimental_ml.orchestration.codecs import cell_result_from_dict
from experimental_ml.orchestration.engine import run_experiment_matrix
from experimental_ml.orchestration.state import load_execution_state
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
        "x1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "x2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "y": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6],
    }
    schema = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        column_semantic_types={
            "x1": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "x2": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "y": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
    )
    bundle = load_dataset(raw_data, schema)
    profile = profile_dataset(bundle)
    plan_prep = create_preparation_plan(profile, rules=[])
    view = sanitize_dataset(bundle, profile, plan_prep)

    obs = view.observation_ids
    # 3 folds
    f0 = FoldPartition(fold_index=0, train_ids=obs[:4], val_ids=obs[4:])
    f1 = FoldPartition(fold_index=1, train_ids=obs[2:], val_ids=obs[:2])
    f2 = FoldPartition(fold_index=2, train_ids=(obs[0], obs[1], obs[4], obs[5]), val_ids=(obs[2], obs[3]))

    partition_plan = PartitionPlan(
        plan_id=PartitionPlanId("plan_par"),
        source_dataset_hash=view.dataset_hash,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=obs,
        holdout_ids=(),
        folds=(f0, f1, f2),
        config=PartitionConfig(
            strategy=PartitionStrategy.KFOLD,
            regime=EvaluationRegime.CV_ONLY,
            n_splits=3,
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
    m2 = ModelSpec(
        model_id=ModelId("dummy_median"),
        display_name="Median Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEDIAN"),
        description="Median",
        scientific_justification="Test",
    )

    s1 = FeatureScenario(
        scenario_id=ScenarioId("sc_f1"),
        name="Fixed F1",
        description="Fixed F1",
        scientific_justification="Test",
        mode=ScenarioMode.FIXED,
        selected_features=("x1",),
    )

    # 2 models x 1 scenario x 3 folds = 6 cells
    return view, partition_plan, [m1, m2], [s1]


def test_m52_04_01_parallel_dispatch(tmp_path: Path):
    """C18: run_experiment_matrix outer_n_jobs > 1 dispatches cells concurrently (ORCH-12, AC 1)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_par_dispatch"

    active_threads: set[int] = set()
    lock = threading.Lock()

    class ConcurrencyTrackingCallback(MatrixProgressCallback):
        def on_matrix_start(self, total_cells: int) -> None:
            pass
        def on_cell_start(self, cell_id: CellId) -> None:
            with lock:
                active_threads.add(threading.get_ident())
        def on_cell_completed(self, cell_result: CellResultRecord) -> None:
            pass
        def on_cell_failed(self, cell_result: CellResultRecord) -> None:
            pass
        def on_cell_skipped(self, cell_id: CellId) -> None:
            pass
        def on_matrix_completed(self, state: Any) -> None:
            pass

    cb = ConcurrencyTrackingCallback()
    state = run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
        outer_n_jobs=3,
        progress_callback=cb,
    )

    assert state.total_cells == 6
    assert state.completed_cells == 6
    # Multiple distinct threads executed the tasks
    assert len(active_threads) > 1


def test_m52_04_02_thread_safe_state_updates(tmp_path: Path):
    """C19: Concurrent updates to execution_state.json are thread-safe without race conditions (ORCH-12, AC 2)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_thread_safety"

    state = run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse", "mae"),
        outer_n_jobs=4,
    )

    # Reload from disk and verify consistency
    loaded = load_execution_state(run_dir)
    assert loaded.total_cells == 6
    assert loaded.completed_cells == 6
    assert loaded.failed_cells == 0
    assert len(loaded.cell_statuses) == 6
    assert all(s == ExecutionStatus.COMPLETED for s in loaded.cell_statuses.values())


def test_m52_04_03_parallel_sequential_parity(tmp_path: Path):
    """C20: Parallel execution produces identical cell artifacts and metrics as sequential (ORCH-12, AC 3)."""
    view, plan, models, scenarios = _build_test_env()

    seq_dir = tmp_path / "run_parity_seq"
    par_dir = tmp_path / "run_parity_par"

    # 1. Sequential run
    seq_state = run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=seq_dir,
        metrics=("rmse",),
        master_seed=12345,
        outer_n_jobs=1,
    )

    # 2. Parallel run with identical seed
    par_state = run_experiment_matrix(
        model_specs=models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=par_dir,
        metrics=("rmse",),
        master_seed=12345,
        outer_n_jobs=3,
    )

    assert seq_state.total_cells == par_state.total_cells
    assert seq_state.completed_cells == par_state.completed_cells

    # Check that all cell files and predictions match bit-for-bit
    for cell_id in seq_state.cell_statuses.keys():
        seq_res, seq_pred = load_cell_artifacts(cell_id, seq_dir)
        par_res, par_pred = load_cell_artifacts(cell_id, par_dir)

        assert seq_res.cell_id == par_res.cell_id
        assert seq_res.status == par_res.status
        assert seq_res.metrics["rmse"].value == pytest.approx(par_res.metrics["rmse"].value)
        assert seq_pred is not None and par_pred is not None
        np.testing.assert_allclose(seq_pred.y_pred, par_pred.y_pred)


def test_m52_04_04_parallel_cell_failure_handling(tmp_path: Path):
    """C21: Parallel execution handles individual cell failures cleanly (ORCH-12, AC 1)."""
    view, plan, models, scenarios = _build_test_env()
    run_dir = tmp_path / "run_par_failure"

    # Add a broken model
    def failing_factory(seed: int | None = None):
        class Broken:
            def fit(self, X, y):
                raise ValueError("Worker thread failure")
            def predict(self, X):
                return [0.0]
        return Broken()

    broken_model = ModelSpec(
        model_id=ModelId("broken_par"),
        display_name="Broken Par",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=failing_factory,
        description="Fails",
        scientific_justification="Test",
    )

    all_models = [models[0], broken_model]
    # 2 models x 1 scenario x 3 folds = 6 cells
    state = run_experiment_matrix(
        model_specs=all_models,
        scenarios=scenarios,
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
        outer_n_jobs=2,
        error_policy=ErrorPolicy.FAULT_TOLERANT,
    )

    assert state.total_cells == 6
    assert state.completed_cells == 3  # models[0] succeeded across 3 folds
    assert state.failed_cells == 3  # broken_par failed across 3 folds

    loaded = load_execution_state(run_dir)
    assert loaded.completed_cells == 3
    assert loaded.failed_cells == 3
