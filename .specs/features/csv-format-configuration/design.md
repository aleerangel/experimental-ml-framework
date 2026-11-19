# Design: CSV Formatting Configuration (`csv-format-configuration`)

## 1. Architecture & Component Boundaries

The feature extends Stage 1 (`experimental_ml.data`), the Python facade (`experimental_ml.pipeline`), and the CLI (`experimental_ml.cli`) without breaking any existing M1–M7 contracts, `DatasetSchemaSpec.schema_hash` determinism, `XCUT-02` (Python stdlib + `numpy` only), or `CLI-10` (no `numpy`/`hashlib` imports at CLI parser startup).

1. **Contract (`src/experimental_ml/data/schema.py` & `data/__init__.py`):**
   - `CsvFormatSpec` (`frozen=True, slots=True`): `delimiter: str | None = None`, `decimal: str | None = "."`, `encoding: str = "utf-8-sig"`, `has_header: bool = True`, `column_names: tuple[str, ...] | None = None`, `quotechar: str = '"'`.
   - `validate_csv_format_spec(spec: CsvFormatSpec) -> CsvFormatSpec` normalizes `"auto"` to `None` for `decimal`, checks `decimal in {None, ".", ","}`, `delimiter in {None, ",", ";", "\t", "|", "whitespace"}`, rejects `decimal == ","` paired with `delimiter == ","`, validates `len(quotechar) == 1` (disjoint from `delimiter`/`decimal`), and checks `encoding == "auto"` or valid `codecs.lookup(encoding)`.
   - Kept separate from `DatasetSchemaSpec` so existing `schema_hash` values remain bit-for-bit identical.

2. **Parsing & Auto-Detection (`src/experimental_ml/data/parsing.py` & `loader.py`):**
   - `_tokenize_row(line, delimiter, quotechar='"')` passes `quotechar` to `csv.reader`.
   - `detect_decimal(sample_lines, *, delimiter, quotechar='"', has_header=True) -> str` inspects up to 100 non-header lines for comma-decimal vs dot-decimal numeric tokens; raises `DataIntegrityError` on mixed `.`/`,` decimals, returns `","` when comma-decimals appear under a non-comma delimiter, and returns `"."` otherwise.
   - `detect_delimiter(..., decimal=".", quotechar='"', has_header=True)` excludes `","` when `decimal == ","`, and when `decimal is None` uses comma-decimal token matching to break ties between `","` and non-comma delimiters (e.g., `1,5;2,3`).
   - `load_dataset` accepts `decimal`, `quotechar`, and `csv_format: CsvFormatSpec | None = None`, defaults `encoding` to `"utf-8-sig"` (backward-compatible with UTF-8, plus BOM handling), supports `encoding="auto"` (`utf-8-sig` → `cp1252` on `UnicodeDecodeError`), and normalizes `decimal=","` tokens before `float64` coercion in `_infer_and_cast_column`.

3. **Python Facade & CLI (`pipeline.py`, `cli/main.py`, `cli/cmd_data.py`, `cli/cmd_init.py`):**
   - `run_experiment` accepts `delimiter`, `decimal`, `encoding`, `has_header`, `column_names`, `quotechar`, and `csv_format`, forwarding them to `load_dataset`.
   - `main.py` registers `--delimiter`, `--decimal`, `--encoding`, `--no-header`, `--column-names`, and `--quotechar` on both `expml data profile` and `expml quickrun`.
   - `cmd_data.py` parses optional `"csv_format"` from `schema.json` and merges CLI flags on top (CLI flags win). `cmd_init.py` forwards CLI flags from `quickrun` to `handle_data_profile`.
