# exploratory-visual-redesign Tasks

**Design**: `.specs/features/exploratory-visual-redesign/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-19 - user: "aprovado"  
**Build**: .venv/bin/python -c "import experimental_ml.features"  
**Run explr_unit**: .venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -v  
**Run explr_cli**: .venv/bin/pytest tests/unit/cli/test_exploratory_cli_visuals.py tests/integration/test_mvp_audit_invariants.py -v  
**Run explr_docs**: .venv/bin/pytest tests/unit/test_documentation_integrity.py -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Ranking único `summary()` | unit | 1 linha por feature por `mean(\|valor\|)`, métricas detalhadas, `UNDEFINED_NAN` separado | `tests/unit/features/test_exploratory_visualization.py` | `.venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -k "summary" -v` |
| PNGs legíveis + CSVs + MD + HTML print | unit | Fonte bitmap no PNG, 300 DPI, rejeição de SVG, CSVs, `@page`/print CSS | `tests/unit/features/test_exploratory_visualization.py` | `.venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -v` |
| CLI `features explore` & `quickrun` | unit / integration | Stdout sem duplicatas/hashes, CSVs + MD + HTML + PNGs, zero SVG, `scenarios.json` intocado | `tests/unit/cli/test_exploratory_cli_visuals.py` | `.venv/bin/pytest tests/unit/cli/test_exploratory_cli_visuals.py tests/integration/test_mvp_audit_invariants.py -v` |
| Documentação & Invariantes | unit | Links, API/CLI docs, `STATE.md` e `XCUT-02` | `tests/unit/test_documentation_integrity.py` | `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After T1–T3 | `.venv/bin/pytest tests/unit/features/test_exploratory_visualization.py tests/unit/cli/test_exploratory_cli_visuals.py -v` |
| Full | After T4 | `.venv/bin/pytest tests/ -q` |

---

## Execution Plan

```
T1 --> T2 --> T3 --> T4
```

---

## Task Breakdown

### T1: Implement per-feature `mean(|value|)` aggregation and `ExploratoryFeatureReport.summary()` in `features/types.py` [x]
**Depends on**: none  
**Files**: `src/experimental_ml/features/types.py`, `tests/unit/features/test_exploratory_visualization.py`  
**Done when**: `report.summary(top_n=15)` groups associations by `feature_name`, ranks by `mean(|value|)` descending, prints individual metric values per feature, and keeps `UNDEFINED_NAN` separate.  
**Tests**: Unit tests verifying unique-feature Top-N deduplication, `mean(|value|)` ordering, and `UNDEFINED_NAN` separation.  
**Gate**: `.venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -k "summary" -v`  

### T2: Implement labeled pure-NumPy PNG charts, CSV exporters, clean Markdown, and print/PDF-ready HTML in `features/visualization.py`
**Depends on**: T1  
**Files**: `src/experimental_ml/features/visualization.py`, `src/experimental_ml/features/__init__.py`, `tests/unit/features/test_exploratory_visualization.py`  
**Done when**: PNG bar chart & heatmap include crisp bitmap text labels/values/legends (`XCUT-02`), SVG is rejected, `render_exploratory_target_csv` & `render_exploratory_redundancy_csv` work, and `exploratory_features.{md,html}` has `@page`/`@media print` CSS and no giant inline matrix.  
**Tests**: Unit tests verifying labeled PNG pixel content & determinism, CSV formats, MD/HTML print CSS, and SVG rejection.  
**Gate**: `.venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -v`  

### T3: Update `cmd_features.py` to emit deduplicated summary, MD, print-ready HTML, CSVs, and PNGs (no SVG)
**Depends on**: T2  
**Files**: `src/experimental_ml/cli/cmd_features.py`, `tests/unit/cli/test_exploratory_cli_visuals.py`  
**Done when**: `expml features explore` and `expml quickrun` generate JSON, MD, HTML, 2 CSVs, and 2 PNGs (zero `.svg` files) while keeping `configuration/scenarios.json` untouched.  
**Tests**: CLI and `quickrun` tests in `tests/unit/cli/test_exploratory_cli_visuals.py` plus `tests/integration/test_mvp_audit_invariants.py`.  
**Gate**: `.venv/bin/pytest tests/unit/cli/test_exploratory_cli_visuals.py tests/integration/test_mvp_audit_invariants.py -v`  

### T4: Synchronize documentation, reference catalogs, engineering docs, and `.specs/STATE.md`
**Depends on**: T3  
**Files**: `docs/guia/02_tutorial_6_etapas.md`, `docs/guias_praticos/07_cenarios_features_estabilidade.md`, `docs/referencia/{api_python,cli_catalogo}.md`, `docs/engenharia_software/{ARQUITETURA_E_CONTRATOS,ESPECIFICACAO_REQUISITOS,ETAPA_ATUAL_ENGENHARIA}.md`, `.specs/STATE.md`  
**Done when**: All docs and `.specs/STATE.md` (`AD-026`) reflect the redesigned Stage 2 outputs (CSVs, labeled PNGs, print-ready HTML, unique Top-N) and pass `test_documentation_integrity.py` + full test suite.  
**Tests**: `tests/unit/test_documentation_integrity.py` and `.venv/bin/pytest tests/ -q`.  
**Gate**: `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v`  

---

## Checks

**C1** - `ExploratoryFeatureReport.summary()` aggregates by unique `feature_name` ranked by `mean(|value|)`, shows individual metrics, and keeps `UNDEFINED_NAN` separate (EXPLR-01).
  Proof: run explr_unit | test_exploratory_report_summary_ranking_and_nan PASSED

**C2** - `render_exploratory_report` generates clean Markdown and `@page`/`@media print` PDF-ready offline HTML without giant inline `N x N` matrices (EXPLR-02, EXPLR-05).
  Proof: run explr_unit | test_render_exploratory_report_md_and_html PASSED

**C3** - `render_exploratory_target_csv` and `render_exploratory_redundancy_csv` export valid deterministic CSVs matching the unique-feature ranking and full matrix (EXPLR-03).
  Proof: run explr_unit | test_exploratory_csv_exports PASSED

**C4** - Pure-NumPy PNG bar chart & heatmap render crisp labels/values/legends deterministically (`XCUT-02`) and reject SVG (EXPLR-04, EXPLR-06).
  Proof: run explr_unit | test_exploratory_png_charts_labeled_and_no_svg PASSED

**C5** - `expml features explore` and `expml quickrun` emit JSON, MD, HTML, 2 CSVs, and 2 PNGs with zero `.svg` files and `scenarios.json` untouched (EXPLR-02, EXPLR-06).
  Proof: run explr_cli | test_cli_features_explore_visual_outputs_and_stdout PASSED

**C6** - Documentation integrity and MVP invariants pass after synchronizing all docs (EXPLR-06).
  Proof: run explr_docs | test_markdown_links_and_anchors_valid PASSED

## Handoff

- **Next step**: Awaiting user approval of `tasks.md` before starting T1.
- **Dispatched:** none
