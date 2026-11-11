"""Unit tests for hyperparameter candidate generation (TUN-03)."""

from experimental_ml.core.enums import MetricDirection
from experimental_ml.tuning.candidates import generate_candidates
from experimental_ml.tuning.types import HyperparameterSearchSpec, SearchStrategy


def test_m43_03_01_grid_search_cartesian_product() -> None:
    """C10: generate_candidates produces deterministic Cartesian product for grid search."""
    spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.1, 1.0), "fit_intercept": (True, False)},
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
    )
    candidates = generate_candidates(spec)
    # alpha has 2 values, fit_intercept has 2 values -> 4 combinations
    assert len(candidates) == 4
    # Deterministic alphabetical order by key: alpha, fit_intercept
    expected = [
        {"alpha": 0.1, "fit_intercept": True},
        {"alpha": 0.1, "fit_intercept": False},
        {"alpha": 1.0, "fit_intercept": True},
        {"alpha": 1.0, "fit_intercept": False},
    ]
    for c, exp in zip(candidates, expected):
        assert dict(c) == exp


def test_m43_03_02_random_search_seed_determinism() -> None:
    """C11: generate_candidates samples exactly n_iter candidates deterministically with seed."""
    spec1 = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.RANDOM_SEARCH,
        param_grid={
            "alpha": (0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
            "max_iter": (100, 200, 500, 1000),
            "tol": (1e-4, 1e-3, 1e-2),
        },
        optimization_metric="r2",
        direction=MetricDirection.MAXIMIZE,
        n_iter=5,
        seed=12345,
    )
    candidates1 = generate_candidates(spec1)
    assert len(candidates1) == 5

    spec2 = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.RANDOM_SEARCH,
        param_grid={
            "alpha": (0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
            "max_iter": (100, 200, 500, 1000),
            "tol": (1e-4, 1e-3, 1e-2),
        },
        optimization_metric="r2",
        direction=MetricDirection.MAXIMIZE,
        n_iter=5,
        seed=12345,
    )
    candidates2 = generate_candidates(spec2)

    # Re-running with same seed produces identical candidates
    assert [dict(c) for c in candidates1] == [dict(c) for c in candidates2]

    # Re-running with another seed produces different candidates
    spec_diff = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.RANDOM_SEARCH,
        param_grid={
            "alpha": (0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
            "max_iter": (100, 200, 500, 1000),
            "tol": (1e-4, 1e-3, 1e-2),
        },
        optimization_metric="r2",
        direction=MetricDirection.MAXIMIZE,
        n_iter=5,
        seed=99999,
    )
    candidates_diff = generate_candidates(spec_diff)
    assert [dict(c) for c in candidates1] != [dict(c) for c in candidates_diff]


def test_m43_03_03_fixed_strategy_single_candidate() -> None:
    """C12: generate_candidates produces a single candidate mapping for fixed strategy."""
    spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.FIXED,
        param_grid={"alpha": 0.5, "normalize": True},
        optimization_metric="mae",
        direction=MetricDirection.MINIMIZE,
    )
    candidates = generate_candidates(spec)
    assert len(candidates) == 1
    assert dict(candidates[0]) == {"alpha": 0.5, "normalize": True}
