"""Structured conclusion synthesis (Submodule 5C, RF5.6, STAT-11, CA-E5-02)."""

from __future__ import annotations

import math

from experimental_ml.core.enums import MetricStatus
from experimental_ml.metrics.types import MetricDirection
from experimental_ml.statistics.types import (
    CoverageStatus,
    DescriptiveConsolidation,
    MethodSuitabilityReport,
    MultiObjectiveSummary,
    StatisticalComparisonBundle,
    StructuredConclusion,
)


def _select_observed_leader(
    consolidation: DescriptiveConsolidation,
    primary_metric: str,
    direction: MetricDirection,
) -> tuple[tuple[str, str] | None, float | None]:
    """Identify the observed leader among configurations with VALID metric mean."""
    candidates: list[tuple[float, tuple[str, str]]] = []
    for cfg_id in sorted(consolidation.configurations.keys()):
        summary = consolidation.configurations[cfg_id]
        agg = summary.aggregated_metrics.get(primary_metric)
        if (
            agg is not None
            and agg.status != MetricStatus.UNDEFINED_NAN
            and agg.mean is not None
            and math.isfinite(agg.mean)
        ):
            candidates.append((agg.mean, cfg_id))

    if not candidates:
        return None, None

    if direction == MetricDirection.MINIMIZE:
        best_val, best_cfg = min(candidates, key=lambda x: (x[0], x[1]))
    else:
        best_val, best_cfg = max(candidates, key=lambda x: (x[0], x[1]))
    return best_cfg, best_val


def synthesize_conclusions(
    consolidation: DescriptiveConsolidation,
    suitability_report: MethodSuitabilityReport,
    comparison_bundle: StatisticalComparisonBundle,
    primary_metric: str,
    primary_direction: MetricDirection = MetricDirection.MINIMIZE,
    multi_objective_summary: MultiObjectiveSummary | None = None,
) -> StructuredConclusion:
    """Synthesize auditable StructuredConclusion strictly from 5A and 5B numerical outputs (STAT-11)."""
    if not isinstance(primary_direction, MetricDirection):
        primary_direction = MetricDirection(primary_direction)

    leader_cfg, leader_mean = _select_observed_leader(
        consolidation, primary_metric, primary_direction
    )

    primary_cmps = [
        c for c in comparison_bundle.comparisons if c.metric_name == primary_metric
    ]
    alpha = comparison_bundle.comparison_spec.alpha

    if not primary_cmps:
        evidence_status = (
            "No inferential comparisons executed for primary metric "
            f"'{primary_metric}' (alpha={alpha:.3f})."
        )
        effect_summary = "Effect sizes not available (no executed comparisons)."
        pract_summary = "NOT_CONFIGURED_OR_NOT_APPLICABLE"
    else:
        sig_cmps = [c for c in primary_cmps if c.nadeau_bengio_adjusted_p < alpha]
        nonsig_cmps = [c for c in primary_cmps if c.nadeau_bengio_adjusted_p >= alpha]
        evidence_status = (
            f"{len(sig_cmps)} of {len(primary_cmps)} comparison(s) reached adjusted significance "
            f"(p_adj < {alpha:.3f}); {len(nonsig_cmps)} comparison(s) had insufficient statistical "
            f"evidence to reject H0 (non-significance does not imply equivalence)."
        )
        effect_parts = [
            f"{c.config_a[0]}/{c.config_a[1]} vs {c.config_b[0]}/{c.config_b[1]}: "
            f"{c.effect_size.magnitude.value} (d_z={c.effect_size.cohens_d:.4f})"
            for c in primary_cmps
        ]
        effect_summary = "; ".join(effect_parts)
        pract_statuses = sorted({c.practical_relevance.value for c in primary_cmps})
        pract_summary = ", ".join(pract_statuses)

    if multi_objective_summary is None:
        cost_summary = "Multi-objective Pareto analysis not provided."
    else:
        frontier_names = [
            f"{p.config_id[0]}/{p.config_id[1]}"
            for p in multi_objective_summary.pareto_frontier
        ]
        cost_summary = (
            f"Pareto frontier contains {len(frontier_names)} configuration(s): "
            f"{', '.join(frontier_names) if frontier_names else 'none'} "
            f"({len(multi_objective_summary.dominated_configurations)} dominated, "
            f"{len(multi_objective_summary.excluded_configurations)} excluded)."
        )

    caveats: list[str] = []
    caveats.extend(suitability_report.warnings)
    caveats.extend(comparison_bundle.non_applicable_reasons)
    caveats.extend(comparison_bundle.warnings)
    for cfg_id, summary in sorted(consolidation.configurations.items()):
        if summary.coverage_status != CoverageStatus.VALID:
            caveats.append(
                f"Configuration {cfg_id[0]}/{cfg_id[1]} has {summary.coverage_status.value} "
                f"({summary.completed_folds}/{summary.total_folds} folds completed)."
            )
    for sk in comparison_bundle.skipped_comparisons:
        caveats.append(
            f"Skipped {sk.config_a[0]}/{sk.config_a[1]} vs {sk.config_b[0]}/{sk.config_b[1]} "
            f"({sk.metric_name}): {sk.reason}"
        )

    # Deduplicate preserving order
    seen: set[str] = set()
    unique_caveats = tuple(c for c in caveats if not (c in seen or seen.add(c)))

    narrative_parts: list[str] = []
    if leader_cfg is not None and leader_mean is not None:
        narrative_parts.append(
            f"On primary metric '{primary_metric}' ({primary_direction.value}), observed leader is "
            f"{leader_cfg[0]}/{leader_cfg[1]} with mean={leader_mean:.4f}."
        )
    else:
        narrative_parts.append(
            f"No valid observed leader could be determined on primary metric '{primary_metric}'."
        )

    narrative_parts.append(evidence_status)

    for c in primary_cmps:
        narrative_parts.append(
            f"Comparison {c.config_a[0]}/{c.config_a[1]} vs {c.config_b[0]}/{c.config_b[1]}: "
            f"diff={c.observed_difference:.4f}, t={c.nadeau_bengio.t_statistic:.4f}, "
            f"p_adj={c.nadeau_bengio_adjusted_p:.4f} (Nadeau-Bengio), "
            f"W={c.wilcoxon.statistic:.1f}, wx_p_adj={c.wilcoxon_adjusted_p:.4f}, "
            f"d_z={c.effect_size.cohens_d:.4f} [{c.effect_size.magnitude.value}], "
            f"practical={c.practical_relevance.value}."
        )

    narrative_parts.append(cost_summary)
    if unique_caveats:
        narrative_parts.append(f"Caveats: {' | '.join(unique_caveats)}")

    return StructuredConclusion(
        primary_metric=primary_metric,
        observed_leader=leader_cfg,
        statistical_evidence_status=evidence_status,
        effect_magnitude_summary=effect_summary,
        practical_relevance_status=pract_summary,
        cost_tradeoff_summary=cost_summary,
        methodological_caveats=unique_caveats,
        narrative_text=" ".join(narrative_parts),
    )
