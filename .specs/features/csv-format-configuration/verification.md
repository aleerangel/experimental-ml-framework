# csv-format-configuration verification

**Verdict**: PASS
**Proofs**: `proofs.md`
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/data/test_csv_format.py` `test_csv_format_spec_validation` | yes |
| C2 | `tests/unit/data/test_csv_format.py` `test_load_dataset_regional_csv_and_hash_equivalence` | yes |
| C3 | `tests/unit/data/test_csv_format.py` `test_csv_auto_detection_and_mixed_decimal_rejection` | yes |
| C4 | `tests/unit/cli/test_csv_format_cli.py` `test_cli_csv_format_schema_and_flag_precedence` | yes |
| C5 | `tests/unit/cli/test_csv_format_cli.py` `test_quickrun_and_facade_regional_csv_end_to_end` | yes |
| C6 | `tests/unit/test_documentation_integrity.py` `test_markdown_links_and_anchors_valid` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Full test suite fails (`CA-CSV-05` regression): `experimental_ml.data.__all__` now exports 27 symbols (`CsvFormatSpec`, `validate_csv_format_spec`, `detect_decimal` added), breaking HARD-13 and XCUT-04 symbol-count assertions | `.venv/bin/pytest tests/ -q`: `2 failed, 602 passed in 17.95s` (`tests/integration/test_m1_foundation_integration.py:85` `assert 27 in (13, 17, 23, 24)` and `tests/integration/test_profiling_integration.py:174` `Expected 23 or 24 exported symbols in data, got 27`) | Update `test_hard_13_documentation_and_symbol_counts_aligned` (`tests/integration/test_m1_foundation_integration.py`) and `test_exported_symbols_count_xcut_04` (`tests/integration/test_profiling_integration.py`) to accept 27 exported symbols (including `CsvFormatSpec`, `validate_csv_format_spec`, `detect_decimal`) and re-run `.venv/bin/pytest tests/ -q` | closed (604 passed in 18.01s) |

## Full Suite Execution

Command: `.venv/bin/pytest tests/ -q`  
Result: `604 passed in 18.01s` (0 failures)

## Independent Boundary Probes

Ran two additional boundary checks at `9c92f00` (both passed):
- `cp1252`-specific byte `0x80` (`€`, invalid UTF-8) with `encoding="auto"`, `delimiter=None`, `decimal="auto"`, `has_header=False`, and `column_names=("x1", "moeda", "alvo")`.
- Custom `quotechar="'"` with `delimiter="whitespace"` and `decimal=","`.
