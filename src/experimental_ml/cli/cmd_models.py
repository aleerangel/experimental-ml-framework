"""Command handlers for 'expml models' subcommands.

Complies with CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11, MPC-05, MPC-06, and ARQUITETURA §2.4.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def handle_models_validate(args: argparse.Namespace) -> int:
    """Validate a models definition file and save configuration/models.json atomically.

    Args:
        args: Parsed CLI arguments containing experiment_dir, models, and optional force.

    Returns:
        0 on success, non-zero on error.
    """
    from experimental_ml.core.findings import ConfigurationError, ExperimentalMLError
    from experimental_ml.core.storage import read_json
    from experimental_ml.models.catalog import ModelsCatalog
    from experimental_ml.models.storage import save_models_catalog
    from experimental_ml.stages.stage_gates import (
        MODELS_CATALOG_REL_PATH,
        verify_preparation_gate,
    )

    try:
        experiment_dir = Path(args.experiment_dir).resolve()
        if not experiment_dir.exists():
            raise ConfigurationError(f"Experiment directory not found at '{experiment_dir}'")

        models_path = Path(args.models).resolve()
        if not models_path.exists():
            raise ConfigurationError(f"Models input file not found at '{models_path}'")

        # Upstream Stage 1 precondition check
        verify_preparation_gate(experiment_dir)

        models_data = read_json(models_path)
        if isinstance(models_data, list):
            catalog = ModelsCatalog.from_dict({"models": models_data})
        elif isinstance(models_data, dict):
            catalog = ModelsCatalog.from_dict(models_data)
        else:
            raise ConfigurationError(
                "Models file must contain a JSON list of model objects or a dictionary with 'models' key"
            )

        dest_path = experiment_dir / MODELS_CATALOG_REL_PATH
        save_models_catalog(catalog, dest_path, overwrite=getattr(args, "force", False))

        sys.stdout.write(
            f"Models catalog validated and saved successfully:\n"
            f"  - Models count: {len(catalog.models)}\n"
            f"  - Catalog hash: {catalog.catalog_hash}\n"
            f"  - Destination: {dest_path.relative_to(experiment_dir)}\n"
        )
        return 0
    except ExperimentalMLError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2


def handle_models_verify(args: argparse.Namespace) -> int:
    """Verify models stage gate for the experiment.

    Args:
        args: Parsed CLI arguments containing experiment_dir.

    Returns:
        0 on success, non-zero on error.
    """
    from experimental_ml.core.findings import ConfigurationError, ExperimentalMLError
    from experimental_ml.stages.stage_gates import (
        MODELS_CATALOG_REL_PATH,
        verify_models_gate,
    )

    try:
        experiment_dir = Path(args.experiment_dir).resolve()
        if not experiment_dir.exists():
            raise ConfigurationError(f"Experiment directory not found at '{experiment_dir}'")

        catalog = verify_models_gate(experiment_dir)

        sys.stdout.write(
            f"Models gate verified successfully:\n"
            f"  - Models count: {len(catalog.models)}\n"
            f"  - Catalog hash: {catalog.catalog_hash}\n"
            f"  - Catalog file: {MODELS_CATALOG_REL_PATH}\n"
        )
        return 0
    except ExperimentalMLError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
