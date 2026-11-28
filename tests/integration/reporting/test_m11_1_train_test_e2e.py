"""End-to-end integration test for M11.1 opt-in train_metrics and Train vs. Test Table D & Figure D."""

from __future__ import annotations

from pathlib import Path
import numpy as np

from experimental_ml.core.enums import TaskType
from experimental_ml.pipeline import run_experiment
from experimental_ml.reporting import ReportFamily, build_figure_spec, build_table_model, load_experiment_artifacts_readonly, render_figure


class _SimpleLinearRegressor:
    def __init__(self, reg: float = 0.0) -> None:
        self.reg = reg
        self.w: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "_SimpleLinearRegressor":
        X_aug = np.column_stack([np.ones(X.shape[0]), X.astype(np.float64)])
        xtx = X_aug.T @ X_aug + self.reg * np.eye(X_aug.shape[1])
        self.w = np.linalg.solve(xtx, X_aug.T @ y.astype(np.float64))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        assert self.w is not None
        X_aug = np.column_stack([np.ones(X.shape[0]), X.astype(np.float64)])
        return X_aug @ self.w


def test_m11_1_e2e_train_vs_test_table_and_figure(tmp_path: Path) -> None:
    """C3 (M11.1): Opt-in collect_train_metrics=True populates Train Mean in Table D and Treino series in Figure D."""
    rng = np.random.default_rng(7)
    csv_path = tmp_path / "data.csv"
    lines = ["x1,x2,y"]
    for i in range(36):
        x1 = float(i) * 0.1
        x2 = float(rng.normal(0.0, 0.5))
        y = 3.0 * x1 - 0.8 * x2 + float(rng.normal(0.0, 0.2))
        lines.append(f"{x1:.4f},{x2:.4f},{y:.4f}")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 1. Default (opt-in off) must not populate train_metrics
    exp_off = tmp_path / "exp_off"
    run_experiment(
        data=csv_path,
        target="y",
        task=TaskType.REGRESSION,
        models={"lin": _SimpleLinearRegressor(0.01)},
        output_dir=exp_off,
        cv_folds=3,
        master_seed=7,
    )
    loaded_off = load_experiment_artifacts_readonly(exp_off)
    tbl_off = build_table_model(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded_off)
    assert "train_mean" not in [c.key for c in tbl_off.columns]

    # 2. Explicit opt-in on populates Table D (Train Mean) and Figure D (Treino vs DEV_CV)
    exp_on = tmp_path / "exp_on"
    summary = run_experiment(
        data=csv_path,
        target="y",
        task=TaskType.REGRESSION,
        models={
            "lin_low_reg": _SimpleLinearRegressor(0.01),
            "lin_high_reg": _SimpleLinearRegressor(5.0),
        },
        output_dir=exp_on,
        cv_folds=3,
        master_seed=7,
        collect_train_metrics=True,
    )
    loaded_on = load_experiment_artifacts_readonly(exp_on)
    tbl_on = build_table_model(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded_on)
    assert "train_mean" in [c.key for c in tbl_on.columns]
    assert all(r["train_mean"] is not None for r in tbl_on.rows)

    fig_d = build_figure_spec(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded_on, metric_name="rmse")
    assert any("(Treino)" in s.name for s in fig_d.series)
    assert render_figure(fig_d, "png")[:8] == b"\x89PNG\r\n\x1a\n"
    assert render_figure(fig_d, "svg").decode("utf-8").startswith("<svg ")
    assert render_figure(fig_d, "pdf").startswith(b"%PDF-1.4")
    assert "Train Mean" in summary.report_md_path.read_text(encoding="utf-8")
