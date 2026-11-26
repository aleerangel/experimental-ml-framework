"""Testes de usabilidade da CLI (`expml init`, `quickrun`, flags) e fachada Python `run_experiment`."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from experimental_ml import run_experiment
from experimental_ml.cli.main import main as cli_main
from experimental_ml.models import DummyBaselineModel


class _SimplesRegressorLinear:
    """Estimador simples estilo scikit-learn sem herança do framework."""

    def __init__(self, scale: float = 1.0) -> None:
        self.scale = scale
        self.coef_: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> "_SimplesRegressorLinear":
        self.coef_ = float(np.mean(y))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(len(X), self.coef_ * self.scale, dtype=float)


def test_cli_init_and_end_to_end_workflow(tmp_path: Path, capsys) -> None:
    """C1: `expml init` cria projeto válido e `expml quickrun` + subcomandos funcionam ponta a ponta."""
    proj_dir = tmp_path / "meu_exp"

    rc_init = cli_main(["init", "--output-dir", str(proj_dir), "--task", "regression"])
    assert rc_init == 0
    for fname in (
        "dados_exemplo.csv",
        "schema.json",
        "rules.json",
        "scenarios.json",
        "models.json",
        "partition.json",
        "stats_config.json",
    ):
        assert (proj_dir / fname).is_file()

    # Execução completa em 1 comando
    rc_qr = cli_main(["quickrun", "--experiment-dir", str(proj_dir), "--metrics", "rmse", "rmse_rel_pct"])
    assert rc_qr == 0
    captured = capsys.readouterr().out
    assert "report.md" in captured
    assert (proj_dir / "reports" / "report.md").is_file()
    assert (proj_dir / "reports" / "report.html").is_file()

    # Verificar --experiment-dir unificado em run status e run verify
    assert cli_main(["run", "status", "--experiment-dir", str(proj_dir)]) == 0
    assert cli_main(["run", "verify", "--experiment-dir", str(proj_dir)]) == 0

    # Verificar data sanitize sem --rules (quando não há achados confirmados)
    assert cli_main(["data", "sanitize", "--experiment-dir", str(proj_dir), "--force"]) == 0


def test_python_facade_run_experiment_end_to_end(tmp_path: Path) -> None:
    """C2: `experimental_ml.run_experiment` executa Etapas 1-6 com 10 linhas de ML simples."""
    rng = np.random.default_rng(7)
    x1 = rng.normal(0.0, 1.0, size=30)
    x2 = rng.normal(2.0, 0.5, size=30)
    y = 3.0 * x1 + 0.5 * x2 + 1.0
    csv_path = tmp_path / "dados.csv"
    rows = ["x1,x2,alvo"] + [f"{a:.4f},{b:.4f},{c:.4f}" for a, b, c in zip(x1, x2, y)]
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    out_dir = tmp_path / "exp_python"
    res = run_experiment(
        data=csv_path,
        target="alvo",
        task="regression",
        models={
            "Media Baseline": DummyBaselineModel(strategy="mean"),
            "Regressor Simples": _SimplesRegressorLinear(scale=1.0),
        },
        output_dir=out_dir,
        cv_folds=3,
        metrics=["rmse", "r2"],
    )

    assert res.completed_cells == 6
    assert res.failed_cells == 0
    assert res.report_md_path.is_file()
    assert res.report_html_path.is_file()
    resumo = res.summary()
    assert "=== Resumo do Experimento ===" in resumo
    assert "Relatório Markdown:" in resumo
    assert json.loads((out_dir / "statistics" / "descriptive_consolidation.json").read_text(encoding="utf-8"))


class _SeedAwareRegressor:
    """Estimador com random_state=None para validar propagação determinística de seed."""

    def __init__(self, random_state: int | None = None) -> None:
        self.random_state = random_state
        self.bias_: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> "_SeedAwareRegressor":
        rng = np.random.default_rng(self.random_state)
        self.bias_ = float(np.mean(y)) + float(rng.normal(0.0, 0.01))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(len(X), self.bias_, dtype=float)


def test_run_experiment_cli_interoperability_and_seed_propagation(tmp_path: Path) -> None:
    """C4 (M8-05): run_experiment persists full CLI-compatible artifacts and propagates cell seed to instances."""
    rng = np.random.default_rng(11)
    x1 = rng.normal(0.0, 1.0, size=24)
    y = 2.0 * x1 + 1.0
    csv_path = tmp_path / "dados_interop.csv"
    rows = ["x1,alvo"] + [f"{a:.4f},{c:.4f}" for a, c in zip(x1, y)]
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    out_1 = tmp_path / "exp_1"
    out_2 = tmp_path / "exp_2"
    res1 = run_experiment(
        data=csv_path,
        target="alvo",
        task="regression",
        models={
            "Media": DummyBaselineModel(strategy="mean"),
            "Stochastic": _SeedAwareRegressor(random_state=None),
        },
        output_dir=out_1,
        cv_folds=3,
        metrics=["rmse", "r2"],
        master_seed=42,
    )
    res2 = run_experiment(
        data=csv_path,
        target="alvo",
        task="regression",
        models={
            "Media": DummyBaselineModel(strategy="mean"),
            "Stochastic": _SeedAwareRegressor(random_state=None),
        },
        output_dir=out_2,
        cv_folds=3,
        metrics=["rmse", "r2"],
        master_seed=42,
    )

    assert res1.observed_leader == res2.observed_leader
    assert (out_1 / "data" / "sanitized_view.json").is_file()
    assert (out_1 / "partitions" / "splits.csv.gz").is_file()
    assert (out_1 / "partitions" / "splits.schema.json").is_file()
    assert (out_1 / "statistics" / "pareto_summary.json").is_file()
    assert (out_1 / "reports" / "exploratory_features.json").is_file()

    assert cli_main(["partition", "verify", "--experiment-dir", str(out_1)]) == 0
    assert cli_main(["run", "verify", "--experiment-dir", str(out_1)]) == 0
    assert cli_main(["report", "export", "--experiment-dir", str(out_1), "--output-dir", str(out_1 / "bundle"), "--force"]) == 0
    assert (
        res1.consolidation.configurations[("stochastic", "todas_features")].aggregated_metrics["rmse"].mean
        == res2.consolidation.configurations[("stochastic", "todas_features")].aggregated_metrics["rmse"].mean
    )
