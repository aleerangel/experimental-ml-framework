"""Unit tests for paired Wilcoxon signed-rank test and paired Cohen's d_z (STAT-07)."""

import math
import pytest

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.statistics.inference import (
    compute_paired_cohens_d,
    paired_wilcoxon_test,
)
from experimental_ml.statistics.types import EffectSizeMagnitude


def test_m62_03_wilcoxon_exact_pratt_and_normal() -> None:
    """C8: Wilcoxon supports exact DP (with/without ties), wilcox vs pratt, and normal approx."""
    # Exact n=5 all positive -> W=0, p = 2/32 = 0.0625
    res5 = paired_wilcoxon_test([2.0, 3.0, 4.0, 5.0, 6.0], [1.0, 1.0, 1.0, 1.0, 1.0])
    assert res5.is_exact is True
    assert res5.n_effective == 5
    assert res5.statistic == 0.0
    assert res5.w_plus == 15.0
    assert res5.w_minus == 0.0
    assert res5.p_value == pytest.approx(0.0625, abs=1e-12)

    # Exact n=6 all positive -> W=0, p = 2/64 = 0.03125
    res6 = paired_wilcoxon_test([2, 3, 4, 5, 6, 7], [1, 1, 1, 1, 1, 1])
    assert res6.is_exact is True
    assert res6.p_value == pytest.approx(0.03125, abs=1e-12)
    assert res6.warnings == ()

    # Exact with ties: |d| = [1, 1, 1, 2, 3] -> ranks = [2, 2, 2, 4, 5]
    # signs: +, +, -, +, + -> W- = 2, W+ = 13, min = 2
    res_ties = paired_wilcoxon_test([1, 1, -1, 2, 3], [0, 0, 0, 0, 0])
    assert res_ties.is_exact is True
    assert res_ties.w_minus == pytest.approx(2.0)
    assert res_ties.w_plus == pytest.approx(13.0)
    # Out of 32 sign configs for [2,2,2,4,5]:
    # subsets summing <= 2: empty (0), {2_a}, {2_b}, {2_c} -> 4 configs. Two-sided: 8/32 = 0.25
    assert res_ties.p_value == pytest.approx(0.25, abs=1e-12)

    # Pratt vs Wilcox with zeros (small exact)
    diffs_z = [0.0, 0.0, 1.0, 2.0, 3.0, 4.0]
    zeros = [0.0] * 6
    res_wilcox = paired_wilcoxon_test(diffs_z, zeros, zero_method="wilcox")
    res_pratt = paired_wilcoxon_test(diffs_z, zeros, zero_method="pratt")
    assert res_wilcox.n_effective == 4 and res_pratt.n_effective == 4
    assert res_wilcox.w_plus == pytest.approx(10.0)
    assert res_pratt.w_plus == pytest.approx(18.0)  # ranks 3+4+5+6
    assert res_wilcox.p_value == pytest.approx(2.0 / 16.0, abs=1e-12)
    assert res_pratt.p_value == pytest.approx(2.0 / 16.0, abs=1e-12)

    # Normal approximation (n_effective = 25 > 20)
    a_large = [float(i + 1) for i in range(25)]
    b_large = [0.0] * 25
    res_norm = paired_wilcoxon_test(a_large, b_large, zero_method="wilcox")
    assert res_norm.is_exact is False
    assert res_norm.n_effective == 25
    assert res_norm.p_value < 1e-4

    # Normal approximation with Pratt and zeros (n_total=25, n_zeros=3, n_eff=22 > 20)
    a_pratt_large = [0.0, 0.0, 0.0] + [float(i + 1) for i in range(22)]
    b_pratt_large = [0.0] * 25
    res_pratt_norm = paired_wilcoxon_test(a_pratt_large, b_pratt_large, zero_method="pratt")
    assert res_pratt_norm.is_exact is False
    assert res_pratt_norm.n_effective == 22
    assert res_pratt_norm.p_value < 1e-4

    with pytest.raises(ConfigurationError):
        paired_wilcoxon_test([1.0, 2.0], [0.0, 0.0], zero_method="invalid")


def test_m62_03_wilcoxon_all_zeros() -> None:
    """C9: All zero differences return W=0.0 and p=1.0 without ZeroDivisionError."""
    for zm in ("wilcox", "pratt"):
        res = paired_wilcoxon_test([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0], zero_method=zm)
        assert res.statistic == 0.0
        assert res.w_plus == 0.0
        assert res.w_minus == 0.0
        assert res.n_effective == 0
        assert res.p_value == 1.0


def test_m62_03_wilcoxon_small_sample_warning() -> None:
    """C10: Emits warning when J < 6 or n_effective < 6."""
    # J = 5 < 6
    res_j5 = paired_wilcoxon_test([1, 2, 3, 4, 5], [0, 0, 0, 0, 0])
    assert any("0.0625" in w or "6" in w for w in res_j5.warnings)

    # J = 8 >= 6, but 4 zeros -> n_effective = 4 < 6
    res_neff4 = paired_wilcoxon_test([0, 0, 0, 0, 1, 2, 3, 4], [0] * 8)
    assert res_neff4.n_total == 8
    assert res_neff4.n_effective == 4
    assert any("n_effective" in w or "6" in w for w in res_neff4.warnings)


def test_m62_03_cohens_d_and_ci() -> None:
    """C11: Paired Cohen's d_z computes d_z, analytical CI with CV caveat, magnitude, and handles s_d=0."""
    # diffs = [1, 2, 3, 4, 5] -> mean = 3.0, std(ddof=1) = sqrt(2.5) = 1.58113883
    # d_z = 3.0 / sqrt(2.5) = 1.897366596 -> LARGE
    res = compute_paired_cohens_d([1, 2, 3, 4, 5], [0, 0, 0, 0, 0], alpha=0.05)
    expected_d = 3.0 / math.sqrt(2.5)
    assert res.cohens_d == pytest.approx(expected_d, rel=1e-12)
    assert res.magnitude == EffectSizeMagnitude.LARGE
    assert res.confidence_interval[0] is not None and res.confidence_interval[1] is not None
    assert res.confidence_interval[0] < res.cohens_d < res.confidence_interval[1]
    assert any("overlap" in w.lower() or "cv" in w.lower() for w in res.warnings)

    # Magnitude thresholds: NEGLIGIBLE, SMALL, MEDIUM
    # diffs = [0.1, -0.1, 0.1, -0.1, 0.1] -> mean = 0.02, std ~ 0.1095 -> |d| ~ 0.182 < 0.2
    res_neg = compute_paired_cohens_d([0.1, -0.1, 0.1, -0.1, 0.1], [0] * 5)
    assert res_neg.magnitude == EffectSizeMagnitude.NEGLIGIBLE

    # s_d = 0, mean = 0 -> d_z = 0.0, CI = (0.0, 0.0)
    res_zero = compute_paired_cohens_d([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert res_zero.cohens_d == 0.0
    assert res_zero.magnitude == EffectSizeMagnitude.NEGLIGIBLE
    assert res_zero.confidence_interval == (0.0, 0.0)

    # s_d = 0, mean != 0 -> d_z = +inf, CI = (None, None)
    res_const = compute_paired_cohens_d([2.0, 3.0, 4.0], [1.0, 2.0, 3.0])
    assert math.isinf(res_const.cohens_d) and res_const.cohens_d > 0
    assert res_const.magnitude == EffectSizeMagnitude.LARGE
    assert res_const.confidence_interval == (None, None)

    with pytest.raises(ContractViolationError):
        compute_paired_cohens_d([1.0], [0.0])
