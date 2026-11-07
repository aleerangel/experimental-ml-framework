"""Integration tests for M2.2 preparation planning and sanitization pipeline.

Verifies end-to-end flows, determinism, bundle immutability, and architectural
import isolation per PREP-10 and ADR-002.
"""

from __future__ import annotations

import ast
import os
import numpy as np
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    PreparationPlan,
    PreparationRule,
    SanitizedDatasetView,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)


def test_prep_10_immutability_and_determinism() -> None:
    """PREP-10: Sourced DatasetBundle remains bit-identical and repeated runs produce identical hashes."""
    data = {
        "feat_num": [10.0, 20.0, np.nan, 40.0, 50.0],
        "feat_cat": ["A", "B", "A", "C", "B"],
        "feat_const": [1, 1, 1, 1, 1],
        "target": ["pos", "neg", "pos", "neg", "pos"],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)

    initial_hash = bundle.dataset_hash
    initial_arrays = {col: arr.copy() for col, arr in bundle.columns.items()}

    rules = [
        PreparationRule("E1_FEATURE_MISSING", "feat_num", "DROP_ROWS"),
        PreparationRule("E1_CATEGORICAL_UNENCODED", "feat_cat", "DEFER_INTRA_FOLD", {"encoding_strategy": "ONE_HOT"}),
        PreparationRule("E1_CONSTANT_COLUMN", "feat_const", "EXCLUDE_COLUMN"),
        PreparationRule("E1_TARGET_BINARY_UNMAPPED", "target", "MAP_BINARY_TARGET", {"positive_label": "pos"}),
    ]

    plan_1 = create_preparation_plan(profile, rules)
    assert plan_1.status == "READY"
    view_1 = sanitize_dataset(bundle, profile, plan_1)

    # 1. Immutability verification: bundle remains 100% bit-identical
    assert bundle.dataset_hash == initial_hash
    for col, orig_arr in initial_arrays.items():
        assert len(bundle.columns[col]) == len(orig_arr)
        for v1, v2 in zip(bundle.columns[col], orig_arr):
            assert (v1 == v2) or (isinstance(v1, float) and np.isnan(v1) and np.isnan(v2))
        assert not bundle.columns[col].flags.writeable

    # 2. Determinism verification: identical inputs produce identical plan digest and view hash
    plan_2 = create_preparation_plan(profile, rules)
    view_2 = sanitize_dataset(bundle, profile, plan_2)

    assert plan_1.plan_digest == plan_2.plan_digest
    assert view_1.dataset_hash == view_2.dataset_hash
    assert view_1.source_dataset_hash == view_2.source_dataset_hash
    assert view_1.observation_ids == view_2.observation_ids
    assert view_1.candidate_feature_cols == view_2.candidate_feature_cols
    assert view_1.dropped_observation_ids == view_2.dropped_observation_ids


def test_end_to_end_preparation_pipeline() -> None:
    """Exercise complete workflow with multiple diagnostic findings and structural resolution."""
    data = {
        "feature_1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "feature_missing": [10.0, np.nan, 30.0, 40.0, np.nan, 60.0],
        "feature_constant": [42.0, 42.0, 42.0, 42.0, 42.0, 42.0],
        "target": ["class_1", "class_2", "class_1", "class_2", "class_1", "class_2"],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)

    rules = [
        PreparationRule("E1_FEATURE_MISSING", "feature_missing", "DEFER_INTRA_FOLD", {"imputation_strategy": "MEDIAN"}),
        PreparationRule("E1_CONSTANT_COLUMN", "feature_constant", "EXCLUDE_COLUMN"),
        PreparationRule("E1_TARGET_BINARY_UNMAPPED", "target", "MAP_BINARY_TARGET", {"positive_label": "class_1"}),
    ]

    plan = create_preparation_plan(profile, rules)
    assert plan.status == "READY"

    view = sanitize_dataset(bundle, profile, plan)

    assert isinstance(view, SanitizedDatasetView)
    assert "feature_constant" not in view.columns
    assert "feature_missing" in view.columns
    assert "feature_1" in view.candidate_feature_cols
    assert "feature_missing" in view.candidate_feature_cols
    assert view.columns["target"].dtype == np.int64
    assert set(view.columns["target"]) == {0, 1}
    assert view.target_label_mapping == {"class_1": 1, "class_2": 0}


def test_architectural_import_direction_data_preparation() -> None:
    """Verify that preparation module does not import from validation, models, or cli."""
    prep_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "src",
        "experimental_ml",
        "data",
        "preparation.py",
    )
    prep_path = os.path.abspath(prep_path)

    with open(prep_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=prep_path)

    forbidden_prefixes = (
        "experimental_ml.validation",
        "experimental_ml.models",
        "experimental_ml.experiments",
        "experimental_ml.cli",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for prefix in forbidden_prefixes:
                    assert not alias.name.startswith(prefix), f"preparation.py imports {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for prefix in forbidden_prefixes:
                assert not mod.startswith(prefix), f"preparation.py imports from {mod}"
