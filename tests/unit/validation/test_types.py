"""Unit tests for validation types, enums, config boundary validation, and plan immutability."""

from dataclasses import FrozenInstanceError
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ObservationId
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def test_t1_enums_and_coercion() -> None:
    # Test strategy enum
    assert PartitionStrategy.KFOLD == "KFOLD"
    assert PartitionStrategy.STRATIFIED_KFOLD == "STRATIFIED_KFOLD"
    assert PartitionStrategy.GROUP_KFOLD == "GROUP_KFOLD"
    assert PartitionStrategy.BOOTSTRAP == "BOOTSTRAP"
    assert PartitionStrategy.TEMPORAL == "TEMPORAL"
    assert PartitionStrategy.HOLDOUT == "HOLDOUT"

    # Test regime enum
    assert EvaluationRegime.CV_ONLY == "CV_ONLY"
    assert EvaluationRegime.HOLDOUT_ONLY == "HOLDOUT_ONLY"
    assert EvaluationRegime.CV_AND_HOLDOUT == "CV_AND_HOLDOUT"

    # Coercion from string
    cfg = PartitionConfig(strategy="KFOLD", regime="CV_ONLY")
    assert cfg.strategy == PartitionStrategy.KFOLD
    assert cfg.regime == EvaluationRegime.CV_ONLY

    with pytest.raises(ConfigurationError, match="Invalid strategy"):
        PartitionConfig(strategy="INVALID_STRATEGY")

    with pytest.raises(ConfigurationError, match="Invalid regime"):
        PartitionConfig(strategy="KFOLD", regime="INVALID_REGIME")


def test_part_10_config_boundary_validation() -> None:
    # 1. n_splits < 2 in CV_ONLY
    with pytest.raises(ConfigurationError, match="n_splits must be >= 2"):
        PartitionConfig(strategy=PartitionStrategy.KFOLD, regime=EvaluationRegime.CV_ONLY, n_splits=1)

    # 2. holdout_fraction invalid in HOLDOUT_ONLY or CV_AND_HOLDOUT
    with pytest.raises(ConfigurationError, match="holdout_fraction must be in"):
        PartitionConfig(strategy=PartitionStrategy.HOLDOUT, regime=EvaluationRegime.HOLDOUT_ONLY, holdout_fraction=None)

    with pytest.raises(ConfigurationError, match="holdout_fraction must be in"):
        PartitionConfig(strategy=PartitionStrategy.KFOLD, regime=EvaluationRegime.CV_AND_HOLDOUT, holdout_fraction=0.0)

    with pytest.raises(ConfigurationError, match="holdout_fraction must be in"):
        PartitionConfig(strategy=PartitionStrategy.KFOLD, regime=EvaluationRegime.CV_AND_HOLDOUT, holdout_fraction=1.0)

    # 3. Missing group_col for GROUP_KFOLD
    with pytest.raises(ConfigurationError, match="GROUP_KFOLD strategy requires 'group_col'"):
        PartitionConfig(strategy=PartitionStrategy.GROUP_KFOLD, group_col=None)

    # 4. Missing time_col for TEMPORAL
    with pytest.raises(ConfigurationError, match="TEMPORAL strategy requires 'time_col'"):
        PartitionConfig(strategy=PartitionStrategy.TEMPORAL, time_col=None)

    # 5. Invalid n_bootstraps
    with pytest.raises(ConfigurationError, match="n_bootstraps must be >= 2"):
        PartitionConfig(strategy=PartitionStrategy.BOOTSTRAP, n_bootstraps=1)


def test_part_08_partition_plan_plan_id() -> None:
    cfg = PartitionConfig(strategy=PartitionStrategy.KFOLD, n_splits=5)
    f0 = FoldPartition(
        fold_index=0,
        train_ids=(ObservationId("obs_2"), ObservationId("obs_3")),
        val_ids=(ObservationId("obs_1"),),
    )
    plan = PartitionPlan(
        plan_id="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        source_dataset_hash="hash_123",
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=(ObservationId("obs_1"), ObservationId("obs_2"), ObservationId("obs_3")),
        holdout_ids=(),
        folds=(f0,),
        config=cfg,
    )

    assert len(plan.plan_id) == 64
    assert plan.source_dataset_hash == "hash_123"
    assert isinstance(plan.folds, tuple)
    assert isinstance(plan.development_ids, tuple)
    assert isinstance(plan.holdout_ids, tuple)

    # Immutability and slots check
    with pytest.raises(FrozenInstanceError):
        plan.plan_id = "new_id"  # type: ignore[misc]

    assert not hasattr(plan, "__dict__")
    assert not hasattr(f0, "__dict__")
    assert not hasattr(cfg, "__dict__")
