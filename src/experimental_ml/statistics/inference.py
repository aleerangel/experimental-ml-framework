"""Paired inferential statistical tests and effect size estimators (STAT-06, STAT-07).

Implements pure-NumPy/Python Nadeau-Bengio corrected paired t-test,
Wilcoxon signed-rank test, and paired Cohen's d_z without SciPy (XCUT-02).
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.statistics._distributions import (
    norm_two_sided_pvalue,
    student_t_ppf,
    student_t_two_sided_pvalue,
)
from experimental_ml.statistics.types import (
    EffectSizeMagnitude,
    EffectSizeResult,
    NadeauBengioResult,
    WilcoxonResult,
)


def _validate_paired_arrays(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
) -> tuple[np.ndarray, np.ndarray]:
    """Validate and convert paired score sequences into finite 1D float64 NumPy arrays."""
    arr_a = np.asarray(scores_a, dtype=np.float64)
    arr_b = np.asarray(scores_b, dtype=np.float64)

    if arr_a.ndim != 1 or arr_b.ndim != 1:
        raise ContractViolationError("Paired score inputs must be 1-dimensional sequences.")
    if arr_a.shape[0] != arr_b.shape[0]:
        raise ContractViolationError(
            f"Paired score sequences must have identical lengths; got {arr_a.shape[0]} vs {arr_b.shape[0]}."
        )
    if arr_a.shape[0] < 2:
        raise ContractViolationError(
            f"At least J >= 2 paired folds are required for hypothesis testing; got J = {arr_a.shape[0]}."
        )
    if not (np.all(np.isfinite(arr_a)) and np.all(np.isfinite(arr_b))):
        raise ContractViolationError(
            "Paired score inputs must contain only finite values (NaN and Inf are forbidden)."
        )
    return arr_a, arr_b


def paired_nadeau_bengio_test(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    train_val_ratios: float | Sequence[float],
    fold_val_sizes: Sequence[int] | None = None,
    alpha: float = 0.05,
) -> NadeauBengioResult:
    """Execute the Nadeau-Bengio (2003) corrected paired t-test for cross-validation folds (STAT-06, ADR-004).

    Args:
        scores_a: Paired metric values for configuration A across J folds.
        scores_b: Paired metric values for configuration B across J folds.
        train_val_ratios: Scalar n_val/n_train ratio or per-fold sequence of ratios.
        fold_val_sizes: Optional per-fold validation sample counts for CV (> 20%) check.
        alpha: Significance level in (0.0, 1.0) for confidence interval.

    Returns:
        Immutable NadeauBengioResult.
    """
    if not math.isfinite(alpha) or not (0.0 < alpha < 1.0):
        raise ConfigurationError(f"Significance level alpha must be in (0.0, 1.0); got {alpha}")

    arr_a, arr_b = _validate_paired_arrays(scores_a, scores_b)
    j = int(arr_a.shape[0])
    diffs = arr_a - arr_b

    if isinstance(train_val_ratios, (int, float)):
        r_val = float(train_val_ratios)
        if not math.isfinite(r_val) or r_val < 0.0:
            raise ConfigurationError(f"train_val_ratios must be finite and >= 0; got {r_val}")
        ratios_arr = np.full(j, r_val, dtype=np.float64)
    else:
        ratios_arr = np.asarray(train_val_ratios, dtype=np.float64)
        if ratios_arr.ndim != 1 or ratios_arr.shape[0] != j:
            raise ContractViolationError(
                f"Per-fold train_val_ratios must have length J={j}; got {ratios_arr.shape}."
            )
        if not np.all(np.isfinite(ratios_arr)) or np.any(ratios_arr < 0.0):
            raise ConfigurationError("All train_val_ratios must be finite and >= 0.")

    mean_r = float(np.mean(ratios_arr))
    warnings_list: list[str] = []

    fold_size_cv: float | None = None
    if fold_val_sizes is not None:
        sizes_arr = np.asarray(fold_val_sizes, dtype=np.float64)
        if sizes_arr.ndim != 1 or sizes_arr.shape[0] != j:
            raise ContractViolationError(
                f"fold_val_sizes must have length J={j}; got {sizes_arr.shape}."
            )
        if not np.all(np.isfinite(sizes_arr)) or np.any(sizes_arr <= 0.0):
            raise ConfigurationError("All fold_val_sizes must be finite and > 0.")
        mean_sz = float(np.mean(sizes_arr))
        if mean_sz > 0.0:
            fold_size_cv = float(np.std(sizes_arr, ddof=1) / mean_sz)
    elif mean_r > 0.0 and not isinstance(train_val_ratios, (int, float)):
        fold_size_cv = float(np.std(ratios_arr, ddof=1) / mean_r)

    if fold_size_cv is not None and fold_size_cv > 0.20:
        warnings_list.append(
            f"Fold validation size coefficient of variation ({fold_size_cv:.1%}) exceeds 20%; "
            "Nadeau-Bengio exchangeability approximation using mean ratio may be stressed (ADR-004)."
        )

    mean_diff = float(np.mean(diffs))
    var_diff = float(np.var(diffs, ddof=1))
    std_diff = float(math.sqrt(var_diff))
    df = j - 1

    corrected_var = float((1.0 / j + mean_r) * var_diff)
    corrected_se = float(math.sqrt(corrected_var))

    if var_diff == 0.0:
        warnings_list.append(
            "zero_difference_variance: all paired fold differences are identical (S^2_d = 0); "
            "avoiding division by zero."
        )
        if mean_diff == 0.0:
            t_stat = 0.0
            p_val = 1.0
            ci = (0.0, 0.0)
        else:
            t_stat = math.copysign(float("inf"), mean_diff)
            p_val = 0.0
            ci = (mean_diff, mean_diff)
    else:
        t_stat = float(mean_diff / corrected_se)
        p_val = float(student_t_two_sided_pvalue(t_stat, df))
        t_crit = float(student_t_ppf(1.0 - alpha / 2.0, df))
        margin = t_crit * corrected_se
        ci = (float(mean_diff - margin), float(mean_diff + margin))

    return NadeauBengioResult(
        mean_difference=mean_diff,
        std_difference=std_diff,
        corrected_variance=corrected_var,
        corrected_se=corrected_se,
        t_statistic=t_stat,
        degrees_of_freedom=df,
        p_value=p_val,
        confidence_interval=ci,
        alpha=float(alpha),
        mean_train_val_ratio=mean_r,
        fold_size_cv=fold_size_cv,
        warnings=tuple(warnings_list),
    )


def _rank_with_ties(abs_values: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """Compute 1-based average ranks and tie group sizes for a 1D array of non-negative values."""
    n = abs_values.shape[0]
    order = np.argsort(abs_values, kind="mergesort")
    sorted_vals = abs_values[order]
    ranks_sorted = np.empty(n, dtype=np.float64)
    tie_sizes: list[int] = []

    i = 0
    while i < n:
        j = i + 1
        while j < n and sorted_vals[j] == sorted_vals[i]:
            j += 1
        avg_rank = 0.5 * ((i + 1) + j)
        ranks_sorted[i:j] = avg_rank
        count = j - i
        if count > 1:
            tie_sizes.append(count)
        i = j

    ranks = np.empty(n, dtype=np.float64)
    ranks[order] = ranks_sorted
    return ranks, tie_sizes


def _exact_wilcoxon_two_sided_p(ranks_nonzero: np.ndarray, w_stat: float) -> float:
    """Exact two-sided p-value via dynamic programming over doubled integer ranks."""
    doubled = [int(round(2.0 * r)) for r in ranks_nonzero]
    w_obs = int(round(2.0 * w_stat))
    total_sum = sum(doubled)

    dp = np.zeros(total_sum + 1, dtype=np.int64)
    dp[0] = 1
    for dr in doubled:
        dp[dr:] = dp[dr:] + dp[:-dr]

    n_eff = len(doubled)
    total_configs = 1 << n_eff
    if 2 * w_obs == total_sum:
        return 1.0
    tail_count = int(np.sum(dp[: w_obs + 1]))
    return min(1.0, (2.0 * tail_count) / total_configs)


def paired_wilcoxon_test(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    zero_method: str = "wilcox",
    alpha: float = 0.05,
) -> WilcoxonResult:
    """Execute paired Wilcoxon signed-rank test (STAT-07, ADR-004).

    Supports zero_method='wilcox' (drops zero differences) and 'pratt' (ranks all J
    observations including zeros, then drops zero ranks using Pratt's exact null mean
    and variance). Uses exact dynamic programming for n_effective <= 20 and J <= 25,
    and normal approximation with continuity and tie corrections otherwise.
    """
    if zero_method not in ("wilcox", "pratt"):
        raise ConfigurationError(
            f"Unsupported zero_method '{zero_method}'; expected 'wilcox' or 'pratt'."
        )
    if not math.isfinite(alpha) or not (0.0 < alpha < 1.0):
        raise ConfigurationError(f"Significance level alpha must be in (0.0, 1.0); got {alpha}")

    arr_a, arr_b = _validate_paired_arrays(scores_a, scores_b)
    n_total = int(arr_a.shape[0])
    diffs = arr_a - arr_b

    nonzero_mask = diffs != 0.0
    n_effective = int(np.sum(nonzero_mask))
    n_zeros = n_total - n_effective

    warnings_list: list[str] = []
    if n_total < 6 or n_effective < 6:
        warnings_list.append(
            f"Low sample size (J = {n_total}, n_effective = {n_effective} < 6): two-sided "
            "significance at alpha = 0.05 cannot be reached mathematically for n_effective <= 5 "
            "(minimum exact p-value >= 0.0625)."
        )

    if n_effective == 0:
        return WilcoxonResult(
            statistic=0.0,
            w_plus=0.0,
            w_minus=0.0,
            n_total=n_total,
            n_effective=0,
            zero_method=zero_method,
            p_value=1.0,
            is_exact=True,
            warnings=tuple(warnings_list),
        )

    if zero_method == "wilcox":
        diffs_nz = diffs[nonzero_mask]
        ranks_nz, tie_sizes_nz = _rank_with_ties(np.abs(diffs_nz))
    else:
        ranks_all, _ = _rank_with_ties(np.abs(diffs))
        diffs_nz = diffs[nonzero_mask]
        ranks_nz = ranks_all[nonzero_mask]
        _, tie_sizes_nz = _rank_with_ties(np.abs(diffs_nz))

    w_plus = float(np.sum(ranks_nz[diffs_nz > 0.0]))
    w_minus = float(np.sum(ranks_nz[diffs_nz < 0.0]))
    w_stat = min(w_plus, w_minus)

    use_exact = n_effective <= 20 and n_total <= 25
    if use_exact:
        p_val = float(_exact_wilcoxon_two_sided_p(ranks_nz, w_stat))
    else:
        tie_correction = sum(t * (t * t - 1) for t in tie_sizes_nz)
        if zero_method == "wilcox":
            mean_w = 0.25 * n_effective * (n_effective + 1)
            var_w = (
                n_effective * (n_effective + 1) * (2 * n_effective + 1)
                - 0.5 * tie_correction
            ) / 24.0
        else:
            mean_w = 0.25 * (n_total * (n_total + 1) - n_zeros * (n_zeros + 1))
            var_w = (
                n_total * (n_total + 1) * (2 * n_total + 1)
                - n_zeros * (n_zeros + 1) * (2 * n_zeros + 1)
                - 0.5 * tie_correction
            ) / 24.0

        if var_w <= 0.0:
            p_val = 1.0
        else:
            sd_w = math.sqrt(var_w)
            z_num = max(0.0, abs(w_plus - mean_w) - 0.5)
            z_val = z_num / sd_w
            p_val = float(norm_two_sided_pvalue(z_val))

    return WilcoxonResult(
        statistic=float(w_stat),
        w_plus=w_plus,
        w_minus=w_minus,
        n_total=n_total,
        n_effective=n_effective,
        zero_method=zero_method,
        p_value=p_val,
        is_exact=use_exact,
        warnings=tuple(warnings_list),
    )


def _classify_cohens_d(abs_d: float) -> EffectSizeMagnitude:
    """Classify standardized effect size magnitude according to Cohen (1988)."""
    if abs_d < 0.2:
        return EffectSizeMagnitude.NEGLIGIBLE
    if abs_d < 0.5:
        return EffectSizeMagnitude.SMALL
    if abs_d < 0.8:
        return EffectSizeMagnitude.MEDIUM
    return EffectSizeMagnitude.LARGE


def compute_paired_cohens_d(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    alpha: float = 0.05,
) -> EffectSizeResult:
    """Compute paired Cohen's d_z = mean(d)/sd(d) with approximate analytical CI (STAT-07)."""
    if not math.isfinite(alpha) or not (0.0 < alpha < 1.0):
        raise ConfigurationError(f"Significance level alpha must be in (0.0, 1.0); got {alpha}")

    arr_a, arr_b = _validate_paired_arrays(scores_a, scores_b)
    j = int(arr_a.shape[0])
    diffs = arr_a - arr_b

    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1))

    warnings_list: list[str] = [
        "Analytical confidence interval for Cohen's d_z treats paired fold differences as the "
        "unit of analysis and is not adjusted for cross-validation training overlap."
    ]

    if std_diff == 0.0:
        if mean_diff == 0.0:
            d_z = 0.0
            ci: tuple[float | None, float | None] = (0.0, 0.0)
        else:
            d_z = math.copysign(float("inf"), mean_diff)
            ci = (None, None)
            warnings_list.append("zero_difference_variance: standard deviation of differences is zero.")
    else:
        d_z = float(mean_diff / std_diff)
        se_d = math.sqrt((1.0 / j) + (d_z * d_z) / (2.0 * j))
        t_crit = float(student_t_ppf(1.0 - alpha / 2.0, df=j - 1))
        margin = t_crit * se_d
        ci = (float(d_z - margin), float(d_z + margin))

    magnitude = _classify_cohens_d(abs(d_z))
    return EffectSizeResult(
        cohens_d=d_z,
        magnitude=magnitude,
        confidence_interval=ci,
        alpha=float(alpha),
        warnings=tuple(warnings_list),
    )
