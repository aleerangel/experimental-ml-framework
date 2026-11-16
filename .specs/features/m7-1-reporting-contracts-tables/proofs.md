# m7-1-reporting-contracts-tables proofs

**HEAD**: 55ae9ab
**Tree**: clean
**Shell**: /bin/sh
**Result**: 11 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/reporting/test_reporting_types.py::test_m71_01_enums_values PASSED` | pass |
| C2 | `run unit / tests/unit/reporting/test_reporting_types.py::test_m71_01_frozen_immutability PASSED` | pass |
| C3 | `run unit / tests/unit/reporting/test_reporting_types.py::test_m71_01_provenance_rejects_absolute_paths PASSED` | pass |
| C4 | `run unit / tests/unit/reporting/test_reporting_loader.py::test_m71_02_readonly_loader_no_model_execution PASSE` | pass |
| C5 | `run unit / tests/unit/reporting/test_reporting_loader.py::test_m71_02_select_report_content_modes PASSED` | pass |
| C6 | `run unit / tests/unit/reporting/test_reporting_tables.py::test_m71_03_all_seven_families_supported PASSED` | pass |
| C7 | `run unit / tests/unit/reporting/test_reporting_tables.py::test_m71_03_numeric_parity_and_missing_distinction P` | pass |
| C8 | `run unit / tests/unit/reporting/test_reporting_tables.py::test_m71_03_structural_hash_exclusion PASSED` | pass |
| C9 | `run unit / tests/unit/reporting/test_reporting_tables.py::test_m71_03_renderers_csv_markdown_latex_booktabs PA` | pass |
| C10 | `run unit / tests/integration/reporting/test_m71_integration.py::test_m71_end_to_end_readonly_tables PASSED` | pass |
| C11 | `run unit / tests/integration/reporting/test_m71_integration.py::test_m71_runtime_purity_xcut02 PASSED` | pass |

## Output

`Run unit` - exit 0

```
collecting ... collected 11 items

tests/unit/reporting/test_reporting_loader.py::test_m71_02_readonly_loader_no_model_execution PASSED [  9%]
tests/unit/reporting/test_reporting_loader.py::test_m71_02_select_report_content_modes PASSED [ 18%]
tests/unit/reporting/test_reporting_tables.py::test_m71_03_all_seven_families_supported PASSED [ 27%]
tests/unit/reporting/test_reporting_tables.py::test_m71_03_numeric_parity_and_missing_distinction PASSED [ 36%]
tests/unit/reporting/test_reporting_tables.py::test_m71_03_structural_hash_exclusion PASSED [ 45%]
tests/unit/reporting/test_reporting_tables.py::test_m71_03_renderers_csv_markdown_latex_booktabs PASSED [ 54%]
tests/unit/reporting/test_reporting_types.py::test_m71_01_enums_values PASSED [ 63%]
tests/unit/reporting/test_reporting_types.py::test_m71_01_frozen_immutability PASSED [ 72%]
tests/unit/reporting/test_reporting_types.py::test_m71_01_provenance_rejects_absolute_paths PASSED [ 81%]
tests/integration/reporting/test_m71_integration.py::test_m71_end_to_end_readonly_tables PASSED [ 90%]
tests/integration/reporting/test_m71_integration.py::test_m71_runtime_purity_xcut02 PASSED [100%]

============================== 11 passed in 0.40s ==============================
```
