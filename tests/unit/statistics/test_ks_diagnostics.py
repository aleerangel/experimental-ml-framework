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


def test_m11_2_partition_ks_drift_cv_holdout_and_temporal() -> None:
    """C2 (M11.2): compute_partition_ks_drift detects covariate shift in CV_AND_HOLDOUT and TEMPORAL."""
    from types import SimpleNamespace
    from experimental_ml.statistics.distributions_diagnostics import (
        analyze_oof_residuals_map,
        compute_partition_ks_drift,
        oof_residuals_to_dict,
        partition_drift_to_dict,
    )
    from experimental_ml.validation.types import EvaluationRegime, PartitionStrategy

    rng = np.random.default_rng(123)
    n = 120
    obs_ids = tuple(f"obs_{i:04d}" for i in range(n))
    # First 80 (DEV) from N(0,1), last 40 (HOLDOUT) shifted to N(3,1) on x1
    x1 = np.concatenate([rng.normal(0.0, 1.0, 80), rng.normal(3.0, 1.0, 40)])
    x2 = rng.normal(0.0, 1.0, n)
    y = 2.0 * x1 + rng.normal(0.0, 0.2, n)
    view = SimpleNamespace(
        observation_ids=obs_ids,
        columns={"x1": x1, "x2": x2, "y": y},
        schema=SimpleNamespace(target_col="y"),
    )

    plan_holdout = SimpleNamespace(
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        strategy=PartitionStrategy.KFOLD,
        development_ids=obs_ids[:80],
        holdout_ids=obs_ids[80:],
        folds=(),
    )
    rep_holdout = compute_partition_ks_drift(view, plan_holdout)
    assert rep_holdout.reference_label == "DEV"
    assert rep_holdout.comparison_label == "FINAL_HOLDOUT"
    f_x1 = next(f for f in rep_holdout.features if f.feature_name == "x1")
    f_x2 = next(f for f in rep_holdout.features if f.feature_name == "x2")
    assert f_x1.drift_detected is True
    assert f_x2.drift_detected is False
    assert partition_drift_to_dict(rep_holdout)["n_drifted_features"] >= 1

    # Temporal split
    plan_temp = SimpleNamespace(
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.TEMPORAL,
        holdout_ids=(),
        folds=(
            SimpleNamespace(train_ids=obs_ids[:60], val_ids=obs_ids[60:80]),
            SimpleNamespace(train_ids=obs_ids[:80], val_ids=obs_ids[80:120]),
        ),
    )
    rep_temp = compute_partition_ks_drift(view, plan_temp)
    assert rep_temp.reference_label == "TEMPORAL_INICIAL"
    assert rep_temp.comparison_label == "TEMPORAL_FINAL"
    assert next(f for f in rep_temp.features if f.feature_name == "x1").drift_detected is True

    # OOF residuals diagnostics
    oof_rec = SimpleNamespace(y_true=y[:80], y_pred_mean=2.0 * x1[:80])
    diag_entries = analyze_oof_residuals_map({("m1", "s1"): oof_rec})
    assert len(diag_entries) == 1
    assert diag_entries[0].fit.lilliefors_p > 0.05
    assert oof_residuals_to_dict(diag_entries)["configurations"][0]["preferred_family"] == "NORMAL"
