"""Integration tests for M3.3 intra-fold feature selection, evaluation projection, and stability.

Complies with SEL-01 to SEL-08, XCUT-02, RF2.4, CA-E2-01, CA-E2-02, ADR-002, and ADR-008.
"""

from __future__ import annotations

import subprocess
import sys
import numpy as np
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    load_dataset,
    profile_dataset,
    create_preparation_plan,
    sanitize_dataset,
)
from experimental_ml.features import (
    FeatureScenario,
    ScenarioMode,
    apply_feature_selection,
    compute_selection_stability,
    select_features_in_fold,
)
from experimental_ml.validation import (
    PartitionConfig,
    build_partition_plan,
)


def test_sel_08_multi_fold_selection_pipeline() -> None:
    """Proof C8: Full multi-fold selection pipeline executed strictly on fold training data without leakage (SEL-01 to SEL-08)."""
    np.random.seed(999)
    n = 100
    x_base = np.linspace(0.0, 20.0, n)
    # Target continuous variable
    y = 2.5 * x_base + np.random.normal(0, 1.0, n)

    # 5 candidate features with varying degrees of correlation with y
    f1 = x_base + np.random.normal(0, 0.5, n)      # strong correlation
    f2 = 2.0 * x_base + np.random.normal(0, 1.0, n) # strong correlation
    f3 = -1.5 * x_base + np.random.normal(0, 2.0, n) # moderate negative correlation
    f4 = np.random.normal(0, 5.0, n)                 # pure noise
    f5 = np.sin(x_base * 3.0)                        # low correlation noise

    data = {
        "f1": f1,
        "f2": f2,
        "f3": f3,
        "f4": f4,
        "f5": f5,
        "target": y,
    }

    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.REGRESSION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)
    plan = create_preparation_plan(profile, [])
    view = sanitize_dataset(bundle, profile, plan)

    # Generate 5-fold cross-validation partition plan
    part_config = PartitionConfig(
        strategy="KFOLD",
        regime="CV_ONLY",
        n_splits=5,
        master_seed=42,
    )
    part_plan = build_partition_plan(bundle, part_config)
    assert len(part_plan.folds) == 5

    # Define dynamic scenario: Top 3 features by relevance
    scenario = FeatureScenario(
        scenario_id="dyn_top_3",
        name="Top 3 Features",
        description="Selects top 3 features within each fold",
        scientific_justification="Leakage-free feature selection baseline",
        mode=ScenarioMode.DYNAMIC,
        strategy_name="TOP_K_RELEVANCE",
        strategy_params={"k": 3},
    )

    # Track selections across folds
    fold_selections = []

    # Map observation_ids to integer indices for array slicing
    obs_id_to_idx = {oid: idx for idx, oid in enumerate(view.observation_ids)}

    for fold in part_plan.folds:
        train_indices = np.array([obs_id_to_idx[oid] for oid in fold.train_ids])
        val_indices = np.array([obs_id_to_idx[oid] for oid in fold.val_ids])

        # Slice fold data strictly
        X_train = {feat: view.columns[feat][train_indices] for feat in view.candidate_feature_cols}
        y_train = view.columns["target"][train_indices]

        X_val = {feat: view.columns[feat][val_indices] for feat in view.candidate_feature_cols}

        # 1. Select features strictly on training split
        selection_res = select_features_in_fold(X_train, y_train, scenario)
        assert len(selection_res.selected_features) == 3
        # Strongest predictors f1 and f2 should always be selected in every fold
        assert "f1" in selection_res.selected_features
        assert "f2" in selection_res.selected_features

        # 2. Project selection onto evaluation set
        X_val_selected = apply_feature_selection(X_val, selection_res)
        assert list(X_val_selected.keys()) == list(selection_res.selected_features)
        assert len(X_val_selected["f1"]) == len(val_indices)

        fold_selections.append(selection_res.selected_features)

    # 3. Compute selection stability across the 5 folds
    stability = compute_selection_stability(fold_selections, n_total_candidates=len(view.candidate_feature_cols))

    assert stability.n_folds == 5
    assert stability.n_total_candidates == 5
    # Since f1 and f2 are consistently selected, Jaccard and Kuncheva stability must be high
    assert stability.mean_jaccard >= 0.70
    assert stability.mean_kuncheva >= 0.50
    assert stability.pairwise_jaccard["fold_0"]["fold_0"] == 1.0


def test_xcut_02_runtime_purity_selection() -> None:
    """Verify XCUT-02: zero external runtime dependencies when importing features selection and stability."""
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
