"""Unit tests for validation storage and codecs (validation/storage.py, codecs.py).

Verifies STORE-02, STORE-04 and Check C4.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import read_json
from experimental_ml.core.types import ObservationId
from experimental_ml.validation.codecs import (
    partition_plan_from_dict,
    partition_plan_to_dict,
)
from experimental_ml.validation.engine import build_partition_plan
from experimental_ml.validation.storage import (
    read_splits_csv_gz,
    write_splits_csv_gz,
    write_splits_schema,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    PartitionConfig,
    PartitionStrategy,
)


class DummyView:
    def __init__(self, observation_ids: list[ObservationId], dataset_hash: str = "hash_dummy"):
        self.observation_ids = tuple(observation_ids)
        self.dataset_hash = dataset_hash
        self.columns = {}
        self.schema = None


def test_store_04_splits_csv_gz_deterministic(tmp_path: Path) -> None:
    """STORE-04 (Check C4): write_splits_csv_gz writes deterministic bit-identical gzip archives."""
    obs_ids = [ObservationId(f"obs_{i}") for i in range(20)]
    view = DummyView(obs_ids)

    config = PartitionConfig(
        strategy=PartitionStrategy.KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=3,
        holdout_fraction=0.2,
        shuffle=False,
        master_seed=42,
    )
    plan = build_partition_plan(view, config)

    splits_file_1 = tmp_path / "splits_1.csv.gz"
    splits_file_2 = tmp_path / "splits_2.csv.gz"

    # Write in two separate paths
    write_splits_csv_gz(splits_file_1, plan)
    write_splits_csv_gz(splits_file_2, plan)

    # 1. Determinism: bit-identical bytes
    bytes_1 = splits_file_1.read_bytes()
    bytes_2 = splits_file_2.read_bytes()
    assert bytes_1 == bytes_2

    # 2. Structure and content verification
    rows = read_splits_csv_gz(splits_file_1)
    assert len(rows) == 20
    assert list(rows[0].keys()) == ["observation_id", "holdout_role", "fold_0", "fold_1", "fold_2"]

    # Verify holdout and dev roles match plan
    holdout_set = set(str(oid) for oid in plan.holdout_ids)
    dev_set = set(str(oid) for oid in plan.development_ids)

    for row in rows:
        oid_str = row["observation_id"]
        if oid_str in holdout_set:
            assert row["holdout_role"] == "HOLDOUT"
            assert row["fold_0"] == "EXCLUDED"
            assert row["fold_1"] == "EXCLUDED"
            assert row["fold_2"] == "EXCLUDED"
        else:
            assert oid_str in dev_set
            assert row["holdout_role"] == "DEVELOPMENT"
            roles = [row["fold_0"], row["fold_1"], row["fold_2"]]
            assert roles.count("VAL") == 1
            assert roles.count("TRAIN") == 2

    # 3. Overwrite protection
    with pytest.raises(ConfigurationError, match="Target artifact already exists"):
        write_splits_csv_gz(splits_file_1, plan, overwrite=False)


def test_partition_plan_codec_roundtrip() -> None:
    """STORE-02: Lossless roundtrip for PartitionPlan."""
    obs_ids = [ObservationId(f"id_{i}") for i in range(15)]
    view = DummyView(obs_ids)

    config = PartitionConfig(
        strategy=PartitionStrategy.KFOLD,
        regime=EvaluationRegime.CV_ONLY,
        n_splits=3,
        shuffle=False,
        master_seed=123,
    )
    plan = build_partition_plan(view, config)

    plan_dict = partition_plan_to_dict(plan)
    # Check valid JSON
    json_bytes = json.dumps(plan_dict, allow_nan=False)
    restored = partition_plan_from_dict(json.loads(json_bytes))

    assert restored.plan_id == plan.plan_id
    assert restored.source_dataset_hash == plan.source_dataset_hash
    assert restored.regime == plan.regime
    assert restored.strategy == plan.strategy
    assert restored.development_ids == plan.development_ids
    assert restored.holdout_ids == plan.holdout_ids
    assert len(restored.folds) == len(plan.folds)
    for f1, f2 in zip(restored.folds, plan.folds):
        assert f1.fold_index == f2.fold_index
        assert f1.train_ids == f2.train_ids
        assert f1.val_ids == f2.val_ids


def test_splits_schema_writer(tmp_path: Path) -> None:
    """Verify write_splits_schema writes valid JSON metadata."""
    obs_ids = [ObservationId(f"id_{i}") for i in range(10)]
    view = DummyView(obs_ids)
    config = PartitionConfig(strategy=PartitionStrategy.KFOLD, regime=EvaluationRegime.CV_ONLY, n_splits=2)
    plan = build_partition_plan(view, config)

    schema_file = tmp_path / "splits.schema.json"
    write_splits_schema(schema_file, plan)
    assert schema_file.exists()

    data = read_json(schema_file)
    assert data["plan_id"] == plan.plan_id
    assert data["n_folds"] == 2
    assert data["n_total"] == 10
    assert len(data["columns"]) == 4  # obs_id, holdout_role, fold_0, fold_1
