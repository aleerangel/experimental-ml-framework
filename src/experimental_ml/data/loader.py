"""Dataset loader with deep memory isolation, buffer immutability and tripartite hashing.

Provides load_dataset and build_immutable_column for tabular files and in-memory structures,
guaranteeing complete data ownership and compliance with ADR-007, ADR-008, RF1.1 and RF1.7.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence
import unicodedata
import numpy as np

from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.core.hashing import config_hash, dataset_hash as core_dataset_hash
from experimental_ml.data.parsing import detect_delimiter, parse_tabular_text
from experimental_ml.data.schema import DatasetSchemaSpec
from experimental_ml.data.types import ColumnDescriptor, DatasetBundle
from experimental_ml.data.validation import (
    assign_or_validate_observation_ids,
    derive_column_descriptor,
    validate_dataset_schema,
)


def _is_int_string(s: str) -> bool:
    """Check if string represents an integer."""
    if not s:
        return False
    if s[0] in ("+", "-"):
        return s[1:].isdigit()
    return s.isdigit()


def _is_float_string(s: str) -> bool:
    """Check if string represents a floating point number."""
    if not s:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_bool_value(v: Any) -> bool:
    """Check if value is a boolean or boolean string."""
    if isinstance(v, (bool, np.bool_)):
        return True
    if isinstance(v, str) and v.lower() in ("true", "false"):
        return True
    return False


def _coerce_column_values(values: Sequence[Any]) -> tuple[np.ndarray, str, int]:
    """Infer physical type and build an immutable array with missing values preserved.

    Returns:
        tuple of (immutable_array, physical_type_str, null_count)
    """
    n = len(values)
    null_count = 0
    non_null_vals: list[Any] = []

    for v in values:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            null_count += 1
        else:
            non_null_vals.append(v)

    if not non_null_vals:
        # All nulls: object array
        arr = np.empty(n, dtype=object)
        arr[:] = None
        arr.flags.writeable = False
        return arr, "object", null_count

    # Check if boolean
    all_bool = all(_is_bool_value(v) for v in non_null_vals)
    if all_bool:
        if null_count == 0:
            bool_vals = [
                bool(v) if isinstance(v, (bool, np.bool_)) else (str(v).lower() == "true")
                for v in values
            ]
            temp = np.array(bool_vals, dtype=np.bool_)
            immutable = np.frombuffer(temp.tobytes(), dtype=np.bool_)
            return immutable, "bool", 0
        else:
            # Nullable boolean stored as object array
            arr = np.empty(n, dtype=object)
            for i, v in enumerate(values):
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    arr[i] = None
                elif isinstance(v, (bool, np.bool_)):
                    arr[i] = bool(v)
                else:
                    arr[i] = str(v).lower() == "true"
            arr.flags.writeable = False
            return arr, "object", null_count

    # Check if numeric (integer or float)
    all_numeric = True
    all_int = True

    for v in non_null_vals:
        if isinstance(v, (bool, np.bool_)):
            all_numeric = False
            all_int = False
            break
        elif isinstance(v, (int, np.integer)):
            continue
        elif isinstance(v, (float, np.floating)):
            all_int = False
        elif isinstance(v, str):
            if _is_int_string(v):
                continue
            elif _is_float_string(v):
                all_int = False
            else:
                all_numeric = False
                all_int = False
                break
        else:
            all_numeric = False
            all_int = False
            break

    if all_numeric:
        if all_int and null_count == 0:
            int_vals = [int(v) for v in values]
            temp = np.array(int_vals, dtype=np.int64)
            immutable = np.frombuffer(temp.tobytes(), dtype=np.int64)
            return immutable, "int64", 0
        else:
            # Float64 (or integer with nulls represented as np.nan)
            float_vals = [
                np.nan if (v is None or (isinstance(v, float) and math.isnan(v))) else float(v)
                for v in values
            ]
            temp = np.array(float_vals, dtype=np.float64)
            immutable = np.frombuffer(temp.tobytes(), dtype=np.float64)
            return immutable, "float64", null_count

    # Object / String column: validate no mutable objects (DATA-10)
    arr = np.empty(n, dtype=object)
    for i, v in enumerate(values):
        if v is None or (isinstance(v, float) and math.isnan(v)):
            arr[i] = None
        elif isinstance(v, (list, dict, set, bytearray)):
            raise DataIntegrityError(
                f"Column contains mutable object of type '{type(v).__name__}' at index {i}"
            )
        elif isinstance(v, str):
            arr[i] = unicodedata.normalize("NFC", v)
        else:
            # Immutable scalar (int, float, bool, np.generic)
            arr[i] = v

    arr.flags.writeable = False
    return arr, "object", null_count


def load_dataset(
    source: Any,
    schema: DatasetSchemaSpec,
    *,
    delimiter: str | None = None,
    has_header: bool = True,
    column_names: Sequence[str] | None = None,
    encoding: str = "utf-8",
) -> DatasetBundle:
    """Load a tabular dataset into an immutable DatasetBundle with exclusive data ownership.

    Accepts file paths (.csv, .txt, .tsv) or in-memory structures (dict, 2D ndarray, DataFrame).
    Guarantees deep memory isolation, bytes-buffer immutability and tripartite audit hashes.

    Raises:
        FileNotFoundError: If source path does not exist.
        DataIntegrityError: On parsing, encoding, structural or immutability violations.
    """
    source_path_str: str | None = None
    is_file_source = isinstance(source, (str, Path))

    if is_file_source:
        source_path = Path(source)
        if not source_path.exists() or source_path.is_dir():
            raise FileNotFoundError(f"Dataset file not found or is a directory: {source_path}")

        source_path_str = str(source_path.resolve())

        try:
            with open(source_path, mode="r", encoding=encoding, newline="") as f:
                sample_lines = [f.readline() for _ in range(100)]
                sample_lines = [line for line in sample_lines if line != ""]
        except UnicodeDecodeError as err:
            raise DataIntegrityError(
                f"Failed to decode tabular file '{source_path}' with encoding '{encoding}': {err}"
            ) from err

        if delimiter is None:
            effective_delimiter = detect_delimiter(sample_lines)
        else:
            effective_delimiter = delimiter

        with open(source_path, mode="r", encoding=encoding, newline="") as f:
            parsed_col_names, raw_columns_dict = parse_tabular_text(
                f,
                delimiter=effective_delimiter,
                has_header=has_header,
                column_names=column_names,
            )

    else:
        # Extract column names and columns dictionary from in-memory source
        if hasattr(source, "columns") and hasattr(source, "__getitem__"):
            # Duck-typed DataFrame
            parsed_col_names = tuple(unicodedata.normalize("NFC", str(c).strip()) for c in source.columns)
            raw_columns_dict = {
                col: list(source[orig_c])
                for col, orig_c in zip(parsed_col_names, source.columns)
            }
        elif isinstance(source, Mapping):
            parsed_col_names = tuple(unicodedata.normalize("NFC", str(k).strip()) for k in source.keys())
            raw_columns_dict = {
                col: list(source[orig_k])
                for col, orig_k in zip(parsed_col_names, source.keys())
            }
        elif isinstance(source, np.ndarray) and source.ndim == 2:
            n_rows_arr, n_cols_arr = source.shape
            if column_names is not None:
                if len(column_names) != n_cols_arr:
                    raise DataIntegrityError(
                        f"Specified column_names length ({len(column_names)}) does not match "
                        f"ndarray column count ({n_cols_arr})"
                    )
                parsed_col_names = tuple(unicodedata.normalize("NFC", str(c).strip()) for c in column_names)
            else:
                parsed_col_names = tuple(f"col_{j}" for j in range(n_cols_arr))

            raw_columns_dict = {
                col: list(source[:, j])
                for j, col in enumerate(parsed_col_names)
            }
        elif isinstance(source, Sequence) and len(source) > 0 and isinstance(source[0], Mapping):
            keys = list(source[0].keys())
            parsed_col_names = tuple(unicodedata.normalize("NFC", str(k).strip()) for k in keys)
            raw_columns_dict = {
                col: [row.get(orig_k) for row in source]
                for col, orig_k in zip(parsed_col_names, keys)
            }
        else:
            raise DataIntegrityError(f"Unsupported in-memory source type: {type(source).__name__}")

    # Determine n_rows
    if parsed_col_names:
        n_rows = len(raw_columns_dict[parsed_col_names[0]])
        for col_name in parsed_col_names:
            if len(raw_columns_dict[col_name]) != n_rows:
                raise DataIntegrityError(
                    f"Inconsistent column length in column '{col_name}': expected {n_rows}, "
                    f"got {len(raw_columns_dict[col_name])}"
                )
    else:
        n_rows = 0

    # Validate schema against dataset structural consistency
    valid_col_names, feature_cols = validate_dataset_schema(parsed_col_names, n_rows, schema)

    # Assign or validate ObservationIds
    observation_ids = assign_or_validate_observation_ids(
        raw_columns_dict, n_rows, schema.observation_id_col
    )

    # Build immutable columns and descriptors (validates scalar immutability)
    immutable_columns: dict[str, np.ndarray] = {}
    descriptors: dict[str, ColumnDescriptor] = {}
    total_memory_bytes = 0

    for idx, col_name in enumerate(valid_col_names):
        col_vals = raw_columns_dict[col_name]
        arr, phys_type, n_missing = _coerce_column_values(col_vals)
        immutable_columns[col_name] = arr
        col_bytes = arr.nbytes
        total_memory_bytes += col_bytes

        # Determine role
        if col_name == schema.target_col:
            role = "target"
        elif col_name == schema.group_col:
            role = "group"
        elif col_name == schema.observation_id_col:
            role = "observation_id"
        elif col_name == schema.time_col:
            role = "time"
        elif col_name in schema.ignore_cols:
            role = "ignored"
        else:
            role = "feature"

        desc = derive_column_descriptor(
            name=col_name,
            index=idx,
            role=role,
            physical_type=phys_type,
            n_missing=n_missing,
            memory_bytes=col_bytes,
            schema=schema,
        )
        descriptors[col_name] = desc

    # Compute raw_source_hash
    if is_file_source:
        assert source_path_str is not None
        raw_source_hash = core_dataset_hash(source_path_str, schema)
    else:
        raw_source_hash = core_dataset_hash(source, schema)

    # Compute canonical in-memory dataset_hash (DATA-13)
    dataset_hash_val = core_dataset_hash(immutable_columns, schema)
    schema_hash_val = config_hash(schema)

    return DatasetBundle(
        schema=schema,
        n_rows=n_rows,
        n_cols=len(valid_col_names),
        column_names=valid_col_names,
        feature_cols=feature_cols,
        columns=MappingProxyType(immutable_columns),
        descriptors=MappingProxyType(descriptors),
        observation_ids=observation_ids,
        dataset_hash=dataset_hash_val,
        raw_source_hash=raw_source_hash,
        schema_hash=schema_hash_val,
        memory_bytes=total_memory_bytes,
        source_path=source_path_str,
    )
