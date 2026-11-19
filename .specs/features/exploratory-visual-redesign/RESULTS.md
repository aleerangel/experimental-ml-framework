# exploratory-visual-redesign Results

**Status**: Implemented (T1–T4 Completed)

## Summary of Changes
- **T1 (`src/experimental_ml/features/types.py`)**: Added `ExploratoryFeatureReport.ranked_target_features()` and updated `summary(top_n=15)` to aggregate associations per unique `feature_name` ranked by `mean(|value|)` descending, showing individual metric values and keeping `UNDEFINED_NAN` separate (`EXPLR-01`).
- **T2 (`src/experimental_ml/features/visualization.py`, `__init__.py`)**: Implemented pure-NumPy/Python labeled PNG charts (`render_exploratory_target_chart`, `render_exploratory_redundancy_heatmap` with 5×7 bitmap labels/values/color legends, rejecting `.svg` — `XCUT-02`), dedicated CSV exporters (`render_exploratory_target_csv`, `render_exploratory_redundancy_csv`), clean Markdown, and offline A4 print/PDF-ready HTML (`@page`, `@media print`, `print-color-adjust: exact`, zero horizontal scrollbars).
- **T3 (`src/experimental_ml/cli/cmd_features.py`, `tests/unit/cli/test_exploratory_cli_visuals.py`)**: Updated `expml features explore` and `expml quickrun` to emit JSON, MD, print-ready HTML, 2 CSVs, and 2 labeled PNGs with zero `.svg` files while preserving `configuration/scenarios.json` untouched (`CA-E2-01`).
- **T4 (`docs/`, `.specs/STATE.md`)**: Synchronized user guides, API/CLI references, engineering docs, and `AD-026`.

## Verification Gates Executed
- `.venv/bin/pytest tests/unit/features/test_exploratory_visualization.py -v`: `4 passed`
- `.venv/bin/pytest tests/unit/cli/test_exploratory_cli_visuals.py tests/unit/cli/test_cmd_features.py tests/integration/test_mvp_audit_invariants.py -v`: `12 passed`
- `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v`: `4 passed`
