"""Integration tests for M2.4 artifacts persistence and stage gates.

Verifies end-to-end lifecycle, standard directory layout (STORE-03, Check C3),
cryptographic hash linkage, tamper detection, and layer import direction isolation.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
import numpy as np
import pytest

from experimental_ml.core import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
)
from experimental_ml.core.enums import TaskType
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.data import (
    DatasetSchemaSpec,
    PreparationRule,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.data.codecs import (
    dataset_descriptor_to_dict,
    dataset_profile_to_dict,
    preparation_plan_to_dict,
    sanitized_view_descriptor_to_dict,
)
from experimental_ml.data.descriptors import (
    DatasetDescriptor,
    SanitizedViewDescriptor,
)
from experimental_ml.stages import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    PARTITION_PLAN_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    SANITIZED_VIEW_REL_PATH,
    SPLITS_CSV_GZ_REL_PATH,
    SPLITS_SCHEMA_REL_PATH,
    verify_partition_gate,
    verify_preparation_gate,
)
from experimental_ml.validation import (
    EvaluationRegime,
    PartitionConfig,
    PartitionStrategy,
    build_partition_plan,
)
from experimental_ml.validation.codecs import partition_plan_to_dict
from experimental_ml.validation.storage import (
    read_splits_csv_gz,
    write_splits_csv_gz,
    write_splits_schema,
)


def test_store_03_experiment_directory_layout(tmp_path: Path) -> None:
    """STORE-03 (Check C3): Full end-to-end experiment layout creation and stage gates verification."""
    exp_dir = tmp_path / "experiment_run_01"

    # 1. Ingestion & Profile (Stage 1A)
    raw_data = {
        "feature_1": [float(i * 1.5) for i in range(50)],
        "feature_2": ["cat_a" if i % 2 == 0 else "cat_b" for i in range(50)],
        "target": [1 if i % 3 == 0 else 0 for i in range(50)],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(raw_data, schema=schema)
    profile = profile_dataset(bundle)

    # Write Stage 1A artifacts
    desc = DatasetDescriptor(
        dataset_hash=bundle.dataset_hash,
        n_observations=len(bundle.observation_ids),
        n_columns=len(bundle.columns),
        column_names=tuple(bundle.columns.keys()),
        column_types={c: str(bundle.columns[c].dtype) for c in bundle.columns},
        target_col=schema.target_col,
        task_type=schema.task_type.value,
    )
    write_json_atomic(exp_dir / DATASET_DESCRIPTOR_REL_PATH, dataset_descriptor_to_dict(desc))
    write_json_atomic(exp_dir / DATASET_PROFILE_REL_PATH, dataset_profile_to_dict(profile))

    # 2. Preparation Plan & Sanitization (Stage 1B)
    rules = [
        PreparationRule("E1_CATEGORICAL_UNENCODED", "feature_2", "DEFER_INTRA_FOLD", {"encoding_strategy": "ORDINAL"}),
    ]
    prep_plan = create_preparation_plan(profile, rules)
    assert prep_plan.status == "READY"
    view = sanitize_dataset(bundle, profile, prep_plan)

    write_json_atomic(exp_dir / PREPARATION_PLAN_REL_PATH, preparation_plan_to_dict(prep_plan))

    view_desc = SanitizedViewDescriptor(
        dataset_hash=view.dataset_hash,
        source_dataset_hash=view.source_dataset_hash,
        source_plan_digest=view.source_plan_digest,
        n_observations=len(view.observation_ids),
        candidate_feature_cols=view.candidate_feature_cols,
        dropped_observation_ids=view.dropped_observation_ids,
        target_label_mapping=view.target_label_mapping,
        deferred_rules=view.deferred_rules,
    )
    write_json_atomic(exp_dir / SANITIZED_VIEW_REL_PATH, sanitized_view_descriptor_to_dict(view_desc))

    # Preparation gate passes
    verify_preparation_gate(exp_dir)

    # 3. Partitioning Engine (Stage 4A)
    part_config = PartitionConfig(
        strategy=PartitionStrategy.STRATIFIED_KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=3,
        holdout_fraction=0.2,
        stratify=True,
        master_seed=42,
    )
    part_plan = build_partition_plan(view, part_config)

    write_json_atomic(exp_dir / PARTITION_PLAN_REL_PATH, partition_plan_to_dict(part_plan))
    write_splits_csv_gz(exp_dir / SPLITS_CSV_GZ_REL_PATH, part_plan)
    write_splits_schema(exp_dir / SPLITS_SCHEMA_REL_PATH, part_plan)

    # Partition gate passes
    verify_partition_gate(exp_dir)

    # All 7 standard experiment files exist
    assert (exp_dir / DATASET_DESCRIPTOR_REL_PATH).exists()
    assert (exp_dir / DATASET_PROFILE_REL_PATH).exists()
    assert (exp_dir / PREPARATION_PLAN_REL_PATH).exists()
    assert (exp_dir / SANITIZED_VIEW_REL_PATH).exists()
    assert (exp_dir / PARTITION_PLAN_REL_PATH).exists()
    assert (exp_dir / SPLITS_CSV_GZ_REL_PATH).exists()
    assert (exp_dir / SPLITS_SCHEMA_REL_PATH).exists()

    # 4. Tamper detection: modifying splits.csv.gz causes partition gate failure
    # Re-writing with corrupt observation ID
    tampered_plan = build_partition_plan(view, PartitionConfig(
        strategy=PartitionStrategy.STRATIFIED_KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=3,
        holdout_fraction=0.2,
        stratify=True,
        master_seed=999,  # different seed!
    ))
    write_splits_csv_gz(exp_dir / SPLITS_CSV_GZ_REL_PATH, tampered_plan, overwrite=True)

    with pytest.raises(DataIntegrityError):
        verify_partition_gate(exp_dir)


def test_architectural_import_direction_artifacts_stage_gates() -> None:
    """Verify architectural layer isolation: core and data do not import higher layers."""
    base_src = Path(__file__).resolve().parent.parent.parent / "src" / "experimental_ml"

    # Core must not import data, validation, stages, cli, models
    core_dir = base_src / "core"
    forbidden_for_core = (
        "experimental_ml.data",
        "experimental_ml.validation",
        "experimental_ml.stages",
        "experimental_ml.cli",
        "experimental_ml.models",
    )
    for py_file in core_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_for_core:
                        assert not alias.name.startswith(prefix), f"{py_file.name} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for prefix in forbidden_for_core:
                    assert not mod.startswith(prefix), f"{py_file.name} imports from {mod}"

    # Data must not import validation, stages, cli, models
    data_dir = base_src / "data"
    forbidden_for_data = (
        "experimental_ml.validation",
        "experimental_ml.stages",
        "experimental_ml.cli",
        "experimental_ml.models",
    )
    for py_file in data_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_for_data:
                        assert not alias.name.startswith(prefix), f"{py_file.name} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for prefix in forbidden_for_data:
                    assert not mod.startswith(prefix), f"{py_file.name} imports from {mod}"
