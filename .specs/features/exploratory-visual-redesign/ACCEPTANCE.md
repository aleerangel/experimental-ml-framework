# Acceptance Walkthrough: `exploratory-visual-redesign`

## Prerequisites
- Virtualenv active (`pytest`, `expml`).
- Chrome/DevTools available for real-browser visual inspection of `exploratory_features.html` and PNGs.

## Consumer Scenarios
1. **Unique Top-N Ranking (`report.summary(top_n=15)`):**
   - Numeric dataset with both `PEARSON` and `SPEARMAN` per feature shows 1 row/bar per unique feature ranked by `mean(|value|)`.
2. **CLI (`expml features explore` & `expml quickrun`):**
   - Generates `.json`, `.md`, `.html`, `exploratory_target_associations.csv`, `exploratory_redundancy_matrix.csv`, and both `.png` charts; zero `.svg` files; `scenarios.json` untouched.
3. **Browser & Print/PDF Visual Verification:**
   - Open `exploratory_features.html` in headless Chrome (`verify-screens` / browser check) to verify zero horizontal scrollbars (`scrollWidth <= innerWidth`), crisp embedded PNGs with legible text/values/legends, and clean A4 print CSS.

## Approval Criteria
- All checks (`C1`–`C6`) pass (`check_proofs.py`), visual browser check confirms HTML + PNG legibility, independent Verifier reports `PASS`, and full suite passes.
