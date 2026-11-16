# Verification: m6-3-pareto-acquisition-synthesis

**Verdict**: PASS  
**Author**: coding-agent  
**Verifier**: independent-verifier-subagent  
**Date**: 2026-11-16  

## Checks

| Check | Requirement | Test / Proof | Holds |
| --- | --- | --- | --- |
| C1 | `MultiObjectiveSpec`, `ObjectiveSpec`, `ParetoConfigurationPoint`, `MultiObjectiveSummary` validation & immutability (STAT-09, AC-M63-01-01) | `tests/unit/statistics/test_m63_types.py::test_m63_01_multiobjective_types_and_immutability` | yes |
| C2 | `compute_pareto_frontier` filters `CoverageStatus.VALID` + finite objectives and records `excluded_configurations` (STAT-09, AC-M63-01-02) | `tests/unit/statistics/test_pareto.py::test_m63_01_excludes_partial_and_nan_configs` | yes |
| C3 | `compute_pareto_frontier` exact non-dominated set & `dominated_by` tracking (STAT-09, AC-M63-01-03) | `tests/unit/statistics/test_pareto.py::test_m63_01_exact_pareto_frontier_and_dominance` | yes |
| C4 | `AcquisitionCriterion`, `CandidatePrediction`, `AcquisitionScoreRecord` validation & freeze (STAT-10, AC-M63-02-01) | `tests/unit/statistics/test_m63_types.py::test_m63_02_acquisition_types_and_immutability` | yes |
| C5 | `score_candidate_acquisition` exact EI/UCB/LCB/EXPLOITATION/EXPLORATION, safe `std=0`, deterministic tie-break (STAT-10, AC-M63-02-02) | `tests/unit/statistics/test_acquisition.py::test_m63_02_acquisition_criteria_and_zero_std` | yes |
| C6 | `score_candidate_acquisition` rejects negative `std`/`kappa` and non-finite inputs (STAT-10, AC-M63-02-03) | `tests/unit/statistics/test_acquisition.py::test_m63_02_invalid_candidates_rejected` | yes |
| C7 | `StructuredConclusion` frozen with all required fields (STAT-11, AC-M63-03-01) | `tests/unit/statistics/test_m63_types.py::test_m63_03_structured_conclusion_immutability` | yes |
| C8 | `synthesize_conclusions` numeric traceability in `narrative_text` without fabricating metrics (STAT-11, AC-M63-03-02) | `tests/unit/statistics/test_synthesis.py::test_m63_03_numeric_traceability_in_narrative` | yes |
| C9 | `synthesize_conclusions` never equates `p_adj >= alpha` with equivalence (STAT-11, AC-M63-03-03) | `tests/unit/statistics/test_synthesis.py::test_m63_03_no_equivalence_from_nonsignificance` | yes |
| C10 | `synthesize_conclusions` preserves `HOLDOUT_ONLY` & `PARTIAL_COVERAGE` caveats (STAT-11, AC-M63-03-04) | `tests/unit/statistics/test_synthesis.py::test_m63_03_preserves_methodological_caveats` | yes |
| C11 | End-to-end M6.1 -> M6.2 -> M6.3 pipeline via public `experimental_ml.statistics` API (STAT-09) | `tests/integration/statistics/test_m63_integration.py::test_m63_end_to_end_pipeline` | yes |
| C12 | Pure Python/NumPy runtime without `scipy` (XCUT-02) | `tests/integration/statistics/test_m63_integration.py::test_m63_runtime_purity_xcut02` | yes |

## Adversarial Numerical Probes

Executed via `.venv/bin/python -c ...` on 2026-11-16:
1. **Pareto mixed objectives & tie points**: Verified `compute_pareto_frontier` with `acc` (`MAXIMIZE`) and `fit_mean_s` (`MINIMIZE`), identical tie points `tie1`/`tie2` (neither dominates the other, both remain on `pareto_frontier` and both appear in `dom.dominated_by`), and exclusion of `PARTIAL_COVERAGE` and `UNDEFINED_NAN`.
2. **Acquisition EI (`MINIMIZE` vs `MAXIMIZE`, `std=0` with `delta > 0`, tie-breaking)**: Verified `EXPECTED_IMPROVEMENT` returns `max(0, delta)` (`0.49` for `delta=0.5, xi=0.01`) when `std=0` under both `MAXIMIZE` and `MINIMIZE`, and breaks ties deterministically by ascending `candidate_id`.
3. **Synthesis edge cases (`observed_leader is None`, `p_adj >= alpha`, `HOLDOUT_ONLY` + `PARTIAL_COVERAGE`)**: Verified `observed_leader is None` produces `"No valid observed leader"` in `narrative_text`, `p_adj >= alpha` states `"insufficient statistical evidence to reject H0 (non-significance does not imply equivalence)"`, and `HOLDOUT_ONLY` + `PARTIAL_COVERAGE` caveats are preserved in both `methodological_caveats` and `narrative_text`.

## Findings

None.
