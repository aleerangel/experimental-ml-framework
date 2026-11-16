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
    student_t_ppf,
    student_t_two_sided_pvalue,
)
from experimental_ml.statistics.types import NadeauBengioResult


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
