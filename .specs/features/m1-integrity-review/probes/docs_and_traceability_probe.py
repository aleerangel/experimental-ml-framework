"""Probe script for Dimension E (Documentation & Traceability) of M1 Integrity Review.

Checks DOC-01 through DOC-07 empirically without modifying any repository files.
"""

from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]


def probe_doc_01_readme_python_blocks() -> dict[str, Any]:
    """DOC-01: Extract and execute every ```python block in README.md."""
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    lines = readme_text.splitlines()

    blocks = []
    in_py = False
    start_line = 0
    buf: list[str] = []

    for idx, ln in enumerate(lines, start=1):
        if ln.strip() == "```python":
            in_py = True
            start_line = idx
            buf = []
            continue
        if in_py and ln.strip() == "```":
            in_py = False
            blocks.append({"index": len(blocks) + 1, "start_line": start_line, "end_line": idx, "code": "\n".join(buf)})
            continue
        if in_py:
            buf.append(ln)

    results = []
    for b in blocks:
        proc = subprocess.run(
            [sys.executable, "-c", b["code"]],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        results.append({
            "block_index": b["index"],
            "lines": f"L{b['start_line']}-L{b['end_line']}",
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        })
    return {"total_blocks": len(blocks), "blocks": results}


def probe_doc_02_readme_directory_tree() -> dict[str, Any]:
    """DOC-02: Compare README.md directory tree under src/experimental_ml/ and .specs/features/ against disk."""
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    # Check specific files claimed in README tree
    claimed_paths = [
        "src/experimental_ml/__init__.py",
        "src/experimental_ml/cli/__init__.py",
        "src/experimental_ml/cli/main.py",
        "src/experimental_ml/core/__init__.py",
        "src/experimental_ml/core/enums.py",
        "src/experimental_ml/core/exceptions.py",
        "src/experimental_ml/core/findings.py",
        "src/experimental_ml/core/hashing.py",
        "src/experimental_ml/core/identifiers.py",
        "src/experimental_ml/core/seeds.py",
        "src/experimental_ml/metrics/__init__.py",
        "src/experimental_ml/metrics/aggregation.py",
        "src/experimental_ml/metrics/catalog.py",
        "src/experimental_ml/metrics/classification.py",
        "src/experimental_ml/metrics/regression.py",
        "src/experimental_ml/metrics/types.py",
        "src/experimental_ml/metrics/validation.py",
        "src/experimental_ml/data/__init__.py",
        "src/experimental_ml/data/loader.py",
        "src/experimental_ml/data/parsing.py",
        "src/experimental_ml/data/query.py",
        "src/experimental_ml/data/schema.py",
        "src/experimental_ml/data/types.py",
        "src/experimental_ml/data/validation.py",
        ".specs/features/m1-1-setup-cli-smoke/verification.md",
    ]
    missing_on_disk = [p for p in claimed_paths if not (REPO_ROOT / p).exists()]
    actual_src_files = sorted(
        str(p.relative_to(REPO_ROOT))
        for p in (REPO_ROOT / "src" / "experimental_ml").rglob("*.py")
    )
    unlisted_in_readme = [p for p in actual_src_files if Path(p).name not in readme_text]

    return {
        "claimed_but_missing_on_disk": missing_on_disk,
        "actual_src_files_unlisted_in_readme": unlisted_in_readme,
    }


def probe_doc_03_04_counts_and_symbols() -> dict[str, Any]:
    """DOC-03 & DOC-04: Verify symbol counts in ETAPA_ATUAL_ENGENHARIA.md vs actual __all__ and importability."""
    mod_core = importlib.import_module("experimental_ml.core")
    mod_metrics = importlib.import_module("experimental_ml.metrics")
    mod_data = importlib.import_module("experimental_ml.data")

    core_all = list(getattr(mod_core, "__all__", []))
    metrics_all = list(getattr(mod_metrics, "__all__", []))
    data_all = list(getattr(mod_data, "__all__", []))

    etapa_text = (REPO_ROOT / "engenharia_software" / "ETAPA_ATUAL_ENGENHARIA.md").read_text(encoding="utf-8")
    claims_27_metrics = "re-exportação de 27 símbolos públicos com `__all__`" in etapa_text
    claims_7_data = "re-exportação de 7 símbolos públicos centrais com `__all__`" in etapa_text

    return {
        "actual_all_counts": {
            "experimental_ml.core": len(core_all),
            "experimental_ml.metrics": len(metrics_all),
            "experimental_ml.data": len(data_all),
        },
        "etapa_atual_claims": {
            "claims_27_for_metrics": claims_27_metrics,
            "actual_metrics_count": len(metrics_all),
            "claims_7_for_data": claims_7_data,
            "actual_data_count": len(data_all),
        },
    }


def probe_doc_07_governance_records() -> dict[str, Any]:
    """DOC-07: Check presence of governance files across m1-1..m1-4."""
    expected_files = ["spec.md", "SPEC.md", "tasks.md", "proofs.md", "verification.md", "ACCEPTANCE.md", "RESULTS.md"]
    features = ["m1-1-setup-cli-smoke", "m1-2-core", "m1-3-metrics", "m1-4-datasets-schemas"]
    matrix = {}
    for feat in features:
        fdir = REPO_ROOT / ".specs" / "features" / feat
        present = {ef: (fdir / ef).exists() for ef in expected_files}
        missing = [ef for ef, ok in present.items() if not ok]
        matrix[feat] = {"present": present, "missing": missing}
    return {"governance_matrix": matrix}


def main() -> None:
    report = {
        "DOC-01": probe_doc_01_readme_python_blocks(),
        "DOC-02": probe_doc_02_readme_directory_tree(),
        "DOC-03_04": probe_doc_03_04_counts_and_symbols(),
        "DOC-07": probe_doc_07_governance_records(),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
