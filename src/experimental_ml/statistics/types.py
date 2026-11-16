"""Domain enumerations and immutable frozen dataclasses for experimental statistics (STAT-01).

Conforms to XCUT-02 (numpy and stdlib only) and RNF02 (zero domain-specific dependencies).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import math
from types import MappingProxyType
from typing import Any, Mapping

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.features.stability import SelectionStabilityReport
from experimental_ml.metrics.types import MetricDirection, MetricValue
from experimental_ml.validation.types import EvaluationRegime


class CoverageStatus(StrEnum):
    """Execution fold coverage status for an experimental configuration."""

    VALID = "VALID"
    PARTIAL_COVERAGE = "PARTIAL_COVERAGE"
    NO_COVERAGE = "NO_COVERAGE"


class IncompleteComparisonPolicy(StrEnum):
    """Policy governing pairwise comparisons when configurations have incomplete fold coverage."""

    STRICT_COMPLETE_ONLY = "STRICT_COMPLETE_ONLY"
    ALLOW_COMMON_SUBSET = "ALLOW_COMMON_SUBSET"


class ApplicabilityStatus(StrEnum):
    """Methodological applicability status of an inferential statistical method."""

    APPLICABLE = "APPLICABLE"
    CONDITIONALLY_APPLICABLE = "CONDITIONALLY_APPLICABLE"
    NOT_SUITABLE = "NOT_SUITABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class AggregatedMetricStats:
    """Aggregated descriptive statistics for a metric across completed folds."""

    n_valid: int
    n_total: int
    status: MetricStatus
    mean: float | None = None
    std: float | None = None
    median: float | None = None
    iqr: float | None = None
    q25: float | None = None
    q75: float | None = None
    min_value: float | None = None
    max_value: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, MetricStatus):
            object.__setattr__(self, "status", MetricStatus(self.status))
        if self.n_valid < 0 or self.n_total < 0:
            raise ConfigurationError("n_valid and n_total must be non-negative integers")
        if self.n_valid > self.n_total:
            raise ConfigurationError("n_valid cannot exceed n_total")


@dataclass(frozen=True, slots=True)
class AggregatedTimingStats:
    """Aggregated execution durations (seconds) across completed folds for a configuration."""

    data_extraction_mean_s: float
    data_extraction_total_s: float
    preprocessing_mean_s: float
    preprocessing_total_s: float
    feature_selection_mean_s: float
    feature_selection_total_s: float
    tuning_mean_s: float
    tuning_total_s: float
    fit_mean_s: float
    fit_total_s: float
    predict_mean_s: float
    predict_total_s: float
    evaluation_mean_s: float
    evaluation_total_s: float
    total_cell_mean_s: float
    total_cell_sum_s: float


@dataclass(frozen=True, slots=True)
class ConfigurationSummary:
    """Consolidated summary for a single (model_id, scenario_id) configuration."""

    model_id: str
    scenario_id: str
    total_folds: int
    completed_folds: int
    failed_folds: int
    cancelled_folds: int
    coverage: float
    coverage_status: CoverageStatus
    completed_fold_ids: tuple[str, ...]
    failed_fold_ids: tuple[str, ...]
    cancelled_fold_ids: tuple[str, ...]
    fold_metrics: Mapping[str, Mapping[str, MetricValue]] = field(default_factory=dict)
    aggregated_metrics: Mapping[str, AggregatedMetricStats] = field(default_factory=dict)
    pooled_oof_metrics: Mapping[str, MetricValue] = field(default_factory=dict)
    aggregated_timing: AggregatedTimingStats | None = None
    feature_stability: SelectionStabilityReport | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.coverage_status, CoverageStatus):
            object.__setattr__(self, "coverage_status", CoverageStatus(self.coverage_status))
        if not isinstance(self.completed_fold_ids, tuple):
            object.__setattr__(self, "completed_fold_ids", tuple(self.completed_fold_ids))
        if not isinstance(self.failed_fold_ids, tuple):
            object.__setattr__(self, "failed_fold_ids", tuple(self.failed_fold_ids))
        if not isinstance(self.cancelled_fold_ids, tuple):
            object.__setattr__(self, "cancelled_fold_ids", tuple(self.cancelled_fold_ids))

        # Freeze dictionaries into MappingProxyType
        if not isinstance(self.fold_metrics, MappingProxyType):
            frozen_folds = {
                f_id: MappingProxyType(dict(sub_m))
                for f_id, sub_m in self.fold_metrics.items()
            }
            object.__setattr__(self, "fold_metrics", MappingProxyType(frozen_folds))

        if not isinstance(self.aggregated_metrics, MappingProxyType):
            object.__setattr__(
                self,
                "aggregated_metrics",
                MappingProxyType(dict(self.aggregated_metrics)),
            )

        if not isinstance(self.pooled_oof_metrics, MappingProxyType):
            object.__setattr__(
                self,
                "pooled_oof_metrics",
                MappingProxyType(dict(self.pooled_oof_metrics)),
            )


@dataclass(frozen=True, slots=True)
class DescriptiveConsolidation:
    """Consolidated descriptive statistics across all configurations in an experiment matrix."""

    experiment_id: str
    partition_plan_id: str
    total_configurations: int
    configurations: Mapping[tuple[str, str], ConfigurationSummary]
    timestamp_utc: str

    def __post_init__(self) -> None:
        if not isinstance(self.configurations, MappingProxyType):
            object.__setattr__(
                self,
                "configurations",
                MappingProxyType(dict(self.configurations)),
            )


@dataclass(frozen=True, slots=True)
class ApplicableMethod:
    """Evaluation record of a single statistical hypothesis test method."""

    method_name: str
    status: ApplicabilityStatus
    rationale: str
    assumptions_tested: tuple[str, ...] = field(default_factory=tuple)
    assumptions_untested: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.status, ApplicabilityStatus):
            object.__setattr__(self, "status", ApplicabilityStatus(self.status))
        if not isinstance(self.assumptions_tested, tuple):
            object.__setattr__(self, "assumptions_tested", tuple(self.assumptions_tested))
        if not isinstance(self.assumptions_untested, tuple):
            object.__setattr__(self, "assumptions_untested", tuple(self.assumptions_untested))
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True, slots=True)
class MethodSuitabilityReport:
    """Methodological suitability report assessing applicable statistical methods."""

    evaluation_regime: EvaluationRegime
    total_development_partitions: int
    fold_ratios: tuple[float, ...]
    mean_train_overlap_ratio: float
    is_cross_validation: bool
    applicable_methods: Mapping[str, ApplicableMethod]
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_regime, EvaluationRegime):
            object.__setattr__(self, "evaluation_regime", EvaluationRegime(self.evaluation_regime))
        if not isinstance(self.fold_ratios, tuple):
            object.__setattr__(self, "fold_ratios", tuple(float(r) for r in self.fold_ratios))
        if not isinstance(self.applicable_methods, MappingProxyType):
            object.__setattr__(
                self,
                "applicable_methods",
                MappingProxyType(dict(self.applicable_methods)),
            )
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(str(w) for w in self.warnings))


class ComparisonScope(StrEnum):
    """Comparison scope governing candidate pair generation (RF5.1, STAT-05)."""

    MODELS_WITHIN_SCENARIO = "MODELS_WITHIN_SCENARIO"
    SCENARIOS_WITHIN_MODEL = "SCENARIOS_WITHIN_MODEL"
    FULL_CONFIGURATIONS = "FULL_CONFIGURATIONS"
    AGAINST_BASELINE = "AGAINST_BASELINE"
    ALL_PAIRWISE = "ALL_PAIRWISE"
    PLANNED_HYPOTHESES = "PLANNED_HYPOTHESES"


class MultiplicityMethod(StrEnum):
    """Multiple hypothesis testing correction method (STAT-05, STAT-08)."""

    NONE = "NONE"
    HOLM_BONFERRONI = "HOLM_BONFERRONI"
    BENJAMINI_HOCHBERG = "BENJAMINI_HOCHBERG"


class EffectSizeMagnitude(StrEnum):
    """Qualitative effect size magnitude classification for paired Cohen's d_z."""

    NEGLIGIBLE = "NEGLIGIBLE"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class PracticalRelevanceStatus(StrEnum):
    """Practical relevance classification relative to configured Delta_min thresholds."""

    NOT_CONFIGURED = "NOT_CONFIGURED"
    STATISTICALLY_SIGNIFICANT_AND_PRACTICAL = "STATISTICALLY_SIGNIFICANT_AND_PRACTICAL"
    STATISTICALLY_SIGNIFICANT_NOT_PRACTICAL = "STATISTICALLY_SIGNIFICANT_NOT_PRACTICAL"
    PRACTICAL_NOT_STATISTICALLY_SIGNIFICANT = "PRACTICAL_NOT_STATISTICALLY_SIGNIFICANT"
    INCONCLUSIVE = "INCONCLUSIVE"
    EVIDENCE_OF_EQUIVALENCE = "EVIDENCE_OF_EQUIVALENCE"


@dataclass(frozen=True, slots=True)
class ComparisonSpec:
    """Researcher-defined specification for statistical comparisons (STAT-05)."""

    metrics_of_interest: tuple[str, ...]
    metric_directions: Mapping[str, MetricDirection]
    comparison_scope: ComparisonScope
    baseline_config: tuple[str, str] | None = None
    planned_pairs: tuple[tuple[tuple[str, str], tuple[str, str]], ...] = field(default_factory=tuple)
    alpha: float = 0.05
    multiplicity_method: MultiplicityMethod = MultiplicityMethod.HOLM_BONFERRONI
    hypothesis_family_spec: Mapping[tuple[tuple[str, str], tuple[str, str], str], str] | None = None
    practical_relevance_thresholds: Mapping[str, float] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.comparison_scope, ComparisonScope):
            object.__setattr__(self, "comparison_scope", ComparisonScope(self.comparison_scope))
        if not isinstance(self.multiplicity_method, MultiplicityMethod):
            object.__setattr__(self, "multiplicity_method", MultiplicityMethod(self.multiplicity_method))

        metrics = tuple(str(m) for m in self.metrics_of_interest)
        if not metrics:
            raise ConfigurationError("ComparisonSpec.metrics_of_interest must not be empty.")
        object.__setattr__(self, "metrics_of_interest", metrics)

        directions = {
            str(k): (v if isinstance(v, MetricDirection) else MetricDirection(v))
            for k, v in self.metric_directions.items()
        }
        missing_dirs = [m for m in metrics if m not in directions]
        if missing_dirs:
            raise ConfigurationError(
                f"ComparisonSpec.metric_directions missing entries for metrics: {missing_dirs}"
            )
        object.__setattr__(self, "metric_directions", MappingProxyType(directions))

        if not math.isfinite(self.alpha) or not (0.0 < self.alpha < 1.0):
            raise ConfigurationError(f"ComparisonSpec.alpha must be in (0.0, 1.0); got {self.alpha}")

        if self.comparison_scope == ComparisonScope.AGAINST_BASELINE:
            if self.baseline_config is None or len(self.baseline_config) != 2:
                raise ConfigurationError(
                    "ComparisonSpec.baseline_config (model_id, scenario_id) is required for AGAINST_BASELINE."
                )
        if self.baseline_config is not None:
            object.__setattr__(
                self,
                "baseline_config",
                (str(self.baseline_config[0]), str(self.baseline_config[1])),
            )

        pairs = tuple(
            ((str(a[0]), str(a[1])), (str(b[0]), str(b[1])))
            for a, b in self.planned_pairs
        )
        if self.comparison_scope == ComparisonScope.PLANNED_HYPOTHESES and not pairs:
            raise ConfigurationError(
                "ComparisonSpec.planned_pairs must not be empty for PLANNED_HYPOTHESES."
            )
        object.__setattr__(self, "planned_pairs", pairs)

        if self.hypothesis_family_spec is not None:
            fam_map = {
                (
                    (str(k[0][0]), str(k[0][1])),
                    (str(k[1][0]), str(k[1][1])),
                    str(k[2]),
                ): str(v)
                for k, v in self.hypothesis_family_spec.items()
            }
            object.__setattr__(self, "hypothesis_family_spec", MappingProxyType(fam_map))

        if self.practical_relevance_thresholds is not None:
            thresh: dict[str, float] = {}
            for k, v in self.practical_relevance_thresholds.items():
                val = float(v)
                if not math.isfinite(val) or val < 0.0:
                    raise ConfigurationError(
                        f"Practical relevance threshold for '{k}' must be finite and >= 0; got {val}"
                    )
                thresh[str(k)] = val
            object.__setattr__(self, "practical_relevance_thresholds", MappingProxyType(thresh))


@dataclass(frozen=True, slots=True)
class NadeauBengioResult:
    """Result of the Nadeau-Bengio (2003) corrected paired t-test (STAT-06)."""

    mean_difference: float
    std_difference: float
    corrected_variance: float
    corrected_se: float
    t_statistic: float
    degrees_of_freedom: int
    p_value: float
    confidence_interval: tuple[float, float]
    alpha: float
    mean_train_val_ratio: float
    fold_size_cv: float | None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.confidence_interval, tuple):
            object.__setattr__(
                self,
                "confidence_interval",
                (float(self.confidence_interval[0]), float(self.confidence_interval[1])),
            )
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(str(w) for w in self.warnings))


@dataclass(frozen=True, slots=True)
class WilcoxonResult:
    """Result of the paired Wilcoxon signed-rank test (STAT-07)."""

    statistic: float
    w_plus: float
    w_minus: float
    n_total: int
    n_effective: int
    zero_method: str
    p_value: float
    is_exact: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(str(w) for w in self.warnings))


@dataclass(frozen=True, slots=True)
class EffectSizeResult:
    """Paired Cohen's d_z effect size result with approximate analytical CI (STAT-07)."""

    cohens_d: float
    magnitude: EffectSizeMagnitude
    confidence_interval: tuple[float | None, float | None]
    alpha: float
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.magnitude, EffectSizeMagnitude):
            object.__setattr__(self, "magnitude", EffectSizeMagnitude(self.magnitude))
        if not isinstance(self.confidence_interval, tuple):
            object.__setattr__(
                self,
                "confidence_interval",
                (self.confidence_interval[0], self.confidence_interval[1]),
            )
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(str(w) for w in self.warnings))


@dataclass(frozen=True, slots=True)
class PairwiseComparisonResult:
    """Complete inferential result for a pair of configurations on a single metric (STAT-08)."""

    comparison_id: str
    family_id: str
    metric_name: str
    direction: MetricDirection
    config_a: tuple[str, str]
    config_b: tuple[str, str]
    shared_fold_ids: tuple[str, ...]
    observed_mean_a: float
    observed_mean_b: float
    observed_difference: float
    observed_better: tuple[str, str] | None
    nadeau_bengio: NadeauBengioResult
    wilcoxon: WilcoxonResult
    effect_size: EffectSizeResult
    nadeau_bengio_adjusted_p: float
    wilcoxon_adjusted_p: float
    practical_relevance: PracticalRelevanceStatus
    is_conditional: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.direction, MetricDirection):
            object.__setattr__(self, "direction", MetricDirection(self.direction))
        if not isinstance(self.practical_relevance, PracticalRelevanceStatus):
            object.__setattr__(
                self,
                "practical_relevance",
                PracticalRelevanceStatus(self.practical_relevance),
            )
        if not isinstance(self.shared_fold_ids, tuple):
            object.__setattr__(self, "shared_fold_ids", tuple(str(f) for f in self.shared_fold_ids))
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(str(w) for w in self.warnings))


@dataclass(frozen=True, slots=True)
class SkippedComparison:
    """Audit record for a requested comparison that could not be executed (STAT-08)."""

    config_a: tuple[str, str]
    config_b: tuple[str, str]
    metric_name: str
    reason: str


@dataclass(frozen=True, slots=True)
class StatisticalComparisonBundle:
    """Immutable container for all inferential comparisons and audit records (STAT-08)."""

    experiment_id: str
    partition_plan_id: str
    comparison_spec: ComparisonSpec
    comparisons: tuple[PairwiseComparisonResult, ...]
    skipped_comparisons: tuple[SkippedComparison, ...] = field(default_factory=tuple)
    non_applicable_reasons: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.comparisons, tuple):
            object.__setattr__(self, "comparisons", tuple(self.comparisons))
        if not isinstance(self.skipped_comparisons, tuple):
            object.__setattr__(self, "skipped_comparisons", tuple(self.skipped_comparisons))
        if not isinstance(self.non_applicable_reasons, tuple):
            object.__setattr__(
                self,
                "non_applicable_reasons",
                tuple(str(r) for r in self.non_applicable_reasons),
            )
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(str(w) for w in self.warnings))
