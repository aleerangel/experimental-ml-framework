"""Feature engineering, exploratory relation analysis, and scenario definition.

Complies with EXP-01 to EXP-08, RF2.1, CA-E2-01, ADR-005, ADR-007, and ADR-008.
"""

from experimental_ml.features.exploration import explore_features
from experimental_ml.features.stats import (
    compute_correlation_ratio,
    compute_cramers_v,
    compute_pearson,
    compute_spearman,
)
from experimental_ml.features.types import (
    METHODOLOGICAL_WARNINGS,
    SCOPE_EXPLORATORY_FULL_DATA,
    AssociationMeasure,
    ExploratoryFeatureReport,
    RedundancyPair,
)

__all__ = [
    "explore_features",
    "compute_pearson",
    "compute_spearman",
    "compute_correlation_ratio",
    "compute_cramers_v",
    "SCOPE_EXPLORATORY_FULL_DATA",
    "METHODOLOGICAL_WARNINGS",
    "AssociationMeasure",
    "RedundancyPair",
    "ExploratoryFeatureReport",
]
