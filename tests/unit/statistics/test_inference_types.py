"""Unit tests for M6.2 statistical inference types, specs, and immutability (STAT-05)."""

from dataclasses import FrozenInstanceError
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.metrics.types import MetricDirection
from experimental_ml.statistics.types import (
    ComparisonScope,
    ComparisonSpec,
    EffectSizeMagnitude,
    EffectSizeResult,
    MultiplicityMethod,
    NadeauBengioResult,
    PairwiseComparisonResult,
    PracticalRelevanceStatus,
    SkippedComparison,
    StatisticalComparisonBundle,
    WilcoxonResult,
)


def test_m62_01_enums_values() -> None:
    """C1: Canonical enum values for ComparisonScope, MultiplicityMethod, EffectSizeMagnitude, PracticalRelevanceStatus."""
    assert set(ComparisonScope) == {
        ComparisonScope.MODELS_WITHIN_SCENARIO,
        ComparisonScope.SCENARIOS_WITHIN_MODEL,
        ComparisonScope.FULL_CONFIGURATIONS,
        ComparisonScope.AGAINST_BASELINE,
        ComparisonScope.ALL_PAIRWISE,
        ComparisonScope.PLANNED_HYPOTHESES,
    }
    assert set(MultiplicityMethod) == {
        MultiplicityMethod.NONE,
        MultiplicityMethod.HOLM_BONFERRONI,
        MultiplicityMethod.BENJAMINI_HOCHBERG,
    }
    assert set(EffectSizeMagnitude) == {
        EffectSizeMagnitude.NEGLIGIBLE,
        EffectSizeMagnitude.SMALL,
        EffectSizeMagnitude.MEDIUM,
        EffectSizeMagnitude.LARGE,
    }
    assert set(PracticalRelevanceStatus) == {
        PracticalRelevanceStatus.NOT_CONFIGURED,
        PracticalRelevanceStatus.STATISTICALLY_SIGNIFICANT_AND_PRACTICAL,
        PracticalRelevanceStatus.STATISTICALLY_SIGNIFICANT_NOT_PRACTICAL,
        PracticalRelevanceStatus.PRACTICAL_NOT_STATISTICALLY_SIGNIFICANT,
        PracticalRelevanceStatus.INCONCLUSIVE,
        PracticalRelevanceStatus.EVIDENCE_OF_EQUIVALENCE,
    }


def test_m62_01_comparison_spec_validation() -> None:
    """C2: ComparisonSpec validates scope prerequisites, directions, alpha, and thresholds."""
    spec = ComparisonSpec(
        metrics_of_interest=("rmse", "r2"),
        metric_directions={
            "rmse": MetricDirection.MINIMIZE,
            "r2": MetricDirection.MAXIMIZE,
        },
        comparison_scope=ComparisonScope.ALL_PAIRWISE,
        alpha=0.05,
        multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI,
        practical_relevance_thresholds={"rmse": 0.1},
    )
    assert spec.metrics_of_interest == ("rmse", "r2")
    assert spec.alpha == 0.05

    # Empty metrics_of_interest rejected
    with pytest.raises(ConfigurationError):
        ComparisonSpec(
            metrics_of_interest=(),
            metric_directions={"rmse": MetricDirection.MINIMIZE},
            comparison_scope=ComparisonScope.ALL_PAIRWISE,
        )

    # Missing metric direction rejected
    with pytest.raises(ConfigurationError):
        ComparisonSpec(
            metrics_of_interest=("rmse", "r2"),
            metric_directions={"rmse": MetricDirection.MINIMIZE},
            comparison_scope=ComparisonScope.ALL_PAIRWISE,
        )

    # Invalid alpha rejected
    for bad_alpha in (0.0, 1.0, -0.05, 1.5, float("nan")):
        with pytest.raises(ConfigurationError):
            ComparisonSpec(
                metrics_of_interest=("rmse",),
                metric_directions={"rmse": MetricDirection.MINIMIZE},
                comparison_scope=ComparisonScope.ALL_PAIRWISE,
                alpha=bad_alpha,
            )

    # AGAINST_BASELINE requires baseline_config
    with pytest.raises(ConfigurationError):
        ComparisonSpec(
            metrics_of_interest=("rmse",),
            metric_directions={"rmse": MetricDirection.MINIMIZE},
            comparison_scope=ComparisonScope.AGAINST_BASELINE,
        )

    # PLANNED_HYPOTHESES requires planned_pairs
    with pytest.raises(ConfigurationError):
        ComparisonSpec(
            metrics_of_interest=("rmse",),
            metric_directions={"rmse": MetricDirection.MINIMIZE},
            comparison_scope=ComparisonScope.PLANNED_HYPOTHESES,
        )

    # Negative practical threshold rejected
    with pytest.raises(ConfigurationError):
        ComparisonSpec(
            metrics_of_interest=("rmse",),
            metric_directions={"rmse": MetricDirection.MINIMIZE},
            comparison_scope=ComparisonScope.ALL_PAIRWISE,
            practical_relevance_thresholds={"rmse": -0.5},
        )


def test_m62_01_frozen_immutability() -> None:
    """C3: All M6.2 result dataclasses are frozen and raise FrozenInstanceError on mutation."""
    spec = ComparisonSpec(
        metrics_of_interest=("rmse",),
        metric_directions={"rmse": MetricDirection.MINIMIZE},
        comparison_scope=ComparisonScope.ALL_PAIRWISE,
    )
    nb = NadeauBengioResult(
        mean_difference=-0.2,
        std_difference=0.1,
        corrected_variance=0.005,
        corrected_se=0.0707,
        t_statistic=-2.828,
        degrees_of_freedom=4,
        p_value=0.047,
        confidence_interval=(-0.396, -0.004),
        alpha=0.05,
        mean_train_val_ratio=0.25,
        fold_size_cv=0.0,
        warnings=(),
    )
    wx = WilcoxonResult(
        statistic=0.0,
        w_plus=0.0,
        w_minus=15.0,
        n_total=5,
        n_effective=5,
        zero_method="wilcox",
        p_value=0.0625,
        is_exact=True,
        warnings=("J < 6",),
    )
    es = EffectSizeResult(
        cohens_d=-2.0,
        magnitude=EffectSizeMagnitude.LARGE,
        confidence_interval=(-3.5, -0.5),
        alpha=0.05,
        warnings=("Unadjusted for CV overlap",),
    )
    pw = PairwiseComparisonResult(
        comparison_id="cmp_001",
        family_id="rmse",
        metric_name="rmse",
        direction=MetricDirection.MINIMIZE,
        config_a=("m1", "s1"),
        config_b=("m2", "s1"),
        shared_fold_ids=("f0", "f1", "f2", "f3", "f4"),
        observed_mean_a=1.0,
        observed_mean_b=1.2,
        observed_difference=-0.2,
        observed_better=("m1", "s1"),
        nadeau_bengio=nb,
        wilcoxon=wx,
        effect_size=es,
        nadeau_bengio_adjusted_p=0.047,
        wilcoxon_adjusted_p=0.0625,
        practical_relevance=PracticalRelevanceStatus.NOT_CONFIGURED,
        is_conditional=False,
        warnings=(),
    )
    skip = SkippedComparison(
        config_a=("m1", "s1"),
        config_b=("m3", "s1"),
        metric_name="rmse",
        reason="Insufficient shared folds",
    )
    bundle = StatisticalComparisonBundle(
        experiment_id="exp_01",
        partition_plan_id="pp_01",
        comparison_spec=spec,
        comparisons=(pw,),
        skipped_comparisons=(skip,),
        non_applicable_reasons=(),
        warnings=(),
    )

    for obj, attr, val in [
        (spec, "alpha", 0.01),
        (nb, "p_value", 0.5),
        (wx, "p_value", 0.5),
        (es, "cohens_d", 0.0),
        (pw, "nadeau_bengio_adjusted_p", 0.9),
        (skip, "reason", "other"),
        (bundle, "experiment_id", "exp_02"),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, attr, val)  # type: ignore[misc]
