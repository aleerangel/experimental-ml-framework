"""Experimental statistics package (Marco M6 — Consolidação e Comparação Estatística Rigorosa).

Provides descriptive consolidation (Submodule 5A), methodological suitability
evaluation, and comparison eligibility policies.
"""

from experimental_ml.statistics.consolidation import (
    consolidate_descriptive,
    validate_stage5_entry,
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
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    IncompleteComparisonPolicy,
    MethodSuitabilityReport,
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
    "validate_stage5_entry",
    "consolidate_descriptive",
    "evaluate_method_suitability",
    "check_pairwise_comparison_eligibility",
]
