"""Unit tests for methodological suitability evaluation and comparison eligibility (STAT-04, CA-E5-01)."""

import pytest

from experimental_ml.core.types import ObservationId
from experimental_ml.statistics.types import (
    ApplicabilityStatus,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    IncompleteComparisonPolicy,
)
from experimental_ml.statistics.suitability import (
    check_pairwise_comparison_eligibility,
    evaluate_method_suitability,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _make_partition_plan(
    regime: EvaluationRegime = EvaluationRegime.CV_ONLY,
    n_folds: int = 5,
    train_size: int = 80,
    val_size: int = 20,
    holdout_size: int = 0,
    strategy: PartitionStrategy = PartitionStrategy.KFOLD,
) -> PartitionPlan:
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"tr_{i}_{k}") for k in range(train_size)),
            val_ids=tuple(ObservationId(f"val_{i}_{k}") for k in range(val_size)),
        )
        for i in range(n_folds)
    )
    holdout_ids = tuple(ObservationId(f"hold_{k}") for k in range(holdout_size))
    dev_ids = tuple(ObservationId(f"dev_{k}") for k in range(train_size + val_size))
    h_frac = 0.2 if regime in (EvaluationRegime.HOLDOUT_ONLY, EvaluationRegime.CV_AND_HOLDOUT) else None
    return PartitionPlan(
        plan_id="plan_test_01",
        source_dataset_hash="hash123",
        regime=regime,
        strategy=strategy,
        development_ids=dev_ids,
        holdout_ids=holdout_ids,
        folds=folds,
        config=PartitionConfig(
            strategy=strategy,
            n_splits=n_folds,
            regime=regime,
            holdout_fraction=h_frac,
        ),
    )


def _make_config_summary(
    model_id: str = "ridge",
    scenario_id: str = "sc1",
    completed_ids: tuple[str, ...] = ("fold_0", "fold_1", "fold_2", "fold_3", "fold_4"),
    failed_ids: tuple[str, ...] = (),
    cancelled_ids: tuple[str, ...] = (),
    total_folds: int = 5,
) -> ConfigurationSummary:
    k_comp = len(completed_ids)
    cov = float(k_comp / total_folds) if total_folds > 0 else 0.0
    if cov >= 1.0:
        cov_status = CoverageStatus.VALID
    elif cov > 0.0:
        cov_status = CoverageStatus.PARTIAL_COVERAGE
    else:
        cov_status = CoverageStatus.NO_COVERAGE

    return ConfigurationSummary(
        model_id=model_id,
        scenario_id=scenario_id,
        total_folds=total_folds,
        completed_folds=k_comp,
        failed_folds=len(failed_ids),
        cancelled_folds=len(cancelled_ids),
        coverage=cov,
        coverage_status=cov_status,
        completed_fold_ids=completed_ids,
        failed_fold_ids=failed_ids,
        cancelled_fold_ids=cancelled_ids,
        fold_metrics={},
        aggregated_metrics={},
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )


def test_evaluate_method_suitability_extracts_regime_and_ratios() -> None:
    """C21: evaluate_method_suitability extracts evaluation regime, development folds J, fold ratios r_j, and mean ratio r (STAT-04, AC-M61-04-01)."""
    # 5 folds: 80 train, 20 val -> r_j = 20/80 = 0.25
    plan = _make_partition_plan(n_folds=5, train_size=80, val_size=20)
    report = evaluate_method_suitability(plan)

    assert report.evaluation_regime == EvaluationRegime.CV_ONLY
    assert report.total_development_partitions == 5
    assert len(report.fold_ratios) == 5
    assert all(r == pytest.approx(0.25) for r in report.fold_ratios)
    assert report.mean_train_overlap_ratio == pytest.approx(0.25)
    assert report.is_cross_validation is True


def test_evaluate_method_suitability_cv_applicable_methods() -> None:
    """C22: CV_ONLY and CV_AND_HOLDOUT with J >= 2 declare corrected Nadeau-Bengio and Wilcoxon as applicable (STAT-04, AC-M61-04-02)."""
    plan = _make_partition_plan(n_folds=10, train_size=90, val_size=10)
    report = evaluate_method_suitability(plan)

    assert "nadeau_bengio_paired_t" in report.applicable_methods
    nb = report.applicable_methods["nadeau_bengio_paired_t"]
    assert nb.status == ApplicabilityStatus.APPLICABLE
    assert "cross-validation overlap" in nb.rationale.lower()

    assert "wilcoxon_signed_rank_paired" in report.applicable_methods
    wx = report.applicable_methods["wilcoxon_signed_rank_paired"]
    assert wx.status == ApplicabilityStatus.APPLICABLE


def test_evaluate_method_suitability_flags_uncorrected_t_test() -> None:
    """C23: Uncorrected standard paired t-test is flagged as NOT_SUITABLE for CV designs (STAT-04, AC-M61-04-03)."""
    plan = _make_partition_plan(n_folds=5, train_size=80, val_size=20)
    report = evaluate_method_suitability(plan)

    assert "paired_t_test_uncorrected" in report.applicable_methods
    uncorr_t = report.applicable_methods["paired_t_test_uncorrected"]
    assert uncorr_t.status == ApplicabilityStatus.NOT_SUITABLE
    assert "violate" in uncorr_t.rationale.lower() or "independent" in uncorr_t.rationale.lower()


def test_evaluate_method_suitability_holdout_only_rejection() -> None:
    """C24: HOLDOUT_ONLY (J=1) rejects multi-fold paired tests as NOT_SUITABLE and does not recommend pooled OOF (STAT-04, AC-M61-04-04)."""
    plan = _make_partition_plan(
        regime=EvaluationRegime.HOLDOUT_ONLY,
        n_folds=1,
        train_size=80,
        val_size=20,
        strategy=PartitionStrategy.HOLDOUT,
    )
    report = evaluate_method_suitability(plan)

    assert report.is_cross_validation is False
    assert report.total_development_partitions == 1

    # Both Nadeau-Bengio and fold Wilcoxon must be NOT_SUITABLE
    assert report.applicable_methods["nadeau_bengio_paired_t"].status == ApplicabilityStatus.NOT_SUITABLE
    assert report.applicable_methods["wilcoxon_signed_rank_paired"].status == ApplicabilityStatus.NOT_SUITABLE

    # Verify no erroneous pooled OOF recommendation in rationales or warnings
    for method in report.applicable_methods.values():
        assert "pooled oof" not in method.rationale.lower()


def test_evaluate_method_suitability_wilcoxon_small_sample_warning() -> None:
    """C25: Wilcoxon with J < 6 attaches mathematical warning of inability to reach alpha = 0.05 and power caveats (STAT-04, AC-M61-04-05)."""
    plan = _make_partition_plan(n_folds=5, train_size=80, val_size=20)
    report = evaluate_method_suitability(plan)

    wx = report.applicable_methods["wilcoxon_signed_rank_paired"]
    assert wx.status == ApplicabilityStatus.APPLICABLE
    # Must contain warning regarding J < 6 and minimum p-value 0.0625
    assert len(wx.warnings) >= 1
    w_text = wx.warnings[0].lower()
    assert "0.0625" in w_text or "0.05" in w_text
    assert "power" in w_text or "limitation" in w_text


def test_evaluate_method_suitability_cv_and_holdout_isolation() -> None:
    """C26: CV_AND_HOLDOUT isolates holdout in plan.holdout_ids, keeping J restricted to development folds (STAT-04, AC-M61-04-06)."""
    plan = _make_partition_plan(
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_folds=5,
        train_size=80,
        val_size=20,
        holdout_size=50,
    )
    report = evaluate_method_suitability(plan)

    assert report.evaluation_regime == EvaluationRegime.CV_AND_HOLDOUT
    assert report.is_cross_validation is True
    # J is strictly 5, not 6
    assert report.total_development_partitions == 5
    assert len(plan.holdout_ids) == 50


def test_check_pairwise_comparison_strict_policy() -> None:
    """C27: IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY rejects comparisons if coverage is not VALID (STAT-04, AC-M61-04-07)."""
    s_valid = _make_config_summary(model_id="ridge", completed_ids=("f0", "f1", "f2", "f3", "f4"), total_folds=5)
    s_partial = _make_config_summary(
        model_id="lasso",
        completed_ids=("f0", "f1", "f2", "f3"),
        failed_ids=("f4",),
        total_folds=5,
    )

    eligible, reason, shared_folds = check_pairwise_comparison_eligibility(
        s_valid,
        s_partial,
        IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY,
    )
    assert eligible is False
    assert "valid" in reason.lower()
    assert shared_folds == ()


def test_check_pairwise_comparison_common_subset_policy() -> None:
    """C28: IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET permits comparison if J_paired >= 2 with conditional caveat (STAT-04, AC-M61-04-08)."""
    s1 = _make_config_summary(model_id="m1", completed_ids=("f0", "f1", "f2", "f3"), total_folds=5)
    s2 = _make_config_summary(model_id="m2", completed_ids=("f1", "f2", "f3", "f4"), total_folds=5)

    eligible, reason, shared_folds = check_pairwise_comparison_eligibility(
        s1,
        s2,
        IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET,
    )
    assert eligible is True
    assert "conditional" in reason.lower() or "common subset" in reason.lower()
    # Shared folds are f1, f2, f3 (3 folds)
    assert set(shared_folds) == {"f1", "f2", "f3"}


def test_check_pairwise_comparison_insufficient_pairs() -> None:
    """C29: Pairwise comparison with J_paired < 2 is declared NOT_APPLICABLE regardless of policy (STAT-04, AC-M61-04-09)."""
    # Only 1 shared fold ("f0")
    s1 = _make_config_summary(model_id="m1", completed_ids=("f0", "f1"), total_folds=5)
    s2 = _make_config_summary(model_id="m2", completed_ids=("f0", "f2"), total_folds=5)

    eligible_strict, reason_strict, _ = check_pairwise_comparison_eligibility(
        s1,
        s2,
        IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY,
    )
    assert eligible_strict is False

    eligible_common, reason_common, _ = check_pairwise_comparison_eligibility(
        s1,
        s2,
        IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET,
    )
    assert eligible_common is False
    assert "insufficient" in reason_common.lower() or "j_paired < 2" in reason_common.lower()
