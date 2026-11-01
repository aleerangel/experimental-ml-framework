"""Diagnostic findings and core exceptions for Experimental ML Framework.

Provides structured diagnostic findings (confirmed issues and heuristic warnings)
and standard contract violation and integrity exceptions according to ADR-002,
ADR-008 and RNF07.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from experimental_ml.core.enums import FindingSeverity


class ExperimentalMLError(Exception):
    """Base exception for all domain errors in Experimental ML Framework."""


class ContractViolationError(ExperimentalMLError):
    """Raised when an architectural or API contract is violated."""


class DataIntegrityError(ExperimentalMLError):
    """Raised when data integrity or schema validation fails."""


class ConfigurationError(ExperimentalMLError):
    """Raised when an invalid or contradictory configuration is provided."""


@dataclass(frozen=True, slots=True)
class Finding:
    """Immutable diagnostic record for contract and integrity checks."""

    severity: FindingSeverity
    code: str
    message: str
    context: Mapping[str, Any] | None = None


def make_finding(
    code: str,
    message: str,
    context: Mapping[str, Any] | None = None,
) -> Finding:
    """Create a confirmed issue finding (FindingSeverity.CONFIRMED_ISSUE).

    Args:
        code: Unique machine-readable diagnostic code (e.g., 'E1_DATA_LEAKAGE').
        message: Human-readable explanation of the issue.
        context: Optional auxiliary context metadata.

    Returns:
        Immutable Finding instance with severity CONFIRMED_ISSUE.
    """
    return Finding(
        severity=FindingSeverity.CONFIRMED_ISSUE,
        code=code,
        message=message,
        context=context,
    )


def make_warning(
    code: str,
    message: str,
    context: Mapping[str, Any] | None = None,
) -> Finding:
    """Create a heuristic warning finding (FindingSeverity.HEURISTIC_WARNING).

    Args:
        code: Unique machine-readable diagnostic code (e.g., 'W1_HIGH_CORRELATION').
        message: Pedagogical warning message explaining potential risk.
        context: Optional auxiliary context metadata.

    Returns:
        Immutable Finding instance with severity HEURISTIC_WARNING.
    """
    return Finding(
        severity=FindingSeverity.HEURISTIC_WARNING,
        code=code,
        message=message,
        context=context,
    )

