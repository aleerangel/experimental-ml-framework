# Acceptance Walkthrough: `exploratory-features-visualization`

## Prerequisites
- Virtualenv active with `experimental-ml-framework` installed (`.venv/bin/pytest`, `.venv/bin/expml`).

## Consumer Scenarios
1. **Python (`report.summary()` & visual builders):**
   - Call `explore_features(view)` and `report.summary(top_n=10)` to inspect ranked associations, `UNDEFINED_NAN` separation, redundant pairs, and `METHODOLOGICAL_WARNINGS`.
   - Render Markdown, offline HTML, and SVG/PNG charts directly from `ExploratoryFeatureReport`.
2. **CLI (`expml features explore` & `expml quickrun`):**
   - Run `expml features explore` and verify ranked summary appears on `stdout` without SHA-256 hashes, alongside `reports/exploratory_features.{md,html}` and `figures/exploratory_*.{svg,png}`, with `configuration/scenarios.json` untouched.
3. **Documentation:**
   - Verify updated guides, references, engineering docs, and `test_documentation_integrity.py`.

## Approval Criteria
- All checks (`C1`–`C6`) pass (`check_proofs.py`), independent Verifier reports `PASS`, and full suite passes without `XCUT-02` or `CLI-10`/`CLI-11` regressions.
