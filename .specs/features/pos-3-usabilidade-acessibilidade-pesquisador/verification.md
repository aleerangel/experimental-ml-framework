# Verification: pos-3-usabilidade-acessibilidade-pesquisador (`POS-3`)

**Verdict:** PASS

**HEAD:** `c32004c`

## Checks

| Check | Criterion | Test | Holds |
| --- | --- | --- | --- |
| C1 | `expml init` cria projeto válido e o pipeline CLI executa de ponta a ponta com `--rules` opcional, `--metrics` e `--experiment-dir` unificado (`USAB-01`, `AC-POS3-01-01..04`) | `tests/unit/test_usability_cli_and_facade.py::test_cli_init_and_end_to_end_workflow` | Yes |
| C2 | `experimental_ml.run_experiment(...)` executa Etapas 1–6 preservando `CLI-10` (PEP 562 lazy export em `src/experimental_ml/__init__.py`) e `XCUT-02` (`USAB-02`, `AC-POS3-02-01`, `AC-POS3-02-02`) | `tests/unit/test_usability_cli_and_facade.py::test_python_facade_run_experiment_end_to_end` | Yes |
| C3 | Documentação por 5 Jornadas (`docs/README.md`, `docs/guia/00_comecando_do_zero.md`, `docs/guia/03_interpretando_resultados.md`, `docs/referencia/cli_schemas_json.md`) passa na suíte de integridade documental (`USAB-03`, `AC-POS3-03-01`, `AC-POS3-03-02`) | `tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid` | Yes |

## Findings

None - `.venv/bin/pytest tests/unit/test_usability_cli_and_facade.py tests/unit/test_documentation_integrity.py tests/integration/test_mvp_audit_invariants.py -v` passed (`9 passed in 0.70s`, confirming `XCUT-02` AST purity, stage gates, and domain neutrality), `python3 .agent/skills/tlc-spec-driven/scripts/check_proofs.py pos-3-usabilidade-acessibilidade-pesquisador` passed (`3 pass, 0 fail` on `HEAD c32004c`, `Tree: clean`), and the full test suite `.venv/bin/pytest tests/ -q` passed (`598 passed in 17.75s`, 0 skips).
