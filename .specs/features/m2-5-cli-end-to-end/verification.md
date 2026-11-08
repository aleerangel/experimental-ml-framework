# m2-5-cli-end-to-end verification

**Verdict**: PASS
**Proofs**: `proofs.md` at 5b67ef6
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/cli/test_cmd_data.py` `test_cli_01_data_profile_success` | yes |
| C2 | `tests/unit/cli/test_cmd_data.py` `test_cli_02_data_sanitize_ready_plan` | yes |
| C3 | `tests/unit/cli/test_cmd_data.py` `test_cli_03_data_sanitize_incomplete_plan_rejected` | yes |
| C4 | `tests/unit/cli/test_cmd_partition.py` `test_cli_04_partition_build_success` | yes |
| C5 | `tests/unit/cli/test_cmd_partition.py` `test_cli_05_partition_verify_clean_and_tampered` | yes |
| C6 | `tests/unit/cli/test_cli_main.py` `test_cli_06_domain_error_handling_and_exit_code_2` | yes |
| C7 | `tests/unit/cli/test_cli_main.py` `test_cli_09_base_cli_compatibility_and_help` | yes |
| C8 | `tests/unit/cli/test_cli_main.py` `test_cli_10_architectural_pure_cli_no_numpy_no_hashlib` | yes |
| C9 | `tests/unit/cli/test_cli_main.py` `test_cli_11_no_hash_digests_in_output` | yes |
| C10 | `tests/integration/test_cli_end_to_end_integration.py` `test_cli_12_end_to_end_subprocess_acceptance_scenario` | yes |

## Findings

None - probed pure CLI layer with zero numpy/hashlib AST imports, zero 64-char hash digests in stdout/stderr, standardized exit codes (0, 1, 2) with traceback suppression on domain errors, and cross-run bit-identical byte determinism.
