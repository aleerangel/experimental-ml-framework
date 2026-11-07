"""Atomic storage utilities and robust JSON serialization.

Complies with STORE-01, STORE-07, CA-GER-01, and ADR-008.
"""

from __future__ import annotations

from enum import Enum
import json
import math
import os
from pathlib import Path
import tempfile
from types import MappingProxyType
from typing import Any

import numpy as np

from experimental_ml.core.findings import ConfigurationError


def _json_default(obj: Any) -> Any:
    """Fallback encoder converting framework types into standard JSON primitives."""
    if isinstance(obj, MappingProxyType):
        return dict(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (set, frozenset)):
        return sorted(list(obj))
    if isinstance(obj, tuple):
        return list(obj)
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            raise ValueError(f"Out of range float value is not JSON compliant: {val}")
        return val
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def write_json_atomic(
    path: Path | str,
    payload: Any,
    *,
    overwrite: bool = False,
    indent: int = 2,
) -> None:
    """Write payload as formatted UTF-8 JSON atomically with overwrite protection.

    Writes to a temporary file in the target directory, flushes, fsyncs, and atomically
    renames via os.replace. If the write or serialization fails, the temporary file is
    removed, leaving the target path untouched or absent (STORE-01).

    Args:
        path: Destination file path.
        payload: Python object serializable to JSON (RFC 8259).
        overwrite: If False, raises ConfigurationError if destination already exists (STORE-07).
        indent: Indentation level for pretty-printing (default: 2).

    Raises:
        ConfigurationError: If path exists and overwrite=False.
        ValueError: If payload contains NaN, Infinity, or unsupported floats.
        OSError: If an operating system I/O error occurs.
    """
    dest_path = Path(path).resolve()

    if dest_path.exists() and not overwrite:
        raise ConfigurationError(
            f"Target artifact already exists and overwrite is False: '{dest_path}'"
        )

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=dest_path.parent,
        delete=False,
        prefix=f".tmp_{dest_path.name}_",
    )
    temp_path = Path(temp_file.name)

    try:
        json.dump(
            payload,
            temp_file,
            indent=indent,
            ensure_ascii=False,
            allow_nan=False,
            default=_json_default,
        )
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


def read_json(path: Path | str) -> Any:
    """Read and decode a JSON document from disk using UTF-8 encoding.

    Args:
        path: Path to the JSON file.

    Returns:
        Decoded Python object.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    src_path = Path(path).resolve()
    with open(src_path, "r", encoding="utf-8") as f:
        return json.load(f)
