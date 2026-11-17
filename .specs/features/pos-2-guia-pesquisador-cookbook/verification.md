# Verification: pos-2-guia-pesquisador-cookbook (`TA-POS.2`)

**Verdict:** PASS

**HEAD:** `995422c`

## Checks

| Check | Criterion | Test | Holds |
| --- | --- | --- | --- |
| C1 | Estrutura modular em português (`docs/README.md`, `docs/guia/`, `docs/cookbook/`, `docs/referencia/`) e links relativos válidos sem referências quebradas | `tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid` | Yes |
| C2 | Sintaxe AST válida em blocos Python, resolução estática de imports públicos nos 11 pacotes e conformidade léxica dos comandos CLI `expml` | `tests/unit/test_documentation_integrity.py::test_python_snippets_ast_and_public_imports` | Yes |
| C3 | Validação léxica de CLI `expml` em blocos shell e execução ponta a ponta (smoke test) do exemplo executável do Início Rápido | `tests/unit/test_documentation_integrity.py::test_cli_blocks_and_quickstart_smoke_execution` | Yes |
| C4 | `README.md` enxuto e equilibrado (sem exemplos extensos de código de implementação ou detalhamento de engenharia/requisitos), apontando diretamente para `docs/`, `engenharia_software/` e `REFERENCIAS_E_FUNDAMENTACAO.md` | `tests/unit/test_documentation_integrity.py::test_readme_lean_structure_and_pointers` | Yes |

## Findings

None - all 4 tests in `tests/unit/test_documentation_integrity.py` passed (`4 passed in 0.21s`), all 3 tests in `tests/integration/test_mvp_audit_invariants.py` passed (`3 passed in 0.47s`, confirming `XCUT-02` runtime purity), `check_proofs.py pos-2-guia-pesquisador-cookbook` passed (`4 pass, 0 fail` on `HEAD 995422c`, `Tree: clean`), all last 6 git commits adhere to Portuguese conventional messages, and `GEMINI.md` is not cited in any delivered documentation or commit messages.
