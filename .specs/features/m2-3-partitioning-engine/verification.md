# m2-3-partitioning-engine verification

**Verdict**: PASS
**Proofs**: `proofs.md` at d7f5595
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/validation/test_engine.py` `test_part_01_kfold_cv_only` | yes |
| C2 | `tests/unit/validation/test_splitters.py` `test_part_02_stratified_kfold_proportions` | yes |
| C3 | `tests/unit/validation/test_splitters.py` `test_part_03_group_kfold_disjointness` | yes |
| C4 | `tests/unit/validation/test_splitters.py` `test_part_04_temporal_monotonicity` | yes |
| C5 | `tests/unit/validation/test_splitters.py` `test_part_05_bootstrap_oob` | yes |
| C6 | `tests/unit/validation/test_engine.py` `test_part_06_holdout_separation` | yes |
| C7 | `tests/unit/validation/test_validators.py` `test_part_07_validate_partition_plan_invariants` | yes |
| C8 | `tests/unit/validation/test_types.py` `test_part_08_partition_plan_plan_id` | yes |
| C9 | `tests/integration/test_validation_integration.py` `test_part_09_immutability_and_determinism` | yes |
| C10 | `tests/unit/validation/test_types.py` `test_part_10_config_boundary_validation` | yes |

## Own examples

Three boundary / edge case behaviors were tested independently against the codebase at `HEAD`:

1. **`GROUP_KFOLD` boundary where unique groups equals `n_splits`**:
   - Tested partitioning with 6 observations across exactly 3 unique groups (`g1`, `g2`, `g3`) and `n_splits = 3`.
   - Verified that each bin receives exactly 1 group (2 observations), train sets have size 4, val sets have size 2, and zero group overlap exists between train and validation across all folds.

2. **`STRATIFIED_KFOLD` with rare classes ($< n\_splits$)**:
   - Tested 12 observations across 3 classes where class 2 contains only 2 observations while `n_splits = 3`.
   - Verified that `stratified_kfold_split` preserves complete coverage, strictly disjoint train/val sets for each fold, and correctly distributes the rare class samples without index errors or omission.

3. **`TEMPORAL` expanding window minimal boundary ($N = n\_splits + 1$)**:
   - Tested 3 observations across timestamps with `n_splits = 2` ($N = 2 + 1 = 3$).
   - Verified that `temporal_split` yields 2 valid folds where $\max(\text{Time}(\text{Train}_k)) \le \min(\text{Time}(\text{Val}_k))$ and train/val sets strictly partition segments chronologically without temporal leakage.

## Findings

None - all checks genuinely prove their acceptance criteria, boundary conditions hold across all splitters, and mathematical invariants are strictly enforced by the engine and validator.
