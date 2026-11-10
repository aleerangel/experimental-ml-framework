"""Intra-fold feature selection engine and evaluation projection.

Complies with SEL-01, SEL-02, SEL-03, SEL-04, SEL-05, SEL-07, RF2.4, ADR-002, and ADR-008.
Ensures zero data leakage by adjusting selection criteria strictly on fold training data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
)
from experimental_ml.features.scenarios import FeatureScenario, ScenarioMode
from experimental_ml.features.stats import (
    compute_correlation_ratio,
    compute_cramers_v,
    compute_pearson,
)


def _is_numeric(arr: np.ndarray) -> bool:
    """Check if array has continuous/numeric data type (excluding booleans)."""
    return bool(
        (np.issubdtype(arr.dtype, np.floating) or np.issubdtype(arr.dtype, np.integer))
        and not np.issubdtype(arr.dtype, np.bool_)
    )


@dataclass(frozen=True, slots=True)
class SelectionResult:
    """Immutable result of an intra-fold feature selection execution."""

    selected_features: tuple[str, ...]
    scores: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    fitted_params: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    strategy_name: str = "FIXED"

    def __post_init__(self) -> None:
        if not isinstance(self.selected_features, tuple):
            object.__setattr__(self, "selected_features", tuple(self.selected_features))

        if not isinstance(self.scores, MappingProxyType):
            object.__setattr__(self, "scores", MappingProxyType(dict(self.scores)))

        if not isinstance(self.fitted_params, MappingProxyType):
            object.__setattr__(self, "fitted_params", MappingProxyType(dict(self.fitted_params)))

        if not isinstance(self.strategy_name, str):
            object.__setattr__(self, "strategy_name", str(self.strategy_name))

    def to_dict(self) -> dict[str, Any]:
        """Serialize SelectionResult to a JSON-compliant primitive dictionary."""
        return {
            "selected_features": list(self.selected_features),
            "scores": dict(self.scores),
            "fitted_params": dict(self.fitted_params),
            "strategy_name": self.strategy_name,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SelectionResult:
        """Reconstruct SelectionResult from dictionary representation."""
        return cls(
            selected_features=tuple(data.get("selected_features", ())),
            scores=MappingProxyType(dict(data.get("scores", {}))),
            fitted_params=MappingProxyType(dict(data.get("fitted_params", {}))),
            strategy_name=data.get("strategy_name", "FIXED"),
        )


def select_features_in_fold(
    X_train: Mapping[str, np.ndarray],
    y_train: np.ndarray | None,
    scenario: FeatureScenario,
    random_state: int | None = None,
) -> SelectionResult:
    """Select predictor features strictly within the fold training data.

    Enforces zero data leakage (RF2.4, ADR-002). For FIXED scenarios, bypasses calculation
    and returns static features. For DYNAMIC scenarios, fits parameters exclusively on
    (X_train, y_train).

    Args:
        X_train: Mapping of feature names to 1D training arrays.
        y_train: 1D training target array (required for supervised strategies).
        scenario: Validated FeatureScenario instance.
        random_state: Optional random seed for reproducible stochastic selection.

    Returns:
        Immutable SelectionResult with selected features, scores, and fitted parameters.

    Raises:
        ContractViolationError: If inputs are invalid or missing required target.
        ConfigurationError: If dynamic strategy name is unsupported or parameters invalid.
        DataIntegrityError: If dynamic selection results in 0 selected features.
    """
    if not isinstance(scenario, FeatureScenario):
        raise ContractViolationError(
            f"select_features_in_fold requires a FeatureScenario, got {type(scenario).__name__}"
        )

    if not X_train:
        raise ContractViolationError("X_train mapping cannot be empty.")

    # 1. FIXED Mode: immediate bypass without data dependence (SEL-02)
    if scenario.mode == ScenarioMode.FIXED:
        return SelectionResult(
            selected_features=scenario.selected_features,
            scores=MappingProxyType({}),
            fitted_params=MappingProxyType({}),
            strategy_name="FIXED",
        )

    # 2. DYNAMIC Mode: execute strategy strictly on fold training data
    strategy = scenario.strategy_name
    params = scenario.strategy_params

    if strategy == "VARIANCE_THRESHOLD":
        threshold = float(params.get("threshold", 0.0))
        scores: dict[str, float] = {}
        selected: list[str] = []

        for feat_name, arr in sorted(X_train.items()):
            if _is_numeric(arr):
                valid = arr[~np.isnan(arr)]
                if len(valid) > 1:
                    var_val = float(np.var(valid, ddof=1))
                else:
                    var_val = 0.0
                scores[feat_name] = var_val
                if var_val > threshold:
                    selected.append(feat_name)

        if not selected:
            raise DataIntegrityError(
                f"Variance threshold selection with threshold={threshold} resulted in 0 selected features."
            )

        # Sort selected features by descending variance, then name
        selected.sort(key=lambda f: (-scores[f], f))
        return SelectionResult(
            selected_features=tuple(selected),
            scores=MappingProxyType(scores),
            fitted_params=MappingProxyType({"threshold": threshold}),
            strategy_name="VARIANCE_THRESHOLD",
        )

    elif strategy in ("TOP_K_RELEVANCE", "MUTUAL_INFO_TOP_K"):
        if y_train is None:
            raise ContractViolationError(
                f"Supervised selection strategy '{strategy}' requires y_train."
            )

        k = int(params.get("k", 5))
        if k <= 0:
            raise ConfigurationError(f"Strategy parameter 'k' must be positive, got {k}")

        y_is_num = _is_numeric(y_train)
        scores = {}

        for feat_name, arr in sorted(X_train.items()):
            feat_is_num = _is_numeric(arr)
            if feat_is_num and y_is_num:
                val, stat = compute_pearson(arr, y_train)
            elif not feat_is_num and not y_is_num:
                val, stat = compute_cramers_v(arr, y_train)
            else:
                if feat_is_num:
                    val, stat = compute_correlation_ratio(categories=y_train, continuous=arr)
                else:
                    val, stat = compute_correlation_ratio(categories=arr, continuous=y_train)

            abs_val = abs(val) if not math.isnan(val) else 0.0
            scores[feat_name] = float(abs_val)

        # Rank all features by descending score
        ranked_features = sorted(X_train.keys(), key=lambda f: (-scores[f], f))
        top_k = ranked_features[:k]

        if not top_k:
            raise DataIntegrityError(
                f"Top-K relevance selection with k={k} resulted in 0 selected features."
            )

        return SelectionResult(
            selected_features=tuple(top_k),
            scores=MappingProxyType(scores),
            fitted_params=MappingProxyType({"k": k, "strategy": strategy}),
            strategy_name=strategy,
        )

    else:
        raise ConfigurationError(
            f"Unsupported dynamic feature selection strategy: '{strategy}'. "
            "Supported strategies: ['VARIANCE_THRESHOLD', 'TOP_K_RELEVANCE', 'MUTUAL_INFO_TOP_K']"
        )


def apply_feature_selection(
    X_eval: Mapping[str, np.ndarray],
    selection_result: SelectionResult,
) -> dict[str, np.ndarray]:
    """Project the feature selection fitted on training data onto evaluation data (SEL-05).

    Filters columns in X_eval to retain strictly the features present in
    selection_result.selected_features in identical order, without data leakage.

    Args:
        X_eval: Mapping of feature names to 1D evaluation arrays (validation or test fold).
        selection_result: Validated SelectionResult produced by select_features_in_fold.

    Returns:
        Dictionary of filtered feature arrays ordered canonically by selected_features.

    Raises:
        ContractViolationError: If selection_result is invalid or any selected feature
            is missing from X_eval.
    """
    if not isinstance(selection_result, SelectionResult):
        raise ContractViolationError(
            f"apply_feature_selection requires a SelectionResult, got {type(selection_result).__name__}"
        )

    filtered: dict[str, np.ndarray] = {}
    for feat_name in selection_result.selected_features:
        if feat_name not in X_eval:
            raise ContractViolationError(
                f"Selected feature '{feat_name}' is missing from evaluation data."
            )
        filtered[feat_name] = X_eval[feat_name]

    return filtered


__all__ = [
    "SelectionResult",
    "select_features_in_fold",
    "apply_feature_selection",
]
