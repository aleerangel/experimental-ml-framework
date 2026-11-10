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
    compute_pearson,
    compute_spearman,
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
    )


__all__ = ["explore_features"]
