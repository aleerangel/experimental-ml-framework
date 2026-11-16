"""Unit tests for expml stats CLI subcommands (STAT-14, CLI-06 to CLI-11)."""

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
from experimental_ml.validation.codecs import partition_plan_to_dict
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _populate_stage4_experiment(exp_dir: Path) -> None:
    n_folds = 5
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"obs_{k:03d}") for k in range(20) if k % n_folds != i),
            val_ids=tuple(ObservationId(f"obs_{k:03d}") for k in range(20) if k % n_folds == i),
        )
        for i in range(n_folds)
    )
    plan = PartitionPlan(
        plan_id="pp_cli_stats",
        source_dataset_hash="a" * 64,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=tuple(ObservationId(f"obs_{k:03d}") for k in range(20)),
        holdout_ids=(),
        folds=folds,
        config=PartitionConfig(
            strategy=PartitionStrategy.KFOLD,
            regime=EvaluationRegime.CV_ONLY,
            n_splits=n_folds,
        ),
    )
    part_dir = exp_dir / "partitions"
    part_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(part_dir / "partition_plan.json", partition_plan_to_dict(plan), overwrite=True)

    run_dir = exp_dir / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    timing = TimingBreakdown(0.01, 0.0, 0.0, 0.01, 0.05, 0.01, 0.01, 0.09)

    cell_statuses: dict[str, ExecutionStatus] = {}
    for model_id, base_err in [("m_fast", 1.2), ("m_best", 0.8)]:
        preds_all: list[PredictionRecord] = []
        cells_all: list[CellResultRecord] = []
        for i in range(n_folds):
            cid = f"{model_id}__sc1__fold_{i}"
            cell_statuses[cid] = ExecutionStatus.COMPLETED
            cell = CellResultRecord(
                cell_id=cid,
                experiment_id="exp_cli_stats",
                partition_plan_id=plan.plan_id,
                model_id=model_id,
                scenario_id="sc1",
                fold_id=f"fold_{i}",
                status=ExecutionStatus.COMPLETED,
                metrics={
                    "rmse": MetricValue(
                        "rmse",
                        base_err + 0.02 * i,
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
        experiment_id="exp_cli_stats",
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


def test_m64_03_cli_stats_run_success(tmp_path: Path, capsys) -> None:
    """C7: expml stats run executes Stage 5, persists statistics/, suppresses raw hashes, exits 0."""
    _populate_stage4_experiment(tmp_path)
    rc = main(["stats", "run", "--experiment-dir", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "m_best" in out
    assert "a" * 64 not in out  # CLI-11: raw SHA-256 hash suppressed
    assert (tmp_path / "statistics" / "statistics_manifest.json").is_file()


def test_m64_03_cli_stats_status(tmp_path: Path, capsys) -> None:
    """C8: expml stats status displays summary (exit 0) or returns 2 when missing."""
    rc_missing = main(["stats", "status", "--experiment-dir", str(tmp_path)])
    assert rc_missing == 2

    _populate_stage4_experiment(tmp_path)
    assert main(["stats", "run", "--experiment-dir", str(tmp_path)]) == 0
    capsys.readouterr()

    rc_ok = main(["stats", "status", "--experiment-dir", str(tmp_path)])
    assert rc_ok == 0
    out = capsys.readouterr().out
    assert "m_best" in out
    assert "VERIFIED" in out or "comparisons" in out.lower()


def test_m64_03_cli_stats_verify(tmp_path: Path) -> None:
    """C9: expml stats verify returns 0 on valid Stage 5 and 2 without traceback on failure."""
    rc_fail = main(["stats", "verify", "--experiment-dir", str(tmp_path)])
    assert rc_fail == 2

    _populate_stage4_experiment(tmp_path)
    assert main(["stats", "run", "--experiment-dir", str(tmp_path)]) == 0
    rc_ok = main(["stats", "verify", "--experiment-dir", str(tmp_path)])
    assert rc_ok == 0


def test_m64_03_cli_lazy_imports_purity() -> None:
    """C10: Importing cli.main and cli.cmd_stats does not eagerly load heavy statistics modules."""
    code = (
        "import sys; "
        "import experimental_ml.cli.main; "
        "import experimental_ml.cli.cmd_stats; "
        "assert 'experimental_ml.statistics.inference' not in sys.modules; "
        "assert 'experimental_ml.statistics.comparisons' not in sys.modules; "
        "assert 'numpy' not in sys.modules"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, f"Lazy import check failed: {proc.stderr}"
