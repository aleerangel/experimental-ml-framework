# csv-format-configuration Tasks

**Design**: `.specs/features/csv-format-configuration/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-19 - user: "aprovado"  
**Build**: .venv/bin/python -c "import experimental_ml"  
**Run csv_unit**: .venv/bin/pytest tests/unit/data/test_csv_format.py -v  
**Run csv_cli_facade**: .venv/bin/pytest tests/unit/cli/test_csv_format_cli.py tests/unit/test_usability_cli_and_facade.py -v  
**Run invariants_docs**: .venv/bin/pytest tests/unit/test_documentation_integrity.py tests/integration/test_mvp_audit_invariants.py -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Contrato `CsvFormatSpec` | unit | Validação de `decimal`, `delimiter`, `quotechar`, `encoding`, `"auto"` e rejeição de conflitos | `tests/unit/data/test_csv_format.py` | `.venv/bin/pytest tests/unit/data/test_csv_format.py -k "spec" -v` |
| Parsing & Detecção | unit | Leitura `;` + `,` decimal + `latin-1`/`cp1252` + `quotechar`, `dataset_hash` equivalente e detecção automática | `tests/unit/data/test_csv_format.py` | `.venv/bin/pytest tests/unit/data/test_csv_format.py tests/unit/test_data_schemas.py -v` |
| CLI & Fachada Python | unit / integration | `schema.json` `"csv_format"`, flags CLI com precedência, `quickrun` e `run_experiment` | `tests/unit/cli/test_csv_format_cli.py` | `.venv/bin/pytest tests/unit/cli/test_csv_format_cli.py tests/unit/test_usability_cli_and_facade.py -v` |
| Documentação & Invariantes | unit / integration | Links, snippets Python, CLI e `XCUT-02` / `CLI-10` | `tests/unit/test_documentation_integrity.py` | `.venv/bin/pytest tests/unit/test_documentation_integrity.py tests/integration/test_mvp_audit_invariants.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After T1–T3 | `.venv/bin/pytest tests/unit/data/test_csv_format.py tests/unit/cli/test_csv_format_cli.py -v` |
| Full | After T4 | `.venv/bin/pytest tests/ -q` |

---

## Execution Plan

```
T1 --> T2 --> T3 --> T4
```

---

## Task Breakdown

### T1: Add `CsvFormatSpec` and validation contract in `data/schema.py` and `data/__init__.py` [x]
**Depends on**: none  
**Files**: `src/experimental_ml/data/schema.py`, `src/experimental_ml/data/__init__.py`, `tests/unit/data/test_csv_format.py`  
**Done when**: `CsvFormatSpec` and `validate_csv_format_spec` are implemented and exported, validating defaults, `"auto"`, and rejecting `decimal=","` + `delimiter=","`.  
**Tests**: Unit tests verifying `CsvFormatSpec` defaults, `"auto"` normalization, invalid `decimal`/`delimiter`/`quotechar`/`encoding`, and `ConfigurationError` on `decimal=","` + `delimiter=","`.  
**Gate**: `.venv/bin/pytest tests/unit/data/test_csv_format.py -k "spec" -v`  

### T2: Implement `quotechar`, `decimal`, `detect_decimal`, tie-breaking `detect_delimiter`, and `encoding="auto"` in `parsing.py` and `loader.py` [x]
**Depends on**: T1  
**Files**: `src/experimental_ml/data/parsing.py`, `src/experimental_ml/data/loader.py`, `src/experimental_ml/data/__init__.py`, `tests/unit/data/test_csv_format.py`  
**Done when**: `load_dataset`, `parse_tabular_text`, `detect_delimiter`, and `detect_decimal` handle regional CSVs, auto-detection, and mixed-decimal rejection cleanly.  
**Tests**: Unit tests covering `;` + `,` decimal + `latin-1`/`cp1252` + custom `quotechar`, `dataset_hash` invariance, auto-detection tie-break (`1,5;2,3`), mixed-decimal rejection (`DataIntegrityError`), and `tests/unit/test_data_schemas.py`.  
**Gate**: `.venv/bin/pytest tests/unit/data/test_csv_format.py tests/unit/test_data_schemas.py -v`  

### T3: Expose CSV formatting in `pipeline.py`, `cli/main.py`, `cli/cmd_data.py`, and `cli/cmd_init.py`
**Depends on**: T2  
**Files**: `src/experimental_ml/pipeline.py`, `src/experimental_ml/cli/main.py`, `src/experimental_ml/cli/cmd_data.py`, `src/experimental_ml/cli/cmd_init.py`, `tests/unit/cli/test_csv_format_cli.py`, `tests/unit/test_usability_cli_and_facade.py`  
**Done when**: `run_experiment`, `expml data profile`, `expml quickrun`, and `schema.json` `"csv_format"` support all CSV formatting options with CLI flags taking precedence.  
**Tests**: CLI and facade tests verifying `"csv_format"` in `schema.json`, CLI flag overrides, `quickrun`, and `run_experiment` end-to-end on regional CSVs, plus `tests/integration/test_mvp_audit_invariants.py`.  
**Gate**: `.venv/bin/pytest tests/unit/cli/test_csv_format_cli.py tests/unit/test_usability_cli_and_facade.py tests/integration/test_mvp_audit_invariants.py -v`  

### T4: Synchronize documentation, reference catalogs, engineering docs, and `.specs/STATE.md`
**Depends on**: T3  
**Files**: `README.md`, `docs/guia/00_comecando_do_zero.md`, `docs/guia/02_tutorial_6_etapas.md`, `docs/referencia/api_python.md`, `docs/referencia/cli_catalogo.md`, `docs/referencia/cli_schemas_json.md`, `docs/engenharia_software/{ARQUITETURA_E_CONTRATOS,ESPECIFICACAO_REQUISITOS,ETAPA_ATUAL_ENGENHARIA}.md`, `.specs/STATE.md`  
**Done when**: All user guides, reference docs, engineering specs, and `.specs/STATE.md` (`AD-024`) document CSV formatting options and pass automated integrity checks.  
**Tests**: `tests/unit/test_documentation_integrity.py` and full test suite `.venv/bin/pytest tests/ -q`.  
**Gate**: `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v`  

---

## Checks

**C1** - `CsvFormatSpec` validates `decimal`, `delimiter`, `quotechar`, `encoding`, and rejects `decimal=","` + `delimiter=","` with `ConfigurationError` (CSV-01).
  Proof: run csv_unit | test_csv_format_spec_validation PASSED

**C2** - `load_dataset` parses `;`-delimited `,`-decimal `latin-1` CSVs with custom `quotechar` to identical `float64` values and `dataset_hash` (CSV-02).
  Proof: run csv_unit | test_load_dataset_regional_csv_and_hash_equivalence PASSED

**C3** - Auto-detection resolves `;` + `,` decimal tie-breaks (`1,5;2,3`), decodes `cp1252` via `encoding="auto"`, and raises `DataIntegrityError` on mixed decimals (CSV-03).
  Proof: run csv_unit | test_csv_auto_detection_and_mixed_decimal_rejection PASSED

**C4** - `schema.json` `"csv_format"` is parsed by CLI and overridden by explicit CLI flags (CSV-04).
  Proof: run csv_cli_facade | test_cli_csv_format_schema_and_flag_precedence PASSED

**C5** - `expml quickrun` and `run_experiment` execute Stages 1–6 end-to-end on regional CSVs without `XCUT-02` or `CLI-10` violations (CSV-05).
  Proof: run csv_cli_facade | test_quickrun_and_facade_regional_csv_end_to_end PASSED

**C6** - Documentation integrity and MVP invariants pass after synchronizing all docs (CSV-06).
  Proof: run invariants_docs | test_markdown_links_and_anchors_valid PASSED

---

## Handoff

- **Next step**: Awaiting user approval of `tasks.md` before starting T1.
- **Dispatched:** none
