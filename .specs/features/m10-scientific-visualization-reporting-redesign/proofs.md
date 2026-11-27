# m10-scientific-visualization-reporting-redesign proofs

**HEAD**: decf35b
**Tree**: dirty - docs/referencia/api_python.md
**Shell**: /bin/sh
**Result**: 5 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run m10_invariants / test_audit_xcut02_runtime_purity_ast PASSED` | pass |
| C2 | `run m10_unit / test_m10_figures_pareto_paired_parity_and_formats PASSED` | pass |
| C3 | `run m10_unit / test_m10_exploratory_charts_matplotlib_utf8 PASSED` | pass |
| C4 | `run m10_unit / test_m10_tables_pandas_prep_and_enriched_metadata PASSED` | pass |
| C5 | `run m10_e2e / test_m10_pipeline_e2e_ptbr_report_and_figures PASSED` | pass |

## Output

`Run m10_invariants` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/test_mvp_audit_invariants.py::test_audit_xcut02_runtime_purity_ast PASSED [ 33%]
tests/integration/test_mvp_audit_invariants.py::test_audit_stage_gates_cli_and_domain_neutrality PASSED [ 66%]
tests/integration/test_mvp_audit_invariants.py::test_audit_report_zero_open_p0_p1 PASSED [100%]

============================== 3 passed in 0.40s ===============================
```

`Run m10_unit` - exit 0

```
tests/unit/reporting/test_reporting_tables.py::test_m10_tables_pandas_prep_and_enriched_metadata PASSED [ 33%]
tests/unit/reporting/test_reporting_figures.py::test_m72_01_build_figure_spec_excludes_nan_and_provenance PASSED [ 38%]
tests/unit/reporting/test_reporting_figures.py::test_m72_01_render_figure_svg_png_300dpi_pdf_deterministic PASSED [ 44%]
tests/unit/reporting/test_reporting_figures.py::test_m72_01_unsupported_format_raises PASSED [ 50%]
tests/unit/reporting/test_reporting_figures.py::test_m10_figures_pareto_paired_parity_and_formats PASSED [ 55%]
tests/unit/reporting/test_reporting_report.py::test_m72_02_three_sections_markdown_and_html PASSED [ 61%]
tests/unit/reporting/test_reporting_report.py::test_m72_02_html_offline_parity_and_no_hashes PASSED [ 66%]
tests/unit/reporting/test_reporting_report.py::test_m72_02_invalid_report_format_raises PASSED [ 72%]
tests/unit/features/test_exploratory_visualization.py::test_exploratory_report_summary_ranking_and_nan PASSED [ 77%]
tests/unit/features/test_exploratory_visualization.py::test_render_exploratory_report_md_and_html PASSED [ 83%]
tests/unit/features/test_exploratory_visualization.py::test_exploratory_csv_exports PASSED [ 88%]
tests/unit/features/test_exploratory_visualization.py::test_exploratory_png_charts_labeled_and_no_svg PASSED [ 94%]
tests/unit/features/test_exploratory_visualization.py::test_m10_exploratory_charts_matplotlib_utf8 PASSED [100%]

============================== 18 passed in 3.05s ==============================
```

`Run m10_e2e` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 1 item

tests/integration/reporting/test_m10_reporting_e2e.py::test_m10_pipeline_e2e_ptbr_report_and_figures PASSED [100%]

============================== 1 passed in 1.93s ===============================
```
