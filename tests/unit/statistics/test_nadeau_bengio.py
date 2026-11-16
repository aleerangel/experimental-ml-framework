"""Unit tests for pure Student-t distribution and Nadeau-Bengio paired t-test (STAT-06)."""

import math
import pytest

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.statistics._distributions import student_t_ppf, student_t_two_sided_pvalue
from experimental_ml.statistics.inference import paired_nadeau_bengio_test


def test_m62_02_student_t_exact_reference_values() -> None:
    """Verify pure NumPy/Python Student-t p-values and quantiles against analytical values."""
    # df=1 (Cauchy): P(|T| >= 12.706204736174698) == 0.05
    assert student_t_two_sided_pvalue(12.706204736174698, df=1) == pytest.approx(0.05, abs=1e-10)
    assert student_t_ppf(0.975, df=1) == pytest.approx(12.706204736174698, rel=1e-9)

    # df=2: exact quantile sqrt(2) * (1 - 2*p)/sqrt(4*p*(1-p)) -> at p=0.975: 4.302652729911275
    assert student_t_two_sided_pvalue(4.302652729911275, df=2) == pytest.approx(0.05, abs=1e-10)
    assert student_t_ppf(0.975, df=2) == pytest.approx(4.302652729911275, rel=1e-9)

    # df=4: 2.7764451051977987
    assert student_t_two_sided_pvalue(2.7764451051977987, df=4) == pytest.approx(0.05, abs=1e-10)
    assert student_t_ppf(0.975, df=4) == pytest.approx(2.7764451051977987, rel=1e-9)

    # df=10: 2.2281388519649385
    assert student_t_two_sided_pvalue(2.2281388519649385, df=10) == pytest.approx(0.05, abs=1e-10)
    assert student_t_ppf(0.975, df=10) == pytest.approx(2.2281388519649385, rel=1e-9)


def test_m62_02_corrected_variance_and_pvalue() -> None:
    """C4: Nadeau-Bengio computes corrected variance (1/J + r)*S^2, df=J-1, exact p-value and CI."""
    scores_a = [0.80, 0.82, 0.78, 0.85, 0.81]
    scores_b = [0.75, 0.76, 0.75, 0.79, 0.77]
    # diffs = [0.05, 0.06, 0.03, 0.06, 0.04], mean = 0.048
    # std (ddof=1) = sqrt(((0.002)^2 + (0.012)^2 + (-0.018)^2 + (0.012)^2 + (-0.008)^2)/4)
    # = sqrt(0.00068 / 4) = sqrt(0.00017) = 0.01303840481
    # 5-fold CV: n_val/n_train = 1/4 = 0.25
    # factor = 1/5 + 0.25 = 0.45 -> var_corr = 0.45 * 0.00017 = 0.0000765
    # se_corr = sqrt(0.0000765) = 0.008746427842
    # t = 0.048 / 0.008746427842 = 5.487954729
    res = paired_nadeau_bengio_test(scores_a, scores_b, train_val_ratios=0.25, alpha=0.05)

    assert res.degrees_of_freedom == 4
    assert res.mean_difference == pytest.approx(0.048, rel=1e-12)
    assert res.std_difference == pytest.approx(math.sqrt(0.00017), rel=1e-12)
    assert res.corrected_variance == pytest.approx(0.45 * 0.00017, rel=1e-12)
    assert res.corrected_se == pytest.approx(math.sqrt(0.45 * 0.00017), rel=1e-12)
    assert res.t_statistic == pytest.approx(0.048 / math.sqrt(0.45 * 0.00017), rel=1e-12)
    assert 0.0 < res.p_value < 0.01
    assert res.confidence_interval[0] < res.mean_difference < res.confidence_interval[1]
    assert res.warnings == ()


def test_m62_02_fold_size_cv_warning() -> None:
    """C5: Emits methodological warning when fold validation size CV exceeds 20%."""
    scores_a = [0.80, 0.82, 0.78, 0.85, 0.81]
    scores_b = [0.75, 0.76, 0.75, 0.79, 0.77]
    # Unbalanced fold sizes: CV > 20%
    fold_val_sizes = [10, 10, 10, 50, 20]
    ratios = [10 / 90, 10 / 90, 10 / 90, 50 / 50, 20 / 80]

    res = paired_nadeau_bengio_test(
        scores_a,
        scores_b,
        train_val_ratios=ratios,
        fold_val_sizes=fold_val_sizes,
        alpha=0.05,
    )
    assert res.fold_size_cv is not None and res.fold_size_cv > 0.20
    assert any("20%" in w or "coefficient of variation" in w.lower() for w in res.warnings)


def test_m62_02_zero_variance_handling() -> None:
    """C6: Zero variance differences handled safely without ZeroDivisionError."""
    # Case 1: identical scores (d_bar = 0, s^2_d = 0)
    res_equal = paired_nadeau_bengio_test([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], train_val_ratios=0.5)
    assert res_equal.mean_difference == 0.0
    assert res_equal.t_statistic == 0.0
    assert res_equal.p_value == 1.0
    assert res_equal.confidence_interval == (0.0, 0.0)
    assert any("zero_difference_variance" in w for w in res_equal.warnings)

    # Case 2: constant non-zero difference (d_bar = 0.5, s^2_d = 0)
    res_const = paired_nadeau_bengio_test([1.5, 2.5, 3.5], [1.0, 2.0, 3.0], train_val_ratios=0.5)
    assert res_const.mean_difference == pytest.approx(0.5)
    assert math.isinf(res_const.t_statistic) and res_const.t_statistic > 0
    assert res_const.p_value == 0.0
    assert res_const.confidence_interval == (0.5, 0.5)
    assert any("zero_difference_variance" in w for w in res_const.warnings)


def test_m62_02_invalid_inputs_rejected() -> None:
    """C7: Rejects J < 2, invalid alpha, negative ratios, mismatched lengths, or NaN/Inf."""
    with pytest.raises(ContractViolationError):
        paired_nadeau_bengio_test([1.0], [0.5], train_val_ratios=0.25)

    with pytest.raises(ContractViolationError):
        paired_nadeau_bengio_test([1.0, 2.0], [1.0], train_val_ratios=0.25)

    with pytest.raises(ContractViolationError):
        paired_nadeau_bengio_test([1.0, float("nan")], [1.0, 2.0], train_val_ratios=0.25)

    with pytest.raises(ConfigurationError):
        paired_nadeau_bengio_test([1.0, 2.0], [1.0, 1.5], train_val_ratios=0.25, alpha=1.0)

    with pytest.raises(ConfigurationError):
        paired_nadeau_bengio_test([1.0, 2.0], [1.0, 1.5], train_val_ratios=-0.1)
