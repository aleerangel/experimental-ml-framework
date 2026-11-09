"""Integration and architectural invariant tests for M2.1 dataset profiling.

Tests end-to-end profiling flows, import graph integrity, dependency bounds,
and symbol export counts per XCUT-01, XCUT-02, XCUT-03, and PROF-10.
"""

from __future__ import annotations

import ast
import os
import tomllib
import numpy as np
import pytest

from experimental_ml.core.enums import FindingSeverity, TaskType
from experimental_ml.data import (
    ColumnProfile,
    ColumnSemanticType,
    DatasetBundle,
    DatasetProfile,
    DatasetSchemaSpec,
    ProfileConfig,
    load_dataset,
    profile_dataset,
)


def test_prof_10_immutability_and_determinism() -> None:
    """PROF-10: End-to-end integration test verifying immutability and determinism across calls."""
    data = {
        "x_num": [10.0, 20.0, 30.0, 40.0, 50.0],
        "x_cat": ["A", "B", "A", "C", "B"],
        "target": [0, 1, 0, 1, 0],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)

    initial_hash = bundle.dataset_hash
    initial_arrays = {col: arr.copy() for col, arr in bundle.columns.items()}

    profile_1 = profile_dataset(bundle)

    # Immutability
    assert bundle.dataset_hash == initial_hash
    for col, orig_arr in initial_arrays.items():
        assert len(bundle.columns[col]) == len(orig_arr)
        for v1, v2 in zip(bundle.columns[col], orig_arr):
            assert (v1 == v2) or (v1 != v1 and v2 != v2)

    profile_2 = profile_dataset(bundle)

    # Determinism
    assert profile_1 == profile_2
    assert profile_1.source_dataset_hash == initial_hash
    assert profile_1.findings == profile_2.findings


def test_end_to_end_profiling_on_complex_dataset() -> None:
    """Verify profile_dataset on a realistic dataset with multiple findings."""
    data = {
        "id": ["row_1", "row_2", "row_3", "row_4", "row_5", "row_6"],
        "f_num_normal": [1.0, 2.0, 3.0, 4.0, 5.0, 1.0],
        "f_num_large": [10000.0, 20000.0, 30000.0, 40000.0, 50000.0, 10000.0],
        "f_cat_obj": ["alpha", "beta", "alpha", "gamma", "beta", "alpha"],
        "group": ["g1", "g1", "g2", "g2", "g2", "g1"],
        "target": ["neg", "pos", "neg", "pos", "neg", "neg"],
    }
    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        observation_id_col="id",
        group_col="group",
    )
    bundle = load_dataset(data, schema=schema)

    config = ProfileConfig(scale_disparity_orders=3.0, small_group_size=5)
    profile = profile_dataset(bundle, config=config)

    assert isinstance(profile, DatasetProfile)
    assert profile.n_rows == 6
    assert profile.n_cols == 6

    # Findings should include:
    # 1. E1_CATEGORICAL_UNENCODED on f_cat_obj (CONFIRMED_ISSUE)
    # 2. E1_TARGET_BINARY_UNMAPPED on target (CONFIRMED_ISSUE, classes "neg", "pos")
    # 3. W1_SCALE_DISPARITY (HEURISTIC_WARNING, ratio between f_num_large and f_num_normal is 10000 >= 10^3)
    # 4. W1_SMALL_GROUPS (HEURISTIC_WARNING, g1 size 3 < 5, g2 size 3 < 5)
    # 5. W1_DUPLICATE_ROWS (HEURISTIC_WARNING, row 6 duplicates row 1 excluding 'id')
    codes = [f.code for f in profile.findings]
    assert "E1_CATEGORICAL_UNENCODED" in codes
    assert "E1_TARGET_BINARY_UNMAPPED" in codes
    assert "W1_SCALE_DISPARITY" in codes
    assert "W1_SMALL_GROUPS" in codes
    assert "W1_DUPLICATE_ROWS" in codes

    # Canonical sorting: confirmed issues before heuristic warnings
    seen_warning = False
    for f in profile.findings:
        if f.severity == FindingSeverity.HEURISTIC_WARNING:
            seen_warning = True
        elif f.severity == FindingSeverity.CONFIRMED_ISSUE:
            assert not seen_warning, f"CONFIRMED_ISSUE {f.code} found after HEURISTIC_WARNING"


def test_architectural_import_direction_xcut_01() -> None:
    """XCUT-01: data package must import core, but never validation package or cli."""
    src_data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "src", "experimental_ml", "data")
    src_data_dir = os.path.abspath(src_data_dir)

    for root, _, files in os.walk(src_data_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=fpath)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith("experimental_ml.validation"), f"{fpath} imports validation package"
                        assert not alias.name.startswith("experimental_ml.cli"), f"{fpath} imports cli"
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    assert not mod.startswith("experimental_ml.validation"), f"{fpath} imports from validation package"
                    assert not mod.startswith("experimental_ml.cli"), f"{fpath} imports from cli"


def test_single_runtime_dependency_xcut_02() -> None:
    """XCUT-02: pyproject.toml must declare only numpy>=1.24.0 as runtime dependency."""
    pyproject_path = os.path.join(os.path.dirname(__file__), "..", "..", "pyproject.toml")
    pyproject_path = os.path.abspath(pyproject_path)

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    deps = data.get("project", {}).get("dependencies", [])
    assert len(deps) == 1, f"Expected exactly 1 runtime dependency, found {deps}"
    assert deps[0].startswith("numpy"), f"Expected numpy runtime dependency, found {deps[0]}"


def test_exported_symbols_count_xcut_04() -> None:
    """XCUT-04: experimental_ml.data exports core data and preparation public symbols."""
    import experimental_ml.data as data_pkg

    expected_symbols = [
        "ColumnSemanticType",
        "DatasetSchemaSpec",
        "validate_schema_spec",
        "ColumnDescriptor",
        "DatasetBundle",
        "ColumnProfile",
        "DatasetProfile",
        "ProfileConfig",
        "profile_dataset",
        "SUPPORTED_DELIMITERS",
        "detect_delimiter",
        "parse_tabular_text",
        "assign_or_validate_observation_ids",
        "validate_dataset_schema",
        "load_dataset",
        "get_column_array",
        "slice_bundle_by_observation_ids",
        "slice_view_by_observation_ids",
        "PreparationRule",
        "PreparationPlan",
        "SanitizedDatasetView",
        "UnresolvedFinding",
        "create_preparation_plan",
        "sanitize_dataset",
    ]

    actual_all = getattr(data_pkg, "__all__", [])
    assert len(actual_all) in (23, 24), f"Expected 23 or 24 exported symbols in data, got {len(actual_all)}: {actual_all}"
    for sym in expected_symbols:
        assert sym in actual_all, f"Symbol {sym} missing from data.__all__"
        assert hasattr(data_pkg, sym), f"Symbol {sym} not present on data module"
