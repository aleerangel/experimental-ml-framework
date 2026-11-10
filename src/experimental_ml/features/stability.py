"""Selection stability metrics across cross-validation folds.

Complies with SEL-06, RF2.1, CA-E2-01, ADR-005, and ADR-008.
Implements pairwise Jaccard index and chance-corrected Kuncheva stability index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from experimental_ml.core.findings import ConfigurationError


@dataclass(frozen=True, slots=True)
class SelectionStabilityReport:
    """Immutable report of feature selection stability across multiple folds."""

    mean_jaccard: float
    std_jaccard: float
    mean_kuncheva: float
    std_kuncheva: float
    pairwise_jaccard: Mapping[str, Mapping[str, float]]
    pairwise_kuncheva: Mapping[str, Mapping[str, float]]
    n_folds: int
    n_total_candidates: int

    def __post_init__(self) -> None:
        if not isinstance(self.pairwise_jaccard, MappingProxyType):
            frozen_jaccard = {
                k: MappingProxyType(dict(sub))
                for k, sub in self.pairwise_jaccard.items()
            }
            object.__setattr__(self, "pairwise_jaccard", MappingProxyType(frozen_jaccard))

        if not isinstance(self.pairwise_kuncheva, MappingProxyType):
            frozen_kuncheva = {
                k: MappingProxyType(dict(sub))
                for k, sub in self.pairwise_kuncheva.items()
            }
            object.__setattr__(self, "pairwise_kuncheva", MappingProxyType(frozen_kuncheva))

    def to_dict(self) -> dict[str, Any]:
        """Serialize report to a JSON-compliant primitive dictionary."""
        return {
            "mean_jaccard": float(self.mean_jaccard),
            "std_jaccard": float(self.std_jaccard),
            "mean_kuncheva": float(self.mean_kuncheva),
            "std_kuncheva": float(self.std_kuncheva),
            "pairwise_jaccard": {k: dict(v) for k, v in self.pairwise_jaccard.items()},
            "pairwise_kuncheva": {k: dict(v) for k, v in self.pairwise_kuncheva.items()},
            "n_folds": self.n_folds,
            "n_total_candidates": self.n_total_candidates,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SelectionStabilityReport:
        """Reconstruct report from dictionary representation."""
        raw_jaccard = data.get("pairwise_jaccard", {})
        frozen_jaccard = {
            k: MappingProxyType(dict(sub)) for k, sub in raw_jaccard.items()
        }

        raw_kuncheva = data.get("pairwise_kuncheva", {})
        frozen_kuncheva = {
            k: MappingProxyType(dict(sub)) for k, sub in raw_kuncheva.items()
        }

        return cls(
            mean_jaccard=float(data["mean_jaccard"]),
            std_jaccard=float(data["std_jaccard"]),
            mean_kuncheva=float(data["mean_kuncheva"]),
            std_kuncheva=float(data["std_kuncheva"]),
            pairwise_jaccard=MappingProxyType(frozen_jaccard),
            pairwise_kuncheva=MappingProxyType(frozen_kuncheva),
            n_folds=int(data["n_folds"]),
            n_total_candidates=int(data["n_total_candidates"]),
        )


def compute_selection_stability(
    fold_selections: Sequence[Sequence[str]],
    n_total_candidates: int,
) -> SelectionStabilityReport:
    """Compute feature selection stability across folds using Jaccard and Kuncheva indices (SEL-06).

    Args:
        fold_selections: Sequence of feature subsets selected in each fold (length >= 2).
        n_total_candidates: Total number of candidate features in the pool (N >= 1).

    Returns:
        Immutable SelectionStabilityReport.

    Raises:
        ConfigurationError: If fold_selections has fewer than 2 folds, or n_total_candidates < 1.
    """
    if len(fold_selections) < 2:
        raise ConfigurationError(
            f"compute_selection_stability requires at least 2 folds, got {len(fold_selections)}"
        )

    if n_total_candidates < 1:
        raise ConfigurationError(
            f"n_total_candidates must be >= 1, got {n_total_candidates}"
        )

    k_folds = len(fold_selections)
    fold_names = [f"fold_{i}" for i in range(k_folds)]
    set_selections = [set(s) for s in fold_selections]

    # Validate that no selection exceeds candidate universe
    for i, s in enumerate(set_selections):
        if len(s) > n_total_candidates:
            raise ConfigurationError(
                f"Selection in fold_{i} has {len(s)} features, which exceeds n_total_candidates ({n_total_candidates})."
            )

    jaccard_matrix: dict[str, dict[str, float]] = {f: {} for f in fold_names}
    kuncheva_matrix: dict[str, dict[str, float]] = {f: {} for f in fold_names}

    # Diagonal identity
    for f in fold_names:
        jaccard_matrix[f][f] = 1.0
        kuncheva_matrix[f][f] = 1.0

    pair_jaccards: list[float] = []
    pair_kunchevas: list[float] = []

    N = float(n_total_candidates)

    for i in range(k_folds):
        s_i = set_selections[i]
        k_i = float(len(s_i))
        name_i = fold_names[i]

        for j in range(i + 1, k_folds):
            s_j = set_selections[j]
            k_j = float(len(s_j))
            name_j = fold_names[j]

            # 1. Jaccard similarity: |A ∩ B| / |A ∪ B|
            intersection_size = float(len(s_i & s_j))
            union_size = float(len(s_i | s_j))
            if union_size > 0:
                jaccard = intersection_size / union_size
            else:
                jaccard = 1.0

            # 2. Kuncheva index (chance-corrected)
            # Kuncheva (2007) / Lustgarten et al. (2009):
            # K = (r * N - k_i * k_j) / sqrt(k_i * k_j * (N - k_i) * (N - k_j))
            if (k_i == N and k_j == N) or (k_i == 0.0 and k_j == 0.0):
                kuncheva = 1.0
            else:
                variance_product = k_i * k_j * (N - k_i) * (N - k_j)
                if variance_product > 1e-15:
                    denom = math.sqrt(variance_product)
                    raw_k = (intersection_size * N - k_i * k_j) / denom
                    kuncheva = max(-1.0, min(1.0, raw_k))
                else:
                    kuncheva = 1.0 if s_i == s_j else 0.0

            jaccard_matrix[name_i][name_j] = jaccard
            jaccard_matrix[name_j][name_i] = jaccard

            kuncheva_matrix[name_i][name_j] = kuncheva
            kuncheva_matrix[name_j][name_i] = kuncheva

            pair_jaccards.append(jaccard)
            pair_kunchevas.append(kuncheva)

    mean_j = float(np.mean(pair_jaccards))
    std_j = float(np.std(pair_jaccards))
    mean_k = float(np.mean(pair_kunchevas))
    std_k = float(np.std(pair_kunchevas))

    return SelectionStabilityReport(
        mean_jaccard=mean_j,
        std_jaccard=std_j,
        mean_kuncheva=mean_k,
        std_kuncheva=std_k,
        pairwise_jaccard=jaccard_matrix,
        pairwise_kuncheva=kuncheva_matrix,
        n_folds=k_folds,
        n_total_candidates=n_total_candidates,
    )


__all__ = [
    "SelectionStabilityReport",
    "compute_selection_stability",
]
