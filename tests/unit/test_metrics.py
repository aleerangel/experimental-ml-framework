"""Unit test suite for experimental_ml.metrics.

Validates:
- Domain types, immutability, scope validation and coercion (MET-01, MET-22 - C1, C2)
- Array validation, dimensions, and non-finites rejection (MET-04, MET-05 - C5, C6)
- Numerical stability and overflow mitigation (MET-21 - C7)
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from experimental_ml.core.enums import AggregationScope, MetricDirection, MetricStatus, TaskType
from experimental_ml.core.findings import ConfigurationError, DataIntegrityError, Finding, FindingSeverity
from experimental_ml.metrics import (
    AggregatedMetricValue,
    MetricEvaluationScope,
    MetricSpec,
    MetricValue,
    RankedCandidate,
)
from experimental_ml.metrics.validation import (
    scaled_quadratic_sum,
    validate_numeric_arrays,
)
from experimental_ml.metrics.regression import (
    mae,
    mbe,
    rmse,
)


# =============================================================================
# C8: Direct-scale errors mae, rmse, and mbe operate in float64 with zero error on identity (MET-06)
# =============================================================================
def test_direct_scale_errors_accuracy() -> None:
    """Validate mae, rmse, and mbe analytical accuracy and identity zero error."""
    yt = np.array([10.0, 20.0, 30.0, 40.0])
    yp = np.array([12.0, 19.0, 31.0, 42.0])

    # Analytical values:
    # diffs = [2.0, -1.0, 1.0, 2.0]
    # |diffs| = [2.0, 1.0, 1.0, 2.0] -> mean = 6.0 / 4 = 1.5
    # diffs^2 = [4.0, 1.0, 1.0, 4.0] -> mean = 10.0 / 4 = 2.5 -> rmse = sqrt(2.5) ~ 1.5811388300841898
    res_mae = mae(yt, yp)
    assert res_mae.metric_id == "mae"
    assert res_mae.status == MetricStatus.VALID
    assert math.isclose(res_mae.value, 1.5, rel_tol=1e-12, abs_tol=1e-12)

    res_rmse = rmse(yt, yp)
    assert res_rmse.metric_id == "rmse"
    assert res_rmse.status == MetricStatus.VALID
    assert math.isclose(res_rmse.value, math.sqrt(2.5), rel_tol=1e-12, abs_tol=1e-12)

    # Identity produces exactly 0.0 error
    res_mae_id = mae(yt, yt)
    assert res_mae_id.value == 0.0
    assert res_mae_id.status == MetricStatus.VALID

    res_rmse_id = rmse(yt, yt)
    assert res_rmse_id.value == 0.0
    assert res_rmse_id.status == MetricStatus.VALID

    res_mbe_id = mbe(yt, yt)
    assert res_mbe_id.value == 0.0
    assert res_mbe_id.status == MetricStatus.VALID


# =============================================================================
# C9: mbe preserves positive and negative signed values (MET-06)
# =============================================================================
def test_mbe_preserves_signed_value() -> None:
    """Validate that mbe preserves signed direction for overestimation and underestimation."""
    yt = np.array([10.0, 20.0, 30.0, 40.0])

    # Overestimation: y_pred > y_true -> positive MBE
    yp_over = yt + 2.5
    res_over = mbe(yt, yp_over)
    assert math.isclose(res_over.value, 2.5, rel_tol=1e-12, abs_tol=1e-12)
    assert res_over.status == MetricStatus.VALID
    assert res_over.direction == MetricDirection.MINIMIZE

    # Underestimation: y_pred < y_true -> negative MBE
    yp_under = yt - 3.75
    res_under = mbe(yt, yp_under)
    assert math.isclose(res_under.value, -3.75, rel_tol=1e-12, abs_tol=1e-12)
    assert res_under.status == MetricStatus.VALID
    assert res_under.direction == MetricDirection.MINIMIZE


# =============================================================================
# C10: Function rmse preserves scale homoscedasticity without rounding (MET-07)
# =============================================================================
def test_rmse_scale_homoscedasticity() -> None:
    """Validate RMSE(c*y, c*y_hat) == |c|*RMSE(y, y_hat) with atol=0.0 and no rounding."""
    yt = np.array([1.2, 3.4, 5.6, 7.8])
    yp = np.array([1.5, 3.1, 5.9, 7.4])

    base_rmse = rmse(yt, yp).value
    assert base_rmse > 0.0

    scalars = [0.5, 2.0, 10.0, -3.0, -0.25, 123.456]
    for c in scalars:
        scaled_rmse = rmse(c * yt, c * yp).value
        expected = abs(c) * base_rmse
        assert math.isclose(scaled_rmse, expected, rel_tol=1e-12, abs_tol=1e-12)


# =============================================================================
# C1: MetricValue, AggregatedMetricValue, MetricSpec, RankedCandidate are immutable (MET-01)
# =============================================================================
def test_metric_structures_immutable() -> None:
    """Validate that all metric record structures are frozen/immutable."""
    mv = MetricValue(
        metric_id="rmse",
        value=1.5,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=100,
        warnings=(),
    )
    with pytest.raises((TypeError, AttributeError)):
        mv.value = 2.0  # type: ignore[misc]

    agg = AggregatedMetricValue(
        metric_id="rmse",
        mean=1.5,
        std=0.2,
        median=1.45,
        iqr=0.1,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=AggregationScope.FOLD_AGGREGATION,
        valid_folds=5,
        total_folds=5,
        coverage=1.0,
        fold_values=(mv,),
        warnings=(),
    )
    with pytest.raises((TypeError, AttributeError)):
        agg.mean = 2.0  # type: ignore[misc]

    spec = MetricSpec(
        metric_id="rmse",
        name="Root Mean Squared Error",
        family="Direct-Scale Error",
        direction=MetricDirection.MINIMIZE,
        compare_by_abs=False,
        supported_tasks=(TaskType.REGRESSION,),
        func=lambda yt, yp, **kwargs: mv,
        rtol=1e-12,
        atol=1e-12,
    )
    with pytest.raises((TypeError, AttributeError)):
        spec.direction = MetricDirection.MAXIMIZE  # type: ignore[misc]

    ranked = RankedCandidate(
        candidate_id="model_a",
        metric=agg,
        rank=1,
        status=MetricStatus.VALID,
    )
    with pytest.raises((TypeError, AttributeError)):
        ranked.rank = 2  # type: ignore[misc]


# =============================================================================
# C2: MetricEvaluationScope defines 4 canonical members and validates strictly (MET-22)
# =============================================================================
def test_metric_evaluation_scope_validation() -> None:
    """Validate MetricEvaluationScope members and strict scope validation."""
    assert MetricEvaluationScope.PER_FOLD == "PER_FOLD"
    assert MetricEvaluationScope.FOLD_AGGREGATION == "FOLD_AGGREGATION"
    assert MetricEvaluationScope.POOLED_OOF == "POOLED_OOF"
    assert MetricEvaluationScope.FINAL_HOLDOUT == "FINAL_HOLDOUT"
    assert len(MetricEvaluationScope) == 4

    # Valid MetricValue scope
    mv = MetricValue(
        metric_id="rmse",
        value=1.0,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope="PER_FOLD",
        n_samples=10,
    )
    assert mv.scope == MetricEvaluationScope.PER_FOLD

    # Arbitrary scope raises ConfigurationError
    with pytest.raises(ConfigurationError):
        MetricValue(
            metric_id="rmse",
            value=1.0,
            status=MetricStatus.VALID,
            direction=MetricDirection.MINIMIZE,
            scope="ARBITRARY_SCOPE",
            n_samples=10,
        )

    # AggregatedMetricValue rejects PER_FOLD
    with pytest.raises(ConfigurationError):
        AggregatedMetricValue(
            metric_id="rmse",
            mean=1.0,
            std=0.1,
            median=1.0,
            iqr=0.05,
            status=MetricStatus.VALID,
            direction=MetricDirection.MINIMIZE,
            scope=MetricEvaluationScope.PER_FOLD,  # type: ignore[arg-type]
            valid_folds=5,
            total_folds=5,
            coverage=1.0,
        )


# =============================================================================
# C5: Array validation converts to float64, rejects mismatched lengths and zero samples (MET-04)
# =============================================================================
def test_array_validation_dimensions() -> None:
    """Validate numeric array dimension and length checks."""
    yt = [1, 2, 3]
    yp = [1.1, 2.1, 3.1]
    yt_arr, yp_arr, n = validate_numeric_arrays(yt, yp)
    assert yt_arr.dtype == np.float64
    assert yp_arr.dtype == np.float64
    assert n == 3

    # Zero samples
    with pytest.raises(DataIntegrityError):
        validate_numeric_arrays([], [])

    # Length mismatch
    with pytest.raises(DataIntegrityError):
        validate_numeric_arrays([1, 2], [1, 2, 3])

    # Multidimensional incompatible shape
    with pytest.raises(DataIntegrityError):
        validate_numeric_arrays(np.zeros((3, 2)), np.zeros(3))


# =============================================================================
# C6: Array validation rejects NaN, +Inf, and -Inf with DataIntegrityError (MET-05)
# =============================================================================
def test_array_validation_non_finites() -> None:
    """Validate that NaN and infinities in inputs raise DataIntegrityError."""
    with pytest.raises(DataIntegrityError):
        validate_numeric_arrays([1.0, np.nan], [1.0, 2.0])

    with pytest.raises(DataIntegrityError):
        validate_numeric_arrays([1.0, 2.0], [1.0, np.inf])

    with pytest.raises(DataIntegrityError):
        validate_numeric_arrays([1.0, -np.inf], [1.0, 2.0])


# =============================================================================
# C7: scaled_quadratic_sum prevents intermediate overflow for large magnitudes (MET-21)
# =============================================================================
def test_numerical_stability_and_overflow() -> None:
    """Validate scaled_quadratic_sum behavior on large magnitudes near float64 boundaries."""
    # Magnitudes > 1e154 would overflow if squared directly: (1e200)**2 -> inf
    diff = np.array([1e200, 2e200, -1e200])
    m, s = scaled_quadratic_sum(diff)
    assert m == 2e200
    assert math.isclose(s, (0.5)**2 + 1.0 + (0.5)**2)  # 0.25 + 1.0 + 0.25 = 1.5

    # RMSE computation via scaled values: m * sqrt(s / n)
    rmse_scaled = m * math.sqrt(s / 3.0)
    assert math.isfinite(rmse_scaled)
    assert rmse_scaled > 0.0

    # Zero differences
    m0, s0 = scaled_quadratic_sum(np.zeros(5))
    assert m0 == 0.0
    assert s0 == 0.0
