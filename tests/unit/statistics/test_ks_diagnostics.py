"""Unit tests for M11.2 pure-NumPy KS tests, Lilliefors normality, and Normal vs. Student-t AIC."""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.statistics.distributions_diagnostics import (
    compare_normal_vs_student_t,
    ks_2samp,
    ks_normal_lilliefors,
)


def test_m11_2_ks_2samp_and_lilliefors_pure_numpy() -> None:
    """C1 (M11.2): ks_2samp and ks_normal_lilliefors compute consistent D and p-values in pure NumPy."""
    rng = np.random.default_rng(42)

    # 1. Same distribution -> small D, non-significant p
    a = rng.normal(0.0, 1.0, size=150)
    b_same = rng.normal(0.0, 1.0, size=150)
    res_same = ks_2samp(a, b_same)
    assert res_same.status == "VALID"
    assert 0.0 <= res_same.statistic < 0.25
    assert res_same.p_value > 0.05

    # 2. Shifted distribution -> large D, p < 0.01
    b_shift = rng.normal(2.5, 1.0, size=150)
    res_shift = ks_2samp(a, b_shift)
    assert res_shift.statistic > 0.65
    assert res_shift.p_value < 0.01

    # 3. Lilliefors: Normal passes (p > 0.05), Exponential fails (p < 0.01)
    lill_norm = ks_normal_lilliefors(a)
    assert lill_norm.status == "VALID"
    assert lill_norm.p_value > 0.05

    exp_samples = rng.exponential(scale=1.0, size=200)
    lill_exp = ks_normal_lilliefors(exp_samples)
    assert lill_exp.p_value < 0.01

    # 4. Normal vs Student-t AIC on heavy-tailed data (t with df=3)
    heavy = rng.standard_t(df=3.0, size=300)
    fit_heavy = compare_normal_vs_student_t(heavy)
    assert fit_heavy.heavy_tails_detected is True
    assert fit_heavy.preferred_family == "STUDENT_T"
    assert fit_heavy.student_t_aic < fit_heavy.normal_aic
