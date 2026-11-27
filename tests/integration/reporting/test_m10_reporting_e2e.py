"""End-to-end integration test for M10 visualization and pt-BR reporting via run_experiment."""

from __future__ import annotations

from pathlib import Path
import numpy as np

from experimental_ml.core.enums import TaskType
from experimental_ml.pipeline import run_experiment


class _SimpleLinearModel:
    def __init__(self, scale: float = 1.0) -> None:
        self.scale = scale
        self.w: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "_SimpleLinearModel":
        X_aug = np.column_stack([np.ones(X.shape[0]), X.astype(np.float64)])
        coef, *_ = np.linalg.lstsq(X_aug, y.astype(np.float64), rcond=None)
        self.w = coef * self.scale
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        assert self.w is not None
        X_aug = np.column_stack([np.ones(X.shape[0]), X.astype(np.float64)])
        return X_aug @ self.w


def test_m10_pipeline_e2e_ptbr_report_and_figures(tmp_path: Path) -> None:
    """C5 (M10): run_experiment generates Stage 2 PNGs/HTML and Stage 6 pt-BR report with embedded figures and glossary."""
    rng = np.random.default_rng(42)
    csv_path = tmp_path / "dataset.csv"
    lines = ["f_um,f_dois,alvo"]
    for i in range(40):
        x1 = float(i) * 0.1 + float(rng.normal(0, 0.05))
        x2 = float(rng.normal(0, 1.0))
        y = 2.5 * x1 + 0.3 * x2 + 1.0
        lines.append(f"{x1:.4f},{x2:.4f},{y:.4f}")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    exp_dir = tmp_path / "exp_m10_e2e"
    summary = run_experiment(
        data=csv_path,
        target="alvo",
        task=TaskType.REGRESSION,
        models={
            "lin_a": _SimpleLinearModel(1.0),
            "lin_b": _SimpleLinearModel(0.95),
        },
        output_dir=exp_dir,
        cv_folds=3,
        master_seed=42,
    )

    reports_dir = exp_dir / "reports"
    # Stage 2 artifacts
    assert (reports_dir / "exploratory_target.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert (reports_dir / "exploratory_redundancy.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert (reports_dir / "exploratory_features.html").exists()
    assert (reports_dir / "exploratory_features.md").exists()

    # Stage 6 figures & pt-BR report
    assert (reports_dir / "figures" / "fig_family_d.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert (reports_dir / "figures" / "fig_family_e.png").exists()
    assert (reports_dir / "figures" / "fig_family_f.png").exists()

    md_text = summary.report_md_path.read_text(encoding="utf-8")
    html_text = summary.report_html_path.read_text(encoding="utf-8")

    assert "1. Declarações do Pesquisador" in md_text
    assert "4. Glossário Estatístico" in md_text
    assert "![Figura — figures/fig_family_d.png](figures/fig_family_d.png)" in md_text

    assert '<html lang="pt-BR">' in html_text
    assert "4. Glossário Estatístico" in html_text
    assert "@media print" in html_text
    assert '<img src="figures/fig_family_d.png"' in html_text
