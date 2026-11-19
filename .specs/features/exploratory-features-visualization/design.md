# Design: Exploratory Feature Visualization & Usability (`exploratory-features-visualization`)

## 1. Architecture & Component Boundaries

All Stage 2 visual reporting and plotting logic remains strictly pure Python stdlib + `numpy` (`XCUT-02`), never imports `reporting` into `features` circularly (dependency remains acyclic: `features` is Level 2), and never mutates `configuration/scenarios.json` (`CA-E2-01`).

1. **`ExploratoryFeatureReport.summary(top_n: int = 15) -> str` (`src/experimental_ml/features/types.py`):**
   - Ranks `target_associations` where `status == MetricStatus.VALID` and `math.isfinite(value)` by `abs(value)` descending (tie-break by `feature_name` ascending).
   - Lists `UNDEFINED_NAN` associations in a separate note (never coerced to `0.0`).
   - Formats `high_redundancy_pairs` sorted by `abs(value)` descending and appends `METHODOLOGICAL_WARNINGS`.

2. **Visual Report & Deterministic Figure Builders (`src/experimental_ml/features/visualization.py`, exported in `features/__init__.py`):**
   - `render_exploratory_report(report, fmt="markdown"|"html", *, top_n=15, figure_paths=()) -> str`:
     - Generates `exploratory_features.md` and self-contained offline `exploratory_features.html` (embedded CSS matching `reporting/report.py` aesthetic, including a prominent warning banner for `EXPLORATORY_FULL_DATA`, ranked Feature×Target table with strength bands `[Forte ≥ 0.70]`, `[Moderada 0.30–0.69]`, `[Fraca < 0.30]`, Redundant Pairs table, full Predictor×Predictor matrix, and practical `FIXED`/`DYNAMIC` scenario guidance).
   - `render_exploratory_target_chart(report, fmt="svg"|"png", *, top_n=15) -> bytes`:
     - Pure Python/NumPy (`zlib` + `struct` for 300 DPI PNG; `xml.sax.saxutils.escape` for SVG) horizontal bar chart sorted by `|value|`.
   - `render_exploratory_redundancy_heatmap(report, fmt="svg"|"png") -> bytes`:
     - Pure Python/NumPy symmetric Predictor×Predictor heatmap in SVG and PNG.

3. **CLI Integration (`src/experimental_ml/cli/cmd_features.py`):**
   - `handle_features_explore` persists `reports/exploratory_features.json`, generates `reports/exploratory_features.{md,html}` and `figures/exploratory_{target_associations,redundancy_heatmap}.{svg,png}`, and prints `report.summary()` to `stdout` (without raw 64-hex hashes, `CLI-11`).
