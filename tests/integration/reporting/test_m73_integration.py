"""Integration and runtime purity tests for M7.3 reproducibility packaging and Stage 6 gate."""

from pathlib import Path
import shutil
import subprocess
import sys

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.reporting import (
    PackageMode,
    ReproducibilityPackageManifest,
    ResearcherDeclarations,
    build_reproducibility_package,
    load_experiment_artifacts_readonly,
)
from experimental_ml.stages.stage_gates import verify_report_gate
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


def test_m73_end_to_end_packaging_and_gate(tmp_path: Path) -> None:
    """C8: End-to-end packaging -> directory relocation -> verify_report_gate + XCUT-02 runtime purity."""
    n_folds = 5
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"tr_{i}_{k}") for k in range(20)),
            val_ids=tuple(ObservationId(f"va_{i}_{k}") for k in range(5)),
        )
        for i in range(n_folds)
    )
    plan = PartitionPlan(
        plan_id="pp_int_m73",
        source_dataset_hash="a" * 64,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=tuple(ObservationId(f"d_{k}") for k in range(25)),
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
                "rmse": MetricValue("rmse", 1.0 + 0.01 * i, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 5)
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
                "rmse": MetricValue("rmse", 1.5 + 0.01 * i, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 5)
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
    consol = DescriptiveConsolidation("exp_int_m73", plan.plan_id, 2, {("m1", "s1"): sum1, ("m2", "s1"): sum2}, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(("rmse",), {"rmse": MetricDirection.MINIMIZE}, ComparisonScope.ALL_PAIRWISE, multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI)
    comp = run_statistical_comparisons(consol, plan, spec, suit)
    pareto = compute_pareto_frontier(consol, MultiObjectiveSpec((ObjectiveSpec("rmse", MetricDirection.MINIMIZE),)))
    conc = synthesize_conclusions(consol, suit, comp, "rmse", MetricDirection.MINIMIZE, pareto)

    exp_dir = tmp_path / "exp_src"
    save_statistics_artifacts(exp_dir / "statistics", consol, suit, comp, conc, pareto=pareto)

    loaded = load_experiment_artifacts_readonly(exp_dir)
    pkg_dir = tmp_path / "pkg_initial"
    manifest = build_reproducibility_package(
        loaded,
        output_dir=pkg_dir,
        mode=PackageMode.FULL_PACKAGE,
        declarations=ResearcherDeclarations(scientific_objective="Integration verification"),
        source_experiment_dir=exp_dir,
    )
    assert isinstance(manifest, ReproducibilityPackageManifest)

    relocated_dir = tmp_path / "relocated" / "pkg_moved"
    relocated_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pkg_dir), str(relocated_dir))

    gate_summary = verify_report_gate(relocated_dir)
    assert gate_summary["status"] == "VERIFIED"
    assert gate_summary["experiment_id"] == "exp_int_m73"

    # XCUT-02 runtime purity check
    code = (
        "import sys; "
        "sys.modules['matplotlib'] = None; "
        "sys.modules['PIL'] = None; "
        "sys.modules['scipy'] = None; "
        "sys.modules['pandas'] = None; "
        "from experimental_ml.reporting import PackageMode, ReproducibilityPackageManifest, build_reproducibility_package; "
        "from experimental_ml.stages.stage_gates import verify_report_gate; "
        "print('PURE_OK')"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert "PURE_OK" in proc.stdout
