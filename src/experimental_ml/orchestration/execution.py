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


def resolve_deferred_preprocessing(
    model_spec: ModelSpec,
    deferred_rules: tuple[Any, ...],
) -> ModelSpec:
    """Inject Stage 1 DEFER_INTRA_FOLD rules into ModelSpec.preprocessing when not overridden (AD-031)."""
    if not deferred_rules:
        return model_spec

    from experimental_ml.models.preprocessing.types import (
        PreprocessingStepSpec,
        TwoLayerPreprocessingSpec,
    )

    existing_l1 = list(model_spec.preprocessing.layer1_steps) if model_spec.preprocessing else []
    existing_l2 = list(model_spec.preprocessing.layer2_steps) if model_spec.preprocessing else []
    existing_l1_types = {s.transformer_type.upper().strip() for s in existing_l1}
    scaler_types = {"STANDARD", "MINMAX", "MAXABS", "ROBUST", "ANGULAR"}
    has_l2_scaler = any(s.transformer_type.upper().strip() in scaler_types for s in existing_l2)

    injected_encoders: list[PreprocessingStepSpec] = []
    injected_imputers: list[PreprocessingStepSpec] = []
    injected_scalers: list[PreprocessingStepSpec] = []
    seen_steps: set[tuple[str, str]] = set()

    for rule in deferred_rules:
        code = str(getattr(rule, "finding_code", ""))
        params = getattr(rule, "parameters", {}) or {}
        if code == "E1_CATEGORICAL_UNENCODED":
            if not (existing_l1_types & {"ORDINAL_ENCODER", "FREQUENCY_ENCODER"}):
                raw_enc = str(params.get("encoding_strategy", "ORDINAL_ENCODER")).upper().strip()
                ttype = "FREQUENCY_ENCODER" if "FREQ" in raw_enc else "ORDINAL_ENCODER"
                if (ttype, "") not in seen_steps:
                    seen_steps.add((ttype, ""))
                    injected_encoders.append(
                        PreprocessingStepSpec(
                            step_id=f"deferred_{ttype.lower()}",
                            transformer_type=ttype,
                        )
                    )
        elif code == "E1_FEATURE_MISSING":
            if "IMPUTER" not in existing_l1_types:
                strat = str(params.get("imputation_strategy", "MEDIAN")).upper().strip()
                if ("IMPUTER", strat) not in seen_steps:
                    seen_steps.add(("IMPUTER", strat))
                    injected_imputers.append(
                        PreprocessingStepSpec(
                            step_id=f"deferred_imputer_{strat.lower()}",
                            transformer_type="IMPUTER",
                            parameters={"strategy": strat},
                        )
                    )
        elif code == "E1_SCALE_DISPARITY":
            if not has_l2_scaler:
                strat = str(params.get("scaling_strategy", "STANDARD")).upper().strip()
                if strat in scaler_types and ("SCALER", strat) not in seen_steps:
                    seen_steps.add(("SCALER", strat))
                    injected_scalers.append(
                        PreprocessingStepSpec(
                            step_id=f"deferred_scaler_{strat.lower()}",
                            transformer_type=strat,
                        )
                    )

    if not (injected_encoders or injected_imputers or injected_scalers):
        return model_spec

    new_prep = TwoLayerPreprocessingSpec(
        layer1_steps=tuple(injected_encoders + injected_imputers + existing_l1),
        layer2_steps=tuple(existing_l2 + injected_scalers),
    )
    return ModelSpec(
        model_id=model_spec.model_id,
        display_name=model_spec.display_name,
        family=model_spec.family,
        estimator_factory=model_spec.estimator_factory,
        capabilities=model_spec.capabilities,
        description=model_spec.description,
        scientific_justification=model_spec.scientific_justification,
        parameters=model_spec.parameters,
        random_seed_policy=model_spec.random_seed_policy,
        preprocessing=new_prep,
        search_spec=model_spec.search_spec,
    )


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
    phase: str = "DEV_CV",
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
    fold_id = (
        "final_holdout"
        if phase == "FINAL_HOLDOUT"
        else (getattr(fold, "fold_id", None) or f"fold_{getattr(fold, 'fold_index', 0)}")
    )
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
    effective_spec = resolve_deferred_preprocessing(model_spec, getattr(sanitized_view, "deferred_rules", ()))

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

        # 2. FEATURE_SELECTION & 3. HYPERPARAMETER_TUNING (ADR-003, AD-028):
        # When DYNAMIC + search_spec are both active, Nested CV runs Layer 1 + dynamic selection
        # inside each inner sub-fold first, then refits Layer 1 + dynamic selection + Layer 2 on outer train.
        X_train_cand = {col: train_view.columns[col] for col in train_view.candidate_feature_cols}
        X_val_cand = {col: val_view.columns[col] for col in val_view.candidate_feature_cols}

        part_strategy = str(getattr(partition_plan, "strategy", "")) or None
        group_col = sanitized_view.schema.group_col
        groups_arr = (
            np.asarray(train_view.columns[group_col])
            if group_col and group_col in train_view.columns
            else None
        )

        is_dynamic = getattr(getattr(scenario, "mode", None), "value", scenario.mode) == "DYNAMIC"

        if effective_spec.search_spec is not None and is_dynamic:
            current_phase = CellPhase.HYPERPARAMETER_TUNING
            t_phase_start = time.perf_counter()
            cand_cols = list(X_train_cand.keys())
            X_train_cand_mat = np.column_stack([X_train_cand[col] for col in cand_cols])
            tuning_res = run_nested_tuning(
                spec=effective_spec.search_spec,
                model_spec=effective_spec,
                X_train=X_train_cand_mat,
                y_train=y_train,
                seed=cell_seed,
                X_train_cand=X_train_cand,
                scenario=scenario,
                partition_strategy=part_strategy,
                groups=groups_arr,
            )
            merged_params = dict(effective_spec.parameters)
            merged_params.update(tuning_res.best_params)
            effective_spec = ModelSpec(
                model_id=effective_spec.model_id,
                display_name=effective_spec.display_name,
                family=effective_spec.family,
                estimator_factory=effective_spec.estimator_factory,
                capabilities=effective_spec.capabilities,
                description=effective_spec.description,
                scientific_justification=effective_spec.scientific_justification,
                parameters=merged_params,
                random_seed_policy=effective_spec.random_seed_policy,
                preprocessing=effective_spec.preprocessing,
                search_spec=None,
            )
            t_tune = time.perf_counter() - t_phase_start

        current_phase = CellPhase.FEATURE_SELECTION
        t_phase_start = time.perf_counter()

        # When DYNAMIC + Layer 1 (e.g. deferred encoders/imputers) are active, fit Layer 1 on outer
        # X_train_cand before select_features_in_fold so relevance/redundancy stats see finite floats.
        outer_l1_fitted = None
        X_train_cand_fs = X_train_cand
        X_val_cand_fs = X_val_cand
        if is_dynamic and effective_spec.preprocessing is not None and effective_spec.preprocessing.layer1_steps:
            from experimental_ml.models.preprocessing.types import TwoLayerPreprocessingSpec

            cand_cols_fs = list(X_train_cand.keys())
            l1_only_spec = TwoLayerPreprocessingSpec(
                layer1_steps=effective_spec.preprocessing.layer1_steps,
                layer2_steps=(),
            )
            l1_tr_mat = np.column_stack([X_train_cand[c] for c in cand_cols_fs])
            l1_va_mat = np.column_stack([X_val_cand[c] for c in cand_cols_fs])
            outer_l1_fitted = fit_two_layer_preprocessing(l1_only_spec, l1_tr_mat)
            l1_tr_out = apply_two_layer_preprocessing(outer_l1_fitted, l1_tr_mat)
            l1_va_out = apply_two_layer_preprocessing(outer_l1_fitted, l1_va_mat)
            X_train_cand_fs = {c: l1_tr_out[:, i] for i, c in enumerate(cand_cols_fs)}
            X_val_cand_fs = {c: l1_va_out[:, i] for i, c in enumerate(cand_cols_fs)}

        selection_res = select_features_in_fold(
            X_train=X_train_cand_fs,
            y_train=y_train,
            scenario=scenario,
            random_state=cell_seed,
        )
        selected_features_tuple = tuple(selection_res.selected_features)

        X_train_sel = apply_feature_selection(X_train_cand_fs, selection_res)
        X_val_sel = apply_feature_selection(X_val_cand_fs, selection_res)

        X_train_matrix = np.column_stack([X_train_sel[col] for col in selected_features_tuple])
        X_val_matrix = np.column_stack([X_val_sel[col] for col in selected_features_tuple])

        t_fs = time.perf_counter() - t_phase_start

        # 3. HYPERPARAMETER_TUNING (FIXED scenario with search_spec)
        if effective_spec.search_spec is not None and not is_dynamic:
            current_phase = CellPhase.HYPERPARAMETER_TUNING
            t_phase_start = time.perf_counter()
            tuning_res = run_nested_tuning(
                spec=effective_spec.search_spec,
                model_spec=effective_spec,
                X_train=X_train_matrix,
                y_train=y_train,
                seed=cell_seed,
                partition_strategy=part_strategy,
                groups=groups_arr,
            )
            merged_params = dict(effective_spec.parameters)
            merged_params.update(tuning_res.best_params)

            effective_spec = ModelSpec(
                model_id=effective_spec.model_id,
                display_name=effective_spec.display_name,
                family=effective_spec.family,
                estimator_factory=effective_spec.estimator_factory,
                capabilities=effective_spec.capabilities,
                description=effective_spec.description,
                scientific_justification=effective_spec.scientific_justification,
                parameters=merged_params,
                random_seed_policy=effective_spec.random_seed_policy,
                preprocessing=effective_spec.preprocessing,
                search_spec=None,
            )

            t_tune = time.perf_counter() - t_phase_start

        # 4. PREPROCESSING_L2: Two-layer preprocessing fit on train and project validation
        current_phase = CellPhase.PREPROCESSING_L2
        t_phase_start = time.perf_counter()

        if effective_spec.preprocessing is not None:
            if outer_l1_fitted is not None:
                from experimental_ml.models.preprocessing.types import TwoLayerPreprocessingSpec

                l2_only_spec = TwoLayerPreprocessingSpec(
                    layer1_steps=(),
                    layer2_steps=effective_spec.preprocessing.layer2_steps,
                )
                prep_state = fit_two_layer_preprocessing(l2_only_spec, X_train_matrix)
            else:
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

        from experimental_ml.metrics.catalog import get_metric_spec

        y_pred = np.asarray(pred_outputs["y_pred"])
        y_proba_raw = pred_outputs.get("y_proba")
        computed_metrics: dict[str, MetricValue] = {}
        for metric_name in metrics:
            m_spec = get_metric_spec(metric_name)
            if m_spec.requires_probabilities:
                if y_proba_raw is None:
                    raise ConfigurationError(
                        f"Metric '{metric_name}' requires predicted probabilities ('y_proba'), "
                        f"but model '{effective_spec.model_id}' did not return them."
                    )
                eval_pred = np.asarray(y_proba_raw)
            else:
                eval_pred = y_pred
            m_val = compute_metric(
                metric_name,
                y_val,
                eval_pred,
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
            phase=phase,
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
