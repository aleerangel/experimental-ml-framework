"""Kolmogorov-Smirnov, Lilliefors, dataset-shift, and residual diagnostics in pure Python/NumPy (XCUT-02, VAL-ENH-006)."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

import numpy as np


@dataclass(frozen=True, slots=True)
class KSTestResult:
    """Result of a 1-sample or 2-sample Kolmogorov-Smirnov test."""

    statistic: float
    p_value: float
    n_a: int
    n_b: int | None
    method: str
    status: str = "VALID"


@dataclass(frozen=True, slots=True)
class ResidualDistributionFit:
    """Goodness-of-fit comparison (Lilliefors + Normal vs. Student-t AIC) for OOF residuals."""

    n_samples: int
    mean: float
    std: float
    lilliefors_d: float
    lilliefors_p: float
    normal_loglik: float
    normal_aic: float
    student_t_nu: float
    student_t_loglik: float
    student_t_aic: float
    preferred_family: str
    heavy_tails_detected: bool


@dataclass(frozen=True, slots=True)
class FeatureDriftRecord:
    """KS 2-sample drift diagnostic for a single numeric column between two partitions."""

    feature_name: str
    is_target: bool
    ks_statistic: float
    p_value: float
    n_ref: int
    n_cmp: int
    drift_detected: bool
    status: str = "VALID"


@dataclass(frozen=True, slots=True)
class PartitionDriftReport:
    """Summary of KS dataset-shift checks between reference and comparison partitions."""

    regime: str
    reference_label: str
    comparison_label: str
    alpha: float
    d_threshold: float
    features: tuple[FeatureDriftRecord, ...]
    n_drifted_features: int


@dataclass(frozen=True, slots=True)
class OofResidualsDiagnosticEntry:
    """Residual normality and heavy-tail diagnostics for one (model_id, scenario_id) configuration."""

    model_id: str
    scenario_id: str
    fit: ResidualDistributionFit


def _finite_float_array(values: Sequence[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64).ravel()
    return arr[np.isfinite(arr)]


def ks_2samp(a: Sequence[float] | np.ndarray, b: Sequence[float] | np.ndarray) -> KSTestResult:
    """Compute 2-sample Kolmogorov-Smirnov statistic D and asymptotic p-value in pure NumPy."""
    xa = np.sort(_finite_float_array(a))
    xb = np.sort(_finite_float_array(b))
    n1, n2 = len(xa), len(xb)
    if n1 < 2 or n2 < 2:
        return KSTestResult(statistic=float("nan"), p_value=float("nan"), n_a=n1, n_b=n2, method="KS_2SAMP", status="INSUFFICIENT_SAMPLES")

    combined = np.concatenate([xa, xb])
    cdf1 = np.searchsorted(xa, combined, side="right") / float(n1)
    cdf2 = np.searchsorted(xb, combined, side="right") / float(n2)
    d_stat = float(np.max(np.abs(cdf1 - cdf2)))

    n_eff = (n1 * n2) / float(n1 + n2)
    sqrt_n = math.sqrt(n_eff)
    lam = (sqrt_n + 0.12 + 0.11 / sqrt_n) * d_stat
    if lam <= 0.0:
        p_val = 1.0
    else:
        p_sum = 0.0
        for k in range(1, 101):
            term = math.exp(-2.0 * (k * k) * (lam * lam))
            p_sum += (1.0 if k % 2 == 1 else -1.0) * term
            if term < 1e-12:
                break
        p_val = max(0.0, min(1.0, 2.0 * p_sum))

    return KSTestResult(statistic=d_stat, p_value=p_val, n_a=n1, n_b=n2, method="KS_2SAMP", status="VALID")


def _lilliefors_p_from_stephens(d_star: float) -> float:
    """Approximate Lilliefors p-value from Stephens (1974) modified statistic D*."""
    # Critical points from Stephens (1974) Table 1A (Normal, unknown mean & variance)
    pts_d = (0.600, 0.775, 0.819, 0.895, 0.955, 1.035, 1.250)
    pts_p = (0.500, 0.150, 0.100, 0.050, 0.025, 0.010, 0.0005)
    if d_star <= pts_d[0]:
        return 1.0 - 0.5 * (d_star / pts_d[0])
    if d_star >= pts_d[-1]:
        return max(1e-12, 0.0005 * math.exp(-6.0 * (d_star - pts_d[-1])))
    for i in range(len(pts_d) - 1):
        if pts_d[i] <= d_star <= pts_d[i + 1]:
            t = (d_star - pts_d[i]) / (pts_d[i + 1] - pts_d[i])
            return float(pts_p[i] + t * (pts_p[i + 1] - pts_p[i]))
    return 0.0005


def ks_normal_lilliefors(values: Sequence[float] | np.ndarray) -> KSTestResult:
    """Compute 1-sample Normal KS statistic with Lilliefors/Stephens (1974) correction."""
    x = np.sort(_finite_float_array(values))
    n = len(x)
    if n < 5:
        return KSTestResult(statistic=float("nan"), p_value=float("nan"), n_a=n, n_b=None, method="LILLIEFORS_NORMAL", status="INSUFFICIENT_SAMPLES")

    mean = float(np.mean(x))
    std = float(np.std(x, ddof=1))
    if std <= 1e-15 or not math.isfinite(std):
        return KSTestResult(statistic=float("nan"), p_value=float("nan"), n_a=n, n_b=None, method="LILLIEFORS_NORMAL", status="ZERO_VARIANCE")

    z = (x - mean) / std
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    cdf_norm = np.array([0.5 * (1.0 + math.erf(float(zi) * inv_sqrt2)) for zi in z], dtype=np.float64)
    idx = np.arange(1, n + 1, dtype=np.float64)
    d_plus = float(np.max(idx / n - cdf_norm))
    d_minus = float(np.max(cdf_norm - (idx - 1.0) / n))
    d_stat = max(d_plus, d_minus)

    sqrt_n = math.sqrt(float(n))
    d_star = d_stat * (sqrt_n - 0.01 + 0.85 / sqrt_n)
    p_val = _lilliefors_p_from_stephens(d_star)
    return KSTestResult(statistic=d_stat, p_value=p_val, n_a=n, n_b=None, method="LILLIEFORS_NORMAL", status="VALID")


def compare_normal_vs_student_t(values: Sequence[float] | np.ndarray) -> ResidualDistributionFit:
    """Fit Normal (MLE) vs. Student-t (EM over nu grid) and compare AIC for heavy-tail detection."""
    x = _finite_float_array(values)
    n = len(x)
    if n < 5:
        raise ValueError(f"At least 5 finite residual samples are required, got {n}.")

    mean = float(np.mean(x))
    std_sample = float(np.std(x, ddof=1))
    sigma_mle = max(float(np.std(x, ddof=0)), 1e-12)
    normal_ll = float(-0.5 * n * math.log(2.0 * math.pi * sigma_mle * sigma_mle) - 0.5 * n)
    normal_aic = 4.0 - 2.0 * normal_ll  # k = 2 (mu, sigma)

    best_nu = 30.0
    best_ll = -float("inf")
    for nu in (2.5, 3.0, 4.0, 5.0, 7.0, 10.0, 15.0, 30.0, 100.0):
        mu_t = float(np.median(x))
        mad = float(np.median(np.abs(x - mu_t)))
        s_t = max(mad * 1.4826 if mad > 1e-12 else sigma_mle, 1e-12)
        for _ in range(15):
            diff2 = ((x - mu_t) / s_t) ** 2
            w = (nu + 1.0) / (nu + diff2)
            w_sum = float(np.sum(w))
            if w_sum <= 1e-12:
                break
            mu_t = float(np.sum(w * x) / w_sum)
            s_t = max(math.sqrt(float(np.sum(w * (x - mu_t) ** 2) / n)), 1e-12)
        const = math.lgamma(0.5 * (nu + 1.0)) - math.lgamma(0.5 * nu) - 0.5 * math.log(nu * math.pi) - math.log(s_t)
        ll_t = float(n * const - 0.5 * (nu + 1.0) * np.sum(np.log1p(((x - mu_t) / s_t) ** 2 / nu)))
        if ll_t > best_ll:
            best_ll = ll_t
            best_nu = float(nu)

    student_aic = 6.0 - 2.0 * best_ll  # k = 3 (mu, sigma, nu)
    lill = ks_normal_lilliefors(x)
    heavy_tails = student_aic + 2.0 < normal_aic
    preferred = "STUDENT_T" if heavy_tails else "NORMAL"

    return ResidualDistributionFit(
        n_samples=n,
        mean=mean,
        std=std_sample,
        lilliefors_d=lill.statistic,
        lilliefors_p=lill.p_value,
        normal_loglik=normal_ll,
        normal_aic=normal_aic,
        student_t_nu=best_nu,
        student_t_loglik=best_ll,
        student_t_aic=student_aic,
        preferred_family=preferred,
        heavy_tails_detected=heavy_tails,
    )
