"""End-to-end integration tests for M6.1 -> M6.2 -> M6.3 and runtime purity XCUT-02."""

import subprocess
import sys

from experimental_ml.core.enums import ExecutionStatus, MetricStatus
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.orchestration.types import CellResultRecord, TimingBreakdown
from experimental_ml.statistics import (
    AcquisitionCriterion,
    CandidatePrediction,
    ComparisonScope,
    ComparisonSpec,
    MultiObjectiveSpec,
    MultiplicityMethod,
    ObjectiveSource,
    ObjectiveSpec,
    compute_pareto_frontier,
    consolidate_descriptive,
    evaluate_method_suitability,
    run_statistical_comparisons,
    score_candidate_acquisition,
    synthesize_conclusions,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def test_m63_end_to_end_pipeline() -> None:
    """C11: Full Stage 5 pipeline from M6.1 consolidation -> M6.2 inference -> M6.3 Pareto & synthesis."""
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
        plan_id="pp_int_m63",
        source_dataset_hash="hash_int_m63",
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

    cells: list[CellResultRecord] = []
    for i in range(n_folds):
        for model_id, base_err, fit_t in [("fast", 1.2, 0.05), ("accurate", 1.0, 0.40)]:
            timing = TimingBreakdown(
                data_extraction_time_s=0.01,
                preprocessing_time_s=0.01,
                feature_selection_time_s=0.0,
                tuning_time_s=0.0,
                fit_time_s=fit_t,
                predict_time_s=0.01,
                evaluation_time_s=0.01,
                total_cell_time_s=fit_t + 0.04,
            )
            cells.append(
                CellResultRecord(
                    cell_id=f"{model_id}__sc1__fold_{i}",
                    experiment_id="exp_int_m63",
                    partition_plan_id=plan.plan_id,
                    model_id=model_id,
                    scenario_id="sc1",
                    fold_id=f"fold_{i}",
                    status=ExecutionStatus.COMPLETED,
                    metrics={
                        "rmse": MetricValue(
                            metric_id="rmse",
                            value=base_err + 0.01 * i,
                            status=MetricStatus.VALID,
                            direction=MetricDirection.MINIMIZE,
                            scope=MetricEvaluationScope.PER_FOLD,
                            n_samples=20,
                        )
                    },
                    timing=timing,
                    selected_features=("f1",),
                )
            )

    consol = consolidate_descriptive(
        cells,
        total_folds_per_config=n_folds,
        experiment_id="exp_int_m63",
        partition_plan_id=plan.plan_id,
    )
    suit = evaluate_method_suitability(plan, consol)
    cmp_spec = ComparisonSpec(
        metrics_of_interest=("rmse",),
        metric_directions={"rmse": MetricDirection.MINIMIZE},
        comparison_scope=ComparisonScope.ALL_PAIRWISE,
        multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI,
    )
    bundle = run_statistical_comparisons(consol, plan, cmp_spec, suit)
    pareto = compute_pareto_frontier(
        consol,
        MultiObjectiveSpec(
            objectives=(
                ObjectiveSpec("rmse", MetricDirection.MINIMIZE),
                ObjectiveSpec("fit_mean_s", MetricDirection.MINIMIZE, ObjectiveSource.TIMING_MEAN, "fit_mean_s"),
            )
        ),
    )
    conc = synthesize_conclusions(
        consol, suit, bundle, "rmse", MetricDirection.MINIMIZE, multi_objective_summary=pareto
    )

    assert conc.observed_leader == ("accurate", "sc1")
    assert len(pareto.pareto_frontier) == 2
    assert "accurate" in conc.narrative_text and "fast" in conc.narrative_text

    acq = score_candidate_acquisition(
        [CandidatePrediction("cand_1", 0.9, 0.2), CandidatePrediction("cand_2", 1.1, 0.05)],
        AcquisitionCriterion.LCB,
        direction=MetricDirection.MINIMIZE,
    )
    assert acq[0].candidate_id == "cand_1"


def test_m63_runtime_purity_xcut02() -> None:
    """C12: Verify M6.3 Pareto, acquisition, and synthesis run purely on stdlib + numpy without SciPy."""
    code = (
        "import sys; "
        "sys.modules['scipy'] = None; "
        "import experimental_ml.statistics as st; "
        "res = st.score_candidate_acquisition("
        "[st.CandidatePrediction('a', 1.0, 0.2), st.CandidatePrediction('b', 1.2, 0.3)], "
        "st.AcquisitionCriterion.EXPECTED_IMPROVEMENT); "
        "assert len(res) == 2 and sys.modules['scipy'] is None"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, f"Purity check failed: {proc.stderr}"
