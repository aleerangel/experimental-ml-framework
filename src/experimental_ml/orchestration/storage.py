"""Atomic filesystem persistence for cell execution artifacts.

Complies with ORCH-08, STORE-01, STORE-07, and ADR-008.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import read_json, write_json_atomic
from experimental_ml.orchestration.codecs import (
    cell_result_from_dict,
    cell_result_to_dict,
    prediction_record_from_dict,
    prediction_record_to_dict,
)
from experimental_ml.orchestration.types import CellId, CellResultRecord, PredictionRecord


def save_cell_artifacts(
    cell_result: CellResultRecord,
    prediction_record: PredictionRecord | None,
    run_dir: Path | str,
    *,
    overwrite: bool = False,
) -> tuple[Path, Path | None]:
    """Atomically save cell result record and optional prediction record to run directory.

    Files written:
      - `{run_dir}/cells/cell_{cell_id}.json`
      - `{run_dir}/predictions/pred_{cell_id}.json` (if prediction_record is not None)

    Args:
        cell_result: The completed or failed cell execution result.
        prediction_record: Predictions on the validation fold, or None if failed.
        run_dir: Base directory for the experiment run.
        overwrite: If False, raises ConfigurationError if destination files already exist.

    Returns:
        Tuple of (path_to_cell_json, path_to_pred_json_or_None).

    Raises:
        ConfigurationError: If any target file exists and overwrite=False.
    """
    run_path = Path(run_dir).resolve()
    cells_dir = run_path / "cells"
    preds_dir = run_path / "predictions"

    cells_dir.mkdir(parents=True, exist_ok=True)
    preds_dir.mkdir(parents=True, exist_ok=True)

    cell_file = cells_dir / f"cell_{cell_result.cell_id}.json"
    pred_file = (
        preds_dir / f"pred_{cell_result.cell_id}.json"
        if prediction_record is not None
        else None
    )

    if not overwrite:
        if cell_file.exists():
            raise ConfigurationError(
                f"Target cell artifact already exists and overwrite is False: '{cell_file}'"
            )
        if pred_file is not None and pred_file.exists():
            raise ConfigurationError(
                f"Target prediction artifact already exists and overwrite is False: '{pred_file}'"
            )

    cell_dict = cell_result_to_dict(cell_result)
    write_json_atomic(cell_file, cell_dict, overwrite=overwrite)

    if prediction_record is not None and pred_file is not None:
        pred_dict = prediction_record_to_dict(prediction_record)
        write_json_atomic(pred_file, pred_dict, overwrite=overwrite)

    return cell_file, pred_file


def load_cell_artifacts(
    cell_id: CellId | str,
    run_dir: Path | str,
) -> tuple[CellResultRecord, PredictionRecord | None]:
    """Load cell result and optional prediction record from run directory.

    Args:
        cell_id: Unique cell identifier.
        run_dir: Base directory for the experiment run.

    Returns:
        Tuple of (CellResultRecord, PredictionRecord | None).

    Raises:
        ConfigurationError: If cell artifact does not exist or content is malformed.
    """
    run_path = Path(run_dir).resolve()
    cell_file = run_path / "cells" / f"cell_{cell_id}.json"
    pred_file = run_path / "predictions" / f"pred_{cell_id}.json"

    if not cell_file.exists():
        raise ConfigurationError(f"Cell artifact not found: '{cell_file}'")

    try:
        cell_raw = read_json(cell_file)
        cell_result = cell_result_from_dict(cell_raw)
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to load or parse cell artifact '{cell_file}': {exc}"
        ) from exc

    prediction_record: PredictionRecord | None = None
    if pred_file.exists():
        try:
            pred_raw = read_json(pred_file)
            prediction_record = prediction_record_from_dict(pred_raw)
        except Exception as exc:
            raise ConfigurationError(
                f"Failed to load or parse prediction artifact '{pred_file}': {exc}"
            ) from exc

    return cell_result, prediction_record
