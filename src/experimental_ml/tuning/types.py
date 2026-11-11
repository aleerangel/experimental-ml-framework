"""Types, enums, and immutable dataclasses for hyperparameter tuning (Stage 3B)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from experimental_ml.core.enums import MetricDirection, MetricStatus
from experimental_ml.core.findings import ContractViolationError

__all__ = [
    "SearchStrategy",
    "TuningOptimizationError",
    "HyperparameterSearchSpec",
    "TuningTrialRecord",
    "TuningResult",
]


class SearchStrategy(str, Enum):
    """Supported hyperparameter search strategies."""

    FIXED = "FIXED"
    GRID_SEARCH = "GRID_SEARCH"
    RANDOM_SEARCH = "RANDOM_SEARCH"
    CUSTOM_TUNER = "CUSTOM_TUNER"


class TuningOptimizationError(ContractViolationError):
    """Raised when hyperparameter tuning fails completely or all trials produce UNDEFINED_NAN."""


@dataclass(frozen=True, slots=True)
class HyperparameterSearchSpec:
    """Declarative specification for hyperparameter search within an outer training partition."""

    search_strategy: SearchStrategy
    param_grid: MappingProxyType[str, tuple[Any, ...]]
    optimization_metric: str
    direction: MetricDirection
    n_iter: int | None = None
    inner_cv_folds: int = 3
    seed: int | None = None
    description: str = ""

    def __init__(
        self,
        search_strategy: SearchStrategy | str,
        param_grid: Mapping[str, Any],
        optimization_metric: str,
        direction: MetricDirection | str,
        n_iter: int | None = None,
        inner_cv_folds: int = 3,
        seed: int | None = None,
        description: str = "",
    ) -> None:
        object.__setattr__(
            self,
            "search_strategy",
            SearchStrategy(search_strategy) if isinstance(search_strategy, str) else search_strategy,
        )
        normalized_grid: dict[str, tuple[Any, ...]] = {}
        for k, v in param_grid.items():
            if isinstance(v, (list, tuple)):
                normalized_grid[str(k)] = tuple(v)
            else:
                normalized_grid[str(k)] = (v,)
        object.__setattr__(self, "param_grid", MappingProxyType(normalized_grid))
        object.__setattr__(self, "optimization_metric", str(optimization_metric))
        object.__setattr__(
            self,
            "direction",
            MetricDirection(direction) if isinstance(direction, str) else direction,
        )
        object.__setattr__(self, "n_iter", int(n_iter) if n_iter is not None else None)
        object.__setattr__(self, "inner_cv_folds", int(inner_cv_folds))
        object.__setattr__(self, "seed", int(seed) if seed is not None else None)
        object.__setattr__(self, "description", str(description))


@dataclass(frozen=True, slots=True)
class TuningTrialRecord:
    """Immutable record of an individual hyperparameter evaluation trial across inner folds."""

    trial_index: int
    params: MappingProxyType[str, Any]
    fold_scores: tuple[float, ...]
    mean_score: float
    status: MetricStatus
    error_message: str | None = None

    def __init__(
        self,
        trial_index: int,
        params: Mapping[str, Any],
        fold_scores: tuple[float, ...] | list[float],
        mean_score: float,
        status: MetricStatus | str,
        error_message: str | None = None,
    ) -> None:
        object.__setattr__(self, "trial_index", int(trial_index))
        object.__setattr__(self, "params", MappingProxyType(dict(params)))
        object.__setattr__(self, "fold_scores", tuple(float(s) for s in fold_scores))
        object.__setattr__(self, "mean_score", float(mean_score))
        object.__setattr__(
            self,
            "status",
            MetricStatus(status) if isinstance(status, str) else status,
        )
        object.__setattr__(
            self,
            "error_message",
            str(error_message) if error_message is not None else None,
        )


@dataclass(frozen=True, slots=True)
class TuningResult:
    """Immutable consolidated outcome of a nested hyperparameter tuning execution."""

    best_params: MappingProxyType[str, Any]
    best_score: float
    best_trial_index: int
    trials: tuple[TuningTrialRecord, ...]
    search_strategy: SearchStrategy
    optimization_metric: str

    def __init__(
        self,
        best_params: Mapping[str, Any],
        best_score: float,
        best_trial_index: int,
        trials: tuple[TuningTrialRecord, ...] | list[TuningTrialRecord],
        search_strategy: SearchStrategy | str,
        optimization_metric: str,
    ) -> None:
        object.__setattr__(self, "best_params", MappingProxyType(dict(best_params)))
        object.__setattr__(self, "best_score", float(best_score))
        object.__setattr__(self, "best_trial_index", int(best_trial_index))
        object.__setattr__(self, "trials", tuple(trials))
        object.__setattr__(
            self,
            "search_strategy",
            SearchStrategy(search_strategy) if isinstance(search_strategy, str) else search_strategy,
        )
        object.__setattr__(self, "optimization_metric", str(optimization_metric))
