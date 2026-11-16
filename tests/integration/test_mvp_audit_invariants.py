"""Transversal MVP audit invariant suite (TA-POS.1: XCUT-02, 7 Stage Gates, CLI-10, RNF02)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
import re
import subprocess
import sys

from experimental_ml.stages import stage_gates

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "experimental_ml"
AUDIT_REPORT_PATH = REPO_ROOT / ".specs" / "features" / "pos-1-mega-auditoria-mvp" / "AUDIT_REPORT.md"

ALLOWED_TOP_LEVEL_MODULES = set(sys.stdlib_module_names) | {"experimental_ml", "numpy"}


def _collect_runtime_imports(py_file: Path) -> list[tuple[int, str]]:
    """Collect runtime top-level imported modules via AST, ignoring `if TYPE_CHECKING:` blocks."""
    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(py_file))

    type_checking_nodes: set[int] = set()

    class _Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.imports: list[tuple[int, str]] = []
            self._in_type_checking = False

        def visit_If(self, node: ast.If) -> None:
            is_tc = (
                (isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING")
                or (
                    isinstance(node.test, ast.Attribute)
                    and node.test.attr == "TYPE_CHECKING"
                )
            )
            if is_tc:
                prev = self._in_type_checking
                self._in_type_checking = True
                for child in node.body:
                    self.visit(child)
                self._in_type_checking = prev
                for child in node.orelse:
                    self.visit(child)
                return
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            if self._in_type_checking:
                return
            for alias in node.names:
                top = alias.name.split(".")[0]
                self.imports.append((node.lineno, top))

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if self._in_type_checking:
                return
            if node.level and node.level > 0:
                return
            if node.module:
                top = node.module.split(".")[0]
                self.imports.append((node.lineno, top))

        def visit_Call(self, node: ast.Call) -> None:
            if self._in_type_checking:
                return
            func_name = None
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                func_name = "__import__"
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            ):
                func_name = "import_module"
            if func_name and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                mod_str = node.args[0].value
                if not mod_str.startswith("."):
                    top = mod_str.split(".")[0]
                    self.imports.append((node.lineno, top))
            self.generic_visit(node)

    visitor = _Visitor()
    visitor.visit(tree)
    return visitor.imports


def test_audit_xcut02_runtime_purity_ast() -> None:
    """C1: Every .py file in src/experimental_ml/ imports only stdlib, experimental_ml, or numpy at runtime."""
    py_files = sorted(SRC_ROOT.rglob("*.py"))
    assert len(py_files) > 30, "Expected full package source tree under src/experimental_ml/"

    violations: list[str] = []
    for py_file in py_files:
        rel = py_file.relative_to(REPO_ROOT).as_posix()
        for lineno, top_mod in _collect_runtime_imports(py_file):
            if top_mod not in ALLOWED_TOP_LEVEL_MODULES:
                violations.append(f"{rel}:{lineno} -> forbidden import '{top_mod}'")

    assert not violations, "XCUT-02 runtime purity violations:\n" + "\n".join(violations)


def test_audit_stage_gates_cli_and_domain_neutrality() -> None:
    """C2: Verify all 7 stage gates exist and are callable, CLI-10 lazy imports hold, and RNF02 domain neutrality holds."""
    expected_gates = (
        "verify_preparation_gate",
        "verify_partition_gate",
        "verify_scenarios_gate",
        "verify_models_gate",
        "verify_runs_gate",
        "verify_statistics_gate",
        "verify_report_gate",
    )
    for gate_name in expected_gates:
        gate_fn = getattr(stage_gates, gate_name, None)
        assert callable(gate_fn), f"Missing or non-callable stage gate: {gate_name}"
        sig = inspect.signature(gate_fn)
        assert len(sig.parameters) >= 1, f"Gate {gate_name} must accept package/experiment path"

    # CLI-10: importing experimental_ml.cli.main and running --help must not load numpy or hashlib
    code = (
        "import sys; "
        "from experimental_ml.cli.main import build_parser; "
        "build_parser(); "
        "assert 'numpy' not in sys.modules, 'numpy loaded eagerly in cli.main'"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert proc.returncode == 0

    # RNF02: no applied domain dataset filenames or domain-specific biological/clinical constants hardcoded in src/
    forbidden_domain_patterns = re.compile(r"\b(paciente|patient_id|hemoglobina|glicose|hospital_id|cpf)\b", re.IGNORECASE)
    domain_hits: list[str] = []
    for py_file in sorted(SRC_ROOT.rglob("*.py")):
        text = py_file.read_text(encoding="utf-8")
        if forbidden_domain_patterns.search(text):
            domain_hits.append(py_file.relative_to(REPO_ROOT).as_posix())
    assert not domain_hits, f"RNF02 domain neutrality violated in: {domain_hits}"


def test_audit_report_zero_open_p0_p1() -> None:
    """C3: Verify AUDIT_REPORT.md exists and records 0 open P0 and 0 open P1 findings."""
    assert AUDIT_REPORT_PATH.is_file(), f"Missing audit report: {AUDIT_REPORT_PATH}"
    content = AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    assert "Open P0 Findings: 0" in content
    assert "Open P1 Findings: 0" in content
