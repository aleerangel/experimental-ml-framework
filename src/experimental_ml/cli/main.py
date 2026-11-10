"""Main command-line entrypoint for experimental-ml-framework.

Complies with CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11, and ARQUITETURA §2.4.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from experimental_ml import __version__
from experimental_ml.core.findings import ExperimentalMLError


def build_parser() -> argparse.ArgumentParser:
    """Build the hierarchical command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="expml",
        description="Experimental ML Framework - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version and exit.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # --- data command ---
    data_parser = subparsers.add_parser("data", help="Data ingestion, profiling and sanitization.")
    data_subparsers = data_parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    # data profile
    profile_p = data_subparsers.add_parser("profile", help="Ingest and profile a tabular dataset.")
    profile_p.add_argument("--data", required=True, help="Path to input tabular data file.")
    profile_p.add_argument("--schema", required=True, help="Path to schema JSON file.")
    profile_p.add_argument("--output-dir", required=True, help="Path to output experiment directory.")
    profile_p.add_argument("--force", action="store_true", help="Overwrite existing output artifacts.")

    # data sanitize
    sanitize_p = data_subparsers.add_parser("sanitize", help="Apply preparation rules and create sanitized view.")
    sanitize_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")
    sanitize_p.add_argument("--rules", required=True, help="Path to preparation rules JSON file.")
    sanitize_p.add_argument("--force", action="store_true", help="Overwrite existing output artifacts.")

    # --- partition command ---
    part_parser = subparsers.add_parser("partition", help="Dataset partitioning and validation.")
    part_subparsers = part_parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    # partition build
    build_p = part_subparsers.add_parser("build", help="Build partition plan and splits matrix.")
    build_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")
    build_p.add_argument("--config", required=True, help="Path to partition config JSON file.")
    build_p.add_argument("--seed", type=int, default=None, help="Optional master seed override.")
    build_p.add_argument("--force", action="store_true", help="Overwrite existing output artifacts.")

    # partition verify
    verify_p = part_subparsers.add_parser("verify", help="Verify partition plan invariants and stage gates.")
    verify_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")

    # --- features command ---
    feat_parser = subparsers.add_parser("features", help="Feature exploration and scenario configuration.")
    feat_subparsers = feat_parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    # features explore
    explore_p = feat_subparsers.add_parser("explore", help="Run exploratory feature analysis.")
    explore_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")
    explore_p.add_argument("--force", action="store_true", help="Overwrite existing output artifacts.")

    # features scenarios
    scenarios_p = feat_subparsers.add_parser("scenarios", help="Validate and save feature scenarios.")
    scenarios_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")
    scenarios_p.add_argument("--scenarios", required=True, help="Path to scenarios JSON file.")
    scenarios_p.add_argument("--force", action="store_true", help="Overwrite existing output artifacts.")

    # features verify
    feat_verify_p = feat_subparsers.add_parser("verify", help="Verify feature scenarios gate.")
    feat_verify_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the CLI dispatcher with unified error trapping and exit code standardization.

    Exit codes:
        0: Successful execution, --help, or empty arguments.
        2: Domain error (ExperimentalMLError), invalid argument, or unmet stage precondition.
        1: Unexpected fatal runtime error.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()

    # Empty arguments display help and exit with code 0 (M1.1 baseline)
    if not argv:
        parser.print_help()
        return 0

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        return code

    if getattr(args, "command", None) is None:
        parser.print_help()
        return 0

    if getattr(args, "subcommand", None) is None:
        sys.stderr.write(f"Error: subcommand required for '{args.command}'\n")
        return 2

    try:
        if args.command == "data":
            from experimental_ml.cli.cmd_data import handle_data_profile, handle_data_sanitize

            if args.subcommand == "profile":
                return handle_data_profile(args)
            if args.subcommand == "sanitize":
                return handle_data_sanitize(args)
        elif args.command == "partition":
            from experimental_ml.cli.cmd_partition import (
                handle_partition_build,
                handle_partition_verify,
            )

            if args.subcommand == "build":
                return handle_partition_build(args)
            if args.subcommand == "verify":
                return handle_partition_verify(args)
        elif args.command == "features":
            from experimental_ml.cli.cmd_features import (
                handle_features_explore,
                handle_features_scenarios,
                handle_features_verify,
            )

            if args.subcommand == "explore":
                return handle_features_explore(args)
            if args.subcommand == "scenarios":
                return handle_features_scenarios(args)
            if args.subcommand == "verify":
                return handle_features_verify(args)
    except ExperimentalMLError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    except Exception as exc:
        sys.stderr.write(f"Unexpected error: {exc}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
