# m3-1-exploratory-features verification

**Verdict**: PASS
**Proofs**: `proofs.md` at b757812
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/features/test_exploration.py` `test_exp_01_mandatory_scope_and_warnings` | yes |
| C2 | `tests/unit/features/test_stats.py` `test_exp_02_pearson_and_spearman_continuous` | yes |
| C3 | `tests/unit/features/test_stats.py` `test_exp_03_correlation_ratio_eta` | yes |
| C4 | `tests/unit/features/test_stats.py` `test_exp_04_cramers_v` | yes |
| C5 | `tests/unit/features/test_stats.py` `test_exp_05_degeneracy_and_undefined_nan` | yes |
| C6 | `tests/unit/features/test_exploration.py` `test_exp_06_predictor_redundancy_and_sorting` | yes |
| C7 | `tests/unit/features/test_feature_types.py` `test_exp_07_roundtrip_serialization` | yes |
| C8 | `tests/integration/features/test_features_integration.py` `test_exp_08_end_to_end_pipeline` | yes |

## Own examples

Three boundary, numeric degeneracy, and extreme configuration behaviors were tested independently against the codebase at `HEAD`:

1. **Large numeric offsets and catastrophic cancellation guard in Pearson correlation**:
   - Vectors evaluated with $x = 10^{12} + [1, 2, 3, 4, 5]$ and $y = 10^{12} + [2, 4, 6, 8, 10]$.
   - Verified that center-subtracted variance computation maintains numerical precision without catastrophic cancellation, returning $r = 1.0$ and `MetricStatus.VALID`.

2. **Multiclass categorical association with high cardinality in Cramér's V**:
   - Evaluated 5x5 categorical arrays with balanced frequencies across categories.
   - Verified that contingency table generation and $\chi^2$ degrees of freedom scaling correctly yield $V = 1.0$ and `MetricStatus.VALID` without numerical overflow or index misalignments.

3. **Extreme boundary values for redundancy threshold ($0.0$ and $1.0$)**:
   - Tested `explore_features` with `redundancy_threshold=0.0` and `redundancy_threshold=1.0`.
   - Verified that threshold filtering accurately includes all pairs at $0.0$ and strictly limits inclusion to perfect correlations ($|r| \ge 1.0$) at $1.0$, while inputs outside $[0.0, 1.0]$ or non-finite values reject gracefully with `ConfigurationError`.

## Findings

None - all 8 checks genuinely prove their acceptance criteria, numerical degeneracy and edge cases return UNDEFINED_NAN gracefully, and immutability invariants are strictly enforced across feature reports and public exports.
