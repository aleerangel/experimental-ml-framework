"""CLI integration tests for Stage 2 exploratory feature visualization (EXPL-02..EXPL-05)."""

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

    # Ranked summary in stdout, no raw 64-hex hashes (CLI-11)
    assert "Ranking Atributo x Alvo" in res_exp.stdout
    assert "x1 [PEARSON]" in res_exp.stdout
    assert "Pares Redundantes" in res_exp.stdout
    assert not re.search(r"\b[0-9a-f]{64}\b", res_exp.stdout)

    # Visual artifacts created
    assert (exp_dir / "reports" / "exploratory_features.json").exists()
    assert (exp_dir / "reports" / "exploratory_features.md").exists()
    assert (exp_dir / "reports" / "exploratory_features.html").exists()
    assert (exp_dir / "figures" / "exploratory_target_associations.svg").exists()
    assert (exp_dir / "figures" / "exploratory_target_associations.png").exists()
    assert (exp_dir / "figures" / "exploratory_redundancy_heatmap.svg").exists()
    assert (exp_dir / "figures" / "exploratory_redundancy_heatmap.png").exists()

    # Anti-leakage: configuration/scenarios.json is never auto-created (EXPL-05)
    assert not (exp_dir / "configuration" / "scenarios.json").exists()
