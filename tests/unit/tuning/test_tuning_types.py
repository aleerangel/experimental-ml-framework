"""Unit tests for tuning types, enums, dataclasses, and exceptions (TUN-01)."""

import pytest
from experimental_ml.core.enums import MetricDirection, MetricStatus
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.tuning.types import (
    HyperparameterSearchSpec,
    SearchStrategy,
    TuningOptimizationError,
    TuningResult,
    TuningTrialRecord,
)


def test_m43_01_01_search_strategy_enum() -> None:
    """C1: SearchStrategy is a closed Enum with all canonical members."""
    expected = {"FIXED", "GRID_SEARCH", "RANDOM_SEARCH", "CUSTOM_TUNER"}
    members = {s.value for s in SearchStrategy}
    assert members == expected
    assert SearchStrategy.FIXED == "FIXED"
    assert SearchStrategy.GRID_SEARCH == "GRID_SEARCH"
    assert SearchStrategy.RANDOM_SEARCH == "RANDOM_SEARCH"
    assert SearchStrategy.CUSTOM_TUNER == "CUSTOM_TUNER"


def test_m43_01_02_search_spec_dataclass() -> None:
    """C2: HyperparameterSearchSpec is an immutable frozen dataclass with slots."""
    spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"n_estimators": [10, 50], "max_depth": (3, 5)},
        optimization_metric="RMSE",
        direction=MetricDirection.MINIMIZE,
        n_iter=None,
        inner_cv_folds=3,
        seed=42,
        description="Grid search for tree ensemble",
    )
    assert spec.search_strategy == SearchStrategy.GRID_SEARCH
    assert spec.optimization_metric == "RMSE"
    assert spec.direction == MetricDirection.MINIMIZE
    assert spec.param_grid["n_estimators"] == (10, 50)
    assert spec.param_grid["max_depth"] == (3, 5)
    assert spec.inner_cv_folds == 3
    assert spec.seed == 42
    assert spec.description == "Grid search for tree ensemble"

    # Immutability
    with pytest.raises(Exception):
        spec.inner_cv_folds = 5  # type: ignore[misc]

    with pytest.raises(Exception):
        spec.param_grid["n_estimators"] = (100,)  # type: ignore[index]


def test_m43_01_03_trial_record_dataclass() -> None:
    """C3: TuningTrialRecord is an immutable frozen dataclass with slots."""
    trial = TuningTrialRecord(
        trial_index=0,
        params={"lr": 0.01},
        fold_scores=(0.15, 0.12, 0.18),
        mean_score=0.15,
        status=MetricStatus.VALID,
        error_message=None,
    )
    assert trial.trial_index == 0
    assert trial.params["lr"] == 0.01
    assert trial.fold_scores == (0.15, 0.12, 0.18)
    assert trial.mean_score == 0.15
    assert trial.status == MetricStatus.VALID
    assert trial.error_message is None

    # Immutability
    with pytest.raises(Exception):
        trial.mean_score = 0.20  # type: ignore[misc]


def test_m43_01_04_tuning_result_dataclass() -> None:
    """C4: TuningResult is an immutable frozen dataclass with slots."""
    trial1 = TuningTrialRecord(
        trial_index=0,
        params={"depth": 3},
        fold_scores=(0.80, 0.82),
        mean_score=0.81,
        status=MetricStatus.VALID,
    )
    trial2 = TuningTrialRecord(
        trial_index=1,
        params={"depth": 5},
        fold_scores=(0.85, 0.87),
        mean_score=0.86,
        status=MetricStatus.VALID,
    )
    result = TuningResult(
        best_params={"depth": 5},
        best_score=0.86,
        best_trial_index=1,
        trials=[trial1, trial2],
        search_strategy=SearchStrategy.GRID_SEARCH,
        optimization_metric="R2",
    )
    assert result.best_params["depth"] == 5
    assert result.best_score == 0.86
    assert result.best_trial_index == 1
    assert len(result.trials) == 2
    assert result.search_strategy == SearchStrategy.GRID_SEARCH
    assert result.optimization_metric == "R2"

    with pytest.raises(Exception):
        result.best_score = 0.90  # type: ignore[misc]


def test_m43_01_05_tuning_error_inheritance() -> None:
    """C5: TuningOptimizationError inherits from ContractViolationError."""
    assert issubclass(TuningOptimizationError, ContractViolationError)
    err = TuningOptimizationError("All candidates produced UNDEFINED_NAN")
    assert isinstance(err, ContractViolationError)
    assert str(err) == "All candidates produced UNDEFINED_NAN"
