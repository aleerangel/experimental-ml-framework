# m7-2-figures-full-report proofs

**HEAD**: 08ba64e
**Tree**: clean
**Shell**: /bin/sh
**Result**: 8 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/reporting/test_reporting_figures.py::test_m72_01_build_figure_spec_excludes_nan_and_prov` | pass |
| C2 | `run unit / tests/unit/reporting/test_reporting_figures.py::test_m72_01_render_figure_svg_png_300dpi_pdf_determ` | pass |
| C3 | `run unit / tests/unit/reporting/test_reporting_figures.py::test_m72_01_unsupported_format_raises PASSED` | pass |
| C4 | `run unit / tests/unit/reporting/test_reporting_report.py::test_m72_02_three_sections_markdown_and_html PASSED` | pass |
| C5 | `run unit / tests/unit/reporting/test_reporting_report.py::test_m72_02_html_offline_parity_and_no_hashes PASSED` | pass |
| C6 | `run unit / tests/unit/reporting/test_reporting_report.py::test_m72_02_invalid_report_format_raises PASSED` | pass |
| C7 | `run unit / tests/integration/reporting/test_m72_integration.py::test_m72_end_to_end_figures_and_report PASSED` | pass |
| C8 | `run unit / tests/integration/reporting/test_m72_integration.py::test_m72_runtime_purity_xcut02 PASSED` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/reporting/test_reporting_report.py::test_m72_02_html_offline_parity_and_no_hashes PASSED [ 36%]
tests/unit/reporting/test_reporting_report.py::test_m72_02_invalid_report_format_raises PASSED [ 42%]
tests/unit/reporting/test_reporting_tables.py::test_m71_03_all_seven_families_supported PASSED [ 47%]
tests/unit/reporting/test_reporting_tables.py::test_m71_03_numeric_parity_and_missing_distinction PASSED [ 52%]
tests/unit/reporting/test_reporting_tables.py::test_m71_03_structural_hash_exclusion PASSED [ 57%]
tests/unit/reporting/test_reporting_tables.py::test_m71_03_renderers_csv_markdown_latex_booktabs PASSED [ 63%]
tests/unit/reporting/test_reporting_types.py::test_m71_01_enums_values PASSED [ 68%]
tests/unit/reporting/test_reporting_types.py::test_m71_01_frozen_immutability PASSED [ 73%]
tests/unit/reporting/test_reporting_types.py::test_m71_01_provenance_rejects_absolute_paths PASSED [ 78%]
tests/integration/reporting/test_m71_integration.py::test_m71_end_to_end_readonly_tables PASSED [ 84%]
tests/integration/reporting/test_m71_integration.py::test_m71_runtime_purity_xcut02 PASSED [ 89%]
tests/integration/reporting/test_m72_integration.py::test_m72_end_to_end_figures_and_report PASSED [ 94%]
tests/integration/reporting/test_m72_integration.py::test_m72_runtime_purity_xcut02 PASSED [100%]

============================== 19 passed in 0.75s ==============================
```
