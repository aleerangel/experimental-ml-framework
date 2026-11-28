"""Atomic persistence and typed JSON codecs for Stage 5 statistics artifacts (STAT-12, STORE-03, STORE-05)."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

from experimental_ml.core.enums import FindingSeverity, MetricStatus
from experimental_ml.core.findings import (
    ContractViolationError,
    DataIntegrityError,
    Finding,
)
from experimental_ml.core.storage import read_json, write_json_atomic
from experimental_ml.features.stability import SelectionStabilityReport
from experimental_ml.metrics.types import (
    AggregationScope,
    MetricDirection,
    MetricEvaluationScope,
    MetricValue,
)
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    AggregatedTimingStats,
    ApplicabilityStatus,
    ApplicableMethod,
    ComparisonScope,
    ComparisonSpec,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    EffectSizeMagnitude,
    EffectSizeResult,
    ExcludedParetoConfiguration,
    MethodSuitabilityReport,
    MultiObjectiveSummary,
    MultiplicityMethod,
    NadeauBengioResult,
    ObjectiveSource,
    ObjectiveSpec,
    PairwiseComparisonResult,
    ParetoConfigurationPoint,
    PracticalRelevanceStatus,
    SkippedComparison,
    StatisticalComparisonBundle,
    StructuredConclusion,
    WilcoxonResult,
)
from experimental_ml.validation.types import EvaluationRegime


REQUIRED_STATISTICS_FILES = (
    "descriptive_consolidation.json",
    "method_suitability.json",
    "statistical_comparisons.json",
    "structured_conclusion.json",
    "statistics_manifest.json",
)


@dataclass(frozen=True, slots=True)
class LoadedStatisticsArtifacts:
    """Loaded Stage 5 statistical artifacts bundle."""

    consolidation: DescriptiveConsolidation
    suitability: MethodSuitabilityReport
    comparisons: StatisticalComparisonBundle
    conclusion: StructuredConclusion
    pareto: MultiObjectiveSummary | None
    manifest: dict[str, Any]


def _encode_float(val: float | None) -> Any:
    if val is None:
        return None
    f = float(val)
    if math.isnan(f):
        return {"__nonfinite__": "NaN"}
    if math.isinf(f):
        return {"__nonfinite__": "Inf" if f > 0 else "-Inf"}
    return f


def _decode_float(raw: Any) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, dict) and "__nonfinite__" in raw:
        tag = raw["__nonfinite__"]
        if tag == "NaN":
            return float("nan")
        if tag == "Inf":
            return float("inf")
        if tag == "-Inf":
            return float("-inf")
        raise DataIntegrityError(f"Unknown non-finite marker: {tag!r}")
    return float(raw)


def _metric_value_to_dict(mv: MetricValue) -> dict[str, Any]:
    return {
        "metric_id": mv.metric_id,
        "value": _encode_float(mv.value),
        "status": mv.status.value,
        "direction": mv.direction.value,
        "scope": mv.scope.value,
        "n_samples": mv.n_samples,
        "warnings": [
            {
                "code": w.code,
                "severity": w.severity.value,
                "message": w.message,
                "context": dict(w.context) if w.context is not None else None,
            }
            for w in mv.warnings
        ],
    }


def _metric_value_from_dict(d: dict[str, Any]) -> MetricValue:
    scope_raw = d["scope"]
    try:
        scope: MetricEvaluationScope | AggregationScope = MetricEvaluationScope(scope_raw)
    except ValueError:
        scope = AggregationScope(scope_raw)
    warnings = tuple(
        Finding(
            code=w["code"],
            severity=FindingSeverity(w["severity"]),
            message=w["message"],
            context=w.get("context"),
        )
        for w in d.get("warnings", ())
    )
    return MetricValue(
        metric_id=d["metric_id"],
        value=_decode_float(d["value"]),  # type: ignore[arg-type]
        status=MetricStatus(d["status"]),
        direction=MetricDirection(d["direction"]),
        scope=scope,
        n_samples=int(d["n_samples"]),
        warnings=warnings,
    )


def _agg_metric_to_dict(am: AggregatedMetricStats) -> dict[str, Any]:
    return {
        "n_valid": am.n_valid,
        "n_total": am.n_total,
        "status": am.status.value,
        "mean": _encode_float(am.mean),
        "std": _encode_float(am.std),
        "median": _encode_float(am.median),
        "iqr": _encode_float(am.iqr),
        "q25": _encode_float(am.q25),
        "q75": _encode_float(am.q75),
        "min_value": _encode_float(am.min_value),
        "max_value": _encode_float(am.max_value),
    }


def _agg_metric_from_dict(d: dict[str, Any]) -> AggregatedMetricStats:
    return AggregatedMetricStats(
        n_valid=int(d["n_valid"]),
        n_total=int(d["n_total"]),
        status=MetricStatus(d["status"]),
        mean=_decode_float(d["mean"]),
        std=_decode_float(d["std"]),
        median=_decode_float(d["median"]),
        iqr=_decode_float(d["iqr"]),
        q25=_decode_float(d["q25"]),
        q75=_decode_float(d["q75"]),
        min_value=_decode_float(d["min_value"]),
        max_value=_decode_float(d["max_value"]),
    )


def _timing_to_dict(t: AggregatedTimingStats | None) -> dict[str, Any] | None:
    if t is None:
        return None
    return {
        "data_extraction_mean_s": t.data_extraction_mean_s,
        "data_extraction_total_s": t.data_extraction_total_s,
        "preprocessing_mean_s": t.preprocessing_mean_s,
        "preprocessing_total_s": t.preprocessing_total_s,
        "feature_selection_mean_s": t.feature_selection_mean_s,
        "feature_selection_total_s": t.feature_selection_total_s,
        "tuning_mean_s": t.tuning_mean_s,
        "tuning_total_s": t.tuning_total_s,
        "fit_mean_s": t.fit_mean_s,
        "fit_total_s": t.fit_total_s,
        "predict_mean_s": t.predict_mean_s,
        "predict_total_s": t.predict_total_s,
        "evaluation_mean_s": t.evaluation_mean_s,
        "evaluation_total_s": t.evaluation_total_s,
        "total_cell_mean_s": t.total_cell_mean_s,
        "total_cell_sum_s": t.total_cell_sum_s,
    }


def _timing_from_dict(d: dict[str, Any] | None) -> AggregatedTimingStats | None:
    if d is None:
        return None
    return AggregatedTimingStats(**{k: float(v) for k, v in d.items()})


def _stability_to_dict(st: SelectionStabilityReport | None) -> dict[str, Any] | None:
    if st is None:
        return None
    return {
        "mean_jaccard": _encode_float(st.mean_jaccard),
        "std_jaccard": _encode_float(st.std_jaccard),
        "mean_kuncheva": _encode_float(st.mean_kuncheva),
        "std_kuncheva": _encode_float(st.std_kuncheva),
        "pairwise_jaccard": {k: {ik: _encode_float(iv) for ik, iv in v.items()} for k, v in st.pairwise_jaccard.items()},
        "pairwise_kuncheva": {k: {ik: _encode_float(iv) for ik, iv in v.items()} for k, v in st.pairwise_kuncheva.items()},
        "n_folds": st.n_folds,
        "n_total_candidates": st.n_total_candidates,
    }


def _stability_from_dict(d: dict[str, Any] | None) -> SelectionStabilityReport | None:
    if d is None:
        return None
    return SelectionStabilityReport(
        mean_jaccard=_decode_float(d["mean_jaccard"]),  # type: ignore[arg-type]
        std_jaccard=_decode_float(d["std_jaccard"]),  # type: ignore[arg-type]
        mean_kuncheva=_decode_float(d["mean_kuncheva"]),  # type: ignore[arg-type]
        std_kuncheva=_decode_float(d["std_kuncheva"]),  # type: ignore[arg-type]
        pairwise_jaccard={k: {ik: _decode_float(iv) for ik, iv in v.items()} for k, v in d["pairwise_jaccard"].items()},  # type: ignore[misc]
        pairwise_kuncheva={k: {ik: _decode_float(iv) for ik, iv in v.items()} for k, v in d["pairwise_kuncheva"].items()},  # type: ignore[misc]
        n_folds=int(d["n_folds"]),
        n_total_candidates=int(d["n_total_candidates"]),
    )


def _consolidation_to_dict(c: DescriptiveConsolidation) -> dict[str, Any]:
    configs_list = []
    for (mod, scen), s in sorted(c.configurations.items()):
        configs_list.append(
            {
                "model_id": mod,
                "scenario_id": scen,
                "total_folds": s.total_folds,
                "completed_folds": s.completed_folds,
                "failed_folds": s.failed_folds,
                "cancelled_folds": s.cancelled_folds,
                "coverage": s.coverage,
                "coverage_status": s.coverage_status.value,
                "completed_fold_ids": list(s.completed_fold_ids),
                "failed_fold_ids": list(s.failed_fold_ids),
                "cancelled_fold_ids": list(s.cancelled_fold_ids),
                "fold_metrics": {
                    fid: {m: _metric_value_to_dict(mv) for m, mv in m_map.items()}
                    for fid, m_map in s.fold_metrics.items()
                },
                "aggregated_metrics": {
                    m: _agg_metric_to_dict(am) for m, am in s.aggregated_metrics.items()
                },
                "aggregated_train_metrics": {
                    m: _agg_metric_to_dict(am) for m, am in s.aggregated_train_metrics.items()
                },
                "pooled_oof_metrics": {
                    m: _metric_value_to_dict(mv) for m, mv in s.pooled_oof_metrics.items()
                },
                "holdout_metrics": {
                    m: _metric_value_to_dict(mv) for m, mv in s.holdout_metrics.items()
                },
                "aggregated_timing": _timing_to_dict(s.aggregated_timing),
                "feature_stability": _stability_to_dict(s.feature_stability),
            }
        )
    return {
        "experiment_id": c.experiment_id,
        "partition_plan_id": c.partition_plan_id,
        "total_configurations": c.total_configurations,
        "configurations": configs_list,
        "timestamp_utc": c.timestamp_utc,
    }


def _consolidation_from_dict(d: dict[str, Any]) -> DescriptiveConsolidation:
    configs: dict[tuple[str, str], ConfigurationSummary] = {}
    for item in d["configurations"]:
        key = (item["model_id"], item["scenario_id"])
        configs[key] = ConfigurationSummary(
            model_id=item["model_id"],
            scenario_id=item["scenario_id"],
            total_folds=int(item["total_folds"]),
            completed_folds=int(item["completed_folds"]),
            failed_folds=int(item["failed_folds"]),
            cancelled_folds=int(item["cancelled_folds"]),
            coverage=float(item["coverage"]),
            coverage_status=CoverageStatus(item["coverage_status"]),
            completed_fold_ids=tuple(item["completed_fold_ids"]),
            failed_fold_ids=tuple(item["failed_fold_ids"]),
            cancelled_fold_ids=tuple(item["cancelled_fold_ids"]),
            fold_metrics={
                fid: {m: _metric_value_from_dict(mv) for m, mv in m_map.items()}
                for fid, m_map in item["fold_metrics"].items()
            },
            aggregated_metrics={
                m: _agg_metric_from_dict(am) for m, am in item["aggregated_metrics"].items()
            },
            aggregated_train_metrics={
                m: _agg_metric_from_dict(am) for m, am in item.get("aggregated_train_metrics", {}).items()
            },
            pooled_oof_metrics={
                m: _metric_value_from_dict(mv) for m, mv in item["pooled_oof_metrics"].items()
            },
            holdout_metrics={
                m: _metric_value_from_dict(mv) for m, mv in item.get("holdout_metrics", {}).items()
            },
            aggregated_timing=_timing_from_dict(item["aggregated_timing"]),
            feature_stability=_stability_from_dict(item["feature_stability"]),
        )
    return DescriptiveConsolidation(
        experiment_id=d["experiment_id"],
        partition_plan_id=d["partition_plan_id"],
        total_configurations=int(d["total_configurations"]),
        configurations=configs,
        timestamp_utc=d["timestamp_utc"],
    )


def _suitability_to_dict(s: MethodSuitabilityReport) -> dict[str, Any]:
    return {
        "evaluation_regime": s.evaluation_regime.value,
        "total_development_partitions": s.total_development_partitions,
        "fold_ratios": list(s.fold_ratios),
        "mean_train_overlap_ratio": s.mean_train_overlap_ratio,
        "is_cross_validation": s.is_cross_validation,
        "applicable_methods": {
            k: {
                "method_name": m.method_name,
                "status": m.status.value,
                "rationale": m.rationale,
                "assumptions_tested": list(m.assumptions_tested),
                "assumptions_untested": list(m.assumptions_untested),
                "warnings": list(m.warnings),
            }
            for k, m in s.applicable_methods.items()
        },
        "warnings": list(s.warnings),
    }


def _suitability_from_dict(d: dict[str, Any]) -> MethodSuitabilityReport:
    return MethodSuitabilityReport(
        evaluation_regime=EvaluationRegime(d["evaluation_regime"]),
        total_development_partitions=int(d["total_development_partitions"]),
        fold_ratios=tuple(float(r) for r in d["fold_ratios"]),
        mean_train_overlap_ratio=float(d["mean_train_overlap_ratio"]),
        is_cross_validation=bool(d["is_cross_validation"]),
        applicable_methods={
            k: ApplicableMethod(
                method_name=m["method_name"],
                status=ApplicabilityStatus(m["status"]),
                rationale=m["rationale"],
                assumptions_tested=tuple(m["assumptions_tested"]),
                assumptions_untested=tuple(m["assumptions_untested"]),
                warnings=tuple(m["warnings"]),
            )
            for k, m in d["applicable_methods"].items()
        },
        warnings=tuple(d["warnings"]),
    )


def _comparisons_to_dict(b: StatisticalComparisonBundle) -> dict[str, Any]:
    spec = b.comparison_spec
    fam_list = None
    if spec.hypothesis_family_spec is not None:
        fam_list = [
            {"config_a": list(k[0]), "config_b": list(k[1]), "metric": k[2], "family_id": v}
            for k, v in spec.hypothesis_family_spec.items()
        ]
    return {
        "experiment_id": b.experiment_id,
        "partition_plan_id": b.partition_plan_id,
        "comparison_spec": {
            "metrics_of_interest": list(spec.metrics_of_interest),
            "metric_directions": {k: v.value for k, v in spec.metric_directions.items()},
            "comparison_scope": spec.comparison_scope.value,
            "baseline_config": list(spec.baseline_config) if spec.baseline_config else None,
            "planned_pairs": [[list(a), list(b_)] for a, b_ in spec.planned_pairs],
            "alpha": spec.alpha,
            "multiplicity_method": spec.multiplicity_method.value,
            "hypothesis_family_spec": fam_list,
            "practical_relevance_thresholds": (
                dict(spec.practical_relevance_thresholds)
                if spec.practical_relevance_thresholds is not None
                else None
            ),
        },
        "comparisons": [
            {
                "comparison_id": c.comparison_id,
                "family_id": c.family_id,
                "metric_name": c.metric_name,
                "direction": c.direction.value,
                "config_a": list(c.config_a),
                "config_b": list(c.config_b),
                "shared_fold_ids": list(c.shared_fold_ids),
                "observed_mean_a": _encode_float(c.observed_mean_a),
                "observed_mean_b": _encode_float(c.observed_mean_b),
                "observed_difference": _encode_float(c.observed_difference),
                "observed_better": list(c.observed_better) if c.observed_better else None,
                "nadeau_bengio": {
                    "mean_difference": _encode_float(c.nadeau_bengio.mean_difference),
                    "std_difference": _encode_float(c.nadeau_bengio.std_difference),
                    "corrected_variance": _encode_float(c.nadeau_bengio.corrected_variance),
                    "corrected_se": _encode_float(c.nadeau_bengio.corrected_se),
                    "t_statistic": _encode_float(c.nadeau_bengio.t_statistic),
                    "degrees_of_freedom": c.nadeau_bengio.degrees_of_freedom,
                    "p_value": _encode_float(c.nadeau_bengio.p_value),
                    "confidence_interval": [
                        _encode_float(c.nadeau_bengio.confidence_interval[0]),
                        _encode_float(c.nadeau_bengio.confidence_interval[1]),
                    ],
                    "alpha": c.nadeau_bengio.alpha,
                    "mean_train_val_ratio": c.nadeau_bengio.mean_train_val_ratio,
                    "fold_size_cv": _encode_float(c.nadeau_bengio.fold_size_cv),
                    "warnings": list(c.nadeau_bengio.warnings),
                },
                "wilcoxon": {
                    "statistic": c.wilcoxon.statistic,
                    "w_plus": c.wilcoxon.w_plus,
                    "w_minus": c.wilcoxon.w_minus,
                    "n_total": c.wilcoxon.n_total,
                    "n_effective": c.wilcoxon.n_effective,
                    "zero_method": c.wilcoxon.zero_method,
                    "p_value": c.wilcoxon.p_value,
                    "is_exact": c.wilcoxon.is_exact,
                    "warnings": list(c.wilcoxon.warnings),
                },
                "effect_size": {
                    "cohens_d": _encode_float(c.effect_size.cohens_d),
                    "magnitude": c.effect_size.magnitude.value,
                    "confidence_interval": [
                        _encode_float(c.effect_size.confidence_interval[0]),
                        _encode_float(c.effect_size.confidence_interval[1]),
                    ],
                    "alpha": c.effect_size.alpha,
                    "warnings": list(c.effect_size.warnings),
                },
                "nadeau_bengio_adjusted_p": _encode_float(c.nadeau_bengio_adjusted_p),
                "wilcoxon_adjusted_p": _encode_float(c.wilcoxon_adjusted_p),
                "practical_relevance": c.practical_relevance.value,
                "is_conditional": c.is_conditional,
                "warnings": list(c.warnings),
            }
            for c in b.comparisons
        ],
        "skipped_comparisons": [
            {
                "config_a": list(s.config_a),
                "config_b": list(s.config_b),
                "metric_name": s.metric_name,
                "reason": s.reason,
            }
            for s in b.skipped_comparisons
        ],
        "non_applicable_reasons": list(b.non_applicable_reasons),
        "warnings": list(b.warnings),
    }


def _comparisons_from_dict(d: dict[str, Any]) -> StatisticalComparisonBundle:
    sp = d["comparison_spec"]
    fam_map = None
    if sp.get("hypothesis_family_spec") is not None:
        fam_map = {
            (
                (item["config_a"][0], item["config_a"][1]),
                (item["config_b"][0], item["config_b"][1]),
                item["metric"],
            ): item["family_id"]
            for item in sp["hypothesis_family_spec"]
        }
    spec = ComparisonSpec(
        metrics_of_interest=tuple(sp["metrics_of_interest"]),
        metric_directions={k: MetricDirection(v) for k, v in sp["metric_directions"].items()},
        comparison_scope=ComparisonScope(sp["comparison_scope"]),
        baseline_config=(sp["baseline_config"][0], sp["baseline_config"][1])
        if sp.get("baseline_config")
        else None,
        planned_pairs=tuple(
            ((a[0], a[1]), (b_[0], b_[1])) for a, b_ in sp.get("planned_pairs", ())
        ),
        alpha=float(sp["alpha"]),
        multiplicity_method=MultiplicityMethod(sp["multiplicity_method"]),
        hypothesis_family_spec=fam_map,
        practical_relevance_thresholds=sp.get("practical_relevance_thresholds"),
    )

    cmps: list[PairwiseComparisonResult] = []
    for c in d["comparisons"]:
        nb_d = c["nadeau_bengio"]
        wx_d = c["wilcoxon"]
        es_d = c["effect_size"]
        nb = NadeauBengioResult(
            mean_difference=_decode_float(nb_d["mean_difference"]),  # type: ignore[arg-type]
            std_difference=_decode_float(nb_d["std_difference"]),  # type: ignore[arg-type]
            corrected_variance=_decode_float(nb_d["corrected_variance"]),  # type: ignore[arg-type]
            corrected_se=_decode_float(nb_d["corrected_se"]),  # type: ignore[arg-type]
            t_statistic=_decode_float(nb_d["t_statistic"]),  # type: ignore[arg-type]
            degrees_of_freedom=int(nb_d["degrees_of_freedom"]),
            p_value=_decode_float(nb_d["p_value"]),  # type: ignore[arg-type]
            confidence_interval=(
                _decode_float(nb_d["confidence_interval"][0]),  # type: ignore[arg-type]
                _decode_float(nb_d["confidence_interval"][1]),  # type: ignore[arg-type]
            ),
            alpha=float(nb_d["alpha"]),
            mean_train_val_ratio=float(nb_d["mean_train_val_ratio"]),
            fold_size_cv=_decode_float(nb_d["fold_size_cv"]),
            warnings=tuple(nb_d["warnings"]),
        )
        wx = WilcoxonResult(
            statistic=float(wx_d["statistic"]),
            w_plus=float(wx_d["w_plus"]),
            w_minus=float(wx_d["w_minus"]),
            n_total=int(wx_d["n_total"]),
            n_effective=int(wx_d["n_effective"]),
            zero_method=str(wx_d["zero_method"]),
            p_value=float(wx_d["p_value"]),
            is_exact=bool(wx_d["is_exact"]),
            warnings=tuple(wx_d["warnings"]),
        )
        es = EffectSizeResult(
            cohens_d=_decode_float(es_d["cohens_d"]),  # type: ignore[arg-type]
            magnitude=EffectSizeMagnitude(es_d["magnitude"]),
            confidence_interval=(
                _decode_float(es_d["confidence_interval"][0]),
                _decode_float(es_d["confidence_interval"][1]),
            ),
            alpha=float(es_d["alpha"]),
            warnings=tuple(es_d["warnings"]),
        )
        cmps.append(
            PairwiseComparisonResult(
                comparison_id=c["comparison_id"],
                family_id=c["family_id"],
                metric_name=c["metric_name"],
                direction=MetricDirection(c["direction"]),
                config_a=(c["config_a"][0], c["config_a"][1]),
                config_b=(c["config_b"][0], c["config_b"][1]),
                shared_fold_ids=tuple(c["shared_fold_ids"]),
                observed_mean_a=_decode_float(c["observed_mean_a"]),  # type: ignore[arg-type]
                observed_mean_b=_decode_float(c["observed_mean_b"]),  # type: ignore[arg-type]
                observed_difference=_decode_float(c["observed_difference"]),  # type: ignore[arg-type]
                observed_better=(c["observed_better"][0], c["observed_better"][1])
                if c.get("observed_better")
                else None,
                nadeau_bengio=nb,
                wilcoxon=wx,
                effect_size=es,
                nadeau_bengio_adjusted_p=_decode_float(c["nadeau_bengio_adjusted_p"]),  # type: ignore[arg-type]
                wilcoxon_adjusted_p=_decode_float(c["wilcoxon_adjusted_p"]),  # type: ignore[arg-type]
                practical_relevance=PracticalRelevanceStatus(c["practical_relevance"]),
                is_conditional=bool(c["is_conditional"]),
                warnings=tuple(c["warnings"]),
            )
        )

    skips = tuple(
        SkippedComparison(
            config_a=(s["config_a"][0], s["config_a"][1]),
            config_b=(s["config_b"][0], s["config_b"][1]),
            metric_name=s["metric_name"],
            reason=s["reason"],
        )
        for s in d["skipped_comparisons"]
    )
    return StatisticalComparisonBundle(
        experiment_id=d["experiment_id"],
        partition_plan_id=d["partition_plan_id"],
        comparison_spec=spec,
        comparisons=tuple(cmps),
        skipped_comparisons=skips,
        non_applicable_reasons=tuple(d["non_applicable_reasons"]),
        warnings=tuple(d["warnings"]),
    )


def _pareto_to_dict(p: MultiObjectiveSummary) -> dict[str, Any]:
    return {
        "objectives": [
            {
                "name": o.name,
                "direction": o.direction.value,
                "source": o.source.value,
                "field_name": o.field_name,
            }
            for o in p.objectives
        ],
        "pareto_frontier": [
            {
                "config_id": list(pt.config_id),
                "objective_values": dict(pt.objective_values),
                "is_pareto_optimal": pt.is_pareto_optimal,
                "dominated_by": [list(db) for db in pt.dominated_by],
            }
            for pt in p.pareto_frontier
        ],
        "dominated_configurations": [
            {
                "config_id": list(pt.config_id),
                "objective_values": dict(pt.objective_values),
                "is_pareto_optimal": pt.is_pareto_optimal,
                "dominated_by": [list(db) for db in pt.dominated_by],
            }
            for pt in p.dominated_configurations
        ],
        "excluded_configurations": [
            {"config_id": list(e.config_id), "reason": e.reason}
            for e in p.excluded_configurations
        ],
    }


def _pareto_from_dict(d: dict[str, Any]) -> MultiObjectiveSummary:
    return MultiObjectiveSummary(
        objectives=tuple(
            ObjectiveSpec(
                name=o["name"],
                direction=MetricDirection(o["direction"]),
                source=ObjectiveSource(o["source"]),
                field_name=o.get("field_name"),
            )
            for o in d["objectives"]
        ),
        pareto_frontier=tuple(
            ParetoConfigurationPoint(
                config_id=(pt["config_id"][0], pt["config_id"][1]),
                objective_values=pt["objective_values"],
                is_pareto_optimal=bool(pt["is_pareto_optimal"]),
                dominated_by=tuple((db[0], db[1]) for db in pt["dominated_by"]),
            )
            for pt in d["pareto_frontier"]
        ),
        dominated_configurations=tuple(
            ParetoConfigurationPoint(
                config_id=(pt["config_id"][0], pt["config_id"][1]),
                objective_values=pt["objective_values"],
                is_pareto_optimal=bool(pt["is_pareto_optimal"]),
                dominated_by=tuple((db[0], db[1]) for db in pt["dominated_by"]),
            )
            for pt in d["dominated_configurations"]
        ),
        excluded_configurations=tuple(
            ExcludedParetoConfiguration(
                config_id=(e["config_id"][0], e["config_id"][1]),
                reason=e["reason"],
            )
            for e in d["excluded_configurations"]
        ),
    )


def _conclusion_to_dict(sc: StructuredConclusion) -> dict[str, Any]:
    return {
        "primary_metric": sc.primary_metric,
        "observed_leader": list(sc.observed_leader) if sc.observed_leader else None,
        "statistical_evidence_status": sc.statistical_evidence_status,
        "effect_magnitude_summary": sc.effect_magnitude_summary,
        "practical_relevance_status": sc.practical_relevance_status,
        "cost_tradeoff_summary": sc.cost_tradeoff_summary,
        "methodological_caveats": list(sc.methodological_caveats),
        "narrative_text": sc.narrative_text,
    }


def _conclusion_from_dict(d: dict[str, Any]) -> StructuredConclusion:
    return StructuredConclusion(
        primary_metric=d["primary_metric"],
        observed_leader=(d["observed_leader"][0], d["observed_leader"][1])
        if d.get("observed_leader")
        else None,
        statistical_evidence_status=d["statistical_evidence_status"],
        effect_magnitude_summary=d["effect_magnitude_summary"],
        practical_relevance_status=d["practical_relevance_status"],
        cost_tradeoff_summary=d["cost_tradeoff_summary"],
        methodological_caveats=tuple(d["methodological_caveats"]),
        narrative_text=d["narrative_text"],
    )


def save_statistics_artifacts(
    target_dir: Path | str,
    consolidation: DescriptiveConsolidation,
    suitability: MethodSuitabilityReport,
    comparisons: StatisticalComparisonBundle,
    conclusion: StructuredConclusion,
    pareto: MultiObjectiveSummary | None = None,
    *,
    force: bool = False,
) -> dict[str, Path]:
    """Atomically persist all Stage 5 statistical artifacts into target_dir (STAT-12, STORE-03, STORE-05)."""
    stats_dir = Path(target_dir)
    stats_dir.mkdir(parents=True, exist_ok=True)

    files_to_write = list(REQUIRED_STATISTICS_FILES)
    if pareto is not None:
        files_to_write.append("pareto_summary.json")

    if not force:
        existing = [f for f in files_to_write if (stats_dir / f).exists()]
        if existing:
            raise ContractViolationError(
                f"Statistics artifacts already exist in '{stats_dir}' ({existing}); pass force=True to overwrite."
            )

    manifest = {
        "experiment_id": consolidation.experiment_id,
        "partition_plan_id": consolidation.partition_plan_id,
        "total_configurations": consolidation.total_configurations,
        "total_comparisons": len(comparisons.comparisons),
        "skipped_comparisons": len(comparisons.skipped_comparisons),
        "has_pareto_summary": pareto is not None,
        "files": sorted(files_to_write),
    }

    written: dict[str, Path] = {}
    payloads: list[tuple[str, dict[str, Any]]] = [
        ("descriptive_consolidation.json", _consolidation_to_dict(consolidation)),
        ("method_suitability.json", _suitability_to_dict(suitability)),
        ("statistical_comparisons.json", _comparisons_to_dict(comparisons)),
        ("structured_conclusion.json", _conclusion_to_dict(conclusion)),
        ("statistics_manifest.json", manifest),
    ]
    if pareto is not None:
        payloads.append(("pareto_summary.json", _pareto_to_dict(pareto)))

    for fname, data in payloads:
        out_path = stats_dir / fname
        write_json_atomic(out_path, data, overwrite=force)
        written[fname] = out_path

    return written


def load_statistics_artifacts(target_dir: Path | str) -> LoadedStatisticsArtifacts:
    """Load and reconstruct all Stage 5 statistical artifacts from target_dir (STAT-12)."""
    stats_dir = Path(target_dir)
    for fname in REQUIRED_STATISTICS_FILES:
        fpath = stats_dir / fname
        if not fpath.is_file():
            raise DataIntegrityError(f"Missing required Stage 5 artifact: '{fpath}'")

    try:
        consol = _consolidation_from_dict(read_json(stats_dir / "descriptive_consolidation.json"))
        suit = _suitability_from_dict(read_json(stats_dir / "method_suitability.json"))
        comp = _comparisons_from_dict(read_json(stats_dir / "statistical_comparisons.json"))
        conc = _conclusion_from_dict(read_json(stats_dir / "structured_conclusion.json"))
        manifest = read_json(stats_dir / "statistics_manifest.json")
        pareto_path = stats_dir / "pareto_summary.json"
        pareto = _pareto_from_dict(read_json(pareto_path)) if pareto_path.is_file() else None
    except DataIntegrityError:
        raise
    except Exception as exc:
        raise DataIntegrityError(f"Corrupt or invalid Stage 5 artifact in '{stats_dir}': {exc}") from exc

    return LoadedStatisticsArtifacts(
        consolidation=consol,
        suitability=suit,
        comparisons=comp,
        conclusion=conc,
        pareto=pareto,
        manifest=manifest,
    )
