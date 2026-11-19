"""CLI integration tests for Stage 2 exploratory feature visualization (EXPLR-01..EXPLR-06)."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "experimental_ml.cli.main", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_features_explore_visual_outputs_and_stdout(tmp_path: Path) -> None:
    """expml features explore prints ranked summary without hashes and creates MD/HTML/SVG/PNG without scenarios.json."""
    csv_path = tmp_path / "dados.csv"
    lines = ["x1,x2,alvo"] + [
        f"{i * 0.1:.2f},{i * 0.2:.2f},{2.0 * i + 1.0:.2f}" for i in range(1, 16)
    ]
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        json.dumps({"target_col": "alvo", "task_type": "REGRESSION"}),
        encoding="utf-8",
    )

    exp_dir = tmp_path / "exp"
    res_prof = _run_cli(
        "data", "profile",
        "--data", str(csv_path),
        "--schema", str(schema_path),
        "--output-dir", str(exp_dir),
    )
    assert res_prof.returncode == 0, res_prof.stderr

    res_san = _run_cli("data", "sanitize", "--experiment-dir", str(exp_dir))
    assert res_san.returncode == 0, res_san.stderr

    res_exp = _run_cli("features", "explore", "--experiment-dir", str(exp_dir))
    assert res_exp.returncode == 0, res_exp.stderr

    # Ranked summary in stdout (1 line per unique feature), no raw 64-hex hashes (CLI-11)
    assert "Ranking Único Atributo x Alvo" in res_exp.stdout
    ranking_section = res_exp.stdout.split("Pares Redundantes")[0]
    assert ranking_section.count("x1 — Média |·|:") == 1
    assert "PEARSON=" in ranking_section
    assert "SPEARMAN=" in ranking_section
    assert "Pares Redundantes" in res_exp.stdout
    assert not re.search(r"\b[0-9a-f]{64}\b", res_exp.stdout)

    # Visual artifacts created (JSON, MD, print-ready HTML, 2 CSVs, 2 PNGs; zero SVGs)
    assert (exp_dir / "reports" / "exploratory_features.json").exists()
    assert (exp_dir / "reports" / "exploratory_features.md").exists()
    html_path = exp_dir / "reports" / "exploratory_features.html"
    assert html_path.exists()
    html_text = html_path.read_text(encoding="utf-8")
    assert "@page { size: A4 portrait;" in html_text
    assert "@media print" in html_text
    assert "matrix-wrap" not in html_text

    assert (exp_dir / "reports" / "exploratory_target_associations.csv").exists()
    assert (exp_dir / "reports" / "exploratory_redundancy_matrix.csv").exists()
    assert (exp_dir / "figures" / "exploratory_target_associations.png").exists()
    assert (exp_dir / "figures" / "exploratory_redundancy_heatmap.png").exists()
    assert not list((exp_dir / "figures").glob("*.svg"))

    # Anti-leakage: configuration/scenarios.json is never auto-created (EXPLR-06)
    assert not (exp_dir / "configuration" / "scenarios.json").exists()


def test_quickrun_generates_stage2_visuals_and_preserves_scenarios(tmp_path: Path) -> None:
    """expml quickrun produces Stage 2 visual reports/CSVs/PNGs (no SVGs) without mutating scenarios.json."""
    exp_dir = tmp_path / "qr_exp"
    init_res = _run_cli("init", "--output-dir", str(exp_dir), "--task", "regression")
    assert init_res.returncode == 0, init_res.stderr

    orig_scenarios = (exp_dir / "scenarios.json").read_text(encoding="utf-8")

    qr_res = _run_cli("quickrun", "--experiment-dir", str(exp_dir))
    assert qr_res.returncode == 0, qr_res.stderr
    assert (exp_dir / "reports" / "exploratory_features.md").exists()
    assert (exp_dir / "reports" / "exploratory_features.html").exists()
    assert (exp_dir / "reports" / "exploratory_target_associations.csv").exists()
    assert (exp_dir / "reports" / "exploratory_redundancy_matrix.csv").exists()
    assert (exp_dir / "figures" / "exploratory_target_associations.png").exists()
    assert (exp_dir / "figures" / "exploratory_redundancy_heatmap.png").exists()
    assert not list((exp_dir / "figures").glob("*.svg"))
    assert (exp_dir / "scenarios.json").read_text(encoding="utf-8") == orig_scenarios
