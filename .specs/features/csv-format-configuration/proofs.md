# csv-format-configuration proofs

**HEAD**: 9c92f00
**Tree**: clean
**Shell**: /bin/sh
**Result**: 7 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run csv_unit / test_csv_format_spec_validation PASSED` | pass |
| C2 | `run csv_unit / test_load_dataset_regional_csv_and_hash_equivalence PASSED` | pass |
| C3 | `run csv_unit / test_csv_auto_detection_and_mixed_decimal_rejection PASSED` | pass |
| C4 | `run csv_cli_facade / test_cli_csv_format_schema_and_flag_precedence PASSED` | pass |
| C5 | `run csv_cli_facade / test_quickrun_and_facade_regional_csv_end_to_end PASSED` | pass |
| C6 | `run invariants_docs / test_markdown_links_and_anchors_valid PASSED` | pass |
| Build | `.venv/bin/python -c "import experimental_ml"` | pass |

## Output

`Run csv_unit` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 4 items

tests/unit/data/test_csv_format.py::test_csv_format_spec_validation PASSED [ 25%]
tests/unit/data/test_csv_format.py::test_load_dataset_regional_csv_and_hash_equivalence PASSED [ 50%]
tests/unit/data/test_csv_format.py::test_csv_auto_detection_and_mixed_decimal_rejection PASSED [ 75%]
tests/unit/data/test_csv_format.py::test_csv_headerless_and_custom_column_names PASSED [100%]

============================== 4 passed in 0.12s ===============================
```

`Run csv_cli_facade` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 4 items

tests/unit/cli/test_csv_format_cli.py::test_cli_csv_format_schema_and_flag_precedence PASSED [ 25%]
tests/unit/cli/test_csv_format_cli.py::test_quickrun_and_facade_regional_csv_end_to_end PASSED [ 50%]
tests/unit/test_usability_cli_and_facade.py::test_cli_init_and_end_to_end_workflow PASSED [ 75%]
tests/unit/test_usability_cli_and_facade.py::test_python_facade_run_experiment_end_to_end PASSED [100%]

============================== 4 passed in 1.34s ===============================
```

`Run invariants_docs` - exit 0

```
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 7 items

tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid PASSED [ 14%]
tests/unit/test_documentation_integrity.py::test_python_snippets_ast_and_public_imports PASSED [ 28%]
tests/unit/test_documentation_integrity.py::test_cli_blocks_and_quickstart_smoke_execution PASSED [ 42%]
tests/unit/test_documentation_integrity.py::test_readme_lean_structure_and_pointers PASSED [ 57%]
tests/integration/test_mvp_audit_invariants.py::test_audit_xcut02_runtime_purity_ast PASSED [ 71%]
tests/integration/test_mvp_audit_invariants.py::test_audit_stage_gates_cli_and_domain_neutrality PASSED [ 85%]
tests/integration/test_mvp_audit_invariants.py::test_audit_report_zero_open_p0_p1 PASSED [100%]

============================== 7 passed in 0.48s ===============================
```
