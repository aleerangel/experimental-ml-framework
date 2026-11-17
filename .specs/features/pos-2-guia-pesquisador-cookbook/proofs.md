# pos-2-guia-pesquisador-cookbook proofs

**HEAD**: 995422c
**Tree**: clean
**Shell**: /bin/sh
**Result**: 4 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid PASSED` | pass |
| C2 | `run unit / tests/unit/test_documentation_integrity.py::test_python_snippets_ast_and_public_imports PASSED` | pass |
| C3 | `run unit / tests/unit/test_documentation_integrity.py::test_cli_blocks_and_quickstart_smoke_execution PASSED` | pass |
| C4 | `run unit / tests/unit/test_documentation_integrity.py::test_readme_lean_structure_and_pointers PASSED` | pass |

## Output

`Run unit` - exit 0

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

============================== 4 passed in 0.41s ===============================
```
