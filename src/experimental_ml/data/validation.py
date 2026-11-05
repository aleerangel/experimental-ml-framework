"""Validation of tabular data against DatasetSchemaSpec and ObservationId handling.

Provides assign_or_validate_observation_ids, schema-data consistency checks,
and derivation of ColumnDescriptor instances according to ADR-007 and ADR-008.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence
import unicodedata
import numpy as np

from experimental_ml.core.enums import TaskType
from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.core.types import ObservationId
from experimental_ml.data.schema import ColumnSemanticType, DatasetSchemaSpec
from experimental_ml.data.types import ColumnDescriptor


def assign_or_validate_observation_ids(
    raw_columns: Mapping[str, Sequence[Any]],
    n_rows: int,
    observation_id_col: str | None,
) -> tuple[ObservationId, ...]:
    """Assign or validate ObservationId sequence for the dataset.

    When observation_id_col is None, deterministically generates obs_000000..obs_{N-1}.
    When observation_id_col is provided, validates non-nullness and strict uniqueness.

    Raises:
        DataIntegrityError: On missing values, duplicate IDs, or invalid format.
    """
    if observation_id_col is None:
        return tuple(ObservationId(f"obs_{i:06d}") for i in range(n_rows))

    if observation_id_col not in raw_columns:
        raise DataIntegrityError(
            f"Declared observation_id_col '{observation_id_col}' not found in dataset columns"
        )

    col_values = raw_columns[observation_id_col]
    if len(col_values) != n_rows:
        raise DataIntegrityError(
            f"observation_id_col length ({len(col_values)}) does not match n_rows ({n_rows})"
        )

    seen: set[ObservationId] = set()
    result: list[ObservationId] = []

    for row_idx, val in enumerate(col_values):
        line_num = row_idx + 1
        if val is None or (isinstance(val, float) and math.isnan(val)) or str(val).strip() == "":
            raise DataIntegrityError(
                f"Row {line_num}: observation_id_col '{observation_id_col}' contains missing/null value"
            )

        str_val = unicodedata.normalize("NFC", str(val).strip())
        try:
            obs_id = ObservationId(str_val)
        except Exception as err:
            raise DataIntegrityError(
                f"Row {line_num}: invalid ObservationId format '{str_val}' in column '{observation_id_col}'"
            ) from err

        if obs_id in seen:
            raise DataIntegrityError(
                f"Row {line_num}: duplicate ObservationId '{str_val}' encountered in column '{observation_id_col}'"
            )

        seen.add(obs_id)
        result.append(obs_id)

    return tuple(result)


def derive_column_descriptor(
    name: str,
    index: int,
    role: str,
    physical_type: str,
    n_missing: int,
    memory_bytes: int,
    schema: DatasetSchemaSpec,
) -> ColumnDescriptor:
    """Derive ColumnDescriptor for a column adhering to declared types or neutral defaults."""
    if name in schema.column_semantic_types:
        semantic_type = schema.column_semantic_types[name]
        is_semantic_declared = True
    else:
        is_semantic_declared = False
        # Neutral default fallbacks (DATA-24, AC 3)
        if role == "observation_id":
            semantic_type = ColumnSemanticType.IDENTIFIER
        elif role == "time":
            semantic_type = ColumnSemanticType.TEMPORAL
        elif role == "group":
            semantic_type = ColumnSemanticType.CATEGORICAL
        elif role == "target":
            if schema.task_type == TaskType.REGRESSION:
                if physical_type == "float64":
                    semantic_type = ColumnSemanticType.NUMERIC_CONTINUOUS
                else:
                    semantic_type = ColumnSemanticType.NUMERIC_DISCRETE
            else:  # BINARY_CLASSIFICATION or MULTICLASS_CLASSIFICATION
                if physical_type == "bool":
                    semantic_type = ColumnSemanticType.BOOLEAN
                else:
                    semantic_type = ColumnSemanticType.CATEGORICAL
        else:  # feature or ignored
            if physical_type == "bool":
                semantic_type = ColumnSemanticType.BOOLEAN
            elif physical_type == "float64":
                semantic_type = ColumnSemanticType.NUMERIC_CONTINUOUS
            elif physical_type == "int64":
                semantic_type = ColumnSemanticType.NUMERIC_DISCRETE
            else:
                semantic_type = ColumnSemanticType.CATEGORICAL

    return ColumnDescriptor(
        name=name,
        index=index,
        role=role,
        physical_type=physical_type,
        semantic_type=semantic_type,
        is_semantic_declared=is_semantic_declared,
        n_missing=n_missing,
        memory_bytes=memory_bytes,
    )


def validate_dataset_schema(
    column_names: Sequence[str],
    n_rows: int,
    schema: DatasetSchemaSpec,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Validate tabular structural consistency against DatasetSchemaSpec.

    Verifies:
    - N > 0 and M > 0.
    - No duplicate column names after Unicode NFC normalization.
    - All declared schema columns exist in column_names.
    - All declared column_semantic_types keys exist in column_names.
    - At least one candidate predictor feature column remains (len(feature_cols) >= 1).

    Returns:
        tuple of (normalized_column_names, feature_cols)

    Raises:
        DataIntegrityError: On any structural violation.
    """
    if n_rows <= 0:
        raise DataIntegrityError(f"Dataset has zero rows (N = {n_rows})")

    if not column_names or len(column_names) == 0:
        raise DataIntegrityError("Dataset has zero columns (M = 0)")

    # Normalize column names with NFC and check duplicates
    normalized_cols: list[str] = []
    for col in column_names:
        nfc_col = unicodedata.normalize("NFC", str(col).strip())
        if nfc_col in normalized_cols:
            raise DataIntegrityError(
                f"Duplicate column name '{nfc_col}' encountered after NFC normalization"
            )
        normalized_cols.append(nfc_col)

    cols_set = set(normalized_cols)

    # Verify declared schema columns exist
    missing_cols: list[str] = []
    if schema.target_col not in cols_set:
        missing_cols.append(f"target_col: '{schema.target_col}'")
    if schema.group_col is not None and schema.group_col not in cols_set:
        missing_cols.append(f"group_col: '{schema.group_col}'")
    if schema.observation_id_col is not None and schema.observation_id_col not in cols_set:
        missing_cols.append(f"observation_id_col: '{schema.observation_id_col}'")
    if schema.time_col is not None and schema.time_col not in cols_set:
        missing_cols.append(f"time_col: '{schema.time_col}'")
    for ic in schema.ignore_cols:
        if ic not in cols_set:
            missing_cols.append(f"ignore_cols: '{ic}'")

    if missing_cols:
        raise DataIntegrityError(
            f"Columns declared in DatasetSchemaSpec missing from dataset: {', '.join(missing_cols)}"
        )

    # Verify declared semantic types exist (DATA-24, AC 4)
    for sem_col in schema.column_semantic_types:
        if sem_col not in cols_set:
            raise DataIntegrityError(
                f"Column '{sem_col}' declared in column_semantic_types not found in dataset columns"
            )

    # Partition columns to compute feature_cols
    reserved = {schema.target_col}
    if schema.group_col is not None:
        reserved.add(schema.group_col)
    if schema.observation_id_col is not None:
        reserved.add(schema.observation_id_col)
    if schema.time_col is not None:
        reserved.add(schema.time_col)
    reserved.update(schema.ignore_cols)

    feature_cols = tuple(c for c in normalized_cols if c not in reserved)
    if len(feature_cols) == 0:
        raise DataIntegrityError(
            "Dataset contains zero candidate predictor feature columns (len(feature_cols) == 0)"
        )

    return tuple(normalized_cols), feature_cols
