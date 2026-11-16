# m7-2-figures-full-report Tasks (M7.2 Figuras Determinísticas e Relatório Completo)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m7-2-figures-full-report/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-16 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/reporting/ tests/integration/reporting/ -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Deterministic Figures (`src/experimental_ml/reporting/figures.py`) | unit | build_figure_spec (filtra UNDEFINED_NAN/não-finitos, proveniência relativa), render_figure (SVG, PNG 300 DPI, PDF, determinismo de bytes, formato inválido) | `tests/unit/reporting/test_reporting_figures.py` | `.venv/bin/pytest tests/unit/reporting/test_reporting_figures.py -v` |
| Full Scientific Report (`src/experimental_ml/reporting/report.py`) | unit | ResearcherDeclarations, render_full_report (Markdown, HTML autocontido CSS inline offline), 3 seções separadas, sem hashes, formato inválido | `tests/unit/reporting/test_reporting_report.py` | `.venv/bin/pytest tests/unit/reporting/test_reporting_report.py -v` |
| Integration & Purity (`tests/integration/reporting/test_m72_integration.py`) | integration | Fluxo M7.1 + M7.2 ponta a ponta e pureza runtime XCUT-02 (zero matplotlib/pillow) | `tests/integration/reporting/test_m72_integration.py` | `.venv/bin/pytest tests/integration/reporting/test_m72_integration.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After unit tasks | `.venv/bin/pytest tests/unit/reporting/ -v` |
| Full | After integration task | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/unit/reporting/ -v` |

---

## Execution Plan

### Phase 1: Figuras Determinísticas em Python/NumPy Puro (`P1`)

```
T1
```

### Phase 2: Relatório Científico Completo (`P2`)

```
T1 --> T2
```

### Phase 3: API Pública e Integração (`P3`)

```
T2 --> T3
```

---

## Task Breakdown

### Phase 1: Figuras Determinísticas em Python/NumPy Puro

#### T1: Implementar build_figure_spec e render_figure (SVG, PNG 300 DPI, PDF) [ ]

**What**: Criar `src/experimental_ml/reporting/figures.py` com `build_figure_spec` (construindo `PlotSpecification` com `ArtifactProvenance` relativa e excluindo valores `UNDEFINED_NAN`/não-finitos com nota explícita) e `render_figure` gerando bytes determinísticos em `"svg"`, `"png"` (chunk `pHYs` 300 DPI) e `"pdf"` (PDF 1.4 válido), lançando `ConfigurationError` para formatos não suportados. Adicionar testes em `tests/unit/reporting/test_reporting_figures.py`.  
**Where**: `src/experimental_ml/reporting/figures.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/reporting/types.py`, `src/experimental_ml/reporting/loader.py`  
**Requirement**: REP-04  
**Tests**: `tests/unit/reporting/test_reporting_figures.py`  
**Gate**: `.venv/bin/pytest tests/unit/reporting/test_reporting_figures.py -v`

---

### Phase 2: Relatório Científico Completo

#### T2: Implementar ResearcherDeclarations e render_full_report (Markdown e HTML) [ ]

**What**: Adicionar `ResearcherDeclarations` em `src/experimental_ml/reporting/types.py` e criar `src/experimental_ml/reporting/report.py` com `render_full_report` gerando Markdown e HTML autocontido (CSS inline, zero links externos), separado explicitamente em Declarações do Pesquisador, Fatos Computacionais Registrados e Interpretações Derivadas, com paridade numérica e exclusão de `*_hash`. Adicionar testes em `tests/unit/reporting/test_reporting_report.py`.  
**Where**: `src/experimental_ml/reporting/report.py`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/reporting/tables.py`, `src/experimental_ml/reporting/types.py`  
**Requirement**: REP-05  
**Tests**: `tests/unit/reporting/test_reporting_report.py`  
**Gate**: `.venv/bin/pytest tests/unit/reporting/test_reporting_report.py -v`

---

### Phase 3: API Pública e Integração

#### T3: Expor API pública de M7.2 e validar integração e pureza XCUT-02 [ ]

**What**: Atualizar `src/experimental_ml/reporting/__init__.py` exportando `ResearcherDeclarations`, `build_figure_spec`, `render_figure` e `render_full_report`. Criar `tests/integration/reporting/test_m72_integration.py` validando geração de figuras + relatório Markdown/HTML e pureza runtime sem `matplotlib`/`pillow` (`XCUT-02`).  
**Where**: `src/experimental_ml/reporting/__init__.py`  
**Depends on**: T2  
**Reuses**: `src/experimental_ml/reporting/figures.py`, `report.py`  
**Requirement**: REP-04, REP-05  
**Tests**: `tests/integration/reporting/test_m72_integration.py`  
**Gate**: `.venv/bin/pytest tests/unit/reporting/ tests/integration/reporting/ -v`

---

## Checks

**C1** - `build_figure_spec` constrói `PlotSpecification` com proveniência relativa, exclui `UNDEFINED_NAN`/não-finitos e registra exclusões em `notes`. (REP-04, AC-M72-01-01)  
Proof: run unit | tests/unit/reporting/test_reporting_figures.py::test_m72_01_build_figure_spec_excludes_nan_and_provenance PASSED

**C2** - `render_figure` produz bytes válidos e determinísticos para `"svg"`, `"png"` (300 DPI `pHYs`) e `"pdf"` em Python/NumPy puro. (REP-04, AC-M72-01-02)  
Proof: run unit | tests/unit/reporting/test_reporting_figures.py::test_m72_01_render_figure_svg_png_300dpi_pdf_deterministic PASSED

**C3** - `render_figure` lança `ConfigurationError` para formatos não suportados. (REP-04, AC-M72-01-03)  
Proof: run unit | tests/unit/reporting/test_reporting_figures.py::test_m72_01_unsupported_format_raises PASSED

**C4** - `render_full_report` estrutura o relatório nas 3 seções explícitas (Declarações, Fatos Computacionais e Interpretações Derivadas) em Markdown e HTML. (REP-05, AC-M72-02-01)  
Proof: run unit | tests/unit/reporting/test_reporting_report.py::test_m72_02_three_sections_markdown_and_html PASSED

**C5** - `render_full_report` preserva paridade numérica, exclui `*_hash` e embute CSS inline sem links externos no HTML. (REP-05, AC-M72-02-02)  
Proof: run unit | tests/unit/reporting/test_reporting_report.py::test_m72_02_html_offline_parity_and_no_hashes PASSED

**C6** - `render_full_report` lança `ConfigurationError` para formato inválido. (REP-05, AC-M72-02-03)  
Proof: run unit | tests/unit/reporting/test_reporting_report.py::test_m72_02_invalid_report_format_raises PASSED

**C7** - Fluxo integrado M7.1 + M7.2 gerando tabelas, figuras e relatório completo via API pública. (REP-04)  
Proof: run unit | tests/integration/reporting/test_m72_integration.py::test_m72_end_to_end_figures_and_report PASSED

**C8** - Renderização de figuras e relatórios opera 100% sem `matplotlib`/`pillow`/`scipy` (`XCUT-02`). (XCUT-02)  
Proof: run unit | tests/integration/reporting/test_m72_integration.py::test_m72_runtime_purity_xcut02 PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T1
- **Next Task:** T2
