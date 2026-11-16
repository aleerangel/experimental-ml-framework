"""Unit tests for M6.3 multi-objective, acquisition, and synthesis types (STAT-09 to STAT-11)."""

from dataclasses import FrozenInstanceError
import pytest

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.metrics.types import MetricDirection
from experimental_ml.statistics.types import (
    AcquisitionCriterion,
    AcquisitionScoreRecord,
    CandidatePrediction,
    ExcludedParetoConfiguration,
    MultiObjectiveSpec,
    MultiObjectiveSummary,
    ObjectiveSource,
    ObjectiveSpec,
    ParetoConfigurationPoint,
    StructuredConclusion,
)


def test_m63_01_multiobjective_types_and_immutability() -> None:
    """C1: ObjectiveSpec, MultiObjectiveSpec, ParetoConfigurationPoint, MultiObjectiveSummary validation and freeze."""
    obj1 = ObjectiveSpec(name="rmse", direction=MetricDirection.MINIMIZE)
    obj2 = ObjectiveSpec(
        name="fit_time",
        direction=MetricDirection.MINIMIZE,
        source=ObjectiveSource.TIMING_MEAN,
        field_name="mean_fit_time_s",
    )
    spec = MultiObjectiveSpec(objectives=(obj1, obj2))
    assert len(spec.objectives) == 2

    with pytest.raises(ConfigurationError):
        MultiObjectiveSpec(objectives=())

    pt = ParetoConfigurationPoint(
        config_id=("m1", "s1"),
        objective_values={"rmse": 1.0, "fit_time": 0.2},
        is_pareto_optimal=True,
        dominated_by=(),
    )
    excl = ExcludedParetoConfiguration(config_id=("m2", "s1"), reason="Incomplete coverage")
    summary = MultiObjectiveSummary(
        objectives=spec.objectives,
        pareto_frontier=(pt,),
        dominated_configurations=(),
        excluded_configurations=(excl,),
    )

    for obj, attr, val in [
        (obj1, "name", "other"),
        (spec, "objectives", ()),
        (pt, "is_pareto_optimal", False),
        (excl, "reason", "x"),
        (summary, "pareto_frontier", ()),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, attr, val)  # type: ignore[misc]


def test_m63_02_acquisition_types_and_immutability() -> None:
    """C4: AcquisitionCriterion, CandidatePrediction, AcquisitionScoreRecord validation and freeze."""
    assert set(AcquisitionCriterion) == {
        AcquisitionCriterion.EXPECTED_IMPROVEMENT,
        AcquisitionCriterion.UCB,
        AcquisitionCriterion.LCB,
        AcquisitionCriterion.EXPLOITATION,
        AcquisitionCriterion.EXPLORATION,
    }
    cand = CandidatePrediction(candidate_id="c1", mean=1.5, std=0.2)
    rec = AcquisitionScoreRecord(
        candidate_id="c1",
        criterion=AcquisitionCriterion.UCB,
        score=1.9,
        mean=1.5,
        std=0.2,
        rank=1,
    )

    with pytest.raises(ContractViolationError):
        CandidatePrediction(candidate_id="c2", mean=1.0, std=-0.1)
    with pytest.raises(ContractViolationError):
        CandidatePrediction(candidate_id="c3", mean=float("nan"), std=0.1)

    with pytest.raises(FrozenInstanceError):
        cand.mean = 2.0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        rec.rank = 2  # type: ignore[misc]


def test_m63_03_structured_conclusion_immutability() -> None:
    """C7: StructuredConclusion contains all required fields and is frozen."""
    conc = StructuredConclusion(
        primary_metric="rmse",
        observed_leader=("m1", "s1"),
        statistical_evidence_status="1 significant comparison after Holm-Bonferroni",
        effect_magnitude_summary="LARGE (d_z = -1.80)",
        practical_relevance_status="STATISTICALLY_SIGNIFICANT_AND_PRACTICAL",
        cost_tradeoff_summary="m1/s1 on Pareto frontier",
        methodological_caveats=("J = 5 < 6 for Wilcoxon",),
        narrative_text="Observed leader m1/s1 (mean=1.0000).",
    )
    assert conc.primary_metric == "rmse"
    with pytest.raises(FrozenInstanceError):
        conc.narrative_text = "mutated"  # type: ignore[misc]
