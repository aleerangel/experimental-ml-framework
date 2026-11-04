"""Aggregation, comparison, and ranking for experimental_ml.metrics (ADR-005 compliant)."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

from experimental_ml.core.enums import AggregationScope, MetricDirection, MetricStatus
from experimental_ml.core.findings import ConfigurationError, DataIntegrityError, make_warning
from experimental_ml.metrics.catalog import get_metric_spec
from experimental_ml.metrics.types import (
    AggregatedMetricValue,
    MetricEvaluationScope,
    MetricSpec,
    MetricValue,
    RankedCandidate,
)

_ALLOWED_AGG_SCOPES = {
    AggregationScope.FOLD_AGGREGATION,
    AggregationScope.REPETITION_AGGREGATION,
    AggregationScope.OVERALL_AGGREGATION,
}


def is_better(
    cand_a: MetricValue | AggregatedMetricValue,
    cand_b: MetricValue | AggregatedMetricValue,
    direction: MetricDirection | None = None,
    *,
    metric_spec: MetricSpec | None = None,
) -> bool:
    """Determine if candidate A strictly outperforms candidate B per ADR-005 rules.

    Evaluation precedence:
    1. Rankable (VALID or PARTIAL_COVERAGE with finite value) strictly beats non-rankable (UNDEFINED_NAN).
    2. Two non-rankable candidates return False.
    3. VALID strictly beats PARTIAL_COVERAGE.
    4. Higher coverage beats lower coverage between two PARTIAL_COVERAGE candidates.
    5. For identical status and coverage, compares directed values according to metric_spec.direction
       and metric_spec.compare_by_abs (|v| comparison for MBE).

    Args:
        cand_a: First candidate metric.
        cand_b: Second candidate metric.
        direction: Optional direction override (defaults to metric_spec.direction).
        metric_spec: Optional MetricSpec (resolved via catalog if None).

    Returns:
        True if cand_a is strictly better than cand_b, False otherwise.
    """
    if metric_spec is None:
        metric_spec = get_metric_spec(cand_a.metric_id)

    eff_direction = direction if direction is not None else metric_spec.direction
    use_abs = metric_spec.compare_by_abs

    # Extract values and coverages
    def _extract_cand_info(cand: MetricValue | AggregatedMetricValue) -> tuple[float, float, bool]:
        if isinstance(cand, MetricValue):
            val = cand.value
            is_valid = cand.status == MetricStatus.VALID and math.isfinite(val)
            cov = 1.0 if is_valid else 0.0
            return val, cov, is_valid
        elif isinstance(cand, AggregatedMetricValue):
            val = cand.mean
            is_rankable = cand.status in (
                MetricStatus.VALID,
                MetricStatus.PARTIAL_COVERAGE,
            ) and math.isfinite(val)
            cov = cand.coverage if is_rankable else 0.0
            return val, cov, is_rankable
        else:
            raise ConfigurationError(f"Unsupported candidate type {type(cand)}")

    val_a, cov_a, rankable_a = _extract_cand_info(cand_a)
    val_b, cov_b, rankable_b = _extract_cand_info(cand_b)

    # 1. Non-rankable checks
    if not rankable_a and not rankable_b:
        return False
    if rankable_a and not rankable_b:
        return True
    if not rankable_a and rankable_b:
        return False

    # 2. VALID strictly beats PARTIAL_COVERAGE
    if cand_a.status == MetricStatus.VALID and cand_b.status == MetricStatus.PARTIAL_COVERAGE:
        return True
    if cand_a.status == MetricStatus.PARTIAL_COVERAGE and cand_b.status == MetricStatus.VALID:
        return False

    # 3. Higher coverage beats lower coverage
    if cov_a > cov_b:
        return True
    if cov_a < cov_b:
        return False

    # 4. Value comparison
    comp_a = abs(val_a) if use_abs else val_a
    comp_b = abs(val_b) if use_abs else val_b

    if eff_direction == MetricDirection.MINIMIZE:
        return bool(comp_a < comp_b)
    else:
        return bool(comp_a > comp_b)


def aggregate_fold_metrics(
    fold_values: Sequence[MetricValue],
    *,
    scope: AggregationScope | str = AggregationScope.FOLD_AGGREGATION,
) -> AggregatedMetricValue:
    """Aggregate individual fold metric evaluations into summary statistics.

    Computes sample mean, std (ddof=1 for k >= 2), median, and IQR.
    Assigns:
    - VALID when k == K (100% valid folds).
    - PARTIAL_COVERAGE with warning when 0 < k < K.
    - UNDEFINED_NAN with warning when k == 0.

    Args:
        fold_values: Non-empty sequence of MetricValue from cross-validation folds.
        scope: Aggregation scope enum or string.

    Returns:
        AggregatedMetricValue summary.

    Raises:
        DataIntegrityError: If fold_values is empty or metric_id is inconsistent.
        ConfigurationError: If scope is invalid or not an aggregation scope.
    """
    if not fold_values:
        raise DataIntegrityError("fold_values cannot be empty")

    # Scope validation
    if isinstance(scope, str):
        try:
            scope_enum = AggregationScope(scope)
        except ValueError as exc:
            raise ConfigurationError(
                f"Invalid aggregation scope '{scope}'. Allowed scopes: {[s.value for s in _ALLOWED_AGG_SCOPES]}"
            ) from exc
    elif isinstance(scope, AggregationScope):
        scope_enum = scope
    else:
        raise ConfigurationError(f"Invalid scope type {type(scope)}")

    if scope_enum not in _ALLOWED_AGG_SCOPES:
        raise ConfigurationError(
            f"Scope {scope_enum} is not an allowed aggregation scope. Allowed: {[s.value for s in _ALLOWED_AGG_SCOPES]}"
        )

    # Metric consistency check
    base_id = fold_values[0].metric_id
    base_dir = fold_values[0].direction
    for fv in fold_values:
        if fv.metric_id != base_id:
            raise DataIntegrityError(
                f"Metric id mismatch across folds: expected '{base_id}', got '{fv.metric_id}'"
            )

    k_total = len(fold_values)
    valid_fvs = [
        fv for fv in fold_values if fv.status == MetricStatus.VALID and math.isfinite(fv.value)
    ]
    k_valid = len(valid_fvs)
    coverage = float(k_valid / k_total)

    warnings: list[Any] = []
    # Collect warnings from folds
    for fv in fold_values:
        for w in fv.warnings:
            if w not in warnings:
                warnings.append(w)

    if k_valid == k_total:
        status = MetricStatus.VALID
    elif k_valid > 0:
        status = MetricStatus.PARTIAL_COVERAGE
        warnings.append(
            make_warning(
                "W_METRIC_PARTIAL_COVERAGE",
                f"Partial fold coverage: {k_valid}/{k_total} folds valid ({coverage * 100.0:.1f}%)",
                {"valid_folds": k_valid, "total_folds": k_total, "coverage": coverage},
            )
        )
    else:
        status = MetricStatus.UNDEFINED_NAN
        warnings.append(
            make_warning(
                "W_METRIC_ZERO_COVERAGE",
                f"Zero valid folds: 0/{k_total} folds valid",
                {"valid_folds": 0, "total_folds": k_total, "coverage": 0.0},
            )
        )

    if k_valid == 0:
        mean_val = float("nan")
        std_val = float("nan")
        median_val = float("nan")
        iqr_val = float("nan")
    else:
        vals = np.array([fv.value for fv in valid_fvs], dtype=np.float64)
        mean_val = float(np.mean(vals))
        std_val = float(np.std(vals, ddof=1)) if k_valid >= 2 else 0.0
        median_val = float(np.median(vals))
        q75, q25 = np.percentile(vals, [75, 25])
        iqr_val = float(q75 - q25)

    return AggregatedMetricValue(
        metric_id=base_id,
        mean=mean_val,
        std=std_val,
        median=median_val,
        iqr=iqr_val,
        status=status,
        direction=base_dir,
        scope=scope_enum,
        valid_folds=k_valid,
        total_folds=k_total,
        coverage=coverage,
        fold_values=tuple(fold_values),
        warnings=tuple(warnings),
    )


def rank_configurations(
    candidates: Mapping[str, MetricValue | AggregatedMetricValue]
    | Sequence[tuple[str, MetricValue | AggregatedMetricValue]],
    *,
    direction: MetricDirection | None = None,
    metric_spec: MetricSpec | None = None,
) -> tuple[RankedCandidate, ...]:
    """Rank candidate model configurations using lexicographic sorting (ADR-005).

    Sort order for rankable candidates:
    (0 if status == VALID else 1, -coverage, directed_value, candidate_id)
    where directed_value is:
    - abs(val) if compare_by_abs is True (for MBE)
    - val if direction == MINIMIZE
    - -val if direction == MAXIMIZE

    Candidates with status UNDEFINED_NAN, UNRANKABLE, or non-finite values are
    placed at the end with status=UNRANKABLE and rank=None, sorted by candidate_id.

    Args:
        candidates: Mapping or sequence of (candidate_id, metric) pairs.
        direction: Optional direction override.
        metric_spec: Optional MetricSpec for resolving compare_by_abs and direction.

    Returns:
        Tuple of RankedCandidate objects.
    """
    if isinstance(candidates, Mapping):
        items = list(candidates.items())
    else:
        items = list(candidates)

    if not items:
        return ()

    if metric_spec is None:
        first_metric = items[0][1]
        metric_spec = get_metric_spec(first_metric.metric_id)

    eff_direction = direction if direction is not None else metric_spec.direction
    use_abs = metric_spec.compare_by_abs

    rankable: list[tuple[tuple[int, float, float, str], str, MetricValue | AggregatedMetricValue]] = []
    unrankable: list[tuple[str, MetricValue | AggregatedMetricValue]] = []

    for cid, cand in items:
        # Check rankability
        if isinstance(cand, MetricValue):
            val = cand.value
            is_valid = cand.status == MetricStatus.VALID and math.isfinite(val)
            cov = 1.0 if is_valid else 0.0
            status = cand.status
        elif isinstance(cand, AggregatedMetricValue):
            val = cand.mean
            is_valid = cand.status in (
                MetricStatus.VALID,
                MetricStatus.PARTIAL_COVERAGE,
            ) and math.isfinite(val)
            cov = cand.coverage if is_valid else 0.0
            status = cand.status
        else:
            raise ConfigurationError(f"Unsupported candidate type {type(cand)}")

        if not is_valid:
            unrankable.append((cid, cand))
        else:
            # Directed value
            comp_val = abs(val) if use_abs else val
            directed_val = comp_val if eff_direction == MetricDirection.MINIMIZE else -comp_val
            status_order = 0 if status == MetricStatus.VALID else 1
            sort_key = (status_order, -cov, directed_val, str(cid))
            rankable.append((sort_key, str(cid), cand))

    # Sort rankable
    rankable.sort(key=lambda x: x[0])

    ranked_results: list[RankedCandidate] = []
    for rank_idx, (_, cid, cand) in enumerate(rankable, start=1):
        cand_status = cand.status
        ranked_results.append(
            RankedCandidate(
                candidate_id=cid,
                metric=cand,
                rank=rank_idx,
                status=cand_status,
            )
        )

    # Sort unrankable deterministically by candidate_id
    unrankable.sort(key=lambda x: str(x[0]))
    for cid, cand in unrankable:
        ranked_results.append(
            RankedCandidate(
                candidate_id=str(cid),
                metric=cand,
                rank=None,
                status=MetricStatus.UNRANKABLE,
            )
        )

    return tuple(ranked_results)


__all__ = [
    "is_better",
    "aggregate_fold_metrics",
    "rank_configurations",
]
