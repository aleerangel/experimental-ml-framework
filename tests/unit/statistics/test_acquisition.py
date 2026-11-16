"""Unit tests for sequential acquisition scoring functions (STAT-10, XCUT-02)."""

import math
import pytest

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.metrics.types import MetricDirection
from experimental_ml.statistics.acquisition import score_candidate_acquisition
from experimental_ml.statistics.types import AcquisitionCriterion, CandidatePrediction


def test_m63_02_acquisition_criteria_and_zero_std() -> None:
    """C5: Exact EI, UCB, LCB, EXPLOITATION, EXPLORATION with safe std=0 and deterministic tie-break."""
    cands = [
        CandidatePrediction("c_b", mean=1.0, std=0.5),
        CandidatePrediction("c_a", mean=1.0, std=0.5),  # tie-break c_a before c_b
        CandidatePrediction("c_high_mean", mean=2.0, std=0.0),
        CandidatePrediction("c_uncertain", mean=1.5, std=1.0),
    ]

    # UCB (MAXIMIZE): mu + kappa*std with kappa=2.0 -> c_uncertain = 3.5, c_high_mean = 2.0, c_a = 2.0, c_b = 2.0
    ucb_res = score_candidate_acquisition(cands, AcquisitionCriterion.UCB, kappa=2.0)
    assert ucb_res[0].candidate_id == "c_uncertain"
    assert ucb_res[0].score == pytest.approx(3.5)
    assert [r.rank for r in ucb_res] == [1, 2, 3, 4]
    # Tie-break: c_a before c_b (score=2.0)
    ids_tied = [r.candidate_id for r in ucb_res if r.score == 2.0]
    assert ids_tied == ["c_a", "c_b", "c_high_mean"]

    # LCB (MINIMIZE): mu - kappa*std with kappa=2.0 -> c_uncertain = -0.5, c_a=0.0, c_b=0.0, c_high_mean=2.0
    lcb_res = score_candidate_acquisition(
        cands, AcquisitionCriterion.LCB, direction=MetricDirection.MINIMIZE, kappa=2.0
    )
    assert lcb_res[0].candidate_id == "c_uncertain"
    assert lcb_res[0].score == pytest.approx(-0.5)

    # EXPECTED_IMPROVEMENT (MAXIMIZE, best_observed=2.0, xi=0.0):
    # c_high_mean has std=0 and mean=2.0 -> EI=0.0
    # c_uncertain has mean=1.5, std=1.0 -> delta=-0.5, Z=-0.5 -> EI = -0.5*Phi(-0.5) + 1.0*phi(-0.5)
    ei_res = score_candidate_acquisition(
        cands, AcquisitionCriterion.EXPECTED_IMPROVEMENT, direction=MetricDirection.MAXIMIZE, best_observed=2.0, xi=0.0
    )
    z = -0.5
    phi_cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    phi_pdf = math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    expected_ei = -0.5 * phi_cdf + 1.0 * phi_pdf
    assert ei_res[0].candidate_id == "c_uncertain"
    assert ei_res[0].score == pytest.approx(expected_ei, abs=1e-12)
    zero_std_rec = [r for r in ei_res if r.candidate_id == "c_high_mean"][0]
    assert zero_std_rec.score == 0.0

    # EXPLOITATION & EXPLORATION
    exp_res = score_candidate_acquisition(cands, AcquisitionCriterion.EXPLOITATION, direction=MetricDirection.MAXIMIZE)
    assert exp_res[0].candidate_id == "c_high_mean"
    expl_res = score_candidate_acquisition(cands, AcquisitionCriterion.EXPLORATION)
    assert expl_res[0].candidate_id == "c_uncertain"


def test_m63_02_invalid_candidates_rejected() -> None:
    """C6: Rejects empty candidate list, negative kappa/xi, negative std, or non-finite values."""
    with pytest.raises(ContractViolationError):
        CandidatePrediction("bad", mean=1.0, std=-0.01)

    with pytest.raises(ConfigurationError):
        score_candidate_acquisition([], AcquisitionCriterion.UCB)

    with pytest.raises(ConfigurationError):
        score_candidate_acquisition(
            [CandidatePrediction("c1", 1.0, 0.1)],
            AcquisitionCriterion.UCB,
            kappa=-1.0,
        )
