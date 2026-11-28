"""Unit tests for statistical association metrics and degeneracy handling (EXP-02 to EXP-05)."""

import math

import numpy as np
import pytest

from experimental_ml.core.enums import MetricStatus
from experimental_ml.features.stats import (
    compute_correlation_ratio,
    compute_cramers_v,
    compute_pearson,
    compute_spearman,
)


def test_exp_02_pearson_and_spearman_continuous() -> None:
    """Proof C2: Verify Pearson r and Spearman rho on continuous pairs with fractional ties (EXP-02)."""
    # 1. Perfect positive and negative linear relations
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pos = 2.0 * x + 3.0
    y_neg = -1.5 * x + 10.0

    r_pos, stat_pos = compute_pearson(x, y_pos)
    assert stat_pos == MetricStatus.VALID
    assert pytest.approx(r_pos, abs=1e-7) == 1.0

    rho_pos, rho_stat_pos = compute_spearman(x, y_pos)
    assert rho_stat_pos == MetricStatus.VALID
    assert pytest.approx(rho_pos, abs=1e-7) == 1.0

    r_neg, stat_neg = compute_pearson(x, y_neg)
    assert stat_neg == MetricStatus.VALID
    assert pytest.approx(r_neg, abs=1e-7) == -1.0

    rho_neg, rho_stat_neg = compute_spearman(x, y_neg)
    assert rho_stat_neg == MetricStatus.VALID
    assert pytest.approx(rho_neg, abs=1e-7) == -1.0

    # 2. Monotonic non-linear relation (y = exp(x))
    # Pearson < 1.0, but Spearman rho == 1.0
    x_mono = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    y_mono = np.exp(x_mono)

    r_m, _ = compute_pearson(x_mono, y_mono)
    rho_m, _ = compute_spearman(x_mono, y_mono)
    assert r_m < 0.95  # not strictly linear
    assert pytest.approx(rho_m, abs=1e-7) == 1.0  # strictly monotonic

    # 3. Fractional ranking for ties
    # Known canonical example with ties:
    # x = [1, 2, 2, 4], y = [1, 2, 3, 4]
    # Ranks of x: 1, 2.5, 2.5, 4
    # Ranks of y: 1, 2, 3, 4
    x_ties = np.array([1.0, 2.0, 2.0, 4.0])
    y_ties = np.array([1.0, 2.0, 3.0, 4.0])
    rho_ties, stat_ties = compute_spearman(x_ties, y_ties)
    assert stat_ties == MetricStatus.VALID
    # Exact Pearson between [1, 2.5, 2.5, 4] and [1, 2, 3, 4]:
    # covariance = ( -1.5*-1.5 + 0*-0.5 + 0*0.5 + 1.5*1.5 ) = 2.25 + 2.25 = 4.5
    # ss_x = 2.25 + 0 + 0 + 2.25 = 4.5
    # ss_y = 2.25 + 0.25 + 0.25 + 2.25 = 5.0
    # rho = 4.5 / sqrt(4.5 * 5.0) = 4.5 / sqrt(22.5) ~ 0.948683298
    expected_rho = 4.5 / math.sqrt(4.5 * 5.0)
    assert pytest.approx(rho_ties, abs=1e-6) == expected_rho


def test_exp_03_correlation_ratio_eta() -> None:
    """Proof C3: Verify Correlation Ratio eta for categorical-continuous pairs in [0, 1] (EXP-03)."""
    # 1. Perfect separation between groups: each group has identical values with distinct means -> eta == 1.0
    cats_perf = np.array(["A", "A", "B", "B", "C", "C"])
    cont_perf = np.array([10.0, 10.0, 20.0, 20.0, 30.0, 30.0])
    eta_perf, stat_perf = compute_correlation_ratio(cats_perf, cont_perf)
    assert stat_perf == MetricStatus.VALID
    assert pytest.approx(eta_perf, abs=1e-6) == 1.0

    # 2. Identical group means: between-group sum of squares is 0 -> eta == 0.0
    cats_zero = np.array(["A", "A", "B", "B"])
    cont_zero = np.array([1.0, 3.0, 1.0, 3.0])  # mean of A is 2.0, mean of B is 2.0
    eta_zero, stat_zero = compute_correlation_ratio(cats_zero, cont_zero)
    assert stat_zero == MetricStatus.VALID
    assert pytest.approx(eta_zero, abs=1e-6) == 0.0

    # 3. Known intermediate ANOVA calculation
    # Group A: [1, 2], mean = 1.5, n=2
    # Group B: [4, 5], mean = 4.5, n=2
    # Grand mean = 3.0
    # ss_between = 2*(1.5 - 3)^2 + 2*(4.5 - 3)^2 = 2*2.25 + 2*2.25 = 9.0
    # ss_total = (1-3)^2 + (2-3)^2 + (4-3)^2 + (5-3)^2 = 4 + 1 + 1 + 4 = 10.0
    # eta = sqrt(9.0 / 10.0) ~ 0.948683
    cats_inter = np.array(["A", "A", "B", "B"])
    cont_inter = np.array([1.0, 2.0, 4.0, 5.0])
    eta_inter, stat_inter = compute_correlation_ratio(cats_inter, cont_inter)
    assert stat_inter == MetricStatus.VALID
    assert pytest.approx(eta_inter, abs=1e-6) == math.sqrt(0.9)


def test_exp_04_cramers_v() -> None:
    """Proof C4: Verify Cramér's V from 2D contingency table in [0, 1] (EXP-04)."""
    # 1. Perfect association (diagonal 2x2 contingency table)
    cat_x_perf = np.array(["yes", "yes", "no", "no"])
    cat_y_perf = np.array(["1", "1", "0", "0"])
    v_perf, stat_perf = compute_cramers_v(cat_x_perf, cat_y_perf)
    assert stat_perf == MetricStatus.VALID
    assert pytest.approx(v_perf, abs=1e-6) == 1.0

    # 2. Perfect independence (uniform cross-product)
    cat_x_ind = np.array(["A", "A", "B", "B"])
    cat_y_ind = np.array(["X", "Y", "X", "Y"])
    v_ind, stat_ind = compute_cramers_v(cat_x_ind, cat_y_ind)
    assert stat_ind == MetricStatus.VALID
    assert pytest.approx(v_ind, abs=1e-6) == 0.0

    # 3. 3x2 intermediate contingency
    cat_x_3x2 = np.array(["A", "A", "B", "B", "C", "C"])
    cat_y_3x2 = np.array(["0", "1", "1", "1", "0", "0"])
    v_3x2, stat_3x2 = compute_cramers_v(cat_x_3x2, cat_y_3x2)
    assert stat_3x2 == MetricStatus.VALID
    assert 0.0 <= v_3x2 <= 1.0


def test_exp_05_degeneracy_and_undefined_nan() -> None:
    """Proof C5: Verify strict UNDEFINED_NAN handling without crashes or 0.0 substitution (EXP-05, ADR-005)."""
    # Constant vector (zero variance)
    const_arr = np.array([5.0, 5.0, 5.0, 5.0])
    var_arr = np.array([1.0, 2.0, 3.0, 4.0])

    r_const, stat_r = compute_pearson(const_arr, var_arr)
    assert math.isnan(r_const)
    assert stat_r == MetricStatus.UNDEFINED_NAN

    rho_const, stat_rho = compute_spearman(const_arr, var_arr)
    assert math.isnan(rho_const)
    assert stat_rho == MetricStatus.UNDEFINED_NAN

    # Correlation ratio on zero-variance continuous vector
    eta_zero_var, stat_eta_var = compute_correlation_ratio(np.array(["A", "B", "A", "B"]), const_arr)
    assert math.isnan(eta_zero_var)
    assert stat_eta_var == MetricStatus.UNDEFINED_NAN

    # Correlation ratio with only 1 category
    eta_one_cat, stat_eta_cat = compute_correlation_ratio(np.array(["A", "A", "A", "A"]), var_arr)
    assert math.isnan(eta_one_cat)
    assert stat_eta_cat == MetricStatus.UNDEFINED_NAN

    # Cramér's V with single category in one variable
    v_one_cat, stat_v = compute_cramers_v(np.array(["A", "A", "A"]), np.array(["X", "Y", "X"]))
    assert math.isnan(v_one_cat)
    assert stat_v == MetricStatus.UNDEFINED_NAN

    # Vectors with insufficient observations (< 2)
    r_empty, stat_empty = compute_pearson(np.array([1.0]), np.array([2.0]))
    assert math.isnan(r_empty)
    assert stat_empty == MetricStatus.UNDEFINED_NAN


def test_categorical_stats_ignore_none_values() -> None:
    """C2 (M8-03): compute_correlation_ratio and compute_cramers_v filter None/NaN pairwise without TypeError."""
    cats_none = np.array(["A", "A", None, "B", "B"], dtype=object)
    cont_vals = np.array([1.0, 1.0, 99.0, 5.0, 5.0])
    eta, stat_eta = compute_correlation_ratio(cats_none, cont_vals)
    assert stat_eta == MetricStatus.VALID
    assert pytest.approx(eta, abs=1e-6) == 1.0

    cats_nan = np.array(["A", float("nan"), "B", "B"], dtype=object)
    eta_nan, stat_eta_nan = compute_correlation_ratio(cats_nan, np.array([1.0, 2.0, 5.0, 5.0]))
    assert stat_eta_nan == MetricStatus.VALID
    assert pytest.approx(eta_nan, abs=1e-6) == 1.0

    cat_x = np.array(["yes", None, "no", "no", "yes"], dtype=object)
    cat_y = np.array(["1", "1", "0", None, "1"], dtype=object)
    v, stat_v = compute_cramers_v(cat_x, cat_y)
    assert stat_v == MetricStatus.VALID
    assert pytest.approx(v, abs=1e-6) == 1.0

    # Filtering leaves < 2 valid rows -> UNDEFINED_NAN
    v_deg, stat_deg = compute_cramers_v(
        np.array(["yes", None, None], dtype=object),
        np.array([None, "1", "0"], dtype=object),
    )
    assert math.isnan(v_deg)
    assert stat_deg == MetricStatus.UNDEFINED_NAN


def test_m11_3_vif_distance_corr_and_linearity() -> None:
    """M113-02: compute_vif, compute_distance_correlation e compute_linearity_score em NumPy puro."""
    from experimental_ml.core.enums import TaskType
    from experimental_ml.features.stats import (
        compute_distance_correlation,
        compute_linearity_score,
        compute_vif,
    )

    rng = np.random.default_rng(42)
    x1 = rng.normal(size=100)
    x2 = 2.0 * x1 + rng.normal(scale=0.05, size=100)  # alta colinearidade com x1
    x3 = rng.normal(size=100)
    vifs, vif_stat = compute_vif(np.column_stack([x1, x2, x3]))
    assert vif_stat == MetricStatus.VALID
    assert vifs[0] > 10.0 and vifs[1] > 10.0
    assert vifs[2] < 2.0

    # Relação quadrática não-linear: Pearson ~ 0, mas Distance Correlation > 0.4
    x_quad = np.linspace(-2.0, 2.0, 120)
    y_quad = x_quad ** 2
    dcor, dcor_stat = compute_distance_correlation(x_quad, y_quad)
    assert dcor_stat == MetricStatus.VALID
    assert dcor > 0.4

    # Linearidade OLS R^2 em regressão
    y_lin = 3.0 * x1 - 1.5 * x3 + 2.0
    r2_lin, lin_stat = compute_linearity_score(np.column_stack([x1, x3]), y_lin, TaskType.REGRESSION)
    assert lin_stat == MetricStatus.VALID
    assert r2_lin > 0.99

    # Separabilidade linear em classificação
    x_clf = np.vstack([rng.normal(-2.0, 0.3, size=(30, 2)), rng.normal(2.0, 0.3, size=(30, 2))])
    y_clf = np.array(["A"] * 30 + ["B"] * 30, dtype=object)
    bal_acc, clf_stat = compute_linearity_score(x_clf, y_clf, TaskType.BINARY_CLASSIFICATION)
    assert clf_stat == MetricStatus.VALID
    assert bal_acc > 0.95

