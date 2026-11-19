# Specification: Clean Exploratory Feature Outputs, Legible PNGs & Print-Ready HTML (`exploratory-visual-redesign`)

**Status**: Approved  
**Approved**: 2026-11-19 - user: "aprovado"  
**Scope**: Medium (terminal summary + clean Markdown + print/PDF-ready HTML + CSVs + self-contained legible PNGs with per-feature aggregation, no SVG)  
**Depends on**: M3.1 (`m3-1-exploratory-features`), M3.4 (`m3-4-cli-end-to-end`), `exploratory-features-visualization`

## Problem Statement

1. **Duplicate features in Top-N rankings:** Because `explore_features` computes two metrics per numeric feature in regression (`PEARSON` and `SPEARMAN`), flat Top-15 lists repeat high-scoring features twice, crowding out other predictors. Aggregating by unique feature using the mean of `|metric|` (while still displaying each metric's value) ensures Top-N shows N distinct predictors.
2. **Unlabeled PNGs & messy HTML/SVG:** Previous HTML tables with wide matrices caused horizontal scrollbars and poor print layout, and PNGs lacked text labels/legends. Both PNGs must render complete labels/values/legends, giant matrices must live in CSV/PNG rather than overflowing HTML/MD, and `exploratory_features.html` must be print/PDF-ready (`@page` A4, clean pagination, no scrollbars) and visually verified.

## Out of Scope

- SVG chart generation for Stage 2 (PNG + CSV + MD + print-ready HTML only).
- External plotting/font dependencies (`matplotlib`, `pillow`, `cairo`), prohibited by `XCUT-02`.
- Automatic or silent creation/modification of `configuration/scenarios.json` (`CA-E2-01`).

## Assumptions & Open Questions

**Open questions:** none — user confirmed on 2026-11-19 to include terminal summary, clean Markdown, CSVs, complete/legible PNGs, and print/PDF-ready HTML (without SVG), with per-feature aggregation by mean `|value|`.

| Decision / Assumption | Chosen Default | Rationale |
| :--- | :--- | :--- |
| Stage 2 outputs | Terminal summary (`report.summary()` + `stdout`), clean `reports/exploratory_features.md`, print/PDF-ready `reports/exploratory_features.html`, `reports/exploratory_features.json`, CSVs (`exploratory_target_associations.csv`, `exploratory_redundancy_matrix.csv`), and labeled PNGs (`figures/exploratory_target_associations.png`, `figures/exploratory_redundancy_heatmap.png`) | Covers terminal, Markdown, spreadsheets, high-resolution PNGs, and print/PDF export cleanly. |
| Per-feature ranking aggregation | Group `target_associations` by `feature_name`; compute `mean_abs = mean(|valid_values|)` (in `[0, 1]`) for ranking, displaying individual metrics alongside | Prevents duplicate features in Top-N while preserving both linear and monotonic values. |
| PNG legibility (`XCUT-02`) | Pure Python/NumPy crisp bitmap font rendering feature names, values, titles, and color-bar legend directly into PNG bytes | Ensures PNGs are self-explanatory and 100% dependency-free. |
| Print/PDF-ready HTML | `@page { size: A4 portrait; margin: 15mm; }`, `@media print` with `break-inside: avoid` and `print-color-adjust: exact`, zero giant inline `N x N` tables or scrollbars, linking CSVs and embedding PNGs | Guarantees clean PDF export via browser print without clipping or horizontal overflow. |

## User Stories

### US-EXPLR-01 (Priority: P1) — Ranking Único por Atributo (Sem Duplicatas)
As a researcher, I want Top-15 associations grouped by unique predictor (ranked by mean `|value|` across its valid metrics while showing each metric), so that 15 entries represent 15 distinct predictors.

### US-EXPLR-02 (Priority: P1) — PNGs Completos e Legíveis + CSVs + Markdown Limpo
As a researcher, I want `expml features explore` to produce clean Markdown, structured CSVs, and complete, legible PNG charts (with feature names, values, and legends rendered inside the PNG), without SVG files.

### US-EXPLR-03 (Priority: P1) — HTML Pronto para Impressão / Exportação para PDF
As a researcher, I want `reports/exploratory_features.html` formatted for clean screen reading and A4 PDF export (no horizontal scrollbars, crisp tables, embedded PNGs, print CSS, visually verified in a real browser).

## Requirements (EARS Notation)

- **EXPLR-01 (Per-Feature Aggregation & Unique Top-N):** WHEN `report.summary(top_n=15)`, Markdown, HTML, CSV, or PNG ranking is built from `ExploratoryFeatureReport`, THE SYSTEM SHALL group valid finite `target_associations` by `feature_name`, compute the mean absolute score (`mean_abs = mean(|value|)` across valid metrics for that feature), sort descending by `mean_abs` (tie-break by `feature_name`), and display both the aggregated score and individual metric values (keeping `UNDEFINED_NAN` features separate, never `0.0`).
- **EXPLR-02 (Clean Terminal & Markdown Report):** WHEN `expml features explore` or `render_exploratory_report(..., fmt="markdown")` runs, THE SYSTEM SHALL output the deduplicated ranked summary to `stdout` (without raw 64-hex hashes, `CLI-11`) and write `reports/exploratory_features.md` containing: `EXPLORATORY_FULL_DATA` warning, unique-feature ranked table, flagged Redundant Pairs table, links to CSVs and PNG charts (no giant inline `N x N` table), and `FIXED`/`DYNAMIC` scenario guidance.
- **EXPLR-03 (Structured CSV Exports):** WHEN `expml features explore` runs, THE SYSTEM SHALL write `reports/exploratory_target_associations.csv` (ranked by `mean_abs` descending, 1 row per feature with individual metrics) and `reports/exploratory_redundancy_matrix.csv` (full symmetric matrix).
- **EXPLR-04 (Complete, Legible Pure-NumPy PNG Charts — `XCUT-02`):** WHEN `render_exploratory_target_chart` or `render_exploratory_redundancy_heatmap` renders PNG bytes, THE SYSTEM SHALL draw readable text labels (feature names, numeric values, title, and color legend) directly onto the NumPy RGB canvas using pure Python/NumPy only, deterministically.
- **EXPLR-05 (Print/PDF-Ready Offline HTML):** WHEN `render_exploratory_report(..., fmt="html")` generates `reports/exploratory_features.html`, THE SYSTEM SHALL produce self-contained offline HTML (no SVG charts, no giant `N x N` inline table, no horizontal scrollbars) with `@page` A4 portrait rules, `@media print` pagination/color preservation (`break-inside: avoid`, `print-color-adjust: exact`), and embedded PNG charts (`../figures/exploratory_*.png`).
- **EXPLR-06 (No SVG, Strict Non-Leakage & Sync):** WHEN `expml features explore` runs, THE SYSTEM SHALL NOT generate `.svg` files and SHALL NEVER create or mutate `configuration/scenarios.json` (`CA-E2-01`), with all docs/tests/`STATE.md` (`AD-026`) synchronized and passing.

## Acceptance Criteria

- `CA-EXPLR-01`: `report.summary(top_n=15)`, `exploratory_features.md`, and `exploratory_features.html` list at most 1 entry per `feature_name`, ranked by `mean(|value|)`, showing individual metrics and keeping `UNDEFINED_NAN` separate.
- `CA-EXPLR-02`: `expml features explore` creates `reports/exploratory_features.{json,md,html}`, `reports/exploratory_target_associations.csv`, `reports/exploratory_redundancy_matrix.csv`, `figures/exploratory_target_associations.png`, and `figures/exploratory_redundancy_heatmap.png`, and does NOT create `.svg` or `configuration/scenarios.json`.
- `CA-EXPLR-03`: Both PNGs are deterministic, valid PNGs (`300 DPI`) with rendered labels/values/legend using stdlib + `numpy` only (`XCUT-02`).
- `CA-EXPLR-04`: `exploratory_features.html` contains `@page` / `@media print` PDF-export CSS, zero horizontal overflow/scrollbars (verified in real browser rendering), and `expml quickrun`, `test_documentation_integrity.py`, and full suite pass cleanly.

## Requirement Traceability

| Requirement | User Story | Acceptance Criterion | Status |
| :--- | :--- | :--- | :--- |
| EXPLR-01 | `US-EXPLR-01` | `CA-EXPLR-01` | pending |
| EXPLR-02 | `US-EXPLR-01`, `US-EXPLR-02` | `CA-EXPLR-01`, `CA-EXPLR-02` | pending |
| EXPLR-03 | `US-EXPLR-02` | `CA-EXPLR-02` | pending |
| EXPLR-04 | `US-EXPLR-02` | `CA-EXPLR-03` | pending |
| EXPLR-05 | `US-EXPLR-03` | `CA-EXPLR-04` | pending |
| EXPLR-06 | `US-EXPLR-02`, `US-EXPLR-03` | `CA-EXPLR-02`, `CA-EXPLR-04` | pending |
