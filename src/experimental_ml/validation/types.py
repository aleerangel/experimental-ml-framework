"""Validation types, strategies, evaluation regimes, and partition contracts.

Complies with ADR-002 (no data leakage), ADR-007, ADR-008, RF4.1 and RF4.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ObservationId


class PartitionStrategy(StrEnum):
    """Supported data partitioning and resampling strategies."""

    KFOLD = "KFOLD"
    STRATIFIED_KFOLD = "STRATIFIED_KFOLD"
    GROUP_KFOLD = "GROUP_KFOLD"
    BOOTSTRAP = "BOOTSTRAP"
    TEMPORAL = "TEMPORAL"
    HOLDOUT = "HOLDOUT"


class EvaluationRegime(StrEnum):
    """High-level evaluation regimes governing development vs final holdout."""

    CV_ONLY = "CV_ONLY"
    HOLDOUT_ONLY = "HOLDOUT_ONLY"
    CV_AND_HOLDOUT = "CV_AND_HOLDOUT"


@dataclass(frozen=True, slots=True)
class FoldPartition:
    """Individual train/validation split for a fold or resampling repetition."""

    fold_index: int
    train_ids: tuple[ObservationId, ...]
    val_ids: tuple[ObservationId, ...]

    def __post_init__(self) -> None:
        if self.fold_index < 0:
            raise ConfigurationError(f"fold_index must be >= 0, got {self.fold_index}")
        if not isinstance(self.train_ids, tuple):
            object.__setattr__(self, "train_ids", tuple(self.train_ids))
        if not isinstance(self.val_ids, tuple):
            object.__setattr__(self, "val_ids", tuple(self.val_ids))


@dataclass(frozen=True, slots=True)
class PartitionConfig:
    """Configuration specification for generating partition plans."""

    strategy: PartitionStrategy
    regime: EvaluationRegime = EvaluationRegime.CV_ONLY
    n_splits: int = 5
    holdout_fraction: float | None = None
    n_bootstraps: int | None = None
    time_col: str | None = None
    group_col: str | None = None
    stratify: bool = False
    shuffle: bool = True
    master_seed: int = 42

    def __post_init__(self) -> None:
        # Coerce strategy
        if not isinstance(self.strategy, PartitionStrategy):
            try:
                object.__setattr__(self, "strategy", PartitionStrategy(self.strategy))
            except Exception as err:
                raise ConfigurationError(f"Invalid strategy '{self.strategy}'") from err

        # Coerce regime
        if not isinstance(self.regime, EvaluationRegime):
            try:
                object.__setattr__(self, "regime", EvaluationRegime(self.regime))
            except Exception as err:
                raise ConfigurationError(f"Invalid regime '{self.regime}'") from err

        # Boundary checks
        if self.regime in (EvaluationRegime.CV_ONLY, EvaluationRegime.CV_AND_HOLDOUT):
            if self.strategy not in (PartitionStrategy.BOOTSTRAP, PartitionStrategy.HOLDOUT):
                if self.n_splits < 2:
                    raise ConfigurationError(
                        f"Cross-validation n_splits must be >= 2, got {self.n_splits}"
                    )

        if self.strategy == PartitionStrategy.BOOTSTRAP:
            b_count = self.n_bootstraps if self.n_bootstraps is not None else 100
            if b_count < 2:
                raise ConfigurationError(
                    f"n_bootstraps must be >= 2, got {b_count}"
                )
            object.__setattr__(self, "n_bootstraps", b_count)

        if self.regime in (EvaluationRegime.HOLDOUT_ONLY, EvaluationRegime.CV_AND_HOLDOUT):
            if self.holdout_fraction is None or not (0.0 < self.holdout_fraction < 1.0):
                raise ConfigurationError(
                    f"holdout_fraction must be in (0.0, 1.0) for regime '{self.regime.value}', "
                    f"got {self.holdout_fraction}"
                )

        if self.strategy == PartitionStrategy.TEMPORAL and self.time_col is None:
            raise ConfigurationError("TEMPORAL strategy requires 'time_col' to be specified")

        if self.strategy == PartitionStrategy.GROUP_KFOLD and self.group_col is None:
            raise ConfigurationError("GROUP_KFOLD strategy requires 'group_col' to be specified")


@dataclass(frozen=True, slots=True)
class PartitionPlan:
    """Immutable, shared partition plan across all matrix experiments (CA-E4A-01, CA-E4A-02)."""

    plan_id: str
    source_dataset_hash: str
    regime: EvaluationRegime
    strategy: PartitionStrategy
    development_ids: tuple[ObservationId, ...]
    holdout_ids: tuple[ObservationId, ...]
    folds: tuple[FoldPartition, ...]
    config: PartitionConfig

    def __post_init__(self) -> None:
        if not isinstance(self.development_ids, tuple):
            object.__setattr__(self, "development_ids", tuple(self.development_ids))
        if not isinstance(self.holdout_ids, tuple):
            object.__setattr__(self, "holdout_ids", tuple(self.holdout_ids))
        if not isinstance(self.folds, tuple):
            object.__setattr__(self, "folds", tuple(self.folds))
