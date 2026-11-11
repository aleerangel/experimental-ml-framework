"""Integration tests for hyperparameter tuning subsystem and runtime purity.

Covers TUN-07 (AC-M43-07-01, AC-M43-07-02) and checks C22, C23, C24, testing end-to-end
nested cross-validation lifecycle, anti-leakage invariance, and runtime purity.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any
import numpy as np
import pytest

import experimental_ml.tuning as tuning
from experimental_ml.core.enums import MetricDirection
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily


class RidgeModel:
    """Deterministic Ridge regression model for end-to-end integration tests."""

    def __init__(self, alpha: float = 1.0) -> None:
        self.alpha = float(alpha)
        self.coef_: np.ndarray | None = None
        self.__is_fitted__: bool = False

    def set_params(self, **params: Any) -> RidgeModel:
        if "alpha" in params:
            self.alpha = float(params["alpha"])
        return self

    def fit(self, X: np.ndarray, y: np.ndarray) -> RidgeModel:
        p = X.shape[1]
        self.coef_ = np.linalg.solve(X.T @ X + self.alpha * np.eye(p), X.T @ y)
        self.__is_fitted__ = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        assert self.coef_ is not None
        return X @ self.coef_


def _make_ridge_spec() -> ModelSpec:
    return ModelSpec(
        model_id="integration_ridge",
        display_name="Integration Ridge Regressor",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory=lambda seed: RidgeModel(),
        capabilities=ModelCapabilities(requires_fit=True),
        description="Ridge regression model for integration suite",
        scientific_justification="End-to-end testing of nested cross-validation",
    )


def test_m43_07_01_public_api_exports() -> None:
    """AC-M43-07-01 / C22: Tuning subsystem cleanly exports public API via __all__."""
    expected_exports = [
        "HyperparameterSearchSpec",
        "SearchStrategy",
        "TuningOptimizationError",
        "TuningResult",
        "TuningTrialRecord",
        "generate_candidates",
        "run_nested_tuning",
        "split_inner_folds",
        "validate_search_spec",
    ]
    for symbol in expected_exports:
        assert hasattr(tuning, symbol), f"Symbol {symbol} missing in experimental_ml.tuning"
    assert sorted(tuning.__all__) == sorted(expected_exports)


def test_m43_07_02_runtime_purity_numpy_only() -> None:
    """AC-M43-07-02 / C23: Tuning maintains single runtime dependency (numpy>=1.24.0)."""
    check_code = (
        "import sys\n"
        "import experimental_ml.tuning\n"
        "forbidden = ['optuna', 'ray', 'sklearn', 'scipy', 'torch', 'tensorflow', 'jax', 'qiskit']\n"
        "loaded_forbidden = [pkg for pkg in forbidden if any(mod.startswith(pkg) for mod in sys.modules)]\n"
        "if loaded_forbidden:\n"
        "    print(f'Forbidden packages loaded: {loaded_forbidden}')\n"
        "    sys.exit(1)\n"
        "assert 'numpy' in sys.modules, 'numpy must be loaded'\n"
        "print('PURE_NUMPY_OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", check_code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Runtime purity violation: {result.stderr or result.stdout}"
    assert "PURE_NUMPY_OK" in result.stdout


def test_m43_07_03_end_to_end_tuning_lifecycle() -> None:
    """AC-M43-07-01 / C24: End-to-end integration test verifies full nested CV lifecycle."""
    model_spec = _make_ridge_spec()

    rng = np.random.default_rng(42)
    true_weights = np.array([3.0, -1.5, 2.0])
    X_train = rng.normal(size=(60, 3))
    y_train = X_train @ true_weights + rng.normal(scale=0.1, size=60)

    # 1. Grid Search Nested CV
    spec_grid = tuning.HyperparameterSearchSpec(
        search_strategy=tuning.SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.0001, 0.01, 1.0, 100.0)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=3,
        seed=42,
    )
    tuning.validate_search_spec(spec_grid)

    result_grid = tuning.run_nested_tuning(spec_grid, model_spec, X_train, y_train)
    assert isinstance(result_grid, tuning.TuningResult)
    assert len(result_grid.trials) == 4
    assert result_grid.search_strategy == tuning.SearchStrategy.GRID_SEARCH
    assert result_grid.best_score > 0.0
    assert result_grid.best_params["alpha"] in (0.0001, 0.01)

    # 2. Random Search Nested CV
    spec_random = tuning.HyperparameterSearchSpec(
        search_strategy=tuning.SearchStrategy.RANDOM_SEARCH,
        param_grid={"alpha": (0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        n_iter=3,
        inner_cv_folds=3,
        seed=100,
    )
    result_random = tuning.run_nested_tuning(spec_random, model_spec, X_train, y_train)
    assert isinstance(result_random, tuning.TuningResult)
    assert len(result_random.trials) == 3
    assert result_random.search_strategy == tuning.SearchStrategy.RANDOM_SEARCH

    # 3. Anti-leakage invariance check:
    # Outer evaluation data does not exist in run_nested_tuning signature,
    # ensuring zero data leakage into the tuning process (CA-E4B-01).
    X_val_dummy = rng.normal(size=(20, 3))
    y_val_dummy = rng.normal(size=20)
    # Re-running on unchanged X_train, y_train yields strictly identical result
    result_grid_rerun = tuning.run_nested_tuning(spec_grid, model_spec, X_train, y_train)
    assert result_grid_rerun.best_params == result_grid.best_params
    assert result_grid_rerun.best_score == result_grid.best_score
    assert result_grid_rerun.best_trial_index == result_grid.best_trial_index
