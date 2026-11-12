"""Pure functional cell executor and anti-leakage isolation pipeline (Stage 4B).

Complies with ORCH-05, ORCH-06, ORCH-07, CA-E4B-01, CA-E4B-02, and ADR-002.
"""

from __future__ import annotations

import time
import traceback
from typing import Sequence

import numpy as np

from experimental_ml.core.enums import ExecutionStatus, TaskType
from experimental_ml.core.types import ExperimentId, ModelId, PartitionPlanId, ScenarioId
from experimental_ml.data.preparation import SanitizedDatasetView
from experimental_ml.data.query import slice_view_by_observation_ids
from experimental_ml.features.scenarios import FeatureScenario
from experimental_ml.features.selection import apply_feature_selection, select_features_in_fold
from experimental_ml.metrics.catalog import compute_metric
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue
from experimental_ml.models.execution import (
    extract_model_diagnostics,
    fit_model,
    instantiate_fresh_model,
    predict_model,
)
from experimental_ml.models.preprocessing.pipeline import (
    apply_two_layer_preprocessing,
    fit_two_layer_preprocessing,
)
from experimental_ml.models.spec import ModelSpec
from experimental_ml.orchestration.types import (
    CellId,
    CellPhase,
    CellResultRecord,
    ErrorPolicy,
    PredictionRecord,
    TimingBreakdown,
)
from experimental_ml.tuning.engine import run_nested_tuning
from experimental_ml.tuning.types import SearchStrategy
from experimental_ml.validation.types import FoldPartition, PartitionPlan


def execute_single_cell(
    model_spec: ModelSpec,
    scenario: FeatureScenario,
    fold: FoldPartition,
    sanitized_view: SanitizedDatasetView,
    partition_plan: PartitionPlan,
    metrics: Sequence[str] = (),
    error_policy: ErrorPolicy = ErrorPolicy.FAULT_TOLERANT,
    cell_seed: int | None = None,
    cell_id: CellId | None = None,
) -> tuple[CellResultRecord, PredictionRecord | None]:
    """Execute a single experimental cell (m, c, f) under strict anti-leakage isolation.

    Coordinating sequential fold slicing, feature selection, nested tuning, two-layer
    preprocessing, fresh model fitting, inference, and metric computation.

    Args:
        model_spec: Declarative specification of the model.
        scenario: Feature scenario defining fixed or dynamic predictors.
        fold: Target fold partition containing train and val observation IDs.
        sanitized_view: Pre-partition sanitized dataset view.
        partition_plan: Immutable partition plan.
        metrics: Sequence of metric names to evaluate on validation data.
        error_policy: FAULT_TOLERANT (catches exceptions and marks FAILED) or FAIL_FAST.
        cell_seed: Deterministic random seed derived for this cell.
        cell_id: Optional explicit CellId for the cell.

    Returns:
        Tuple of (CellResultRecord, PredictionRecord | None).

    Raises:
        Exception: If error_policy is FAIL_FAST and an exception occurs.
    """
    fold_id = getattr(fold, "fold_id", None) or f"fold_{getattr(fold, 'fold_index', 0)}"
    plan_id = getattr(partition_plan, "partition_plan_id", None) or getattr(partition_plan, "plan_id", "default_plan")
    if cell_id is None:
        cell_id = CellId(f"cell_{model_spec.model_id}__{scenario.scenario_id}__{fold_id}")
    else:
        cell_id = CellId(str(cell_id))
    t_total_start = time.perf_counter()
    current_phase = CellPhase.DATA_EXTRACTION

    t_data = 0.0
    t_fs = 0.0
    t_tune = 0.0
    t_prep = 0.0
    t_fit = 0.0
    t_pred = 0.0
    t_eval = 0.0

    selected_features_tuple: tuple[str, ...] = ()
    effective_spec = model_spec

    try:
        # 1. DATA_EXTRACTION: Slice training and validation subsets from SanitizedDatasetView
        current_phase = CellPhase.DATA_EXTRACTION
        t_phase_start = time.perf_counter()

        train_view = slice_view_by_observation_ids(sanitized_view, fold.train_ids)
        val_view = slice_view_by_observation_ids(sanitized_view, fold.val_ids)

        target_col = sanitized_view.schema.target_col
        y_train = np.asarray(train_view.columns[target_col])
        y_val = np.asarray(val_view.columns[target_col])

        t_data = time.perf_counter() - t_phase_start

        # 2. FEATURE_SELECTION: Select features on training fold and project validation fold
        current_phase = CellPhase.FEATURE_SELECTION
        t_phase_start = time.perf_counter()

        X_train_cand = {col: train_view.columns[col] for col in train_view.candidate_feature_cols}
        X_val_cand = {col: val_view.columns[col] for col in val_view.candidate_feature_cols}

        selection_res = select_features_in_fold(
            X_train=X_train_cand,
            y_train=y_train,
            scenario=scenario,
            random_state=cell_seed,
        )
        selected_features_tuple = tuple(selection_res.selected_features)

        X_train_sel = apply_feature_selection(X_train_cand, selection_res)
        X_val_sel = apply_feature_selection(X_val_cand, selection_res)

        X_train_matrix = np.column_stack([X_train_sel[col] for col in selected_features_tuple])
        X_val_matrix = np.column_stack([X_val_sel[col] for col in selected_features_tuple])

        t_fs = time.perf_counter() - t_phase_start

        # 3. HYPERPARAMETER_TUNING: Nested CV on training fold only if search_spec is active
        current_phase = CellPhase.HYPERPARAMETER_TUNING
        t_phase_start = time.perf_counter()

        if model_spec.search_spec is not None:
            tuning_res = run_nested_tuning(
                spec=model_spec.search_spec,
                model_spec=model_spec,
                X_train=X_train_matrix,
                y_train=y_train,
                seed=cell_seed,
            )
            merged_params = dict(model_spec.parameters)
            merged_params.update(tuning_res.best_params)

            effective_spec = ModelSpec(
                model_id=model_spec.model_id,
                display_name=model_spec.display_name,
                family=model_spec.family,
                estimator_factory=model_spec.estimator_factory,
                capabilities=model_spec.capabilities,
                description=model_spec.description,
                scientific_justification=model_spec.scientific_justification,
                parameters=merged_params,
                random_seed_policy=model_spec.random_seed_policy,
                preprocessing=model_spec.preprocessing,
                search_spec=None,
            )

        t_tune = time.perf_counter() - t_phase_start

        # 4. PREPROCESSING_L2: Two-layer preprocessing fit on train and project validation
        current_phase = CellPhase.PREPROCESSING_L2
        t_phase_start = time.perf_counter()

        if effective_spec.preprocessing is not None:
            prep_state = fit_two_layer_preprocessing(effective_spec.preprocessing, X_train_matrix)
            X_train_proc = apply_two_layer_preprocessing(prep_state, X_train_matrix)
            X_val_proc = apply_two_layer_preprocessing(prep_state, X_val_matrix)
        else:
            X_train_proc = X_train_matrix
            X_val_proc = X_val_matrix

        t_prep = time.perf_counter() - t_phase_start

        # 5. MODEL_FIT: Instantiate fresh estimator and fit on transformed training data
        current_phase = CellPhase.MODEL_FIT
        t_phase_start = time.perf_counter()

        model_instance = instantiate_fresh_model(effective_spec, seed=cell_seed)
        fitted_model, fit_diag = fit_model(model_instance, effective_spec, X_train_proc, y_train)

        t_fit = time.perf_counter() - t_phase_start

        # 6. PREDICTION: Infer on transformed validation data and extract diagnostics
        current_phase = CellPhase.PREDICTION
        t_phase_start = time.perf_counter()

        pred_outputs = predict_model(fitted_model, effective_spec, X_val_proc)
        diagnostics = extract_model_diagnostics(fitted_model, effective_spec, "predict")

        t_pred = time.perf_counter() - t_phase_start

        # 7. METRIC_COMPUTATION: Evaluate metrics comparing y_val with predictions
        current_phase = CellPhase.METRIC_COMPUTATION
        t_phase_start = time.perf_counter()

        y_pred = np.asarray(pred_outputs["y_pred"])
        computed_metrics: dict[str, MetricValue] = {}
        for metric_name in metrics:
            m_val = compute_metric(
                metric_name,
                y_val,
                y_pred,
                scope=MetricEvaluationScope.PER_FOLD,
            )
            computed_metrics[metric_name] = m_val

        residuals: tuple[float, ...] | None = None
        if sanitized_view.schema.task_type == TaskType.REGRESSION:
            residuals = tuple(float(yt - yp) for yt, yp in zip(y_val, y_pred))

        t_eval = time.perf_counter() - t_phase_start
        t_total = time.perf_counter() - t_total_start

        timing = TimingBreakdown(
            data_extraction_time_s=t_data,
            feature_selection_time_s=t_fs,
            tuning_time_s=t_tune,
            preprocessing_time_s=t_prep,
            fit_time_s=t_fit,
            predict_time_s=t_pred,
            evaluation_time_s=t_eval,
            total_cell_time_s=t_total,
        )

        y_std_tuple: tuple[float, ...] | None = None
        if pred_outputs.get("y_std") is not None:
            y_std_tuple = tuple(float(s) for s in pred_outputs["y_std"])

        y_proba_tuple: tuple[tuple[float, ...], ...] | None = None
        if pred_outputs.get("y_proba") is not None:
            y_proba_tuple = tuple(tuple(float(p) for p in row) for row in pred_outputs["y_proba"])

        pred_record = PredictionRecord(
            cell_id=cell_id,
            observation_ids=tuple(val_view.observation_ids),
            y_true=tuple(float(v) for v in y_val),
            y_pred=tuple(float(v) for v in y_pred),
            y_std=y_std_tuple,
            y_proba=y_proba_tuple,
            residuals=residuals,
        )

        cell_result = CellResultRecord(
            cell_id=cell_id,
            experiment_id=ExperimentId(str(plan_id)),
            partition_plan_id=PartitionPlanId(str(plan_id)),
            model_id=ModelId(str(model_spec.model_id)),
            scenario_id=ScenarioId(str(scenario.scenario_id)),
            fold_id=str(fold_id),
            status=ExecutionStatus.COMPLETED,
            selected_features=selected_features_tuple,
            effective_parameters=effective_spec.parameters,
            timing=timing,
            metrics=computed_metrics,
            diagnostics=diagnostics,
        )

        return cell_result, pred_record

    except Exception as exc:
        if error_policy == ErrorPolicy.FAIL_FAST:
            raise

        t_total = time.perf_counter() - t_total_start
        timing = TimingBreakdown(
            data_extraction_time_s=t_data,
            feature_selection_time_s=t_fs,
            tuning_time_s=t_tune,
            preprocessing_time_s=t_prep,
            fit_time_s=t_fit,
            predict_time_s=t_pred,
            evaluation_time_s=t_eval,
            total_cell_time_s=t_total,
        )

        err_type = type(exc).__name__
        err_msg = str(exc)
        err_tb = traceback.format_exc()

        cell_result = CellResultRecord(
            cell_id=cell_id,
            experiment_id=ExperimentId(str(plan_id)),
            partition_plan_id=PartitionPlanId(str(plan_id)),
            model_id=ModelId(str(model_spec.model_id)),
            scenario_id=ScenarioId(str(scenario.scenario_id)),
            fold_id=str(fold_id),
            status=ExecutionStatus.FAILED,
            selected_features=selected_features_tuple,
            effective_parameters=effective_spec.parameters,
            timing=timing,
            metrics={},
            diagnostics=None,
            error_type=err_type,
            error_message=err_msg,
            error_phase=current_phase,
            error_traceback=err_tb,
        )

        return cell_result, None
