"""Experimental statistics package (Marco M6 — Consolidação e Comparação Estatística Rigorosa).

Provides descriptive consolidation (Submodule 5A), methodological suitability
evaluation, comparison eligibility policies, paired inferential statistics,
effect size estimation, multiplicity adjustments, multi-objective Pareto analysis,
sequential acquisition scoring (Submodule 5B), and structured synthesis (Submodule 5C).
"""

from experimental_ml.statistics.acquisition import score_candidate_acquisition
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
from experimental_ml.statistics.multiobjective import compute_pareto_frontier
from experimental_ml.statistics.multiplicity import (
    adjust_pvalues_bh,
    adjust_pvalues_holm,
)
from experimental_ml.statistics.storage import (
    LoadedStatisticsArtifacts,
    load_statistics_artifacts,
    save_statistics_artifacts,
)
from experimental_ml.statistics.suitability import (
    check_pairwise_comparison_eligibility,
    evaluate_method_suitability,
)
from experimental_ml.statistics.synthesis import synthesize_conclusions
from experimental_ml.statistics.types import (
    AcquisitionCriterion,
    AcquisitionScoreRecord,
    AggregatedMetricStats,
    AggregatedTimingStats,
    ApplicabilityStatus,
    ApplicableMethod,
    CandidatePrediction,
    ComparisonScope,
    ComparisonSpec,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    EffectSizeMagnitude,
    EffectSizeResult,
    ExcludedParetoConfiguration,
    IncompleteComparisonPolicy,
    MethodSuitabilityReport,
    MultiObjectiveSpec,
    MultiObjectiveSummary,
    MultiplicityMethod,
    NadeauBengioResult,
    ObjectiveSource,
    ObjectiveSpec,
    PairwiseComparisonResult,
    ParetoConfigurationPoint,
    PracticalRelevanceStatus,
    SkippedComparison,
    StatisticalComparisonBundle,
    StructuredConclusion,
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
    "ObjectiveSource",
    "AcquisitionCriterion",
    "ObjectiveSpec",
    "MultiObjectiveSpec",
    "ParetoConfigurationPoint",
    "ExcludedParetoConfiguration",
    "MultiObjectiveSummary",
    "CandidatePrediction",
    "AcquisitionScoreRecord",
    "StructuredConclusion",
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
    "compute_pareto_frontier",
    "score_candidate_acquisition",
    "synthesize_conclusions",
    "LoadedStatisticsArtifacts",
    "save_statistics_artifacts",
    "load_statistics_artifacts",
]
