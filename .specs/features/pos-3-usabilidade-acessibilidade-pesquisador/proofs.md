# pos-3-usabilidade-acessibilidade-pesquisador proofs

**HEAD**: c32004c
**Tree**: clean
**Shell**: /bin/sh
**Result**: 3 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/test_usability_cli_and_facade.py::test_cli_init_and_end_to_end_workflow PASSED` | pass |
| C2 | `run unit / tests/unit/test_usability_cli_and_facade.py::test_python_facade_run_experiment_end_to_end PASSED` | pass |
| C3 | `run unit / tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid PASSED` | pass |

## Output

`Run unit` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 6 items

tests/unit/test_usability_cli_and_facade.py::test_cli_init_and_end_to_end_workflow PASSED [ 16%]
tests/unit/test_usability_cli_and_facade.py::test_python_facade_run_experiment_end_to_end PASSED [ 33%]
tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid PASSED [ 50%]
tests/unit/test_documentation_integrity.py::test_python_snippets_ast_and_public_imports PASSED [ 66%]
tests/unit/test_documentation_integrity.py::test_cli_blocks_and_quickstart_smoke_execution PASSED [ 83%]
tests/unit/test_documentation_integrity.py::test_readme_lean_structure_and_pointers PASSED [100%]

============================== 6 passed in 0.57s ===============================
```
