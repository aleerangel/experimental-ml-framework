"""Main command-line entrypoint for experimental-ml-framework.

Complies with CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11, and ARQUITETURA §2.4.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from experimental_ml import __version__
from experimental_ml.core.findings import ExperimentalMLError


class _ExpMLParser(argparse.ArgumentParser):
    """ArgumentParser enforcing at least one of --run-dir or --experiment-dir when configured."""

    def parse_known_args(self, args=None, namespace=None):  # type: ignore[override]
        ns, rest = super().parse_known_args(args, namespace)
        if getattr(self, "_require_run_or_exp", False):
            if not getattr(ns, "run_dir", None) and not getattr(ns, "experiment_dir", None):
                self.error("one of the arguments --run-dir or --experiment-dir is required")
        return ns, rest


def _add_csv_format_args(p: argparse.ArgumentParser) -> None:
    """Register optional CSV formatting flags on a subcommand parser."""
    p.add_argument(
        "--delimiter",
        default=None,
        help="CSV column delimiter (',', ';', '\\t', '|', 'whitespace'). Auto-detected if omitted.",
    )
    p.add_argument(
        "--decimal",
        choices=[".", ",", "auto"],
        default=None,
        help="Decimal separator ('.', ',', or 'auto').",
    )
    p.add_argument(
        "--encoding",
        default=None,
        help="File character encoding (e.g., 'utf-8-sig', 'latin-1', 'cp1252', or 'auto').",
    )
    p.add_argument(
        "--no-header",
        action="store_true",
        default=False,
        help="Treat the first row as data instead of column headers.",
    )
    p.add_argument(
        "--column-names",
        nargs="+",
        default=None,
        help="Explicit column names (typically used with --no-header).",
    )
    p.add_argument(
        "--quotechar",
        default=None,
        help="Single-character quote delimiter (default: '\"').",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the hierarchical command-line argument parser."""
    parser = _ExpMLParser(
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

    # --- init command ---
    init_p = subparsers.add_parser("init", help="Create a starter experiment directory with example CSV and JSON configs.")
    init_p.add_argument("--output-dir", required=True, help="Destination directory for starter project.")
    init_p.add_argument(
        "--task",
        choices=["regression", "binary_classification", "multiclass_classification"],
        default="regression",
        help="Target task type for starter templates (default: regression).",
    )
    init_p.add_argument("--force", action="store_true", help="Overwrite existing starter files.")

    # --- quickrun command ---
    qr_p = subparsers.add_parser("quickrun", help="Run Stages 1-6 sequentially from an initialized experiment directory.")
    qr_p.add_argument("--experiment-dir", "--exp-dir", dest="experiment_dir", required=True, help="Path to initialized experiment directory.")
    qr_p.add_argument("--data", default=None, help="Optional custom CSV path (default: <experiment-dir>/dados_exemplo.csv).")
    qr_p.add_argument("--metrics", nargs="+", default=None, help="Optional list of metric IDs to evaluate.")
    qr_p.add_argument(
        "--collect-train-metrics",
        action="store_true",
        default=False,
        help="Opt-in: evaluate training metrics per fold for Train vs. Test diagnostics.",
    )
    qr_p.add_argument("--force", action="store_true", default=True, help="Overwrite existing outputs (default: True).")
    _add_csv_format_args(qr_p)

    # --- data command ---
    data_parser = subparsers.add_parser("data", help="Data ingestion, profiling and sanitization.")
    data_subparsers = data_parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    # data profile
    profile_p = data_subparsers.add_parser("profile", help="Ingest and profile a tabular dataset.")
    profile_p.add_argument("--data", required=True, help="Path to input tabular data file.")
    profile_p.add_argument("--schema", required=True, help="Path to schema JSON file.")
    profile_p.add_argument("--output-dir", required=True, help="Path to output experiment directory.")
    profile_p.add_argument("--force", action="store_true", help="Overwrite existing output artifacts.")
    _add_csv_format_args(profile_p)

    # data sanitize
    sanitize_p = data_subparsers.add_parser("sanitize", help="Apply preparation rules and create sanitized view.")
    sanitize_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")
    sanitize_p.add_argument("--rules", default=None, help="Optional path to preparation rules JSON file (defaults to [] if no confirmed issues).")
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

    # --- models command ---
    models_parser = subparsers.add_parser("models", help="Model specification, validation and catalog persistence.")
    models_subparsers = models_parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    # models validate
    models_val_p = models_subparsers.add_parser("validate", help="Validate and save models catalog.")
    models_val_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")
    models_val_p.add_argument("--models", required=True, help="Path to models JSON file.")
    models_val_p.add_argument("--force", action="store_true", help="Overwrite existing output artifacts.")

    # models verify
    models_ver_p = models_subparsers.add_parser("verify", help="Verify models stage gate.")
    models_ver_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")

    # --- run command ---
    run_parser = subparsers.add_parser("run", help="Experiment execution, resume, status and stage verification.")
    run_subparsers = run_parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    # run start
    run_start_p = run_subparsers.add_parser("start", help="Execute an experiment matrix and consolidate OOF.")
    run_start_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")
    run_start_p.add_argument("--run-dir", default=None, help="Optional custom run output directory.")
    run_start_p.add_argument(
        "-j", "--jobs", "--parallel",
        dest="parallel",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1).",
    )
    run_start_p.add_argument(
        "--error-policy",
        choices=["fault_tolerant", "fail_fast"],
        default="fault_tolerant",
        help="Cell failure handling policy (default: fault_tolerant).",
    )
    run_start_p.add_argument(
        "--no-oof",
        action="store_true",
        help="Disable automatic out-of-fold predictions consolidation.",
    )
    run_start_p.add_argument(
        "--metrics",
        nargs="+",
        default=None,
        help="Optional list of metric IDs from METRICS_CATALOG (defaults to task-appropriate metrics).",
    )
    run_start_p.add_argument(
        "--collect-train-metrics",
        action="store_true",
        default=False,
        help="Opt-in: evaluate training metrics per fold for Train vs. Test diagnostics.",
    )
    run_start_p.add_argument("--force", action="store_true", help="Overwrite existing execution directory if present.")

    # run resume
    run_resume_p = run_subparsers.add_parser("resume", help="Resume an interrupted experiment execution.")
    run_resume_p._require_run_or_exp = True  # type: ignore[attr-defined]
    run_resume_p.add_argument("--run-dir", default=None, help="Path to run directory containing execution_state.json.")
    run_resume_p.add_argument(
        "--experiment-dir", "--exp-dir",
        dest="experiment_dir",
        default=None,
        help="Path to experiment directory (infers <experiment-dir>/runs if --run-dir omitted).",
    )
    run_resume_p.add_argument(
        "-j", "--jobs", "--parallel",
        dest="parallel",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1).",
    )
    run_resume_p.add_argument("--retry-failed", action="store_true", help="Retry previously failed cells.")
    run_resume_p.add_argument(
        "--no-oof",
        action="store_true",
        help="Disable automatic out-of-fold predictions consolidation.",
    )

    # run status
    run_status_p = run_subparsers.add_parser("status", help="Inspect current progress of an experiment execution.")
    status_grp = run_status_p.add_mutually_exclusive_group(required=True)
    status_grp.add_argument("--run-dir", default=None, help="Path to run directory containing execution_state.json.")
    status_grp.add_argument("--experiment-dir", "--exp-dir", dest="experiment_dir", default=None, help="Path to experiment directory (infers <experiment-dir>/runs).")

    # run verify
    run_verify_p = run_subparsers.add_parser("verify", help="Verify stage 4 execution and OOF gates.")
    verify_grp = run_verify_p.add_mutually_exclusive_group(required=True)
    verify_grp.add_argument("--run-dir", default=None, help="Path to run directory containing execution_state.json.")
    verify_grp.add_argument("--experiment-dir", "--exp-dir", dest="experiment_dir", default=None, help="Path to experiment directory (infers <experiment-dir>/runs).")

    # --- stats command ---
    stats_parser = subparsers.add_parser("stats", help="Stage 5 statistical consolidation and inference.")
    stats_subparsers = stats_parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    # stats run
    stats_run_p = stats_subparsers.add_parser("run", help="Run Stage 5 descriptive consolidation and comparisons.")
    stats_run_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")
    stats_run_p.add_argument("--config", default=None, help="Optional path to comparison config JSON.")
    stats_run_p.add_argument("--force", action="store_true", help="Overwrite existing statistics artifacts.")

    # stats status
    stats_status_p = stats_subparsers.add_parser("status", help="Inspect Stage 5 statistics summary.")
    stats_status_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")

    # stats verify
    stats_verify_p = stats_subparsers.add_parser("verify", help="Verify Stage 5 statistics gate.")
    stats_verify_p.add_argument("--experiment-dir", required=True, help="Path to experiment directory.")

    # --- report command ---
    report_parser = subparsers.add_parser("report", help="Stage 6 scientific reporting, packaging, and gate verification.")
    report_subparsers = report_parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    # report generate
    report_gen_p = report_subparsers.add_parser("generate", help="Generate scientific report (Markdown/HTML) read-only.")
    report_gen_p.add_argument("--experiment-dir", "--exp-dir", dest="experiment_dir", required=True, help="Path to experiment directory.")
    report_gen_p.add_argument("--output-dir", default=None, help="Output directory for generated reports (default: <exp-dir>/reports).")
    report_gen_p.add_argument("--format", choices=["markdown", "html", "both"], default="both", help="Report output format.")
    report_gen_p.add_argument("--audience", choices=["FULL_LAB", "ARTICLE_COMPACT", "CUSTOM"], default="FULL_LAB", help="Report audience selection.")
    report_gen_p.add_argument("--families", default=None, help="Comma-separated ReportFamily values (required for CUSTOM audience).")
    report_gen_p.add_argument("--objective", default="", help="Optional researcher scientific objective declaration.")
    report_gen_p.add_argument("--force", action="store_true", help="Overwrite existing report files.")

    # report export
    report_exp_p = report_subparsers.add_parser("export", help="Export full reproducibility package with relative SHA-256 checksums.")
    report_exp_p.add_argument("--experiment-dir", "--exp-dir", dest="experiment_dir", required=True, help="Path to experiment directory.")
    report_exp_p.add_argument("--output-dir", default=None, help="Output package directory (default: <exp-dir>).")
    report_exp_p.add_argument("--mode", choices=["full_package", "reduced_no_raw_data"], default="full_package", help="Reproducibility package mode.")
    report_exp_p.add_argument("--audience", choices=["FULL_LAB", "ARTICLE_COMPACT", "CUSTOM"], default="FULL_LAB", help="Report audience selection.")
    report_exp_p.add_argument("--families", default=None, help="Comma-separated ReportFamily values (required for CUSTOM audience).")
    report_exp_p.add_argument("--objective", default="", help="Optional researcher scientific objective declaration.")
    report_exp_p.add_argument("--force", action="store_true", help="Overwrite existing package files.")

    # report verify
    report_ver_p = report_subparsers.add_parser("verify", help="Verify Stage 6 report integrity gate.")
    report_ver_p.add_argument("--experiment-dir", "--exp-dir", dest="experiment_dir", required=True, help="Path to package or experiment directory.")

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

    if args.command not in {"init", "quickrun"} and getattr(args, "subcommand", None) is None:
        sys.stderr.write(f"Error: subcommand required for '{args.command}'\n")
        return 2

    try:
        if args.command == "init":
            from experimental_ml.cli.cmd_init import handle_init

            return handle_init(args)
        if args.command == "quickrun":
            from experimental_ml.cli.cmd_init import handle_quickrun

            return handle_quickrun(args)
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
        elif args.command == "models":
            from experimental_ml.cli.cmd_models import (
                handle_models_validate,
                handle_models_verify,
            )

            if args.subcommand == "validate":
                return handle_models_validate(args)
            if args.subcommand == "verify":
                return handle_models_verify(args)
        elif args.command == "run":
            from experimental_ml.cli.cmd_run import (
                handle_run_resume,
                handle_run_start,
                handle_run_status,
                handle_run_verify,
            )

            if args.subcommand == "start":
                return handle_run_start(args)
            if args.subcommand == "resume":
                return handle_run_resume(args)
            if args.subcommand == "status":
                return handle_run_status(args)
            if args.subcommand == "verify":
                return handle_run_verify(args)
        elif args.command == "stats":
            from experimental_ml.cli.cmd_stats import (
                handle_stats_run,
                handle_stats_status,
                handle_stats_verify,
            )

            if args.subcommand == "run":
                return handle_stats_run(args)
            if args.subcommand == "status":
                return handle_stats_status(args)
            if args.subcommand == "verify":
                return handle_stats_verify(args)
        elif args.command == "report":
            from experimental_ml.cli.cmd_report import (
                handle_report_export,
                handle_report_generate,
                handle_report_verify,
            )

            if args.subcommand == "generate":
                return handle_report_generate(args)
            if args.subcommand == "export":
                return handle_report_export(args)
            if args.subcommand == "verify":
                return handle_report_verify(args)
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
