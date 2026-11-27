"""End-to-end integration test for M9 deferred intra-fold imputation and categorical encoding (M9-03, AC-M9-03)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from experimental_ml import run_experiment
from experimental_ml.data import PreparationRule
from experimental_ml.features import FeatureScenario, ScenarioMode
from experimental_ml.models import (
    DummyBaselineModel,
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
)
from experimental_ml.tuning import HyperparameterSearchSpec, SearchStrategy
from experimental_ml.core.enums import MetricDirection


class _RidgeLikeModel:
    """Minimal pure-NumPy linear regressor with alpha hyperparameter."""

    def __init__(self, alpha: float = 1.0) -> None:
        self.alpha = float(alpha)
        self.weights_: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "_RidgeLikeModel":
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float)
        assert np.all(np.isfinite(X_arr))
        xtx = X_arr.T @ X_arr + self.alpha * np.eye(X_arr.shape[1])
        self.weights_ = np.linalg.solve(xtx, X_arr.T @ y_arr)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        assert self.weights_ is not None
        return np.asarray(X, dtype=float) @ self.weights_


def _make_ridge_model(seed: int | None = None) -> _RidgeLikeModel:
    return _RidgeLikeModel()


_make_ridge_model._factory_ref = "inline:ridge_tuned"  # type: ignore[attr-defined]


def test_deferred_missing_and_categorical_e2e_no_leakage(tmp_path: Path) -> None:
    """C3 (M9-03, AC-M9-03): Dataset with NaN + string categorical + DEFER_INTRA_FOLD executes Stages 1-6 cleanly."""
    csv_path = tmp_path / "dados_m9.csv"
    rows = ["x_num,x_cat,alvo"]
    rng = np.random.default_rng(42)
    cats = ["alto", "medio", "baixo"]
    for i in range(30):
        c = cats[i % 3]
        x_val = "" if i % 7 == 0 else f"{(i * 0.5 + rng.normal(0.0, 0.1)):.4f}"
        cat_val = "" if i % 11 == 0 else c
        base_y = (i * 0.5) + (2.0 if c == "alto" else (1.0 if c == "medio" else 0.0))
        rows.append(f"{x_val},{cat_val},{base_y:.4f}")
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    rules = [
        PreparationRule(
            finding_code="E1_FEATURE_MISSING",
            column="x_num",
            kind="DEFER_INTRA_FOLD",
            parameters={"imputation_strategy": "MEDIAN"},
        ),
        PreparationRule(
            finding_code="E1_FEATURE_MISSING",
            column="x_cat",
            kind="DEFER_INTRA_FOLD",
            parameters={"imputation_strategy": "MODE"},
        ),
        PreparationRule(
            finding_code="E1_CATEGORICAL_UNENCODED",
            column="x_cat",
            kind="DEFER_INTRA_FOLD",
            parameters={"encoding_strategy": "ORDINAL_ENCODER"},
        ),
    ]

    scenarios = [
        FeatureScenario(
            scenario_id="sc_dyn",
            name="Dynamic Top 2",
            description="Dynamic selection after Layer 1 encoding/imputation",
            scientific_justification="Test M9 Layer 1 + dynamic selection",
            mode=ScenarioMode.DYNAMIC,
            strategy_name="TOP_K_RELEVANCE",
            strategy_params={"k": 2},
        )
    ]

    from experimental_ml.models import resolve_estimator_factory

    model_specs = [
        ModelSpec(
            model_id="baseline_media",
            display_name="Baseline Média",
            family=ModelFamily.BASELINE,
            capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
            estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
            description="Mean baseline",
            scientific_justification="Baseline",
        ),
        ModelSpec(
            model_id="ridge_tuned",
            display_name="Ridge Tuned",
            family=ModelFamily.CLASSICAL_ML,
            capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
            estimator_factory=_make_ridge_model,
            description="Ridge-like linear model with Nested CV",
            scientific_justification="Test M9 with Nested CV",
            search_spec=HyperparameterSearchSpec(
                search_strategy=SearchStrategy.GRID_SEARCH,
                param_grid={"alpha": (0.1, 1.0)},
                optimization_metric="rmse",
                direction=MetricDirection.MINIMIZE,
                inner_cv_folds=3,
            ),
        ),
    ]

    out_dir = tmp_path / "exp_m9"
    summary = run_experiment(
        data=csv_path,
        target="alvo",
        task="regression",
        models=model_specs,
        scenarios=scenarios,
        rules=rules,
        output_dir=out_dir,
        cv_folds=3,
        metrics=["rmse", "r2"],
        master_seed=42,
    )

    assert summary.completed_cells == 6
    assert summary.failed_cells == 0
    assert summary.report_md_path.is_file()
    assert summary.report_html_path.is_file()
