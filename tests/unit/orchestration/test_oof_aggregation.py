"""Unit tests for out-of-fold prediction aggregation and committee statistics.

Covers ORCH-15, ORCH-16, AC-M53-01-01 to AC-M53-01-05, and Checks C5 to C9.
"""

from __future__ import annotations

import math
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.core.types import ModelId, ObservationId, ScenarioId
from experimental_ml.orchestration.oof import (
    ConsolidatedOofPredictions,
    consolidate_oof_predictions,
)
from experimental_ml.orchestration.types import CellId, PredictionRecord


def test_m53_01_01_consolidate_aggregates_records() -> None:
    """Proof C5: consolidate_oof_predictions aggregates PredictionRecords into single record (ORCH-15, AC 1)."""
    p1 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_0"),
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        y_true=(10.0, 20.0),
        y_pred=(10.5, 19.5),
    )
    p2 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_1"),
        observation_ids=(ObservationId("obs_3"), ObservationId("obs_4")),
        y_true=(30.0, 40.0),
        y_pred=(29.8, 40.2),
    )

    oof = consolidate_oof_predictions(
        model_id="ridge",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        prediction_records=[p1, p2],
    )

    assert isinstance(oof, ConsolidatedOofPredictions)
    assert oof.model_id == ModelId("ridge")
    assert oof.scenario_id == ScenarioId("sc1")
    assert len(oof.observation_ids) == 4
    assert oof.observation_ids == (
        ObservationId("obs_1"),
        ObservationId("obs_2"),
        ObservationId("obs_3"),
        ObservationId("obs_4"),
    )
    assert oof.y_true == (10.0, 20.0, 30.0, 40.0)
    assert oof.y_pred == (10.5, 19.5, 29.8, 40.2)
    assert oof.residuals is not None
    assert pytest.approx(list(oof.residuals), abs=1e-6) == [-0.5, 0.5, 0.2, -0.2]
    assert oof.fold_ids == ("fold_0", "fold_1")


def test_m53_01_02_canonical_sorting_by_obs_id() -> None:
    """Proof C6: consolidate_oof_predictions sorts predictions canonically by observation_id (ORCH-15, AC 2)."""
    # Unordered records with unordered observation_ids
    p1 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_1"),
        observation_ids=(ObservationId("obs_Z"), ObservationId("obs_A")),
        y_true=(100.0, 5.0),
        y_pred=(102.0, 5.2),
    )
    p2 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_0"),
        observation_ids=(ObservationId("obs_M"),),
        y_true=(50.0,),
        y_pred=(49.5,),
    )

    oof = consolidate_oof_predictions(
        model_id="ridge",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        prediction_records=[p1, p2],
    )

    assert oof.observation_ids == (
        ObservationId("obs_A"),
        ObservationId("obs_M"),
        ObservationId("obs_Z"),
    )
    assert oof.y_true == (5.0, 50.0, 100.0)
    assert oof.y_pred == (5.2, 49.5, 102.0)


def test_m53_01_03_multi_fold_committee_statistics() -> None:
    """Proof C7: Multi-fold evaluated observations compute committee mean and sample std (ORCH-16, AC 3)."""
    # Repeated evaluation (e.g. bootstrap or repeated CV): obs_1 evaluated across 3 folds
    p1 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_0"),
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        y_true=(10.0, 20.0),
        y_pred=(10.0, 20.0),
    )
    p2 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_1"),
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        y_true=(10.0, 20.0),
        y_pred=(12.0, 22.0),
    )
    p3 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_2"),
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        y_true=(10.0, 20.0),
        y_pred=(14.0, 24.0),
    )

    oof = consolidate_oof_predictions(
        model_id="ridge",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        prediction_records=[p1, p2, p3],
    )

    assert oof.observation_ids == (ObservationId("obs_1"), ObservationId("obs_2"))
    # Mean of [10.0, 12.0, 14.0] = 12.0
    # Mean of [20.0, 22.0, 24.0] = 22.0
    assert oof.y_pred == (12.0, 22.0)

    # Sample std (ddof=1) of [10, 12, 14]:
    # deviations: -2, 0, 2; sum sq = 8; var = 8/2 = 4; std = 2.0
    assert oof.y_std is not None
    assert pytest.approx(oof.y_std[0], abs=1e-6) == 2.0
    assert pytest.approx(oof.y_std[1], abs=1e-6) == 2.0


def test_m53_01_04_single_fold_prediction_preservation() -> None:
    """Proof C8: Single-fold evaluated observations preserve point prediction and y_std (ORCH-16, AC 4)."""
    p1 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_0"),
        observation_ids=(ObservationId("obs_1"),),
        y_true=(10.0,),
        y_pred=(10.8,),
        y_std=(0.42,),
    )
    p2 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_1"),
        observation_ids=(ObservationId("obs_2"),),
        y_true=(20.0,),
        y_pred=(19.4,),
        y_std=(0.58,),
    )

    oof = consolidate_oof_predictions(
        model_id="ridge",
        scenario_id="sc1",
        task_type=TaskType.REGRESSION,
        prediction_records=[p1, p2],
    )

    assert oof.y_pred == (10.8, 19.4)
    assert oof.y_std == (0.42, 0.58)


def test_m53_01_05_classification_probability_pooling() -> None:
    """Proof C9: Classification models aggregate average class probabilities across folds (ORCH-16, AC 5)."""
    # Obs 1 evaluated in fold 0 and fold 1
    p1 = PredictionRecord(
        cell_id=CellId("cell_rf__sc1__fold_0"),
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        y_true=(0.0, 1.0),
        y_pred=(0.0, 1.0),
        y_proba=((0.8, 0.2), (0.1, 0.9)),
    )
    p2 = PredictionRecord(
        cell_id=CellId("cell_rf__sc1__fold_1"),
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_3")),
        y_true=(0.0, 1.0),
        y_pred=(0.0, 1.0),
        y_proba=((0.6, 0.4), (0.3, 0.7)),
    )

    oof = consolidate_oof_predictions(
        model_id="rf",
        scenario_id="sc1",
        task_type=TaskType.BINARY_CLASSIFICATION,
        prediction_records=[p1, p2],
    )

    assert oof.observation_ids == (
        ObservationId("obs_1"),
        ObservationId("obs_2"),
        ObservationId("obs_3"),
    )
    assert oof.y_proba is not None
    # obs_1: mean([0.8, 0.6], [0.2, 0.4]) = (0.7, 0.3)
    assert pytest.approx(oof.y_proba[0][0], abs=1e-6) == 0.7
    assert pytest.approx(oof.y_proba[0][1], abs=1e-6) == 0.3
    # obs_2: only from p1 -> (0.1, 0.9)
    assert pytest.approx(oof.y_proba[1][0], abs=1e-6) == 0.1
    assert pytest.approx(oof.y_proba[1][1], abs=1e-6) == 0.9
    # obs_3: only from p2 -> (0.3, 0.7)
    assert pytest.approx(oof.y_proba[2][0], abs=1e-6) == 0.3
    assert pytest.approx(oof.y_proba[2][1], abs=1e-6) == 0.7


def test_inconsistent_y_true_rejected() -> None:
    """Extra test: Conflicting true values across folds raise DataIntegrityError."""
    p1 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_0"),
        observation_ids=(ObservationId("obs_1"),),
        y_true=(10.0,),
        y_pred=(10.5,),
    )
    p2 = PredictionRecord(
        cell_id=CellId("cell_ridge__sc1__fold_1"),
        observation_ids=(ObservationId("obs_1"),),
        y_true=(99.0,),  # Conflicting true label!
        y_pred=(10.5,),
    )

    with pytest.raises(DataIntegrityError, match="Conflicting true labels"):
        consolidate_oof_predictions(
            model_id="ridge",
            scenario_id="sc1",
            task_type=TaskType.REGRESSION,
            prediction_records=[p1, p2],
        )
