"""Unit tests for nested cross-validation engine and parameter optimization (TUN-05)."""

from __future__ import annotations

from typing import Any
import numpy as np
import pytest

from experimental_ml.core.enums import MetricDirection
from experimental_ml.models.preprocessing.types import PreprocessingStepSpec, TwoLayerPreprocessingSpec
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily
from experimental_ml.tuning.engine import run_nested_tuning
from experimental_ml.tuning.types import HyperparameterSearchSpec, SearchStrategy


class SimpleLinearModel:
    """Deterministic linear regressor for testing hyperparameter tuning."""

    def __init__(self, alpha: float = 1.0) -> None:
        self.alpha = float(alpha)
        self.coef_: np.ndarray | None = None
        self.__is_fitted__: bool = False

    def set_params(self, **params: Any) -> SimpleLinearModel:
        if "alpha" in params:
            self.alpha = float(params["alpha"])
        return self

    def fit(self, X: np.ndarray, y: np.ndarray) -> SimpleLinearModel:
        # Simple Ridge: (X^T X + alpha * I)^(-1) X^T y
        p = X.shape[1]
        self.coef_ = np.linalg.solve(X.T @ X + self.alpha * np.eye(p), X.T @ y)
        self.__is_fitted__ = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        assert self.coef_ is not None
        return X @ self.coef_


def _make_dummy_model_spec(factory_tracker: list[Any] | None = None) -> ModelSpec:
    def factory(seed: int | None = None) -> SimpleLinearModel:
        instance = SimpleLinearModel()
        if factory_tracker is not None:
            factory_tracker.append(instance)
        return instance

    return ModelSpec(
        model_id="test_linear",
        display_name="Test Linear Model",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory=factory,
        capabilities=ModelCapabilities(requires_fit=True),
        description="Linear model for testing nested CV",
        scientific_justification="Unit testing nested tuning execution",
    )


def test_m43_05_01_fresh_model_instances_per_fold() -> None:
    """C16: run_nested_tuning instantiates fresh model instances per candidate and inner fold."""
    instances_created: list[Any] = []
    model_spec = _make_dummy_model_spec(instances_created)

    rng = np.random.default_rng(42)
    X = rng.normal(size=(30, 3))
    y = X @ np.array([1.5, -2.0, 0.5]) + rng.normal(scale=0.1, size=30)

    spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.01, 0.1)},  # 2 candidates
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=3,  # 3 folds
    )

    result = run_nested_tuning(spec, model_spec, X, y)
    assert len(result.trials) == 2

    # 2 candidates * 3 folds = 6 distinct instances allocated
    assert len(instances_created) == 6
    # Verify all instances are distinct objects in memory
    assert len({id(inst) for inst in instances_created}) == 6


def test_m43_05_02_metric_computation_and_aggregation() -> None:
    """C17: run_nested_tuning computes internal fold metrics via catalog and aggregates mean."""
    model_spec = _make_dummy_model_spec()

    rng = np.random.default_rng(100)
    X = rng.normal(size=(40, 2))
    y = X @ np.array([2.0, -1.0]) + rng.normal(scale=0.05, size=40)

    spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.001, 10.0)},
        optimization_metric="mae",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=4,
    )

    result = run_nested_tuning(spec, model_spec, X, y)
    assert len(result.trials) == 2

    for trial in result.trials:
        assert len(trial.fold_scores) == 4
        # Mean score is the exact arithmetic mean of the 4 fold scores
        expected_mean = float(np.mean(trial.fold_scores))
        assert pytest.approx(trial.mean_score, rel=1e-9) == expected_mean
        assert trial.mean_score > 0.0


def test_m43_05_03_direction_selection_and_tie_breaking() -> None:
    """C18: run_nested_tuning selects winning candidate by declared direction with deterministic tie-breaking."""
    model_spec = _make_dummy_model_spec()

    rng = np.random.default_rng(200)
    X = rng.normal(size=(50, 3))
    y = X @ np.array([1.0, 2.0, 3.0]) + rng.normal(scale=0.1, size=50)

    # 1. MINIMIZE direction: lower RMSE is better
    spec_min = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.001, 1.0, 100.0)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=3,
    )
    res_min = run_nested_tuning(spec_min, model_spec, X, y)
    assert res_min.best_params["alpha"] == 0.001
    assert res_min.best_score == min(t.mean_score for t in res_min.trials)

    # 2. MAXIMIZE direction: higher R2 is better
    spec_max = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.001, 1.0, 100.0)},
        optimization_metric="r2",
        direction=MetricDirection.MAXIMIZE,
        inner_cv_folds=3,
    )
    res_max = run_nested_tuning(spec_max, model_spec, X, y)
    assert res_max.best_params["alpha"] == 0.001
    assert res_max.best_score == max(t.mean_score for t in res_max.trials)


def test_aud_m4_03_run_nested_tuning_with_preprocessing_anti_leakage() -> None:
    """AUD-M4-03: run_nested_tuning applies preprocessing per inner fold without validation leakage."""
    class ScaleAssertingModel:
        """Model that verifies input features are standardized (mean approx 0, std approx 1)."""
        def __init__(self, alpha: float = 1.0) -> None:
            self.alpha = float(alpha)
            self.coef_: np.ndarray | None = None
            self.__is_fitted__: bool = False

        def set_params(self, **params: Any) -> ScaleAssertingModel:
            if "alpha" in params:
                self.alpha = float(params["alpha"])
            return self

        def fit(self, X: np.ndarray, y: np.ndarray) -> ScaleAssertingModel:
            # Verify X is standardized by preprocessing (mean ~ 0, std ~ 1)
            mean_abs = np.abs(np.mean(X, axis=0))
            assert np.all(mean_abs < 1e-7), f"Expected standardized X, got column means: {mean_abs}"
            p = X.shape[1]
            self.coef_ = np.linalg.solve(X.T @ X + self.alpha * np.eye(p), X.T @ y)
            self.__is_fitted__ = True
            return self

        def predict(self, X: np.ndarray) -> np.ndarray:
            assert self.coef_ is not None
            return X @ self.coef_

    prep = TwoLayerPreprocessingSpec(
        layer1_steps=(),
        layer2_steps=(
            PreprocessingStepSpec(
                step_id="std_scaler",
                transformer_type="STANDARD",
                parameters={"with_mean": True, "with_std": True},
            ),
        ),
    )

    spec_with_prep = ModelSpec(
        model_id="scaled_linear",
        display_name="Scaled Linear Model",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory=lambda seed: ScaleAssertingModel(),
        capabilities=ModelCapabilities(requires_fit=True),
        description="Linear model requiring standardized features",
        scientific_justification="Testing AUD-M4-03 intra-fold preprocessing",
        preprocessing=prep,
    )

    rng = np.random.default_rng(300)
    # Raw features with non-zero mean and large scale (e.g. mean=1000, std=50)
    X_raw = rng.normal(loc=1000.0, scale=50.0, size=(60, 2))
    y = X_raw @ np.array([2.0, -1.5]) + rng.normal(scale=0.1, size=60)

    tuning_spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.01, 1.0)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=3,
    )

    # If run_nested_tuning did NOT apply preprocessing, ScaleAssertingModel.fit would raise AssertionError
    result = run_nested_tuning(tuning_spec, spec_with_prep, X_raw, y)
    assert len(result.trials) == 2
    assert result.best_score > 0.0
    assert all(t.status.value == "VALID" for t in result.trials)


def test_nested_tuning_dynamic_selection_isolated_per_inner_fold(monkeypatch: pytest.MonkeyPatch) -> None:
    """C3 (M8-04, AD-028): select_features_in_fold runs strictly on inner_train per sub-fold during Nested CV."""
    from experimental_ml.core.types import ScenarioId
    from experimental_ml.features.scenarios import FeatureScenario, ScenarioMode
    import experimental_ml.features.selection as sel_mod

    rng = np.random.default_rng(77)
    n = 30
    x_sig = rng.normal(size=n)
    x_noise = rng.normal(size=n)
    y = 3.0 * x_sig + 0.05 * rng.normal(size=n)
    X_cand = {"x_sig": x_sig, "x_noise": x_noise}
    X_mat = np.column_stack([x_sig, x_noise])

    scenario = FeatureScenario(
        scenario_id=ScenarioId("sc_dyn"),
        name="Dynamic Top 1",
        description="Dynamic top 1",
        scientific_justification="Test ADR-003",
        mode=ScenarioMode.DYNAMIC,
        strategy_name="TOP_K_RELEVANCE",
        strategy_params={"k": 1},
    )

    observed_train_sizes: list[int] = []
    orig_select = sel_mod.select_features_in_fold

    def _spy_select(X_train, y_train, scenario, random_state=42):
        observed_train_sizes.append(len(y_train))
        return orig_select(X_train=X_train, y_train=y_train, scenario=scenario, random_state=random_state)

    monkeypatch.setattr(sel_mod, "select_features_in_fold", _spy_select)

    spec = _make_dummy_model_spec()
    tuning_spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.1, 1.0)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=3,
    )
    res = run_nested_tuning(
        tuning_spec,
        spec,
        X_mat,
        y,
        seed=42,
        X_train_cand=X_cand,
        scenario=scenario,
    )
    assert len(res.trials) == 2
    # 3 inner folds cached across 2 candidates = 3 inner selections, each strictly on 20 samples (< 30 outer samples)
    assert len(observed_train_sizes) == 3
    assert all(sz == 20 for sz in observed_train_sizes)


def test_m11_4_nested_cv_caches_inner_fold_preprocessing(monkeypatch: pytest.MonkeyPatch) -> None:
    """M114-02: execute_nested_cv cacheia pré-processamento por fold interno sem alterar resultados."""
    from experimental_ml.models.preprocessing.types import (
        PreprocessingStepSpec,
        TwoLayerPreprocessingSpec,
    )
    import experimental_ml.models.preprocessing.pipeline as preproc_mod

    rng = np.random.default_rng(11)
    X_mat = rng.normal(size=(24, 3))
    y = 2.0 * X_mat[:, 0] + rng.normal(scale=0.1, size=24)

    fit_calls = 0
    orig_fit = preproc_mod.fit_two_layer_preprocessing

    def _spy_fit(spec, x_arr):
        nonlocal fit_calls
        fit_calls += 1
        return orig_fit(spec, x_arr)

    monkeypatch.setattr(preproc_mod, "fit_two_layer_preprocessing", _spy_fit)

    from dataclasses import replace

    base_spec = _make_dummy_model_spec()
    spec = replace(
        base_spec,
        preprocessing=TwoLayerPreprocessingSpec(
            layer1_steps=(
                PreprocessingStepSpec(
                    step_id="s1",
                    transformer_type="STANDARD",
                ),
            ),
            layer2_steps=(),
        ),
    )
    tuning_spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.1, 1.0, 10.0)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=3,
    )
    res = run_nested_tuning(tuning_spec, spec, X_mat, y, seed=42)
    assert len(res.trials) == 3
    # 3 candidatos * 3 folds internos -> pré-processamento ajustado apenas 3 vezes (1x por fold)
    assert fit_calls == 3


