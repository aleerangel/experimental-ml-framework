"""Unit tests for Stage 5 statistics atomic persistence and roundtrip codecs (STAT-12)."""

import math
from pathlib import Path
import pytest

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.statistics.comparisons import run_statistical_comparisons
from experimental_ml.statistics.multiobjective import compute_pareto_frontier
from experimental_ml.statistics.storage import (
    load_statistics_artifacts,
    save_statistics_artifacts,
)
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
        plan_id="pp_store",
        source_dataset_hash="hash_store",
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

    # Include constant non-zero diff (t_stat = -inf) and an UNDEFINED_NAN metric
    m1_folds = {
        f"fold_{i}": {
            "rmse": MetricValue("rmse", 1.0, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 20),
            "r2": MetricValue("r2", float("nan"), MetricStatus.UNDEFINED_NAN, MetricDirection.MAXIMIZE, MetricEvaluationScope.PER_FOLD, 20),
        }
        for i in range(n_folds)
    }
    m2_folds = {
        f"fold_{i}": {
            "rmse": MetricValue("rmse", 1.5, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 20),
            "r2": MetricValue("r2", 0.7, MetricStatus.VALID, MetricDirection.MAXIMIZE, MetricEvaluationScope.PER_FOLD, 20),
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
            "r2": AggregatedMetricStats(0, 5, MetricStatus.UNDEFINED_NAN, None, None, None, None, None, None, None, None),
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
            "r2": AggregatedMetricStats(5, 5, MetricStatus.VALID, 0.7, 0.0, 0.7, 0.0, 0.7, 0.7, 0.7, 0.7),
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    consol = DescriptiveConsolidation("exp_store", plan.plan_id, 2, {("m1", "s1"): sum1, ("m2", "s1"): sum2}, "2026-11-16T00:00:00Z")
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


def test_m64_01_atomic_save_creates_all_files(tmp_path: Path) -> None:
    """C1: save_statistics_artifacts writes all required JSON files and optional pareto_summary.json."""
    consol, suit, comp, conc, pareto = _sample_artifacts()
    stats_dir = tmp_path / "statistics"
    save_statistics_artifacts(stats_dir, consol, suit, comp, conc, pareto=pareto)

    for fname in (
        "descriptive_consolidation.json",
        "method_suitability.json",
        "statistical_comparisons.json",
        "pareto_summary.json",
        "structured_conclusion.json",
        "statistics_manifest.json",
    ):
        assert (stats_dir / fname).is_file(), f"Missing {fname}"


def test_m64_01_no_overwrite_protection(tmp_path: Path) -> None:
    """C2: Rejects overwriting existing artifacts when force=False."""
    consol, suit, comp, conc, pareto = _sample_artifacts()
    stats_dir = tmp_path / "statistics"
    save_statistics_artifacts(stats_dir, consol, suit, comp, conc, pareto=pareto)

    with pytest.raises(ContractViolationError):
        save_statistics_artifacts(stats_dir, consol, suit, comp, conc, pareto=pareto, force=False)

    # With force=True succeeds
    save_statistics_artifacts(stats_dir, consol, suit, comp, conc, pareto=pareto, force=True)


def test_m64_01_roundtrip_fidelity_with_nonfinite(tmp_path: Path) -> None:
    """C3: Roundtrip load preserves enums, tuple keys, NaN, and +/-Inf accurately."""
    consol, suit, comp, conc, pareto = _sample_artifacts()
    stats_dir = tmp_path / "statistics"
    save_statistics_artifacts(stats_dir, consol, suit, comp, conc, pareto=pareto)

    loaded = load_statistics_artifacts(stats_dir)
    assert loaded.consolidation.experiment_id == consol.experiment_id
    assert loaded.consolidation.partition_plan_id == consol.partition_plan_id
    assert set(loaded.consolidation.configurations.keys()) == {("m1", "s1"), ("m2", "s1")}

    # NaN preserved in fold_metrics
    r2_mv = loaded.consolidation.configurations[("m1", "s1")].fold_metrics["fold_0"]["r2"]
    assert r2_mv.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(r2_mv.value)

    # -Inf preserved in Nadeau-Bengio & Cohen's d for constant diff
    loaded_cmp = loaded.comparisons.comparisons[0]
    assert math.isinf(loaded_cmp.nadeau_bengio.t_statistic) and loaded_cmp.nadeau_bengio.t_statistic < 0
    assert math.isinf(loaded_cmp.effect_size.cohens_d) and loaded_cmp.effect_size.cohens_d < 0
    assert loaded.conclusion == conc
    assert loaded.pareto is not None and len(loaded.pareto.pareto_frontier) == 1
