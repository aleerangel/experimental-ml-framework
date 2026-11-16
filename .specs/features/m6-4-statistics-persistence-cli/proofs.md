# m6-4-statistics-persistence-cli proofs

**HEAD**: 7460578
**Tree**: clean
**Shell**: /bin/sh
**Result**: 12 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/statistics/test_statistics_storage.py::test_m64_01_atomic_save_creates_all_files PASSED` | pass |
| C2 | `run unit / tests/unit/statistics/test_statistics_storage.py::test_m64_01_no_overwrite_protection PASSED` | pass |
| C3 | `run unit / tests/unit/statistics/test_statistics_storage.py::test_m64_01_roundtrip_fidelity_with_nonfinite PAS` | pass |
| C4 | `run unit / tests/unit/stages/test_stage_statistics_gate.py::test_m64_02_missing_or_corrupt_raises PASSED` | pass |
| C5 | `run unit / tests/unit/stages/test_stage_statistics_gate.py::test_m64_02_partition_plan_mismatch_raises PASSED` | pass |
| C6 | `run unit / tests/unit/stages/test_stage_statistics_gate.py::test_m64_02_valid_gate_returns_summary PASSED` | pass |
| C7 | `run unit / tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_run_success PASSED` | pass |
| C8 | `run unit / tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_status PASSED` | pass |
| C9 | `run unit / tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_verify PASSED` | pass |
| C10 | `run unit / tests/unit/cli/test_cli_stats.py::test_m64_03_cli_lazy_imports_purity PASSED` | pass |
| C11 | `run unit / tests/integration/statistics/test_m64_integration.py::test_m64_cli_end_to_end_pipeline PASSED` | pass |
| C12 | `run unit / tests/integration/statistics/test_m64_integration.py::test_m64_runtime_purity_xcut02 PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_run_success PASSED [ 84%]
tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_status PASSED    [ 85%]
tests/unit/cli/test_cli_stats.py::test_m64_03_cli_stats_verify PASSED    [ 87%]
tests/unit/cli/test_cli_stats.py::test_m64_03_cli_lazy_imports_purity PASSED [ 88%]
tests/integration/statistics/test_m62_integration.py::test_m62_end_to_end_pipeline PASSED [ 89%]
tests/integration/statistics/test_m62_integration.py::test_m62_runtime_purity_xcut02 PASSED [ 90%]
tests/integration/statistics/test_m63_integration.py::test_m63_end_to_end_pipeline PASSED [ 92%]
tests/integration/statistics/test_m63_integration.py::test_m63_runtime_purity_xcut02 PASSED [ 93%]
tests/integration/statistics/test_m64_integration.py::test_m64_cli_end_to_end_pipeline PASSED [ 94%]
tests/integration/statistics/test_m64_integration.py::test_m64_runtime_purity_xcut02 PASSED [ 96%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_public_api_exports PASSED [ 97%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_end_to_end_lifecycle PASSED [ 98%]
tests/integration/statistics/test_statistics_integration.py::test_statistics_runtime_purity_xcut02 PASSED [100%]

============================== 77 passed in 1.58s ==============================
```
