"""Exploratory feature analysis engine.

Complies with EXP-01, EXP-06, EXP-08, RF2.1, CA-E2-01, ADR-005, and ADR-008.
Analyzes univariate predictor-target associations and predictor-predictor redundancy
without data leakage, binding the mandatory EXPLORATORY_FULL_DATA scope and warnings.
"""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from experimental_ml.core.enums import MetricStatus, TaskType
from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
)
from experimental_ml.data.preparation import SanitizedDatasetView
from experimental_ml.features.stats import (
    compute_correlation_ratio,
    compute_cramers_v,
    compute_distance_correlation,
    compute_linearity_score,
    compute_pearson,
    compute_spearman,
    compute_vif,
)
from experimental_ml.features.types import (
    METHODOLOGICAL_WARNINGS,
    SCOPE_EXPLORATORY_FULL_DATA,
    AssociationMeasure,
    ExploratoryFeatureReport,
    RedundancyPair,
)


def _is_numeric(arr: np.ndarray) -> bool:
    """Check if array has continuous/numeric data type (excluding booleans)."""
    return bool(
        (np.issubdtype(arr.dtype, np.floating) or np.issubdtype(arr.dtype, np.integer))
        and not np.issubdtype(arr.dtype, np.bool_)
    )


def explore_features(
    view: SanitizedDatasetView,
    *,
    redundancy_threshold: float = 0.85,
    extended_stats: bool = False,
) -> ExploratoryFeatureReport:
    """Perform exploratory analysis of predictor-target associations and predictor redundancy.

    Binds scope='EXPLORATORY_FULL_DATA' and mandatory methodological warnings (CA-E2-01).

    Args:
        view: Validated and sanitized immutable dataset view from Stage 1 (M2.2).
        redundancy_threshold: Absolute correlation/association threshold for reporting
            high redundancy pairs (must be between 0.0 and 1.0, default: 0.85).

    Returns:
        ExploratoryFeatureReport containing target associations, pairwise predictor
        redundancy matrix, high redundancy pairs, and mandatory warnings.

    Raises:
        ContractViolationError: If view is not a valid SanitizedDatasetView or lacks features.
        ConfigurationError: If redundancy_threshold is outside [0.0, 1.0] or non-finite.
    """
    if not isinstance(view, SanitizedDatasetView):
        raise ContractViolationError(
            f"explore_features requires a SanitizedDatasetView, got {type(view).__name__}"
        )

    if not isinstance(redundancy_threshold, (int, float)) or isinstance(redundancy_threshold, bool):
        raise ConfigurationError(
            f"redundancy_threshold must be a numeric float, got {redundancy_threshold!r}"
        )

    thresh = float(redundancy_threshold)
    if math.isnan(thresh) or math.isinf(thresh) or thresh < 0.0 or thresh > 1.0:
        raise ConfigurationError(
            f"redundancy_threshold must be in the closed interval [0.0, 1.0], got {thresh}"
        )

    if not view.candidate_feature_cols:
        raise ContractViolationError(
            "SanitizedDatasetView contains no candidate feature columns to analyze."
        )

    schema = view.schema
    target_col = schema.target_col
    if isinstance(target_col, (list, tuple)):
        # Multi-target regression: pick first target for univariate report or evaluate single
        target_name = target_col[0]
    else:
        target_name = target_col

    if target_name not in view.columns:
        raise ContractViolationError(
            f"Target column '{target_name}' not found in SanitizedDatasetView columns."
        )

    target_arr = view.columns[target_name]
    target_is_numeric = _is_numeric(target_arr)
    task_type = schema.task_type

    candidate_features = tuple(sorted(view.candidate_feature_cols))
    target_associations: list[AssociationMeasure] = []

    # 1. Target Associations Analysis
    for feat_name in candidate_features:
        if feat_name not in view.columns:
            raise DataIntegrityError(f"Candidate feature '{feat_name}' missing from view columns.")
        feat_arr = view.columns[feat_name]
        feat_is_numeric = _is_numeric(feat_arr)

        if task_type == TaskType.REGRESSION:
            if feat_is_numeric:
                # Continuous-continuous: compute Pearson and Spearman
                r_val, r_stat = compute_pearson(feat_arr, target_arr)
                target_associations.append(
                    AssociationMeasure(
                        feature_name=feat_name,
                        target_name=target_name,
                        metric_name="PEARSON",
                        value=r_val,
                        status=r_stat,
                    )
                )
                rho_val, rho_stat = compute_spearman(feat_arr, target_arr)
                target_associations.append(
                    AssociationMeasure(
                        feature_name=feat_name,
                        target_name=target_name,
                        metric_name="SPEARMAN",
                        value=rho_val,
                        status=rho_stat,
                    )
                )
            else:
                # Categorical-continuous: Correlation Ratio (eta)
                eta_val, eta_stat = compute_correlation_ratio(categories=feat_arr, continuous=target_arr)
                target_associations.append(
                    AssociationMeasure(
                        feature_name=feat_name,
                        target_name=target_name,
                        metric_name="CORRELATION_RATIO",
                        value=eta_val,
                        status=eta_stat,
                    )
                )
        else:
            # Classification tasks (BINARY_CLASSIFICATION, MULTICLASS_CLASSIFICATION)
            if feat_is_numeric:
                # Continuous feature with discrete target: Correlation Ratio (eta)
                eta_val, eta_stat = compute_correlation_ratio(categories=target_arr, continuous=feat_arr)
                target_associations.append(
                    AssociationMeasure(
                        feature_name=feat_name,
                        target_name=target_name,
                        metric_name="CORRELATION_RATIO",
                        value=eta_val,
                        status=eta_stat,
                    )
                )
            else:
                # Categorical-categorical: Cramér's V
                v_val, v_stat = compute_cramers_v(cat_x=feat_arr, cat_y=target_arr)
                target_associations.append(
                    AssociationMeasure(
                        feature_name=feat_name,
                        target_name=target_name,
                        metric_name="CRAMERS_V",
                        value=v_val,
                        status=v_stat,
                    )
                )

    # 2. Predictor-Predictor Pairwise Redundancy Analysis
    matrix: dict[str, dict[str, float | None]] = {f: {} for f in candidate_features}
    high_redundancy_pairs: list[RedundancyPair] = []

    n_feats = len(candidate_features)
    for i in range(n_feats):
        feat_a = candidate_features[i]
        arr_a = view.columns[feat_a]
        is_num_a = _is_numeric(arr_a)

        # Self-association on the diagonal
        matrix[feat_a][feat_a] = 1.0

        for j in range(i + 1, n_feats):
            feat_b = candidate_features[j]
            arr_b = view.columns[feat_b]
            is_num_b = _is_numeric(arr_b)

            if is_num_a and is_num_b:
                val, stat = compute_pearson(arr_a, arr_b)
                metric_name = "PEARSON"
            elif not is_num_a and not is_num_b:
                val, stat = compute_cramers_v(arr_a, arr_b)
                metric_name = "CRAMERS_V"
            else:
                # Mixed: continuous and categorical
                if is_num_a:
                    val, stat = compute_correlation_ratio(categories=arr_b, continuous=arr_a)
                else:
                    val, stat = compute_correlation_ratio(categories=arr_a, continuous=arr_b)
                metric_name = "CORRELATION_RATIO"

            matrix[feat_a][feat_b] = val
            matrix[feat_b][feat_a] = val

            if stat == MetricStatus.VALID and abs(val) >= thresh:
                high_redundancy_pairs.append(
                    RedundancyPair(
                        feature_a=feat_a,
                        feature_b=feat_b,
                        metric_name=metric_name,
                        value=val,
                        status=stat,
                    )
                )

    # Canonical sorting of high redundancy pairs: descending absolute value, then lexicographical
    high_redundancy_pairs.sort(
        key=lambda p: (-abs(p.value), p.feature_a, p.feature_b)
    )

    extended_diagnostics: MappingProxyType[str, Any] | None = None
    if extended_stats:
        extended_diagnostics = MappingProxyType(
            _compute_extended_feature_diagnostics(
                view=view,
                candidate_features=list(candidate_features),
                target_arr=view.columns[target_name],
                task_type=task_type,
            )
        )

    return ExploratoryFeatureReport(
        scope=SCOPE_EXPLORATORY_FULL_DATA,
        dataset_hash=view.dataset_hash,
        task_type=task_type,
        target_associations=tuple(target_associations),
        pairwise_redundancy_matrix=matrix,
        high_redundancy_pairs=tuple(high_redundancy_pairs),
        warnings=METHODOLOGICAL_WARNINGS,
        metadata=MappingProxyType({
            "redundancy_threshold": thresh,
            "n_candidate_features": n_feats,
            "target_col": target_name,
        }),
        extended_diagnostics=extended_diagnostics,
    )


def _compute_extended_feature_diagnostics(
    *,
    view: SanitizedDatasetView,
    candidate_features: list[str],
    target_arr: np.ndarray,
    task_type: TaskType,
) -> dict[str, Any]:
    """Compute opt-in exploratory VIF, Distance Correlation, and linearity diagnostics."""
    num_feats = [f for f in candidate_features if _is_numeric(view.columns[f])]
    vif_by_feature: dict[str, float | None] = {}
    dcor_by_feature: dict[str, float | None] = {}
    linearity_score: float | None = None

    if num_feats:
        cols_imputed: list[np.ndarray] = []
        for f in num_feats:
            arr = np.asarray(view.columns[f], dtype=np.float64).copy()
            finite = np.isfinite(arr)
            if np.any(finite):
                arr[~finite] = float(np.mean(arr[finite]))
            else:
                arr[:] = 0.0
            cols_imputed.append(arr)

        x_mat = np.column_stack(cols_imputed)
        vifs, vif_status = compute_vif(x_mat)
        if vif_status == MetricStatus.VALID and len(vifs) == len(num_feats):
            for fname, v in zip(num_feats, vifs):
                vif_by_feature[fname] = float(v) if math.isfinite(float(v)) else None

        if _is_numeric(target_arr):
            y_num = np.asarray(target_arr, dtype=np.float64)
            for fname, x_col in zip(num_feats, cols_imputed):
                dval, dstat = compute_distance_correlation(x_col, y_num)
                dcor_by_feature[fname] = float(dval) if dstat == MetricStatus.VALID else None

        lin_val, lin_stat = compute_linearity_score(x_mat, target_arr, task_type)
        if lin_stat == MetricStatus.VALID:
            linearity_score = float(lin_val)

    valid_vifs = [v for v in vif_by_feature.values() if v is not None]
    valid_dcors = [v for v in dcor_by_feature.values() if v is not None]

    return {
        "scope": SCOPE_EXPLORATORY_FULL_DATA,
        "vif_by_feature": vif_by_feature,
        "max_vif": float(max(valid_vifs)) if valid_vifs else None,
        "mean_vif": float(np.mean(valid_vifs)) if valid_vifs else None,
        "distance_correlation_to_target": dcor_by_feature,
        "mean_distance_correlation_target": float(np.mean(valid_dcors)) if valid_dcors else None,
        "linearity_score": linearity_score,
    }


def build_dataset_meta_features(
    profile: Any,
    report: ExploratoryFeatureReport,
) -> dict[str, Any]:
    """Build standardized exploratory dataset_meta_features dictionary (Rivolli et al., 2022)."""
    skews: list[float] = []
    kurts: list[float] = []
    outliers: list[float] = []
    for col_prof in profile.columns.values():
        if col_prof.role in ("target", "observation_id", "group", "time"):
            continue
        ns = col_prof.numeric_stats
        if ns is None:
            continue
        if ns.skewness is not None and math.isfinite(ns.skewness):
            skews.append(abs(float(ns.skewness)))
        if ns.kurtosis is not None and math.isfinite(ns.kurtosis):
            kurts.append(float(ns.kurtosis))
        if ns.outlier_rate_iqr is not None and math.isfinite(ns.outlier_rate_iqr):
            outliers.append(float(ns.outlier_rate_iqr))

    ext = dict(report.extended_diagnostics) if report.extended_diagnostics is not None else {}
    return {
        "schema_version": "1.0",
        "scope": SCOPE_EXPLORATORY_FULL_DATA,
        "dataset_hash": profile.source_dataset_hash,
        "task_type": profile.target.task_type.value,
        "n_rows": int(profile.n_rows),
        "n_cols": int(profile.n_cols),
        "n_candidate_features": int(report.metadata.get("n_candidate_features", 0)),
        "samples_to_features_ratio": profile.samples_to_features_ratio,
        "intrinsic_dim_ratio_95": profile.intrinsic_dim_ratio_95,
        "target_entropy_norm": profile.target_entropy_norm,
        "mean_abs_skewness": float(np.mean(skews)) if skews else None,
        "mean_excess_kurtosis": float(np.mean(kurts)) if kurts else None,
        "mean_outlier_rate_iqr": float(np.mean(outliers)) if outliers else None,
        "max_vif": ext.get("max_vif"),
        "mean_vif": ext.get("mean_vif"),
        "mean_distance_correlation_target": ext.get("mean_distance_correlation_target"),
        "linearity_score": ext.get("linearity_score"),
    }


__all__ = ["explore_features", "build_dataset_meta_features"]
