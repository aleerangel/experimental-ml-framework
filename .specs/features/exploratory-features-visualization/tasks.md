# exploratory-features-visualization Tasks

**Design**: `.specs/features/exploratory-features-visualization/design.md`  
**Status**: Completed  
**Approved**: 2026-11-19 - user: "aprovado"  
**Build**: .venv/bin/python -c "import experimental_ml.features"  
**Run expl_unit**: .venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -v  
**Run expl_cli**: .venv/bin/pytest tests/unit/cli/test_exploratory_cli_visuals.py tests/integration/test_mvp_audit_invariants.py -v  
**Run expl_docs**: .venv/bin/pytest tests/unit/test_documentation_integrity.py -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| `ExploratoryFeatureReport.summary()` | unit | Ranking por `\|valor\|`, `UNDEFINED_NAN` separado, pares redundantes e avisos | `tests/unit/features/test_exploratory_visualization.py` | `.venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -k "summary" -v` |
| Relatórios MD/HTML e Figuras SVG/PNG | unit | HTML offline, tabelas completas, guia de cenários, bytes SVG/PNG determinísticos (`XCUT-02`) | `tests/unit/features/test_exploratory_visualization.py` | `.venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -v` |
| CLI `features explore` & `quickrun` | unit / integration | Stdout legível sem hashes (`CLI-11`), geração de `.md`/`.html`/`.svg`/`.png` e `scenarios.json` intocado | `tests/unit/cli/test_exploratory_cli_visuals.py` | `.venv/bin/pytest tests/unit/cli/test_exploratory_cli_visuals.py tests/integration/test_mvp_audit_invariants.py -v` |
| Documentação & Invariantes | unit | Links, snippets Python, CLI e contagem de símbolos | `tests/unit/test_documentation_integrity.py` | `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v` |

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

### T1: Add `ExploratoryFeatureReport.summary(top_n=15)` in `features/types.py` [x]
**Depends on**: none  
**Files**: `src/experimental_ml/features/types.py`, `tests/unit/features/test_exploratory_visualization.py`  
**Done when**: `report.summary()` formats target, `EXPLORATORY_FULL_DATA`, associations ranked by `|value|` descending, `UNDEFINED_NAN` kept separate, redundant pairs, and `METHODOLOGICAL_WARNINGS`.  
**Tests**: Unit tests in `tests/unit/features/test_exploratory_visualization.py` verifying ranking, `UNDEFINED_NAN` separation, redundant pairs, and warnings.  
**Gate**: `.venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -k "summary" -v`  

### T2: Implement Markdown/HTML exploratory reports and pure-NumPy SVG/PNG builders in `features/visualization.py` [x]
**Depends on**: T1  
**Files**: `src/experimental_ml/features/visualization.py`, `src/experimental_ml/features/__init__.py`, `tests/unit/features/test_exploratory_visualization.py`  
**Done when**: `render_exploratory_report`, `render_exploratory_target_chart`, and `render_exploratory_redundancy_heatmap` generate deterministic MD, offline HTML, SVG, and PNG bytes using stdlib + `numpy` only (`XCUT-02`).  
**Tests**: Unit tests verifying MD/HTML sections (warnings, ranked table, redundant pairs, matrix, scenario guidance), valid SVG XML & PNG magic header, and determinism.  
**Gate**: `.venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -v`  

### T3: Integrate visual outputs and ranked `stdout` summary into `cmd_features.py` [x]
**Depends on**: T2  
**Files**: `src/experimental_ml/cli/cmd_features.py`, `tests/unit/cli/test_exploratory_cli_visuals.py`  
**Done when**: `expml features explore` prints ranked summary to `stdout` without 64-hex hashes (`CLI-11`), writes `reports/exploratory_features.{json,md,html}` and `figures/exploratory_*.{svg,png}`, and leaves `configuration/scenarios.json` untouched.  
**Tests**: CLI and `quickrun` integration tests in `tests/unit/cli/test_exploratory_cli_visuals.py` plus `tests/integration/test_mvp_audit_invariants.py`.  
**Gate**: `.venv/bin/pytest tests/unit/cli/test_exploratory_cli_visuals.py tests/integration/test_mvp_audit_invariants.py -v`  

### T4: Synchronize documentation, reference catalogs, engineering docs, and `.specs/STATE.md` [x]
**Depends on**: T3  
**Files**: `docs/guia/02_tutorial_6_etapas.md`, `docs/guias_praticos/07_cenarios_features_estabilidade.md`, `docs/referencia/{api_python,cli_catalogo}.md`, `docs/engenharia_software/{ARQUITETURA_E_CONTRATOS,ESPECIFICACAO_REQUISITOS,ETAPA_ATUAL_ENGENHARIA}.md`, `.specs/STATE.md`  
**Done when**: All guides, reference docs, engineering docs, and `.specs/STATE.md` (`AD-025`) document Stage 2 visualization outputs and pass automated integrity checks + full test suite.  
**Tests**: `tests/unit/test_documentation_integrity.py` and `.venv/bin/pytest tests/ -q`.  
**Gate**: `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v`  

---

## Checks

**C1** - `ExploratoryFeatureReport.summary()` ranks associations by `|value|` descending, keeps `UNDEFINED_NAN` separate, and includes redundant pairs and `METHODOLOGICAL_WARNINGS` (EXPL-01).
  Proof: run expl_unit | test_exploratory_report_summary_ranking_and_nan PASSED

**C2** - `render_exploratory_report` generates Markdown and offline self-contained HTML with `EXPLORATORY_FULL_DATA` warnings, ranked table, redundant pairs, full matrix, and scenario guidance (EXPL-03).
  Proof: run expl_unit | test_render_exploratory_report_md_and_html PASSED

**C3** - `render_exploratory_target_chart` and `render_exploratory_redundancy_heatmap` produce deterministic SVG and PNG bytes in pure Python/NumPy (`XCUT-02`) (EXPL-04).
  Proof: run expl_unit | test_exploratory_svg_and_png_charts_deterministic PASSED

**C4** - `expml features explore` prints ranked summary to `stdout` without 64-hex hashes (`CLI-11`) and persists all visual reports and charts (EXPL-02).
  Proof: run expl_cli | test_cli_features_explore_visual_outputs_and_stdout PASSED

**C5** - Stage 2 visualization never creates or mutates `configuration/scenarios.json` (`CA-E2-01`) and `expml quickrun` + `XCUT-02` invariants pass (EXPL-05).
  Proof: run expl_cli | test_audit_xcut02_runtime_purity_ast PASSED

**C6** - Documentation integrity passes after synchronizing guides, reference catalogs, and engineering docs (EXPL-06).
  Proof: run expl_docs | test_markdown_links_and_anchors_valid PASSED

## Handoff

- **Next step**: Awaiting user approval of `tasks.md` before starting T1.
- **Dispatched:** none
