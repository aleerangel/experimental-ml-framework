"""Unit tests for multiplicity adjustments and statistical comparisons orchestrator (STAT-08)."""

import pytest

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.statistics.multiplicity import (
    adjust_pvalues_bh,
    adjust_pvalues_holm,
)
from experimental_ml.statistics.comparisons import run_statistical_comparisons
from experimental_ml.statistics.suitability import evaluate_method_suitability
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    ComparisonScope,
    ComparisonSpec,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    IncompleteComparisonPolicy,
    MultiplicityMethod,
    PracticalRelevanceStatus,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def test_m62_04_holm_bonferroni_adjustment() -> None:
    """C12: Holm-Bonferroni step-down procedure preserves order, monotonicity, and ties."""
    # Example: p = [0.01, 0.04, 0.03, 0.005]
    # sorted: (0.005, idx 3), (0.01, idx 0), (0.03, idx 2), (0.04, idx 1)
    # m=4:
    # i=0: 4*0.005 = 0.02
    # i=1: max(0.02, 3*0.01) = 0.03
    # i=2: max(0.03, 2*0.03) = 0.06
    # i=3: max(0.06, 1*0.04) = 0.06 (monotone clamp!)
    adj = adjust_pvalues_holm([0.01, 0.04, 0.03, 0.005])
    assert adj == pytest.approx([0.03, 0.06, 0.06, 0.02], abs=1e-12)

    # Ties must receive identical adjusted p-values
    adj_ties = adjust_pvalues_holm([0.02, 0.02, 0.5])
    assert adj_ties[0] == pytest.approx(adj_ties[1], abs=1e-12)
    assert adj_ties[0] == pytest.approx(0.06, abs=1e-12)

    # Empty and single element
    assert adjust_pvalues_holm([]) == []
    assert adjust_pvalues_holm([0.03]) == pytest.approx([0.03])


def test_m62_04_benjamini_hochberg_adjustment() -> None:
    """C13: Benjamini-Hochberg step-up procedure preserves order, monotonicity, and ties."""
    # p = [0.01, 0.04, 0.03, 0.005]
    # sorted: 0.005 (1), 0.01 (2), 0.03 (3), 0.04 (4)
    # raw BH: 0.005*4/1=0.02, 0.01*4/2=0.02, 0.03*4/3=0.04, 0.04*4/4=0.04
    adj = adjust_pvalues_bh([0.01, 0.04, 0.03, 0.005])
    assert adj == pytest.approx([0.02, 0.04, 0.04, 0.02], abs=1e-12)

    # Step-up monotonicity & ties: p = [0.04, 0.03, 0.03]
    # sorted: 0.03 (1)->0.09, 0.03 (2)->0.045, 0.04 (3)->0.04
    # backward min: all become 0.04!
    adj_ties = adjust_pvalues_bh([0.04, 0.03, 0.03])
    assert adj_ties == pytest.approx([0.04, 0.04, 0.04], abs=1e-12)

    assert adjust_pvalues_bh([]) == []
    assert adjust_pvalues_bh([0.03]) == pytest.approx([0.03])


def test_m62_04_invalid_pvalues_raise() -> None:
    """C14: Out-of-range or non-finite p-values raise ContractViolationError."""
    for fn in (adjust_pvalues_holm, adjust_pvalues_bh):
        for bad in ([-0.01], [1.01], [float("nan")], [float("inf")]):
            with pytest.raises(ContractViolationError):
                fn(bad)


def _make_plan(regime: EvaluationRegime = EvaluationRegime.CV_ONLY, n_folds: int = 6) -> PartitionPlan:
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
    return PartitionPlan(
        plan_id="plan_m62",
        source_dataset_hash="hash_m62",
        regime=regime,
        strategy=PartitionStrategy.KFOLD if regime != EvaluationRegime.HOLDOUT_ONLY else PartitionStrategy.HOLDOUT,
        development_ids=tuple(ObservationId(f"d_{k}") for k in range(100)),
        holdout_ids=h_ids,
        folds=folds,
        config=PartitionConfig(
            strategy=PartitionStrategy.KFOLD if regime != EvaluationRegime.HOLDOUT_ONLY else PartitionStrategy.HOLDOUT,
            regime=regime,
            n_splits=n_folds,
            holdout_fraction=h_frac,
        ),
    )


def _make_metric(name: str, val: float, status: MetricStatus = MetricStatus.VALID) -> MetricValue:
    return MetricValue(
        metric_id=name,
        value=val,
        status=status,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=20,
    )


def _make_summary(
    model_id: str,
    scenario_id: str,
    rmse_vals: list[float | None],
    n_total: int = 6,
) -> ConfigurationSummary:
    completed_ids = tuple(f"fold_{i}" for i, v in enumerate(rmse_vals) if v is not None)
    failed_ids = tuple(f"fold_{i}" for i, v in enumerate(rmse_vals) if v is None)
    fold_metrics = {}
    for i, v in enumerate(rmse_vals):
        if v is None:
            continue
        status = MetricStatus.UNDEFINED_NAN if v != v else MetricStatus.VALID
        fold_metrics[f"fold_{i}"] = {"rmse": _make_metric("rmse", v, status)}
    cov = len(completed_ids) / n_total
    cov_status = (
        CoverageStatus.VALID
        if cov == 1.0
        else (CoverageStatus.NO_COVERAGE if cov == 0.0 else CoverageStatus.PARTIAL_COVERAGE)
    )
    return ConfigurationSummary(
        model_id=model_id,
        scenario_id=scenario_id,
        total_folds=n_total,
        completed_folds=len(completed_ids),
        failed_folds=len(failed_ids),
        cancelled_folds=0,
        coverage=cov,
        coverage_status=cov_status,
        completed_fold_ids=completed_ids,
        failed_fold_ids=failed_ids,
        cancelled_fold_ids=(),
        fold_metrics=fold_metrics,
        aggregated_metrics={
            "rmse": AggregatedMetricStats(
                n_valid=len(completed_ids),
                n_total=n_total,
                status=MetricStatus.VALID if len(completed_ids) == n_total else MetricStatus.UNDEFINED_NAN,
                mean=1.0,
                std=0.1,
                median=1.0,
                iqr=0.1,
                q25=0.95,
                q75=1.05,
                min_value=0.9,
                max_value=1.1,
            )
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )


def test_m62_04_orchestrator_scopes_nan_and_practical_relevance() -> None:
    """C15: Supports all 6 scopes, filters UNDEFINED_NAN metrics, evaluates Delta_min, adjusts per family."""
    plan = _make_plan(EvaluationRegime.CV_ONLY, n_folds=6)
    configs = {
        ("m1", "s1"): _make_summary("m1", "s1", [1.0, 1.1, 1.0, 1.05, 1.02, 1.03]),
        ("m2", "s1"): _make_summary("m2", "s1", [1.5, 1.6, 1.5, 1.55, 1.52, 1.53]),
        ("m1", "s2"): _make_summary("m1", "s2", [1.2, 1.3, float("nan"), 1.25, 1.22, 1.23]),
    }
    consol = DescriptiveConsolidation(
        experiment_id="exp_m62",
        partition_plan_id=plan.plan_id,
        total_configurations=len(configs),
        configurations=configs,
        timestamp_utc="2026-11-16T00:00:00Z",
    )
    suit = evaluate_method_suitability(plan, consol)

    # 1. MODELS_WITHIN_SCENARIO + practical threshold Delta_min = 0.2
    spec_m = ComparisonSpec(
        metrics_of_interest=("rmse",),
        metric_directions={"rmse": MetricDirection.MINIMIZE},
        comparison_scope=ComparisonScope.MODELS_WITHIN_SCENARIO,
        alpha=0.05,
        multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI,
        practical_relevance_thresholds={"rmse": 0.2},
    )
    bundle_m = run_statistical_comparisons(consol, plan, spec_m, suit)
    assert len(bundle_m.comparisons) == 1
    cmp0 = bundle_m.comparisons[0]
    assert cmp0.observed_better == ("m1", "s1")
    assert cmp0.practical_relevance == PracticalRelevanceStatus.STATISTICALLY_SIGNIFICANT_AND_PRACTICAL
    assert cmp0.nadeau_bengio_adjusted_p == pytest.approx(cmp0.nadeau_bengio.p_value)

    # 2. SCENARIOS_WITHIN_MODEL under STRICT_COMPLETE_ONLY skips ("m1","s1") vs ("m1","s2") due to NaN on fold_2
    spec_s = ComparisonSpec(
        metrics_of_interest=("rmse",),
        metric_directions={"rmse": MetricDirection.MINIMIZE},
        comparison_scope=ComparisonScope.SCENARIOS_WITHIN_MODEL,
    )
    bundle_s_strict = run_statistical_comparisons(
        consol, plan, spec_s, suit, policy=IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY
    )
    assert len(bundle_s_strict.comparisons) == 0
    assert len(bundle_s_strict.skipped_comparisons) == 1
    assert "UNDEFINED_NAN" in bundle_s_strict.skipped_comparisons[0].reason

    # Under ALLOW_COMMON_SUBSET, runs on the 5 valid shared folds
    bundle_s_common = run_statistical_comparisons(
        consol, plan, spec_s, suit, policy=IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET
    )
    assert len(bundle_s_common.comparisons) == 1
    assert len(bundle_s_common.comparisons[0].shared_fold_ids) == 5
    assert bundle_s_common.comparisons[0].is_conditional is True

    # 3. AGAINST_BASELINE, ALL_PAIRWISE, FULL_CONFIGURATIONS, PLANNED_HYPOTHESES
    for scope, extra in [
        (ComparisonScope.AGAINST_BASELINE, {"baseline_config": ("m1", "s1")}),
        (ComparisonScope.ALL_PAIRWISE, {}),
        (ComparisonScope.FULL_CONFIGURATIONS, {}),
        (ComparisonScope.PLANNED_HYPOTHESES, {"planned_pairs": ((("m1", "s1"), ("m2", "s1")),)}),
    ]:
        sp = ComparisonSpec(
            metrics_of_interest=("rmse",),
            metric_directions={"rmse": MetricDirection.MINIMIZE},
            comparison_scope=scope,
            multiplicity_method=MultiplicityMethod.BENJAMINI_HOCHBERG,
            **extra,
        )
        bd = run_statistical_comparisons(consol, plan, sp, suit)
        assert len(bd.comparisons) >= 1


def test_m62_04_holdout_protection_and_skipped_pairs() -> None:
    """C16: Blocks multi-fold tests on HOLDOUT_ONLY and isolates FINAL_HOLDOUT in CV_AND_HOLDOUT."""
    # HOLDOUT_ONLY (J=1)
    plan_ho = _make_plan(EvaluationRegime.HOLDOUT_ONLY, n_folds=1)
    configs_ho = {
        ("m1", "s1"): _make_summary("m1", "s1", [1.0], n_total=1),
        ("m2", "s1"): _make_summary("m2", "s1", [1.5], n_total=1),
    }
    consol_ho = DescriptiveConsolidation("exp", plan_ho.plan_id, 2, configs_ho, "2026-11-16T00:00:00Z")
    suit_ho = evaluate_method_suitability(plan_ho, consol_ho)
    spec = ComparisonSpec(
        metrics_of_interest=("rmse",),
        metric_directions={"rmse": MetricDirection.MINIMIZE},
        comparison_scope=ComparisonScope.ALL_PAIRWISE,
    )
    bundle_ho = run_statistical_comparisons(consol_ho, plan_ho, spec, suit_ho)
    assert bundle_ho.comparisons == ()
    assert len(bundle_ho.non_applicable_reasons) >= 1

    # CV_AND_HOLDOUT (J=6 development folds, holdout isolated)
    plan_both = _make_plan(EvaluationRegime.CV_AND_HOLDOUT, n_folds=6)
    configs_both = {
        ("m1", "s1"): _make_summary("m1", "s1", [1.0, 1.1, 1.0, 1.05, 1.02, 1.03]),
        ("m2", "s1"): _make_summary("m2", "s1", [1.5, 1.6, 1.5, 1.55, 1.52, 1.53]),
        ("m3", "s1"): _make_summary("m3", "s1", [None] * 6),  # NO_COVERAGE
    }
    consol_both = DescriptiveConsolidation("exp", plan_both.plan_id, 3, configs_both, "2026-11-16T00:00:00Z")
    suit_both = evaluate_method_suitability(plan_both, consol_both)
    bundle_both = run_statistical_comparisons(consol_both, plan_both, spec, suit_both)
    assert len(bundle_both.comparisons) == 1
    assert len(bundle_both.comparisons[0].shared_fold_ids) == 6
    assert len(bundle_both.skipped_comparisons) == 2
