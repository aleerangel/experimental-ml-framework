"""Unit tests for undefined metric handling and total tuning failure (TUN-06)."""

from __future__ import annotations

import math
from typing import Any
import numpy as np
import pytest

from experimental_ml.core.enums import MetricDirection, MetricStatus
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily
from experimental_ml.tuning.engine import run_nested_tuning
from experimental_ml.tuning.types import (
    HyperparameterSearchSpec,
    SearchStrategy,
    TuningOptimizationError,
)


class DegenerateModel:
    """Model that can be configured to produce NaN, raise exceptions, or predict constants."""

    def __init__(self, mode: str = "valid") -> None:
        self.mode = mode
        self.__is_fitted__: bool = False

    def set_params(self, **params: Any) -> DegenerateModel:
        if "mode" in params:
            self.mode = str(params["mode"])
        return self

    def fit(self, X: np.ndarray, y: np.ndarray) -> DegenerateModel:
        if self.mode == "fail_fit":
            raise RuntimeError("Fit deliberate failure")
        self.__is_fitted__ = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.mode == "fail_pred":
            raise RuntimeError("Predict deliberate failure")
        if self.mode == "nan_pred":
            return np.full(X.shape[0], np.nan)
        if self.mode == "constant":
            # Predicting constant causes zero-variance in R2 calculation
            return np.ones(X.shape[0]) * 42.0
        # Valid prediction
        return np.ones(X.shape[0]) * 1.5


def _make_degenerate_spec() -> ModelSpec:
    return ModelSpec(
        model_id="degenerate_model",
        display_name="Degenerate Test Model",
        family=ModelFamily.CUSTOM,
        estimator_factory=lambda seed: DegenerateModel(),
        capabilities=ModelCapabilities(requires_fit=True),
        description="Model for testing failure modes in tuning",
        scientific_justification="Unit testing ADR-005 failure handling",
    )


def test_m43_06_01_undefined_nan_disqualification() -> None:
    """C19: run_nested_tuning marks candidates producing UNDEFINED_NAN as disqualified."""
    model_spec = _make_degenerate_spec()

    rng = np.random.default_rng(42)
    X = rng.normal(size=(30, 2))
    # y with variation
    y = np.linspace(1.0, 10.0, 30)

    # Candidate 0: 'nan_pred' (returns NaN, causing UNDEFINED_NAN)
    # Candidate 1: 'valid' (returns valid predictions)
    spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"mode": ("nan_pred", "valid")},
        optimization_metric="r2",
        direction=MetricDirection.MAXIMIZE,
        inner_cv_folds=3,
    )

    result = run_nested_tuning(spec, model_spec, X, y)
    assert len(result.trials) == 2

    trial_nan = result.trials[0]
    trial_valid = result.trials[1]

    # Trial 0 must be marked UNDEFINED_NAN and disqualified
    assert trial_nan.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(trial_nan.mean_score)

    # Trial 1 must be VALID
    assert trial_valid.status == MetricStatus.VALID
    assert math.isfinite(trial_valid.mean_score)

    # Valid candidate must win, never the disqualified candidate
    assert result.best_params["mode"] == "valid"
    assert result.best_trial_index == 1


def test_m43_06_02_all_candidates_fail_raises_error() -> None:
    """C20: run_nested_tuning raises TuningOptimizationError when all candidates fail."""
    model_spec = _make_degenerate_spec()

    X = np.ones((20, 2))
    y = np.ones(20)

    # Both candidates fail: one in fit, one in predict
    spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"mode": ("fail_fit", "fail_pred")},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=2,
    )

    with pytest.raises(TuningOptimizationError, match="All 2 hyperparameter candidate trials failed"):
        run_nested_tuning(spec, model_spec, X, y)


def test_m43_06_03_error_preserves_trial_details() -> None:
    """C21: TuningOptimizationError preserves diagnostic details and inherits from ContractViolationError."""
    model_spec = _make_degenerate_spec()

    X = np.ones((20, 2))
    y = np.ones(20)

    spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"mode": ("fail_fit",)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=2,
    )

    with pytest.raises(TuningOptimizationError) as exc_info:
        run_nested_tuning(spec, model_spec, X, y)

    err = exc_info.value
    # Verifies inheritance from ContractViolationError
    assert isinstance(err, ContractViolationError)
    # Verifies preserved trial details
    assert "fail_fit" in str(err)
    assert "Fit deliberate failure" in str(err)
