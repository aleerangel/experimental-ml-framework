"""Methodological suitability evaluation and comparison eligibility module (STAT-04, CA-E5-01).

Implements evaluate_method_suitability and check_pairwise_comparison_eligibility,
verifying cross-validation dependence, fold overlap ratios, and incompleteness policies.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from experimental_ml.statistics.types import (
    ApplicabilityStatus,
    ApplicableMethod,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    IncompleteComparisonPolicy,
    MethodSuitabilityReport,
)
from experimental_ml.validation.types import EvaluationRegime, PartitionPlan


def evaluate_method_suitability(
    partition_plan: PartitionPlan,
    consolidation: DescriptiveConsolidation | None = None,
) -> MethodSuitabilityReport:
    """Evaluate applicability of statistical hypothesis test methods for a given experimental design (STAT-04, CA-E5-01).

    Args:
        partition_plan: Validated PartitionPlan from Stage 4A.
        consolidation: Optional DescriptiveConsolidation instance.

    Returns:
        Immutable MethodSuitabilityReport instance.
    """
    regime = partition_plan.regime
    is_cv = regime in (EvaluationRegime.CV_ONLY, EvaluationRegime.CV_AND_HOLDOUT)
    folds = partition_plan.folds
    j_dev = len(folds)

    # Compute fold-level train overlap ratios r_j = n_val / n_train
    fold_ratios_list: list[float] = []
    for f in folds:
        n_train = len(f.train_ids)
        n_val = len(f.val_ids)
        r_j = float(n_val / n_train) if n_train > 0 else 0.0
        fold_ratios_list.append(r_j)

    fold_ratios = tuple(fold_ratios_list)
    mean_r = float(np.mean(fold_ratios)) if fold_ratios else 0.0

    applicable_methods: dict[str, ApplicableMethod] = {}
    report_warnings: list[str] = []

    # 1. Uncorrected standard paired t-test
    if is_cv:
        applicable_methods["paired_t_test_uncorrected"] = ApplicableMethod(
            method_name="paired_t_test_uncorrected",
            status=ApplicabilityStatus.NOT_SUITABLE,
            rationale=(
                f"Standard paired t-test assumes independent observations, but cross-validation folds "
                f"violate this assumption due to overlapping training sets (train overlap ratio r = {mean_r:.4f})."
            ),
            assumptions_tested=("cross_validation_regime",),
            assumptions_untested=(),
            warnings=(
                "Standard paired t-test yields grossly anti-conservative Type I error rates on cross-validation "
                "folds (Dietterich, 1998).",
            ),
        )
    else:
        applicable_methods["paired_t_test_uncorrected"] = ApplicableMethod(
            method_name="paired_t_test_uncorrected",
            status=ApplicabilityStatus.NOT_SUITABLE,
            rationale="Multi-fold paired tests are not applicable in single holdout regime (J=1).",
            assumptions_tested=("single_holdout_regime",),
            assumptions_untested=(),
            warnings=(),
        )

    # 2. Corrected Nadeau-Bengio paired t-test
    if is_cv and j_dev >= 2:
        variance_factor = float(1.0 / j_dev + mean_r)
        applicable_methods["nadeau_bengio_paired_t"] = ApplicableMethod(
            method_name="nadeau_bengio_paired_t",
            status=ApplicabilityStatus.APPLICABLE,
            rationale=(
                f"Corrects for cross-validation overlap via Nadeau & Bengio (2003) variance factor "
                f"(1/J + r = {variance_factor:.4f}) with J = {j_dev} folds and mean r = {mean_r:.4f}."
            ),
            assumptions_tested=("cross_validation_regime", "J >= 2", "paired_folds"),
            assumptions_untested=("approximate_normality_of_differences",),
            warnings=(),
        )
    else:
        applicable_methods["nadeau_bengio_paired_t"] = ApplicableMethod(
            method_name="nadeau_bengio_paired_t",
            status=ApplicabilityStatus.NOT_SUITABLE,
            rationale="Nadeau-Bengio corrected t-test requires cross-validation with at least 2 partitions (J >= 2).",
            assumptions_tested=("regime_and_partition_count",),
            assumptions_untested=(),
            warnings=(),
        )

    # 3. Paired Wilcoxon signed-rank test
    if is_cv and j_dev >= 2:
        wx_warnings: list[str] = []
        if j_dev < 6:
            min_pval = 2.0 / (2**j_dev)
            wx_warnings.append(
                f"Mathematical limitation: with J = {j_dev} < 6, two-sided p-value cannot reach alpha = 0.05 "
                f"(minimum exact p-value is 2/{2**j_dev} = {min_pval:.4f}). "
                "Note that J >= 6 is a necessary condition, not a guarantee of adequate statistical power."
            )
            report_warnings.append(
                f"Small sample size (J = {j_dev} < 6) severely limits statistical power for non-parametric paired tests."
            )

        applicable_methods["wilcoxon_signed_rank_paired"] = ApplicableMethod(
            method_name="wilcoxon_signed_rank_paired",
            status=ApplicabilityStatus.APPLICABLE,
            rationale="Non-parametric paired signed-rank test comparing paired fold metric differences.",
            assumptions_tested=("cross_validation_regime", "J >= 2", "paired_folds"),
            assumptions_untested=("symmetry_of_differences",),
            warnings=tuple(wx_warnings),
        )
    else:
        applicable_methods["wilcoxon_signed_rank_paired"] = ApplicableMethod(
            method_name="wilcoxon_signed_rank_paired",
            status=ApplicabilityStatus.NOT_SUITABLE,
            rationale="Wilcoxon signed-rank test requires paired partitions with J >= 2.",
            assumptions_tested=("regime_and_partition_count",),
            assumptions_untested=(),
            warnings=(),
        )

    # Contextual warnings for regimes
    if regime == EvaluationRegime.CV_AND_HOLDOUT:
        report_warnings.append(
            "Evaluation regime includes final holdout. Holdout evaluation is strictly isolated in "
            "FINAL_HOLDOUT scope and excluded from cross-validation variance calculations."
        )
    elif regime == EvaluationRegime.HOLDOUT_ONLY:
        report_warnings.append(
            "Holdout only regime evaluated (J = 1). Partition-level hypothesis tests across folds "
            "are not applicable due to zero sample degrees of freedom."
        )

    return MethodSuitabilityReport(
        evaluation_regime=regime,
        total_development_partitions=j_dev,
        fold_ratios=fold_ratios,
        mean_train_overlap_ratio=mean_r,
        is_cross_validation=is_cv,
        applicable_methods=applicable_methods,
        warnings=tuple(report_warnings),
    )


def check_pairwise_comparison_eligibility(
    summary_a: ConfigurationSummary,
    summary_b: ConfigurationSummary,
    policy: IncompleteComparisonPolicy,
) -> tuple[bool, str, tuple[str, ...]]:
    """Determine pairwise statistical comparison eligibility under an incompleteness policy (STAT-04, CA-E5-01).

    Args:
        summary_a: ConfigurationSummary for candidate A.
        summary_b: ConfigurationSummary for candidate B.
        policy: Configured IncompleteComparisonPolicy.

    Returns:
        Tuple of (is_eligible, explanation_message, shared_fold_ids).
    """
    shared_folds = tuple(
        f for f in summary_a.completed_fold_ids if f in summary_b.completed_fold_ids
    )
    j_paired = len(shared_folds)

    if j_paired < 2:
        return (
            False,
            f"Insufficient shared valid folds between configurations (J_paired = {j_paired} < 2). "
            "At least 2 paired folds are required for cross-validation hypothesis tests.",
            (),
        )

    if policy == IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY:
        if (
            summary_a.coverage_status != CoverageStatus.VALID
            or summary_b.coverage_status != CoverageStatus.VALID
        ):
            return (
                False,
                f"Pairwise comparison rejected under STRICT_COMPLETE_ONLY: one or both configurations have "
                f"incomplete fold coverage ({summary_a.model_id}: {summary_a.coverage_status.value}, "
                f"{summary_b.model_id}: {summary_b.coverage_status.value}).",
                (),
            )
        return (
            True,
            "Fully eligible under STRICT_COMPLETE_ONLY with valid complete coverage on all folds.",
            shared_folds,
        )

    if policy == IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET:
        if (
            summary_a.coverage_status == CoverageStatus.VALID
            and summary_b.coverage_status == CoverageStatus.VALID
        ):
            return (
                True,
                "Fully eligible with complete fold coverage.",
                shared_folds,
            )
        return (
            True,
            f"Conditionally applicable on common subset of {j_paired} shared folds. "
            "Loss of coverage documented; caution advised regarding potential non-random attrition bias.",
            shared_folds,
        )

    return (False, f"Unsupported IncompleteComparisonPolicy: {policy}", ())
