"""Pure Python/NumPy statistical distribution functions (XCUT-02).

Provides regularized incomplete beta function I_x(a, b) via Lentz's continued
fraction and exact Student-t CDF, two-sided p-value, and quantile functions
without any runtime dependency on SciPy.
"""

from __future__ import annotations

import math


_TINY = 1e-30
_EPS = 1e-15
_MAX_ITER = 300


def _betacf(a: float, b: float, x: float) -> float:
    """Evaluate continued fraction for incomplete beta function using modified Lentz method."""
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0

    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < _TINY:
        d = _TINY
    d = 1.0 / d
    h = d

    for m in range(1, _MAX_ITER + 1):
        m2 = 2 * m
        # Even step
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _TINY:
            d = _TINY
        c = 1.0 + aa / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        h *= d * c

        # Odd step
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _TINY:
            d = _TINY
        c = 1.0 + aa / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) <= _EPS:
            break

    return h


def betainc_reg(a: float, b: float, x: float) -> float:
    """Compute the regularized incomplete beta function I_x(a, b) for x in [0, 1]."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0

    log_bt = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log(1.0 - x)
    )
    bt = math.exp(log_bt)

    if x < (a + 1.0) / (a + b + 2.0):
        return min(1.0, max(0.0, bt * _betacf(a, b, x) / a))
    return min(1.0, max(0.0, 1.0 - bt * _betacf(b, a, 1.0 - x) / b))


def student_t_two_sided_pvalue(t_value: float, df: int) -> float:
    """Compute exact two-sided p-value P(|T_df| >= |t_value|)."""
    if math.isnan(t_value):
        return float("nan")
    if math.isinf(t_value):
        return 0.0
    if t_value == 0.0:
        return 1.0
    x = df / (df + t_value * t_value)
    return min(1.0, max(0.0, betainc_reg(0.5 * df, 0.5, x)))


def student_t_cdf(t_value: float, df: int) -> float:
    """Compute exact Student-t cumulative distribution function P(T_df <= t_value)."""
    if t_value == 0.0:
        return 0.5
    p_two = student_t_two_sided_pvalue(t_value, df)
    if t_value > 0.0:
        return 1.0 - 0.5 * p_two
    return 0.5 * p_two


def student_t_ppf(q: float, df: int) -> float:
    """Compute Student-t quantile (inverse CDF) for probability q in (0, 1)."""
    if not (0.0 < q < 1.0):
        raise ValueError(f"Quantile probability q must be in (0, 1); got {q}")
    if q == 0.5:
        return 0.0

    sign = 1.0 if q > 0.5 else -1.0
    target_cdf = q if q > 0.5 else 1.0 - q

    lo = 0.0
    hi = 1.0
    while student_t_cdf(hi, df) < target_cdf:
        hi *= 2.0
        if hi > 1e12:
            break

    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if student_t_cdf(mid, df) < target_cdf:
            lo = mid
        else:
            hi = mid
        if abs(hi - lo) <= 1e-13 * max(1.0, abs(mid)):
            break

    return sign * 0.5 * (lo + hi)


def norm_two_sided_pvalue(z_value: float) -> float:
    """Compute standard normal two-sided p-value P(|Z| >= |z_value|)."""
    return math.erfc(abs(z_value) / math.sqrt(2.0))
