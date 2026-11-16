# m7-3-reproducibility-package-gate proofs

**HEAD**: 880da31
**Tree**: clean
**Shell**: /bin/sh
**Result**: 8 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/reporting/test_reporting_packaging.py::test_m73_01_manifest_and_mode PASSED` | pass |
| C2 | `run unit / tests/unit/reporting/test_reporting_packaging.py::test_m73_01_relative_paths_and_structure PASSED` | pass |
| C3 | `run unit / tests/unit/reporting/test_reporting_packaging.py::test_m73_01_reduced_mode_excludes_raw_data PASSED` | pass |
| C4 | `run unit / tests/unit/reporting/test_reporting_packaging.py::test_m73_01_force_false_protects_overwrite PASSED` | pass |
| C5 | `run unit / tests/unit/stages/test_stage_report_gate.py::test_m73_02_valid_and_portable_after_move PASSED` | pass |
| C6 | `run unit / tests/unit/stages/test_stage_report_gate.py::test_m73_02_tampering_or_missing_raises PASSED` | pass |
| C7 | `run unit / tests/unit/stages/test_stage_report_gate.py::test_m73_02_absolute_or_traversal_rejected PASSED` | pass |
| C8 | `run unit / tests/integration/reporting/test_m73_integration.py::test_m73_end_to_end_packaging_and_gate PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/reporting/test_reporting_tables.py::test_m71_03_structural_hash_exclusion PASSED [ 55%]
tests/unit/reporting/test_reporting_tables.py::test_m71_03_renderers_csv_markdown_latex_booktabs PASSED [ 59%]
tests/unit/reporting/test_reporting_types.py::test_m71_01_enums_values PASSED [ 62%]
tests/unit/reporting/test_reporting_types.py::test_m71_01_frozen_immutability PASSED [ 66%]
tests/unit/reporting/test_reporting_types.py::test_m71_01_provenance_rejects_absolute_paths PASSED [ 70%]
tests/unit/stages/test_stage_report_gate.py::test_m73_02_valid_and_portable_after_move PASSED [ 74%]
tests/unit/stages/test_stage_report_gate.py::test_m73_02_tampering_or_missing_raises PASSED [ 77%]
tests/unit/stages/test_stage_report_gate.py::test_m73_02_absolute_or_traversal_rejected PASSED [ 81%]
tests/integration/reporting/test_m71_integration.py::test_m71_end_to_end_readonly_tables PASSED [ 85%]
tests/integration/reporting/test_m71_integration.py::test_m71_runtime_purity_xcut02 PASSED [ 88%]
tests/integration/reporting/test_m72_integration.py::test_m72_end_to_end_figures_and_report PASSED [ 92%]
tests/integration/reporting/test_m72_integration.py::test_m72_runtime_purity_xcut02 PASSED [ 96%]
tests/integration/reporting/test_m73_integration.py::test_m73_end_to_end_packaging_and_gate PASSED [100%]

============================== 27 passed in 1.59s ==============================
```
