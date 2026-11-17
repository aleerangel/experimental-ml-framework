"""Experimental ML Framework - Core Package."""

from __future__ import annotations

from typing import Any

__version__ = "0.1.0.dev0"

__all__ = ["__version__", "ExperimentRunSummary", "run_experiment"]


def __getattr__(name: str) -> Any:
    """Lazy PEP 562 export for high-level facade preserving CLI-10 startup purity."""
    if name in {"ExperimentRunSummary", "run_experiment"}:
        from experimental_ml import pipeline

        return getattr(pipeline, name)
    raise AttributeError(f"module 'experimental_ml' has no attribute {name!r}")
