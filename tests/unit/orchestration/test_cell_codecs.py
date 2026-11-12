"""Unit tests for cell codecs and atomic persistence (M5.1).

Covers C25 to C30 (ORCH-08).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from experimental_ml.core.enums import MetricDirection, MetricStatus
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import (
    ExperimentId,
    ModelId,
    ObservationId,
    PartitionPlanId,
    ScenarioId,
)
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue
from experimental_ml.models.types import ModelDiagnostics
from experimental_ml.orchestration.codecs import (
    cell_result_from_dict,
    cell_result_to_dict,
    prediction_record_from_dict,
    prediction_record_to_dict,
)
from experimental_ml.orchestration.storage import load_cell_artifacts, save_cell_artifacts
from experimental_ml.orchestration.types import (
    CellId,
    CellPhase,
    CellResultRecord,
    ExecutionStatus,
    PredictionRecord,
    TimingBreakdown,
)


def _make_dummy_cell_result(cell_id_str: str = "ridge_baseline_f0") -> CellResultRecord:
    timing = TimingBreakdown(
        data_extraction_time_s=0.01,
        feature_selection_time_s=0.02,
        tuning_time_s=0.0,
        preprocessing_time_s=0.03,
        fit_time_s=0.04,
        predict_time_s=0.01,
        evaluation_time_s=0.01,
        total_cell_time_s=0.12,
    )
    metrics = {
        "rmse": MetricValue(
            metric_id="rmse",
            value=1.25,
            status=MetricStatus.VALID,
            direction=MetricDirection.MINIMIZE,
            scope=MetricEvaluationScope.PER_FOLD,
            n_samples=2,
        ),
        "r2": MetricValue(
            metric_id="r2",
            value=float("nan"),
            status=MetricStatus.UNDEFINED_NAN,
            direction=MetricDirection.MAXIMIZE,
            scope=MetricEvaluationScope.PER_FOLD,
            n_samples=2,
        ),
    }
    diagnostics = ModelDiagnostics(
        model_id="ridge",
        phase="TRAIN",
        diagnostics={"n_iter": 5},
        extracted_at="2026-11-12T10:00:00Z",
    )
    return CellResultRecord(
        cell_id=CellId(cell_id_str),
        experiment_id=ExperimentId("exp_test"),
        partition_plan_id=PartitionPlanId("plan_test"),
        model_id=ModelId("ridge"),
        scenario_id=ScenarioId("baseline"),
        fold_id="0",
        timing=timing,
        phase="DEV_CV",
        status=ExecutionStatus.COMPLETED,
        selected_features=("f1",),
        effective_parameters={"alpha": 1.0},
        metrics=metrics,
        diagnostics=diagnostics,
        error_phase=None,
        error_type=None,
        error_message=None,
        error_traceback=None,
    )


def _make_dummy_prediction_record(cell_id_str: str = "ridge_baseline_f0") -> PredictionRecord:
    return PredictionRecord(
        cell_id=CellId(cell_id_str),
        observation_ids=(ObservationId("obs_3"), ObservationId("obs_4")),
        y_true=(30.0, 40.0),
        y_pred=(29.5, 41.2),
        y_std=(0.1, 0.2),
        y_proba=None,
        residuals=(0.5, -1.2),
    )


def test_m51_04_01_cell_result_to_dict():
    """C25: cell_result_to_dict produces JSON-serializable dictionary."""
    result = _make_dummy_cell_result()
    d = cell_result_to_dict(result)

    assert isinstance(d, dict)
    assert d["cell_id"] == "ridge_baseline_f0"
    assert d["model_id"] == "ridge"
    assert d["status"] == "COMPLETED"
    assert d["timing"]["total_cell_time_s"] == 0.12
    assert d["metrics"]["rmse"]["value"] == 1.25
    assert d["metrics"]["r2"]["value"] is None  # NaN serializes to null
    assert d["metrics"]["r2"]["status"] == "UNDEFINED_NAN"

    # Must be serializable by standard json.dumps without NaN
    json_str = json.dumps(d, allow_nan=False)
    assert "ridge_baseline_f0" in json_str


def test_m51_04_02_cell_result_from_dict():
    """C26: cell_result_from_dict round-trip fidelity."""
    original = _make_dummy_cell_result()
    d = cell_result_to_dict(original)
    reconstructed = cell_result_from_dict(d)

    assert reconstructed.cell_id == original.cell_id
    assert reconstructed.model_id == original.model_id
    assert reconstructed.scenario_id == original.scenario_id
    assert reconstructed.fold_id == original.fold_id
    assert reconstructed.status == original.status
    assert reconstructed.timing == original.timing
    assert reconstructed.effective_parameters == original.effective_parameters
    assert reconstructed.diagnostics == original.diagnostics

    assert "rmse" in reconstructed.metrics
    assert reconstructed.metrics["rmse"].value == pytest.approx(1.25)
    assert reconstructed.metrics["rmse"].status == MetricStatus.VALID

    assert "r2" in reconstructed.metrics
    assert math.isnan(reconstructed.metrics["r2"].value)
    assert reconstructed.metrics["r2"].status == MetricStatus.UNDEFINED_NAN


def test_m51_04_03_prediction_record_to_dict():
    """C27: prediction_record_to_dict produces JSON-serializable dictionary."""
    pred = _make_dummy_prediction_record()
    d = prediction_record_to_dict(pred)

    assert isinstance(d, dict)
    assert d["cell_id"] == "ridge_baseline_f0"
    assert d["observation_ids"] == ["obs_3", "obs_4"]
    assert d["y_true"] == [30.0, 40.0]
    assert d["y_pred"] == [29.5, 41.2]
    assert d["y_std"] == [0.1, 0.2]
    assert d["y_proba"] is None
    assert d["residuals"] == [0.5, -1.2]

    json_str = json.dumps(d, allow_nan=False)
    assert "obs_3" in json_str


def test_m51_04_04_prediction_record_from_dict():
    """C28: prediction_record_from_dict round-trip fidelity."""
    original = _make_dummy_prediction_record()
    d = prediction_record_to_dict(original)
    reconstructed = prediction_record_from_dict(d)

    assert reconstructed.cell_id == original.cell_id
    assert reconstructed.observation_ids == original.observation_ids
    np.testing.assert_allclose(reconstructed.y_true, original.y_true)
    np.testing.assert_allclose(reconstructed.y_pred, original.y_pred)
    assert reconstructed.y_std is not None
    assert original.y_std is not None
    np.testing.assert_allclose(reconstructed.y_std, original.y_std)
    assert reconstructed.y_proba is None
    assert reconstructed.residuals is not None
    assert original.residuals is not None
    np.testing.assert_allclose(reconstructed.residuals, original.residuals)


def test_m51_04_05_atomic_save_artifacts(tmp_path: Path):
    """C29: save_cell_artifacts atomically writes cell_<id>.json and pred_<id>.json."""
    result = _make_dummy_cell_result("cell_alpha")
    pred = _make_dummy_prediction_record("cell_alpha")

    run_dir = tmp_path / "exp_run_1"
    cell_file, pred_file = save_cell_artifacts(result, pred, run_dir)

    assert cell_file.exists()
    assert cell_file.name == "cell_cell_alpha.json"
    assert pred_file is not None
    assert pred_file.exists()
    assert pred_file.name == "pred_cell_alpha.json"

    # Reload and verify
    re_result, re_pred = load_cell_artifacts("cell_alpha", run_dir)
    assert re_result.cell_id == result.cell_id
    assert re_result.status == ExecutionStatus.COMPLETED
    assert re_pred is not None
    assert re_pred.cell_id == pred.cell_id
    np.testing.assert_allclose(re_pred.y_pred, pred.y_pred)


def test_m51_04_06_overwrite_protection(tmp_path: Path):
    """C30: save_cell_artifacts raises ConfigurationError if files exist and overwrite=False."""
    result = _make_dummy_cell_result("cell_beta")
    pred = _make_dummy_prediction_record("cell_beta")

    run_dir = tmp_path / "exp_run_2"
    save_cell_artifacts(result, pred, run_dir, overwrite=False)

    # Second call with overwrite=False must raise ConfigurationError
    with pytest.raises(ConfigurationError, match="Target cell artifact already exists"):
        save_cell_artifacts(result, pred, run_dir, overwrite=False)

    # Second call with overwrite=True succeeds
    cell_file, pred_file = save_cell_artifacts(result, pred, run_dir, overwrite=True)
    assert cell_file.exists()
