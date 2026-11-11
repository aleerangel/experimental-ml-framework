"""Hyperparameter search and nested cross-validation subsystem (Stage 3B).

Exports declarative search specifications, deterministic candidate generators,
anti-leakage inner partitioning, and the nested cross-validation execution engine.
"""

from experimental_ml.tuning.candidates import generate_candidates
from experimental_ml.tuning.engine import run_nested_tuning
from experimental_ml.tuning.partitioning import split_inner_folds
from experimental_ml.tuning.types import (
    HyperparameterSearchSpec,
    SearchStrategy,
    TuningOptimizationError,
    TuningResult,
    TuningTrialRecord,
)
from experimental_ml.tuning.validation import validate_search_spec

__all__ = [
    "HyperparameterSearchSpec",
    "SearchStrategy",
    "TuningOptimizationError",
    "TuningResult",
    "TuningTrialRecord",
    "generate_candidates",
    "run_nested_tuning",
    "split_inner_folds",
    "validate_search_spec",
]
