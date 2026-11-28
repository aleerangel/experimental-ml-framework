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


def compute_partition_ks_drift(
    sanitized_view: Any,
    partition_plan: Any,
    *,
    alpha: float = 0.05,
    d_threshold: float = 0.15,
) -> PartitionDriftReport:
    """Detect covariate and target shift across partitions using 2-sample KS (Quiñonero-Candela et al., 2009)."""
    from experimental_ml.validation.types import EvaluationRegime, PartitionStrategy

    regime_val = getattr(partition_plan, "regime", EvaluationRegime.CV_ONLY)
    strategy_val = getattr(partition_plan, "strategy", getattr(partition_plan, "splitting_strategy", None))
    folds = tuple(getattr(partition_plan, "folds", ()))

    if regime_val == EvaluationRegime.CV_AND_HOLDOUT and getattr(partition_plan, "holdout_ids", ()):
        ref_ids = set(partition_plan.development_ids)
        cmp_ids = set(partition_plan.holdout_ids)
        ref_lbl, cmp_lbl = "DEV", "FINAL_HOLDOUT"
    elif strategy_val == PartitionStrategy.TEMPORAL and len(folds) >= 2:
        ref_ids = set(folds[0].train_ids)
        cmp_ids = set(folds[-1].val_ids)
        ref_lbl, cmp_lbl = "TEMPORAL_INICIAL", "TEMPORAL_FINAL"
    elif folds:
        ref_ids = set(folds[0].train_ids)
        cmp_ids = set(folds[0].val_ids)
        ref_lbl, cmp_lbl = "FOLD_0_TRAIN", "FOLD_0_VAL"
    else:
        return PartitionDriftReport(
            regime=str(getattr(regime_val, "value", regime_val)),
            reference_label="NONE",
            comparison_label="NONE",
            alpha=alpha,
            d_threshold=d_threshold,
            features=(),
            n_drifted_features=0,
        )

    obs_ids = tuple(sanitized_view.observation_ids)
    ref_idx = np.array([i for i, oid in enumerate(obs_ids) if oid in ref_ids], dtype=np.intp)
    cmp_idx = np.array([i for i, oid in enumerate(obs_ids) if oid in cmp_ids], dtype=np.intp)
    target_col = sanitized_view.schema.target_col

    records: list[FeatureDriftRecord] = []
    for col_name in sorted(sanitized_view.columns.keys()):
        col_arr = np.asarray(sanitized_view.columns[col_name])
        if not np.issubdtype(col_arr.dtype, np.number) or np.issubdtype(col_arr.dtype, np.bool_):
            continue
        res = ks_2samp(col_arr[ref_idx], col_arr[cmp_idx])
        drifted = bool(res.status == "VALID" and res.p_value < alpha and res.statistic >= d_threshold)
        records.append(
            FeatureDriftRecord(
                feature_name=col_name,
                is_target=(col_name == target_col),
                ks_statistic=res.statistic,
                p_value=res.p_value,
                n_ref=res.n_a,
                n_cmp=res.n_b or 0,
                drift_detected=drifted,
                status=res.status,
            )
        )

    return PartitionDriftReport(
        regime=str(getattr(regime_val, "value", regime_val)),
        reference_label=ref_lbl,
        comparison_label=cmp_lbl,
        alpha=alpha,
        d_threshold=d_threshold,
        features=tuple(records),
        n_drifted_features=sum(1 for r in records if r.drift_detected),
    )


def analyze_oof_residuals_map(
    oof_by_config: Mapping[tuple[str, str], Any],
) -> tuple[OofResidualsDiagnosticEntry, ...]:
    """Analyze regression OOF residuals per configuration via Lilliefors and Normal vs. Student-t AIC."""
    entries: list[OofResidualsDiagnosticEntry] = []
    for (m_id, sc_id), oof_rec in sorted(oof_by_config.items()):
        y_true = np.asarray(oof_rec.y_true, dtype=np.float64)
        y_pred = np.asarray(oof_rec.y_pred_mean, dtype=np.float64) if hasattr(oof_rec, "y_pred_mean") else np.asarray(oof_rec.y_pred, dtype=np.float64)
        residuals = y_true - y_pred
        if len(_finite_float_array(residuals)) < 5:
            continue
        fit = compare_normal_vs_student_t(residuals)
        entries.append(OofResidualsDiagnosticEntry(model_id=m_id, scenario_id=sc_id, fit=fit))
    return tuple(entries)


def partition_drift_to_dict(report: PartitionDriftReport) -> dict[str, Any]:
    return {
        "regime": report.regime,
        "reference_label": report.reference_label,
        "comparison_label": report.comparison_label,
        "alpha": report.alpha,
        "d_threshold": report.d_threshold,
        "n_drifted_features": report.n_drifted_features,
        "features": [
            {
                "feature_name": f.feature_name,
                "is_target": f.is_target,
                "ks_statistic": None if math.isnan(f.ks_statistic) else f.ks_statistic,
                "p_value": None if math.isnan(f.p_value) else f.p_value,
                "n_ref": f.n_ref,
                "n_cmp": f.n_cmp,
                "drift_detected": f.drift_detected,
                "status": f.status,
            }
            for f in report.features
        ],
    }


def oof_residuals_to_dict(
    entries: Sequence[OofResidualsDiagnosticEntry],
    oof_samples: Mapping[tuple[str, str], tuple[Sequence[float], Sequence[float]]] | None = None,
) -> dict[str, Any]:
    configs: list[dict[str, Any]] = []
    for e in entries:
        item: dict[str, Any] = {
            "model_id": e.model_id,
            "scenario_id": e.scenario_id,
            "n_samples": e.fit.n_samples,
            "mean": e.fit.mean,
            "std": e.fit.std,
            "lilliefors_d": e.fit.lilliefors_d,
            "lilliefors_p": e.fit.lilliefors_p,
            "normal_loglik": e.fit.normal_loglik,
            "normal_aic": e.fit.normal_aic,
            "student_t_nu": e.fit.student_t_nu,
            "student_t_loglik": e.fit.student_t_loglik,
            "student_t_aic": e.fit.student_t_aic,
            "preferred_family": e.fit.preferred_family,
            "heavy_tails_detected": e.fit.heavy_tails_detected,
        }
        if oof_samples and (e.model_id, e.scenario_id) in oof_samples:
            yp, res = oof_samples[(e.model_id, e.scenario_id)]
            item["y_pred"] = [float(v) for v in yp]
            item["residuals"] = [float(v) for v in res]
        configs.append(item)
    return {"configurations": configs}

