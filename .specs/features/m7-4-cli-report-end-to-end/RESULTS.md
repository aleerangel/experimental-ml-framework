# M7.4 Results — `m7-4-cli-report-end-to-end`

## Summary

- **CLI Subcommands (`src/experimental_ml/cli/cmd_report.py`, `main.py`)**:
  - `expml report generate`: geração somente-leitura de `report.md` e/ou `report.html` com seleção de audiência/famílias e proteção `--force` (`STORE-05`).
  - `expml report export`: exportação do pacote completo (`full_package` ou `reduced_no_raw_data`) via `build_reproducibility_package`.
  - `expml report verify`: verificação Stage 6 via `verify_report_gate` com saída JSON (`CLI-11`) e código `2` em adulteração de 1 byte ou caminho não relativo.
- **End-to-End Stage 1 → Stage 6 (`tests/integration/reporting/test_m74_e2e.py`)**:
  - Fluxo completo via CLI (`data profile` → `data sanitize` → `partition build` → `partition verify` → estatísticas Stage 5 → `report generate` → `report export` → movimentação de diretório → `report verify` → detecção de adulteração de 1 byte).

## Verification

- `check_proofs.py m7-4-cli-report-end-to-end`: **6 pass, 0 fail**
- `.venv/bin/pytest tests/ -q`: **581 passed in 20.70s**
- `verification.md`: **PASS**
