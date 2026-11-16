# Verification Report: m6-4-statistics-persistence-cli

**Verdict**: PASS  
**Author**: coding-agent  
**Verifier**: independent-verifier-subagent  

## Checks

| Check | Requirement | Test / Proof | Holds |
| --- | --- | --- | --- |
| C1 | STAT-12, AC-M64-01-01 | `tests/unit/statistics/test_statistics_storage.py::test_m64_01_atomic_save_creates_all_files` | yes |
| C2 | STAT-12, AC-M64-01-02 | `tests/unit/statistics/test_statistics_storage.py::test_m64_01_no_overwrite_protection` | yes |
| C3 | STAT-12, AC-M64-01-03 | `tests/unit/statistics/test_statistics_storage.py::test_m64_01_roundtrip_fidelity_with_nonfinite` | yes |
| C4 | STAT-13, AC-M64-02-01 | `tests/unit/stages/test_stage_statistics_gate.py::test_m64_02_missing_or_corrupt_raises` | yes |
| C5 | STAT-13, AC-M64-02-02 | `tests/unit/stages/test_stage_statistics_gate.py::test_m64_02_partition_plan_mismatch_raises` | yes |
| C6 | STAT-13, AC-M64-02-03 | `tests/unit/stages/test_stage_statistics_gate.py::test_m64_02_valid_gate_returns_summary` | yes |
| C7 | STAT-14, AC-M64-03-01 | `tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_run_success` | yes |
| C8 | STAT-14, AC-M64-03-02 | `tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_status` | yes |
| C9 | STAT-14, AC-M64-03-03 | `tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_verify` | yes |
| C10 | STAT-14, AC-M64-03-04 | `tests/unit/cli/test_cli_stats.py::test_m64_03_cli_lazy_imports_purity` | yes |
| C11 | STAT-12 | `tests/integration/statistics/test_m64_integration.py::test_m64_cli_end_to_end_pipeline` | yes |
| C12 | XCUT-02 | `tests/integration/statistics/test_m64_integration.py::test_m64_runtime_purity_xcut02` | yes |

## Adversarial Probes Executed

1. **Storage roundtrip & overwrite protection**: Verified `save_statistics_artifacts` / `load_statistics_artifacts` roundtrip with `NaN`, `+Inf`, `-Inf`, `AggregatedTimingStats`, and `SelectionStabilityReport` (including non-finite `std_jaccard`, `mean_kuncheva`, `std_kuncheva`, `pairwise_kuncheva`), plus `ContractViolationError` on `force=False` (`PROBE 1 PASS`).
2. **Stage 5 gate integrity**: Verified `verify_statistics_gate` raises `DataIntegrityError` on missing files, corrupted JSON (`statistics_manifest.json`), and `partition_plan_id` mismatch between `statistics_manifest.json` and `descriptive_consolidation.json` (`PROBE 2 PASS`).
3. **CLI `--config` & error exit codes**: Verified `expml stats run --config` with custom `ComparisonSpec` JSON (`AGAINST_BASELINE`, `BENJAMINI_HOCHBERG`, `alpha=0.01`, `baseline_config`) exits `0` without raw hashes on stdout, and `expml stats verify` returns exit code `2` without `Traceback` on missing or corrupted artifacts (`PROBE 3 PASS`).

## Findings

None
