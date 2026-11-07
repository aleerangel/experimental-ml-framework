"""Mathematical validation of PartitionPlan invariants.

Complies with CA-E4A-01, ADR-002, and RF4.2.
"""

from __future__ import annotations

from typing import Any

from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.validation.types import (
    EvaluationRegime,
    PartitionPlan,
    PartitionStrategy,
)


def validate_partition_plan(
    plan: PartitionPlan,
    data_or_view: Any,
) -> None:
    """Mathematically verify partition disjointness and structural integrity (PART-07).

    Validates:
    1. Development and holdout subsets are disjoint and partition the source dataset.
    2. For every fold k: Train_k ∩ Val_k = ∅.
    3. For every fold k: (Train_k ∪ Val_k) ∩ Holdout = ∅.
    4. For GROUP_KFOLD: Groups(Train_k) ∩ Groups(Val_k) = ∅.
    5. For TEMPORAL: max(Time(Train_k)) <= min(Time(Val_k)).
    6. For standard CV: complete coverage of development observations across validation sets.

    Args:
        plan: Immutable PartitionPlan to validate.
        data_or_view: SanitizedDatasetView or DatasetBundle source.

    Raises:
        DataIntegrityError: If any mathematical or structural invariant is violated.
    """
    source_obs_set = set(data_or_view.observation_ids)
    dev_set = set(plan.development_ids)
    holdout_set = set(plan.holdout_ids)

    # 1. Universe and disjointness of dev/holdout
    if not dev_set.issubset(source_obs_set):
        raise DataIntegrityError("development_ids contains identifiers not present in source dataset")
    if not holdout_set.issubset(source_obs_set):
        raise DataIntegrityError("holdout_ids contains identifiers not present in source dataset")
    if not dev_set.isdisjoint(holdout_set):
        overlap = dev_set & holdout_set
        raise DataIntegrityError(f"development_ids and holdout_ids overlap: {overlap}")
    if (dev_set | holdout_set) != source_obs_set:
        raise DataIntegrityError("development_ids and holdout_ids do not span source dataset observations")

    # Mapping helpers for group and time validation
    group_map: dict[Any, Any] | None = None
    if plan.config.group_col and plan.config.group_col in data_or_view.columns:
        grp_col = data_or_view.columns[plan.config.group_col]
        group_map = {oid: grp_col[i] for i, oid in enumerate(data_or_view.observation_ids)}

    time_map: dict[Any, Any] | None = None
    if plan.config.time_col and plan.config.time_col in data_or_view.columns:
        tm_col = data_or_view.columns[plan.config.time_col]
        time_map = {oid: tm_col[i] for i, oid in enumerate(data_or_view.observation_ids)}

    val_sets_union: set[Any] = set()

    for fold in plan.folds:
        train_s = set(fold.train_ids)
        val_s = set(fold.val_ids)

        # 2. Train_k ∩ Val_k = ∅
        if not train_s.isdisjoint(val_s):
            overlap = train_s & val_s
            raise DataIntegrityError(
                f"Fold {fold.fold_index} violates disjointness: Train and Val overlap on {overlap}"
            )

        # 3. Holdout isolation: (Train_k ∪ Val_k) ∩ Holdout = ∅
        if not train_s.isdisjoint(holdout_set):
            overlap = train_s & holdout_set
            raise DataIntegrityError(
                f"Fold {fold.fold_index} leaks holdout observations into Train: {overlap}"
            )
        if not val_s.isdisjoint(holdout_set):
            overlap = val_s & holdout_set
            raise DataIntegrityError(
                f"Fold {fold.fold_index} leaks holdout observations into Val: {overlap}"
            )

        # Ensure train and val belong to development_ids
        if not train_s.issubset(dev_set):
            raise DataIntegrityError(
                f"Fold {fold.fold_index} Train contains observations outside development set"
            )
        if not val_s.issubset(dev_set):
            raise DataIntegrityError(
                f"Fold {fold.fold_index} Val contains observations outside development set"
            )

        # 4. Group disjointness
        if plan.strategy == PartitionStrategy.GROUP_KFOLD and group_map is not None:
            train_groups = {group_map[oid] for oid in fold.train_ids}
            val_groups = {group_map[oid] for oid in fold.val_ids}
            if not train_groups.isdisjoint(val_groups):
                overlap_grps = train_groups & val_groups
                raise DataIntegrityError(
                    f"Fold {fold.fold_index} violates group isolation: overlapping groups {overlap_grps}"
                )

        # 5. Temporal monotonicity
        if plan.strategy == PartitionStrategy.TEMPORAL and time_map is not None:
            train_times = [time_map[oid] for oid in fold.train_ids]
            val_times = [time_map[oid] for oid in fold.val_ids]
            if len(train_times) > 0 and len(val_times) > 0:
                if max(train_times) > min(val_times):
                    raise DataIntegrityError(
                        f"Fold {fold.fold_index} violates temporal monotonicity: "
                        f"max Train time ({max(train_times)}) > min Val time ({min(val_times)})"
                    )

        val_sets_union.update(val_s)

    # 6. Standard K-Fold / Stratified complete coverage
    if plan.strategy in (PartitionStrategy.KFOLD, PartitionStrategy.STRATIFIED_KFOLD):
        if plan.regime in (EvaluationRegime.CV_ONLY, EvaluationRegime.CV_AND_HOLDOUT):
            if val_sets_union != dev_set:
                missing = dev_set - val_sets_union
                raise DataIntegrityError(
                    f"Validation sets across folds do not completely cover development_ids. Missing: {len(missing)}"
                )
