"""PartitionPlan builder engine and deterministic plan_id generation.

Complies with CA-E4A-01, CA-E4A-02, ADR-002, ADR-007, and ADR-008.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Sequence

import numpy as np

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ObservationId
from experimental_ml.validation.splitters import (
    bootstrap_split,
    group_kfold_split,
    holdout_split,
    kfold_split,
    stratified_kfold_split,
    temporal_split,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)
from experimental_ml.validation.validators import validate_partition_plan


def _compute_plan_id(
    source_dataset_hash: str,
    config: PartitionConfig,
    development_ids: Sequence[ObservationId],
    holdout_ids: Sequence[ObservationId],
    folds: Sequence[FoldPartition],
) -> str:
    """Compute canonical 64-character SHA-256 digest for PartitionPlan (D8, ADR-007)."""
    hasher = hashlib.sha256()

    # Config frame
    config_repr = (
        f"{config.strategy.value}|{config.regime.value}|{config.n_splits}|"
        f"{config.holdout_fraction}|{config.n_bootstraps}|{config.time_col}|"
        f"{config.group_col}|{config.stratify}|{config.shuffle}|{config.master_seed}"
    )
    hasher.update(config_repr.encode("utf-8"))
    hasher.update(b"|")
    hasher.update(source_dataset_hash.encode("ascii"))
    hasher.update(b"|")

    # Development and holdout counts and sample IDs
    hasher.update(f"dev:{len(development_ids)};holdout:{len(holdout_ids)}|".encode("utf-8"))
    for oid in development_ids:
        hasher.update(str(oid).encode("utf-8") + b",")
    hasher.update(b"|")
    for oid in holdout_ids:
        hasher.update(str(oid).encode("utf-8") + b",")
    hasher.update(b"|")

    # Folds frame
    for f in folds:
        hasher.update(f"f{f.fold_index}:t{len(f.train_ids)}:v{len(f.val_ids)}:".encode("utf-8"))
        for tid in f.train_ids:
            hasher.update(str(tid).encode("utf-8") + b",")
        hasher.update(b":")
        for vid in f.val_ids:
            hasher.update(str(vid).encode("utf-8") + b",")
        hasher.update(b";")

    return hasher.hexdigest()


def build_partition_plan(
    data_or_view: Any,
    config: PartitionConfig,
) -> PartitionPlan:
    """Build a deterministic, validated PartitionPlan from data view and configuration.

    Consumes contracts exposed by SanitizedDatasetView or DatasetBundle without coupling
    to internal preparation implementations (M2.3 architectural boundary).

    Args:
        data_or_view: SanitizedDatasetView or DatasetBundle.
        config: Validated PartitionConfig.

    Returns:
        Immutable PartitionPlan mathematically validated via validate_partition_plan.

    Raises:
        ConfigurationError: If requested columns are missing or parameters are incompatible.
        DataIntegrityError: If mathematical partition validation fails.
    """
    obs_ids: tuple[ObservationId, ...] = tuple(data_or_view.observation_ids)
    source_hash: str = data_or_view.dataset_hash
    n_total = len(obs_ids)

    # 1. Resolve columns for stratification, grouping, and time
    target: np.ndarray | None = None
    if config.stratify or config.strategy == PartitionStrategy.STRATIFIED_KFOLD:
        target_col = getattr(data_or_view.schema, "target_col", None)
        if target_col and target_col in data_or_view.columns:
            target = data_or_view.columns[target_col]
        else:
            raise ConfigurationError(
                f"Stratification requested but target column '{target_col}' not available in dataset"
            )

    group_col_name = config.group_col or getattr(data_or_view.schema, "group_col", None)
    groups: np.ndarray | None = None
    if group_col_name:
        if group_col_name in data_or_view.columns:
            groups = data_or_view.columns[group_col_name]
        elif config.strategy == PartitionStrategy.GROUP_KFOLD:
            raise ConfigurationError(
                f"GROUP_KFOLD requested but group column '{group_col_name}' not in dataset columns"
            )

    time_col_name = config.time_col or getattr(data_or_view.schema, "time_col", None)
    times: np.ndarray | None = None
    if time_col_name:
        if time_col_name in data_or_view.columns:
            times = data_or_view.columns[time_col_name]
        elif config.strategy == PartitionStrategy.TEMPORAL:
            raise ConfigurationError(
                f"TEMPORAL requested but time column '{time_col_name}' not in dataset columns"
            )

    # 2. Regimes: Holdout separation (D7)
    obs_to_idx = {oid: i for i, oid in enumerate(obs_ids)}

    if config.regime == EvaluationRegime.CV_ONLY:
        development_ids = obs_ids
        holdout_ids = ()
        dev_target = target
        dev_groups = groups
        dev_times = times
    elif config.regime in (EvaluationRegime.HOLDOUT_ONLY, EvaluationRegime.CV_AND_HOLDOUT):
        assert config.holdout_fraction is not None
        development_ids, holdout_ids = holdout_split(
            observation_ids=obs_ids,
            holdout_fraction=config.holdout_fraction,
            stratify=config.stratify,
            target=target,
            seed=config.master_seed,
        )
        dev_indices = [obs_to_idx[oid] for oid in development_ids]
        dev_target = target[dev_indices] if target is not None else None
        dev_groups = groups[dev_indices] if groups is not None else None
        dev_times = times[dev_indices] if times is not None else None
    else:
        raise ConfigurationError(f"Unsupported EvaluationRegime '{config.regime}'")

    # 3. Strategy dispatch on development_ids
    if config.regime == EvaluationRegime.HOLDOUT_ONLY or config.strategy == PartitionStrategy.HOLDOUT:
        raw_folds = [(development_ids, holdout_ids)]
    elif config.strategy == PartitionStrategy.KFOLD:
        raw_folds = kfold_split(
            observation_ids=development_ids,
            n_splits=config.n_splits,
            shuffle=config.shuffle,
            seed=config.master_seed,
        )
    elif config.strategy == PartitionStrategy.STRATIFIED_KFOLD:
        if dev_target is None:
            raise ConfigurationError("STRATIFIED_KFOLD requires valid target column in development set")
        raw_folds = stratified_kfold_split(
            observation_ids=development_ids,
            target=dev_target,
            n_splits=config.n_splits,
            shuffle=config.shuffle,
            seed=config.master_seed,
        )
    elif config.strategy == PartitionStrategy.GROUP_KFOLD:
        if dev_groups is None:
            raise ConfigurationError("GROUP_KFOLD requires valid group column in development set")
        raw_folds = group_kfold_split(
            observation_ids=development_ids,
            groups=dev_groups,
            n_splits=config.n_splits,
            shuffle=config.shuffle,
            seed=config.master_seed,
        )
    elif config.strategy == PartitionStrategy.BOOTSTRAP:
        n_boot = config.n_bootstraps or 100
        raw_folds = bootstrap_split(
            observation_ids=development_ids,
            n_bootstraps=n_boot,
            seed=config.master_seed,
        )
    elif config.strategy == PartitionStrategy.TEMPORAL:
        if dev_times is None:
            raise ConfigurationError("TEMPORAL strategy requires valid time column in development set")
        raw_folds = temporal_split(
            observation_ids=development_ids,
            times=dev_times,
            n_splits=config.n_splits,
        )
    else:
        raise ConfigurationError(f"Unsupported strategy '{config.strategy}'")

    folds = tuple(
        FoldPartition(fold_index=k, train_ids=tr, val_ids=va)
        for k, (tr, va) in enumerate(raw_folds)
    )

    # 4. Compute deterministic plan_id (D8, ADR-007)
    plan_id = _compute_plan_id(
        source_dataset_hash=source_hash,
        config=config,
        development_ids=development_ids,
        holdout_ids=holdout_ids,
        folds=folds,
    )

    plan = PartitionPlan(
        plan_id=plan_id,
        source_dataset_hash=source_hash,
        regime=config.regime,
        strategy=config.strategy,
        development_ids=development_ids,
        holdout_ids=holdout_ids,
        folds=folds,
        config=config,
    )

    # 5. Math integrity validation
    validate_partition_plan(plan, data_or_view)

    return plan
