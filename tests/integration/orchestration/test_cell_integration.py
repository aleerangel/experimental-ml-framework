"""Transversal integration tests for single-cell execution and orchestration (M5.1).

Covers C17, C18, and XCUT-02.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experimental_ml.core.enums import ExecutionStatus, MetricDirection, MetricStatus, TaskType
from experimental_ml.core.types import (
    ModelId,
    ObservationId,
    PartitionPlanId,
    ScenarioId,
)
from experimental_ml.data import (
    ColumnSemanticType,
    DatasetSchemaSpec,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features.scenarios import FeatureScenario, ScenarioMode
from experimental_ml.models import (
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    resolve_estimator_factory,
)
from experimental_ml.models.preprocessing.pipeline import (
    PreprocessingStepSpec,
    TwoLayerPreprocessingSpec,
)
from experimental_ml.orchestration import (
    CellId,
    CellPhase,
    CellResultRecord,
    ErrorPolicy,
    PredictionRecord,
    execute_single_cell,
    load_cell_artifacts,
    save_cell_artifacts,
)
from experimental_ml.tuning.types import (
    HyperparameterSearchSpec,
    SearchStrategy,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _build_synthetic_dataset_and_plan():
    """Create a multi-sample dataset and partition plan for integration testing."""
    rng = np.random.RandomState(42)
    n_samples = 40

    x1 = rng.uniform(0.0, 10.0, size=n_samples)
    x2 = rng.uniform(-5.0, 5.0, size=n_samples)
    x_noise = rng.normal(0.0, 1.0, size=n_samples)
    y = 3.0 * x1 - 2.0 * x2 + 10.0 + rng.normal(0.0, 0.1, size=n_samples)

    raw_data = {
        "x1": x1.tolist(),
        "x2": x2.tolist(),
        "x_noise": x_noise.tolist(),
        "target": y.tolist(),
    }
    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.REGRESSION,
        column_semantic_types={
            "x1": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "x2": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "x_noise": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "target": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
    )
    bundle = load_dataset(raw_data, schema)
    profile = profile_dataset(bundle)
    plan_prep = create_preparation_plan(profile, rules=[])
    view = sanitize_dataset(bundle, profile, plan_prep)

    obs_ids = view.observation_ids
    train_obs = obs_ids[:30]
    val_obs = obs_ids[30:]

    fold = FoldPartition(fold_index=0, train_ids=train_obs, val_ids=val_obs)
    partition_plan = PartitionPlan(
        plan_id=PartitionPlanId("plan_integration"),
        source_dataset_hash=view.dataset_hash,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=obs_ids,
        holdout_ids=(),
        folds=(fold,),
        config=PartitionConfig(
            strategy=PartitionStrategy.KFOLD,
            regime=EvaluationRegime.CV_ONLY,
            n_splits=2,
            master_seed=42,
        ),
    )
    return view, partition_plan, fold


def test_m51_02_08_end_to_end_cell_lifecycle(tmp_path: Path):
    """C17: execute_single_cell returns CellResultRecord COMPLETED and PredictionRecord.

    Tests the complete end-to-end cell lifecycle:
    - Feature selection with SelectKBest
    - Nested hyperparameter tuning
    - Two-layer preprocessing (standard scaler)
    - Fresh model instantiation, fitting, predicting
    - Metric evaluation and timing
    - Atomic save and reload verification
    """
    view, partition_plan, fold = _build_synthetic_dataset_and_plan()

    scenario = FeatureScenario(
        scenario_id=ScenarioId("fs_k2"),
        name="Select K Best Scenario",
        description="Top 2 features via pearson correlation",
        scientific_justification="Linear correlation filtering",
        mode=ScenarioMode.DYNAMIC,
        strategy_name="TOP_K_RELEVANCE",
        strategy_params={"k": 2, "score_func": "pearson"},
    )

    search_spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"dummy_param": (1.0, 2.0)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=2,
        seed=42,
    )

    preprocessing_spec = TwoLayerPreprocessingSpec(
        layer2_steps=(
            PreprocessingStepSpec(step_id="scaler", transformer_type="STANDARD"),
        )
    )

    model_spec = ModelSpec(
        model_id=ModelId("baseline_mean_full"),
        display_name="Baseline Mean Full Lifecycle",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Dummy mean baseline for lifecycle test",
        scientific_justification="Lifecycle integration testing",
        preprocessing=preprocessing_spec,
        search_spec=search_spec,
    )

    cell_result, pred_record = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=partition_plan,
        metrics=("rmse", "mae"),
        error_policy=ErrorPolicy.FAULT_TOLERANT,
        cell_seed=42,
    )

    # Assertions on cell result
    assert isinstance(cell_result, CellResultRecord)
    assert cell_result.status == ExecutionStatus.COMPLETED
    assert cell_result.error_phase is None
    assert cell_result.error_type is None
    assert cell_result.error_message is None
    assert cell_result.fold_id == "fold_0"
    assert cell_result.selected_features == ("x1", "x2")  # noise dropped
    assert "dummy_param" in cell_result.effective_parameters

    # Metrics evaluation
    assert "rmse" in cell_result.metrics
    assert "mae" in cell_result.metrics
    assert cell_result.metrics["rmse"].status == MetricStatus.VALID

    # Timing
    timing = cell_result.timing
    assert timing.total_cell_time_s > 0.0
    assert timing.fit_time_s >= 0.0
    assert timing.predict_time_s >= 0.0
    assert timing.tuning_time_s >= 0.0
    assert timing.preprocessing_time_s >= 0.0

    # Prediction record
    assert pred_record is not None
    assert isinstance(pred_record, PredictionRecord)
    assert len(pred_record.observation_ids) == len(fold.val_ids)
    assert len(pred_record.y_pred) == len(fold.val_ids)
    assert pred_record.residuals is not None

    # Atomic persistence and roundtrip reload
    cell_file, pred_file = save_cell_artifacts(cell_result, pred_record, tmp_path)
    assert cell_file.exists()
    assert pred_file is not None and pred_file.exists()

    reloaded_result, reloaded_pred = load_cell_artifacts(cell_result.cell_id, tmp_path)
    assert reloaded_result.cell_id == cell_result.cell_id
    assert reloaded_result.status == ExecutionStatus.COMPLETED
    assert reloaded_result.selected_features == cell_result.selected_features
    assert reloaded_pred is not None
    assert reloaded_pred.observation_ids == pred_record.observation_ids
    np.testing.assert_allclose(reloaded_pred.y_pred, pred_record.y_pred)


def test_m51_02_09_anti_leakage_adversarial():
    """C18: Perturbed y_val leaves fitted parameters bit-for-bit unchanged.

    Adversarial validation:
    1. Run cell execution on clean dataset.
    2. Run cell execution on adversarial dataset where val rows have radical values.
    3. Verify that feature selection, tuning choice, and effective parameters
       are 100% bit-for-bit identical, demonstrating zero validation leakage into training.
    """
    view, partition_plan, fold = _build_synthetic_dataset_and_plan()

    scenario = FeatureScenario(
        scenario_id=ScenarioId("fs_k2_adv"),
        name="Select K Best Adv",
        description="Top 2 features via pearson correlation",
        scientific_justification="Adversarial validation test",
        mode=ScenarioMode.DYNAMIC,
        strategy_name="TOP_K_RELEVANCE",
        strategy_params={"k": 2, "score_func": "pearson"},
    )

    search_spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"dummy_param": (10.0, 20.0)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=2,
        seed=100,
    )

    preprocessing_spec = TwoLayerPreprocessingSpec(
        layer2_steps=(
            PreprocessingStepSpec(step_id="scaler", transformer_type="STANDARD"),
        )
    )

    model_spec = ModelSpec(
        model_id=ModelId("baseline_mean_adv"),
        display_name="Baseline Mean Adv",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Dummy mean baseline for adversarial test",
        scientific_justification="Adversarial anti-leakage test",
        preprocessing=preprocessing_spec,
        search_spec=search_spec,
    )

    # 1. Clean run
    clean_result, clean_pred = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=partition_plan,
        metrics=("rmse",),
        cell_seed=12345,
    )

    # 2. Adversarial run: build a dataset where val rows have radical values
    val_set = set(fold.val_ids)
    corrupted_data = {}
    for col_name, original_vals in view.columns.items():
        new_vals = []
        for oid, val in zip(view.observation_ids, original_vals):
            if oid in val_set:
                if col_name == "target":
                    new_vals.append(float(val) * 1_000_000.0 + 999_999.0)
                else:
                    new_vals.append(float(val) + 500.0)
            else:
                new_vals.append(float(val))
        corrupted_data[col_name] = new_vals

    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.REGRESSION,
        column_semantic_types={
            "x1": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "x2": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "x_noise": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "target": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
    )
    bundle_adv = load_dataset(corrupted_data, schema)
    profile_adv = profile_dataset(bundle_adv)
    plan_adv = create_preparation_plan(profile_adv, rules=[])
    view_adv = sanitize_dataset(bundle_adv, profile_adv, plan_adv)

    adv_result, adv_pred = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view_adv,
        partition_plan=partition_plan,
        metrics=("rmse",),
        cell_seed=12345,
    )

    # Selected features must be bit-for-bit identical
    assert adv_result.selected_features == clean_result.selected_features
    # Tuned hyperparameters must be bit-for-bit identical
    assert adv_result.effective_parameters == clean_result.effective_parameters
    # Status and diagnostics
    assert adv_result.status == ExecutionStatus.COMPLETED
    assert clean_result.status == ExecutionStatus.COMPLETED


def test_orchestration_runtime_purity_xcut_02():
    """Verify single runtime dependency numpy>=1.24.0 without third-party ML frameworks (XCUT-02)."""
    code = (
        "import sys\n"
        "import experimental_ml.orchestration\n"
        "forbidden = ['scipy', 'pandas', 'sklearn', 'torch', 'qiskit']\n"
        "loaded_forbidden = [pkg for pkg in forbidden if pkg in sys.modules]\n"
        "if loaded_forbidden:\n"
        "    print(f'FORBIDDEN_LOADED: {loaded_forbidden}', file=sys.stderr)\n"
        "    sys.exit(1)\n"
        "sys.exit(0)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"XCUT-02 violation: {result.stderr}"
