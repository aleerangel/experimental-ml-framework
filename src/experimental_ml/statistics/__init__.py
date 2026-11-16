"""Experimental statistics package (Marco M6 — Consolidação e Comparação Estatística Rigorosa).

Provides descriptive consolidation (Submodule 5A), methodological suitability
evaluation, comparison eligibility policies, paired inferential statistics,
effect size estimation, and multiplicity adjustments (Submodule 5B).
"""

from experimental_ml.statistics.comparisons import run_statistical_comparisons
from experimental_ml.statistics.consolidation import (
    consolidate_descriptive,
    validate_stage5_entry,
)
from experimental_ml.statistics.inference import (
    compute_paired_cohens_d,
    paired_nadeau_bengio_test,
    paired_wilcoxon_test,
)
from experimental_ml.statistics.multiplicity import (
    adjust_pvalues_bh,
    adjust_pvalues_holm,
)
from experimental_ml.statistics.suitability import (
    check_pairwise_comparison_eligibility,
    evaluate_method_suitability,
)
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    AggregatedTimingStats,
    ApplicabilityStatus,
    ApplicableMethod,
    ComparisonScope,
    ComparisonSpec,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    EffectSizeMagnitude,
    EffectSizeResult,
    IncompleteComparisonPolicy,
    MethodSuitabilityReport,
    MultiplicityMethod,
    NadeauBengioResult,
    PairwiseComparisonResult,
    PracticalRelevanceStatus,
    SkippedComparison,
    StatisticalComparisonBundle,
    WilcoxonResult,
)

__all__ = [
    "CoverageStatus",
    "IncompleteComparisonPolicy",
    "ApplicabilityStatus",
    "AggregatedMetricStats",
    "AggregatedTimingStats",
    "ConfigurationSummary",
    "DescriptiveConsolidation",
    "ApplicableMethod",
    "MethodSuitabilityReport",
    "ComparisonScope",
    "MultiplicityMethod",
    "EffectSizeMagnitude",
    "PracticalRelevanceStatus",
    "ComparisonSpec",
    "NadeauBengioResult",
    "WilcoxonResult",
    "EffectSizeResult",
    "PairwiseComparisonResult",
    "SkippedComparison",
    "StatisticalComparisonBundle",
    "validate_stage5_entry",
    "consolidate_descriptive",
    "evaluate_method_suitability",
    "check_pairwise_comparison_eligibility",
    "paired_nadeau_bengio_test",
    "paired_wilcoxon_test",
    "compute_paired_cohens_d",
    "adjust_pvalues_holm",
    "adjust_pvalues_bh",
    "run_statistical_comparisons",
]
