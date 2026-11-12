"""Unit tests for cell failure handling and error policies (M5.1).

Covers C19 to C24 (ORCH-07).
"""

from __future__ import annotations

import pytest

from experimental_ml.core.enums import ExecutionStatus, TaskType
from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.core.types import ModelId, PartitionPlanId, ScenarioId
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
from experimental_ml.orchestration.execution import execute_single_cell
from experimental_ml.orchestration.types import CellId, CellPhase, ErrorPolicy, ExecutionStatus
from experimental_ml.validation.types import EvaluationRegime, FoldPartition, PartitionConfig, PartitionPlan, PartitionStrategy


def _create_synthetic_environment():
    schema = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        column_semantic_types={
            "f1": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "y": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
    )
    raw_data = {
        "f1": [1.0, 2.0, 3.0, 4.0],
        "y": [10.0, 20.0, 30.0, 40.0],
    }
    bundle = load_dataset(raw_data, schema)
    profile = profile_dataset(bundle)
    plan = create_preparation_plan(profile, rules=[])
    view = sanitize_dataset(bundle, profile, plan)

    all_obs = view.observation_ids
    f0 = FoldPartition(
        fold_index=0,
        train_ids=all_obs[:2],
        val_ids=all_obs[2:],
    )
    p_config = PartitionConfig(
        strategy=PartitionStrategy.KFOLD,
        regime=EvaluationRegime.CV_ONLY,
        n_splits=2,
    )
    part_plan = PartitionPlan(
        plan_id="plan_fail_test",
        source_dataset_hash=view.dataset_hash,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=all_obs,
        holdout_ids=(),
        folds=(f0,),
        config=p_config,
    )

    scenario = FeatureScenario(
        scenario_id=ScenarioId("sc_valid"),
        name="Valid Scenario",
        description="Valid",
        scientific_justification="Valid",
        mode=ScenarioMode.FIXED,
        selected_features=("f1",),
    )

    return view, part_plan, scenario


def _failing_factory(seed: int | None = None):
    raise RuntimeError("Simulated failure in estimator factory")


def test_m51_03_01_fault_tolerant_catches_exception() -> None:
    """C19: FAULT_TOLERANT catches exceptions without aborting process (ORCH-07, AC 1)."""
    view, part_plan, scenario = _create_synthetic_environment()
    fold = part_plan.folds[0]

    failing_spec = ModelSpec(
        model_id=ModelId("failing_model"),
        display_name="Failing Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=_failing_factory,
        description="Always fails",
        scientific_justification="Failure testing",
    )

    # In FAULT_TOLERANT, does not raise
    cell_result, pred_record = execute_single_cell(
        model_spec=failing_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
        error_policy=ErrorPolicy.FAULT_TOLERANT,
    )

    assert cell_result is not None


def test_m51_03_02_status_failed() -> None:
    """C20: FAULT_TOLERANT sets status = FAILED (ORCH-07, AC 2)."""
    view, part_plan, scenario = _create_synthetic_environment()
    fold = part_plan.folds[0]

    failing_spec = ModelSpec(
        model_id=ModelId("failing_model"),
        display_name="Failing Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=_failing_factory,
        description="Always fails",
        scientific_justification="Failure testing",
    )

    cell_result, _ = execute_single_cell(
        model_spec=failing_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
        error_policy=ErrorPolicy.FAULT_TOLERANT,
    )

    assert cell_result.status == ExecutionStatus.FAILED


def test_m51_03_03_error_phase_recorded() -> None:
    """C21: FAULT_TOLERANT populates exact error_phase (ORCH-07, AC 3)."""
    view, part_plan, scenario = _create_synthetic_environment()
    fold = part_plan.folds[0]

    failing_spec = ModelSpec(
        model_id=ModelId("failing_model"),
        display_name="Failing Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=_failing_factory,
        description="Always fails in instantiate_fresh_model",
        scientific_justification="Failure testing",
    )

    cell_result, _ = execute_single_cell(
        model_spec=failing_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
        error_policy=ErrorPolicy.FAULT_TOLERANT,
    )

    assert cell_result.error_phase == CellPhase.MODEL_FIT


def test_m51_03_04_error_details_recorded() -> None:
    """C22: FAULT_TOLERANT populates error_type, message, and traceback (ORCH-07, AC 4)."""
    view, part_plan, scenario = _create_synthetic_environment()
    fold = part_plan.folds[0]

    failing_spec = ModelSpec(
        model_id=ModelId("failing_model"),
        display_name="Failing Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=_failing_factory,
        description="Always fails",
        scientific_justification="Failure testing",
    )

    cell_result, _ = execute_single_cell(
        model_spec=failing_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse",),
        error_policy=ErrorPolicy.FAULT_TOLERANT,
    )

    assert cell_result.error_type in ("RuntimeError", "ConfigurationError")
    assert "Simulated failure in estimator factory" in str(cell_result.error_message)
    assert cell_result.error_traceback is not None
    assert "Traceback" in cell_result.error_traceback


def test_m51_03_05_no_coercion_to_zero() -> None:
    """C23: FAULT_TOLERANT returns empty metrics and prediction_record = None (ORCH-07, AC 5)."""
    view, part_plan, scenario = _create_synthetic_environment()
    fold = part_plan.folds[0]

    failing_spec = ModelSpec(
        model_id=ModelId("failing_model"),
        display_name="Failing Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=_failing_factory,
        description="Always fails",
        scientific_justification="Failure testing",
    )

    cell_result, pred_record = execute_single_cell(
        model_spec=failing_spec,
        scenario=scenario,
        fold=fold,
        sanitized_view=view,
        partition_plan=part_plan,
        metrics=("rmse", "mae"),
        error_policy=ErrorPolicy.FAULT_TOLERANT,
    )

    # Empty metrics, never 0.0 or coerced values
    assert len(cell_result.metrics) == 0
    assert pred_record is None


def test_m51_03_06_fail_fast_propagates() -> None:
    """C24: FAIL_FAST propagates exception immediately (ORCH-07, AC 6)."""
    view, part_plan, scenario = _create_synthetic_environment()
    fold = part_plan.folds[0]

    failing_spec = ModelSpec(
        model_id=ModelId("failing_model"),
        display_name="Failing Model",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=_failing_factory,
        description="Always fails",
        scientific_justification="Failure testing",
    )

    # In FAIL_FAST, exception is propagated directly
    with pytest.raises((RuntimeError, ConfigurationError)):
        execute_single_cell(
            model_spec=failing_spec,
            scenario=scenario,
            fold=fold,
            sanitized_view=view,
            partition_plan=part_plan,
            metrics=("rmse",),
            error_policy=ErrorPolicy.FAIL_FAST,
        )
