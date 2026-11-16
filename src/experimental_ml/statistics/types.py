"""Domain enumerations and immutable frozen dataclasses for experimental statistics (STAT-01).

Conforms to XCUT-02 (numpy and stdlib only) and RNF02 (zero domain-specific dependencies).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.features.stability import SelectionStabilityReport
from experimental_ml.metrics.types import MetricValue
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
