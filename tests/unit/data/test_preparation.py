"""Unit tests for preparation models, plan creation, and dataset sanitization."""

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import numpy as np
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.core.types import ObservationId
from experimental_ml.data.preparation import (
    PreparationPlan,
    PreparationRule,
    SanitizedDatasetView,
    UnresolvedFinding,
)
from experimental_ml.data.schema import DatasetSchemaSpec


def test_t1_preparation_rule_immutability_and_slots() -> None:
    rule = PreparationRule(
        finding_code="E1_TARGET_MISSING",
        column="target",
        kind="DROP_ROWS",
        parameters={"threshold": 0.5},
    )
    assert rule.finding_code == "E1_TARGET_MISSING"
    assert rule.column == "target"
    assert rule.kind == "DROP_ROWS"
    assert isinstance(rule.parameters, MappingProxyType)
    assert rule.parameters["threshold"] == 0.5

    with pytest.raises(FrozenInstanceError):
        rule.column = "other"  # type: ignore[misc]

    # Slot check: should not have __dict__
    assert not hasattr(rule, "__dict__")


def test_t1_unresolved_finding_immutability_and_slots() -> None:
    unresolved = UnresolvedFinding(
        finding_code="E1_TARGET_ALL_MISSING",
        column="target",
        reason="Target column is completely missing; irresolvable.",
    )
    assert unresolved.finding_code == "E1_TARGET_ALL_MISSING"
    assert unresolved.column == "target"
    assert "Target column" in unresolved.reason

    with pytest.raises(FrozenInstanceError):
        unresolved.reason = "modified"  # type: ignore[misc]

    assert not hasattr(unresolved, "__dict__")


def test_t1_preparation_plan_immutability_and_slots() -> None:
    rule = PreparationRule(
        finding_code="E1_TARGET_MISSING",
        column="target",
        kind="DROP_ROWS",
    )
    plan = PreparationPlan(
        status="READY",
        source_dataset_hash="hash123",
        source_profile_digest="digest456",
        rules=(rule,),
        plan_digest="plan789",
    )
    assert plan.status == "READY"
    assert plan.source_dataset_hash == "hash123"
    assert plan.rules == (rule,)
    assert isinstance(plan.rules, tuple)
    assert isinstance(plan.unresolved_findings, tuple)

    with pytest.raises(FrozenInstanceError):
        plan.status = "INCOMPLETE"  # type: ignore[misc]

    assert not hasattr(plan, "__dict__")


def test_t1_sanitized_dataset_view_immutability_and_slots() -> None:
    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
    )
    col_data = np.array([1.0, 2.0], dtype=np.float64)

    view = SanitizedDatasetView(
        columns={"feat": col_data, "target": np.array([1, 0])},
        schema=schema,
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        candidate_feature_cols=("feat",),
        dropped_observation_ids=(),
        target_label_mapping={"pos": 1, "neg": 0},
        deferred_rules=(),
        source_dataset_hash="source_hash",
        source_plan_digest="plan_hash",
        dataset_hash="sanitized_hash",
    )

    assert isinstance(view.columns, MappingProxyType)
    assert isinstance(view.observation_ids, tuple)
    assert isinstance(view.target_label_mapping, MappingProxyType)
    assert view.dataset_hash == "sanitized_hash"

    with pytest.raises(FrozenInstanceError):
        view.dataset_hash = "other"  # type: ignore[misc]

    assert not hasattr(view, "__dict__")
