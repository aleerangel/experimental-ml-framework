"""CLI and Python facade tests for CSV formatting configuration (CSV-04, CSV-05)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np

from experimental_ml import run_experiment


class _LinearMeanLikeRegressor:
    """Minimal pure-NumPy regressor for end-to-end CSV facade/CLI checks."""

    def fit(self, X: np.ndarray, y: np.ndarray) -> _LinearMeanLikeRegressor:
        self.mean_ = float(np.mean(y))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(X.shape[0], self.mean_, dtype=np.float64)


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "experimental_ml.cli.main", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_csv_format_schema_and_flag_precedence(tmp_path: Path) -> None:
    """schema.json 'csv_format' is parsed by 'expml data profile' and overridden by CLI flags."""
    csv_accent = tmp_path / "regional_accent.csv"
    csv_accent.write_bytes(
        "x1;região;alvo\n1,5;Norte;3,5\n2,5;Sul;5,5\n3,5;Leste;7,5\n".encode("latin-1")
    )

    schema_path = tmp_path / "schema.json"
    # Intentionally set wrong encoding & decimal in schema.json to verify CLI flags override them
    schema_path.write_text(
        json.dumps(
            {
                "target_col": "alvo",
                "task_type": "REGRESSION",
                "csv_format": {
                    "delimiter": ";",
                    "decimal": ".",
                    "encoding": "ascii",
                },
            }
        ),
        encoding="utf-8",
    )

    # 1. Fails when broken schema.json csv_format is used without CLI overrides
    out_fail = tmp_path / "exp_fail"
    res_fail = _run_cli(
        "data", "profile",
        "--data", str(csv_accent),
        "--schema", str(schema_path),
        "--output-dir", str(out_fail),
    )
    assert res_fail.returncode == 2

    # 2. Succeeds when CLI flags override decimal and encoding
    out_ok = tmp_path / "exp_ok"
    res_ok = _run_cli(
        "data", "profile",
        "--data", str(csv_accent),
        "--schema", str(schema_path),
        "--output-dir", str(out_ok),
        "--decimal", ",",
        "--encoding", "latin-1",
    )
    assert res_ok.returncode == 0, res_ok.stderr
    assert "3 rows x 3 columns" in res_ok.stdout

    # 3. Also succeeds when schema.json 'csv_format' itself is valid (no CLI overrides)
    schema_ok = tmp_path / "schema_ok.json"
    schema_ok.write_text(
        json.dumps(
            {
                "target_col": "alvo",
                "task_type": "REGRESSION",
                "csv_format": {
                    "delimiter": ";",
                    "decimal": ",",
                    "encoding": "latin-1",
                },
            }
        ),
        encoding="utf-8",
    )
    out_json = tmp_path / "exp_json"
    res_json = _run_cli(
        "data", "profile",
        "--data", str(csv_accent),
        "--schema", str(schema_ok),
        "--output-dir", str(out_json),
    )
    assert res_json.returncode == 0, res_json.stderr
    assert "3 rows x 3 columns" in res_json.stdout


def test_quickrun_and_facade_regional_csv_end_to_end(tmp_path: Path) -> None:
    """expml quickrun and run_experiment complete Stages 1-6 on regional CSVs."""
    # 1. expml init + quickrun with regional ';' + ',' decimal + latin-1 CSV
    exp_cli = tmp_path / "cli_exp"
    init_res = _run_cli("init", "--output-dir", str(exp_cli), "--task", "regression")
    assert init_res.returncode == 0, init_res.stderr

    br_csv = tmp_path / "br_dados.csv"
    lines = ["x1;x2;alvo"] + [
        f"{i * 0.1:.2f};{i * 0.5:.2f};{2.0 * (i * 0.1) + 1.0:.3f}".replace(".", ",")
        for i in range(1, 21)
    ]
    br_csv.write_bytes(("\n".join(lines) + "\n").encode("latin-1"))

    qr_res = _run_cli(
        "quickrun",
        "--experiment-dir", str(exp_cli),
        "--data", str(br_csv),
        "--delimiter", ";",
        "--decimal", ",",
        "--encoding", "latin-1",
    )
    assert qr_res.returncode == 0, qr_res.stderr
    assert (exp_cli / "reports" / "report.md").exists()
    assert (exp_cli / "reports" / "report.html").exists()

    # 2. run_experiment facade with auto-detection on regional CSV
    out_facade = tmp_path / "facade_exp"
    summary = run_experiment(
        data=br_csv,
        target="alvo",
        task="regression",
        models={"media": _LinearMeanLikeRegressor()},
        output_dir=out_facade,
        delimiter=None,
        decimal="auto",
        encoding="auto",
        cv_folds=4,
    )
    assert summary.completed_cells == 4
    assert summary.failed_cells == 0
    assert summary.report_md_path.exists()
