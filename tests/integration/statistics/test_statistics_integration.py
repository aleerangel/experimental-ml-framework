"""End-to-end integration tests for experimental statistics (Marco M6 — Sub-marco M6.1).

Validates full lifecycle integration, public API exports, runtime purity (XCUT-02),
and domain independence (RNF02).
"""

from pathlib import Path
import subprocess
import sys
import pytest

from experimental_ml.core.enums import ExecutionStatus, MetricDirection, MetricStatus, TaskType
from experimental_ml.core.types import CellId, ExperimentId, ObservationId, PartitionPlanId
from experimental_ml.metrics.types import MetricEvaluationScope, MetricValue
from experimental_ml.orchestration.oof import ConsolidatedOofPredictions
from experimental_ml.orchestration.state import MatrixExecutionState, save_execution_state
from experimental_ml.orchestration.types import CellResultRecord, TimingBreakdown
from experimental_ml.statistics import (
    AggregatedMetricStats,
    AggregatedTimingStats,
    ApplicabilityStatus,
    ApplicableMethod,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    IncompleteComparisonPolicy,
    MethodSuitabilityReport,
    check_pairwise_comparison_eligibility,
    consolidate_descriptive,
    evaluate_method_suitability,
    validate_stage5_entry,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def test_statistics_public_api_exports() -> None:
    """Validate all public symbols are properly exported from experimental_ml.statistics."""
    import experimental_ml.statistics as stats_pkg

    expected_symbols = [
        "CoverageStatus",
        "IncompleteComparisonPolicy",
        "ApplicabilityStatus",
        "AggregatedMetricStats",
        "AggregatedTimingStats",
        "ConfigurationSummary",
        "DescriptiveConsolidation",
        "ApplicableMethod",
        "MethodSuitabilityReport",
        "validate_stage5_entry",
        "consolidate_descriptive",
        "evaluate_method_suitability",
        "check_pairwise_comparison_eligibility",
    ]
    for sym in expected_symbols:
        assert hasattr(stats_pkg, sym), f"Symbol {sym} missing from experimental_ml.statistics"
        assert sym in stats_pkg.__all__, f"Symbol {sym} missing from __all__"


def test_statistics_end_to_end_lifecycle(tmp_path: Path) -> None:
    """Full lifecycle integration: stage 5 gate validation, descriptive consolidation, and suitability."""
    exp_id = ExperimentId("exp_integration_01")
    plan_id = PartitionPlanId("plan_integration_01")
    n_folds = 5

    # 1. Build PartitionPlan (CV_AND_HOLDOUT)
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"tr_{i}_{k}") for k in range(80)),
            val_ids=tuple(ObservationId(f"val_{i}_{k}") for k in range(20)),
        )
        for i in range(n_folds)
    )
    holdout_ids = tuple(ObservationId(f"hold_{k}") for k in range(30))
    dev_ids = tuple(ObservationId(f"dev_{k}") for k in range(100))
    plan = PartitionPlan(
        plan_id=str(plan_id),
        source_dataset_hash="hash_data_abc",
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        strategy=PartitionStrategy.KFOLD,
        development_ids=dev_ids,
        holdout_ids=holdout_ids,
        folds=folds,
        config=PartitionConfig(
            strategy=PartitionStrategy.KFOLD,
            n_splits=n_folds,
            regime=EvaluationRegime.CV_AND_HOLDOUT,
            holdout_fraction=0.2,
        ),
    )

    # 2. Simulate 3 Configurations with varying coverage:
    # Config 1: (ridge, sc_all) -> 5/5 COMPLETED -> VALID
    # Config 2: (lasso, sc_all) -> 4/5 COMPLETED, 1 FAILED -> PARTIAL_COVERAGE
    # Config 3: (dummy, sc_all) -> 0/5 COMPLETED (5 CANCELLED) -> NO_COVERAGE
    cell_statuses: dict[CellId, ExecutionStatus] = {}
    cell_records: list[CellResultRecord] = []

    # Config 1
    for i in range(n_folds):
        cid = CellId(f"cell_ridge_sc_all_fold_{i}")
        cell_statuses[cid] = ExecutionStatus.COMPLETED
        cell_records.append(
            CellResultRecord(
                cell_id=cid,
                experiment_id=exp_id,
                partition_plan_id=plan_id,
                model_id="ridge",
                scenario_id="sc_all",
                fold_id=f"fold_{i}",
                timing=TimingBreakdown(fit_time_s=0.1 * (i + 1), total_cell_time_s=0.2 * (i + 1)),
                status=ExecutionStatus.COMPLETED,
                selected_features=("feat_1", "feat_2"),
                metrics={
                    "rmse": MetricValue(
                        metric_id="rmse",
                        value=0.20 + 0.01 * i,
                        status=MetricStatus.VALID,
                        direction=MetricDirection.MINIMIZE,
                        scope=MetricEvaluationScope.PER_FOLD,
                        n_samples=20,
                    )
                },
            )
        )

    # Config 2
    for i in range(n_folds):
        cid = CellId(f"cell_lasso_sc_all_fold_{i}")
        status = ExecutionStatus.COMPLETED if i < 4 else ExecutionStatus.FAILED
        cell_statuses[cid] = status
        cell_records.append(
            CellResultRecord(
                cell_id=cid,
                experiment_id=exp_id,
                partition_plan_id=plan_id,
                model_id="lasso",
                scenario_id="sc_all",
                fold_id=f"fold_{i}",
                timing=TimingBreakdown(fit_time_s=0.05, total_cell_time_s=0.1),
                status=status,
                selected_features=("feat_1",),
                metrics=(
                    {
                        "rmse": MetricValue(
                            metric_id="rmse",
                            value=0.22 + 0.01 * i,
                            status=MetricStatus.VALID,
                            direction=MetricDirection.MINIMIZE,
                            scope=MetricEvaluationScope.PER_FOLD,
                            n_samples=20,
                        )
                    }
                    if status == ExecutionStatus.COMPLETED
                    else {}
                ),
            )
        )

    # Config 3
    for i in range(n_folds):
        cid = CellId(f"cell_dummy_sc_all_fold_{i}")
        cell_statuses[cid] = ExecutionStatus.CANCELLED
        cell_records.append(
            CellResultRecord(
                cell_id=cid,
                experiment_id=exp_id,
                partition_plan_id=plan_id,
                model_id="dummy",
                scenario_id="sc_all",
                fold_id=f"fold_{i}",
                timing=TimingBreakdown(),
                status=ExecutionStatus.CANCELLED,
            )
        )

    # 3. Save MatrixExecutionState to tmp_path / "runs"
    run_dir = tmp_path / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    exec_state = MatrixExecutionState(
        experiment_id=exp_id,
        run_id="run_int_01",
        created_at="2026-11-16T12:00:00Z",
        updated_at="2026-11-16T12:10:00Z",
        master_seed=42,
        total_cells=len(cell_statuses),
        cell_statuses=cell_statuses,
    )
    save_execution_state(exec_state, run_dir, overwrite=True)

    # 4. Stage 5 gate validation
    validate_stage5_entry(run_dir)

    # 5. Descriptive consolidation
    obs_sorted = tuple(ObservationId(f"obs_{k:04d}") for k in range(100))
    oof_ridge = ConsolidatedOofPredictions(
        model_id="ridge",
        scenario_id="sc_all",
        task_type=TaskType.REGRESSION,
        observation_ids=obs_sorted,
        y_true=tuple(1.0 for _ in range(100)),
        y_pred=tuple(1.05 for _ in range(100)),
        coverage=1.0,
        pooled_metrics={
            "rmse": MetricValue(
                metric_id="rmse",
                value=0.22,
                status=MetricStatus.VALID,
                direction=MetricDirection.MINIMIZE,
                scope=MetricEvaluationScope.POOLED_OOF,
                n_samples=100,
            )
        },
    )

    consol = consolidate_descriptive(
        cell_results=cell_records,
        total_folds_per_config={
            ("ridge", "sc_all"): n_folds,
            ("lasso", "sc_all"): n_folds,
            ("dummy", "sc_all"): n_folds,
        },
        oof_predictions=[oof_ridge],
        n_total_candidates_per_config={
            ("ridge", "sc_all"): 10,
            ("lasso", "sc_all"): 10,
            ("dummy", "sc_all"): 10,
        },
        experiment_id=str(exp_id),
        partition_plan_id=str(plan_id),
    )

    assert consol.total_configurations == 3
    s_ridge = consol.configurations[("ridge", "sc_all")]
    s_lasso = consol.configurations[("lasso", "sc_all")]
    s_dummy = consol.configurations[("dummy", "sc_all")]

    assert s_ridge.coverage_status == CoverageStatus.VALID
    assert s_ridge.coverage == 1.0
    assert s_ridge.completed_folds == 5
    assert "rmse" in s_ridge.pooled_oof_metrics
    assert s_ridge.feature_stability is not None

    assert s_lasso.coverage_status == CoverageStatus.PARTIAL_COVERAGE
    assert s_lasso.coverage == 0.8
    assert s_lasso.completed_folds == 4
    assert s_lasso.failed_folds == 1

    assert s_dummy.coverage_status == CoverageStatus.NO_COVERAGE
    assert s_dummy.coverage == 0.0
    assert s_dummy.completed_folds == 0
    assert s_dummy.cancelled_folds == 5
    assert s_dummy.aggregated_timing is None

    # 6. Methodological suitability evaluation
    suitability = evaluate_method_suitability(plan, consol)
    assert suitability.is_cross_validation is True
    assert suitability.total_development_partitions == 5
    assert suitability.evaluation_regime == EvaluationRegime.CV_AND_HOLDOUT
    assert suitability.applicable_methods["nadeau_bengio_paired_t"].status == ApplicabilityStatus.APPLICABLE
    assert suitability.applicable_methods["wilcoxon_signed_rank_paired"].status == ApplicabilityStatus.APPLICABLE
    assert suitability.applicable_methods["paired_t_test_uncorrected"].status == ApplicabilityStatus.NOT_SUITABLE

    # 7. Comparison eligibility
    # Ridge vs Lasso under STRICT: rejected because Lasso has partial coverage
    ok_strict, reason_strict, _ = check_pairwise_comparison_eligibility(
        s_ridge, s_lasso, IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY
    )
    assert ok_strict is False
    assert "strict_complete_only" in reason_strict.lower()

    # Ridge vs Lasso under COMMON_SUBSET: eligible with 4 common folds
    ok_common, reason_common, shared = check_pairwise_comparison_eligibility(
        s_ridge, s_lasso, IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET
    )
    assert ok_common is True
    assert len(shared) == 4

    # Ridge vs Dummy: rejected because J_paired == 0 < 2
    ok_dummy, reason_dummy, _ = check_pairwise_comparison_eligibility(
        s_ridge, s_dummy, IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET
    )
    assert ok_dummy is False
    assert "insufficient" in reason_dummy.lower()


def test_statistics_runtime_purity_xcut02() -> None:
    """Validate runtime purity (XCUT-02): zero heavy external dependencies upon importing statistics."""
    script = (
        "import sys\n"
        "import experimental_ml.statistics\n"
        "forbidden = ['scipy', 'pandas', 'sklearn', 'torch', 'matplotlib', 'seaborn', 'joblib']\n"
        "loaded_forbidden = [pkg for pkg in forbidden if any(m.startswith(pkg) for m in sys.modules)]\n"
        "if loaded_forbidden:\n"
        "    print(f'VIOLATION: {loaded_forbidden}')\n"
        "    sys.exit(1)\n"
        "sys.exit(0)\n"
    )
    res = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Runtime purity violation: {res.stdout} {res.stderr}"
