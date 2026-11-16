# m7-1-reporting-contracts-tables Tasks (M7.1 Contratos, Leitura e Tabelas das 7 Famílias)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m7-1-reporting-contracts-tables/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-16 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/reporting/ tests/integration/reporting/ -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Reporting Types (`src/experimental_ml/reporting/types.py`) | unit | ReportFamily, ReportAudience, PlotType, ColumnAlignment, ArtifactProvenance (rejeita caminhos absolutos), ReportContentSelection, TableModel, PlotSpecification | `tests/unit/reporting/test_reporting_types.py` | `.venv/bin/pytest tests/unit/reporting/test_reporting_types.py -v` |
| Read-Only Loader (`src/experimental_ml/reporting/loader.py`) | unit | load_experiment_artifacts_readonly (sem model fit/predict), select_report_content (FULL_LAB, ARTICLE_COMPACT, CUSTOM) | `tests/unit/reporting/test_reporting_loader.py` | `.venv/bin/pytest tests/unit/reporting/test_reporting_loader.py -v` |
| Table Builders & Renderers (`src/experimental_ml/reporting/tables.py`) | unit | build_table_model (Famílias A–G), paridade exata com statistics/*.json, distinção None vs UNDEFINED_NAN vs ±Inf, exclusão *_hash, CSV/MD/LaTeX booktabs | `tests/unit/reporting/test_reporting_tables.py` | `.venv/bin/pytest tests/unit/reporting/test_reporting_tables.py -v` |
| Integration & Purity (`tests/integration/reporting/test_m71_integration.py`) | integration | Fluxo somente-leitura Stage 1–5 -> Tabelas A–G + pureza XCUT-02 | `tests/integration/reporting/test_m71_integration.py` | `.venv/bin/pytest tests/integration/reporting/test_m71_integration.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After unit tasks | `.venv/bin/pytest tests/unit/reporting/ -v` |
| Full | After integration task | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/unit/reporting/ -v` |

---

## Execution Plan

### Phase 1: Contratos Imutáveis de Publicação (`P1`)

```
T1
```

### Phase 2: Carregamento Somente-Leitura e Seleção (`P2`)

```
T1 --> T2
```

### Phase 3: Tabelas das 7 Famílias e Renderizadores (`P3`)

```
T2 --> T3
```

### Phase 4: API Pública e Integração Ponta a Ponta (`P4`)

```
T3 --> T4
```

---

## Task Breakdown

### Phase 1: Contratos Imutáveis de Publicação

#### T1: Definir enums e dataclasses congeladas de reporting e ArtifactProvenance [x]

**What**: Criar `src/experimental_ml/reporting/types.py` definindo `ReportFamily`, `ReportAudience`, `PlotType`, `ColumnAlignment`, `ArtifactProvenance` (rejeitando caminhos absolutos), `ReportContentSelection`, `TableColumn`, `TableModel`, `PlotSeries`, `PlotSpecification` e `LoadedExperimentData` com imutabilidade (`frozen=True`). Adicionar testes em `tests/unit/reporting/test_reporting_types.py`.  
**Where**: `src/experimental_ml/reporting/types.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/statistics/storage.py`, `src/experimental_ml/core/findings.py`  
**Requirement**: REP-01  
**Tests**: `tests/unit/reporting/test_reporting_types.py`  
**Gate**: `.venv/bin/pytest tests/unit/reporting/test_reporting_types.py -v`

---

### Phase 2: Carregamento Somente-Leitura e Seleção

#### T2: Implementar load_experiment_artifacts_readonly e select_report_content [x]

**What**: Criar `src/experimental_ml/reporting/loader.py` com `load_experiment_artifacts_readonly` (validando `verify_statistics_gate` e lendo artefatos persistidos sem importar ajuste/predição de modelos — `CA-E6-01`) e `select_report_content` (regras determinísticas para `FULL_LAB`, `ARTICLE_COMPACT` e `CUSTOM`). Adicionar testes em `tests/unit/reporting/test_reporting_loader.py`.  
**Where**: `src/experimental_ml/reporting/loader.py`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/stages/stage_gates.py`, `src/experimental_ml/core/storage.py`  
**Requirement**: REP-02  
**Tests**: `tests/unit/reporting/test_reporting_loader.py`  
**Gate**: `.venv/bin/pytest tests/unit/reporting/test_reporting_loader.py -v`

---

### Phase 3: Tabelas das 7 Famílias e Renderizadores

#### T3: Implementar build_table_model (A–G) e renderizadores CSV/Markdown/LaTeX [x]

**What**: Criar `src/experimental_ml/reporting/tables.py` com `build_table_model` para as 7 famílias (`A` a `G`), preservando valores numéricos brutos de `statistics/*.json` em `TableModel.rows`, distinguindo `None` (`"N/A"`), `UNDEFINED_NAN` (`"UNDEFINED_NAN"`) e `±Inf` (`"Inf"`/`"-Inf"`), excluindo campos `*_hash`/`*_digest`/`sha256`/`checksum`, e renderizadores `render_table_csv`, `render_table_markdown` e `render_table_latex` (`booktabs`). Adicionar testes em `tests/unit/reporting/test_reporting_tables.py`.  
**Where**: `src/experimental_ml/reporting/tables.py`  
**Depends on**: T2  
**Reuses**: `src/experimental_ml/reporting/types.py`, `src/experimental_ml/reporting/loader.py`  
**Requirement**: REP-03  
**Tests**: `tests/unit/reporting/test_reporting_tables.py`  
**Gate**: `.venv/bin/pytest tests/unit/reporting/test_reporting_tables.py -v`

---

### Phase 4: API Pública e Integração Ponta a Ponta

#### T4: Expor API pública de M7.1 e validar integração somente-leitura [ ]

**What**: Criar `src/experimental_ml/reporting/__init__.py` exportando todos os símbolos públicos de M7.1. Criar `tests/integration/reporting/test_m71_integration.py` validando fluxo ponta a ponta Stage 1–5 -> Tabelas A–G e pureza runtime `XCUT-02` + ausência de import de `fit_model`/`predict_model`.  
**Where**: `src/experimental_ml/reporting/__init__.py`  
**Depends on**: T3  
**Reuses**: `src/experimental_ml/reporting/types.py`, `loader.py`, `tables.py`  
**Requirement**: REP-01, REP-02, REP-03  
**Tests**: `tests/integration/reporting/test_m71_integration.py`  
**Gate**: `.venv/bin/pytest tests/unit/reporting/ tests/integration/reporting/ -v`

---

## Checks

**C1** - Enums `ReportFamily` (A–G), `ReportAudience`, `PlotType` e `ColumnAlignment` contêm os valores canônicos. (REP-01, AC-M71-01-01)  
Proof: run unit | tests/unit/reporting/test_reporting_types.py::test_m71_01_enums_values PASSED

**C2** - Dataclasses de publicação e proveniência são congeladas e lançam `FrozenInstanceError` ao tentar mutação. (REP-01, AC-M71-01-02)  
Proof: run unit | tests/unit/reporting/test_reporting_types.py::test_m71_01_frozen_immutability PASSED

**C3** - `ArtifactProvenance` rejeita qualquer caminho absoluto em `source_relative_paths`. (REP-01, AC-M71-01-03)  
Proof: run unit | tests/unit/reporting/test_reporting_types.py::test_m71_01_provenance_rejects_absolute_paths PASSED

**C4** - `load_experiment_artifacts_readonly` valida `verify_statistics_gate` e opera em modo somente-leitura sem importar ajuste/predição de modelos. (REP-02, AC-M71-02-01)  
Proof: run unit | tests/unit/reporting/test_reporting_loader.py::test_m71_02_readonly_loader_no_model_execution PASSED

**C5** - `select_report_content` aplica regras determinísticas para `FULL_LAB`, `ARTICLE_COMPACT` e `CUSTOM`. (REP-02, AC-M71-02-02)  
Proof: run unit | tests/unit/reporting/test_reporting_loader.py::test_m71_02_select_report_content_modes PASSED

**C6** - `build_table_model` gera `TableModel` válido com `ArtifactProvenance` relativa para todas as 7 famílias (`A`–`G`). (REP-03, AC-M71-03-01)  
Proof: run unit | tests/unit/reporting/test_reporting_tables.py::test_m71_03_all_seven_families_supported PASSED

**C7** - `TableModel.rows` preserva paridade numérica exata com `statistics/*.json` e distingue `None`, `UNDEFINED_NAN` e `±Inf` sem coerção para zero. (REP-03, AC-M71-03-02)  
Proof: run unit | tests/unit/reporting/test_reporting_tables.py::test_m71_03_numeric_parity_and_missing_distinction PASSED

**C8** - Campos estruturais de hash (`*_hash`, `*_digest`, `sha256`, `checksum`) são excluídos sem remover identificadores legítimos do usuário. (REP-03, AC-M71-03-03)  
Proof: run unit | tests/unit/reporting/test_reporting_tables.py::test_m71_03_structural_hash_exclusion PASSED

**C9** - `render_table_csv`, `render_table_markdown` e `render_table_latex` geram CSV preciso, Markdown alinhado e LaTeX `booktabs` válido. (REP-03, AC-M71-03-04)  
Proof: run unit | tests/unit/reporting/test_reporting_tables.py::test_m71_03_renderers_csv_markdown_latex_booktabs PASSED

**C10** - Fluxo integrado somente-leitura Stage 1–5 -> Tabelas A–G via API pública de `experimental_ml.reporting`. (REP-01)  
Proof: run unit | tests/integration/reporting/test_m71_integration.py::test_m71_end_to_end_readonly_tables PASSED

**C11** - Subsistema `reporting` opera 100% em Python/NumPy puro sem dependências pesadas (`XCUT-02`). (XCUT-02)  
Proof: run unit | tests/integration/reporting/test_m71_integration.py::test_m71_runtime_purity_xcut02 PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T1
- **Next Task:** T2
