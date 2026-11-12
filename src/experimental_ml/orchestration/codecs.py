"""Lossless dictionary codecs for cell execution results and prediction records.

Complies with ORCH-08, STORE-02, STORE-03, RFC 8259, and ADR-008.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from experimental_ml.core.enums import (
    AggregationScope,
    MetricDirection,
    MetricStatus,
)
from experimental_ml.core.findings import ConfigurationError, Finding
from experimental_ml.core.types import (
    ExperimentId,
    ModelId,
    ObservationId,
    PartitionPlanId,
    ScenarioId,
)
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue
from experimental_ml.models.types import ModelDiagnostics
from experimental_ml.orchestration.types import (
    CellId,
    CellPhase,
    CellResultRecord,
    ErrorPolicy,
    ExecutionStatus,
    PredictionRecord,
    TimingBreakdown,
)


def metric_value_to_dict(mv: MetricValue) -> dict[str, Any]:
    """Serialize a MetricValue to a JSON-compatible dictionary."""
    val = mv.value
    if math.isnan(val):
        val_repr: float | None = None
    else:
        val_repr = float(val)

    warnings_list = []
    for w in mv.warnings:
        if hasattr(w, "to_dict"):
            warnings_list.append(w.to_dict())
        else:
            warnings_list.append({
                "category": getattr(w, "category", "WARNING"),
                "message": getattr(w, "message", str(w)),
            })

    return {
        "metric_id": mv.metric_id,
        "value": val_repr,
        "status": mv.status.value,
        "direction": mv.direction.value,
        "scope": mv.scope.value,
        "n_samples": mv.n_samples,
        "warnings": warnings_list,
    }


def metric_value_from_dict(d: dict[str, Any]) -> MetricValue:
    """Reconstruct a MetricValue from a dictionary."""
    raw_val = d.get("value")
    val = float("nan") if raw_val is None else float(raw_val)

    scope_str = d["scope"]
    scope_obj: MetricEvaluationScope | AggregationScope
    try:
        scope_obj = MetricEvaluationScope(scope_str)
    except ValueError:
        scope_obj = AggregationScope(scope_str)

    warnings_list = []
    for w in d.get("warnings", []):
        if isinstance(w, dict):
            warnings_list.append(
                Finding(
                    category=w.get("category", "WARNING"),
                    message=w.get("message", ""),
                    source_column=w.get("source_column"),
                    details=w.get("details", {}),
                )
            )
        else:
            warnings_list.append(Finding(category="WARNING", message=str(w)))

    return MetricValue(
        metric_id=d["metric_id"],
        value=val,
        status=MetricStatus(d["status"]),
        direction=MetricDirection(d["direction"]),
        scope=scope_obj,
        n_samples=int(d["n_samples"]),
        warnings=tuple(warnings_list),
    )


def timing_breakdown_to_dict(timing: TimingBreakdown) -> dict[str, float]:
    """Serialize TimingBreakdown to dictionary."""
    return {
        "data_extraction_time_s": float(timing.data_extraction_time_s),
        "feature_selection_time_s": float(timing.feature_selection_time_s),
        "tuning_time_s": float(timing.tuning_time_s),
        "preprocessing_time_s": float(timing.preprocessing_time_s),
        "fit_time_s": float(timing.fit_time_s),
        "predict_time_s": float(timing.predict_time_s),
        "evaluation_time_s": float(timing.evaluation_time_s),
        "total_cell_time_s": float(timing.total_cell_time_s),
    }


def timing_breakdown_from_dict(d: dict[str, Any]) -> TimingBreakdown:
    """Reconstruct TimingBreakdown from dictionary."""
    return TimingBreakdown(
        data_extraction_time_s=float(d.get("data_extraction_time_s", 0.0)),
        feature_selection_time_s=float(d.get("feature_selection_time_s", 0.0)),
        tuning_time_s=float(d.get("tuning_time_s", 0.0)),
        preprocessing_time_s=float(d.get("preprocessing_time_s", 0.0)),
        fit_time_s=float(d.get("fit_time_s", 0.0)),
        predict_time_s=float(d.get("predict_time_s", 0.0)),
        evaluation_time_s=float(d.get("evaluation_time_s", 0.0)),
        total_cell_time_s=float(d.get("total_cell_time_s", 0.0)),
    )


def model_diagnostics_to_dict(diag: ModelDiagnostics) -> dict[str, Any]:
    """Serialize ModelDiagnostics to dictionary."""
    return {
        "model_id": diag.model_id,
        "phase": diag.phase,
        "diagnostics": dict(diag.diagnostics),
        "extracted_at": diag.extracted_at,
    }


def model_diagnostics_from_dict(d: dict[str, Any]) -> ModelDiagnostics:
    """Reconstruct ModelDiagnostics from dictionary."""
    return ModelDiagnostics(
        model_id=d["model_id"],
        phase=d["phase"],
        diagnostics=dict(d.get("diagnostics", {})),
        extracted_at=d["extracted_at"],
    )


def cell_result_to_dict(result: CellResultRecord) -> dict[str, Any]:
    """Serialize CellResultRecord to a JSON-compatible dictionary."""
    metrics_serialized = {
        k: metric_value_to_dict(v) for k, v in result.metrics.items()
    }
    diag_serialized = (
        model_diagnostics_to_dict(result.diagnostics)
        if result.diagnostics is not None
        else None
    )

    return {
        "cell_id": str(result.cell_id),
        "experiment_id": str(result.experiment_id),
        "partition_plan_id": str(result.partition_plan_id),
        "model_id": str(result.model_id),
        "scenario_id": str(result.scenario_id),
        "fold_id": str(result.fold_id),
        "phase": result.phase,
        "status": result.status.value,
        "timing": timing_breakdown_to_dict(result.timing),
        "selected_features": list(result.selected_features),
        "effective_parameters": dict(result.effective_parameters),
        "metrics": metrics_serialized,
        "diagnostics": diag_serialized,
        "error_phase": result.error_phase.value if result.error_phase is not None else None,
        "error_type": result.error_type,
        "error_message": result.error_message,
        "error_traceback": result.error_traceback,
    }


def cell_result_from_dict(d: dict[str, Any]) -> CellResultRecord:
    """Reconstruct CellResultRecord from a dictionary."""
    raw_error_phase = d.get("error_phase")
    error_phase = CellPhase(raw_error_phase) if raw_error_phase is not None else None

    metrics_reconstructed = {
        k: metric_value_from_dict(v) for k, v in d.get("metrics", {}).items()
    }

    raw_diag = d.get("diagnostics")
    diagnostics = model_diagnostics_from_dict(raw_diag) if raw_diag is not None else None

    return CellResultRecord(
        cell_id=CellId(d["cell_id"]),
        experiment_id=ExperimentId(d.get("experiment_id", "exp_default")),
        partition_plan_id=PartitionPlanId(d.get("partition_plan_id", "plan_default")),
        model_id=ModelId(d["model_id"]),
        scenario_id=ScenarioId(d["scenario_id"]),
        fold_id=str(d["fold_id"]),
        phase=d.get("phase", "DEV_CV"),
        status=ExecutionStatus(d["status"]),
        timing=timing_breakdown_from_dict(d["timing"]),
        selected_features=tuple(d.get("selected_features", ())),
        effective_parameters=dict(d.get("effective_parameters", {})),
        metrics=metrics_reconstructed,
        diagnostics=diagnostics,
        error_phase=error_phase,
        error_type=d.get("error_type"),
        error_message=d.get("error_message"),
        error_traceback=d.get("error_traceback"),
    )


def prediction_record_to_dict(record: PredictionRecord) -> dict[str, Any]:
    """Serialize PredictionRecord to a JSON-compatible dictionary."""
    return {
        "cell_id": str(record.cell_id),
        "observation_ids": [str(oid) for oid in record.observation_ids],
        "y_true": list(record.y_true),
        "y_pred": list(record.y_pred),
        "y_std": list(record.y_std) if record.y_std is not None else None,
        "y_proba": [list(row) for row in record.y_proba] if record.y_proba is not None else None,
        "residuals": list(record.residuals) if record.residuals is not None else None,
    }


def prediction_record_from_dict(d: dict[str, Any]) -> PredictionRecord:
    """Reconstruct PredictionRecord from a dictionary."""
    y_std = tuple(float(x) for x in d["y_std"]) if d.get("y_std") is not None else None
    y_proba = (
        tuple(tuple(float(p) for p in row) for row in d["y_proba"])
        if d.get("y_proba") is not None
        else None
    )
    residuals = tuple(float(r) for r in d["residuals"]) if d.get("residuals") is not None else None

    return PredictionRecord(
        cell_id=CellId(d["cell_id"]),
        observation_ids=tuple(ObservationId(oid) for oid in d["observation_ids"]),
        y_true=tuple(float(y) for y in d["y_true"]),
        y_pred=tuple(float(y) for y in d["y_pred"]),
        y_std=y_std,
        y_proba=y_proba,
        residuals=residuals,
    )
