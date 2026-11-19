# Acceptance Walkthrough: `csv-format-configuration`

## Prerequisites
- Virtualenv active with `experimental-ml-framework` installed (`.venv/bin/pytest`, `.venv/bin/expml`).

## Consumer Scenarios
1. **Python (`load_dataset` & `run_experiment`):**
   - Load a `;`-delimited, `,`-decimal, `latin-1`-encoded CSV with custom `quotechar` and verify `dataset_hash` matches an equivalent `.`-decimal UTF-8 CSV.
   - Auto-detect `delimiter=";"`, `decimal=","`, `encoding="cp1252"` using `delimiter=None, decimal=None, encoding="auto"`.
   - Confirm `ConfigurationError` on `delimiter=",", decimal=","` and `DataIntegrityError` on mixed `.`/`,` decimals.
2. **CLI (`expml data profile` & `expml quickrun`):**
   - Run `expml data profile` and `expml quickrun` using `"csv_format"` in `schema.json` and verify CLI flags (`--delimiter`, `--decimal`, `--encoding`, `--no-header`, `--column-names`, `--quotechar`) override `schema.json`.
3. **Documentation:**
   - Verify `README.md`, `docs/guia/`, `docs/referencia/`, and `docs/engenharia_software/` pass `test_documentation_integrity.py`.

## Approval Criteria
- All unit/integration checks in `tasks.md` pass (`check_proofs.py`), independent Verifier reports `PASS`, and full suite passes with 0 regressions.
