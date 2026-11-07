"""Unit tests for stage gates verification (stages/stage_gates.py).

Verifies STORE-03, STORE-05, STORE-06 and Checks C5, C6.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from experimental_ml.core.findings import ContractViolationError, DataIntegrityError
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.core.types import ObservationId
from experimental_ml.stages.stage_gates import (
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
from experimental_ml.validation.codecs import partition_plan_to_dict
from experimental_ml.validation.engine import build_partition_plan
from experimental_ml.validation.storage import write_splits_csv_gz, write_splits_schema
from experimental_ml.validation.types import (
    EvaluationRegime,
    PartitionConfig,
    PartitionStrategy,
)


class DummyView:
    def __init__(self, observation_ids: list[ObservationId], dataset_hash: str = "sanitized_hash_100"):
        self.observation_ids = tuple(observation_ids)
        self.dataset_hash = dataset_hash
        self.columns = {}
        self.schema = None


def _setup_valid_experiment(exp_dir: Path) -> None:
    """Helper setting up all 7 standard experiment artifacts consistently."""
    data_hash = "source_hash_999"
    sanitized_hash = "sanitized_hash_100"

    # 1. Dataset descriptor
    desc = {
        "dataset_hash": data_hash,
        "n_observations": 10,
        "n_columns": 2,
        "column_names": ["feat", "target"],
        "column_types": {"feat": "float64", "target": "int64"},
    }
    write_json_atomic(exp_dir / DATASET_DESCRIPTOR_REL_PATH, desc)

    # 2. Dataset profile
    prof = {
        "source_dataset_hash": data_hash,
        "n_rows": 10,
        "n_cols": 2,
        "memory_bytes": 160,
        "columns": {},
        "duplicate_rows": {"n_duplicate_rows": 0, "duplicate_observation_ids": [], "is_truncated": False},
        "target": {"column_name": "target", "task_type": "BINARY_CLASSIFICATION", "numeric_stats": None, "class_frequencies": None},
        "findings": [],
    }
    write_json_atomic(exp_dir / DATASET_PROFILE_REL_PATH, prof)

    # 3. Preparation plan (READY)
    plan = {
        "status": "READY",
        "source_dataset_hash": data_hash,
        "source_profile_digest": "profile_digest_abc",
        "rules": [],
        "unresolved_findings": [],
    }
    write_json_atomic(exp_dir / PREPARATION_PLAN_REL_PATH, plan)

    # 4. Sanitized view descriptor
    view_desc = {
        "dataset_hash": sanitized_hash,
        "source_dataset_hash": data_hash,
        "source_plan_digest": "plan_digest_abc",
        "n_observations": 10,
        "candidate_feature_cols": ["feat"],
        "dropped_observation_ids": [],
        "target_label_mapping": None,
        "deferred_rules": [],
    }
    write_json_atomic(exp_dir / SANITIZED_VIEW_REL_PATH, view_desc)

    # 5. Partition plan, splits, schema
    obs_ids = [ObservationId(f"id_{i}") for i in range(10)]
    view = DummyView(obs_ids, dataset_hash=sanitized_hash)
    config = PartitionConfig(
        strategy=PartitionStrategy.KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=2,
        holdout_fraction=0.2,
        shuffle=False,
        master_seed=42,
    )
    part_plan = build_partition_plan(view, config)

    write_json_atomic(exp_dir / PARTITION_PLAN_REL_PATH, partition_plan_to_dict(part_plan))
    write_splits_csv_gz(exp_dir / SPLITS_CSV_GZ_REL_PATH, part_plan)
    write_splits_schema(exp_dir / SPLITS_SCHEMA_REL_PATH, part_plan)


def test_store_05_hash_divergence_and_incomplete_plan_rejection(tmp_path: Path) -> None:
    """STORE-05 (Check C5): Detect hash divergence (DataIntegrityError) and incomplete plan (ContractViolationError)."""
    exp_dir = tmp_path / "exp1"
    _setup_valid_experiment(exp_dir)

    # Valid experiment passes both gates cleanly
    verify_preparation_gate(exp_dir)
    verify_partition_gate(exp_dir)

    # 1. Incomplete preparation plan raises ContractViolationError
    plan_path = exp_dir / PREPARATION_PLAN_REL_PATH
    bad_plan = {
        "status": "INCOMPLETE",
        "source_dataset_hash": "source_hash_999",
        "source_profile_digest": "prof_dig",
        "rules": [],
        "unresolved_findings": [{"finding_code": "E1_MISSING", "column": "feat", "reason": "unresolved"}],
    }
    write_json_atomic(plan_path, bad_plan, overwrite=True)

    with pytest.raises(ContractViolationError, match="not READY"):
        verify_preparation_gate(exp_dir)

    with pytest.raises(ContractViolationError, match="not READY"):
        verify_partition_gate(exp_dir)

    # Restore valid plan
    good_plan = {
        "status": "READY",
        "source_dataset_hash": "source_hash_999",
        "source_profile_digest": "prof_dig",
        "rules": [],
        "unresolved_findings": [],
    }
    write_json_atomic(plan_path, good_plan, overwrite=True)

    # 2. Hash divergence between profile and descriptor raises DataIntegrityError
    prof_path = exp_dir / DATASET_PROFILE_REL_PATH
    bad_prof = {
        "source_dataset_hash": "tampered_divergent_hash",
        "n_rows": 10,
        "n_cols": 2,
        "memory_bytes": 160,
        "columns": {},
        "duplicate_rows": {"n_duplicate_rows": 0, "duplicate_observation_ids": [], "is_truncated": False},
        "target": {"column_name": "target", "task_type": "BINARY_CLASSIFICATION", "numeric_stats": None, "class_frequencies": None},
        "findings": [],
    }
    write_json_atomic(prof_path, bad_prof, overwrite=True)

    with pytest.raises(DataIntegrityError, match="hash divergence"):
        verify_preparation_gate(exp_dir)


def test_store_06_splits_tampering_and_mismatch_rejection(tmp_path: Path) -> None:
    """STORE-06 (Check C6): Detect contradiction between splits.csv.gz and partition_plan.json."""
    exp_dir = tmp_path / "exp2"
    _setup_valid_experiment(exp_dir)

    # Tampering: partition plan points to a different source_dataset_hash than sanitized_view
    part_path = exp_dir / PARTITION_PLAN_REL_PATH
    part_dict = partition_plan_to_dict(
        build_partition_plan(
            DummyView([ObservationId(f"id_{i}") for i in range(10)], dataset_hash="tampered_hash_999"),
            PartitionConfig(strategy=PartitionStrategy.KFOLD, regime=EvaluationRegime.CV_ONLY, n_splits=2),
        )
    )
    write_json_atomic(part_path, part_dict, overwrite=True)

    with pytest.raises(DataIntegrityError, match="diverges from sanitized_view"):
        verify_partition_gate(exp_dir)
