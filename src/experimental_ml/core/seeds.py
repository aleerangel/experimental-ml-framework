"""Deterministic random seed derivation for Experimental ML Framework.

Provides pure functions to derive independent, reproducible random seeds
from master seeds and parent seeds using numpy.random.SeedSequence,
guaranteeing full determinism across sequential and parallel executions
(RNF01, ADR-007).
"""

from __future__ import annotations

import numpy as np


def derive_seeds(master_seed: int, count: int) -> tuple[int, ...]:
    """Derive `count` independent integer seeds from a master seed.

    Args:
        master_seed: Initial integer seed.
        count: Number of independent seeds to derive (must be >= 1).

    Returns:
        Tuple of `count` independent integer seeds.

    Raises:
        ValueError: If count is less than 1.
        TypeError: If master_seed or count is not an integer.
    """
    if not isinstance(count, int) or isinstance(count, bool):
        raise TypeError("count must be an integer")
    if count < 1:
        raise ValueError(f"count must be at least 1, got {count}")
    if not isinstance(master_seed, int) or isinstance(master_seed, bool):
        raise TypeError("master_seed must be an integer")

    ss = np.random.SeedSequence(master_seed)
    states = ss.generate_state(count)
    return tuple(int(s) for s in states)


def spawn_child_seeds(parent_seed: int, count: int) -> tuple[int, ...]:
    """Spawn `count` child seed sequences from a parent seed.

    Args:
        parent_seed: Parent integer seed.
        count: Number of child seeds to spawn (must be >= 1).

    Returns:
        Tuple of `count` independent child integer seeds.

    Raises:
        ValueError: If count is less than 1.
        TypeError: If parent_seed or count is not an integer.
    """
    if not isinstance(count, int) or isinstance(count, bool):
        raise TypeError("count must be an integer")
    if count < 1:
        raise ValueError(f"count must be at least 1, got {count}")
    if not isinstance(parent_seed, int) or isinstance(parent_seed, bool):
        raise TypeError("parent_seed must be an integer")

    parent_ss = np.random.SeedSequence(parent_seed)
    children = parent_ss.spawn(count)
    return tuple(int(child.generate_state(1)[0]) for child in children)

