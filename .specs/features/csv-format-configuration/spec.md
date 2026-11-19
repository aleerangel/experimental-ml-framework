# Specification: CSV Formatting Configuration (`csv-format-configuration`)

**Status**: Approved  
**Approved**: 2026-11-19 - user: "aprovado"  
**Scope**: Large (data parsing/ingestion, Python facade, CLI, JSON schema, and documentation)  
**Depends on**: M1.4 (`m1-4-datasets-schemas`), M2.5 (`m2-5-cli-end-to-end`), Pós-3 (`pos-3-usabilidade-acessibilidade-pesquisador`)

## Problem Statement

Researchers frequently work with tabular CSV/TXT files exported with Brazilian or European regional conventions (e.g., `;` delimiter with `,` decimal separator, `latin-1`/`cp1252` encoding, custom `quotechar`, or headerless files requiring explicit `column_names`). While `load_dataset` already supports `delimiter`, `has_header`, `column_names`, and `encoding`, it lacks `decimal` and `quotechar` configuration, and neither the CLI (`expml data profile`, `expml quickrun`), `schema.json`, nor the high-level Python facade `run_experiment` expose CSV formatting options.

## Out of Scope

- Custom `na_values` lists beyond the framework's standard missing value tokens.
- `comment` lines or `skip_rows` configuration.
- Thousands separators (must not be silently stripped).
- Multi-character delimiters (other than `"whitespace"`) or multi-character `decimal`/`quotechar`.

## Assumptions & Open Questions

**Open questions:** none — todas as decisões de escopo e comportamento foram respondidas pelo usuário em 2026-11-19 (`A1`, `A2`, `A3`).

| Decision / Assumption | Chosen Default | Rationale |
| :--- | :--- | :--- |
| Configurable CSV options | `delimiter` (`None` for auto), `decimal` (`"."`, `","`, or `None`/`"auto"`), `encoding` (`"utf-8-sig"`, explicit codec, or `"auto"`), `has_header`, `column_names`, `quotechar` | Covers regional tabular exports with safe auto-detection while preserving strict RFC 4180 parsing (`A1`, user auto-detection request). |
| Auto-detection of `decimal` & `encoding` | When `decimal` is `None`/`"auto"`: detect `","` if comma-decimal numeric tokens appear without dot-decimals under a non-comma delimiter (resolving delimiter tie-breaks in favor of non-comma delimiters); default to `"."` when unambiguous; raise `DataIntegrityError` on mixed `.`/`,` decimals. When `encoding="auto"`: try `utf-8-sig`, then `cp1252` on `UnicodeDecodeError`. | Eliminates manual config for standard Brazilian/Excel CSVs while refusing silent corruption on truly ambiguous files. |
| Configuration surfaces | Python (`load_dataset`, `run_experiment`), CLI (`expml data profile`, `expml quickrun`), and optional `"csv_format"` in `schema.json` (CLI flags override `schema.json`) | Full parity across basic and granular workflows (`A2`). |
| Ambiguity handling (`decimal=","`) | Reject `decimal=","` paired with `delimiter=","` with `ConfigurationError`; require explicit/unambiguous delimiter; validate `decimal in {".", ","}` | Prevents silent column splitting corruption (`A3`). |
| Runtime purity (`XCUT-02`) | Python stdlib (`csv`, `codecs`) + `numpy` only | Preserves project invariant without external CSV dependencies. |
| CLI runtime purity (`CLI-10`) | No `numpy`/`hashlib` imports at CLI parser startup | Preserves fast CLI startup invariant. |

## User Stories

### US-CSV-01 (Priority: P1) — Leitura de CSVs Regionais em Python (`load_dataset` e `run_experiment`)
As a researcher, I want to configure `delimiter`, `decimal`, `encoding`, `has_header`, `column_names`, and `quotechar` in `load_dataset` and `run_experiment`, so that CSVs exported with `;` and `,` decimal or `latin-1` work without manual pre-conversion.

### US-CSV-02 (Priority: P1) — Configuração via CLI e `schema.json`
As a CLI user, I want to configure CSV formatting either inside `schema.json` (`"csv_format"`) or via `expml data profile` / `expml quickrun` flags (with CLI flags taking precedence), so that my experiment configuration is reproducible and flexible.

### US-CSV-03 (Priority: P2) — Documentação e Referências Atualizadas
As a user or maintainer, I want all guides, reference catalogs, and engineering docs to reflect the CSV formatting options, so that no documentation lags behind the implementation.

## Requirements (EARS Notation)

- **CSV-01 (`CsvFormatSpec` & Validation):** WHEN a caller constructs `CsvFormatSpec` (or passes CSV format parameters to `load_dataset` / `run_experiment`), THE SYSTEM SHALL validate that `decimal` is `None`, `"auto"`, `"."`, or `","`, `quotechar` is a single-character string (default `'"'`), `encoding` is `"auto"` or a non-empty valid Python codec name (default `"utf-8-sig"`), and `delimiter` (if provided) is one of `",", ";", "\t", "|", "whitespace"`, raising `ConfigurationError` if `decimal == ","` is paired with `delimiter == ","` or any parameter is invalid.
- **CSV-02 (Decimal & Quotechar Parsing in `parsing.py` & `loader.py`):** WHEN `parse_tabular_text` or `load_dataset` parses numeric cells with `decimal=","` and a non-comma delimiter (or custom `quotechar`), THE SYSTEM SHALL convert valid comma-decimal numeric tokens (e.g., `"-12,50"`, `"1,5e-3"`) into IEEE 754 `float64` values, reject malformed tokens with `DataIntegrityError`, and compute `dataset_hash` deterministically over the resulting typed values (independent of regional text representation).
- **CSV-03 (Automatic Delimiter, Decimal & Encoding Detection):** WHEN `load_dataset` is called with `decimal=None`/`"auto"`, THE SYSTEM SHALL inspect sampled non-header cells to detect `decimal=","` vs `"."` (breaking ties in `detect_delimiter` in favor of a non-comma delimiter when comma-decimal numeric tokens are present, and excluding `","` when `decimal=","` is explicit), raising `DataIntegrityError` if mixed decimal conventions appear in the sample; AND WHEN `encoding="auto"`, THE SYSTEM SHALL decode using `"utf-8-sig"` and fall back to `"cp1252"` on `UnicodeDecodeError`.
- **CSV-04 (Optional `"csv_format"` in `schema.json` & Precedence):** WHEN `schema.json` includes an optional `"csv_format"` object (`delimiter`, `decimal`, `encoding`, `has_header`, `column_names`, `quotechar`), THE SYSTEM SHALL parse and validate it in `expml data profile` and `expml quickrun`, AND WHEN corresponding CLI flags are also provided, THE SYSTEM SHALL override the `schema.json` values with the CLI flags.
- **CSV-05 (CLI Flags & Python Facade Parity):** WHEN a user invokes `expml data profile` or `expml quickrun` with `--delimiter`, `--decimal`, `--encoding`, `--no-header` / `--has-header`, `--column-names`, or `--quotechar`, OR calls `run_experiment(..., delimiter=..., decimal=..., encoding=..., has_header=..., column_names=..., quotechar=...)`, THE SYSTEM SHALL pass the resolved `CsvFormatSpec` cleanly through Stage 1 ingestion and preserve all downstream M1–M7 stage gates and contracts.
- **CSV-06 (Documentation & Reference Synchronization):** WHEN the CSV formatting feature is implemented, THE SYSTEM SHALL update `README.md`, `docs/guia/00_comecando_do_zero.md`, `docs/guia/02_tutorial_6_etapas.md`, `docs/referencia/api_python.md`, `docs/referencia/cli_catalogo.md`, `docs/referencia/cli_schemas_json.md`, and `docs/engenharia_software/{ARQUITETURA_E_CONTRATOS,ESPECIFICACAO_REQUISITOS,ETAPA_ATUAL_ENGENHARIA}.md`, passing all automated documentation integrity checks.

## Acceptance Criteria

- `CA-CSV-01`: `load_dataset` parses `;`-delimited, `,`-decimal, `latin-1`-encoded CSVs with custom `quotechar` into exact `float64` values matching an equivalent `.`-decimal UTF-8 CSV (`dataset_hash` invariant).
- `CA-CSV-02`: `load_dataset(..., delimiter=",", decimal=",")` raises `ConfigurationError`; `load_dataset(..., delimiter=None, decimal=None, encoding="auto")` auto-detects `;` + `,` decimal + `cp1252`/`utf-8-sig` on regional CSVs and raises `DataIntegrityError` on mixed `.`/`,` decimals.
- `CA-CSV-03`: `expml data profile` and `expml quickrun` accept both `"csv_format"` in `schema.json` and CLI flags (`--delimiter`, `--decimal`, `--encoding`, `--no-header`, `--column-names`, `--quotechar`), with CLI flags taking precedence.
- `CA-CSV-04`: `run_experiment` accepts `delimiter`, `decimal`, `encoding`, `has_header`, `column_names`, and `quotechar` and completes Stages 1–6 on a regional CSV.
- `CA-CSV-05`: All existing tests (`598`) plus new CSV formatting unit/integration tests and `test_documentation_integrity.py` pass without regressions or `XCUT-02`/`CLI-10` violations.

## Requirement Traceability

| Requirement | User Story | Acceptance Criterion | Status |
| :--- | :--- | :--- | :--- |
| CSV-01 | `US-CSV-01` | `CA-CSV-01`, `CA-CSV-02` | pending |
| CSV-02 | `US-CSV-01` | `CA-CSV-01` | pending |
| CSV-03 | `US-CSV-01` | `CA-CSV-02` | pending |
| CSV-04 | `US-CSV-02` | `CA-CSV-03` | pending |
| CSV-05 | `US-CSV-01`, `US-CSV-02` | `CA-CSV-03`, `CA-CSV-04` | pending |
| CSV-06 | `US-CSV-03` | `CA-CSV-05` | pending |
