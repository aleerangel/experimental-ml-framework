"""End-to-end integration test for M11.2 opt-in KS dataset-shift and OOF residuals Q-Q Plot."""

from __future__ import annotations

from pathlib import Path
import numpy as np

from experimental_ml.core.enums import TaskType
from experimental_ml.pipeline import run_experiment
from experimental_ml.validation.types import EvaluationRegime, PartitionConfig, PartitionStrategy


class _LinearReg:
    def __init__(self) -> None:
        self.w: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "_LinearReg":
        X_aug = np.column_stack([np.ones(X.shape[0]), X.astype(np.float64)])
        self.w, *_ = np.linalg.lstsq(X_aug, y.astype(np.float64), rcond=None)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        assert self.w is not None
        X_aug = np.column_stack([np.ones(X.shape[0]), X.astype(np.float64)])
        return X_aug @ self.w


def test_m11_2_e2e_opt_in_ks_drift_and_oof_qq_plot(tmp_path: Path) -> None:
    """C3 (M11.2): Default off produces no extra artifacts; opt-in generates ks_drift, residuals diagnostics, and Q-Q Plot."""
    rng = np.random.default_rng(99)
    csv_path = tmp_path / "data.csv"
    lines = ["x1,x2,y"]
    for i in range(60):
        # Introduce shift in last 20 rows (temporal / holdout)
        x1 = float(rng.normal(0.0 if i < 40 else 3.0, 1.0))
        x2 = float(rng.normal(0.0, 1.0))
        y = 2.0 * x1 - 0.5 * x2 + float(rng.normal(0.0, 0.4))
        lines.append(f"{x1:.4f},{x2:.4f},{y:.4f}")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 1. Default off
    exp_off = tmp_path / "exp_off"
    run_experiment(
        data=csv_path,
        target="y",
        task=TaskType.REGRESSION,
        models={"lin": _LinearReg()},
        output_dir=exp_off,
        cv_folds=3,
        master_seed=99,
    )
    assert not (exp_off / "statistics" / "ks_drift_report.json").exists()
    assert not (exp_off / "statistics" / "oof_residuals_diagnostics.json").exists()
    assert not (exp_off / "reports" / "figures" / "fig_oof_residuals_qq.png").exists()

    # 2. Opt-in on under CV_AND_HOLDOUT
    exp_on = tmp_path / "exp_on"
    part_cfg = PartitionConfig(
        strategy=PartitionStrategy.KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=3,
        holdout_fraction=0.33,
        shuffle=False,
        master_seed=99,
    )
    summary = run_experiment(
        data=csv_path,
        target="y",
        task=TaskType.REGRESSION,
        models={"lin": _LinearReg()},
        partition_config=part_cfg,
        output_dir=exp_on,
        master_seed=99,
        check_ks_drift=True,
        analyze_oof_residuals=True,
    )
    assert (exp_on / "statistics" / "ks_drift_report.json").exists()
    assert (exp_on / "statistics" / "oof_residuals_diagnostics.json").exists()
    assert (exp_on / "reports" / "figures" / "fig_oof_residuals_qq.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    md_text = summary.report_md_path.read_text(encoding="utf-8")
    assert "Diagnóstico de Dataset Shift" in md_text
    assert "Diagnóstico de Resíduos OOF" in md_text
    assert "fig_oof_residuals_qq.png" in md_text
