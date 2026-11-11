"""Atomic storage and loading utilities for ModelsCatalog (Stage 3).

Complies with MPC-03, STORE-03, and STORE-05.
"""

from __future__ import annotations

from pathlib import Path

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import read_json, write_json_atomic
from experimental_ml.models.catalog import ModelsCatalog

__all__ = [
    "save_models_catalog",
    "load_models_catalog",
]


def save_models_catalog(
    catalog: ModelsCatalog,
    path: Path | str,
    overwrite: bool = False,
) -> Path:
    """Save a ModelsCatalog atomically to disk in JSON format.

    Parameters
    ----------
    catalog:
        The validated ModelsCatalog to persist.
    path:
        Destination file path.
    overwrite:
        Whether to overwrite an existing destination file.

    Returns
    -------
    Path
        Resolved destination path.

    Raises
    ------
    ConfigurationError
        If destination exists and overwrite=False, or if catalog is invalid.
    """
    if not isinstance(catalog, ModelsCatalog):
        raise ConfigurationError(
            f"Expected ModelsCatalog instance, got {type(catalog).__name__}"
        )

    dest_path = Path(path).resolve()
    if dest_path.exists() and not overwrite:
        raise ConfigurationError(
            f"Models catalog already exists at '{dest_path}'. Use overwrite=True to replace."
        )

    payload = catalog.to_dict()
    write_json_atomic(dest_path, payload, overwrite=overwrite)
    return dest_path


def load_models_catalog(path: Path | str) -> ModelsCatalog:
    """Load and validate a ModelsCatalog from a JSON file.

    Parameters
    ----------
    path:
        Path to the models JSON file.

    Returns
    -------
    ModelsCatalog
        Reconstructed and validated ModelsCatalog.

    Raises
    ------
    ConfigurationError
        If file does not exist or payload is invalid.
    """
    src_path = Path(path).resolve()
    if not src_path.exists():
        raise ConfigurationError(f"Models catalog file not found at '{src_path}'")

    data = read_json(src_path)
    return ModelsCatalog.from_dict(data)
