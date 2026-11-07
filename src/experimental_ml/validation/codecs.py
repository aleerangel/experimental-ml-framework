"""Lossless codecs for validation layer objects.

Complies with STORE-02, STORE-03, RFC 8259, and ADR-008.
"""

from __future__ import annotations

from typing import Any

from experimental_ml.core.types import ObservationId
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def partition_plan_to_dict(plan: PartitionPlan) -> dict[str, Any]:
    """Serialize PartitionPlan to standard JSON-compatible dict."""
    folds_list = [
        {
            "fold_index": f.fold_index,
            "train_ids": [str(oid) for oid in f.train_ids],
            "val_ids": [str(oid) for oid in f.val_ids],
        }
        for f in plan.folds
    ]

    config_dict = {
        "strategy": plan.config.strategy.value,
        "regime": plan.config.regime.value,
        "n_splits": plan.config.n_splits,
        "holdout_fraction": plan.config.holdout_fraction,
        "n_bootstraps": plan.config.n_bootstraps,
        "time_col": plan.config.time_col,
        "group_col": plan.config.group_col,
        "stratify": plan.config.stratify,
        "shuffle": plan.config.shuffle,
        "master_seed": plan.config.master_seed,
    }

    return {
        "plan_id": plan.plan_id,
        "source_dataset_hash": plan.source_dataset_hash,
        "regime": plan.regime.value,
        "strategy": plan.strategy.value,
        "development_ids": [str(oid) for oid in plan.development_ids],
        "holdout_ids": [str(oid) for oid in plan.holdout_ids],
        "folds": folds_list,
        "config": config_dict,
    }


def partition_plan_from_dict(d: dict[str, Any]) -> PartitionPlan:
    """Reconstruct PartitionPlan from dict."""
    cfg_d = d["config"]
    config = PartitionConfig(
        strategy=PartitionStrategy(cfg_d["strategy"]),
        regime=EvaluationRegime(cfg_d["regime"]),
        n_splits=cfg_d.get("n_splits", 5),
        holdout_fraction=cfg_d.get("holdout_fraction"),
        n_bootstraps=cfg_d.get("n_bootstraps"),
        time_col=cfg_d.get("time_col"),
        group_col=cfg_d.get("group_col"),
        stratify=bool(cfg_d.get("stratify", False)),
        shuffle=bool(cfg_d.get("shuffle", True)),
        master_seed=int(cfg_d.get("master_seed", 42)),
    )

    folds = tuple(
        FoldPartition(
            fold_index=int(f["fold_index"]),
            train_ids=tuple(ObservationId(oid) for oid in f["train_ids"]),
            val_ids=tuple(ObservationId(oid) for oid in f["val_ids"]),
        )
        for f in d["folds"]
    )

    return PartitionPlan(
        plan_id=d["plan_id"],
        source_dataset_hash=d["source_dataset_hash"],
        regime=EvaluationRegime(d["regime"]),
        strategy=PartitionStrategy(d["strategy"]),
        development_ids=tuple(ObservationId(oid) for oid in d["development_ids"]),
        holdout_ids=tuple(ObservationId(oid) for oid in d["holdout_ids"]),
        folds=folds,
        config=config,
    )
