# Specification: Exploratory Feature Visualization & Usability (`exploratory-features-visualization`)

**Status**: Approved  
**Approved**: 2026-11-19 - user: "Aprovado"  
**Scope**: Large (Stage 2 `features`, Stage 2 CLI `cmd_features`, visual reports/figures in pure Python/NumPy, and documentation)  
**Depends on**: M3.1 (`m3-1-exploratory-features`), M3.4 (`m3-4-cli-end-to-end`), M7.2 (`m7-2-figures-full-report`)

## Problem Statement

While `explore_features` (Stage 2) already computes rigorous univariate feature-target associations (Pearson, Spearman, Correlation Ratio $\eta$, Cramér's V), predictor-predictor redundancy matrices, and methodological anti-leakage warnings, its outputs are currently limited to raw JSON (`reports/exploratory_features.json`) and a minimal 4-line counter summary in `expml features explore`. Researchers—especially beginners—lack an immediate, readable summary in Python/CLI, visual Markdown/HTML tables, and deterministic charts to inspect associations and redundancy before defining `scenarios.json`.

## Out of Scope

- Automatic or silent modification of `scenarios.json` from full-data exploratory statistics (prohibited by `CA-E2-01` / anti-leakage).
- External plotting dependencies (`matplotlib`, `seaborn`, `plotly`, `pillow`), which are prohibited by `XCUT-02`.
- Multivariate feature selection algorithms (`PCA`, `RFE`, `Lasso`), which remain out of Wave 1 scope.

## Assumptions & Open Questions

**Open questions:** none — all product and scope decisions were confirmed by the user on 2026-11-19 (`A1`, `A2`, `A3`).

| Decision / Assumption | Chosen Default | Rationale |
| :--- | :--- | :--- |
| Output surfaces (`A1`) | Python `ExploratoryFeatureReport.summary()`, readable CLI stdout in `expml features explore`, `reports/exploratory_features.md`, offline `reports/exploratory_features.html`, and deterministic SVG/PNG figures | Full parity across Python, terminal, and visual browser/IDE inspection. |
| Visual indicators (`A2`) | Ranked Feature×Target table (sorted by `\|value\|` descending, keeping `UNDEFINED_NAN` separate), highlighted Redundant Pairs table, and full Predictor×Predictor matrix (table + SVG/PNG heatmap) + bar chart | Covers both quick triage and complete collinearity inspection. |
| Anti-leakage guidance (`A3`) | Prominent `EXPLORATORY_FULL_DATA` warning box + practical guidance section on translating findings into `FIXED` or `DYNAMIC` scenarios without auto-selecting features | Preserves `CA-E2-01` scientific rigor while guiding scenario construction. |
| Runtime purity (`XCUT-02` & `CLI-10`) | Pure Python stdlib + `numpy` only for SVG/PNG generation; lazy imports in CLI | Preserves project architectural invariants. |

## User Stories

### US-EXPL-01 (Priority: P1) — Resumo Legível em Python e no Terminal (`summary()` & `expml features explore`)
As a researcher, I want `ExploratoryFeatureReport.summary()` and `expml features explore` to display a ranked table of feature-target associations and flagged redundant pairs directly, so I do not have to parse raw JSON to inspect Stage 2 indicators.

### US-EXPL-02 (Priority: P1) — Relatório Visual `exploratory_features.md` / `.html` e Gráficos SVG/PNG
As a researcher, I want Stage 2 to generate readable `reports/exploratory_features.md`, self-contained `reports/exploratory_features.html`, and deterministic SVG/PNG charts (association bar chart and redundancy heatmap), so I can visually inspect relationships and multicollinearity before writing `scenarios.json`.

### US-EXPL-03 (Priority: P2) — Orientação Anti-Leakage para Montagem de Cenários
As a beginner researcher, I want the exploratory report to prominently display the `EXPLORATORY_FULL_DATA` warning alongside practical guidance on building `FIXED` and `DYNAMIC` scenarios, so I know how to interpret the indicators without introducing data leakage.

## Requirements (EARS Notation)

- **EXPL-01 (`ExploratoryFeatureReport.summary()`):** WHEN a caller invokes `report.summary(top_n=15)` on an `ExploratoryFeatureReport`, THE SYSTEM SHALL return a formatted plain-text summary containing the target column, `scope = "EXPLORATORY_FULL_DATA"`, the top `top_n` feature-target associations sorted by descending absolute value (with `UNDEFINED_NAN` entries listed separately, never coerced to `0.0`), flagged redundant pairs, and mandatory methodological warnings.
- **EXPL-02 (Enhanced CLI Output in `expml features explore`):** WHEN a user runs `expml features explore`, THE SYSTEM SHALL persist `reports/exploratory_features.json`, generate the visual report artifacts (`exploratory_features.md`, `exploratory_features.html`, and SVG/PNG figures), and print the ranked associations and redundant pairs summary directly to `stdout` without printing raw 64-char SHA-256 hashes (`CLI-11`).
- **EXPL-03 (Visual Reports `exploratory_features.md` & `.html`):** WHEN Stage 2 visual report rendering runs, THE SYSTEM SHALL generate `reports/exploratory_features.md` and offline self-contained `reports/exploratory_features.html` (embedded CSS, zero external network assets) containing: (1) prominent `EXPLORATORY_FULL_DATA` anti-leakage warnings, (2) ranked Feature×Target association table (highlighting strength bands and separating `UNDEFINED_NAN`), (3) flagged Redundant Pairs table, (4) full Predictor×Predictor redundancy matrix, and (5) practical guidance for defining `FIXED` and `DYNAMIC` scenarios.
- **EXPL-04 (Deterministic Pure-NumPy SVG/PNG Figures):** WHEN Stage 2 figure rendering runs, THE SYSTEM SHALL generate deterministic `figures/exploratory_target_associations.{svg,png}` (horizontal bar chart ranked by `|value|`) and `figures/exploratory_redundancy_heatmap.{svg,png}` (symmetric Predictor×Predictor heatmap) using only Python stdlib + `numpy` (`XCUT-02`), embedding/linking them in `exploratory_features.{md,html}`.
- **EXPL-05 (Strict Non-Leakage & `CA-E2-01` Preservation):** WHEN visual reports and charts are generated in Stage 2, THE SYSTEM SHALL NEVER automatically create or mutate `configuration/scenarios.json` or filter `SanitizedDatasetView.candidate_feature_cols`, preserving bit-for-bit determinism of `exploratory_features.json` and `CA-E2-01`.
- **EXPL-06 (Documentation Synchronization):** WHEN `exploratory-features-visualization` is implemented, THE SYSTEM SHALL update `docs/guia/02_tutorial_6_etapas.md`, `docs/guias_praticos/07_cenarios_features_estabilidade.md`, `docs/referencia/{api_python,cli_catalogo}.md`, `docs/engenharia_software/{ARQUITETURA_E_CONTRATOS,ESPECIFICACAO_REQUISITOS,ETAPA_ATUAL_ENGENHARIA}.md`, and `.specs/STATE.md`, passing `test_documentation_integrity.py` and the full test suite.

## Acceptance Criteria

- `CA-EXPL-01`: `report.summary()` returns ranked associations sorted by `|value|`, keeps `UNDEFINED_NAN` uncoerced, lists redundant pairs, and includes `METHODOLOGICAL_WARNINGS`.
- `CA-EXPL-02`: `expml features explore` prints ranked associations and redundant pairs to `stdout` and generates `reports/exploratory_features.md`, `reports/exploratory_features.html`, `figures/exploratory_target_associations.{svg,png}`, and `figures/exploratory_redundancy_heatmap.{svg,png}` without raw hashes in `stdout` (`CLI-11`) or non-stdlib/numpy imports (`XCUT-02`).
- `CA-EXPL-03`: `exploratory_features.html` renders cleanly offline with embedded CSS, displays `EXPLORATORY_FULL_DATA` warnings, ranked table, redundant pairs, full matrix, and scenario guidance, without modifying `configuration/scenarios.json`.
- `CA-EXPL-04`: `expml quickrun` also produces Stage 2 visual reports/figures cleanly, and all existing + new tests and `test_documentation_integrity.py` pass.

## Requirement Traceability

| Requirement | User Story | Acceptance Criterion | Status |
| :--- | :--- | :--- | :--- |
| EXPL-01 | `US-EXPL-01` | `CA-EXPL-01` | pending |
| EXPL-02 | `US-EXPL-01` | `CA-EXPL-02` | pending |
| EXPL-03 | `US-EXPL-02`, `US-EXPL-03` | `CA-EXPL-03` | pending |
| EXPL-04 | `US-EXPL-02` | `CA-EXPL-02`, `CA-EXPL-04` | pending |
| EXPL-05 | `US-EXPL-03` | `CA-EXPL-03` | pending |
| EXPL-06 | `US-EXPL-01`..`US-EXPL-03` | `CA-EXPL-04` | pending |
