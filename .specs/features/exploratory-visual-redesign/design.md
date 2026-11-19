# Design: Clean Exploratory Feature Outputs, Legible PNGs & Print-Ready HTML (`exploratory-visual-redesign`)

## 1. Architecture & Component Boundaries

All Stage 2 visualization and text rendering remain strictly pure Python stdlib + `numpy` (`XCUT-02`), preserving acyclic imports (`features` is Level 2) and never creating/mutating `configuration/scenarios.json` (`CA-E2-01`).

1. **Per-Feature Aggregation & Summary (`src/experimental_ml/features/types.py`):**
   - Group `target_associations` by `feature_name`:
     - Valid finite associations for a feature → compute `mean_abs = sum(abs(v) for v in vals) / len(vals)`, plus preserve per-metric breakdown (`PEARSON=+0.8800, SPEARMAN=+0.8500`).
     - Features with no valid finite metrics → listed separately under `UNDEFINED_NAN` (never coerced to `0.0`).
     - Sort unique features by `(-mean_abs, feature_name)` so `top_n=15` shows 15 distinct predictors.
   - `ExploratoryFeatureReport.summary(top_n=15)` formats the deduplicated ranking, `UNDEFINED_NAN` features, `high_redundancy_pairs`, and `METHODOLOGICAL_WARNINGS` without raw SHA-256 hashes (`CLI-11`).

2. **Pure-NumPy PNG Renderer with Crisp Bitmap Font (`src/experimental_ml/features/visualization.py`):**
   - Embedded 5×7 pixel bitmap font (printable ASCII + Latin-1 accents/signs, scaled cleanly 2×) draws titles, feature names, numeric values, axes, and color-bar legends directly onto the NumPy RGB canvas (`zlib` + `struct` 300 DPI PNG).
   - `render_exploratory_target_chart(report, fmt="png", *, top_n=15) -> bytes`: horizontal bar chart of unique predictors ranked by `mean_abs` with feature names on the left, colored bars (`+` blue, `-` red/mixed), and `mean_abs` + metric breakdown labels on the right.
   - `render_exploratory_redundancy_heatmap(report, fmt="png") -> bytes`: symmetric Predictor×Predictor PNG heatmap with row/column labels, diagonal neutral gray (`#f1f5f9`), off-diagonal heat gradient, cell values (when space allows), and color legend bar (`0.00 → 0.50 → 1.00`).
   - Raise `ConfigurationError` if `fmt != "png"` (removing SVG generation per `EXPLR-06`).

3. **CSVs, Markdown & Print/PDF-Ready HTML (`src/experimental_ml/features/visualization.py`):**
   - `render_exploratory_target_csv(report) -> str`: `rank,feature,mean_abs,strength,metrics_detail,status` sorted by `mean_abs` descending (with `UNDEFINED_NAN` rows clearly marked).
   - `render_exploratory_redundancy_csv(report) -> str`: full symmetric matrix CSV.
   - `render_exploratory_report(report, fmt="markdown"|"html", *, top_n=15, figure_paths=()) -> str`:
     - Clean Markdown: `EXPLORATORY_FULL_DATA` warning, unique-feature ranked table, Redundant Pairs table, links to CSVs and PNGs (never inlining giant `N x N` matrices), and `FIXED`/`DYNAMIC` guidance.
     - Print/PDF-ready offline HTML: `@page { size: A4 portrait; margin: 15mm; }`, `@media print` (`break-inside: avoid` on tables/boxes/figures, `print-color-adjust: exact`), clean fluid layout (`max-width: 960px`, zero horizontal scrollbars), embedded PNGs (`../figures/*.png`), and links to CSVs.

4. **CLI Integration (`src/experimental_ml/cli/cmd_features.py`):**
   - `handle_features_explore` writes `reports/exploratory_features.{json,md,html}`, `reports/exploratory_target_associations.csv`, `reports/exploratory_redundancy_matrix.csv`, `figures/exploratory_target_associations.png`, and `figures/exploratory_redundancy_heatmap.png` (no `.svg` files), and prints `report.summary()` + relative paths to `stdout`.
