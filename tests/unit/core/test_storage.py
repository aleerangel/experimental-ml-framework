"""Unit tests for atomic JSON storage (core/storage.py).

Verifies STORE-01, STORE-07 and Checks C1, C7.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
import numpy as np
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import read_json, write_json_atomic


def test_store_01_atomic_write_and_failure_cleanup(tmp_path: Path) -> None:
    """STORE-01 (Check C1): write_json_atomic writes atomically and cleans up on failure."""
    target_file = tmp_path / "subdir" / "valid_artifact.json"
    data = {
        "name": "experiment_1",
        "count": 42,
        "values": [1.5, 2.5, 3.5],
        "mapping": MappingProxyType({"key": "val"}),
    }

    # 1. Successful atomic write
    write_json_atomic(target_file, data)
    assert target_file.exists()

    loaded = read_json(target_file)
    assert loaded["name"] == "experiment_1"
    assert loaded["count"] == 42
    assert loaded["values"] == [1.5, 2.5, 3.5]
    assert loaded["mapping"] == {"key": "val"}

    # Verify no temporary files remain in target directory
    temp_files = list(target_file.parent.glob(".tmp_*"))
    assert len(temp_files) == 0

    # 2. Failure cleanup: object that cannot be serialized or contains NaN
    target_fail = tmp_path / "subdir" / "fail_artifact.json"
    bad_data = {"corrupted": np.nan}

    with pytest.raises(ValueError):
        write_json_atomic(target_fail, bad_data)

    # Destination file should not have been created
    assert not target_fail.exists()
    # Temporary file should have been cleaned up
    temp_files_fail = list(target_file.parent.glob(".tmp_*"))
    assert len(temp_files_fail) == 0

    # 3. Existing destination file remains untouched when subsequent write fails
    original_content = target_file.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        write_json_atomic(target_file, bad_data, overwrite=True)

    assert target_file.read_text(encoding="utf-8") == original_content


def test_store_07_overwrite_protection_configuration_error(tmp_path: Path) -> None:
    """STORE-07 (Check C7): Existing file raises ConfigurationError when overwrite=False."""
    target_file = tmp_path / "protected.json"
    target_file.write_text('{"initial": 1}', encoding="utf-8")

    # Overwrite=False raises ConfigurationError
    with pytest.raises(ConfigurationError, match="Target artifact already exists"):
        write_json_atomic(target_file, {"new": 2}, overwrite=False)

    # Content remained unchanged
    assert read_json(target_file) == {"initial": 1}

    # Overwrite=True succeeds cleanly
    write_json_atomic(target_file, {"new": 2}, overwrite=True)
    assert read_json(target_file) == {"new": 2}


def test_storage_converts_numpy_scalars_and_enums(tmp_path: Path) -> None:
    """Verify numpy integer/floats and enums serialize cleanly to JSON primitives."""
    from enum import Enum

    class DemoEnum(Enum):
        ALPHA = "alpha_val"

    target_file = tmp_path / "types.json"
    payload = {
        "int64": np.int64(100),
        "float64": np.float64(3.14),
        "enum": DemoEnum.ALPHA,
        "ndarray": np.array([1, 2, 3]),
    }

    write_json_atomic(target_file, payload)
    loaded = read_json(target_file)

    assert loaded["int64"] == 100
    assert loaded["float64"] == 3.14
    assert loaded["enum"] == "alpha_val"
    assert loaded["ndarray"] == [1, 2, 3]
