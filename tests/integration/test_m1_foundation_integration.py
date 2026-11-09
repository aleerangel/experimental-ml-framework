"""Integration test suite for M1 Foundation (m1-5-foundation-hardening).

Exercises cross-module integration across experimental_ml.core, experimental_ml.data,
and experimental_ml.metrics, cross-process hash determinism (PYTHONHASHSEED), automated
execution of all README.md Python code blocks, and audit finding governance checks
(HARD-12, HARD-13, HARD-14, HARD-15).
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import pytest

from experimental_ml.core import (
    AggregationScope,
    ExperimentId,
    MetricDirection,
    ObservationId,
    TaskType,
    config_hash,
    dataset_hash,
    is_missing_scalar,
    is_nan_scalar,
)
from experimental_ml.data import (
    ColumnSemanticType,
    DatasetBundle,
    DatasetSchemaSpec,
    get_column_array,
    load_dataset,
    slice_bundle_by_observation_ids,
)
from experimental_ml.metrics import (
    aggregate_fold_metrics,
    compute_metric,
    get_metric_spec,
    is_better,
    rank_configurations,
)


def test_hard_12_readme_python_blocks_execute_cleanly() -> None:
    """Validate that every fenced python code block in README.md executes cleanly in subprocess (HARD-12)."""
    readme_path = Path(__file__).resolve().parents[2] / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    # Extract all ```python blocks
    blocks = re.findall(r"```python\n(.*?)```", content, re.DOTALL)
    assert len(blocks) >= 4, f"Expected at least 4 python blocks in README.md, found {len(blocks)}"

    for idx, code in enumerate(blocks, 1):
        # Run code block in isolated subprocess with current venv python
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONHASHSEED": "42"},
        )
        assert proc.returncode == 0, (
            f"README.md Python block {idx} failed with exit code {proc.returncode}:\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\nCODE:\n{code}"
        )


def test_hard_13_documentation_and_symbol_counts_aligned() -> None:
    """Validate exported symbol counts in core and data match docs (HARD-13)."""
    import experimental_ml.core as core_mod
    import experimental_ml.data as data_mod

    # core has 28 exported symbols (__all__)
    assert len(core_mod.__all__) == 28
    # data had 13 exported symbols in M1.5, expands to 17 in M2.1, 23 in M2.2, and 24 in M2 hardening
    assert len(data_mod.__all__) in (13, 17, 23, 24)


def test_hard_14_end_to_end_core_data_metrics_and_cross_process_hash(tmp_path: Path) -> None:
    """Validate end-to-end integration across core, data and metrics, plus cross-process hash (HARD-14)."""
    # 1. Ingest dataset with schema
    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.REGRESSION,
        column_semantic_types={"feature": ColumnSemanticType.NUMERIC_CONTINUOUS},
    )
    raw_data = {
        "feature": [1.0, 2.0, 3.0, 4.0],
        "target": [10.0, 20.0, 30.0, 40.0],
    }
    bundle = load_dataset(raw_data, schema)
    assert isinstance(bundle, DatasetBundle)
    assert bundle.n_rows == 4
    assert len(bundle.observation_ids) == 4

    # 2. Slice bundle by observation IDs and extract column arrays
    train_ids = [bundle.observation_ids[0], bundle.observation_ids[1]]
    val_ids = [bundle.observation_ids[2], bundle.observation_ids[3]]

    train_bundle = slice_bundle_by_observation_ids(bundle, train_ids)
    val_bundle = slice_bundle_by_observation_ids(bundle, val_ids)

    y_val_true = get_column_array(val_bundle, "target")
    # Mock model predictions
    y_val_pred = y_val_true + 1.0

    # 3. Compute metric and aggregate
    m1 = compute_metric("rmse", y_val_true, y_val_pred)
    m2 = compute_metric("rmse", y_val_true, y_val_pred)
    agg = aggregate_fold_metrics([m1, m2])
    assert agg.mean > 0.0

    # 4. Rank candidates
    ranked = rank_configurations(
        {"model_a": agg, "model_b": agg},
        direction=MetricDirection.MINIMIZE,
    )
    assert len(ranked) == 2

    # 5. Cross-process hash determinism
    script = (
        "import numpy as np\n"
        "from experimental_ml.core import dataset_hash\n"
        "h = dataset_hash({'a': [1.0], 'b': [2.0]}, observation_ids=['obs_0'])\n"
        "print(h)\n"
    )
    res1 = subprocess.check_output(
        [sys.executable, "-c", script],
        env={**os.environ, "PYTHONHASHSEED": "0"},
        text=True,
    ).strip()
    res2 = subprocess.check_output(
        [sys.executable, "-c", script],
        env={**os.environ, "PYTHONHASHSEED": "9999"},
        text=True,
    ).strip()
    assert res1 == res2


def test_hard_15_audit_findings_governance_and_integrity_preservation() -> None:
    """Validate that m1-integrity-review reports are preserved and RESULTS.md tracks all findings (HARD-15)."""
    repo_root = Path(__file__).resolve().parents[2]
    audit_reports_dir = repo_root / ".specs" / "features" / "m1-integrity-review" / "reports"
    assert audit_reports_dir.exists()
    assert (audit_reports_dir / "06-achados.md").exists()
    assert (audit_reports_dir / "07-plano-correcoes.md").exists()
    assert (audit_reports_dir / "08-parecer.md").exists()

    # Verify no retroactive verification.md fabricated in m1-1-setup-cli-smoke
    m1_1_verification = repo_root / ".specs" / "features" / "m1-1-setup-cli-smoke" / "verification.md"
    assert not m1_1_verification.exists()
