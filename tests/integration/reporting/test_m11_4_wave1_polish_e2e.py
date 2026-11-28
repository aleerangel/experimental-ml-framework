"""Testes E2E do submarco M11.4 (VAL-ENH-004 e VAL-QUAL-004)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from experimental_ml.core.enums import MetricDirection
from experimental_ml.pipeline import run_experiment
from experimental_ml.statistics import ComparisonScope, ObjectiveSource, ObjectiveSpec


class _LinearReg:
    def __init__(self, reg: float = 0.0) -> None:
        self.reg = reg
        self.w: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "_LinearReg":
        x_aug = np.column_stack([np.ones(X.shape[0]), X.astype(np.float64)])
        eye = self.reg * np.eye(x_aug.shape[1])
        eye[0, 0] = 0.0
        self.w = np.linalg.pinv(x_aug.T @ x_aug + eye) @ (x_aug.T @ y.astype(np.float64))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        assert self.w is not None
        x_aug = np.column_stack([np.ones(X.shape[0]), X.astype(np.float64)])
        return x_aug @ self.w


def test_m11_4_run_experiment_planned_pairs_and_pareto(tmp_path: Path) -> None:
    """M114-01: run_experiment respeita comparison_scope=PLANNED_PAIRS, planned_pairs e pareto_objectives."""
    rng = np.random.default_rng(7)
    x1 = rng.normal(size=36)
    x2 = rng.normal(size=36)
    y = 2.0 * x1 - 0.5 * x2 + rng.normal(scale=0.2, size=36)
    data = {"x1": x1, "x2": x2, "target": y}
    models = {
        "LinA": _LinearReg(0.0),
        "LinB": _LinearReg(1.0),
        "LinC": _LinearReg(10.0),
    }

    out_dir = tmp_path / "exp_planned"
    summary = run_experiment(
        data=data,
        models=models,
        output_dir=out_dir,
        target="target",
        task="regression",
        cv_folds=3,
        master_seed=42,
        comparison_scope=ComparisonScope.PLANNED_HYPOTHESES,
        planned_pairs=((("lina", "todas_features"), ("linc", "todas_features")),),
        pareto_objectives=(
            ObjectiveSpec("rmse", MetricDirection.MINIMIZE),
            ObjectiveSpec("fit_mean_s", MetricDirection.MINIMIZE, ObjectiveSource.TIMING_MEAN, "fit_mean_s"),
        ),
    )

    comp_json = json.loads((out_dir / "statistics" / "statistical_comparisons.json").read_text(encoding="utf-8"))
    pairs_seen = {
        (tuple(r["config_a"]), tuple(r["config_b"]))
        for r in comp_json["comparisons"]
    }
    assert pairs_seen == {(("lina", "todas_features"), ("linc", "todas_features"))}
    pareto_json = json.loads((out_dir / "statistics" / "pareto_summary.json").read_text(encoding="utf-8"))
    assert [o["name"] for o in pareto_json["objectives"]] == ["rmse", "fit_mean_s"]
