"""Data preparation plan and sanitized dataset view.

Implements declarative preparation planning and strict pre-partition sanitization,
enforcing ADR-002 (no data leakage) and zero silent mutations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Mapping

import numpy as np

from experimental_ml.core.types import ObservationId
from experimental_ml.data.schema import DatasetSchemaSpec

FindingCode = str

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
