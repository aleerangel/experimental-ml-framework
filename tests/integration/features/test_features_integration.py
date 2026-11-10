"""Integration tests for M3.1 feature exploration pipeline and architectural purity.

Complies with EXP-01 to EXP-08, XCUT-02, CA-E2-01, ADR-005, ADR-007, and ADR-008.
"""

from __future__ import annotations

import json
import subprocess
import sys
import numpy as np
import pytest

from experimental_ml.core.enums import MetricStatus, TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    PreparationRule,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features import (
    METHODOLOGICAL_WARNINGS,
    SCOPE_EXPLORATORY_FULL_DATA,
    ExploratoryFeatureReport,
    explore_features,
)


def test_exp_08_end_to_end_pipeline() -> None:
    """Proof C8: Full end-to-end integration from raw ingestion to exploratory feature report (EXP-01 to EXP-08)."""
    np.random.seed(1337)
    n = 120
    x_base = np.linspace(1.0, 50.0, n)
    # feat1: continuous predictor
    feat1 = x_base + np.random.normal(0, 0.5, n)
    # feat2: highly collinear with feat1 (r > 0.95)
    feat2 = 2.5 * feat1 + np.random.normal(0, 0.2, n)
    # feat3: uncorrelated random noise
    feat3 = np.random.normal(10.0, 3.0, n)
    # feat_cat: discrete categorical variable
    feat_cat = np.where(x_base > 25.0, "high", "low")
    # target: linear combination + noise
    target = 3.0 * feat1 - 1.2 * feat3 + np.random.normal(0, 1.0, n)

    data = {
        "feat_num1": feat1,
        "feat_num2": feat2,
        "feat_num3": feat3,
        "feat_cat": feat_cat,
        "target": target,
    }

    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.REGRESSION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)

    # If unencoded categorical finding exists, defer it intra-fold
    rules = []
    for finding in profile.findings:
        if finding.code == "E1_CATEGORICAL_UNENCODED":
            col_name = (finding.context or {}).get("column", "feat_cat")
            rules.append(
                PreparationRule(
                    finding.code,
                    col_name,
                    "DEFER_INTRA_FOLD",
                    {"encoding_strategy": "ONE_HOT"},
                )
            )

    plan = create_preparation_plan(profile, rules)
    assert plan.status == "READY"

    sanitized_view = sanitize_dataset(bundle, profile, plan)
    assert sanitized_view.dataset_hash == bundle.dataset_hash

    # Execute exploratory feature analysis
    report = explore_features(sanitized_view, redundancy_threshold=0.90)

    # 1. Assert mandatory scope and warnings (EXP-01, CA-E2-01)
    assert report.scope == SCOPE_EXPLORATORY_FULL_DATA
    assert report.dataset_hash == sanitized_view.dataset_hash
    assert report.task_type == TaskType.REGRESSION
    assert report.warnings == METHODOLOGICAL_WARNINGS

    # 2. Assert target associations calculated (EXP-02, EXP-03)
    target_metric_names = {(a.feature_name, a.metric_name) for a in report.target_associations}
    assert ("feat_num1", "PEARSON") in target_metric_names
    assert ("feat_num1", "SPEARMAN") in target_metric_names
    assert ("feat_cat", "CORRELATION_RATIO") in target_metric_names

    for assoc in report.target_associations:
        assert assoc.status == MetricStatus.VALID
        assert not np.isnan(assoc.value)

    # 3. Assert redundancy matrix and high redundancy detection (EXP-06)
    matrix = report.pairwise_redundancy_matrix
    assert "feat_num1" in matrix
    assert matrix["feat_num1"]["feat_num2"] == pytest.approx(matrix["feat_num2"]["feat_num1"], abs=1e-6)
    assert matrix["feat_num1"]["feat_num1"] == 1.0

    # High redundancy pair (feat_num1, feat_num2) detected with |r| >= 0.90
    redundant_pair_features = {(p.feature_a, p.feature_b) for p in report.high_redundancy_pairs}
    assert ("feat_num1", "feat_num2") in redundant_pair_features or ("feat_num2", "feat_num1") in redundant_pair_features

    # 4. Assert serialization roundtrip conformity (EXP-07)
    serialized = report.to_dict()
    json_bytes = json.dumps(serialized, allow_nan=False, indent=2).encode("utf-8")
    reconstructed = ExploratoryFeatureReport.from_dict(json.loads(json_bytes.decode("utf-8")))

    assert reconstructed.scope == report.scope
    assert reconstructed.dataset_hash == report.dataset_hash
    assert len(reconstructed.target_associations) == len(report.target_associations)
    assert len(reconstructed.high_redundancy_pairs) == len(report.high_redundancy_pairs)


def test_xcut_02_runtime_purity_subprocess() -> None:
    """Verify XCUT-02: zero external runtime dependencies (scipy, sklearn, pandas absent from sys.modules)."""
    script = (
        "import sys\n"
        "import experimental_ml.features as features\n"
        "forbidden = {'scipy', 'sklearn', 'pandas', 'statsmodels'} & set(sys.modules)\n"
        "if forbidden:\n"
        "    print(f'VIOLATION: Forbidden modules in sys.modules: {forbidden}')\n"
        "    sys.exit(1)\n"
        "sys.exit(0)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Runtime purity check failed: {result.stdout} {result.stderr}"
