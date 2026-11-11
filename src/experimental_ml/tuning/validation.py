"""Declarative validation for hyperparameter search spaces and optimization metrics."""

from __future__ import annotations

from typing import Mapping

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.metrics.catalog import METRICS_CATALOG
from experimental_ml.metrics.types import MetricSpec
from experimental_ml.tuning.types import HyperparameterSearchSpec, SearchStrategy

__all__ = ["validate_search_spec"]


def validate_search_spec(
    spec: HyperparameterSearchSpec,
    metric_catalog: Mapping[str, MetricSpec] = METRICS_CATALOG,
) -> HyperparameterSearchSpec:
    """Validate declarative hyperparameter search specification against catalog and boundaries.

    Parameters
    ----------
    spec:
        The hyperparameter search specification to validate.
    metric_catalog:
        Catalog mapping metric identifier strings to MetricSpec instances.

    Returns
    -------
    HyperparameterSearchSpec
        The validated specification.

    Raises
    ------
    ConfigurationError
        If inner_cv_folds < 2, the metric is unknown or has conflicting direction,
        or search strategy parameters are malformed.
    """
    if not isinstance(spec, HyperparameterSearchSpec):
        raise ConfigurationError(
            f"Expected HyperparameterSearchSpec, got {type(spec).__name__}"
        )

    if not isinstance(spec.inner_cv_folds, int) or spec.inner_cv_folds < 2:
        raise ConfigurationError(
            f"inner_cv_folds must be an integer >= 2, got {spec.inner_cv_folds!r}"
        )

    metric_name = spec.optimization_metric.strip().lower()
    if not metric_name:
        raise ConfigurationError("optimization_metric cannot be empty")

    if metric_name not in metric_catalog:
        raise ConfigurationError(
            f"Optimization metric {spec.optimization_metric!r} is not registered in METRICS_CATALOG. "
            f"Available metrics: {sorted(metric_catalog.keys())}"
        )

    cat_entry = metric_catalog[metric_name]
    if spec.direction != cat_entry.direction:
        raise ConfigurationError(
            f"Direction mismatch for metric {spec.optimization_metric!r}: "
            f"spec declared direction {spec.direction.value!r}, "
            f"but catalog requires {cat_entry.direction.value!r}"
        )

    if spec.search_strategy == SearchStrategy.RANDOM_SEARCH:
        if spec.n_iter is None or not isinstance(spec.n_iter, int) or spec.n_iter <= 0:
            raise ConfigurationError(
                f"For RANDOM_SEARCH, n_iter must be a positive integer, got {spec.n_iter!r}"
            )

    if spec.search_strategy == SearchStrategy.GRID_SEARCH:
        if not spec.param_grid:
            raise ConfigurationError(
                "For GRID_SEARCH, param_grid cannot be empty"
            )
        for param_name, values in spec.param_grid.items():
            if not values:
                raise ConfigurationError(
                    f"Parameter {param_name!r} in param_grid must contain at least one value"
                )

    return spec
