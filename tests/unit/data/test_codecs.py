"""Unit tests for data layer lossless codecs (data/codecs.py).

Verifies STORE-02, STORE-03 and Check C2.
"""

from __future__ import annotations

import json
from types import MappingProxyType
import numpy as np
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.core.types import ObservationId
from experimental_ml.data import (
    DatasetSchemaSpec,
    PreparationRule,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
)
from experimental_ml.data.codecs import (
    dataset_descriptor_from_dict,
    dataset_descriptor_to_dict,
    dataset_profile_from_dict,
    dataset_profile_to_dict,
    preparation_plan_from_dict,
    preparation_plan_to_dict,
    sanitized_view_descriptor_from_dict,
    sanitized_view_descriptor_to_dict,
)
from experimental_ml.data.descriptors import DatasetDescriptor, SanitizedViewDescriptor


def test_store_02_lossless_codecs_roundtrip() -> None:
    """STORE-02 (Check C2): Lossless roundtrip for profile, plan, and descriptors without NaN/Inf."""
    # 1. DatasetDescriptor roundtrip
    desc = DatasetDescriptor(
        dataset_hash="hash_123456",
        raw_source_hash="source_hash_abc",
        n_observations=100,
        n_columns=4,
        column_names=("feat1", "feat2", "target", "group"),
        column_types=MappingProxyType({"feat1": "float64", "feat2": "object", "target": "int64", "group": "object"}),
        target_col="target",
        task_type="BINARY_CLASSIFICATION",
        group_col="group",
        time_col=None,
    )
    desc_dict = dataset_descriptor_to_dict(desc)
    json_bytes = json.dumps(desc_dict, allow_nan=False)
    desc_restored = dataset_descriptor_from_dict(json.loads(json_bytes))

    assert desc_restored.dataset_hash == desc.dataset_hash
    assert desc_restored.raw_source_hash == desc.raw_source_hash
    assert desc_restored.n_observations == desc.n_observations
    assert desc_restored.column_names == desc.column_names
    assert dict(desc_restored.column_types) == dict(desc.column_types)
    assert desc_restored.target_col == desc.target_col
    assert desc_restored.task_type == desc.task_type
    assert desc_restored.group_col == desc.group_col

    # 2. SanitizedViewDescriptor roundtrip
    view_desc = SanitizedViewDescriptor(
        dataset_hash="sanitized_hash_789",
        source_dataset_hash="hash_123456",
        source_plan_digest="plan_digest_xyz",
        n_observations=95,
        candidate_feature_cols=("feat1", "feat2"),
        dropped_observation_ids=(ObservationId("obs_1"), ObservationId("obs_5")),
        target_label_mapping=MappingProxyType({"yes": 1, "no": 0}),
        deferred_rules=(
            PreparationRule("E1_CATEGORICAL_UNENCODED", "feat2", "DEFER_INTRA_FOLD", {"encoding_strategy": "ORDINAL"}),
        ),
    )
    view_dict = sanitized_view_descriptor_to_dict(view_desc)
    json_bytes_view = json.dumps(view_dict, allow_nan=False)
    view_restored = sanitized_view_descriptor_from_dict(json.loads(json_bytes_view))

    assert view_restored.dataset_hash == view_desc.dataset_hash
    assert view_restored.source_dataset_hash == view_desc.source_dataset_hash
    assert view_restored.source_plan_digest == view_desc.source_plan_digest
    assert view_restored.n_observations == 95
    assert view_restored.candidate_feature_cols == ("feat1", "feat2")
    assert view_restored.dropped_observation_ids == (ObservationId("obs_1"), ObservationId("obs_5"))
    assert dict(view_restored.target_label_mapping) == {"yes": 1, "no": 0}
    assert len(view_restored.deferred_rules) == 1
    assert view_restored.deferred_rules[0].column == "feat2"

    # 3. DatasetProfile & PreparationPlan roundtrip from real profile
    data = {
        "num": [10.0, 20.0, np.nan, 40.0],
        "cat": ["A", "B", "A", "C"],
        "target": [1, 0, 1, 0],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)

    prof_dict = dataset_profile_to_dict(profile)
    # Check that allow_nan=False does not raise (no NaN/Infinity in dict)
    json_str = json.dumps(prof_dict, allow_nan=False)
    profile_restored = dataset_profile_from_dict(json.loads(json_str))

    assert profile_restored.source_dataset_hash == profile.source_dataset_hash
    assert profile_restored.n_rows == profile.n_rows
    assert profile_restored.n_cols == profile.n_cols
    assert profile_restored.columns["num"].n_missing == 1
    assert profile_restored.columns["num"].missing_proportion == 0.25
    assert profile_restored.columns["cat"].categorical_stats.cardinality == 3

    # PreparationPlan roundtrip
    rules = [
        PreparationRule("E1_FEATURE_MISSING", "num", "DROP_ROWS"),
        PreparationRule("E1_CATEGORICAL_UNENCODED", "cat", "ACCEPT_AS_IS"),
    ]
    plan = create_preparation_plan(profile, rules)
    plan_dict = preparation_plan_to_dict(plan)
    json_str_plan = json.dumps(plan_dict, allow_nan=False)
    plan_restored = preparation_plan_from_dict(json.loads(json_str_plan))

    assert plan_restored.status == plan.status
    assert plan_restored.source_dataset_hash == plan.source_dataset_hash
    assert plan_restored.source_profile_digest == plan.source_profile_digest
    assert plan_restored.plan_digest == plan.plan_digest
    assert len(plan_restored.rules) == len(plan.rules)
    assert plan_restored.rules == plan.rules

    # 4. Immutability checks: modifying restored objects raises FrozenInstanceError
    with pytest.raises(Exception):
        desc_restored.dataset_hash = "tampered"  # type: ignore[misc]

    with pytest.raises(Exception):
        view_restored.dataset_hash = "tampered"  # type: ignore[misc]

    with pytest.raises(Exception):
        plan_restored.status = "INCOMPLETE"  # type: ignore[misc]
