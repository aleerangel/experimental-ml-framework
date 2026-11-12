"""Unit tests for single cell execution and anti-leakage isolation (M5.1).

Covers C10 to C18 (ORCH-05, ORCH-06).
"""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.core.enums import ExecutionStatus, MetricDirection, MetricStatus, TaskType
from experimental_ml.core.types import ExperimentId, ModelId, ObservationId, PartitionPlanId, ScenarioId
from experimental_ml.data import (
    ColumnSemanticType,
    DatasetBundle,
    DatasetSchemaSpec,
    PreparationPlan,
    SanitizedDatasetView,
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
    ScalerType,
    TwoLayerPreprocessingSpec,
    resolve_estimator_factory,
)
from experimental_ml.models.preprocessing import PreprocessingStepSpec
from experimental_ml.orchestration.execution import execute_single_cell
from experimental_ml.orchestration.types import CellId, ErrorPolicy, ExecutionStatus
from experimental_ml.tuning.types import HyperparameterSearchSpec, SearchStrategy
from experimental_ml.validation.types import EvaluationRegime, FoldPartition, PartitionConfig, PartitionPlan, PartitionStrategy


def _create_synthetic_environment() -> tuple[SanitizedDatasetView, PartitionPlan, FeatureScenario, ModelSpec]:
    """Create a fully validated synthetic environment for cell execution testing."""
    schema = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        column_semantic_types={
            "f1": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "f2": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "y": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
    )
    raw_data = {
        "f1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "f2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "y": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
    }
    bundle = load_dataset(raw_data, schema)
    profile = profile_dataset(bundle)
    plan = create_preparation_plan(profile, rules=[])
    view = sanitize_dataset(bundle, profile, plan)

    # 2 folds: 0 -> train: 0..3, val: 4..5; 1 -> train: 2..5, val: 0..1
    all_obs = view.observation_ids
    f0 = FoldPartition(
        fold_index=0,
        train_ids=all_obs[:4],
        val_ids=all_obs[4:],
    )
    f1 = FoldPartition(
        fold_index=1,
        train_ids=all_obs[2:],
        val_ids=all_obs[:2],
    )
    p_config = PartitionConfig(
        strategy=PartitionStrategy.KFOLD,
        regime=EvaluationRegime.CV_ONLY,
        n_splits=2,
    )
    part_plan = PartitionPlan(
        plan_id="plan_synthetic",
        source_dataset_hash=view.dataset_hash,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=all_obs,
        holdout_ids=(),
        folds=(f0, f1),
        config=p_config,
    )

    scenario = FeatureScenario(
        scenario_id=ScenarioId("sc_fixed"),
        name="Fixed Scenario",
        description="All features fixed",
        scientific_justification="Baseline feature set",
        mode=ScenarioMode.FIXED,
        selected_features=("f1", "f2"),
    )

    spec = ModelSpec(
        model_id=ModelId("baseline_mean"),
        display_name="Dummy Mean",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Dummy mean baseline",
        scientific_justification="Reference baseline",
    )

    return view, part_plan, scenario, spec


def test_m51_02_01_fold_slicing() -> None:
    """C10: execute_single_cell slices train and val sets by fold IDs (ORCH-05, AC 1)."""
    view, part_plan, scenario, model_spec = _create_synthetic_environment()
    fold = part_plan.folds[0]

    cell_result, pred_record = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("mae", "rmse"),
    )

    assert cell_result.status == ExecutionStatus.COMPLETED
    assert pred_record is not None
    # val_ids has 2 samples (index 4 and 5)
    assert len(pred_record.observation_ids) == 2
    assert pred_record.observation_ids == fold.val_ids
    assert pred_record.y_true == (500.0, 600.0)


def test_m51_02_02_feature_selection_isolation() -> None:
    """C11: select_features_in_fold on train and project val without y_val (ORCH-05, AC 2)."""
    view, part_plan, _, model_spec = _create_synthetic_environment()
    fold = part_plan.folds[0]

    dyn_scenario = FeatureScenario(
        scenario_id=ScenarioId("sc_dyn"),
        name="Dynamic Top 1",
        description="Select top 1 by relevance",
        scientific_justification="Feature ranking",
        mode=ScenarioMode.DYNAMIC,
        strategy_name="TOP_K_RELEVANCE",
        strategy_params={"k": 1, "score_func": "pearson"},
    )

    cell_result, pred_record = execute_single_cell(
        model_spec=model_spec,
        scenario=dyn_scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
    )

    assert cell_result.status == ExecutionStatus.COMPLETED
    assert len(cell_result.selected_features) == 1
    assert cell_result.selected_features in (("f1",), ("f2",))


def test_m51_02_03_nested_tuning_integration() -> None:
    """C12: run_nested_tuning on train data and apply theta* (ORCH-05, AC 3)."""
    view, part_plan, scenario, _ = _create_synthetic_environment()
    fold = part_plan.folds[0]

    search_spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.FIXED,
        param_grid={"dummy_param": (1.0, 2.0)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=2,
        seed=42,
    )

    tuned_spec = ModelSpec(
        model_id=ModelId("baseline_mean_tuned"),
        display_name="Tuned Mean",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Tuned mean",
        scientific_justification="Tuning test",
        search_spec=search_spec,
    )

    cell_result, pred_record = execute_single_cell(
        model_spec=tuned_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
    )

    assert cell_result.status == ExecutionStatus.COMPLETED
    assert cell_result.timing.tuning_time_s >= 0.0


def test_m51_02_04_two_layer_preprocessing_isolation() -> None:
    """C13: fit_two_layer_preprocessing on train and project val (ORCH-05, AC 4)."""
    view, part_plan, scenario, _ = _create_synthetic_environment()
    fold = part_plan.folds[0]

    prep_spec = TwoLayerPreprocessingSpec(
        layer2_steps=(
            PreprocessingStepSpec(
                step_id="std",
                transformer_type=ScalerType.STANDARD.value,
            ),
        ),
    )

    spec_with_prep = ModelSpec(
        model_id=ModelId("mean_with_prep"),
        display_name="Mean with Prep",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Mean with standard scaler",
        scientific_justification="Preprocessing test",
        preprocessing=prep_spec,
    )

    cell_result, pred_record = execute_single_cell(
        model_spec=spec_with_prep,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
    )

    assert cell_result.status == ExecutionStatus.COMPLETED
    assert cell_result.timing.preprocessing_time_s >= 0.0


def test_m51_02_05_fresh_model_seed() -> None:
    """C14: instantiate_fresh_model with deterministic cell seed (ORCH-06, AC 1)."""
    view, part_plan, scenario, model_spec = _create_synthetic_environment()
    fold = part_plan.folds[0]

    cell_res_1, _ = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
        cell_seed=42,
    )

    cell_res_2, _ = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
        cell_seed=42,
    )

    # Determinism across separate executions
    assert cell_res_1.metrics["rmse"].value == cell_res_2.metrics["rmse"].value


def test_m51_02_06_fit_predict_diagnostics() -> None:
    """C15: fit_model on train, predict_model on val, extract diagnostics (ORCH-06, AC 2)."""
    view, part_plan, scenario, model_spec = _create_synthetic_environment()
    fold = part_plan.folds[0]

    cell_result, pred_record = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("mae", "rmse"),
    )

    assert cell_result.status == ExecutionStatus.COMPLETED
    assert cell_result.diagnostics is not None
    assert cell_result.diagnostics.model_id == ModelId("baseline_mean")
    assert cell_result.timing.fit_time_s >= 0.0
    assert cell_result.timing.predict_time_s >= 0.0


def test_m51_02_07_metric_evaluation_nan() -> None:
    """C16: compute_metric evaluates all metrics preserving UNDEFINED_NAN (ORCH-06, AC 3)."""
    view, part_plan, scenario, model_spec = _create_synthetic_environment()
    fold = part_plan.folds[0]

    # Evaluate pearson (degenerate if constant predictions) and rmse
    cell_result, _ = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse", "pearson"),
    )

    assert "rmse" in cell_result.metrics
    assert "pearson" in cell_result.metrics
    # Dummy mean baseline produces constant prediction -> pearson is UNDEFINED_NAN
    assert cell_result.metrics["pearson"].status == MetricStatus.UNDEFINED_NAN


def test_m51_02_08_successful_cell_result() -> None:
    """C17: execute_single_cell returns CellResultRecord COMPLETED and PredictionRecord (ORCH-06, AC 4)."""
    view, part_plan, scenario, model_spec = _create_synthetic_environment()
    fold = part_plan.folds[0]

    cell_result, pred_record = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
    )

    assert cell_result.status == ExecutionStatus.COMPLETED
    assert pred_record is not None
    assert len(pred_record.y_pred) == len(fold.val_ids)
    assert cell_result.timing.total_cell_time_s >= 0.0


def test_m51_02_09_anti_leakage_adversarial() -> None:
    """C18: Perturbed y_val leaves fitted parameters bit-for-bit unchanged (ORCH-06, AC 5)."""
    view, part_plan, scenario, model_spec = _create_synthetic_environment()
    fold = part_plan.folds[0]

    # Run on clean environment
    cell_res_clean, pred_clean = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
        cell_seed=123,
    )

    # Create perturbed view where validation y is multiplied by 1000
    perturbed_cols = dict(view.columns)
    perturbed_y = np.copy(perturbed_cols["y"])
    val_indices = [i for i, obs in enumerate(view.observation_ids) if obs in fold.val_ids]
    perturbed_y[val_indices] *= 1000.0
    perturbed_y.flags.writeable = False
    perturbed_cols["y"] = perturbed_y

    perturbed_view = SanitizedDatasetView(
        columns=perturbed_cols,
        schema=view.schema,
        observation_ids=view.observation_ids,
        candidate_feature_cols=view.candidate_feature_cols,
        dropped_observation_ids=view.dropped_observation_ids,
        target_label_mapping=view.target_label_mapping,
        deferred_rules=view.deferred_rules,
        source_dataset_hash=view.source_dataset_hash,
        source_plan_digest=view.source_plan_digest,
        dataset_hash="perturbed_hash",
    )

    cell_res_pert, pred_pert = execute_single_cell(
        model_spec=model_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=perturbed_view,
        partition_plan=part_plan,
        metrics=("rmse",),
        cell_seed=123,
    )

    # In Dummy Mean baseline, mean is fitted purely on X_train, y_train.
    # Therefore, y_pred on validation must be 100% bit-for-bit identical regardless of y_val perturbation!
    assert pred_clean is not None and pred_pert is not None
    assert pred_clean.y_pred == pred_pert.y_pred
    assert cell_res_clean.selected_features == cell_res_pert.selected_features
