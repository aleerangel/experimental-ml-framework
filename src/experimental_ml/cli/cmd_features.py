"""Command handlers for 'expml features' subcommands.

Complies with CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11, and ARQUITETURA §2.4.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.features.exploration import explore_features
from experimental_ml.stages.stage_gates import (
    EXPLORATORY_FEATURES_REL_PATH,
    reconstruct_sanitized_view,
)


def handle_features_explore(args: argparse.Namespace) -> int:
    """Execute exploratory feature analysis and save reports/exploratory_features.json.

    Args:
        args: Parsed CLI arguments containing experiment_dir and optional force flag.

    Returns:
        0 on success, non-zero on failure.
    """
    experiment_dir = Path(args.experiment_dir).resolve()
    if not experiment_dir.exists():
        raise ConfigurationError(f"Experiment directory not found at '{experiment_dir}'")

    report_path = experiment_dir / EXPLORATORY_FEATURES_REL_PATH
    if report_path.exists() and not getattr(args, "force", False):
        raise ConfigurationError(
            f"Exploratory features report already exists at '{report_path}'. "
            "Use --force to overwrite."
        )

    # Reconstruct sanitized view from experiment layout
    view = reconstruct_sanitized_view(experiment_dir)

    # Execute exploratory feature analysis
    report = explore_features(view)

    # Persist report atomically
    report_dict = report.to_dict()
    write_json_atomic(report_path, report_dict, overwrite=True)

    # Format summary to stdout
    target_info = view.schema.target_col
    n_assocs = len(report.target_associations)
    n_redundant = len(report.high_redundancy_pairs)

    sys.stdout.write(
        f"Exploratory feature analysis completed successfully:\n"
        f"  - Target column: {target_info}\n"
        f"  - Features analyzed: {n_assocs}\n"
        f"  - Redundant pairs flagged: {n_redundant}\n"
        f"  - Report: {report_path.relative_to(experiment_dir)}\n"
    )

    return 0


def handle_features_scenarios(args: argparse.Namespace) -> int:
    """Execute scenarios validation and save configuration/scenarios.json.

    (Will be implemented in T2)
    """
    raise NotImplementedError("Features scenarios subcommand will be implemented in T2")


def handle_features_verify(args: argparse.Namespace) -> int:
    """Execute feature scenarios gate verification.

    (Will be implemented in T2)
    """
    raise NotImplementedError("Features verify subcommand will be implemented in T2")
