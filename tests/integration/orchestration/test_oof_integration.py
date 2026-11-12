"""Transversal integration tests for out-of-fold consolidation, stage gates, and runtime purity.

Covers ORCH-15 to ORCH-21, XCUT-02, and Checks C23 to C25.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest

import experimental_ml.orchestration as orch
import experimental_ml.stages as stages
from experimental_ml.core.enums import ExecutionStatus, TaskType
from experimental_ml.core.types import ModelId, ObservationId, PartitionPlanId, ScenarioId
from experimental_ml.data import (
    ColumnSemanticType,
    DatasetSchemaSpec,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.data.preparation import SanitizedDatasetView
from experimental_ml.features.scenarios import FeatureScenario, ScenarioMode
from experimental_ml.models import (
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    resolve_estimator_factory,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _build_dummy_view() -> SanitizedDatasetView:
    """Helper creating a minimal SanitizedDatasetView."""
    rng = np.random.default_rng(42)
    n = 20
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    y = 2.0 * x1 + rng.normal(scale=0.1, size=n)

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
    return sanitize_dataset(bundle, profile, plan_prep)


def test_m53_06_01_public_api_exports() -> None:
    """Proof C23: Public API symbols exported in experimental_ml.orchestration and stages (ORCH-15 to ORCH-21)."""
    # Orchestration exports
    expected_orch_symbols = [
        "ConsolidatedOofPredictions",
        "consolidate_oof_predictions",
        "save_oof_predictions",
        "load_oof_predictions",
        "consolidate_matrix_oof",
        "oof_predictions_to_dict",
        "oof_predictions_from_dict",
        "aggregated_metric_value_to_dict",
        "aggregated_metric_value_from_dict",
    ]
    for sym in expected_orch_symbols:
        assert hasattr(orch, sym), f"Symbol '{sym}' missing from experimental_ml.orchestration"
        assert sym in orch.__all__, f"Symbol '{sym}' missing from orchestration.__all__"

    # Stages exports
    expected_stages_symbols = [
        "verify_runs_gate",
        "EXECUTION_STATE_REL_PATH",
        "CELLS_DIR_REL_PATH",
        "PREDICTIONS_DIR_REL_PATH",
        "OOF_DIR_REL_PATH",
    ]
    for sym in expected_stages_symbols:
        assert hasattr(stages, sym), f"Symbol '{sym}' missing from experimental_ml.stages"
        assert sym in stages.__all__, f"Symbol '{sym}' missing from stages.__all__"


def test_m53_06_02_end_to_end_matrix_to_oof_gate(tmp_path: Path) -> None:
    """Proof C24: End-to-end matrix run -> auto OOF consolidation -> verify_runs_gate approval (ORCH-15 to ORCH-21)."""
    view = _build_dummy_view()
    obs = view.observation_ids
    f0 = FoldPartition(fold_index=0, train_ids=obs[10:], val_ids=obs[:10])
    f1 = FoldPartition(fold_index=1, train_ids=obs[:10], val_ids=obs[10:])

    plan = PartitionPlan(
        plan_id=PartitionPlanId("plan_oof_integ"),
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
        display_name="Mean Regressor",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Mean",
        scientific_justification="Baseline",
    )
    sc1 = FeatureScenario(
        scenario_id=ScenarioId("sc_all"),
        name="Scenario All",
        description="All features",
        scientific_justification="Full set",
        mode=ScenarioMode.FIXED,
        selected_features=("x1", "x2"),
    )

    run_dir = tmp_path / "runs"

    # Execute matrix (with auto_consolidate_oof=True)
    state = orch.run_experiment_matrix(
        model_specs=[m1],
        scenarios=[sc1],
        partition_plan=plan,
        sanitized_view=view,
        run_dir=run_dir,
        metrics=["rmse", "mae"],
        auto_consolidate_oof=True,
    )

    assert state.total_cells == 2
    assert state.completed_cells == 2
    assert state.failed_cells == 0

    # Verify OOF file was generated automatically
    oof_file = run_dir / "oof" / "oof_dummy_mean__sc_all.json"
    assert oof_file.exists()

    oof_record = orch.load_oof_predictions("dummy_mean", "sc_all", run_dir)
    assert len(oof_record.observation_ids) == 20
    assert oof_record.coverage == 1.0
    assert "rmse" in oof_record.pooled_metrics
    assert "rmse" in oof_record.aggregated_metrics

    # Verify verify_runs_gate validates and approves the run
    summary = stages.verify_runs_gate(run_dir)
    assert summary["status"] == "READY"
    assert summary["completed_cells"] == 2
    assert summary["failed_cells"] == 0
    assert summary["verified_configurations"] == ["dummy_mean__sc_all"]


def test_m53_06_03_runtime_purity_xcut_02() -> None:
    """Proof C25: Strict runtime purity - only standard library and numpy imported (XCUT-02)."""
    code = """
import sys
import experimental_ml.orchestration as orch
import experimental_ml.stages as stages

forbidden = {"pandas", "scipy", "sklearn", "pyarrow", "torch", "tensorflow"}
imported_forbidden = forbidden.intersection(sys.modules.keys())
if imported_forbidden:
    print(f"FORBIDDEN_MODULES_LOADED: {imported_forbidden}")
    sys.exit(1)
print("PURITY_VERIFIED")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, f"Runtime purity violation: {result.stdout}\n{result.stderr}"
    assert "PURITY_VERIFIED" in result.stdout
