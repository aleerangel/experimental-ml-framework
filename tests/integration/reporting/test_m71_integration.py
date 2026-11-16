"""End-to-end integration tests for M7.1 read-only reporting and runtime purity (XCUT-02)."""

from pathlib import Path
import subprocess
import sys

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.reporting import (
    ReportAudience,
    ReportContentSelection,
    ReportFamily,
    build_table_model,
    load_experiment_artifacts_readonly,
    render_table_csv,
    render_table_latex,
    render_table_markdown,
    select_report_content,
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


def test_m71_end_to_end_readonly_tables(tmp_path: Path) -> None:
    """C10: End-to-end read-only pipeline from persisted Stage 1-5 artifacts to Tables A-G."""
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
        plan_id="pp_int_m71",
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
    consol = DescriptiveConsolidation("exp_int_m71", plan.plan_id, 2, {("m1", "s1"): sum1, ("m2", "s1"): sum2}, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(("rmse",), {"rmse": MetricDirection.MINIMIZE}, ComparisonScope.ALL_PAIRWISE, multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI)
    comp = run_statistical_comparisons(consol, plan, spec, suit)
    pareto = compute_pareto_frontier(consol, MultiObjectiveSpec((ObjectiveSpec("rmse", MetricDirection.MINIMIZE),)))
    conc = synthesize_conclusions(consol, suit, comp, "rmse", MetricDirection.MINIMIZE, pareto)
    save_statistics_artifacts(tmp_path / "statistics", consol, suit, comp, conc, pareto=pareto)

    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    write_json_atomic(tmp_path / "data" / "dataset_profile.json", {"n_rows": 50, "dataset_hash": "a" * 64}, overwrite=True)

    loaded = load_experiment_artifacts_readonly(tmp_path)
    sel = select_report_content(loaded, ReportContentSelection(audience=ReportAudience.FULL_LAB))

    for fam in sel.families:
        tbl = build_table_model(fam, loaded, sel)
        assert render_table_csv(tbl)
        assert render_table_markdown(tbl)
        assert "\\toprule" in render_table_latex(tbl)


def test_m71_runtime_purity_xcut02() -> None:
    """C11: Reporting operates purely on stdlib + numpy without matplotlib/scipy/pandas."""
    code = (
        "import sys; "
        "sys.modules['matplotlib'] = None; "
        "sys.modules['scipy'] = None; "
        "sys.modules['pandas'] = None; "
        "import experimental_ml.reporting as rep; "
        "assert hasattr(rep, 'build_table_model') and sys.modules['matplotlib'] is None"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, f"Purity check failed: {proc.stderr}"
