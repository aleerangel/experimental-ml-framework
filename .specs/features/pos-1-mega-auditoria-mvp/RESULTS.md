# POS-1 Results — `pos-1-mega-auditoria-mvp` (`TA-POS.1`)

## Summary

- **Invariantes Transversais (`tests/integration/test_mvp_audit_invariants.py`)**: Pureza AST estática e dinâmica (`XCUT-02`: stdlib + `numpy` apenas), 7 portões de estágio (`verify_preparation_gate` a `verify_report_gate`), `CLI-10` (imports lazy) e neutralidade de domínio (`RNF02`).
- **Saneamento de Achados (`tests/integration/test_mvp_audit_regressions.py` & [AUDIT_REPORT.md](./AUDIT_REPORT.md))**:
  - **6 achados `P0` corrigidos** (isolamento de grupos/temporal em holdout, aplicação de `ModelSpec.parameters`, exclusão de `UNDEFINED_NAN` em `TOP_K_RELEVANCE`, `requires_probabilities`/`requires_kernel_matrix` no catálogo, precedência `ADR-005` + `compare_by_abs` em `mbe`, e semente determinística em `RANDOM_SEARCH`).
  - **16 achados `P1` e 6 achados `P2` corrigidos** (CLI-11 em `cmd_models.py`, round-trip `Finding` em `orchestration/codecs.py`, OOF em `development_ids`, métricas default em `cmd_run.py`, `export` in-place, re-exports em `stages/__init__.py`, Família B `selected_features`, imutabilidade `Finding`/`DatasetProfile`, e sincronização completa de `engenharia_software/*.md`, `README.md`, `REFERENCIAS_E_FUNDAMENTACAO.md` e `pyproject.toml`).

## Verification

- `check_proofs.py pos-1-mega-auditoria-mvp`: **3 pass, 0 fail** (`HEAD: 65cb86c`)
- `.venv/bin/pytest tests/ -q`: **591 passed in 17.12s**
- `verification.md`: **PASS** (`Open P0 Findings: 0`, `Open P1 Findings: 0`)
