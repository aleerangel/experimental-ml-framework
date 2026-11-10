"""Integration tests for M3.2 feature scenarios pipeline and stage gate verification.

Complies with SCN-01 to SCN-08, XCUT-02, CA-E2-02, ADR-002, ADR-005, and ADR-008.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.data import (
    DatasetSchemaSpec,
    PreparationRule,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features import (
    FeatureScenario,
    ScenarioMode,
    ScenariosCatalog,
    explore_features,
    load_scenarios,
    save_scenarios,
    validate_scenarios,
)
from experimental_ml.stages import (
    SCENARIOS_CATALOG_REL_PATH,
    verify_scenarios_gate,
)


def test_scn_08_end_to_end_scenarios_gate() -> None:
    """Proof C8: Full end-to-end integration from raw ingestion to verified scenarios stage gate (SCN-01 to SCN-08)."""
    np.random.seed(42)
    n = 100
    x_base = np.linspace(10.0, 50.0, n)
    # Continuous predictors
    dap = x_base + np.random.normal(0, 1.0, n)
    ht = 0.8 * dap + np.random.normal(0, 0.5, n)
    site = np.random.uniform(20.0, 35.0, n)
    # Constant column to be excluded in Stage 1
    const_col = np.ones(n)
    # Administrative column to be ignored
    admin_id = np.arange(1000, 1000 + n)
    # Group column
    parcela = np.repeat(np.arange(1, 21), 5)
    # Target volume
    vol = 0.001 * (dap ** 2) * ht + np.random.normal(0, 0.05, n)

    data = {
        "dap": dap,
        "ht": ht,
        "site": site,
        "const_flag": const_col,
        "admin_id": admin_id,
        "parcela": parcela,
        "volume": vol,
    }

    schema = DatasetSchemaSpec(
        target_col="volume",
        task_type=TaskType.REGRESSION,
        group_col="parcela",
        ignore_cols=("admin_id",),
    )

    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)

    # Stage 1: Preparation plan and sanitization
    rules = [
        PreparationRule("E1_CONSTANT_COLUMN", "const_flag", "EXCLUDE_COLUMN"),
    ]
    plan = create_preparation_plan(profile, rules)
    assert plan.status == "READY"

    view = sanitize_dataset(bundle, profile, plan)
    assert "const_flag" not in view.candidate_feature_cols
    assert "admin_id" not in view.candidate_feature_cols
    assert set(view.candidate_feature_cols) == {"dap", "ht", "site"}

    # Stage 2: Exploratory features analysis
    report = explore_features(view)
    assert report.scope == "EXPLORATORY_FULL_DATA"

    # Define experimental feature scenarios
    scenario_fixed_minimal = FeatureScenario(
        scenario_id="biometric_minimal",
        name="Biometric Minimal (DAP, HT)",
        description="Standard Schumacher-Hall inputs",
        scientific_justification="Established forestry allometric theory",
        mode=ScenarioMode.FIXED,
        selected_features=("dap", "ht"),
    )
    scenario_fixed_complete = FeatureScenario(
        scenario_id="biometric_all",
        name="All Candidate Features",
        description="Includes diameter, height, and site index",
        scientific_justification="Evaluating site quality contribution",
        mode="FIXED",
        selected_features=("dap", "ht", "site"),
    )
    scenario_dynamic_top_k = FeatureScenario(
        scenario_id="dynamic_top_2",
        name="Dynamic Top 2 Predictors",
        description="Selects top 2 predictors inside each fold without leakage",
        scientific_justification="Automated feature selection baseline",
        mode=ScenarioMode.DYNAMIC,
        strategy_name="CORRELATION_TOP_K",
        strategy_params={"k": 2},
    )

    # Validate scenarios against sanitized view
    catalog = validate_scenarios(
        [scenario_fixed_minimal, scenario_fixed_complete, scenario_dynamic_top_k],
        view,
    )
    assert catalog.dataset_hash == view.dataset_hash
    assert len(catalog.scenarios) == 3

    # Persist and verify via stage gate in a temporary experiment directory
    with tempfile.TemporaryDirectory() as tmpdir:
        exp_dir = Path(tmpdir)
        scenarios_path = exp_dir / SCENARIOS_CATALOG_REL_PATH

        # 1. Save atomically
        save_scenarios(catalog, scenarios_path)
        assert scenarios_path.exists()

        # 2. Gate verification succeeds
        verified_catalog = verify_scenarios_gate(scenarios_path, view)
        assert verified_catalog.dataset_hash == view.dataset_hash
        assert len(verified_catalog.scenarios) == 3

        # 3. Corrupted dataset_hash in file is rejected by gate
        tampered = catalog.to_dict()
        tampered["dataset_hash"] = "tampered_hash_abc"
        scenarios_path.write_text(json.dumps(tampered), encoding="utf-8")

        with pytest.raises(DataIntegrityError, match="dataset_hash mismatch"):
            verify_scenarios_gate(scenarios_path, view)


def test_xcut_02_runtime_purity_scenarios() -> None:
    """Verify XCUT-02: zero external runtime dependencies when importing features and stages."""
    script = (
        "import sys\n"
        "import experimental_ml.features as features\n"
        "import experimental_ml.stages as stages\n"
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
