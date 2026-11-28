"""Teste E2E para caracterização estatística ampliada e dataset_meta_features opt-in (M11.3 / VAL-ENH-007)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from experimental_ml.pipeline import run_experiment


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


def test_m11_3_e2e_opt_in_dataset_meta_features(tmp_path: Path) -> None:
    """M113-03-E2E: padrão (False) não grava dataset_meta_features.json; opt-in (True) grava e exibe no relatório."""
    rng = np.random.default_rng(123)
    n = 40
    x1 = rng.normal(size=n)
    x2 = 2.5 * x1 + rng.normal(scale=0.05, size=n)
    x3 = rng.normal(size=n)
    y = 3.0 * x1 - x3 + rng.normal(scale=0.2, size=n)
    data = {"x1": x1, "x2": x2, "x3": x3, "target": y}
    models = {"LinA": _LinearReg(0.0), "LinB": _LinearReg(1.0)}

    # 1) Padrão: export_meta_features=False, extended_stats=False
    dir_default = tmp_path / "default_run"
    run_experiment(
        data=data,
        models=models,
        output_dir=dir_default,
        target="target",
        task="regression",
        cv_folds=3,
        master_seed=42,
    )
    assert not (dir_default / "dataset_meta_features.json").exists()
    md_default = (dir_default / "reports" / "report.md").read_text(encoding="utf-8")
    assert "Caracterização Estatística Ampliada (Meta-Features)" not in md_default

    # 2) Opt-in: export_meta_features=True
    dir_opt = tmp_path / "optin_run"
    run_experiment(
        data=data,
        models=models,
        output_dir=dir_opt,
        target="target",
        task="regression",
        cv_folds=3,
        master_seed=42,
        export_meta_features=True,
    )
    meta_path = dir_opt / "dataset_meta_features.json"
    assert meta_path.exists()
    meta_payload = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta_payload["scope"] == "EXPLORATORY_FULL_DATA"
    assert meta_payload["max_vif"] > 10.0
    assert meta_payload["linearity_score"] > 0.9
    assert meta_payload["intrinsic_dim_ratio_95"] is not None

    md_opt = (dir_opt / "reports" / "report.md").read_text(encoding="utf-8")
    html_opt = (dir_opt / "reports" / "report.html").read_text(encoding="utf-8")
    assert "Caracterização Estatística Ampliada (Meta-Features)" in md_opt
    assert "Caracterização Estatística Ampliada (Meta-Features)" in html_opt
