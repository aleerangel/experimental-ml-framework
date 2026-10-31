"""Main command-line entrypoint for experimental-ml-framework."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from experimental_ml import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the base command-line argument parser."""
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the CLI dispatcher."""
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()

    # If no arguments provided, display help and exit with code 0 (Edge Case requirement)
    if not argv:
        parser.print_help()
        return 0

    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())

