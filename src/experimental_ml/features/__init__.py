"""Feature engineering, exploratory relation analysis, scenario definition, and intra-fold selection.

Complies with EXP-01 to EXP-08, SCN-01 to SCN-08, SEL-01 to SEL-08, RF2.1, RF2.2, RF2.3, RF2.4,
CA-E2-01, CA-E2-02, ADR-002, ADR-005, ADR-007, and ADR-008.
"""

from experimental_ml.features.exploration import explore_features
from experimental_ml.features.scenarios import (
    FeatureScenario,
    ScenarioMode,
    ScenariosCatalog,
    load_scenarios,
    save_scenarios,
    validate_scenarios,
)
from experimental_ml.features.selection import (
    SelectionResult,
    apply_feature_selection,
    select_features_in_fold,
)
from experimental_ml.features.stability import (
    SelectionStabilityReport,
    compute_selection_stability,
)
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
    # M3.1: Exploratory analysis
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
    # M3.2: Scenarios modeling & catalog
    "ScenarioMode",
    "FeatureScenario",
    "ScenariosCatalog",
    "validate_scenarios",
    "save_scenarios",
    "load_scenarios",
    # M3.3: Intra-fold feature selection & stability
    "SelectionResult",
    "select_features_in_fold",
    "apply_feature_selection",
    "SelectionStabilityReport",
    "compute_selection_stability",
]
