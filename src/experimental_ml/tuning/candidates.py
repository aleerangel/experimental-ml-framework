"""Deterministic generation of hyperparameter candidate combinations for tuning."""

from __future__ import annotations

import itertools
from types import MappingProxyType
from typing import Any

import numpy as np

from experimental_ml.tuning.types import HyperparameterSearchSpec, SearchStrategy

__all__ = ["generate_candidates"]


def generate_candidates(
    spec: HyperparameterSearchSpec,
) -> tuple[MappingProxyType[str, Any], ...]:
    """Generate deterministic hyperparameter candidates based on the search strategy.

    Parameters
    ----------
    spec:
        The validated search specification.

    Returns
    -------
    tuple[MappingProxyType[str, Any], ...]
        Sequence of candidate parameter mappings.
    """
    param_grid = spec.param_grid

    if spec.search_strategy == SearchStrategy.FIXED:
        candidate: dict[str, Any] = {}
        for k in sorted(param_grid.keys()):
            values = param_grid[k]
            candidate[k] = values[0] if values else None
        return (MappingProxyType(candidate),)

    if spec.search_strategy == SearchStrategy.GRID_SEARCH:
        param_names = sorted(param_grid.keys())
        if not param_names:
            return (MappingProxyType({}),)

        value_lists = [param_grid[k] for k in param_names]
        candidates = []
        for combo in itertools.product(*value_lists):
            candidate_dict = dict(zip(param_names, combo))
            candidates.append(MappingProxyType(candidate_dict))
        return tuple(candidates)

    if spec.search_strategy == SearchStrategy.RANDOM_SEARCH:
        param_names = sorted(param_grid.keys())
        if not param_names:
            return (MappingProxyType({}),)

        n_iter = spec.n_iter if spec.n_iter is not None else 1
        rng = np.random.default_rng(spec.seed)

        # Generate Cartesian product to determine if total pool is small
        value_lists = [param_grid[k] for k in param_names]
        total_combinations = 1
        for v in value_lists:
            total_combinations *= len(v)

        if total_combinations <= n_iter:
            all_combos = list(itertools.product(*value_lists))
            rng.shuffle(all_combos)
            return tuple(
                MappingProxyType(dict(zip(param_names, combo)))
                for combo in all_combos[:n_iter]
            )

        # Sample with or without replacement deterministically
        sampled_candidates = []
        for _ in range(n_iter):
            combo = tuple(
                param_grid[k][int(rng.integers(0, len(param_grid[k])))]
                for k in param_names
            )
            sampled_candidates.append(MappingProxyType(dict(zip(param_names, combo))))

        return tuple(sampled_candidates)

    # For CUSTOM_TUNER or unsupported types, return declared defaults
    candidate_default = {k: param_grid[k][0] for k in sorted(param_grid.keys()) if param_grid[k]}
    return (MappingProxyType(candidate_default),)
