"""Validação estrutural, pureza XCUT-02 e execução ponta a ponta dos notebooks (.ipynb)."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"

ALLOWED_NOTEBOOK_TOP_LEVEL_IMPORTS: set[str] = (
    set(sys.stdlib_module_names) | {"experimental_ml", "numpy", "IPython"}
)


def _iter_notebook_paths() -> list[Path]:
    if not NOTEBOOKS_DIR.is_dir():
        return []
    return sorted(NOTEBOOKS_DIR.glob("*.ipynb"))


def test_all_notebooks_valid_and_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida esquema nbformat >= 4, pureza de imports e executa 100% das células de código."""
    nb_paths = _iter_notebook_paths()
    if not nb_paths:
        # Durante T1 (antes de T2/T3 criarem os notebooks), valida apenas que o parser está íntegro.
        return

    monkeypatch.chdir(tmp_path)

    for nb_path in nb_paths:
        raw = json.loads(nb_path.read_text(encoding="utf-8"))
        assert raw.get("nbformat", 0) >= 4, f"{nb_path.name}: nbformat deve ser >= 4."
        cells = raw.get("cells", [])
        assert isinstance(cells, list) and len(cells) >= 3, f"{nb_path.name}: células insuficientes."

        has_markdown = any(c.get("cell_type") == "markdown" for c in cells)
        has_code = any(c.get("cell_type") == "code" for c in cells)
        assert has_markdown and has_code, f"{nb_path.name}: deve conter células markdown e código."

        ns: dict[str, object] = {"__name__": "__main__"}
        for idx, cell in enumerate(cells, start=1):
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            if not source.strip():
                continue

            tree = ast.parse(source, filename=f"{nb_path.name}#cell-{idx}")
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        assert top in ALLOWED_NOTEBOOK_TOP_LEVEL_IMPORTS, (
                            f"{nb_path.name} célula {idx}: import proibido '{alias.name}' (XCUT-02)."
                        )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    top = node.module.split(".")[0]
                    assert top in ALLOWED_NOTEBOOK_TOP_LEVEL_IMPORTS, (
                        f"{nb_path.name} célula {idx}: import proibido '{node.module}' (XCUT-02)."
                    )

            try:
                exec(compile(tree, f"{nb_path.name}#cell-{idx}", "exec"), ns)
            except Exception as exc:
                pytest.fail(f"Falha ao executar {nb_path.name} célula {idx}: {exc}")
