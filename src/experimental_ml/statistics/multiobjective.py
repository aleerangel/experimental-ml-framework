"""Multi-objective Pareto frontier computation (Submodule 5B, STAT-09, CA-E5-02)."""

from __future__ import annotations

import math

from experimental_ml.core.enums import MetricStatus
from experimental_ml.metrics.types import MetricDirection
from experimental_ml.statistics.types import (
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    ExcludedParetoConfiguration,
    MultiObjectiveSpec,
    MultiObjectiveSummary,
    ObjectiveSource,
    ObjectiveSpec,
    ParetoConfigurationPoint,
)


def _extract_objective_value(
    summary: ConfigurationSummary,
    obj: ObjectiveSpec,
) -> tuple[float | None, str | None]:
    """Extract a finite scalar objective value or return an exclusion reason."""
    field = obj.field_name or obj.name
    if obj.source == ObjectiveSource.AGGREGATED_METRIC:
        agg = summary.aggregated_metrics.get(field)
        if agg is None:
            return None, f"Missing aggregated metric '{field}'."
        if agg.status == MetricStatus.UNDEFINED_NAN or agg.mean is None:
            return None, f"Metric '{field}' is UNDEFINED_NAN."
        if not math.isfinite(agg.mean):
            return None, f"Metric '{field}' mean is non-finite."
        return float(agg.mean), None

    if obj.source == ObjectiveSource.TIMING_MEAN:
        if summary.aggregated_timing is None:
            return None, "Missing aggregated timing statistics."
        val = getattr(summary.aggregated_timing, field, None)
        if val is None or not math.isfinite(float(val)):
            return None, f"Missing or non-finite timing field '{field}'."
        return float(val), None

    if obj.source == ObjectiveSource.FEATURE_STABILITY:
        if summary.feature_stability is None or summary.feature_stability.mean_jaccard is None:
            return None, "Missing feature selection stability (mean_jaccard)."
        val = float(summary.feature_stability.mean_jaccard)
        if not math.isfinite(val):
            return None, "Non-finite feature stability mean_jaccard."
        return val, None

    return None, f"Unsupported ObjectiveSource: {obj.source}"


def _dominates(
    vals_a: dict[str, float],
    vals_b: dict[str, float],
    objectives: tuple[ObjectiveSpec, ...],
) -> bool:
    """Return True iff A Pareto-dominates B under all ObjectiveSpec directions."""
    from experimental_ml.metrics.catalog import METRICS_CATALOG

    strictly_better = False
    for obj in objectives:
        m_spec = METRICS_CATALOG.get(obj.name.lower())
        by_abs = bool(m_spec.compare_by_abs) if m_spec is not None else False
        a = abs(vals_a[obj.name]) if by_abs else vals_a[obj.name]
        b = abs(vals_b[obj.name]) if by_abs else vals_b[obj.name]
        if obj.direction == MetricDirection.MINIMIZE:
            if a > b:
                return False
            if a < b:
                strictly_better = True
        else:
            if a < b:
                return False
            if a > b:
                strictly_better = True
    return strictly_better


def compute_pareto_frontier(
    consolidation: DescriptiveConsolidation,
    spec: MultiObjectiveSpec,
) -> MultiObjectiveSummary:
    """Compute exact Pareto frontier over VALID configurations (STAT-09, CA-E5-02)."""
    eligible_points: list[tuple[tuple[str, str], dict[str, float]]] = []
    excluded: list[ExcludedParetoConfiguration] = []

    for cfg_id in sorted(consolidation.configurations.keys()):
        summary = consolidation.configurations[cfg_id]
        if summary.coverage_status != CoverageStatus.VALID:
            excluded.append(
                ExcludedParetoConfiguration(
                    config_id=cfg_id,
                    reason=f"Coverage status is {summary.coverage_status.value} (requires VALID).",
                )
            )
            continue

        obj_vals: dict[str, float] = {}
        excl_reason: str | None = None
        for obj in spec.objectives:
            val, reason = _extract_objective_value(summary, obj)
            if val is None:
                excl_reason = reason
                break
            obj_vals[obj.name] = val

        if excl_reason is not None:
            excluded.append(ExcludedParetoConfiguration(config_id=cfg_id, reason=excl_reason))
        else:
            eligible_points.append((cfg_id, obj_vals))

    frontier: list[ParetoConfigurationPoint] = []
    dominated: list[ParetoConfigurationPoint] = []

    for cfg_id, vals in eligible_points:
        dominators = tuple(
            other_id
            for other_id, other_vals in eligible_points
            if other_id != cfg_id and _dominates(other_vals, vals, spec.objectives)
        )
        is_opt = len(dominators) == 0
        pt = ParetoConfigurationPoint(
            config_id=cfg_id,
            objective_values=vals,
            is_pareto_optimal=is_opt,
            dominated_by=dominators,
        )
        if is_opt:
            frontier.append(pt)
        else:
            dominated.append(pt)

    return MultiObjectiveSummary(
        objectives=spec.objectives,
        pareto_frontier=tuple(frontier),
        dominated_configurations=tuple(dominated),
        excluded_configurations=tuple(excluded),
    )
