# Verification: m7-4-cli-report-end-to-end

**Verdict**: PASS  
**Date**: 2026-11-16  
**Commit**: `197fc53`

## Checks

| Check | Criterion | Test | Holds |
| --- | --- | --- | --- |
| C1 | `expml report generate` writes `report.md` and/or `report.html` read-only with exit code `0` and JSON summary (REP-08, AC-M74-01-01) | `tests/unit/cli/test_cli_report.py::test_m74_01_cli_report_generate` | Yes |
| C2 | `expml report export` exports complete reproducibility package in `full_package` and `reduced_no_raw_data` modes with exit code `0` and JSON manifest summary (REP-08, AC-M74-01-02) | `tests/unit/cli/test_cli_report.py::test_m74_01_cli_report_export_modes` | Yes |
| C3 | `expml report generate` and `export` without `--force` return exit code `2` (`ContractViolationError`) without overwriting existing files (REP-08, AC-M74-01-03) | `tests/unit/cli/test_cli_report.py::test_m74_01_cli_force_protection` | Yes |
| C4 | `expml report verify` returns exit code `0` and `"status": "VERIFIED"` even after moving the package directory (REP-09, AC-M74-02-01) | `tests/unit/cli/test_cli_report.py::test_m74_02_cli_report_verify_portable` | Yes |
| C5 | `expml report verify` returns exit code `2` (`DataIntegrityError`) on 1-byte tampering, missing file, or non-relative path (REP-09, AC-M74-02-02) | `tests/unit/cli/test_cli_report.py::test_m74_02_cli_report_verify_tamper_fails` | Yes |
| C6 | Complete Stage 1 -> Stage 6 E2E workflow via CLI/API passes with `XCUT-02` purity, move portability, and 1-byte tamper detection (REP-09, AC-M74-02-03) | `tests/integration/reporting/test_m74_e2e.py::test_m74_e2e_stage1_to_stage6_cli` | Yes |

## Evidence

- `.venv/bin/pytest tests/unit/cli/test_cli_report.py tests/integration/reporting/test_m74_e2e.py -v`: `6 passed in 2.77s`.
- `python3 .agent/skills/tlc-spec-driven/scripts/check_proofs.py m7-4-cli-report-end-to-end`: `HEAD: 197fc53`, `Tree: clean`, `Result: 6 pass, 0 fail`.
- Inspected `src/experimental_ml/cli/cmd_report.py` (`handle_report_generate`, `handle_report_export`, `handle_report_verify`) and `src/experimental_ml/cli/main.py` (`report generate`, `report export`, `report verify` subparsers and dispatch): lazy imports (`CLI-10`), no raw hashes on stdout (`CLI-11`), `--force` / `force=False` protection (`STORE-05`), and standardized exit codes (`0` / `2`).

## Findings

None - all 6 checks (C1–C6) hold, both test suites and `check_proofs.py` pass without issues.
