"""Probe script for Dimension C (Implementation Quality & Performance) of M1 Integrity Review.

Checks QUAL-01 through QUAL-06 empirically without modifying any repository files.
"""

from __future__ import annotations

import ast
import json
import math
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np

from experimental_ml.core import (
    AggregationScope,
    DataIntegrityError,
    Finding,
    FindingSeverity,
    MetricDirection,
    MetricStatus,
    ObservationId,
    TaskType,
    config_hash,
    dataset_hash,
)
from experimental_ml.data import (
    ColumnDescriptor,
    ColumnSemanticType,
    DatasetBundle,
    DatasetSchemaSpec,
    get_column_array,
    load_dataset,
)
from experimental_ml.metrics import (
    AggregatedMetricValue,
    MetricEvaluationScope,
    MetricValue,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "src" / "experimental_ml"


def probe_qual_01_ast_scan() -> dict[str, Any]:
    """QUAL-01: AST scan for bare excepts, swallowed exceptions, mutable defaults, runtime asserts, mutable globals."""
    bare_excepts = []
    swallowed_excepts = []
    mutable_defaults = []
    runtime_asserts = []
    mutable_globals = []

    for py_file in sorted(SRC_ROOT.rglob("*.py")):
        rel = str(py_file.relative_to(REPO_ROOT))
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=rel)

        # Top-level mutable globals
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                val = node.value
                targets = (
                    [t.id for t in node.targets if isinstance(t, ast.Name)]
                    if isinstance(node, ast.Assign)
                    else ([node.target.id] if isinstance(node.target, ast.Name) else [])
                )
                for t_name in targets:
                    if t_name == "__all__":
                        continue
                    if isinstance(val, (ast.List, ast.Dict, ast.Set)):
                        mutable_globals.append({"file": rel, "line": node.lineno, "name": t_name, "type": type(val).__name__})

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    bare_excepts.append({"file": rel, "line": node.lineno})
                # Check if body is just Pass or Continue without logging/raising
                if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Continue)):
                    swallowed_excepts.append({"file": rel, "line": node.lineno, "stmt": type(node.body[0]).__name__})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                all_defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
                for d in all_defaults:
                    if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                        mutable_defaults.append({"file": rel, "line": node.lineno, "func": node.name})
            elif isinstance(node, ast.Assert):
                runtime_asserts.append({"file": rel, "line": node.lineno})

    return {
        "bare_excepts": bare_excepts,
        "swallowed_excepts": swallowed_excepts,
        "mutable_defaults": mutable_defaults,
        "runtime_asserts": runtime_asserts,
        "mutable_globals": mutable_globals,
    }


def probe_qual_02_type_annotations() -> dict[str, Any]:
    """QUAL-02: Verify public functions have complete parameter and return type annotations."""
    missing_annotations = []
    total_public_functions = 0

    for py_file in sorted(SRC_ROOT.rglob("*.py")):
        rel = str(py_file.relative_to(REPO_ROOT))
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=rel)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                total_public_functions += 1
                missing_params = [
                    arg.arg
                    for arg in (node.args.posonlyargs + node.args.args + node.args.kwonlyargs)
                    if arg.arg != "self" and arg.annotation is None
                ]
                has_return = node.returns is not None
                if missing_params or not has_return:
                    missing_annotations.append({
                        "file": rel,
                        "line": node.lineno,
                        "func": node.name,
                        "missing_params": missing_params,
                        "has_return": has_return,
                    })

    return {
        "total_public_functions": total_public_functions,
        "missing_annotations": missing_annotations,
    }


def probe_qual_03_edge_cases() -> dict[str, Any]:
    """QUAL-03: Edge cases across core, metrics, data."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)

    # 1. Column-name concatenation collision in core.dataset_hash
    h_col_collision_1 = dataset_hash({"ab": [1.0], "c": [2.0]}, schema)
    h_col_collision_2 = dataset_hash({"a": [1.0], "bc": [2.0]}, schema)

    # 2. np.float32(np.nan) in 2D ndarray passed to load_dataset and dataset_hash
    arr_f32_nan = np.array([[np.float32(np.nan), np.float32(1.0)], [np.float32(2.0), np.float32(3.0)]], dtype=np.float32)
    bundle_f32 = load_dataset(arr_f32_nan, DatasetSchemaSpec(target_col="col_1", task_type=TaskType.REGRESSION), has_header=False)
    col0_n_missing = bundle_f32.descriptors["col_0"].n_missing
    col0_actual_isnan_count = int(np.isnan(bundle_f32.columns["col_0"]).sum())

    # 3. Duplicate NFC column names in in-memory dict (e.g. 'e\u0301' NFD vs '\u00e9' NFC)
    nfd_key = unicodedata.normalize("NFD", "é")
    nfc_key = unicodedata.normalize("NFC", "é")
    try:
        b_dup_nfc = load_dataset({nfd_key: [1.0, 2.0], nfc_key: [10.0, 20.0], "y": [3.0, 4.0]}, schema)
        dup_nfc_result = {
            "raised": None,
            "retained_values": b_dup_nfc.columns[nfc_key].tolist(),
            "silently_overwritten": True,
        }
    except Exception as exc:
        dup_nfc_result = {"raised": type(exc).__name__, "silently_overwritten": False}

    # 4. Control character \x00 in DomainIdentifier
    try:
        oid_null = ObservationId("obs_\x00_1")
        null_char_accepted = True
    except Exception:
        null_char_accepted = False

    # 5. Non-NFC string in ObservationId
    oid_nfd = ObservationId("obs_" + nfd_key)
    oid_nfc = ObservationId("obs_" + nfc_key)
    oid_nfc_normalized = (str(oid_nfd) == str(oid_nfc))

    # 6. Integer >= 2**63 in load_dataset
    try:
        load_dataset({"x": [2**63], "y": [1.0]}, schema)
        int64_overflow_raised = None
    except Exception as exc:
        int64_overflow_raised = type(exc).__name__

    return {
        "column_name_hash_collision": {
            "hash_ab_c": h_col_collision_1,
            "hash_a_bc": h_col_collision_2,
            "collides": h_col_collision_1 == h_col_collision_2,
        },
        "float32_nan_missing_count": {
            "descriptor_n_missing": col0_n_missing,
            "actual_isnan_in_array": col0_actual_isnan_count,
            "mismatch": col0_n_missing != col0_actual_isnan_count,
        },
        "in_memory_dict_duplicate_nfc_keys": dup_nfc_result,
        "domain_identifier_accepts_null_byte": null_char_accepted,
        "domain_identifier_normalizes_nfc": oid_nfc_normalized,
        "int64_overflow_exception": int64_overflow_raised,
    }


def probe_qual_04_scaling_benchmark() -> dict[str, Any]:
    """QUAL-04: Scaling benchmark for 10,000 vs 100,000 rows x 20 columns."""
    rng = np.random.default_rng(42)
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)

    results = {}
    for n_rows in (10_000, 100_000):
        mem_data: dict[str, Any] = {f"f_{j}": rng.standard_normal(n_rows) for j in range(19)}
        mem_data["y"] = rng.standard_normal(n_rows)

        t0 = time.perf_counter()
        bundle_mem = load_dataset(mem_data, schema)
        t_mem = time.perf_counter() - t0

        t0 = time.perf_counter()
        _ = dataset_hash(bundle_mem.columns, schema)
        t_hash = time.perf_counter() - t0

        with tempfile.TemporaryDirectory(prefix="m1-audit-perf-") as tmpdir:
            csv_path = Path(tmpdir) / f"bench_{n_rows}.csv"
            # Fast CSV generation
            header = ",".join(mem_data.keys()) + "\n"
            mat = np.column_stack(list(mem_data.values()))
            with csv_path.open("w", encoding="utf-8") as f:
                f.write(header)
                np.savetxt(f, mat, delimiter=",", fmt="%.6f")

            t0 = time.perf_counter()
            _ = load_dataset(csv_path, schema)
            t_csv = time.perf_counter() - t0

        results[str(n_rows)] = {
            "load_in_memory_sec": round(t_mem, 4),
            "dataset_hash_sec": round(t_hash, 4),
            "load_csv_sec": round(t_csv, 4),
        }

    ratio_mem = round(results["100000"]["load_in_memory_sec"] / max(results["10000"]["load_in_memory_sec"], 1e-6), 2)
    ratio_hash = round(results["100000"]["dataset_hash_sec"] / max(results["10000"]["dataset_hash_sec"], 1e-6), 2)
    ratio_csv = round(results["100000"]["load_csv_sec"] / max(results["10000"]["load_csv_sec"], 1e-6), 2)

    return {
        "timings": results,
        "scaling_ratios_100k_vs_10k": {
            "load_in_memory_ratio": ratio_mem,
            "dataset_hash_ratio": ratio_hash,
            "load_csv_ratio": ratio_csv,
        },
    }


def probe_qual_05_adversarial_immutability() -> dict[str, Any]:
    """QUAL-05: Adversarial immutability probe across DatasetBundle, dataclasses, and DomainIdentifier."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    bundle = load_dataset({"x": [1.0, 2.0], "y": [3.0, 4.0]}, schema)

    # 1. Numeric array setflags(write=True)
    arr_x = get_column_array(bundle, "x", copy=False)
    try:
        arr_x.setflags(write=True)
        numeric_setflags_blocked = False
    except ValueError:
        numeric_setflags_blocked = True

    # 2. MappingProxyType mutation
    try:
        bundle.columns["z"] = np.array([1.0, 2.0])  # type: ignore[index]
        mapping_mutation_blocked = False
    except TypeError:
        mapping_mutation_blocked = True

    # 3. Object column with mutable SimpleNamespace
    ns1 = types.SimpleNamespace(val="initial_1")
    ns2 = types.SimpleNamespace(val="initial_2")
    bundle_obj = load_dataset(
        {"cat": [ns1, ns2], "y": [1.0, 2.0]},
        schema,
    )
    ns1.val = "mutated_after_load"
    object_col_mutated_in_place = (
        bundle_obj.columns["cat"][0].val == "mutated_after_load"
    )

    # 4. Object column setflags(write=True) check
    obj_arr = get_column_array(bundle_obj, "cat", copy=False)
    try:
        obj_arr.setflags(write=True)
        object_setflags_succeeded = True
    except ValueError:
        object_setflags_succeeded = False

    # 5. DomainIdentifier __dict__ mutation
    oid = bundle.observation_ids[0]
    try:
        oid.injected_attr = ["mutable_state"]  # type: ignore[attr-defined]
        identifier_dict_mutable = hasattr(oid, "__dict__") and oid.injected_attr == ["mutable_state"]  # type: ignore[attr-defined]
    except AttributeError:
        identifier_dict_mutable = False

    return {
        "numeric_setflags_blocked": numeric_setflags_blocked,
        "mapping_mutation_blocked": mapping_mutation_blocked,
        "object_col_mutable_container_bypass": object_col_mutated_in_place,
        "object_col_setflags_write_true_succeeded": object_setflags_succeeded,
        "domain_identifier_has_mutable_dict": identifier_dict_mutable,
    }


def probe_qual_06_interpreters() -> dict[str, Any]:
    """QUAL-06: Check available Python interpreters on host against RNF06 (3.10, 3.11, 3.12)."""
    interpreters = {}
    for ver in ("python3.10", "python3.11", "python3.12", "python3.13", "python3.14"):
        path = shutil.which(ver)
        if path is None:
            interpreters[ver] = {"installed": False, "status": "NÃO VERIFICÁVEL (interpretador ausente no host)"}
        else:
            res = subprocess.run([path, "--version"], capture_output=True, text=True, check=False)
            interpreters[ver] = {
                "installed": True,
                "path": path,
                "version": res.stdout.strip() or res.stderr.strip(),
            }
    return {"interpreters": interpreters}


def main() -> None:
    report = {
        "QUAL-01": probe_qual_01_ast_scan(),
        "QUAL-02": probe_qual_02_type_annotations(),
        "QUAL-03": probe_qual_03_edge_cases(),
        "QUAL-04": probe_qual_04_scaling_benchmark(),
        "QUAL-05": probe_qual_05_adversarial_immutability(),
        "QUAL-06": probe_qual_06_interpreters(),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
