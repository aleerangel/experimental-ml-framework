"""Storage routines for splits matrices and schemas.

Complies with STORE-04, STORE-07, D6, D10, and ADR-006.
"""

from __future__ import annotations

import csv
import gzip
import io
import os
from pathlib import Path
import tempfile
from typing import Sequence

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.core.types import ObservationId
from experimental_ml.validation.types import PartitionPlan


def write_splits_csv_gz(
    path: Path | str,
    plan: PartitionPlan,
    *,
    overwrite: bool = False,
) -> None:
    """Write splits matrix to a gzip-compressed CSV file with deterministic byte output.

    Uses gzip.GzipFile with mtime=0.0 to ensure 100% bit-identical gzip archives across
    repeated executions for the identical plan (STORE-04).

    Args:
        path: Target destination path (e.g., 'partitions/splits.csv.gz').
        plan: Validated PartitionPlan.
        overwrite: If False, raises ConfigurationError if destination exists (STORE-07).

    Raises:
        ConfigurationError: If path exists and overwrite=False.
    """
    dest_path = Path(path).resolve()

    if dest_path.exists() and not overwrite:
        raise ConfigurationError(
            f"Target artifact already exists and overwrite is False: '{dest_path}'"
        )

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine headers
    n_folds = len(plan.folds)
    fold_col_names = [f"fold_{k}" for k in range(n_folds)]
    fieldnames = ["observation_id", "holdout_role"] + fold_col_names

    # Precompute fold memberships
    fold_train_sets = [set(f.train_ids) for f in plan.folds]
    fold_val_sets = [set(f.val_ids) for f in plan.folds]
    holdout_set = set(plan.holdout_ids)

    # Observation sequence: development_ids then holdout_ids
    all_obs: Sequence[ObservationId] = tuple(plan.development_ids) + tuple(plan.holdout_ids)

    # Format CSV in memory first
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()

    for oid in all_obs:
        is_holdout = oid in holdout_set
        row: dict[str, str] = {
            "observation_id": str(oid),
            "holdout_role": "HOLDOUT" if is_holdout else "DEVELOPMENT",
        }
        for k in range(n_folds):
            col_name = fold_col_names[k]
            if oid in fold_train_sets[k]:
                row[col_name] = "TRAIN"
            elif oid in fold_val_sets[k]:
                row[col_name] = "VAL"
            else:
                row[col_name] = "EXCLUDED"
        writer.writerow(row)

    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    # Compress deterministically using GzipFile with fixed mtime
    temp_file = tempfile.NamedTemporaryFile(
        mode="wb",
        dir=dest_path.parent,
        delete=False,
        prefix=f".tmp_{dest_path.name}_",
    )
    temp_path = Path(temp_file.name)

    try:
        with gzip.GzipFile(filename="", mode="wb", fileobj=temp_file, mtime=0.0) as gz_out:
            gz_out.write(csv_bytes)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        os.replace(temp_path, dest_path)
    except Exception:
        temp_file.close()
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def read_splits_csv_gz(path: Path | str) -> list[dict[str, str]]:
    """Read decompressed rows from splits.csv.gz.

    Args:
        path: Path to the splits.csv.gz file.

    Returns:
        List of dictionaries mapping column headers to row values.
    """
    src_path = Path(path).resolve()
    with gzip.open(src_path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_splits_schema(
    path: Path | str,
    plan: PartitionPlan,
    *,
    overwrite: bool = False,
) -> None:
    """Write splits.schema.json metadata file."""
    n_folds = len(plan.folds)
    columns_spec = [
        {
            "name": "observation_id",
            "type": "string",
            "description": "Unique identifier of observation",
        },
        {
            "name": "holdout_role",
            "type": "string",
            "allowed_values": ["DEVELOPMENT", "HOLDOUT"],
            "description": "Primary dataset partition role",
        },
    ]

    for k in range(n_folds):
        columns_spec.append(
            {
                "name": f"fold_{k}",
                "type": "string",
                "allowed_values": ["TRAIN", "VAL", "EXCLUDED"],
                "description": f"Role in cross-validation fold {k}",
            }
        )

    payload = {
        "plan_id": plan.plan_id,
        "n_folds": n_folds,
        "n_development": len(plan.development_ids),
        "n_holdout": len(plan.holdout_ids),
        "n_total": len(plan.development_ids) + len(plan.holdout_ids),
        "columns": columns_spec,
    }

    write_json_atomic(path, payload, overwrite=overwrite)
