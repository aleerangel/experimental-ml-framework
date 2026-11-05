"""Probe script for Dimension D (Testing Strategy & TLC Validator Reliability) of M1 Integrity Review.

Checks TEST-01 through TEST-08 empirically, using ephemeral /tmp/m1-audit-* directories for
mutations and check_proofs.py runs, and cleans them up before exiting.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import trace
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "src" / "experimental_ml"
TESTS_ROOT = REPO_ROOT / "tests"
TLC_SCRIPTS = REPO_ROOT / ".agent" / "skills" / "tlc-spec-driven" / "scripts"


def probe_test_01_line_coverage() -> dict[str, Any]:
    """TEST-01: Per-file line coverage of src/experimental_ml/ via trace during pytest."""
    tracer = trace.Trace(count=1, trace=0)
    tracer.runfunc(pytest.main, ["-q", str(TESTS_ROOT)])
    results = tracer.results()

    per_file = {}
    total_exec = 0
    total_hit = 0

    for py_file in sorted(SRC_ROOT.rglob("*.py")):
        abs_str = str(py_file.resolve())
        rel_str = str(py_file.relative_to(REPO_ROOT))
        lines = py_file.read_text(encoding="utf-8").splitlines()
        executable_lines = set(trace._find_executable_linenos(abs_str).keys())

        # Remove pure docstring/signature-only lines or module headers that trace marks
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=rel_str)
        docstring_lines: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    expr = node.body[0]
                    for ln in range(expr.lineno, (expr.end_lineno or expr.lineno) + 1):
                        docstring_lines.add(ln)

        executable_lines -= docstring_lines
        # Also exclude lines that are just `except ...:` or `else:` or closing parens if not counted
        hit_lines = {
            lineno
            for (fname, lineno), count in results.counts.items()
            if Path(fname).resolve() == py_file.resolve() and count > 0 and lineno in executable_lines
        }
        missed = sorted(executable_lines - hit_lines)
        n_exec = len(executable_lines)
        n_hit = len(hit_lines)
        pct = round(100.0 * n_hit / n_exec, 1) if n_exec > 0 else 100.0

        total_exec += n_exec
        total_hit += n_hit
        per_file[rel_str] = {
            "executable_lines": n_exec,
            "covered_lines": n_hit,
            "coverage_pct": pct,
            "missed_lines": missed,
        }

    overall_pct = round(100.0 * total_hit / total_exec, 1) if total_exec > 0 else 100.0
    return {
        "overall_executable_lines": total_exec,
        "overall_covered_lines": total_hit,
        "overall_coverage_pct": overall_pct,
        "per_file": per_file,
    }


def probe_test_02_test_inventory() -> dict[str, Any]:
    """TEST-02: Inventory of test files and test functions."""
    inventory = {}
    total_tests = 0
    for tf in sorted(TESTS_ROOT.rglob("test_*.py")):
        rel = str(tf.relative_to(REPO_ROOT))
        tree = ast.parse(tf.read_text(encoding="utf-8"), filename=rel)
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
        inventory[rel] = {"count": len(funcs), "tests": funcs}
        total_tests += len(funcs)
    return {"total_test_functions": total_tests, "files": inventory}


def probe_test_03_mutations() -> dict[str, Any]:
    """TEST-03: Apply >= 12 controlled semantic mutations in /tmp/m1-audit-mut/ and measure kill rate."""
    mutations = [
        {
            "id": "MUT-01",
            "module": "core",
            "file": "src/experimental_ml/core/hashing.py",
            "description": "Disable -0.0 -> 0.0 canonicalization in _canonical_transform",
            "target": "        if f == 0.0:\n            f = 0.0",
            "replacement": "        if False:\n            f = 0.0",
        },
        {
            "id": "MUT-02",
            "module": "core",
            "file": "src/experimental_ml/core/hashing.py",
            "description": "Disable Unicode NFC normalization in _canonical_transform",
            "target": '    if isinstance(obj, str):\n        return unicodedata.normalize("NFC", obj)',
            "replacement": "    if isinstance(obj, str):\n        return obj",
        },
        {
            "id": "MUT-03",
            "module": "core",
            "file": "src/experimental_ml/core/seeds.py",
            "description": "Return constant seed tuple in derive_seeds instead of SeedSequence",
            "target": "return tuple(int(s) for s in states)",
            "replacement": "return tuple(42 for _ in states)",
        },
        {
            "id": "MUT-04",
            "module": "core",
            "file": "src/experimental_ml/core/types.py",
            "description": "Allow empty string in DomainIdentifier.__new__",
            "target": 'if not stripped:\n            raise ValueError(f"{cls.__name__} cannot be empty or purely whitespace")',
            "replacement": 'if False:\n            raise ValueError(f"{cls.__name__} cannot be empty or purely whitespace")',
        },
        {
            "id": "MUT-05",
            "module": "metrics",
            "file": "src/experimental_ml/metrics/regression.py",
            "description": "Invert MBE sign (y_true - y_pred instead of y_pred - y_true)",
            "target": "    val = float(np.mean(yp - yt))",
            "replacement": "    val = float(np.mean(yt - yp))",
        },
        {
            "id": "MUT-06",
            "module": "metrics",
            "file": "src/experimental_ml/metrics/regression.py",
            "description": "Return VALID instead of UNDEFINED_NAN when ss_tot == 0 in r2",
            "target": '    if m_tot == 0.0 or s_tot == 0.0:\n        return MetricValue(\n            metric_id="r2",\n            value=float("nan"),\n            status=MetricStatus.UNDEFINED_NAN,',
            "replacement": '    if m_tot == 0.0 or s_tot == 0.0:\n        return MetricValue(\n            metric_id="r2",\n            value=0.0,\n            status=MetricStatus.VALID,',
        },
        {
            "id": "MUT-07",
            "module": "metrics",
            "file": "src/experimental_ml/metrics/aggregation.py",
            "description": "Treat UNDEFINED_NAN candidate as better in is_better",
            "target": "    if not rankable_a and rankable_b:\n        return False",
            "replacement": "    if not rankable_a and rankable_b:\n        return True",
        },
        {
            "id": "MUT-08",
            "module": "metrics",
            "file": "src/experimental_ml/metrics/catalog.py",
            "description": "Disable compare_by_abs on MBE in METRICS_CATALOG",
            "target": "        compare_by_abs=True,",
            "replacement": "        compare_by_abs=False,",
        },
        {
            "id": "MUT-09",
            "module": "data",
            "file": "src/experimental_ml/data/loader.py",
            "description": "Skip np.frombuffer immutable bytes backing for float64 arrays",
            "target": "            temp = np.array(float_vals, dtype=np.float64)\n            immutable = np.frombuffer(temp.tobytes(), dtype=np.float64)",
            "replacement": "            immutable = np.array(float_vals, dtype=np.float64)\n            immutable.flags.writeable = False",
        },
        {
            "id": "MUT-10",
            "module": "data",
            "file": "src/experimental_ml/data/query.py",
            "description": "Sort observation_ids in slice_bundle_by_observation_ids instead of preserving requested order",
            "target": "    for obs in observation_ids:",
            "replacement": "    for obs in sorted(observation_ids):",
        },
        {
            "id": "MUT-11",
            "module": "data",
            "file": "src/experimental_ml/data/validation.py",
            "description": "Allow duplicate observation IDs in assign_or_validate_observation_ids",
            "target": "        if obs_id in seen:\n            raise DataIntegrityError(",
            "replacement": "        if False:\n            raise DataIntegrityError(",
        },
        {
            "id": "MUT-12",
            "module": "cli",
            "file": "src/experimental_ml/cli/main.py",
            "description": "Alter CLI program name in build_parser",
            "target": 'prog="expml",',
            "replacement": 'prog="wrong_cli_name",',
        },
    ]

    tmp_dir = Path("/tmp/m1-audit-mut")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    results = []
    try:
        shutil.copytree(REPO_ROOT / "src", tmp_dir / "src")
        shutil.copytree(REPO_ROOT / "tests", tmp_dir / "tests")

        for mut in mutations:
            target_file = tmp_dir / mut["file"]
            orig_text = target_file.read_text(encoding="utf-8")
            assert mut["target"] in orig_text, f"Target not found for {mut['id']}"
            mut_text = orig_text.replace(mut["target"], mut["replacement"], 1)
            target_file.write_text(mut_text, encoding="utf-8")

            env = os.environ.copy()
            env["PYTHONPATH"] = str(tmp_dir / "src")
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", str(tmp_dir / "tests"), "-q", "--tb=no"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            killed = proc.returncode != 0
            results.append({
                "id": mut["id"],
                "module": mut["module"],
                "file": mut["file"],
                "description": mut["description"],
                "exit_code": proc.returncode,
                "status": "KILLED" if killed else "SURVIVED",
            })
            # Restore original text
            target_file.write_text(orig_text, encoding="utf-8")
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)

    killed_count = sum(1 for r in results if r["status"] == "KILLED")
    return {
        "total_mutations": len(results),
        "killed": killed_count,
        "survived": len(results) - killed_count,
        "mutation_score_pct": round(100.0 * killed_count / len(results), 1),
        "mutations": results,
        "tmp_dir_cleaned": not tmp_dir.exists(),
    }


def probe_test_04_cross_module_tests() -> dict[str, Any]:
    """TEST-04: Count how many tests in tests/ import both experimental_ml.data and experimental_ml.metrics."""
    cross_tests = []
    per_file_imports = {}
    for tf in sorted(TESTS_ROOT.rglob("test_*.py")):
        rel = str(tf.relative_to(REPO_ROOT))
        text = tf.read_text(encoding="utf-8")
        has_core = "experimental_ml.core" in text
        has_metrics = "experimental_ml.metrics" in text
        has_data = "experimental_ml.data" in text
        per_file_imports[rel] = {"core": has_core, "metrics": has_metrics, "data": has_data}
        if has_metrics and has_data:
            cross_tests.append(rel)

    return {
        "per_file_imports": per_file_imports,
        "files_combining_data_and_metrics": cross_tests,
        "count_combining_data_and_metrics": len(cross_tests),
    }


def probe_test_05_isolation_and_order() -> dict[str, Any]:
    """TEST-05: Run test suite in normal order, reverse order of files, and sample isolated nodeids."""
    forward = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_smoke.py", "tests/unit/test_core.py", "tests/unit/test_metrics.py", "tests/unit/test_data_schemas.py", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    reverse = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/test_data_schemas.py", "tests/unit/test_metrics.py", "tests/unit/test_core.py", "tests/test_smoke.py", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "forward_exit_code": forward.returncode,
        "forward_summary": forward.stdout.strip().splitlines()[-1] if forward.stdout.strip() else "",
        "reverse_exit_code": reverse.returncode,
        "reverse_summary": reverse.stdout.strip().splitlines()[-1] if reverse.stdout.strip() else "",
    }


def probe_test_06_07_08_tlc_validators() -> dict[str, Any]:
    """TEST-06, TEST-07, TEST-08: Run TLC validators across m1-1..m1-4 and check_proofs in /tmp/m1-audit-clone/."""
    features = [
        "m1-1-setup-cli-smoke",
        "m1-2-core",
        "m1-3-metrics",
        "m1-4-datasets-schemas",
    ]
    validator_matrix = {}
    for feat in features:
        v_spec = subprocess.run(
            [sys.executable, str(TLC_SCRIPTS / "validate_spec.py"), feat, "--strict"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        v_tasks = subprocess.run(
            [sys.executable, str(TLC_SCRIPTS / "validate_tasks.py"), feat, "--strict"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        v_verif = subprocess.run(
            [sys.executable, str(TLC_SCRIPTS / "validate_verification.py"), feat, "--strict"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        validator_matrix[feat] = {
            "validate_spec": {"exit_code": v_spec.returncode, "output": (v_spec.stdout + v_spec.stderr).strip()},
            "validate_tasks": {"exit_code": v_tasks.returncode, "output": (v_tasks.stdout + v_tasks.stderr).strip()},
            "validate_verification": {"exit_code": v_verif.returncode, "output": (v_verif.stdout + v_verif.stderr).strip()},
        }

    # Run check_proofs.py in an ephemeral clone /tmp/m1-audit-clone/ so historical proofs.md are untouched
    clone_dir = Path("/tmp/m1-audit-clone")
    if clone_dir.exists():
        shutil.rmtree(clone_dir)
    clone_proofs = {}
    try:
        subprocess.run(["git", "clone", "--quiet", str(REPO_ROOT), str(clone_dir)], check=True)
        # Symlink .venv and exclude it locally in git/info/exclude so git status stays clean
        os.symlink(REPO_ROOT / ".venv", clone_dir / ".venv")
        exclude_file = clone_dir / ".git" / "info" / "exclude"
        exclude_file.write_text(exclude_file.read_text(encoding="utf-8") + "\n.venv\n", encoding="utf-8")
        for feat in features:
            cp = subprocess.run(
                [sys.executable, str(TLC_SCRIPTS / "check_proofs.py"), feat, "--root", str(clone_dir)],
                cwd=clone_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            vv = subprocess.run(
                [sys.executable, str(TLC_SCRIPTS / "validate_verification.py"), feat, "--root", str(clone_dir), "--strict"],
                cwd=clone_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            clone_proofs[feat] = {
                "check_proofs_exit": cp.returncode,
                "check_proofs_output": (cp.stdout + cp.stderr).strip(),
                "validate_verification_after_fresh_proofs_exit": vv.returncode,
                "validate_verification_after_fresh_proofs_output": (vv.stdout + vv.stderr).strip(),
            }
    finally:
        if clone_dir.exists():
            shutil.rmtree(clone_dir)

    return {
        "validator_matrix_on_repo": validator_matrix,
        "ephemeral_clone_proofs": clone_proofs,
        "clone_dir_cleaned": not clone_dir.exists(),
    }


def main() -> None:
    report = {
        "TEST-01": probe_test_01_line_coverage(),
        "TEST-02": probe_test_02_test_inventory(),
        "TEST-03": probe_test_03_mutations(),
        "TEST-04": probe_test_04_cross_module_tests(),
        "TEST-05": probe_test_05_isolation_and_order(),
        "TEST-06_07_08": probe_test_06_07_08_tlc_validators(),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
