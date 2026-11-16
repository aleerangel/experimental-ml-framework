"""Unit tests for read-only experiment loader and content selection (REP-02, CA-E6-01)."""

from pathlib import Path
import sys

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.reporting.loader import (
    load_experiment_artifacts_readonly,
    select_report_content,
)
from experimental_ml.reporting.types import (
    ReportAudience,
    ReportContentSelection,
    ReportFamily,
)
from experimental_ml.statistics.comparisons import run_statistical_comparisons
from experimental_ml.statistics.multiobjective import compute_pareto_frontier
from experimental_ml.statistics.storage import save_statistics_artifacts
from experimental_ml.statistics.suitability import evaluate_method_suitability
from experimental_ml.statistics.synthesis import synthesize_conclusions
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    ComparisonScope,
    ComparisonSpec,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    MultiObjectiveSpec,
    MultiplicityMethod,
    ObjectiveSpec,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _create_persisted_experiment(exp_dir: Path) -> None:
    n_folds = 5
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"tr_{i}_{k}") for k in range(40)),
            val_ids=tuple(ObservationId(f"va_{i}_{k}") for k in range(10)),
        )
        for i in range(n_folds)
    )
    plan = PartitionPlan(
        plan_id="pp_rep",
        source_dataset_hash="a" * 64,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=tuple(ObservationId(f"d_{k}") for k in range(50)),
        holdout_ids=(),
        folds=folds,
        config=PartitionConfig(PartitionStrategy.KFOLD, EvaluationRegime.CV_ONLY, n_splits=n_folds),
    )
    sum1 = ConfigurationSummary(
        model_id="m1",
        scenario_id="s1",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(5)),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics={
            f"fold_{i}": {
                "rmse": MetricValue("rmse", 1.0 + 0.01 * i, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10)
            }
            for i in range(5)
        },
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.02, 0.0158, 1.02, 0.02, 1.01, 1.03, 1.00, 1.04)
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    sum2 = ConfigurationSummary(
        model_id="m2",
        scenario_id="s1",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(5)),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics={
            f"fold_{i}": {
                "rmse": MetricValue("rmse", 1.5 + 0.01 * i, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10)
            }
            for i in range(5)
        },
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.52, 0.0158, 1.52, 0.02, 1.51, 1.53, 1.50, 1.54)
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    consol = DescriptiveConsolidation("exp_rep", plan.plan_id, 2, {("m1", "s1"): sum1, ("m2", "s1"): sum2}, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(("rmse",), {"rmse": MetricDirection.MINIMIZE}, ComparisonScope.ALL_PAIRWISE, multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI)
    comp = run_statistical_comparisons(consol, plan, spec, suit)
    pareto = compute_pareto_frontier(consol, MultiObjectiveSpec((ObjectiveSpec("rmse", MetricDirection.MINIMIZE),)))
    conc = synthesize_conclusions(consol, suit, comp, "rmse", MetricDirection.MINIMIZE, pareto)
    save_statistics_artifacts(exp_dir / "statistics", consol, suit, comp, conc, pareto=pareto)

    # Optional Stage 1-3 JSONs
    (exp_dir / "data").mkdir(parents=True, exist_ok=True)
    write_json_atomic(exp_dir / "data" / "dataset_profile.json", {"n_rows": 50, "n_cols": 5, "dataset_hash": "a" * 64}, overwrite=True)


def test_m71_02_readonly_loader_no_model_execution(tmp_path: Path, monkeypatch) -> None:
    """C4: load_experiment_artifacts_readonly verifies Stage 5 gate without invoking model fit/predict/tuning."""
    _create_persisted_experiment(tmp_path)

    import experimental_ml.models.execution as mod_exec
    import experimental_ml.tuning.engine as tun_eng

    def _forbid(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("Model fit/predict/tuning must NEVER be invoked during Stage 6 reporting (CA-E6-01).")

    monkeypatch.setattr(mod_exec, "fit_model", _forbid)
    monkeypatch.setattr(mod_exec, "predict_model", _forbid)
    monkeypatch.setattr(tun_eng, "run_nested_tuning", _forbid)

    loaded = load_experiment_artifacts_readonly(tmp_path)
    assert loaded.experiment_id == "exp_rep"
    assert loaded.partition_plan_id == "pp_rep"
    assert loaded.dataset_profile is not None
    assert loaded.dataset_profile["n_rows"] == 50


def test_m71_02_select_report_content_modes(tmp_path: Path) -> None:
    """C5: select_report_content applies deterministic FULL_LAB, ARTICLE_COMPACT, and CUSTOM rules."""
    _create_persisted_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(tmp_path)

    full = select_report_content(loaded, ReportContentSelection(audience=ReportAudience.FULL_LAB))
    assert full.families == tuple(ReportFamily)
    assert full.model_ids == ("m1", "m2")
    assert full.scenario_ids == ("s1",)
    assert full.metric_ids == ("rmse",)

    compact = select_report_content(loaded, ReportContentSelection(audience=ReportAudience.ARTICLE_COMPACT))
    assert compact.families == (
        ReportFamily.D_PREDICTIVE_PERFORMANCE,
        ReportFamily.E_STATISTICAL_COMPARISONS,
        ReportFamily.F_STABILITY_COST_PARETO,
    )

    custom = select_report_content(
        loaded,
        ReportContentSelection(
            audience=ReportAudience.CUSTOM,
            families=(ReportFamily.D_PREDICTIVE_PERFORMANCE,),
            model_ids=("m1",),
        ),
    )
    assert custom.families == (ReportFamily.D_PREDICTIVE_PERFORMANCE,)
    assert custom.model_ids == ("m1",)
    assert custom.scenario_ids == ("s1",)
    assert custom.metric_ids == ("rmse",)
