"""Command handlers for 'expml run' subcommands.

Complies with CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11, ORCH-22 to ORCH-28, and ARQUITETURA §2.4.
"""

from __future__ import annotations

import argparse


def handle_run_start(args: argparse.Namespace) -> int:
    """Execute an experiment matrix and optionally consolidate OOF predictions.

    Args:
        args: Parsed CLI arguments.

    Returns:
        0 on success, non-zero on error.
    """
    raise NotImplementedError("handle_run_start will be implemented in T2")


def handle_run_resume(args: argparse.Namespace) -> int:
    """Resume an interrupted experiment matrix execution.

    Args:
        args: Parsed CLI arguments.

    Returns:
        0 on success, non-zero on error.
    """
    raise NotImplementedError("handle_run_resume will be implemented in T3")


def handle_run_status(args: argparse.Namespace) -> int:
    """Inspect progress of an experiment matrix execution.

    Args:
        args: Parsed CLI arguments.

    Returns:
        0 on success, non-zero on error.
    """
    raise NotImplementedError("handle_run_status will be implemented in T3")


def handle_run_verify(args: argparse.Namespace) -> int:
    """Verify stage 4 execution gate.

    Args:
        args: Parsed CLI arguments.

    Returns:
        0 on success, non-zero on error.
    """
    raise NotImplementedError("handle_run_verify will be implemented in T4")
