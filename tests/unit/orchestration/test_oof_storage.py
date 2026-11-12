"""Unit tests for ConsolidatedOofPredictions data model, codecs, and atomic persistence.

Covers ORCH-20, AC-M53-03-01 to AC-M53-03-04, and Checks C1 to C4.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from experimental_ml.core.enums import AggregationScope, MetricDirection, MetricStatus, TaskType
from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.core.types import ModelId, ObservationId, ScenarioId
from experimental_ml.metrics.types import AggregatedMetricValue, MetricEvaluationScope, MetricValue
from experimental_ml.orchestration.codecs import (
    aggregated_metric_value_from_dict,
    aggregated_metric_value_to_dict,
    oof_predictions_from_dict,
    oof_predictions_to_dict,
)
from experimental_ml.orchestration.oof import (
    ConsolidatedOofPredictions,
    load_oof_predictions,
    save_oof_predictions,
)


def _make_dummy_oof_record() -> ConsolidatedOofPredictions:
    """Helper to build a valid ConsolidatedOofPredictions record."""
    mv = MetricValue(
        metric_id="rmse",
        value=1.25,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.POOLED_OOF,
        n_samples=3,
    )
    amv = AggregatedMetricValue(
        metric_id="rmse",
        mean=1.20,
        std=0.05,
        median=1.21,
        iqr=0.04,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=AggregationScope.FOLD_AGGREGATION,
        valid_folds=2,
        total_folds=2,
        coverage=1.0,
        fold_values=(
            MetricValue(
                metric_id="rmse",
                value=1.15,
                status=MetricStatus.VALID,
                direction=MetricDirection.MINIMIZE,
                scope=MetricEvaluationScope.PER_FOLD,
                n_samples=2,
            ),
            MetricValue(
                metric_id="rmse",
                value=1.25,
                status=MetricStatus.VALID,
                direction=MetricDirection.MINIMIZE,
                scope=MetricEvaluationScope.PER_FOLD,
                n_samples=1,
            ),
        ),
    )

    return ConsolidatedOofPredictions(
        model_id=ModelId("model_ridge"),
        scenario_id=ScenarioId("sc_top5"),
        task_type=TaskType.REGRESSION,
        observation_ids=(ObservationId("obs_01"), ObservationId("obs_02"), ObservationId("obs_03")),
        y_true=(10.0, 20.0, 30.0),
        y_pred=(10.5, 19.8, 29.5),
        y_std=(0.2, 0.3, 0.25),
        residuals=(-0.5, 0.2, 0.5),
        pooled_metrics={"rmse": mv},
        aggregated_metrics={"rmse": amv},
        fold_ids=("fold_0", "fold_1"),
        coverage=1.0,
        status=MetricStatus.VALID,
        warnings=(),
    )


def test_m53_03_01_save_oof_predictions_atomic(tmp_path: Path) -> None:
    """Proof C1: save_oof_predictions atomically writes JSON under {run_dir}/oof/ (ORCH-20, AC 1)."""
    oof = _make_dummy_oof_record()
    out_file = save_oof_predictions(oof, tmp_path)

    assert out_file.exists()
    assert out_file.parent == tmp_path / "oof"
    assert out_file.name == "oof_model_ridge__sc_top5.json"

    # Verify JSON content
    import json

    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["model_id"] == "model_ridge"
    assert data["scenario_id"] == "sc_top5"
    assert data["task_type"] == "REGRESSION"
    assert data["observation_ids"] == ["obs_01", "obs_02", "obs_03"]
    assert data["y_true"] == [10.0, 20.0, 30.0]
    assert data["y_pred"] == [10.5, 19.8, 29.5]
    assert data["y_std"] == [0.2, 0.3, 0.25]
    assert data["residuals"] == [-0.5, 0.2, 0.5]
    assert "rmse" in data["pooled_metrics"]
    assert "rmse" in data["aggregated_metrics"]


def test_m53_03_02_load_oof_predictions(tmp_path: Path) -> None:
    """Proof C2: load_oof_predictions reconstructs ConsolidatedOofPredictions (ORCH-20, AC 2)."""
    oof = _make_dummy_oof_record()
    save_oof_predictions(oof, tmp_path)

    loaded = load_oof_predictions("model_ridge", "sc_top5", tmp_path)
    assert isinstance(loaded, ConsolidatedOofPredictions)
    assert loaded.model_id == ModelId("model_ridge")
    assert loaded.scenario_id == ScenarioId("sc_top5")
    assert loaded.task_type == TaskType.REGRESSION
    assert loaded.observation_ids == (
        ObservationId("obs_01"),
        ObservationId("obs_02"),
        ObservationId("obs_03"),
    )
    assert loaded.y_true == (10.0, 20.0, 30.0)
    assert loaded.y_pred == (10.5, 19.8, 29.5)
    assert loaded.y_std == (0.2, 0.3, 0.25)
    assert loaded.residuals == (-0.5, 0.2, 0.5)
    assert "rmse" in loaded.pooled_metrics
    assert loaded.pooled_metrics["rmse"].value == 1.25
    assert "rmse" in loaded.aggregated_metrics
    assert loaded.aggregated_metrics["rmse"].mean == 1.20
    assert loaded.coverage == 1.0
    assert loaded.status == MetricStatus.VALID


def test_m53_03_03_codecs_roundtrip_fidelity() -> None:
    """Proof C3: oof_predictions_to_dict and oof_predictions_from_dict round-trip fidelity (ORCH-20, AC 3)."""
    oof = _make_dummy_oof_record()
    d = oof_predictions_to_dict(oof)
    restored = oof_predictions_from_dict(d)

    assert restored.model_id == oof.model_id
    assert restored.scenario_id == oof.scenario_id
    assert restored.task_type == oof.task_type
    assert restored.observation_ids == oof.observation_ids
    assert restored.y_true == oof.y_true
    assert restored.y_pred == oof.y_pred
    assert restored.y_std == oof.y_std
    assert restored.y_proba == oof.y_proba
    assert restored.residuals == oof.residuals
    assert restored.fold_ids == oof.fold_ids
    assert restored.coverage == oof.coverage
    assert restored.status == oof.status
    assert restored.warnings == oof.warnings

    # Test AggregatedMetricValue codec with NaNs
    nan_amv = AggregatedMetricValue(
        metric_id="mape",
        mean=float("nan"),
        std=float("nan"),
        median=float("nan"),
        iqr=float("nan"),
        status=MetricStatus.UNDEFINED_NAN,
        direction=MetricDirection.MINIMIZE,
        scope=AggregationScope.FOLD_AGGREGATION,
        valid_folds=0,
        total_folds=3,
        coverage=0.0,
    )
    nan_dict = aggregated_metric_value_to_dict(nan_amv)
    assert nan_dict["mean"] is None
    restored_nan = aggregated_metric_value_from_dict(nan_dict)
    assert math.isnan(restored_nan.mean)
    assert restored_nan.status == MetricStatus.UNDEFINED_NAN


def test_m53_03_04_save_oof_no_overwrite_protection(tmp_path: Path) -> None:
    """Proof C4: save_oof_predictions with overwrite=False raises ConfigurationError on collision (ORCH-20, AC 4)."""
    oof = _make_dummy_oof_record()
    save_oof_predictions(oof, tmp_path)

    with pytest.raises(ConfigurationError, match="Target OOF artifact already exists"):
        save_oof_predictions(oof, tmp_path, overwrite=False)

    # Overwrite=True succeeds
    out_file = save_oof_predictions(oof, tmp_path, overwrite=True)
    assert out_file.exists()


def test_oof_invariants_validation() -> None:
    """Extra invariant tests for ConsolidatedOofPredictions."""
    # Empty observation_ids
    with pytest.raises(ContractViolationError, match="cannot be empty"):
        ConsolidatedOofPredictions(
            model_id=ModelId("m"),
            scenario_id=ScenarioId("s"),
            task_type=TaskType.REGRESSION,
            observation_ids=(),
            y_true=(),
            y_pred=(),
        )

    # Length mismatch
    with pytest.raises(ContractViolationError, match="y_true length"):
        ConsolidatedOofPredictions(
            model_id=ModelId("m"),
            scenario_id=ScenarioId("s"),
            task_type=TaskType.REGRESSION,
            observation_ids=(ObservationId("obs_1"),),
            y_true=(1.0, 2.0),
            y_pred=(1.0,),
        )

    # Non-canonical sorting
    with pytest.raises(ContractViolationError, match="canonically sorted"):
        ConsolidatedOofPredictions(
            model_id=ModelId("m"),
            scenario_id=ScenarioId("s"),
            task_type=TaskType.REGRESSION,
            observation_ids=(ObservationId("obs_2"), ObservationId("obs_1")),
            y_true=(1.0, 2.0),
            y_pred=(1.0, 2.0),
        )

    # Duplicate observation_ids
    with pytest.raises(ContractViolationError, match="must be unique"):
        ConsolidatedOofPredictions(
            model_id=ModelId("m"),
            scenario_id=ScenarioId("s"),
            task_type=TaskType.REGRESSION,
            observation_ids=(ObservationId("obs_1"), ObservationId("obs_1")),
            y_true=(1.0, 2.0),
            y_pred=(1.0, 2.0),
        )
