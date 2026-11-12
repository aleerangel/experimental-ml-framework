"""Transversal integration tests for experiment matrix execution and checkpointing (M5.2).

Covers C27 to C30 (ORCH-09 to ORCH-14, XCUT-02).
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

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
import experimental_ml.orchestration as orch
from experimental_ml.orchestration import (
    CellDescriptor,
    CellId,
    MatrixExecutionState,
    MatrixProgressCallback,
    NullProgressCallback,
    build_cell_matrix,
    derive_cell_seed,
    load_cell_artifacts,
    load_execution_state,
    resume_experiment_matrix,
    run_experiment_matrix,
    save_execution_state,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _build_synthetic_dataset_and_plan():
    """Create a 30-sample dataset and 2-fold partition plan."""
    rng = np.random.RandomState(42)
    n_samples = 30

    x1 = rng.uniform(0.0, 10.0, size=n_samples)
    x2 = rng.uniform(-5.0, 5.0, size=n_samples)
    y = 2.0 * x1 - 1.5 * x2 + 5.0 + rng.normal(0.0, 0.1, size=n_samples)

    raw_data = {
        "x1": x1.tolist(),
        "x2": x2.tolist(),
        "y": y.tolist(),
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
    # 2 folds
    f0 = FoldPartition(fold_index=0, train_ids=obs[:15], val_ids=obs[15:])
    f1 = FoldPartition(fold_index=1, train_ids=obs[15:], val_ids=obs[:15])

    partition_plan = PartitionPlan(
        plan_id=PartitionPlanId("plan_integ_matrix"),
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
    return view, partition_plan


def test_m52_06_01_public_api_exports():
    """C27: Public API cleanly exported in experimental_ml.orchestration (ORCH-09 a ORCH-14)."""
    expected_exports = [
        "ExecutionStatus",
        "ErrorPolicy",
        "CellPhase",
        "CellId",
        "TimingBreakdown",
        "PredictionRecord",
        "CellResultRecord",
        "execute_single_cell",
        "cell_result_to_dict",
        "cell_result_from_dict",
        "prediction_record_to_dict",
        "prediction_record_from_dict",
        "save_cell_artifacts",
        "load_cell_artifacts",
        "CellDescriptor",
        "derive_cell_seed",
        "build_cell_matrix",
        "MatrixExecutionState",
        "matrix_execution_state_to_dict",
        "matrix_execution_state_from_dict",
        "save_execution_state",
        "load_execution_state",
        "MatrixProgressCallback",
        "NullProgressCallback",
        "run_experiment_matrix",
        "resume_experiment_matrix",
    ]

    for sym in expected_exports:
        assert hasattr(orch, sym), f"Symbol '{sym}' missing from experimental_ml.orchestration"
        assert sym in orch.__all__, f"Symbol '{sym}' missing from __all__"


def test_m52_06_02_end_to_end_matrix_lifecycle(tmp_path: Path):
    """C28: End-to-end matrix lifecycle executes 2x2x2 grid with metrics and predictions (ORCH-11)."""
    view, partition_plan = _build_synthetic_dataset_and_plan()
    run_dir = tmp_path / "matrix_e2e"

    # 2 Models
    m1 = ModelSpec(
        model_id=ModelId("mean_regressor"),
        display_name="Mean Regressor",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Mean",
        scientific_justification="Baseline",
    )
    m2 = ModelSpec(
        model_id=ModelId("median_regressor"),
        display_name="Median Regressor",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEDIAN"),
        description="Median",
        scientific_justification="Baseline",
    )

    # 2 Scenarios
    s1 = FeatureScenario(
        scenario_id=ScenarioId("sc_x1"),
        name="Scenario X1",
        description="X1 only",
        scientific_justification="Single feature",
        mode=ScenarioMode.FIXED,
        selected_features=("x1",),
    )
    s2 = FeatureScenario(
        scenario_id=ScenarioId("sc_all"),
        name="Scenario All",
        description="All features",
        scientific_justification="Full set",
        mode=ScenarioMode.FIXED,
        selected_features=("x1", "x2"),
    )

    # 2 Models x 2 Scenarios x 2 Folds = 8 cells
    state = run_experiment_matrix(
        model_specs=[m1, m2],
        scenarios=[s1, s2],
        partition_plan=partition_plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse", "mae"),
        outer_n_jobs=2,
    )

    assert state.total_cells == 8
    assert state.completed_cells == 8
    assert state.failed_cells == 0
    assert state.cancelled_cells == 0

    # Verify physical artifacts on disk
    loaded_state = load_execution_state(run_dir)
    assert loaded_state.completed_cells == 8

    cells_dir = run_dir / "cells"
    preds_dir = run_dir / "predictions"
    assert len(list(cells_dir.glob("cell_*.json"))) == 8
    assert len(list(preds_dir.glob("pred_*.json"))) == 8

    # Load and verify one cell
    first_cell_id = list(state.cell_statuses.keys())[0]
    cell_res, pred_rec = load_cell_artifacts(first_cell_id, run_dir)
    assert cell_res.status == ExecutionStatus.COMPLETED
    assert "rmse" in cell_res.metrics
    assert pred_rec is not None
    assert len(pred_rec.y_pred) == 15


def test_m52_06_03_end_to_end_crash_recovery_resume(tmp_path: Path):
    """C29: End-to-end crash-recovery simulation verifies idempotent resume (ORCH-13)."""
    view, partition_plan = _build_synthetic_dataset_and_plan()
    run_dir = tmp_path / "matrix_crash_resume"

    m1 = ModelSpec(
        model_id=ModelId("mean_regressor"),
        display_name="Mean Regressor",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Mean",
        scientific_justification="Baseline",
    )
    s1 = FeatureScenario(
        scenario_id=ScenarioId("sc_all"),
        name="Scenario All",
        description="All features",
        scientific_justification="Full set",
        mode=ScenarioMode.FIXED,
        selected_features=("x1", "x2"),
    )

    # 1 model x 1 scenario x 2 folds = 2 cells
    # Simulate a crash after completing 1 cell
    stop_flag = False
    class CrashSimulatorCallback(NullProgressCallback):
        def on_cell_completed(self, cell_result):
            nonlocal stop_flag
            stop_flag = True

    cb = CrashSimulatorCallback()
    interrupted_state = run_experiment_matrix(
        model_specs=[m1],
        scenarios=[s1],
        partition_plan=partition_plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=("rmse",),
        cancellation_check=lambda: stop_flag,
        progress_callback=cb,
    )

    assert interrupted_state.completed_cells == 1
    assert interrupted_state.cancelled_cells == 1

    # Resume the interrupted experiment run
    resumed_state = resume_experiment_matrix(
        run_dir=run_dir,
        model_specs=[m1],
        scenarios=[s1],
        partition_plan=partition_plan,
        sanitized_view=view,
        metrics=("rmse",),
    )

    assert resumed_state.total_cells == 2
    assert resumed_state.completed_cells == 2
    assert resumed_state.cancelled_cells == 0
    assert resumed_state.failed_cells == 0


def test_m52_06_04_runtime_purity_xcut_02():
    """C30: Subprocess runtime dependency purity check asserts only numpy and standard library (XCUT-02)."""
    code = (
        "import sys\n"
        "import experimental_ml.orchestration as orch\n"
        "forbidden = ['scipy', 'pandas', 'sklearn', 'torch', 'qiskit', 'pyarrow']\n"
        "loaded = [p for p in forbidden if p in sys.modules]\n"
        "if loaded:\n"
        "    print(f'FORBIDDEN_LOADED: {loaded}', file=sys.stderr)\n"
        "    sys.exit(1)\n"
        "sys.exit(0)\n"
    )
    res = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"XCUT-02 violation in orchestration module: {res.stderr}"
