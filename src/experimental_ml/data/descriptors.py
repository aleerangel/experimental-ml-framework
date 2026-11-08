"""Lightweight descriptors for raw datasets and sanitized views.

Complies with ARQUITETURA §5, D11, STORE-02, and STORE-03.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from experimental_ml.core.enums import TaskType
from experimental_ml.core.types import ObservationId
from experimental_ml.data.preparation import PreparationRule


@dataclass(frozen=True, slots=True)
class DatasetDescriptor:
    """Lightweight metadata descriptor for ingested DatasetBundle."""

    dataset_hash: str
    n_observations: int
    n_columns: int
    column_names: tuple[str, ...]
    column_types: Mapping[str, str]
    raw_source_hash: str | None = None
    raw_source_path: str | None = None
    target_col: str | None = None
    task_type: str | None = None
    group_col: str | None = None
    time_col: str | None = None
    schema_path: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.column_names, tuple):
            object.__setattr__(self, "column_names", tuple(self.column_names))
        if not isinstance(self.column_types, MappingProxyType):
            object.__setattr__(self, "column_types", MappingProxyType(dict(self.column_types)))


@dataclass(frozen=True, slots=True)
class SanitizedViewDescriptor:
    """Lightweight metadata descriptor for SanitizedDatasetView (D11)."""

    dataset_hash: str
    source_dataset_hash: str
    source_plan_digest: str
    n_observations: int
    candidate_feature_cols: tuple[str, ...]
    dropped_observation_ids: tuple[ObservationId, ...]
    target_label_mapping: Mapping[Any, int] | None
    deferred_rules: tuple[PreparationRule, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_feature_cols, tuple):
            object.__setattr__(self, "candidate_feature_cols", tuple(self.candidate_feature_cols))
        if not isinstance(self.dropped_observation_ids, tuple):
            object.__setattr__(self, "dropped_observation_ids", tuple(self.dropped_observation_ids))
        if self.target_label_mapping is not None and not isinstance(self.target_label_mapping, MappingProxyType):
            object.__setattr__(self, "target_label_mapping", MappingProxyType(dict(self.target_label_mapping)))
        if not isinstance(self.deferred_rules, tuple):
            object.__setattr__(self, "deferred_rules", tuple(self.deferred_rules))
