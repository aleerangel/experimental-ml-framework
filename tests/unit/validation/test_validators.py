"""Unit tests for mathematical partition plan validation (CA-E4A-01, PART-07)."""

from dataclasses import dataclass
from types import MappingProxyType
import numpy as np
import pytest

from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.core.types import ObservationId
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)
from experimental_ml.validation.validators import validate_partition_plan


@dataclass(frozen=True, slots=True)
class DummyDataView:
    observation_ids: tuple[ObservationId, ...]
    columns: MappingProxyType[str, np.ndarray]
    dataset_hash: str = "dummy_hash"


def test_part_07_validate_partition_plan_invariants() -> None:
    obs = tuple(ObservationId(f"obs_{i}") for i in range(10))
    data = DummyDataView(
        observation_ids=obs,
        columns=MappingProxyType({}),
    )

    cfg = PartitionConfig(strategy=PartitionStrategy.KFOLD, n_splits=2)
    f0 = FoldPartition(0, train_ids=obs[5:], val_ids=obs[:5])
    f1 = FoldPartition(1, train_ids=obs[:5], val_ids=obs[5:])

    plan = PartitionPlan(
        plan_id="valid_id",
        source_dataset_hash="dummy_hash",
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=obs,
        holdout_ids=(),
        folds=(f0, f1),
        config=cfg,
    )

    # Valid plan passes cleanly
    validate_partition_plan(plan, data)

    # 1. Overlap between Train and Val in a fold raises DataIntegrityError
    bad_f0 = FoldPartition(0, train_ids=obs[4:], val_ids=obs[:5])  # obs_4 in both!
    bad_plan_1 = PartitionPlan(
        plan_id="bad_1",
        source_dataset_hash="dummy_hash",
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=obs,
        holdout_ids=(),
        folds=(bad_f0, f1),
        config=cfg,
    )
    with pytest.raises(DataIntegrityError, match="Train and Val overlap"):
        validate_partition_plan(bad_plan_1, data)

    # 2. Holdout leakage into Train raises DataIntegrityError
    dev = obs[:8]
    holdout = obs[8:]
    f_leak = FoldPartition(0, train_ids=obs[4:9], val_ids=obs[:4])  # obs_8 is in holdout and train!
    bad_plan_2 = PartitionPlan(
        plan_id="bad_2",
        source_dataset_hash="dummy_hash",
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        strategy=PartitionStrategy.KFOLD,
        development_ids=dev,
        holdout_ids=holdout,
        folds=(f_leak,),
        config=cfg,
    )
    with pytest.raises(DataIntegrityError, match="leaks holdout observations"):
        validate_partition_plan(bad_plan_2, data)


def test_validator_group_and_temporal_invariants() -> None:
    obs = tuple(ObservationId(f"obs_{i}") for i in range(6))
    groups = np.array(["g1", "g1", "g2", "g2", "g3", "g3"], dtype=object)
    times = np.array([10, 20, 30, 40, 50, 60], dtype=np.int64)

    data = DummyDataView(
        observation_ids=obs,
        columns=MappingProxyType({"grp": groups, "t": times}),
    )

    # 1. Group overlap detection
    cfg_grp = PartitionConfig(strategy=PartitionStrategy.GROUP_KFOLD, group_col="grp", n_splits=2)
    # Fold where g2 is in both train and val
    bad_grp_f = FoldPartition(0, train_ids=(obs[0], obs[1], obs[2]), val_ids=(obs[3], obs[4], obs[5]))
    bad_grp_plan = PartitionPlan(
        plan_id="bad_grp",
        source_dataset_hash="dummy_hash",
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.GROUP_KFOLD,
        development_ids=obs,
        holdout_ids=(),
        folds=(bad_grp_f,),
        config=cfg_grp,
    )
    with pytest.raises(DataIntegrityError, match="violates group isolation"):
        validate_partition_plan(bad_grp_plan, data)

    # 2. Temporal forward leakage detection
    cfg_time = PartitionConfig(strategy=PartitionStrategy.TEMPORAL, time_col="t", n_splits=2)
    # Train has time 50 (obs_4), Val has time 20 (obs_1) -> max(train) > min(val)
    bad_time_f = FoldPartition(0, train_ids=(obs[0], obs[4]), val_ids=(obs[1], obs[2]))
    bad_time_plan = PartitionPlan(
        plan_id="bad_time",
        source_dataset_hash="dummy_hash",
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.TEMPORAL,
        development_ids=obs,
        holdout_ids=(),
        folds=(bad_time_f,),
        config=cfg_time,
    )
    with pytest.raises(DataIntegrityError, match="violates temporal monotonicity"):
        validate_partition_plan(bad_time_plan, data)
