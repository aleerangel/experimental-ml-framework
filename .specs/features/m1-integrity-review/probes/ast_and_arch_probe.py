#!/usr/bin/env python3
"""Probe for Baseline Capture (AUD-01..04) and Architectural Integrity (ARCH-01..07)."""

from __future__ import annotations

import ast
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "src" / "experimental_ml"
TESTS_ROOT = REPO_ROOT / "tests"


def get_module_name(py_file: Path) -> str:
    rel = py_file.relative_to(REPO_ROOT / "src")
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def get_top_subpackage(mod_name: str) -> str:
    parts = mod_name.split(".")
    if len(parts) >= 2 and parts[0] == "experimental_ml":
        return parts[1]
    return parts[0]


def extract_import_graph() -> dict[str, Any]:
    py_files = sorted(SRC_ROOT.rglob("*.py"))
    edges: list[dict[str, Any]] = []
    adj: dict[str, set[str]] = {}
    pkg_adj: dict[str, set[str]] = {"core": set(), "metrics": set(), "data": set(), "cli": set()}

    for f in py_files:
        src_mod = get_module_name(f)
        adj.setdefault(src_mod, set())
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("experimental_ml"):
                        edges.append(
                            {
                                "source_file": str(f.relative_to(REPO_ROOT)),
                                "line": node.lineno,
                                "source_module": src_mod,
                                "target_module": alias.name,
                                "kind": "import",
                            }
                        )
                        adj[src_mod].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.startswith("experimental_ml"):
                    edges.append(
                        {
                            "source_file": str(f.relative_to(REPO_ROOT)),
                            "line": node.lineno,
                            "source_module": src_mod,
                            "target_module": mod,
                            "names": [a.name for a in node.names],
                            "kind": "from",
                        }
                    )
                    adj[src_mod].add(mod)

    for e in edges:
        s_pkg = get_top_subpackage(e["source_module"])
        t_pkg = get_top_subpackage(e["target_module"])
        if s_pkg in pkg_adj and t_pkg in pkg_adj and s_pkg != t_pkg:
            pkg_adj[s_pkg].add(t_pkg)

    # Allowed dependencies per ARQUITETURA_E_CONTRATOS.md Section 2.3:
    # core -> {}
    # metrics -> {core}
    # data -> {core}
    # cli -> {core, metrics, data}
    allowed_pkg_deps = {
        "core": set(),
        "metrics": {"core"},
        "data": {"core"},
        "cli": {"core", "metrics", "data"},
    }
    violations = []
    for pkg, targets in pkg_adj.items():
        illegal = targets - allowed_pkg_deps.get(pkg, set())
        for il in sorted(illegal):
            violations.append(f"{pkg} -> {il}")

    # Cycle detection (DFS on module graph excluding __init__ -> submodule parent-child)
    # Check both package-level cycles and non-init module-level cycles
    mod_files = [f for f in py_files if f.name != "__init__.py"]
    file_adj: dict[str, set[str]] = {}
    for f in mod_files:
        m = get_module_name(f)
        file_adj[m] = set()
    for e in edges:
        s = e["source_module"]
        t = e["target_module"]
        if s in file_adj and t in file_adj and s != t:
            file_adj[s].add(t)

    cycles: list[list[str]] = []
    visited: set[str] = set()
    stack: list[str] = []
    on_stack: set[str] = set()

    def dfs(u: str) -> None:
        visited.add(u)
        stack.append(u)
        on_stack.add(u)
        for v in sorted(file_adj.get(u, ())):
            if v not in visited:
                dfs(v)
            elif v in on_stack:
                idx = stack.index(v)
                cycles.append(stack[idx:] + [v])
        stack.pop()
        on_stack.remove(u)

    for m in sorted(file_adj):
        if m not in visited:
            dfs(m)

    return {
        "edges": edges,
        "package_dependencies": {k: sorted(v) for k, v in pkg_adj.items()},
        "dependency_violations": violations,
        "module_cycles": cycles,
    }


def classify_classes_adr008() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for f in sorted(SRC_ROOT.rglob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) for b in node.bases]
                decorators = [ast.unparse(d) for d in node.decorator_list]
                methods = [
                    n.name
                    for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                is_frozen_dc = any("dataclass" in d and "frozen=True" in d for d in decorators)
                has_slots = any("dataclass" in d and "slots=True" in d for d in decorators) or any(
                    isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "__slots__" for t in n.targets)
                    for n in node.body
                )
                if is_frozen_dc:
                    category = "frozen data structure"
                elif any("Enum" in b or "StrEnum" in b for b in bases):
                    category = "enum"
                elif any("Exception" in b or "Error" in b for b in bases):
                    category = "exception"
                elif bases == ["str"] and set(methods).issubset({"__new__", "__repr__"}):
                    category = "immutable identifier (str subclass)"
                else:
                    category = "other"

                results.append(
                    {
                        "file": str(f.relative_to(REPO_ROOT)),
                        "line": node.lineno,
                        "name": node.name,
                        "bases": bases,
                        "decorators": decorators,
                        "methods": methods,
                        "has_slots": has_slots,
                        "category": category,
                    }
                )
    return results


def scan_symbol_usage() -> list[dict[str, Any]]:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    packages = ["experimental_ml.core", "experimental_ml.metrics", "experimental_ml.data"]
    all_src_files = sorted(SRC_ROOT.rglob("*.py"))
    all_test_files = sorted(TESTS_ROOT.rglob("*.py"))

    src_texts = {f: f.read_text(encoding="utf-8") for f in all_src_files}
    test_texts = {f: f.read_text(encoding="utf-8") for f in all_test_files}

    inventory: list[dict[str, Any]] = []
    for pkg_name in packages:
        mod = importlib.import_module(pkg_name)
        exported = getattr(mod, "__all__", [])
        pkg_dir = SRC_ROOT / pkg_name.split(".")[-1]
        for sym in exported:
            # Count references outside defining package in src/ and in tests/
            other_src_refs = []
            same_pkg_refs = []
            for f, txt in src_texts.items():
                if f.name == "__init__.py":
                    continue
                # Check AST Name or attribute usage
                if sym in txt:
                    if pkg_dir in f.parents:
                        same_pkg_refs.append(str(f.relative_to(REPO_ROOT)))
                    else:
                        other_src_refs.append(str(f.relative_to(REPO_ROOT)))
            test_refs = [
                str(f.relative_to(REPO_ROOT)) for f, txt in test_texts.items() if sym in txt
            ]
            inventory.append(
                {
                    "package": pkg_name,
                    "symbol": sym,
                    "same_pkg_files": same_pkg_refs,
                    "other_src_files": other_src_refs,
                    "test_files": test_refs,
                    "unreferenced_everywhere": len(other_src_refs) == 0 and len(test_refs) == 0,
                }
            )
    return inventory


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    main_head = subprocess.check_output(
        ["git", "rev-parse", "main"], cwd=REPO_ROOT, text=True
    ).strip()
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True
    ).strip()
    import numpy as np
    import pytest

    graph = extract_import_graph()
    classes = classify_classes_adr008()
    symbols = scan_symbol_usage()

    summary = {
        "head": head,
        "baseline_main_commit": main_head,
        "git_status_porcelain": status,
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "pytest_version": pytest.__version__,
        "import_graph": graph,
        "classes": classes,
        "symbols": symbols,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

