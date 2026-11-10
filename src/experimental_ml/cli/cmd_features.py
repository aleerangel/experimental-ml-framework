"""Command handlers for 'expml features' subcommands.

Complies with CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11, and ARQUITETURA §2.4.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import read_json, write_json_atomic
from experimental_ml.features.exploration import explore_features
from experimental_ml.features.scenarios import (
    FeatureScenario,
    save_scenarios,
    validate_scenarios,
)
from experimental_ml.stages.stage_gates import (
    EXPLORATORY_FEATURES_REL_PATH,
    SCENARIOS_CATALOG_REL_PATH,
    reconstruct_sanitized_view,
    verify_scenarios_gate,
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
    """Validate feature scenarios against sanitized view and save configuration/scenarios.json.

    Args:
        args: Parsed CLI arguments containing experiment_dir, scenarios, and optional force.

    Returns:
        0 on success, non-zero on error.
    """
    experiment_dir = Path(args.experiment_dir).resolve()
    if not experiment_dir.exists():
        raise ConfigurationError(f"Experiment directory not found at '{experiment_dir}'")

    scenarios_path = Path(args.scenarios).resolve()
    if not scenarios_path.exists():
        raise ConfigurationError(f"Scenarios file not found at '{scenarios_path}'")

    scenarios_data = read_json(scenarios_path)
    if isinstance(scenarios_data, list):
        raw_scenarios = scenarios_data
    elif isinstance(scenarios_data, dict) and "scenarios" in scenarios_data:
        raw_scenarios = scenarios_data["scenarios"]
    else:
        raise ConfigurationError(
            "Scenarios file must contain a JSON list of scenario objects or a dictionary with 'scenarios' key"
        )

    scenarios = [FeatureScenario.from_dict(item) for item in raw_scenarios]

    view = reconstruct_sanitized_view(experiment_dir)
    catalog = validate_scenarios(scenarios, view)

    dest_path = experiment_dir / SCENARIOS_CATALOG_REL_PATH
    save_scenarios(catalog, dest_path, overwrite=getattr(args, "force", False))

    sys.stdout.write(
        f"Feature scenarios validated and saved successfully:\n"
        f"  - Scenarios validated: {len(catalog.scenarios)}\n"
        f"  - Catalog: {dest_path.relative_to(experiment_dir)}\n"
    )
    return 0


def handle_features_verify(args: argparse.Namespace) -> int:
    """Verify feature scenarios stage gate.

    Args:
        args: Parsed CLI arguments containing experiment_dir.

    Returns:
        0 on success, non-zero on error.
    """
    experiment_dir = Path(args.experiment_dir).resolve()
    if not experiment_dir.exists():
        raise ConfigurationError(f"Experiment directory not found at '{experiment_dir}'")

    catalog = verify_scenarios_gate(experiment_dir)

    sys.stdout.write(
        f"Feature scenarios gate verified successfully:\n"
        f"  - Scenarios count: {len(catalog.scenarios)}\n"
        f"  - Catalog: {SCENARIOS_CATALOG_REL_PATH}\n"
    )
    return 0
