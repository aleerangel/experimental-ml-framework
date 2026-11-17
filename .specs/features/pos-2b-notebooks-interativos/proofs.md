# pos-2b-notebooks-interativos proofs

**HEAD**: 03f657f
**Tree**: clean
**Shell**: /bin/sh
**Result**: 2 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/test_notebooks_execution.py::test_all_notebooks_valid_and_executable PASSED` | pass |
| C2 | `run unit / tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid PASSED` | pass |

## Output

`Run unit` - exit 0

```
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 5 items

tests/unit/test_notebooks_execution.py::test_all_notebooks_valid_and_executable PASSED [ 20%]
tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid PASSED [ 40%]
tests/unit/test_documentation_integrity.py::test_python_snippets_ast_and_public_imports PASSED [ 60%]
tests/unit/test_documentation_integrity.py::test_cli_blocks_and_quickstart_smoke_execution PASSED [ 80%]
tests/unit/test_documentation_integrity.py::test_readme_lean_structure_and_pointers PASSED [100%]

============================== 5 passed in 0.37s ===============================
```
