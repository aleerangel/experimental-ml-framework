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
    METRICS_CATALOG,
    AggregatedMetricValue,
    MetricEvaluationScope,
    MetricSpec,
    MetricValue,
    RankedCandidate,
    aggregate_fold_metrics,
    compute_metric,
    get_metric_spec,
    is_better,
    list_metrics,
    rank_configurations,
)
from experimental_ml.metrics.validation import (
    scaled_quadratic_sum,
    validate_numeric_arrays,
)
from experimental_ml.metrics.classification import (
    accuracy,
    balanced_accuracy,
    f1,
    log_loss,
    precision,
    recall,
    roc_auc,
)
from experimental_ml.metrics.regression import (
    kta,
    mae,
    mape,
    mbe,
    pearson,
    r2,
    rmse,
    rmse_rel_pct,
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


# =============================================================================
# C11: Dimensionless ratios r2, rmse_rel_pct, mape, pearson, and kta operate within rtol=1e-10, atol=1e-12 (MET-08)
# =============================================================================
def test_dimensionless_ratios_accuracy() -> None:
    """Validate analytical accuracy of r2, rmse_rel_pct, mape, pearson, and kta."""
    yt = np.array([10.0, 20.0, 30.0, 40.0])
    yp = np.array([12.0, 19.0, 31.0, 42.0])

    # R2: y_mean=25, SS_tot=500, SS_res=10 -> R2 = 1 - 10/500 = 0.98
    res_r2 = r2(yt, yp)
    assert res_r2.metric_id == "r2"
    assert res_r2.status == MetricStatus.VALID
    assert math.isclose(res_r2.value, 0.98, rel_tol=1e-10, abs_tol=1e-12)

    # RMSE relative %: 100 * sqrt(2.5) / 25.0 = 4 * sqrt(2.5) ~ 6.324555320336759
    res_rel = rmse_rel_pct(yt, yp)
    assert res_rel.metric_id == "rmse_rel_pct"
    assert res_rel.status == MetricStatus.VALID
    expected_rel = 100.0 * (math.sqrt(2.5) / 25.0)
    assert math.isclose(res_rel.value, expected_rel, rel_tol=1e-10, abs_tol=1e-12)

    # MAPE: (100 / 4) * (2/10 + 1/20 + 1/30 + 2/40) = 25 * (1/3) = 8.333333333333334
    res_mape = mape(yt, yp)
    assert res_mape.metric_id == "mape"
    assert res_mape.status == MetricStatus.VALID
    expected_mape = 100.0 / 12.0
    assert math.isclose(res_mape.value, expected_mape, rel_tol=1e-10, abs_tol=1e-12)

    # Pearson: 510 / sqrt(500 * 526) ~ 0.9943632439169647
    res_pearson = pearson(yt, yp)
    assert res_pearson.metric_id == "pearson"
    assert res_pearson.status == MetricStatus.VALID
    expected_pearson = 510.0 / math.sqrt(500.0 * 526.0)
    assert math.isclose(res_pearson.value, expected_pearson, rel_tol=1e-10, abs_tol=1e-12)

    # KTA: identity Gram matrices yield alignment of 1.0
    k_id = np.eye(4)
    res_kta = kta(k_id, k_id, centered=False)
    assert res_kta.metric_id == "kta"
    assert res_kta.status == MetricStatus.VALID
    assert math.isclose(res_kta.value, 1.0, rel_tol=1e-10, abs_tol=1e-12)

    # Identity predictions for R2 yield 1.0
    res_r2_id = r2(yt, yt)
    assert math.isclose(res_r2_id.value, 1.0, rel_tol=1e-10, abs_tol=1e-12)

    # Identity predictions for MAPE yield 0.0
    res_mape_id = mape(yt, yt)
    assert math.isclose(res_mape_id.value, 0.0, rel_tol=1e-10, abs_tol=1e-12)


# =============================================================================
# C12: Functions r2 and pearson return UNDEFINED_NAN with Finding for n < 2 or zero target variance (MET-09)
# =============================================================================
def test_r2_and_pearson_zero_variance() -> None:
    """Validate r2 and pearson returning UNDEFINED_NAN for small n or zero variance."""
    # n < 2
    r2_n1 = r2(np.array([10.0]), np.array([10.0]))
    assert r2_n1.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(r2_n1.value)
    assert any(w.code == "W_METRIC_INSUFFICIENT_SAMPLES" for w in r2_n1.warnings)

    pearson_n1 = pearson(np.array([10.0]), np.array([10.0]))
    assert pearson_n1.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(pearson_n1.value)
    assert any(w.code == "W_METRIC_INSUFFICIENT_SAMPLES" for w in pearson_n1.warnings)

    # Zero target variance
    yt_const = np.array([5.0, 5.0, 5.0, 5.0])
    yp_var = np.array([4.0, 5.0, 6.0, 7.0])
    r2_zero_var = r2(yt_const, yp_var)
    assert r2_zero_var.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(r2_zero_var.value)
    assert any(w.code == "W_METRIC_ZERO_VARIANCE" for w in r2_zero_var.warnings)

    pearson_zero_var = pearson(yt_const, yp_var)
    assert pearson_zero_var.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(pearson_zero_var.value)
    assert any(w.code == "W_METRIC_ZERO_VARIANCE" for w in pearson_zero_var.warnings)

    # Zero predictor variance in pearson
    pearson_pred_zero_var = pearson(yp_var, yt_const)
    assert pearson_pred_zero_var.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(pearson_pred_zero_var.value)
    assert any(w.code == "W_METRIC_ZERO_VARIANCE" for w in pearson_pred_zero_var.warnings)


# =============================================================================
# C13: Functions rmse_rel_pct and mape return UNDEFINED_NAN with Finding for zero mean or zero target observations (MET-10)
# =============================================================================
def test_rmse_rel_pct_and_mape_degenerate() -> None:
    """Validate rmse_rel_pct and mape returning UNDEFINED_NAN for zero mean or zero targets."""
    # Zero mean target for rmse_rel_pct
    yt_zero_mean = np.array([-10.0, 10.0])
    yp = np.array([-9.0, 9.0])
    res_rel_zero = rmse_rel_pct(yt_zero_mean, yp)
    assert res_rel_zero.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_rel_zero.value)
    assert any(w.code == "W_METRIC_ZERO_MEAN" for w in res_rel_zero.warnings)

    # Zero observation in target for mape (no arbitrary epsilon added)
    yt_with_zero = np.array([0.0, 10.0, 20.0])
    yp_test = np.array([1.0, 11.0, 21.0])
    res_mape_zero = mape(yt_with_zero, yp_test)
    assert res_mape_zero.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_mape_zero.value)
    assert any(w.code == "W_METRIC_ZERO_TARGET" for w in res_mape_zero.warnings)


# =============================================================================
# C14: Function kta computes uncentered and centered alignment and returns UNDEFINED_NAN for zero Gram norm (MET-11)
# =============================================================================
def test_kta_centered_and_uncentered() -> None:
    """Validate kta uncentered and centered alignment and zero Frobenius norm handling."""
    # 1D vector inputs: v1, v2 converted to outer products
    v1 = np.array([1.0, 2.0, 3.0])
    v2 = np.array([2.0, 4.0, 6.0])  # collinear with v1 -> outer product identical up to scale
    res_1d = kta(v1, v2, centered=False)
    assert res_1d.status == MetricStatus.VALID
    assert math.isclose(res_1d.value, 1.0, rel_tol=1e-10, abs_tol=1e-12)

    # Centered alignment with double centering HKH
    # If K is constant matrix 1*1^T, H K H = 0, so Frobenius norm is zero
    k_const = np.ones((4, 4))
    res_centered_zero = kta(k_const, np.eye(4), centered=True)
    assert res_centered_zero.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_centered_zero.value)
    assert any(w.code == "W_METRIC_ZERO_GRAM_NORM" for w in res_centered_zero.warnings)

    # Zero Gram norm uncentered
    k_zeros = np.zeros((3, 3))
    res_uncentered_zero = kta(k_zeros, np.eye(3), centered=False)
    assert res_uncentered_zero.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_uncentered_zero.value)
    assert any(w.code == "W_METRIC_ZERO_GRAM_NORM" for w in res_uncentered_zero.warnings)

    # Valid centered KTA between two distinct non-trivial Gram matrices
    k_a = np.array([[2.0, 1.0], [1.0, 3.0]])
    k_b = np.array([[3.0, 0.5], [0.5, 2.0]])
    res_centered = kta(k_a, k_b, centered=True)
    assert res_centered.status == MetricStatus.VALID
    assert -1.0 <= res_centered.value <= 1.0


# =============================================================================
# C15: Discrete classification metrics accuracy, balanced_accuracy, precision, recall, and f1 operate within rtol=1e-14, atol=1e-15 (MET-12)
# =============================================================================
def test_discrete_classification_accuracy() -> None:
    """Validate discrete classification metrics analytical accuracy on known matrix."""
    yt = np.array([0, 0, 1, 1, 1, 1])
    yp = np.array([0, 1, 0, 1, 1, 1])

    # Accuracy: 4 / 6 = 2/3
    res_acc = accuracy(yt, yp)
    assert res_acc.metric_id == "accuracy"
    assert res_acc.status == MetricStatus.VALID
    assert math.isclose(res_acc.value, 4.0 / 6.0, rel_tol=1e-14, abs_tol=1e-15)

    # Precision (binary, pos_label=1): TP=3, FP=1 -> 3/4 = 0.75
    res_prec_bin = precision(yt, yp, average="binary", pos_label=1)
    assert res_prec_bin.metric_id == "precision"
    assert res_prec_bin.status == MetricStatus.VALID
    assert math.isclose(res_prec_bin.value, 0.75, rel_tol=1e-14, abs_tol=1e-15)

    # Recall (binary, pos_label=1): TP=3, FN=1 -> 3/4 = 0.75
    res_rec_bin = recall(yt, yp, average="binary", pos_label=1)
    assert res_rec_bin.metric_id == "recall"
    assert res_rec_bin.status == MetricStatus.VALID
    assert math.isclose(res_rec_bin.value, 0.75, rel_tol=1e-14, abs_tol=1e-15)

    # F1 (binary, pos_label=1): 2*3 / (2*3 + 1 + 1) = 6/8 = 0.75
    res_f1_bin = f1(yt, yp, average="binary", pos_label=1)
    assert res_f1_bin.metric_id == "f1"
    assert res_f1_bin.status == MetricStatus.VALID
    assert math.isclose(res_f1_bin.value, 0.75, rel_tol=1e-14, abs_tol=1e-15)

    # Balanced accuracy: Recall_0 = 1/2 = 0.5, Recall_1 = 3/4 = 0.75 -> mean = 0.625
    res_bacc = balanced_accuracy(yt, yp)
    assert res_bacc.metric_id == "balanced_accuracy"
    assert res_bacc.status == MetricStatus.VALID
    assert math.isclose(res_bacc.value, 0.625, rel_tol=1e-14, abs_tol=1e-15)

    # Multiclass macro & weighted
    # Precisions: class 0 -> 1/2 = 0.5, class 1 -> 3/4 = 0.75
    res_prec_macro = precision(yt, yp, average="macro")
    assert math.isclose(res_prec_macro.value, 0.625, rel_tol=1e-14, abs_tol=1e-15)

    res_prec_weighted = precision(yt, yp, average="weighted")
    # weighted: (0.5 * 2 + 0.75 * 4) / 6 = (1.0 + 3.0) / 6 = 4/6 = 2/3
    assert math.isclose(res_prec_weighted.value, 4.0 / 6.0, rel_tol=1e-14, abs_tol=1e-15)

    # F1 macro: F1_0 = 2*1 / (2*1 + 1 + 1) = 2/4 = 0.5, F1_1 = 0.75 -> mean = 0.625
    res_f1_macro = f1(yt, yp, average="macro")
    assert math.isclose(res_f1_macro.value, 0.625, rel_tol=1e-14, abs_tol=1e-15)


# =============================================================================
# C16: precision returns UNDEFINED_NAN when TP + FP = 0 and valid 0.0 when TP = 0 with FP > 0 (MET-13)
# =============================================================================
def test_precision_division_by_zero_rules() -> None:
    """Validate precision division by zero rules and valid 0.0."""
    # TP + FP == 0 (no positive predictions made) -> UNDEFINED_NAN
    yt_bin = np.array([0, 1, 1])
    yp_zero_pred = np.array([0, 0, 0])
    res_undef = precision(yt_bin, yp_zero_pred, pos_label=1)
    assert res_undef.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_undef.value)
    assert any(w.code == "W_METRIC_ZERO_PREDICTIONS" for w in res_undef.warnings)

    # TP == 0 with FP > 0 -> valid 0.0
    yt_zeros = np.array([0, 0, 0])
    yp_fps = np.array([1, 0, 0])  # 1 false positive, 0 true positives
    res_valid_zero = precision(yt_zeros, yp_fps, pos_label=1)
    assert res_valid_zero.status == MetricStatus.VALID
    assert res_valid_zero.value == 0.0


# =============================================================================
# C17: recall and balanced_accuracy return UNDEFINED_NAN for absent classes (TP + FN = 0) and valid 0.0 when TP = 0 with FN > 0 (MET-14)
# =============================================================================
def test_recall_and_balanced_accuracy_rules() -> None:
    """Validate recall and balanced_accuracy absent class and valid 0.0 rules."""
    # TP + FN == 0 (pos_label absent in y_true) -> UNDEFINED_NAN
    yt_no_pos = np.array([0, 0, 0])
    yp_any = np.array([0, 1, 0])
    res_rec_undef = recall(yt_no_pos, yp_any, pos_label=1)
    assert res_rec_undef.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_rec_undef.value)
    assert any(w.code == "W_METRIC_ABSENT_CLASS" for w in res_rec_undef.warnings)

    # Balanced accuracy with single class target -> UNDEFINED_NAN
    res_bacc_mono = balanced_accuracy(np.array([1, 1, 1]), np.array([1, 1, 1]))
    assert res_bacc_mono.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_bacc_mono.value)
    assert any(w.code == "W_METRIC_INSUFFICIENT_CLASSES" for w in res_bacc_mono.warnings)

    # Balanced accuracy with explicit labels containing absent class -> UNDEFINED_NAN
    res_bacc_absent = balanced_accuracy(np.array([0, 0]), np.array([0, 1]), labels=[0, 1])
    assert res_bacc_absent.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_bacc_absent.value)
    assert any(w.code == "W_METRIC_ABSENT_CLASS" for w in res_bacc_absent.warnings)

    # TP == 0 with FN > 0 -> valid 0.0 for recall
    yt_has_pos = np.array([1, 1, 0])
    yp_no_pos = np.array([0, 0, 0])
    res_rec_zero = recall(yt_has_pos, yp_no_pos, pos_label=1)
    assert res_rec_zero.status == MetricStatus.VALID
    assert res_rec_zero.value == 0.0

    # Balanced accuracy with all classes present and one having recall 0.0 -> valid
    # class 0: TP=1, FN=0 -> recall=1.0; class 1: TP=0, FN=2 -> recall=0.0 -> mean = 0.5
    res_bacc_valid = balanced_accuracy(yt_has_pos, yp_no_pos)
    assert res_bacc_valid.status == MetricStatus.VALID
    assert math.isclose(res_bacc_valid.value, 0.5, rel_tol=1e-14, abs_tol=1e-15)


# =============================================================================
# C18: f1 computes 2*TP / (2*TP + FP + FN), returning UNDEFINED_NAN only for zero denominator and valid 0.0 when denominator > 0 with TP = 0 (MET-14)
# =============================================================================
def test_f1_own_denominator_rules() -> None:
    """Validate F1 own denominator evaluation, UNDEFINED_NAN and valid 0.0."""
    # Denominator (2*TP + FP + FN) == 0 -> UNDEFINED_NAN
    yt_zeros = np.array([0, 0, 0])
    yp_zeros = np.array([0, 0, 0])
    res_f1_undef = f1(yt_zeros, yp_zeros, pos_label=1)
    assert res_f1_undef.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_f1_undef.value)
    assert any(w.code == "W_METRIC_F1_ZERO_SUPPORT" for w in res_f1_undef.warnings)

    # Subcase A: TP=0, FP=0, FN=2 > 0 -> Denominator=2, Numerator=0 -> valid 0.0
    yt_a = np.array([1, 1, 0])
    yp_a = np.array([0, 0, 0])
    res_f1_a = f1(yt_a, yp_a, pos_label=1)
    assert res_f1_a.status == MetricStatus.VALID
    assert res_f1_a.value == 0.0

    # Subcase B: TP=0, FP=2 > 0, FN=0 -> Denominator=2, Numerator=0 -> valid 0.0
    yt_b = np.array([0, 0, 0])
    yp_b = np.array([1, 1, 0])
    res_f1_b = f1(yt_b, yp_b, pos_label=1)
    assert res_f1_b.status == MetricStatus.VALID
    assert res_f1_b.value == 0.0

    # Subcase C: TP=0, FP=1, FN=1 -> Denominator=2, Numerator=0 -> valid 0.0
    yt_c = np.array([1, 0])
    yp_c = np.array([0, 1])
    res_f1_c = f1(yt_c, yp_c, pos_label=1)
    assert res_f1_c.status == MetricStatus.VALID
    assert res_f1_c.value == 0.0


# =============================================================================
# C19: roc_auc resolves ties via mid-ranks and computes multiclass OVR macro/weighted (MET-15)
# =============================================================================
def test_roc_auc_ties_and_ovr() -> None:
    """Validate ROC AUC calculation, tie resolution via mid-ranks, and multiclass OVR."""
    # Constant scores yield exactly 0.5
    yt_bin = np.array([0, 0, 1, 1])
    scores_const = np.array([0.5, 0.5, 0.5, 0.5])
    res_const = roc_auc(yt_bin, scores_const)
    assert res_const.metric_id == "roc_auc"
    assert res_const.status == MetricStatus.VALID
    assert math.isclose(res_const.value, 0.5, rel_tol=1e-12, abs_tol=1e-12)

    # Ties resolved via mid-ranks: scores [0.1, 0.4, 0.4, 0.8] -> AUC = 0.875
    scores_ties = np.array([0.1, 0.4, 0.4, 0.8])
    res_ties = roc_auc(yt_bin, scores_ties)
    assert res_ties.status == MetricStatus.VALID
    assert math.isclose(res_ties.value, 0.875, rel_tol=1e-12, abs_tol=1e-12)

    # Input dimensionality: (n, 1) and (n, 2) give same result as 1D
    res_2d_col = roc_auc(yt_bin, scores_ties[:, np.newaxis])
    assert math.isclose(res_2d_col.value, 0.875, rel_tol=1e-12, abs_tol=1e-12)

    scores_2col = np.column_stack([1.0 - scores_ties, scores_ties])
    res_2col = roc_auc(yt_bin, scores_2col)
    assert math.isclose(res_2col.value, 0.875, rel_tol=1e-12, abs_tol=1e-12)

    # Single-class target yields UNDEFINED_NAN
    res_single = roc_auc(np.array([1, 1, 1]), np.array([0.2, 0.4, 0.6]))
    assert res_single.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_single.value)
    assert any(w.code == "W_METRIC_INSUFFICIENT_CLASSES" for w in res_single.warnings)

    # Multiclass OVR (3 classes)
    yt_multi = np.array([0, 1, 2, 0, 1, 2])
    # Perfectly separated scores
    scores_multi = np.array([
        [0.9, 0.05, 0.05],
        [0.1, 0.8, 0.1],
        [0.05, 0.05, 0.9],
        [0.85, 0.1, 0.05],
        [0.05, 0.9, 0.05],
        [0.1, 0.1, 0.8],
    ])
    res_multi_macro = roc_auc(yt_multi, scores_multi, average="macro")
    assert res_multi_macro.status == MetricStatus.VALID
    assert math.isclose(res_multi_macro.value, 1.0, rel_tol=1e-12, abs_tol=1e-12)

    res_multi_weighted = roc_auc(yt_multi, scores_multi, average="weighted")
    assert res_multi_weighted.status == MetricStatus.VALID
    assert math.isclose(res_multi_weighted.value, 1.0, rel_tol=1e-12, abs_tol=1e-12)

    # Multiclass OVR with absent class in labels yields UNDEFINED_NAN
    res_multi_absent = roc_auc(yt_multi, np.zeros((6, 4)), labels=[0, 1, 2, 3])
    assert res_multi_absent.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_multi_absent.value)
    assert any(w.code == "W_METRIC_ABSENT_CLASS" for w in res_multi_absent.warnings)


# =============================================================================
# C20: log_loss validates distributions, applies clipping eps=1e-15, and single-class y_true returns UNDEFINED_NAN (MET-16, MET-17)
# =============================================================================
def test_log_loss_validation_and_clipping() -> None:
    """Validate log_loss probability bounds, clipping, row-sum validation and single-class handling."""
    # Binary analytical accuracy
    yt_bin = np.array([0, 1])
    yp_bin = np.array([0.1, 0.8])
    # loss = -0.5 * (log(1 - 0.1) + log(0.8)) = -0.5 * (log(0.9) + log(0.8))
    expected_loss = float(-0.5 * (math.log(0.9) + math.log(0.8)))
    res_bin = log_loss(yt_bin, yp_bin)
    assert res_bin.metric_id == "log_loss"
    assert res_bin.status == MetricStatus.VALID
    assert math.isclose(res_bin.value, expected_loss, rel_tol=1e-9, abs_tol=1e-11)

    # Clipping: exact 0.0 and 1.0 probabilities clipped to eps=1e-15 without overflow/inf
    yt_edge = np.array([0, 1])
    yp_edge = np.array([1.0, 0.0])  # Completely wrong predictions
    res_edge = log_loss(yt_edge, yp_edge, eps=1e-15)
    assert res_edge.status == MetricStatus.VALID
    assert math.isfinite(res_edge.value)
    # Expected: -0.5 * (log(1e-15) + log(1e-15)) = -log(1e-15) ~ 34.538776394910684
    assert math.isclose(res_edge.value, -math.log(1e-15), rel_tol=1e-9, abs_tol=1e-11)

    # Single-class target yields UNDEFINED_NAN
    res_single = log_loss(np.array([1, 1, 1]), np.array([0.5, 0.5, 0.5]))
    assert res_single.status == MetricStatus.UNDEFINED_NAN
    assert math.isnan(res_single.value)
    assert any(w.code == "W_METRIC_INSUFFICIENT_CLASSES" for w in res_single.warnings)

    # Invalid probability (< -1e-12 or > 1 + 1e-12) raises DataIntegrityError
    with pytest.raises(DataIntegrityError):
        log_loss(yt_bin, np.array([-0.05, 0.8]))

    with pytest.raises(DataIntegrityError):
        log_loss(yt_bin, np.array([0.1, 1.2]))

    # Row sums not summing to 1.0 raises DataIntegrityError in 2D
    yp_bad_sum = np.array([[0.3, 0.3], [0.5, 0.5]])  # Row 0 sums to 0.6
    with pytest.raises(DataIntegrityError):
        log_loss(yt_bin, yp_bad_sum)

    # 1D for 3 classes raises DataIntegrityError
    yt_3class = np.array([0, 1, 2])
    with pytest.raises(DataIntegrityError):
        log_loss(yt_3class, np.array([0.2, 0.5, 0.3]))


# =============================================================================
# C3: METRICS_CATALOG registers all 15 metrics with compare_by_abs=True on mbe and False on others (MET-02)
# =============================================================================
def test_metrics_catalog_registration() -> None:
    """Validate METRICS_CATALOG registration, immutability, and compare_by_abs flags."""
    expected_metrics = {
        "mae",
        "rmse",
        "mbe",
        "r2",
        "rmse_rel_pct",
        "mape",
        "pearson",
        "kta",
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "log_loss",
    }
    assert len(METRICS_CATALOG) == 15
    assert set(METRICS_CATALOG.keys()) == expected_metrics

    # mbe is the only metric with compare_by_abs=True
    assert METRICS_CATALOG["mbe"].compare_by_abs is True
    assert METRICS_CATALOG["mbe"].direction == MetricDirection.MINIMIZE

    for m_id, spec in METRICS_CATALOG.items():
        if m_id != "mbe":
            assert spec.compare_by_abs is False, f"Expected compare_by_abs=False for {m_id}"

    # Immutability: catalog cannot be modified
    with pytest.raises((TypeError, AttributeError)):
        METRICS_CATALOG["new_metric"] = METRICS_CATALOG["mae"]  # type: ignore[index]


# =============================================================================
# C4: get_metric_spec and compute_metric resolve metrics and reject unknown ids with ConfigurationError (MET-03)
# =============================================================================
def test_catalog_query_and_dispatch() -> None:
    """Validate get_metric_spec resolution, list_metrics filtering, and compute_metric dispatch."""
    # Exact and case-insensitive resolution
    spec_exact = get_metric_spec("rmse")
    assert spec_exact.metric_id == "rmse"

    spec_upper = get_metric_spec("  RMSE  ")
    assert spec_upper.metric_id == "rmse"

    # Unknown metric raises ConfigurationError
    with pytest.raises(ConfigurationError):
        get_metric_spec("non_existent_metric")

    # list_metrics returns sorted tuple
    all_metrics = list_metrics()
    assert len(all_metrics) == 15
    assert all_metrics == tuple(sorted(all_metrics))

    # list_metrics filtered by task
    reg_metrics = list_metrics(TaskType.REGRESSION)
    assert "rmse" in reg_metrics
    assert "accuracy" not in reg_metrics

    clf_metrics = list_metrics(TaskType.BINARY_CLASSIFICATION)
    assert "accuracy" in clf_metrics
    assert "rmse" not in clf_metrics

    # String task type coercion
    clf_str_metrics = list_metrics("BINARY_CLASSIFICATION")
    assert clf_str_metrics == clf_metrics

    with pytest.raises(ConfigurationError):
        list_metrics("UNKNOWN_TASK")

    # compute_metric dispatch
    res = compute_metric("mae", [1.0, 2.0], [1.5, 2.5])
    assert res.metric_id == "mae"
    assert res.status == MetricStatus.VALID
    assert math.isclose(res.value, 0.5)

    # compute_metric with forwarded kwargs
    res_scope = compute_metric(
        "mae",
        [1.0, 2.0],
        [1.5, 2.5],
        scope=MetricEvaluationScope.POOLED_OOF,
    )
    assert res_scope.scope == MetricEvaluationScope.POOLED_OOF


# =============================================================================
# C21: Function is_better respects compare_by_abs, coverage precedence, and UNDEFINED_NAN rules (MET-18)
# =============================================================================
def test_is_better_adr005_rules() -> None:
    """Validate is_better comparison rules, compare_by_abs, and coverage precedence."""
    # MBE: compare_by_abs -> abs(-0.1) = 0.1 < abs(0.5) = 0.5 -> -0.1 is better!
    mv_mbe1 = MetricValue(
        metric_id="mbe",
        value=-0.1,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )
    mv_mbe2 = MetricValue(
        metric_id="mbe",
        value=0.5,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )
    assert is_better(mv_mbe1, mv_mbe2) is True
    assert is_better(mv_mbe2, mv_mbe1) is False

    # Standard RMSE: 1.2 is better than 1.5
    mv_rmse1 = MetricValue(
        metric_id="rmse",
        value=1.2,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )
    mv_rmse2 = MetricValue(
        metric_id="rmse",
        value=1.5,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )
    assert is_better(mv_rmse1, mv_rmse2) is True
    assert is_better(mv_rmse2, mv_rmse1) is False

    # Accuracy (MAXIMIZE): 0.9 is better than 0.8
    mv_acc1 = MetricValue(
        metric_id="accuracy",
        value=0.9,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )
    mv_acc2 = MetricValue(
        metric_id="accuracy",
        value=0.8,
        status=MetricStatus.VALID,
        direction=MetricDirection.MAXIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )
    assert is_better(mv_acc1, mv_acc2) is True
    assert is_better(mv_acc2, mv_acc1) is False

    # Status precedence: VALID beats PARTIAL_COVERAGE even with higher RMSE
    agg_valid = AggregatedMetricValue(
        metric_id="rmse",
        mean=1.5,
        std=0.1,
        median=1.5,
        iqr=0.05,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=AggregationScope.FOLD_AGGREGATION,
        valid_folds=5,
        total_folds=5,
        coverage=1.0,
    )
    agg_partial = AggregatedMetricValue(
        metric_id="rmse",
        mean=0.8,  # numerically lower, but partial coverage!
        std=0.1,
        median=0.8,
        iqr=0.05,
        status=MetricStatus.PARTIAL_COVERAGE,
        direction=MetricDirection.MINIMIZE,
        scope=AggregationScope.FOLD_AGGREGATION,
        valid_folds=4,
        total_folds=5,
        coverage=0.8,
    )
    assert is_better(agg_valid, agg_partial) is True
    assert is_better(agg_partial, agg_valid) is False

    # Higher coverage beats lower coverage between two PARTIAL_COVERAGE candidates
    agg_partial_lower_cov = AggregatedMetricValue(
        metric_id="rmse",
        mean=0.5,
        std=0.1,
        median=0.5,
        iqr=0.05,
        status=MetricStatus.PARTIAL_COVERAGE,
        direction=MetricDirection.MINIMIZE,
        scope=AggregationScope.FOLD_AGGREGATION,
        valid_folds=3,
        total_folds=5,
        coverage=0.6,
    )
    assert is_better(agg_partial, agg_partial_lower_cov) is True
    assert is_better(agg_partial_lower_cov, agg_partial) is False

    # Rankable beats UNDEFINED_NAN; two UNDEFINED_NAN return False
    mv_undef = MetricValue(
        metric_id="rmse",
        value=float("nan"),
        status=MetricStatus.UNDEFINED_NAN,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )
    assert is_better(mv_rmse1, mv_undef) is True
    assert is_better(mv_undef, mv_rmse1) is False
    assert is_better(mv_undef, mv_undef) is False


# =============================================================================
# C22: aggregate_fold_metrics and rank_configurations enforce coverage stats and strict lexicographic ordering (MET-19, MET-20)
# =============================================================================
def test_aggregate_and_rank_configurations() -> None:
    """Validate aggregate_fold_metrics statistics and rank_configurations lexicographic sorting."""
    mv_rmse1 = MetricValue(
        metric_id="rmse",
        value=1.2,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )
    mv_mbe1 = MetricValue(
        metric_id="mbe",
        value=-0.1,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )
    mv_undef = MetricValue(
        metric_id="rmse",
        value=float("nan"),
        status=MetricStatus.UNDEFINED_NAN,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )

    # aggregate_fold_metrics: 5/5 valid -> VALID
    folds_valid = [
        MetricValue(
            metric_id="rmse",
            value=1.0 + i * 0.1,
            status=MetricStatus.VALID,
            direction=MetricDirection.MINIMIZE,
            scope=MetricEvaluationScope.PER_FOLD,
            n_samples=20,
        )
        for i in range(5)
    ]
    res_agg_valid = aggregate_fold_metrics(folds_valid)
    assert res_agg_valid.status == MetricStatus.VALID
    assert res_agg_valid.valid_folds == 5
    assert res_agg_valid.total_folds == 5
    assert res_agg_valid.coverage == 1.0
    assert math.isclose(res_agg_valid.mean, 1.2, rel_tol=1e-12)

    # 4/5 valid, 1 UNDEFINED_NAN -> PARTIAL_COVERAGE
    folds_partial = list(folds_valid[:4]) + [mv_undef]
    res_agg_part = aggregate_fold_metrics(folds_partial)
    assert res_agg_part.status == MetricStatus.PARTIAL_COVERAGE
    assert res_agg_part.valid_folds == 4
    assert res_agg_part.total_folds == 5
    assert res_agg_part.coverage == 0.8
    assert any(w.code == "W_METRIC_PARTIAL_COVERAGE" for w in res_agg_part.warnings)

    # 0/5 valid -> UNDEFINED_NAN
    folds_zero = [mv_undef, mv_undef, mv_undef]
    res_agg_zero = aggregate_fold_metrics(folds_zero)
    assert res_agg_zero.status == MetricStatus.UNDEFINED_NAN
    assert res_agg_zero.valid_folds == 0
    assert res_agg_zero.coverage == 0.0
    assert math.isnan(res_agg_zero.mean)
    assert any(w.code == "W_METRIC_ZERO_COVERAGE" for w in res_agg_zero.warnings)

    # Inconsistent metric_id raises DataIntegrityError
    mismatched = [mv_rmse1, mv_mbe1]
    with pytest.raises(DataIntegrityError):
        aggregate_fold_metrics(mismatched)

    # Invalid scope (PER_FOLD) raises ConfigurationError
    with pytest.raises(ConfigurationError):
        aggregate_fold_metrics(folds_valid, scope="PER_FOLD")  # type: ignore[arg-type]

    # Rank configurations lexicographic sorting
    cand_a = AggregatedMetricValue(
        metric_id="rmse",
        mean=1.5,
        std=0.1,
        median=1.5,
        iqr=0.05,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=AggregationScope.FOLD_AGGREGATION,
        valid_folds=5,
        total_folds=5,
        coverage=1.0,
    )
    cand_b = AggregatedMetricValue(
        metric_id="rmse",
        mean=1.2,
        std=0.1,
        median=1.2,
        iqr=0.05,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope=AggregationScope.FOLD_AGGREGATION,
        valid_folds=5,
        total_folds=5,
        coverage=1.0,
    )
    cand_c = AggregatedMetricValue(
        metric_id="rmse",
        mean=0.8,
        std=0.1,
        median=0.8,
        iqr=0.05,
        status=MetricStatus.PARTIAL_COVERAGE,
        direction=MetricDirection.MINIMIZE,
        scope=AggregationScope.FOLD_AGGREGATION,
        valid_folds=4,
        total_folds=5,
        coverage=0.8,
    )
    cand_d = AggregatedMetricValue(
        metric_id="rmse",
        mean=0.6,
        std=0.1,
        median=0.6,
        iqr=0.05,
        status=MetricStatus.PARTIAL_COVERAGE,
        direction=MetricDirection.MINIMIZE,
        scope=AggregationScope.FOLD_AGGREGATION,
        valid_folds=3,
        total_folds=5,
        coverage=0.6,
    )
    cand_e = MetricValue(
        metric_id="rmse",
        value=float("nan"),
        status=MetricStatus.UNDEFINED_NAN,
        direction=MetricDirection.MINIMIZE,
        scope=MetricEvaluationScope.PER_FOLD,
        n_samples=50,
    )

    candidates = {
        "model_a": cand_a,
        "model_b": cand_b,
        "model_c": cand_c,
        "model_d": cand_d,
        "model_e": cand_e,
    }

    ranking = rank_configurations(candidates)
    assert len(ranking) == 5

    # Rank 1: model_b (VALID, mean 1.2)
    assert ranking[0].candidate_id == "model_b"
    assert ranking[0].rank == 1
    assert ranking[0].status == MetricStatus.VALID

    # Rank 2: model_a (VALID, mean 1.5)
    assert ranking[1].candidate_id == "model_a"
    assert ranking[1].rank == 2
    assert ranking[1].status == MetricStatus.VALID

    # Rank 3: model_c (PARTIAL_COVERAGE, coverage 0.8)
    assert ranking[2].candidate_id == "model_c"
    assert ranking[2].rank == 3
    assert ranking[2].status == MetricStatus.PARTIAL_COVERAGE

    # Rank 4: model_d (PARTIAL_COVERAGE, coverage 0.6)
    assert ranking[3].candidate_id == "model_d"
    assert ranking[3].rank == 4
    assert ranking[3].status == MetricStatus.PARTIAL_COVERAGE

    # Rank None: model_e (UNRANKABLE)
    assert ranking[4].candidate_id == "model_e"
    assert ranking[4].rank is None
    assert ranking[4].status == MetricStatus.UNRANKABLE

    # MBE ranking with compare_by_abs
    mbe_candidates = {
        "model_pos": MetricValue(
            metric_id="mbe",
            value=0.2,
            status=MetricStatus.VALID,
            direction=MetricDirection.MINIMIZE,
            scope=MetricEvaluationScope.PER_FOLD,
            n_samples=10,
        ),
        "model_neg_small": MetricValue(
            metric_id="mbe",
            value=-0.05,
            status=MetricStatus.VALID,
            direction=MetricDirection.MINIMIZE,
            scope=MetricEvaluationScope.PER_FOLD,
            n_samples=10,
        ),
        "model_neg_large": MetricValue(
            metric_id="mbe",
            value=-0.8,
            status=MetricStatus.VALID,
            direction=MetricDirection.MINIMIZE,
            scope=MetricEvaluationScope.PER_FOLD,
            n_samples=10,
        ),
    }

    mbe_ranking = rank_configurations(mbe_candidates)
    assert len(mbe_ranking) == 3
    # abs(-0.05)=0.05 (rank 1), abs(0.2)=0.2 (rank 2), abs(-0.8)=0.8 (rank 3)
    assert mbe_ranking[0].candidate_id == "model_neg_small"
    assert mbe_ranking[0].rank == 1
    assert mbe_ranking[1].candidate_id == "model_pos"
    assert mbe_ranking[1].rank == 2
    assert mbe_ranking[2].candidate_id == "model_neg_large"
    assert mbe_ranking[2].rank == 3






