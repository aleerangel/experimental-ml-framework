"""Unit tests for search specification validation (TUN-02)."""

import pytest
from experimental_ml.core.enums import MetricDirection
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.tuning.types import HyperparameterSearchSpec, SearchStrategy
from experimental_ml.tuning.validation import validate_search_spec


def test_m43_02_01_validate_search_spec_valid() -> None:
    """C6: validate_search_spec validates valid search specifications without mutating fields."""
    spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.1, 1.0), "fit_intercept": (True, False)},
        optimization_metric="RMSE",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=3,
    )
    validated = validate_search_spec(spec)
    assert validated is spec
    assert validated.optimization_metric == "RMSE"
    assert validated.inner_cv_folds == 3


def test_m43_02_02_validate_search_spec_invalid_folds() -> None:
    """C7: validate_search_spec raises ConfigurationError when inner_cv_folds < 2."""
    spec_zero = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.1,)},
        optimization_metric="RMSE",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=1,
    )
    with pytest.raises(ConfigurationError, match="inner_cv_folds must be an integer >= 2"):
        validate_search_spec(spec_zero)

    spec_neg = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.1,)},
        optimization_metric="RMSE",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=-3,
    )
    with pytest.raises(ConfigurationError, match="inner_cv_folds must be an integer >= 2"):
        validate_search_spec(spec_neg)


def test_m43_02_03_validate_search_spec_metric_direction() -> None:
    """C8: validate_search_spec raises ConfigurationError on unknown metric or conflicting direction."""
    # Unknown metric
    spec_unknown = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.1,)},
        optimization_metric="NON_EXISTENT_METRIC",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=3,
    )
    with pytest.raises(ConfigurationError, match="not registered in METRICS_CATALOG"):
        validate_search_spec(spec_unknown)

    # Conflicting direction (RMSE is MINIMIZE, but spec declares MAXIMIZE)
    spec_conflict = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.1,)},
        optimization_metric="RMSE",
        direction=MetricDirection.MAXIMIZE,
        inner_cv_folds=3,
    )
    with pytest.raises(ConfigurationError, match="Direction mismatch for metric 'RMSE'"):
        validate_search_spec(spec_conflict)

    # Empty metric
    spec_empty = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.GRID_SEARCH,
        param_grid={"alpha": (0.1,)},
        optimization_metric="  ",
        direction=MetricDirection.MINIMIZE,
        inner_cv_folds=3,
    )
    with pytest.raises(ConfigurationError, match="optimization_metric cannot be empty"):
        validate_search_spec(spec_empty)


def test_m43_02_04_validate_search_spec_random_n_iter() -> None:
    """C9: validate_search_spec raises ConfigurationError on non-positive n_iter for random search."""
    # None n_iter
    spec_none = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.RANDOM_SEARCH,
        param_grid={"alpha": (0.1, 1.0)},
        optimization_metric="R2",
        direction=MetricDirection.MAXIMIZE,
        n_iter=None,
        inner_cv_folds=3,
    )
    with pytest.raises(ConfigurationError, match="n_iter must be a positive integer"):
        validate_search_spec(spec_none)

    # Zero n_iter
    spec_zero = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.RANDOM_SEARCH,
        param_grid={"alpha": (0.1, 1.0)},
        optimization_metric="R2",
        direction=MetricDirection.MAXIMIZE,
        n_iter=0,
        inner_cv_folds=3,
    )
    with pytest.raises(ConfigurationError, match="n_iter must be a positive integer"):
        validate_search_spec(spec_zero)

    # Negative n_iter
    spec_neg = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.RANDOM_SEARCH,
        param_grid={"alpha": (0.1, 1.0)},
        optimization_metric="R2",
        direction=MetricDirection.MAXIMIZE,
        n_iter=-5,
        inner_cv_folds=3,
    )
    with pytest.raises(ConfigurationError, match="n_iter must be a positive integer"):
        validate_search_spec(spec_neg)
