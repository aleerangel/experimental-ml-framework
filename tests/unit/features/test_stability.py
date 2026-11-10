"""Unit tests for selection stability metrics Jaccard and Kuncheva index (SEL-06)."""

from dataclasses import FrozenInstanceError
import json
import math
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.features.stability import (
    SelectionStabilityReport,
    compute_selection_stability,
)


def test_sel_06_selection_stability_metrics() -> None:
    """Proof C6: Verify pairwise Jaccard and chance-corrected Kuncheva stability index (SEL-06)."""
    # 1. Identical selections across 3 folds: perfect stability
    identical_selections = [
        ["feat_1", "feat_2"],
        ["feat_1", "feat_2"],
        ["feat_1", "feat_2"],
    ]
    rep_perf = compute_selection_stability(identical_selections, n_total_candidates=10)
    assert rep_perf.mean_jaccard == 1.0
    assert rep_perf.std_jaccard == 0.0
    assert pytest.approx(rep_perf.mean_kuncheva, abs=1e-6) == 1.0
    assert rep_perf.std_kuncheva == 0.0
    assert rep_perf.n_folds == 3
    assert rep_perf.n_total_candidates == 10

    # 2. Known intermediate analytical calculation
    # N = 10 total candidate features
    # Fold 0: {f1, f2, f3} (k=3)
    # Fold 1: {f1, f2, f4} (k=3)
    # Intersection r = 2, Union = 4
    # Jaccard = 2 / 4 = 0.5
    # Kuncheva:
    # r*N - k1*k2 = 2*10 - 3*3 = 20 - 9 = 11
    # denom = sqrt(3 * 3 * (10 - 3) * (10 - 3)) = sqrt(9 * 49) = 3 * 7 = 21
    # K = 11 / 21 ~ 0.5238095
    selections_inter = [
        ["f1", "f2", "f3"],
        ["f1", "f2", "f4"],
    ]
    rep_inter = compute_selection_stability(selections_inter, n_total_candidates=10)
    assert rep_inter.mean_jaccard == 0.5
    assert pytest.approx(rep_inter.mean_kuncheva, abs=1e-6) == (11.0 / 21.0)

    # 3. Disjoint selections
    # Fold 0: {f1, f2}
    # Fold 1: {f3, f4}
    # r = 0, Jaccard = 0.0
    # Kuncheva: (0*10 - 2*2) / sqrt(2*2 * 8*8) = -4 / 16 = -0.25
    selections_disjoint = [
        ["f1", "f2"],
        ["f3", "f4"],
    ]
    rep_disjoint = compute_selection_stability(selections_disjoint, n_total_candidates=10)
    assert rep_disjoint.mean_jaccard == 0.0
    assert pytest.approx(rep_disjoint.mean_kuncheva, abs=1e-6) == -0.25

    # 4. Immutability and roundtrip serialization
    with pytest.raises(FrozenInstanceError):
        rep_inter.mean_jaccard = 0.9  # type: ignore

    data = rep_inter.to_dict()
    json_bytes = json.dumps(data, indent=2, allow_nan=False)
    reconstructed = SelectionStabilityReport.from_dict(json.loads(json_bytes))
    assert reconstructed.mean_jaccard == rep_inter.mean_jaccard
    assert reconstructed.mean_kuncheva == rep_inter.mean_kuncheva
    assert reconstructed.pairwise_jaccard["fold_0"]["fold_1"] == 0.5


def test_stability_input_validations() -> None:
    """Verify input validation rules in compute_selection_stability."""
    # Fewer than 2 folds
    with pytest.raises(ConfigurationError, match="at least 2 folds"):
        compute_selection_stability([["f1", "f2"]], n_total_candidates=5)

    # Invalid n_total_candidates (< 1)
    with pytest.raises(ConfigurationError, match="n_total_candidates must be >= 1"):
        compute_selection_stability([["f1"], ["f2"]], n_total_candidates=0)

    # Fold selection with more features than candidate pool
    with pytest.raises(ConfigurationError, match="exceeds n_total_candidates"):
        compute_selection_stability([["f1", "f2", "f3"], ["f1"]], n_total_candidates=2)
