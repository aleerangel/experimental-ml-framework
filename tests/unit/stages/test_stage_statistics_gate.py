"""Unit tests for Stage 5 verify_statistics_gate (STAT-13, CA-GER-01)."""

from pathlib import Path
import pytest

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.stages.stage_gates import verify_statistics_gate
from experimental_ml.statistics.comparisons import run_statistical_comparisons
from experimental_ml.statistics.multiobjective import compute_pareto_frontier
from experimental_ml.statistics.storage import save_statistics_artifacts
from experimental_ml.statistics.suitability import evaluate_method_suitability
from experimental_ml.statistics.synthesis import synthesize_conclusions
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    ComparisonScope,
    ComparisonSpec,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    MultiObjectiveSpec,
    MultiplicityMethod,
    ObjectiveSpec,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _sample_artifacts():
    n_folds = 5
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"tr_{i}_{k}") for k in range(80)),
            val_ids=tuple(ObservationId(f"va_{i}_{k}") for k in range(20)),
        )
        for i in range(n_folds)
    )
    plan = PartitionPlan(
        plan_id="pp_gate",
        source_dataset_hash="hash_gate",
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=tuple(ObservationId(f"d_{k}") for k in range(100)),
        holdout_ids=(),
        folds=folds,
        config=PartitionConfig(
            strategy=PartitionStrategy.KFOLD,
            regime=EvaluationRegime.CV_ONLY,
            n_splits=n_folds,
        ),
    )
    m1_folds = {
        f"fold_{i}": {
            "rmse": MetricValue("rmse", 1.0, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 20),
        }
        for i in range(n_folds)
    }
    m2_folds = {
        f"fold_{i}": {
            "rmse": MetricValue("rmse", 1.5, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 20),
        }
        for i in range(n_folds)
    }
    sum1 = ConfigurationSummary(
        model_id="m1",
        scenario_id="s1",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(5)),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics=m1_folds,
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0),
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    sum2 = ConfigurationSummary(
        model_id="m2",
        scenario_id="s1",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(5)),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics=m2_folds,
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.5, 0.0, 1.5, 0.0, 1.5, 1.5, 1.5, 1.5),
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    consol = DescriptiveConsolidation("exp_gate", plan.plan_id, 2, {("m1", "s1"): sum1, ("m2", "s1"): sum2}, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(
        metrics_of_interest=("rmse",),
        metric_directions={"rmse": MetricDirection.MINIMIZE},
        comparison_scope=ComparisonScope.ALL_PAIRWISE,
        multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI,
    )
    comp = run_statistical_comparisons(consol, plan, spec, suit)
    pareto = compute_pareto_frontier(consol, MultiObjectiveSpec((ObjectiveSpec("rmse", MetricDirection.MINIMIZE),)))
    conc = synthesize_conclusions(consol, suit, comp, "rmse", MetricDirection.MINIMIZE, pareto)
    return consol, suit, comp, conc, pareto


def test_m64_02_missing_or_corrupt_raises(tmp_path: Path) -> None:
    """C4: Raises DataIntegrityError when any required Stage 5 artifact is missing or corrupt."""
    with pytest.raises(DataIntegrityError):
        verify_statistics_gate(tmp_path)

    consol, suit, comp, conc, pareto = _sample_artifacts()
    stats_dir = tmp_path / "statistics"
    save_statistics_artifacts(stats_dir, consol, suit, comp, conc, pareto=pareto)

    (stats_dir / "structured_conclusion.json").write_text("{bad json", encoding="utf-8")
    with pytest.raises(DataIntegrityError):
        verify_statistics_gate(tmp_path)


def test_m64_02_partition_plan_mismatch_raises(tmp_path: Path) -> None:
    """C5: Raises DataIntegrityError when partition_plan_id diverges from upstream PartitionPlan."""
    consol, suit, comp, conc, pareto = _sample_artifacts()
    stats_dir = tmp_path / "statistics"
    save_statistics_artifacts(stats_dir, consol, suit, comp, conc, pareto=pareto)

    part_dir = tmp_path / "partitions"
    part_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(part_dir / "partition_plan.json", {"plan_id": "different_plan_id"}, overwrite=True)

    with pytest.raises(DataIntegrityError):
        verify_statistics_gate(tmp_path)


def test_m64_02_valid_gate_returns_summary(tmp_path: Path) -> None:
    """C6: Returns structured verification summary dict when Stage 5 artifacts and lineage are valid."""
    consol, suit, comp, conc, pareto = _sample_artifacts()
    stats_dir = tmp_path / "statistics"
    save_statistics_artifacts(stats_dir, consol, suit, comp, conc, pareto=pareto)

    summary = verify_statistics_gate(tmp_path)
    assert summary["status"] == "VERIFIED"
    assert summary["experiment_id"] == consol.experiment_id
    assert summary["partition_plan_id"] == consol.partition_plan_id
    assert summary["total_configurations"] == 2
    assert summary["total_comparisons"] == 1
    assert summary["has_pareto_summary"] is True
