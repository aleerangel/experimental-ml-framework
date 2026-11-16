"""End-to-end integration tests for M6.4 persistence, stage gate, CLI, and runtime purity (XCUT-02)."""

from pathlib import Path
import subprocess
import sys

from experimental_ml.cli.main import main
from experimental_ml.core.enums import ExecutionStatus, MetricStatus, TaskType
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.orchestration.oof import consolidate_oof_predictions, save_oof_predictions
from experimental_ml.orchestration.state import MatrixExecutionState, save_execution_state
from experimental_ml.orchestration.storage import save_cell_artifacts
from experimental_ml.orchestration.types import CellResultRecord, PredictionRecord, TimingBreakdown
from experimental_ml.stages.stage_gates import verify_statistics_gate
from experimental_ml.statistics import (
    LoadedStatisticsArtifacts,
    load_statistics_artifacts,
    save_statistics_artifacts,
)
from experimental_ml.validation.codecs import partition_plan_to_dict
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def test_m64_cli_end_to_end_pipeline(tmp_path: Path) -> None:
    """C11: Complete CLI pipeline Stage 4 -> expml stats run -> load_statistics_artifacts -> expml stats verify."""
    n_folds = 6
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"obs_{k:03d}") for k in range(24) if k % n_folds != i),
            val_ids=tuple(ObservationId(f"obs_{k:03d}") for k in range(24) if k % n_folds == i),
        )
        for i in range(n_folds)
    )
    plan = PartitionPlan(
        plan_id="pp_int_m64",
        source_dataset_hash="b" * 64,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=tuple(ObservationId(f"obs_{k:03d}") for k in range(24)),
        holdout_ids=(),
        folds=folds,
        config=PartitionConfig(
            strategy=PartitionStrategy.KFOLD,
            regime=EvaluationRegime.CV_ONLY,
            n_splits=n_folds,
        ),
    )
    part_dir = tmp_path / "partitions"
    part_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(part_dir / "partition_plan.json", partition_plan_to_dict(plan), overwrite=True)

    run_dir = tmp_path / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    timing = TimingBreakdown(0.01, 0.0, 0.0, 0.01, 0.05, 0.01, 0.01, 0.09)

    cell_statuses: dict[str, ExecutionStatus] = {}
    for model_id, base_err in [("m_a", 0.5), ("m_b", 1.1)]:
        preds_all: list[PredictionRecord] = []
        cells_all: list[CellResultRecord] = []
        for i in range(n_folds):
            cid = f"{model_id}__sc1__fold_{i}"
            cell_statuses[cid] = ExecutionStatus.COMPLETED
            cell = CellResultRecord(
                cell_id=cid,
                experiment_id="exp_int_m64",
                partition_plan_id=plan.plan_id,
                model_id=model_id,
                scenario_id="sc1",
                fold_id=f"fold_{i}",
                status=ExecutionStatus.COMPLETED,
                metrics={
                    "rmse": MetricValue(
                        "rmse",
                        base_err + 0.01 * i,
                        MetricStatus.VALID,
                        MetricDirection.MINIMIZE,
                        MetricEvaluationScope.PER_FOLD,
                        4,
                    )
                },
                timing=timing,
                selected_features=("f1",),
            )
            cells_all.append(cell)
            pred = PredictionRecord(
                cell_id=cid,
                observation_ids=folds[i].val_ids,
                y_true=(1.0,) * len(folds[i].val_ids),
                y_pred=(1.0 + base_err,) * len(folds[i].val_ids),
            )
            preds_all.append(pred)
            save_cell_artifacts(cell, pred, run_dir, overwrite=True)

        oof = consolidate_oof_predictions(
            model_id=model_id,
            scenario_id="sc1",
            task_type=TaskType.REGRESSION,
            prediction_records=preds_all,
            cell_results=cells_all,
        )
        save_oof_predictions(oof, run_dir, overwrite=True)

    state = MatrixExecutionState(
        experiment_id="exp_int_m64",
        run_id="run_001",
        created_at="2026-11-16T00:00:00Z",
        updated_at="2026-11-16T00:01:00Z",
        master_seed=42,
        total_cells=len(cell_statuses),
        cell_statuses=cell_statuses,
        source_dataset_hash=plan.source_dataset_hash,
        partition_plan_id=plan.plan_id,
        completed_cells=len(cell_statuses),
        failed_cells=0,
        cancelled_cells=0,
    )
    save_execution_state(state, run_dir, overwrite=True)

    assert main(["stats", "run", "--experiment-dir", str(tmp_path)]) == 0
    assert main(["stats", "verify", "--experiment-dir", str(tmp_path)]) == 0

    loaded = load_statistics_artifacts(tmp_path / "statistics")
    assert isinstance(loaded, LoadedStatisticsArtifacts)
    assert loaded.conclusion.observed_leader == ("m_a", "sc1")
    summary = verify_statistics_gate(tmp_path)
    assert summary["status"] == "VERIFIED"
    assert save_statistics_artifacts is not None


def test_m64_runtime_purity_xcut02() -> None:
    """C12: Stage 5 persistence, gate, and CLI run purely without SciPy (XCUT-02)."""
    code = (
        "import sys; "
        "sys.modules['scipy'] = None; "
        "from experimental_ml.statistics import save_statistics_artifacts, load_statistics_artifacts; "
        "from experimental_ml.stages.stage_gates import verify_statistics_gate; "
        "from experimental_ml.cli.main import build_parser; "
        "p = build_parser(); "
        "assert p is not None and sys.modules['scipy'] is None"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, f"Purity check failed: {proc.stderr}"
