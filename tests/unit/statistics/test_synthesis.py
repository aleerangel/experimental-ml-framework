"""Unit tests for StructuredConclusion synthesis (Submodule 5C, STAT-11, CA-E5-02)."""

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.statistics.comparisons import run_statistical_comparisons
from experimental_ml.statistics.multiobjective import compute_pareto_frontier
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


def _build_plan(regime: EvaluationRegime = EvaluationRegime.CV_ONLY, n_folds: int = 5) -> PartitionPlan:
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"tr_{i}_{k}") for k in range(80)),
            val_ids=tuple(ObservationId(f"va_{i}_{k}") for k in range(20)),
        )
        for i in range(n_folds)
    )
    h_ids = tuple(ObservationId(f"ho_{k}") for k in range(20)) if regime != EvaluationRegime.CV_ONLY else ()
    h_frac = 0.2 if regime != EvaluationRegime.CV_ONLY else None
    strat = PartitionStrategy.HOLDOUT if regime == EvaluationRegime.HOLDOUT_ONLY else PartitionStrategy.KFOLD
    return PartitionPlan(
        plan_id="pp_synth",
        source_dataset_hash="hash_synth",
        regime=regime,
        strategy=strat,
        development_ids=tuple(ObservationId(f"d_{k}") for k in range(100)),
        holdout_ids=h_ids,
        folds=folds,
        config=PartitionConfig(strategy=strat, regime=regime, n_splits=n_folds, holdout_fraction=h_frac),
    )


def _build_summary(model_id: str, vals: list[float], partial: bool = False) -> ConfigurationSummary:
    fold_metrics = {
        f"fold_{i}": {
            "rmse": MetricValue(
                metric_id="rmse",
                value=v,
                status=MetricStatus.VALID,
                direction=MetricDirection.MINIMIZE,
                scope=MetricEvaluationScope.PER_FOLD,
                n_samples=20,
            )
        }
        for i, v in enumerate(vals)
    }
    mean_v = sum(vals) / len(vals)
    return ConfigurationSummary(
        model_id=model_id,
        scenario_id="s1",
        total_folds=len(vals) + (1 if partial else 0),
        completed_folds=len(vals),
        failed_folds=1 if partial else 0,
        cancelled_folds=0,
        coverage=len(vals) / (len(vals) + (1 if partial else 0)),
        coverage_status=CoverageStatus.PARTIAL_COVERAGE if partial else CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(len(vals))),
        failed_fold_ids=("fold_missing",) if partial else (),
        cancelled_fold_ids=(),
        fold_metrics=fold_metrics,
        aggregated_metrics={
            "rmse": AggregatedMetricStats(
                n_valid=len(vals),
                n_total=len(vals) + (1 if partial else 0),
                status=MetricStatus.VALID,
                mean=mean_v,
                std=0.05,
                median=mean_v,
                iqr=0.02,
                q25=mean_v - 0.01,
                q75=mean_v + 0.01,
                min_value=min(vals),
                max_value=max(vals),
            )
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )


def test_m63_03_numeric_traceability_in_narrative() -> None:
    """C8: StructuredConclusion references exact 5A/5B numbers and Pareto frontier in narrative."""
    plan = _build_plan(EvaluationRegime.CV_ONLY, n_folds=6)
    configs = {
        ("m1", "s1"): _build_summary("m1", [1.0, 1.02, 0.98, 1.01, 0.99, 1.0]),
        ("m2", "s1"): _build_summary("m2", [1.5, 1.52, 1.48, 1.51, 1.49, 1.5]),
    }
    consol = DescriptiveConsolidation("exp_s", plan.plan_id, 2, configs, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(
        metrics_of_interest=("rmse",),
        metric_directions={"rmse": MetricDirection.MINIMIZE},
        comparison_scope=ComparisonScope.ALL_PAIRWISE,
        multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI,
        practical_relevance_thresholds={"rmse": 0.2},
    )
    bundle = run_statistical_comparisons(consol, plan, spec, suit)
    pareto = compute_pareto_frontier(
        consol, MultiObjectiveSpec((ObjectiveSpec("rmse", MetricDirection.MINIMIZE),))
    )

    conc = synthesize_conclusions(
        consol, suit, bundle, primary_metric="rmse", primary_direction=MetricDirection.MINIMIZE, multi_objective_summary=pareto
    )
    assert conc.observed_leader == ("m1", "s1")
    assert "m1" in conc.narrative_text and "1.0000" in conc.narrative_text
    assert "p_adj" in conc.narrative_text
    assert "d_z" in conc.narrative_text
    assert "Pareto" in conc.cost_tradeoff_summary


def test_m63_03_no_equivalence_from_nonsignificance() -> None:
    """C9: Never declares equivalence when p_adj >= alpha."""
    plan = _build_plan(EvaluationRegime.CV_ONLY, n_folds=5)
    configs = {
        ("m1", "s1"): _build_summary("m1", [1.0, 1.1, 0.9, 1.2, 0.8]),
        ("m2", "s1"): _build_summary("m2", [1.05, 1.08, 0.95, 1.15, 0.85]),
    }
    consol = DescriptiveConsolidation("exp_ns", plan.plan_id, 2, configs, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(
        metrics_of_interest=("rmse",),
        metric_directions={"rmse": MetricDirection.MINIMIZE},
        comparison_scope=ComparisonScope.ALL_PAIRWISE,
    )
    bundle = run_statistical_comparisons(consol, plan, spec, suit)
    conc = synthesize_conclusions(consol, suit, bundle, "rmse", MetricDirection.MINIMIZE)

    lower_narr = conc.narrative_text.lower()
    assert "insufficient" in lower_narr or "inconclusive" in lower_narr
    assert "are equivalent" not in lower_narr
    assert "equivalence proven" not in lower_narr


def test_m63_03_preserves_methodological_caveats() -> None:
    """C10: Preserves HOLDOUT_ONLY and partial coverage caveats in methodological_caveats and narrative."""
    plan = _build_plan(EvaluationRegime.HOLDOUT_ONLY, n_folds=1)
    configs = {
        ("m1", "s1"): _build_summary("m1", [1.0], partial=True),
        ("m2", "s1"): _build_summary("m2", [1.2]),
    }
    consol = DescriptiveConsolidation("exp_ho", plan.plan_id, 2, configs, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(
        metrics_of_interest=("rmse",),
        metric_directions={"rmse": MetricDirection.MINIMIZE},
        comparison_scope=ComparisonScope.ALL_PAIRWISE,
    )
    bundle = run_statistical_comparisons(consol, plan, spec, suit)
    conc = synthesize_conclusions(consol, suit, bundle, "rmse", MetricDirection.MINIMIZE)

    assert len(conc.methodological_caveats) >= 1
    assert any("HOLDOUT" in c.upper() or "J = 1" in c for c in conc.methodological_caveats)
    assert any("PARTIAL_COVERAGE" in c for c in conc.methodological_caveats)
    assert "Caveats" in conc.narrative_text or "caveats" in conc.narrative_text.lower()
