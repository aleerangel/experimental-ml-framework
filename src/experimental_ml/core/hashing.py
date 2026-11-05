"""Canonical serialization and hashing for Experimental ML Framework.

Implements ADR-007 compliant canonical hashing for configurations (config_hash)
and tabular datasets (dataset_hash), guaranteeing reproducibility, NFC Unicode
normalization, strict scalar/collection distinction, and platform-independent
byte serialization (RNF01, RNF06, ADR-007).
"""

from __future__ import annotations

import dataclasses
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Any, Mapping, Sequence, Union
import unicodedata

import numpy as np

from experimental_ml.core.findings import ConfigurationError


def is_nan_scalar(val: Any) -> bool:
    """Check if a scalar value is a NaN float (native Python float or NumPy floating).

    Returns False for boolean types (bool, np.bool_) and non-float types.

    Args:
        val: Any value to check.

    Returns:
        True if val is a NaN float scalar, False otherwise.
    """
    if isinstance(val, (bool, np.bool_)):
        return False
    if isinstance(val, float):
        return math.isnan(val)
    if isinstance(val, np.floating):
        return bool(np.isnan(val))
    return False


def is_missing_scalar(val: Any) -> bool:
    """Check if a scalar value represents a missing state (None or NaN scalar).

    Args:
        val: Any value to check.

    Returns:
        True if val is None or a NaN float scalar, False otherwise.
    """
    return val is None or is_nan_scalar(val)


def _canonical_transform(obj: Any, stack: set[int] | None = None) -> Any:
    """Recursively transform an object into canonical JSON-serializable primitives.

    Enforces ADR-007 canonical serialization rules:
    - Unicode NFC normalization for strings and dictionary keys.
    - Strict scalar type differentiation (bool before int, int vs float).
    - Float -0.0 normalization to 0.0, and special float objects for NaN/+Inf/-Inf.
    - Explicit type qualification for tuples, sets, frozensets, and enums.
    - Circular reference detection raising ValueError.
    - Unsupported types raising TypeError.
    """
    if stack is None:
        stack = set()

    # None
    if obj is None:
        return None

    # Booleans (must be checked before integers, as bool is a subclass of int)
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)

    # Integers
    if isinstance(obj, (int, np.integer)):
        return int(obj)

    # Floating point numbers
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        if math.isnan(f):
            return {"__float_special__": "NaN"}
        if math.isinf(f):
            return {"__float_special__": "+Inf" if f > 0 else "-Inf"}
        if f == 0.0:
            f = 0.0
        return f

    # Strings
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)

    # Enums
    if isinstance(obj, Enum):
        return {
            "__type__": obj.__class__.__qualname__,
            "value": _canonical_transform(obj.value, stack),
        }

    # Circular reference check for containers
    obj_id = id(obj)
    if obj_id in stack:
        raise ValueError("Circular reference detected in configuration object")
    stack.add(obj_id)

    try:
        # Dataclasses
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            fields_dict = {f.name: getattr(obj, f.name) for f in dataclasses.fields(obj)}
            return {
                "__type__": obj.__class__.__qualname__,
                "fields": _canonical_transform(fields_dict, stack),
            }

        # Tuples (including NamedTuples)
        if isinstance(obj, tuple):
            return {
                "__type__": "tuple",
                "items": [_canonical_transform(item, stack) for item in obj],
            }

        # Sets and frozensets (sorted by canonical hash of each element)
        if isinstance(obj, (set, frozenset)):
            item_pairs = [
                (config_hash(item), _canonical_transform(item, stack))
                for item in obj
            ]
            item_pairs.sort(key=lambda pair: pair[0])
            return {
                "__type__": "set",
                "items": [pair[1] for pair in item_pairs],
            }

        # Lists
        if isinstance(obj, list):
            return [_canonical_transform(item, stack) for item in obj]

        # Mappings (dictionaries)
        if isinstance(obj, Mapping):
            transformed_items = []
            for k, v in obj.items():
                k_nfc = unicodedata.normalize("NFC", str(k))
                transformed_items.append((k_nfc, _canonical_transform(v, stack)))
            # Sort keys lexicographically by UTF-8 bytes
            transformed_items.sort(key=lambda pair: pair[0].encode("utf-8"))
            return dict(transformed_items)

    finally:
        stack.remove(obj_id)

    raise TypeError(
        f"Object of type '{type(obj).__name__}' is not JSON-serializable under ADR-007"
    )


def config_hash(obj: Any) -> str:
    """Calculate the canonical SHA-256 hash of a configuration object.

    Complies with ADR-007:
    - Normalizes strings to Unicode NFC.
    - Sorts dictionary keys lexicographically by UTF-8 bytes.
    - Differentiates bool vs int, int vs float, list vs tuple.
    - Normalizes -0.0 to 0.0 and special floats (NaN, +Inf, -Inf).
    - Normalizes sets by sorting elements according to their canonical hash.

    Args:
        obj: Configuration or metadata object to hash.

    Returns:
        Lowercase 64-character hexadecimal SHA-256 digest.

    Raises:
        ValueError: If circular references are detected.
        TypeError: If an unsupported object type is encountered.
    """
    canonical_repr = _canonical_transform(obj)
    canonical_json = json.dumps(
        canonical_repr,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _hash_column_binary(col: Any, hasher: Any) -> None:
    """Hash a single data column into binary stream using unambiguous typed representations."""
    if hasattr(col, "to_numpy"):
        arr = col.to_numpy()
    elif isinstance(col, np.ndarray):
        arr = col
    else:
        arr = np.asarray(col)

    hasher.update(struct.pack("<Q", len(arr)))
    kind = arr.dtype.kind

    if kind == "f":
        hasher.update(b"float64")
        f_arr = arr.astype("<f8", copy=True)
        # Normalize -0.0 to 0.0
        f_arr[f_arr == 0.0] = 0.0
        # Normalize all NaN variations to standard quiet NaN
        quiet_nan = np.uint64(0x7FF8000000000000).view("<f8")
        f_arr[np.isnan(f_arr)] = quiet_nan
        hasher.update(f_arr.tobytes())
    elif kind in ("i", "u"):
        hasher.update(b"int64")
        i_arr = arr.astype("<i8", copy=True)
        hasher.update(i_arr.tobytes())
    elif kind == "b":
        hasher.update(b"bool")
        b_arr = arr.astype("|u1", copy=True)
        hasher.update(b_arr.tobytes())
    else:
        hasher.update(b"object")
        for item in arr:
            if is_missing_scalar(item):
                hasher.update(b"\x00")
            elif isinstance(item, (bool, np.bool_)):
                hasher.update(b"\x01b" + (b"\x01" if bool(item) else b"\x00"))
            elif isinstance(item, (int, np.integer)):
                try:
                    val_int = int(item)
                    hasher.update(b"\x01i" + struct.pack("<q", val_int))
                except OverflowError:
                    s_int = str(item).encode("ascii")
                    hasher.update(b"\x01I" + struct.pack("<Q", len(s_int)) + s_int)
            elif isinstance(item, (float, np.floating)):
                f_val = float(item)
                if f_val == 0.0:
                    f_val = 0.0
                f_bytes = struct.pack("<d", f_val)
                hasher.update(b"\x01f" + f_bytes)
            elif isinstance(item, (bytes, np.bytes_)):
                raw_b = bytes(item)
                hasher.update(b"\x01y" + struct.pack("<Q", len(raw_b)) + raw_b)
            elif isinstance(item, (str, np.str_)):
                s_nfc = unicodedata.normalize("NFC", str(item)).encode("utf-8")
                hasher.update(b"\x01s" + struct.pack("<Q", len(s_nfc)) + s_nfc)
            else:
                raise ConfigurationError(
                    f"Scalar value of type '{type(item).__name__}' is not supported for canonical tabular hashing"
                )


def _hash_in_memory_tabular(
    data: Any,
    schema: Any | None,
    hasher: Any,
    *,
    observation_ids: Sequence[Any] | None = None,
) -> None:
    """Compute deterministic binary digest of in-memory tabular data without ambiguities."""
    # 1. Schema frame
    if schema is not None:
        hasher.update(b"\x01" + config_hash(schema).encode("ascii"))
    else:
        hasher.update(b"\x00")

    # 2. Observation IDs frame
    if observation_ids is not None:
        if isinstance(observation_ids, (str, bytes, bytearray, memoryview)) or not isinstance(
            observation_ids, Sequence
        ):
            raise ConfigurationError(
                "observation_ids must be a non-string Sequence of identifiers"
            )
        hasher.update(b"\x01" + struct.pack("<Q", len(observation_ids)))
        for oid in observation_ids:
            if oid is None or not isinstance(oid, str):
                raise ConfigurationError(
                    f"observation_id element must be a non-empty string identifier, got {type(oid).__name__}"
                )
            oid_bytes = str(oid).encode("utf-8")
            hasher.update(struct.pack("<Q", len(oid_bytes)) + oid_bytes)
    else:
        hasher.update(b"\x00")

    # 3. Tabular columns framing
    # Pandas DataFrame or duck-typed tabular object
    if hasattr(data, "columns") and hasattr(data, "__getitem__"):
        cols = list(data.columns)
        hasher.update(b"TABULAR" + struct.pack("<Q", len(cols)))
        for col in cols:
            col_name_nfc = unicodedata.normalize("NFC", str(col)).encode("utf-8")
            hasher.update(struct.pack("<Q", len(col_name_nfc)) + col_name_nfc)
            _hash_column_binary(data[col], hasher)
        return

    # Mapping of column names to columns
    if isinstance(data, Mapping):
        hasher.update(b"TABULAR" + struct.pack("<Q", len(data)))
        for k in data.keys():
            col_name_nfc = unicodedata.normalize("NFC", str(k)).encode("utf-8")
            hasher.update(struct.pack("<Q", len(col_name_nfc)) + col_name_nfc)
            _hash_column_binary(data[k], hasher)
        return

    # 2D NumPy array
    if isinstance(data, np.ndarray) and data.ndim == 2:
        n_rows, n_cols = data.shape
        hasher.update(b"TABULAR" + struct.pack("<Q", n_cols))
        for j in range(n_cols):
            col_name_bytes = f"col_{j}".encode("utf-8")
            hasher.update(struct.pack("<Q", len(col_name_bytes)) + col_name_bytes)
            _hash_column_binary(data[:, j], hasher)
        return

    # Sequence of row records (list of dicts)
    if isinstance(data, Sequence) and len(data) > 0 and isinstance(data[0], Mapping):
        keys = list(data[0].keys())
        hasher.update(b"TABULAR" + struct.pack("<Q", len(keys)))
        for k in keys:
            col_name_nfc = unicodedata.normalize("NFC", str(k)).encode("utf-8")
            hasher.update(struct.pack("<Q", len(col_name_nfc)) + col_name_nfc)
            col_vals = [row.get(k) for row in data]
            _hash_column_binary(col_vals, hasher)
        return

    # Fallback to single column array if 1D sequence or 1D array
    hasher.update(b"TABULAR" + struct.pack("<Q", 1))
    col_name_bytes = b"col_0"
    hasher.update(struct.pack("<Q", len(col_name_bytes)) + col_name_bytes)
    _hash_column_binary(data, hasher)


def dataset_hash(
    data_or_path: Union[str, Path, Any],
    schema: Any | None = None,
    *,
    observation_ids: Sequence[Any] | None = None,
) -> str:
    """Compute the structural integrity hash of a dataset.

    Complies with ADR-007:
    - For files on disk (.csv, .txt): computes SHA-256 of raw file bytes combined
      with schema and observation_ids frames (if provided).
    - For in-memory tabular datasets: computes a deterministic binary digest across
      columns and observations using little-endian buffers, NFC text, column lengths,
      typed scalar tags, and observation IDs.
    - Preserves architectural boundary: does not import or couple to dataset bundle classes.
    - Raises FileNotFoundError if a file path is provided but does not exist.

    Args:
        data_or_path: Path to dataset file on disk, or in-memory tabular data structure.
        schema: Optional schema specification to bind into the hash.
        observation_ids: Optional sequence of observation identifiers to bind into the hash.

    Returns:
        Lowercase 64-character hexadecimal SHA-256 digest.

    Raises:
        FileNotFoundError: If a file path is passed but does not exist on disk.
        ConfigurationError: If observation_ids structure or scalar types are invalid.
    """
    hasher = hashlib.sha256()

    # Check if data_or_path is a path on disk or intended as a file path
    is_path_type = isinstance(data_or_path, Path)
    is_string_path = isinstance(data_or_path, str) and (
        Path(data_or_path).is_file()
        or Path(data_or_path).suffix in (".csv", ".txt", ".tsv", ".gz")
        or "/" in data_or_path
        or "\\" in data_or_path
        or not any(c in data_or_path for c in "\n\r")
    )

    if is_path_type or is_string_path:
        file_path = Path(data_or_path)
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Dataset file not found: {data_or_path}")

        # 1. Schema frame
        if schema is not None:
            hasher.update(b"\x01" + config_hash(schema).encode("ascii"))
        else:
            hasher.update(b"\x00")

        # 2. Observation IDs frame
        if observation_ids is not None:
            if isinstance(observation_ids, (str, bytes, bytearray, memoryview)) or not isinstance(
                observation_ids, Sequence
            ):
                raise ConfigurationError(
                    "observation_ids must be a non-string Sequence of identifiers"
                )
            hasher.update(b"\x01" + struct.pack("<Q", len(observation_ids)))
            for oid in observation_ids:
                if oid is None or not isinstance(oid, str):
                    raise ConfigurationError(
                        f"observation_id element must be a non-empty string identifier, got {type(oid).__name__}"
                    )
                oid_bytes = str(oid).encode("utf-8")
                hasher.update(struct.pack("<Q", len(oid_bytes)) + oid_bytes)
        else:
            hasher.update(b"\x00")

        # 3. Raw file stream
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)

        return hasher.hexdigest()

    # In-memory tabular data
    _hash_in_memory_tabular(data_or_path, schema, hasher, observation_ids=observation_ids)
    return hasher.hexdigest()

