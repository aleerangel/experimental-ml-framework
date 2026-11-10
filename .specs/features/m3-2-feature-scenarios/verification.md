# m3-2-feature-scenarios verification

**Verdict**: PASS
**Proofs**: `proofs.md` at f4b21f4
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/features/test_feature_scenarios.py` `test_scn_01_feature_scenario_immutability` | yes |
| C2 | `tests/unit/features/test_feature_scenarios.py` `test_scn_02_fixed_scenario_constraints` | yes |
| C3 | `tests/unit/features/test_feature_scenarios.py` `test_scn_03_dynamic_scenario_anti_leakage` | yes |
| C4 | `tests/unit/features/test_feature_scenarios.py` `test_scn_04_validate_scenarios_success` | yes |
| C5 | `tests/unit/features/test_feature_scenarios.py` `test_scn_05_validate_scenarios_rejections` | yes |
| C6 | `tests/unit/features/test_feature_scenarios.py` `test_scn_06_roundtrip_serialization` | yes |
| C7 | `tests/unit/features/test_scenarios_storage.py` `test_scn_07_save_and_load_scenarios` | yes |
| C8 | `tests/integration/features/test_scenarios_integration.py` `test_scn_08_end_to_end_scenarios_gate` | yes |

## Own examples

Five boundary, mutation isolation, protected column disjunction, and structural gate re-validation edge cases were independently probed at `HEAD`:

1. **Identifier slug validation and special characters**:
   - Punctuation, path separators, whitespace, and special characters (`scen.1`, `scen/1`, `scen@1`, `scen#1`, `scen:1`, `scen\n1`) were tested in `scenario_id`.
   - Verified that `_VALID_SLUG_PATTERN` rejects invalid characters with typed `ConfigurationError`, while valid slugs with uppercase, hyphens, and underscores (`SCEN-01_valid`) are accepted cleanly.

2. **Dict defensive copy and mutation isolation**:
   - An external dictionary `original_params = {'param1': 100}` was passed to `strategy_params` of a dynamic scenario and then mutated externally to `999`.
   - Verified that `scenario.strategy_params['param1']` remains `100` because `__post_init__` wraps an independent dictionary copy into `MappingProxyType`.

3. **Whitespace string elements in fixed features sequence**:
   - Tested instantiation of fixed scenario with `selected_features=('   ', 'f1')`.
   - Verified that whitespace-only feature names are detected and rejected with `ConfigurationError`.

4. **Protected columns disjunction (observation_id and time_col)**:
   - Evaluated fixed scenarios attempting to select `observation_id_col` (`obs_id_custom`) or `time_col` (`time_stamp`) defined in the schema.
   - Verified that `validate_scenarios` raises `ContractViolationError` with clear diagnostics identifying the protected column.

5. **Stage gate directory lookup and structural re-validation**:
   - Evaluated `verify_scenarios_gate` receiving an experiment root directory.
   - Verified that it correctly resolves `configuration/scenarios.json`, checks hash alignment against the view, and re-validates scenario structure (rejecting any catalog with features unregistered in the active sanitized view with `ContractViolationError`).

## Findings

None - all 8 checks formally prove their acceptance criteria, anti-leakage invariants are strictly guarded for dynamic scenarios, and stage gate validation ensures end-to-end cryptographic and structural integrity.
