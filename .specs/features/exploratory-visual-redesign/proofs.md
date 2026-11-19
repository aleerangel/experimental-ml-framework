# exploratory-visual-redesign proofs

**HEAD**: 91b3608
**Tree**: clean
**Shell**: /bin/sh
**Result**: 7 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run explr_unit / test_exploratory_report_summary_ranking_and_nan PASSED` | pass |
| C2 | `run explr_unit / test_render_exploratory_report_md_and_html PASSED` | pass |
| C3 | `run explr_unit / test_exploratory_csv_exports PASSED` | pass |
| C4 | `run explr_unit / test_exploratory_png_charts_labeled_and_no_svg PASSED` | pass |
| C5 | `run explr_cli / test_cli_features_explore_visual_outputs_and_stdout PASSED` | pass |
| C6 | `run explr_docs / test_markdown_links_and_anchors_valid PASSED` | pass |
| Build | `.venv/bin/python -c "import experimental_ml.features"` | pass |

## Output

`Run explr_unit` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 4 items

tests/unit/features/test_exploratory_visualization.py::test_exploratory_report_summary_ranking_and_nan PASSED [ 25%]
tests/unit/features/test_exploratory_visualization.py::test_render_exploratory_report_md_and_html PASSED [ 50%]
tests/unit/features/test_exploratory_visualization.py::test_exploratory_csv_exports PASSED [ 75%]
tests/unit/features/test_exploratory_visualization.py::test_exploratory_png_charts_labeled_and_no_svg PASSED [100%]

============================== 4 passed in 0.13s ===============================
```

`Run explr_cli` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 5 items

tests/unit/cli/test_exploratory_cli_visuals.py::test_cli_features_explore_visual_outputs_and_stdout PASSED [ 20%]
tests/unit/cli/test_exploratory_cli_visuals.py::test_quickrun_generates_stage2_visuals_and_preserves_scenarios PASSED [ 40%]
tests/integration/test_mvp_audit_invariants.py::test_audit_xcut02_runtime_purity_ast PASSED [ 60%]
tests/integration/test_mvp_audit_invariants.py::test_audit_stage_gates_cli_and_domain_neutrality PASSED [ 80%]
tests/integration/test_mvp_audit_invariants.py::test_audit_report_zero_open_p0_p1 PASSED [100%]

============================== 5 passed in 1.21s ===============================
```

`Run explr_docs` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 4 items

tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid PASSED [ 25%]
tests/unit/test_documentation_integrity.py::test_python_snippets_ast_and_public_imports PASSED [ 50%]
tests/unit/test_documentation_integrity.py::test_cli_blocks_and_quickstart_smoke_execution PASSED [ 75%]
tests/unit/test_documentation_integrity.py::test_readme_lean_structure_and_pointers PASSED [100%]

============================== 4 passed in 0.34s ===============================
```
