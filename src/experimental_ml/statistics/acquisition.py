"""Sequential acquisition functions for candidates with uncertainty (Submodule 5B, STAT-10, XCUT-02)."""

from __future__ import annotations

import math
from typing import Sequence

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.metrics.types import MetricDirection
from experimental_ml.statistics.types import (
    AcquisitionCriterion,
    AcquisitionScoreRecord,
    CandidatePrediction,
)


def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _norm_pdf(z: float) -> float:
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def score_candidate_acquisition(
    candidates: Sequence[CandidatePrediction],
    criterion: AcquisitionCriterion,
    direction: MetricDirection = MetricDirection.MAXIMIZE,
    best_observed: float | None = None,
    xi: float = 0.01,
    kappa: float = 2.0,
) -> tuple[AcquisitionScoreRecord, ...]:
    """Score and deterministically rank candidates with predictive uncertainty (STAT-10)."""
    if not candidates:
        raise ConfigurationError("Candidate list for acquisition scoring must not be empty.")
    if not isinstance(criterion, AcquisitionCriterion):
        criterion = AcquisitionCriterion(criterion)
    if not isinstance(direction, MetricDirection):
        direction = MetricDirection(direction)
    if not math.isfinite(xi) or xi < 0.0:
        raise ConfigurationError(f"Exploration parameter xi must be finite and >= 0; got {xi}.")
    if not math.isfinite(kappa) or kappa < 0.0:
        raise ConfigurationError(f"Confidence bound kappa must be finite and >= 0; got {kappa}.")

    if best_observed is None:
        f_star = (
            max(c.mean for c in candidates)
            if direction == MetricDirection.MAXIMIZE
            else min(c.mean for c in candidates)
        )
    else:
        f_star = float(best_observed)
        if not math.isfinite(f_star):
            raise ConfigurationError(f"best_observed must be finite; got {best_observed}.")

    scored: list[tuple[float, CandidatePrediction, float]] = []
    for cand in candidates:
        if criterion == AcquisitionCriterion.EXPECTED_IMPROVEMENT:
            delta = (
                (cand.mean - f_star - xi)
                if direction == MetricDirection.MAXIMIZE
                else (f_star - cand.mean - xi)
            )
            if cand.std == 0.0:
                raw_score = max(0.0, delta)
            else:
                z = delta / cand.std
                raw_score = max(0.0, delta * _norm_cdf(z) + cand.std * _norm_pdf(z))
            sort_key = -raw_score
        elif criterion == AcquisitionCriterion.UCB:
            raw_score = cand.mean + kappa * cand.std
            sort_key = -raw_score
        elif criterion == AcquisitionCriterion.LCB:
            raw_score = cand.mean - kappa * cand.std
            sort_key = raw_score
        elif criterion == AcquisitionCriterion.EXPLOITATION:
            raw_score = cand.mean
            sort_key = -raw_score if direction == MetricDirection.MAXIMIZE else raw_score
        elif criterion == AcquisitionCriterion.EXPLORATION:
            raw_score = cand.std
            sort_key = -raw_score
        else:
            raise ConfigurationError(f"Unsupported AcquisitionCriterion: {criterion}")

        scored.append((sort_key, cand, raw_score))

    scored.sort(key=lambda item: (item[0], item[1].candidate_id))

    return tuple(
        AcquisitionScoreRecord(
            candidate_id=cand.candidate_id,
            criterion=criterion,
            score=float(raw_score),
            mean=cand.mean,
            std=cand.std,
            rank=idx + 1,
        )
        for idx, (_, cand, raw_score) in enumerate(scored)
    )
