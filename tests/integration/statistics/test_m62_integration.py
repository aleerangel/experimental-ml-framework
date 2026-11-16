"""End-to-end integration tests for M6.1 -> M6.2 and runtime purity XCUT-02."""

import subprocess
import sys

from experimental_ml.core.enums import ExecutionStatus, MetricStatus
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.orchestration.types import CellResultRecord, TimingBreakdown
from experimental_ml.statistics import (
    ComparisonScope,
    ComparisonSpec,
    IncompleteComparisonPolicy,
    MultiplicityMethod,
    consolidate_descriptive,
    evaluate_method_suitability,
    run_statistical_comparisons,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def test_m62_end_to_end_pipeline() -> None:
    """C17: End-to-end integration from Stage 4 cell records through M6.1 consolidation to M6.2 inference."""
    n_folds = 6
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"tr_{i}_{k}") for k in range(80)),
            val_ids=tuple(ObservationId(f"va_{i}_{k}") for k in range(20)),
        )
        for i in range(n_folds)
    )
    plan = PartitionPlan(
        plan_id="pp_int_m62",
        source_dataset_hash="hash_int_m62",
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=tuple(ObservationId(f"d_{k}") for k in range(100)),
        holdout_ids=(),
        folds=folds,
        config=PartitionConfig(
            strategy=PartitionStrategy.KFOLD,
            regime=EvaluationRegime.CV_ONLY,
            n_splits=n_folds,
        ),
    )

    timing = TimingBreakdown(
        data_extraction_time_s=0.01,
        preprocessing_time_s=0.02,
        feature_selection_time_s=0.01,
        tuning_time_s=0.0,
        fit_time_s=0.1,
        predict_time_s=0.01,
        evaluation_time_s=0.01,
        total_cell_time_s=0.16,
    )

    cells: list[CellResultRecord] = []
    for i in range(n_folds):
        for model_id, base_err in [("m_alpha", 1.0), ("m_beta", 1.4), ("m_gamma", 1.6)]:
            val = base_err + 0.03 * i
            cells.append(
                CellResultRecord(
                    cell_id=f"{model_id}__sc1__fold_{i}",
                    experiment_id="exp_int_m62",
                    partition_plan_id=plan.plan_id,
                    model_id=model_id,
                    scenario_id="sc1",
                    fold_id=f"fold_{i}",
                    status=ExecutionStatus.COMPLETED,
                    metrics={
                        "rmse": MetricValue(
                            metric_id="rmse",
                            value=val,
                            status=MetricStatus.VALID,
                            direction=MetricDirection.MINIMIZE,
                            scope=MetricEvaluationScope.PER_FOLD,
                            n_samples=20,
                        )
                    },
                    timing=timing,
                    selected_features=("f1", "f2"),
                )
            )

    consol = consolidate_descriptive(
        cells,
        total_folds_per_config=n_folds,
        experiment_id="exp_int_m62",
        partition_plan_id=plan.plan_id,
    )
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(
        metrics_of_interest=("rmse",),
        metric_directions={"rmse": MetricDirection.MINIMIZE},
        comparison_scope=ComparisonScope.AGAINST_BASELINE,
        baseline_config=("m_gamma", "sc1"),
        alpha=0.05,
        multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI,
        practical_relevance_thresholds={"rmse": 0.3},
    )
    bundle = run_statistical_comparisons(
        consol, plan, spec, suit, policy=IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY
    )

    assert len(bundle.comparisons) == 2
    assert bundle.skipped_comparisons == ()
    for cmp_res in bundle.comparisons:
        assert cmp_res.observed_better in (("m_alpha", "sc1"), ("m_beta", "sc1"))
        assert cmp_res.nadeau_bengio_adjusted_p >= cmp_res.nadeau_bengio.p_value
        assert cmp_res.wilcoxon_adjusted_p >= cmp_res.wilcoxon.p_value


def test_m62_runtime_purity_xcut02() -> None:
    """C18: Verify M6.2 inference and multiplicity run purely on stdlib + numpy without SciPy."""
    code = (
        "import sys; "
        "sys.modules['scipy'] = None; "
        "sys.modules['scipy.stats'] = None; "
        "import experimental_ml.statistics as st; "
        "nb = st.paired_nadeau_bengio_test([1.0, 1.1, 1.2, 1.3, 1.4, 1.5], [1.5, 1.7, 1.8, 1.9, 2.0, 2.1], 0.2); "
        "wx = st.paired_wilcoxon_test([1.0, 1.1, 1.2, 1.3, 1.4, 1.5], [1.5, 1.7, 1.8, 1.9, 2.0, 2.1]); "
        "es = st.compute_paired_cohens_d([1.0, 1.1, 1.2, 1.3, 1.4, 1.5], [1.5, 1.7, 1.8, 1.9, 2.0, 2.1]); "
        "adj = st.adjust_pvalues_holm([nb.p_value, wx.p_value]); "
        "assert len(adj) == 2 and 'scipy' not in sys.modules or sys.modules['scipy'] is None"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, f"Purity check failed: {proc.stderr}"
