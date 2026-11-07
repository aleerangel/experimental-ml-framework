"""Integration tests for M2.3 partitioning engine.

Verifies end-to-end integration with SanitizedDatasetView, determinism,
immutability (PART-09, Check C9), and architectural import direction isolation.
"""

from __future__ import annotations

import ast
import os
import numpy as np
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    PreparationRule,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.validation import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
    build_partition_plan,
    validate_partition_plan,
)


def test_part_09_immutability_and_determinism() -> None:
    """PART-09 (Check C9): Repeated calls with identical seed produce identical plan_id and partitions."""
    data = {
        "feat_num": [float(i) for i in range(50)],
        "target": [i % 2 for i in range(50)],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)
    plan_prep = create_preparation_plan(profile, [])
    view = sanitize_dataset(bundle, profile, plan_prep)

    config_1 = PartitionConfig(
        strategy=PartitionStrategy.STRATIFIED_KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=5,
        holdout_fraction=0.2,
        stratify=True,
        master_seed=42,
    )
    config_2 = PartitionConfig(
        strategy=PartitionStrategy.STRATIFIED_KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=5,
        holdout_fraction=0.2,
        stratify=True,
        master_seed=42,
    )

    plan_1 = build_partition_plan(view, config_1)
    plan_2 = build_partition_plan(view, config_2)

    # Determinism across repeated executions
    assert plan_1.plan_id == plan_2.plan_id
    assert len(plan_1.plan_id) == 64
    assert plan_1.development_ids == plan_2.development_ids
    assert plan_1.holdout_ids == plan_2.holdout_ids
    assert len(plan_1.folds) == len(plan_2.folds)
    for f1, f2 in zip(plan_1.folds, plan_2.folds):
        assert f1.fold_index == f2.fold_index
        assert f1.train_ids == f2.train_ids
        assert f1.val_ids == f2.val_ids

    # Different master_seed generates different plan_id
    config_diff_seed = PartitionConfig(
        strategy=PartitionStrategy.STRATIFIED_KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=5,
        holdout_fraction=0.2,
        stratify=True,
        master_seed=999,
    )
    plan_diff = build_partition_plan(view, config_diff_seed)
    assert plan_diff.plan_id != plan_1.plan_id

    # Immutability verification: frozen dataclass raises on modification
    with pytest.raises(Exception):
        plan_1.plan_id = "tampered_id"  # type: ignore[misc]

    with pytest.raises(Exception):
        plan_1.folds[0].val_ids = ()  # type: ignore[misc]


def test_validation_end_to_end_with_sanitized_dataset_view() -> None:
    """End-to-end flow from loaded dataset through sanitization to partition plan."""
    data = {
        "feature_1": [float(i * 2) for i in range(60)],
        "feature_2": ["cat_a" if i % 2 == 0 else "cat_b" for i in range(60)],
        "target": [1 if i >= 30 else 0 for i in range(60)],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)

    rules = [
        PreparationRule("E1_CATEGORICAL_UNENCODED", "feature_2", "DEFER_INTRA_FOLD", {"encoding_strategy": "ORDINAL"}),
    ]
    prep_plan = create_preparation_plan(profile, rules)
    sanitized_view = sanitize_dataset(bundle, profile, prep_plan)

    config = PartitionConfig(
        strategy=PartitionStrategy.STRATIFIED_KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=3,
        holdout_fraction=0.2,
        stratify=True,
        master_seed=123,
    )

    plan = build_partition_plan(sanitized_view, config)

    assert plan.source_dataset_hash == sanitized_view.dataset_hash
    assert len(plan.holdout_ids) == 12  # 20% of 60
    assert len(plan.development_ids) == 48  # 80% of 60
    assert len(plan.folds) == 3

    # Mathematical validation succeeds cleanly
    validate_partition_plan(plan, sanitized_view)


def test_architectural_import_direction_validation() -> None:
    """Verify that validation package does not import models, cli, or internal data modules."""
    validation_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "src",
        "experimental_ml",
        "validation",
    )
    validation_dir = os.path.abspath(validation_dir)

    forbidden_prefixes = (
        "experimental_ml.models",
        "experimental_ml.experiments",
        "experimental_ml.cli",
        "experimental_ml.data.preparation",
        "experimental_ml.data.profiling",
    )

    py_files = [f for f in os.listdir(validation_dir) if f.endswith(".py")]
    assert len(py_files) >= 4

    for filename in py_files:
        filepath = os.path.join(validation_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_prefixes:
                        assert not alias.name.startswith(prefix), (
                            f"{filename} imports forbidden module {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for prefix in forbidden_prefixes:
                    assert not mod.startswith(prefix), (
                        f"{filename} imports forbidden module {mod}"
                    )
