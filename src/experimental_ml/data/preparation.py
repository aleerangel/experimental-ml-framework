"""Data preparation plan and sanitized dataset view.

Implements declarative preparation planning and strict pre-partition sanitization,
enforcing ADR-002 (no data leakage) and zero silent mutations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Mapping

import numpy as np

from experimental_ml.core.enums import FindingSeverity
from experimental_ml.core.findings import ConfigurationError, ContractViolationError, DataIntegrityError
from experimental_ml.core.types import ObservationId
from experimental_ml.data.profiling import DatasetProfile
from experimental_ml.data.schema import DatasetSchemaSpec

IRRESOLVABLE_FINDING_CODES: frozenset[str] = frozenset(
    {
        "E1_TARGET_ALL_MISSING",
        "E1_TARGET_ZERO_VARIANCE",
        "E1_TARGET_CLASS_COUNT_INVALID",
        "E1_TARGET_NOT_NUMERIC",
    }
)

VALID_RULE_KINDS: frozenset[str] = frozenset(
    {
        "DROP_ROWS",
        "EXCLUDE_COLUMN",
        "MAP_BINARY_TARGET",
        "DEFER_INTRA_FOLD",
        "ACCEPT_AS_IS",
    }
)

ADMISSIBLE_RULES_BY_CODE: dict[str, frozenset[str]] = {
    "E1_TARGET_MISSING": frozenset({"DROP_ROWS"}),
    "E1_GROUP_MISSING": frozenset({"DROP_ROWS"}),
    "E1_GROUP_EMPTY_VALUES": frozenset({"DROP_ROWS"}),
    "E1_FEATURE_MISSING": frozenset({"DROP_ROWS", "EXCLUDE_COLUMN", "DEFER_INTRA_FOLD", "ACCEPT_AS_IS"}),
    "E1_CONSTANT_COLUMN": frozenset({"EXCLUDE_COLUMN", "ACCEPT_AS_IS"}),
    "E1_CONSTANT_FEATURE_COLUMN": frozenset({"EXCLUDE_COLUMN", "ACCEPT_AS_IS"}),
    "E1_COLUMN_ALL_MISSING": frozenset({"EXCLUDE_COLUMN", "ACCEPT_AS_IS"}),
    "E1_IDENTIFIER_COLUMN_SUSPECTED": frozenset({"EXCLUDE_COLUMN", "ACCEPT_AS_IS"}),
    "E1_CATEGORICAL_UNENCODED": frozenset({"EXCLUDE_COLUMN", "DEFER_INTRA_FOLD", "ACCEPT_AS_IS"}),
    "E1_TARGET_BINARY_UNMAPPED": frozenset({"MAP_BINARY_TARGET"}),
}


def _validate_rule_admissibility(rule: PreparationRule, profile: DatasetProfile) -> None:
    """Validate a preparation rule against profile findings and the closed catalog.

    Raises:
        ConfigurationError: If the rule targets an invalid, non-confirmed, or irresolvable
            finding, uses an inadmissible rule kind, targets a protected column for exclusion,
            or carries invalid parameters.
    """
    if rule.kind not in VALID_RULE_KINDS:
        raise ConfigurationError(
            f"Invalid rule kind '{rule.kind}'. Allowed kinds: {sorted(VALID_RULE_KINDS)}"
        )

    # 1. Check if finding exists in profile and verify severity
    matching_findings = [
        f for f in profile.findings
        if f.code == rule.finding_code and f.context.get("column") == rule.column
    ]
    if not matching_findings:
        raise ConfigurationError(
            f"Rule targets non-existent finding ({rule.finding_code}, column={rule.column!r}) in profile"
        )

    finding = matching_findings[0]
    if finding.severity != FindingSeverity.CONFIRMED_ISSUE:
        raise ConfigurationError(
            f"Rule targets finding ({rule.finding_code}, column={rule.column!r}) with severity "
            f"'{finding.severity.value}', but only CONFIRMED_ISSUE can be targeted by preparation rules"
        )

    # 2. Check for irresolvable finding codes
    if rule.finding_code in IRRESOLVABLE_FINDING_CODES:
        raise ConfigurationError(
            f"Finding '{rule.finding_code}' is irresolvable and accepts no preparation rules"
        )

    # 3. Check admissibility catalog
    admissible_kinds = ADMISSIBLE_RULES_BY_CODE.get(rule.finding_code)
    if admissible_kinds is None or rule.kind not in admissible_kinds:
        raise ConfigurationError(
            f"Rule kind '{rule.kind}' is not admissible for finding '{rule.finding_code}'. "
            f"Admissible kinds: {sorted(admissible_kinds) if admissible_kinds else 'none'}"
        )

    # 4. EXCLUDE_COLUMN checks on protected columns
    if rule.kind == "EXCLUDE_COLUMN":
        if rule.column == profile.target.column_name:
            raise ConfigurationError("Cannot apply EXCLUDE_COLUMN to target column")
        if profile.groups is not None and rule.column == profile.groups.group_col:
            raise ConfigurationError("Cannot apply EXCLUDE_COLUMN to group column")
        if rule.column is None:
            raise ConfigurationError("EXCLUDE_COLUMN requires a non-None column")

    # 5. MAP_BINARY_TARGET checks
    elif rule.kind == "MAP_BINARY_TARGET":
        if "positive_label" not in rule.parameters:
            raise ConfigurationError("MAP_BINARY_TARGET requires 'positive_label' parameter")
        pos_label = rule.parameters["positive_label"]
        if profile.target.class_frequencies is not None:
            observed_classes = [cf.value for cf in profile.target.class_frequencies]
            if pos_label not in observed_classes:
                raise ConfigurationError(
                    f"positive_label {pos_label!r} not found in target observed classes: {observed_classes}"
                )

    # 6. DEFER_INTRA_FOLD checks
    elif rule.kind == "DEFER_INTRA_FOLD":
        if rule.finding_code == "E1_FEATURE_MISSING":
            strategy = rule.parameters.get("imputation_strategy")
            if strategy not in ("MEAN", "MEDIAN", "MODE"):
                raise ConfigurationError(
                    f"DEFER_INTRA_FOLD for E1_FEATURE_MISSING requires 'imputation_strategy' in "
                    f"('MEAN', 'MEDIAN', 'MODE'), got {strategy!r}"
                )
        elif rule.finding_code == "E1_CATEGORICAL_UNENCODED":
            encoding = rule.parameters.get("encoding_strategy")
            if not isinstance(encoding, str) or not encoding.strip():
                raise ConfigurationError(
                    "DEFER_INTRA_FOLD for E1_CATEGORICAL_UNENCODED requires non-empty string 'encoding_strategy'"
                )


RuleKind = Literal[
    "DROP_ROWS",
    "EXCLUDE_COLUMN",
    "MAP_BINARY_TARGET",
    "DEFER_INTRA_FOLD",
    "ACCEPT_AS_IS",
]

PlanStatus = Literal["READY", "INCOMPLETE"]


@dataclass(frozen=True, slots=True)
class PreparationRule:
    """Explicit preparation rule targeting a confirmed diagnostic finding."""

    finding_code: FindingCode
    column: str | None
    kind: RuleKind
    parameters: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.parameters, MappingProxyType):
            object.__setattr__(
                self,
                "parameters",
                MappingProxyType(dict(self.parameters) if self.parameters else {}),
            )


@dataclass(frozen=True, slots=True)
class UnresolvedFinding:
    """Diagnostic finding that lacks an admissible preparation rule."""

    finding_code: FindingCode
    column: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class PreparationPlan:
    """Deterministic preparation plan binding profile diagnostics to explicit rules."""

    status: PlanStatus
    source_dataset_hash: str
    source_profile_digest: str
    rules: tuple[PreparationRule, ...] = ()
    unresolved_findings: tuple[UnresolvedFinding, ...] = ()
    plan_digest: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.rules, tuple):
            object.__setattr__(self, "rules", tuple(self.rules))
        if not isinstance(self.unresolved_findings, tuple):
            object.__setattr__(self, "unresolved_findings", tuple(self.unresolved_findings))


@dataclass(frozen=True, slots=True)
class SanitizedDatasetView:
    """Immutable view of sanitized dataset post pre-partition structural preparation."""

    columns: Mapping[str, np.ndarray]
    schema: DatasetSchemaSpec
    observation_ids: tuple[ObservationId, ...]
    candidate_feature_cols: tuple[str, ...]
    dropped_observation_ids: tuple[ObservationId, ...]
    target_label_mapping: Mapping[Any, int] | None
    deferred_rules: tuple[PreparationRule, ...]
    source_dataset_hash: str
    source_plan_digest: str
    dataset_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.columns, MappingProxyType):
            object.__setattr__(self, "columns", MappingProxyType(dict(self.columns)))
        if not isinstance(self.observation_ids, tuple):
            object.__setattr__(self, "observation_ids", tuple(self.observation_ids))
        if not isinstance(self.candidate_feature_cols, tuple):
            object.__setattr__(self, "candidate_feature_cols", tuple(self.candidate_feature_cols))
        if not isinstance(self.dropped_observation_ids, tuple):
            object.__setattr__(self, "dropped_observation_ids", tuple(self.dropped_observation_ids))
        if not isinstance(self.deferred_rules, tuple):
            object.__setattr__(self, "deferred_rules", tuple(self.deferred_rules))
        if self.target_label_mapping is not None and not isinstance(self.target_label_mapping, MappingProxyType):
            object.__setattr__(
                self,
                "target_label_mapping",
                MappingProxyType(dict(self.target_label_mapping)),
            )
