"""Statistical comparison orchestrator (Submodule 5B, STAT-08, CA-E5-01, CA-E5-02).

Coordinates candidate pair generation across ComparisonScope modes, verifies
per-fold and per-metric eligibility, executes Nadeau-Bengio, Wilcoxon, and Cohen's d,
evaluates practical relevance, and applies family-wise multiplicity adjustments.
"""

from __future__ import annotations

from collections import defaultdict
import math
from typing import Sequence

import numpy as np

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.metrics.types import MetricDirection
from experimental_ml.statistics.inference import (
    compute_paired_cohens_d,
    paired_nadeau_bengio_test,
    paired_wilcoxon_test,
)
from experimental_ml.statistics.multiplicity import (
    adjust_pvalues_bh,
    adjust_pvalues_holm,
)
from experimental_ml.statistics.suitability import check_pairwise_comparison_eligibility
from experimental_ml.statistics.types import (
    ComparisonScope,
    ComparisonSpec,
    CoverageStatus,
    DescriptiveConsolidation,
    IncompleteComparisonPolicy,
    MethodSuitabilityReport,
    MultiplicityMethod,
    PairwiseComparisonResult,
    PracticalRelevanceStatus,
    SkippedComparison,
    StatisticalComparisonBundle,
)
from experimental_ml.validation.types import EvaluationRegime, PartitionPlan


def _generate_candidate_pairs(
    consolidation: DescriptiveConsolidation,
    spec: ComparisonSpec,
) -> list[tuple[tuple[str, str], tuple[str, str]]]:
    """Generate deterministic candidate configuration pairs for the requested scope."""
    configs = sorted(consolidation.configurations.keys())
    scope = spec.comparison_scope

    if scope in (ComparisonScope.ALL_PAIRWISE, ComparisonScope.FULL_CONFIGURATIONS):
        return [
            (configs[i], configs[j])
            for i in range(len(configs))
            for j in range(i + 1, len(configs))
        ]

    if scope == ComparisonScope.MODELS_WITHIN_SCENARIO:
        by_scenario: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for cfg in configs:
            by_scenario[cfg[1]].append(cfg)
        pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
        for scen in sorted(by_scenario):
            group = sorted(by_scenario[scen])
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    pairs.append((group[i], group[j]))
        return pairs

    if scope == ComparisonScope.SCENARIOS_WITHIN_MODEL:
        by_model: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for cfg in configs:
            by_model[cfg[0]].append(cfg)
        pairs = []
        for mod in sorted(by_model):
            group = sorted(by_model[mod])
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    pairs.append((group[i], group[j]))
        return pairs

    if scope == ComparisonScope.AGAINST_BASELINE:
        base = spec.baseline_config
        assert base is not None
        if base not in consolidation.configurations:
            raise ConfigurationError(
                f"Baseline configuration {base} not found in DescriptiveConsolidation."
            )
        return [(cfg, base) for cfg in configs if cfg != base]

    if scope == ComparisonScope.PLANNED_HYPOTHESES:
        for a, b in spec.planned_pairs:
            if a not in consolidation.configurations or b not in consolidation.configurations:
                raise ConfigurationError(
                    f"Planned comparison pair ({a}, {b}) references unknown configuration."
                )
        return list(spec.planned_pairs)

    raise ConfigurationError(f"Unsupported ComparisonScope: {scope}")


def _build_fold_geometry_lookup(
    partition_plan: PartitionPlan,
) -> dict[str, tuple[float, int]]:
    """Map fold identifiers from PartitionPlan to (n_val/n_train, n_val)."""
    lookup: dict[str, tuple[float, int]] = {}
    for fold in partition_plan.folds:
        n_train = len(fold.train_ids)
        n_val = len(fold.val_ids)
        ratio = float(n_val / n_train) if n_train > 0 else 0.0
        fid = getattr(fold, "fold_id", None) or f"fold_{fold.fold_index}"
        lookup[fid] = (ratio, n_val)
        lookup[str(fold.fold_index)] = (ratio, n_val)
    return lookup


def _evaluate_practical_relevance(
    abs_diff: float,
    adjusted_p: float,
    alpha: float,
    delta_min: float | None,
) -> PracticalRelevanceStatus:
    """Classify practical relevance without equating p >= alpha with equivalence (CA-E5-02)."""
    if delta_min is None:
        return PracticalRelevanceStatus.NOT_CONFIGURED
    is_sig = adjusted_p < alpha
    is_practical = abs_diff >= delta_min
    if is_sig and is_practical:
        return PracticalRelevanceStatus.STATISTICALLY_SIGNIFICANT_AND_PRACTICAL
    if is_sig and not is_practical:
        return PracticalRelevanceStatus.STATISTICALLY_SIGNIFICANT_NOT_PRACTICAL
    if not is_sig and is_practical:
        return PracticalRelevanceStatus.PRACTICAL_NOT_STATISTICALLY_SIGNIFICANT
    return PracticalRelevanceStatus.INCONCLUSIVE


def _adjust_family_pvalues(
    p_values: Sequence[float],
    method: MultiplicityMethod,
) -> list[float]:
    if method == MultiplicityMethod.HOLM_BONFERRONI:
        return adjust_pvalues_holm(p_values)
    if method == MultiplicityMethod.BENJAMINI_HOCHBERG:
        return adjust_pvalues_bh(p_values)
    return [float(p) for p in p_values]


def run_statistical_comparisons(
    consolidation: DescriptiveConsolidation,
    partition_plan: PartitionPlan,
    comparison_spec: ComparisonSpec,
    suitability_report: MethodSuitabilityReport,
    policy: IncompleteComparisonPolicy = IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY,
) -> StatisticalComparisonBundle:
    """Execute paired statistical comparisons across configurations and metrics (STAT-08).

    Strictly blocks multi-fold inference under HOLDOUT_ONLY (J=1), isolates FINAL_HOLDOUT
    under CV_AND_HOLDOUT, verifies per-metric MetricStatus.VALID availability, and applies
    family-wise multiplicity adjustment independently to Nadeau-Bengio and Wilcoxon p-values.
    """
    if (
        partition_plan.regime == EvaluationRegime.HOLDOUT_ONLY
        or not suitability_report.is_cross_validation
        or suitability_report.total_development_partitions < 2
    ):
        reason = (
            "Multi-fold paired statistical inference is not applicable under HOLDOUT_ONLY "
            f"(J = {suitability_report.total_development_partitions} < 2); no observation-level "
            "pseudoreplication is permitted."
        )
        return StatisticalComparisonBundle(
            experiment_id=consolidation.experiment_id,
            partition_plan_id=consolidation.partition_plan_id,
            comparison_spec=comparison_spec,
            comparisons=(),
            skipped_comparisons=(),
            non_applicable_reasons=(reason,),
            warnings=(reason,),
        )

    if consolidation.total_configurations < 2:
        reason = (
            f"At least 2 configurations are required for comparison; found {consolidation.total_configurations}."
        )
        return StatisticalComparisonBundle(
            experiment_id=consolidation.experiment_id,
            partition_plan_id=consolidation.partition_plan_id,
            comparison_spec=comparison_spec,
            comparisons=(),
            skipped_comparisons=(),
            non_applicable_reasons=(reason,),
            warnings=(reason,),
        )

    fold_geom = _build_fold_geometry_lookup(partition_plan)
    candidate_pairs = _generate_candidate_pairs(consolidation, comparison_spec)

    if not candidate_pairs:
        reason = f"No candidate pairs generated for scope {comparison_spec.comparison_scope.value}."
        return StatisticalComparisonBundle(
            experiment_id=consolidation.experiment_id,
            partition_plan_id=consolidation.partition_plan_id,
            comparison_spec=comparison_spec,
            comparisons=(),
            skipped_comparisons=(),
            non_applicable_reasons=(reason,),
            warnings=(),
        )

    raw_results: list[PairwiseComparisonResult] = []
    skipped: list[SkippedComparison] = []
    bundle_warnings: list[str] = []

    if partition_plan.regime == EvaluationRegime.CV_AND_HOLDOUT:
        bundle_warnings.append(
            "CV_AND_HOLDOUT regime: statistical comparisons are computed strictly over development "
            "CV folds; FINAL_HOLDOUT metrics are isolated and excluded."
        )

    cmp_counter = 0
    for metric_name in comparison_spec.metrics_of_interest:
        direction = comparison_spec.metric_directions[metric_name]

        for cfg_a, cfg_b in candidate_pairs:
            sum_a = consolidation.configurations[cfg_a]
            sum_b = consolidation.configurations[cfg_b]

            eligible, elig_msg, shared_folds = check_pairwise_comparison_eligibility(
                sum_a, sum_b, policy
            )
            if not eligible:
                skipped.append(
                    SkippedComparison(
                        config_a=cfg_a,
                        config_b=cfg_b,
                        metric_name=metric_name,
                        reason=elig_msg,
                    )
                )
                continue

            # Filter per-metric MetricStatus.VALID across shared folds (ADR-005)
            valid_folds: list[str] = []
            invalid_folds: list[str] = []
            for fid in shared_folds:
                mv_a = sum_a.fold_metrics.get(fid, {}).get(metric_name)
                mv_b = sum_b.fold_metrics.get(fid, {}).get(metric_name)
                if (
                    mv_a is not None
                    and mv_b is not None
                    and mv_a.status == MetricStatus.VALID
                    and mv_b.status == MetricStatus.VALID
                    and math.isfinite(mv_a.value)
                    and math.isfinite(mv_b.value)
                ):
                    valid_folds.append(fid)
                else:
                    invalid_folds.append(fid)

            if invalid_folds and policy == IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY:
                skipped.append(
                    SkippedComparison(
                        config_a=cfg_a,
                        config_b=cfg_b,
                        metric_name=metric_name,
                        reason=(
                            f"Metric '{metric_name}' has UNDEFINED_NAN or missing value on shared "
                            f"folds {invalid_folds} under STRICT_COMPLETE_ONLY."
                        ),
                    )
                )
                continue

            if len(valid_folds) < 2:
                skipped.append(
                    SkippedComparison(
                        config_a=cfg_a,
                        config_b=cfg_b,
                        metric_name=metric_name,
                        reason=(
                            f"Insufficient valid paired folds for metric '{metric_name}' "
                            f"(J_valid = {len(valid_folds)} < 2)."
                        ),
                    )
                )
                continue

            is_conditional = (
                sum_a.coverage_status != CoverageStatus.VALID
                or sum_b.coverage_status != CoverageStatus.VALID
                or bool(invalid_folds)
            )
            pair_warnings: list[str] = []
            if is_conditional:
                pair_warnings.append(
                    f"Conditional comparison restricted to {len(valid_folds)} valid shared folds "
                    "(attrition bias risk)."
                )

            scores_a = [float(sum_a.fold_metrics[fid][metric_name].value) for fid in valid_folds]
            scores_b = [float(sum_b.fold_metrics[fid][metric_name].value) for fid in valid_folds]
            ratios = [fold_geom[fid][0] for fid in valid_folds if fid in fold_geom]
            val_sizes = [fold_geom[fid][1] for fid in valid_folds if fid in fold_geom]
            if len(ratios) != len(valid_folds):
                ratios_arg: float | Sequence[float] = suitability_report.mean_train_overlap_ratio
                sizes_arg: Sequence[int] | None = None
            else:
                ratios_arg = ratios
                sizes_arg = val_sizes

            nb_res = paired_nadeau_bengio_test(
                scores_a,
                scores_b,
                train_val_ratios=ratios_arg,
                fold_val_sizes=sizes_arg,
                alpha=comparison_spec.alpha,
            )
            wx_res = paired_wilcoxon_test(
                scores_a,
                scores_b,
                alpha=comparison_spec.alpha,
            )
            es_res = compute_paired_cohens_d(
                scores_a,
                scores_b,
                alpha=comparison_spec.alpha,
            )

            from experimental_ml.metrics.catalog import METRICS_CATALOG

            mean_a = float(np.mean(scores_a))
            mean_b = float(np.mean(scores_b))
            obs_diff = nb_res.mean_difference
            m_spec = METRICS_CATALOG.get(metric_name.lower())
            by_abs = bool(m_spec.compare_by_abs) if m_spec is not None else False
            cmp_a = abs(mean_a) if by_abs else mean_a
            cmp_b = abs(mean_b) if by_abs else mean_b
            if cmp_a == cmp_b:
                better: tuple[str, str] | None = None
            elif direction == MetricDirection.MINIMIZE:
                better = cfg_a if cmp_a < cmp_b else cfg_b
            else:
                better = cfg_a if cmp_a > cmp_b else cfg_b

            family_id = metric_name
            if comparison_spec.hypothesis_family_spec is not None:
                family_id = comparison_spec.hypothesis_family_spec.get(
                    (cfg_a, cfg_b, metric_name),
                    comparison_spec.hypothesis_family_spec.get(
                        (cfg_b, cfg_a, metric_name), metric_name
                    ),
                )

            cmp_counter += 1
            raw_results.append(
                PairwiseComparisonResult(
                    comparison_id=f"cmp_{cmp_counter:04d}",
                    family_id=family_id,
                    metric_name=metric_name,
                    direction=direction,
                    config_a=cfg_a,
                    config_b=cfg_b,
                    shared_fold_ids=tuple(valid_folds),
                    observed_mean_a=mean_a,
                    observed_mean_b=mean_b,
                    observed_difference=obs_diff,
                    observed_better=better,
                    nadeau_bengio=nb_res,
                    wilcoxon=wx_res,
                    effect_size=es_res,
                    nadeau_bengio_adjusted_p=nb_res.p_value,
                    wilcoxon_adjusted_p=wx_res.p_value,
                    practical_relevance=PracticalRelevanceStatus.NOT_CONFIGURED,
                    is_conditional=is_conditional,
                    warnings=tuple(pair_warnings),
                )
            )

    # Multiplicity adjustment per hypothesis family independently for NB and Wilcoxon
    family_indices: dict[str, list[int]] = defaultdict(list)
    for idx, res in enumerate(raw_results):
        family_indices[res.family_id].append(idx)

    final_results = list(raw_results)
    thresholds = comparison_spec.practical_relevance_thresholds or {}

    for fam_id, indices in family_indices.items():
        nb_raw = [raw_results[i].nadeau_bengio.p_value for i in indices]
        wx_raw = [raw_results[i].wilcoxon.p_value for i in indices]
        nb_adj = _adjust_family_pvalues(nb_raw, comparison_spec.multiplicity_method)
        wx_adj = _adjust_family_pvalues(wx_raw, comparison_spec.multiplicity_method)

        for pos, orig_idx in enumerate(indices):
            r = raw_results[orig_idx]
            delta_min = thresholds.get(r.metric_name)
            pract = _evaluate_practical_relevance(
                abs(r.observed_difference),
                nb_adj[pos],
                comparison_spec.alpha,
                delta_min,
            )
            final_results[orig_idx] = PairwiseComparisonResult(
                comparison_id=r.comparison_id,
                family_id=r.family_id,
                metric_name=r.metric_name,
                direction=r.direction,
                config_a=r.config_a,
                config_b=r.config_b,
                shared_fold_ids=r.shared_fold_ids,
                observed_mean_a=r.observed_mean_a,
                observed_mean_b=r.observed_mean_b,
                observed_difference=r.observed_difference,
                observed_better=r.observed_better,
                nadeau_bengio=r.nadeau_bengio,
                wilcoxon=r.wilcoxon,
                effect_size=r.effect_size,
                nadeau_bengio_adjusted_p=nb_adj[pos],
                wilcoxon_adjusted_p=wx_adj[pos],
                practical_relevance=pract,
                is_conditional=r.is_conditional,
                warnings=r.warnings,
            )

    return StatisticalComparisonBundle(
        experiment_id=consolidation.experiment_id,
        partition_plan_id=consolidation.partition_plan_id,
        comparison_spec=comparison_spec,
        comparisons=tuple(final_results),
        skipped_comparisons=tuple(skipped),
        non_applicable_reasons=(),
        warnings=tuple(bundle_warnings),
    )
