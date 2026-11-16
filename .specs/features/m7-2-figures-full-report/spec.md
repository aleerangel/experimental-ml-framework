# Feature: m7-2-figures-full-report

**Approved**: 2026-11-16 - user: "aprovado"

## Problem Statement

Com os contratos imutáveis, o carregamento somente-leitura e os construtores/renderizadores de tabelas das 7 famílias implementados no Sub-marco M7.1, a Etapa 6 (`experimental_ml.reporting`) necessita agora de:
1. **Especificação e Renderização Determinística de Figuras (`figures.py`, `RF6.1`, `RF6.2`, `XCUT-02`)**: Construir `PlotSpecification` a partir de `LoadedExperimentData` (sem invocar ajuste/predição de modelos — `CA-E6-01`) e renderizá-las de forma 100% determinística em **SVG**, **PNG (300 DPI)** e **PDF** usando exclusivamente biblioteca padrão Python + NumPy (`XCUT-02`, sem dependência de `matplotlib`).
2. **Gerador de Relatório Científico Completo (`report.py`, `RF6.1`, `ARQUITETURA §3.6`)**: Compor o relatório científico unificado em **Markdown** e **HTML autocontido com CSS embutido** (100% offline — `RNF03`), separando explicitamente as três naturezas de informação exigidas pela arquitetura:
   - *Declarações do Pesquisador (Proveniência Declarada)*;
   - *Fatos Computacionais Registrados* (tabelas e referências de figuras com paridade numérica com `statistics/*.json` e sem exposição de campos `*_hash` — `CA-E6-01`, `CA-E6-02`);
   - *Interpretações Derivadas e Condicionadas* (`StructuredConclusion` com ressalvas metodológicas).

## Out of Scope

- Empacotamento de reprodutibilidade (`build_reproducibility_package`, `checksums.sha256`, `artifact_provenance.json`, `REPRODUCE.md`) e portão `verify_report_gate` — escopo do Sub-marco M7.3.
- Interface CLI `expml report` (`generate`, `export`, `verify`) — escopo do Sub-marco M7.4.
- Inclusão de `matplotlib`, `pillow`, `weasyprint` ou qualquer dependência externa de runtime além de `numpy>=1.24.0` (`XCUT-02`).
- Acoplamento a qualquer domínio aplicado ou dados reais específicos (`RNF02`, `CA02`).

## Assumptions & Open Questions

**Open questions:** none - os formatos de saída (`png` 300 DPI, `svg`, `pdf`, `markdown`, `html`), a separação tripartite de seções no relatório completo e as restrições `CA-E6-01`, `CA-E6-02` e `XCUT-02` estão formalmente estabelecidos em `ARQUITETURA_E_CONTRATOS.md` (Seção 3.6) e `ESPECIFICACAO_REQUISITOS.md` (`RF6.1`, `RF6.2`).

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Motor de renderização gráfica (`XCUT-02`) | Gerador vetorial SVG, rasterizador PNG (`zlib` + chunk `pHYs` a 300 DPI = 11811 px/m) e escritor PDF 1.4 em Python/NumPy puro | Garante zero dependências externas, execução 100% offline e determinismo bit a bit |
| Tratamento de `UNDEFINED_NAN` / não-finitos em `build_figure_spec` | Pontos não-finitos são excluídos da série plotável e documentados explicitamente em `PlotSpecification.notes` | Evita que `NaN`/`Inf` corrompam escalas de eixos ou sejam coagidos a `0.0` (`ADR-005`) |
| HTML autocontido (`render_full_report`) | CSS embutido em `<style>`, zero links/CDNs externos, escape HTML seguro (`html.escape`) | Cumpre `RNF03` (100% offline) e previne quebra de layout |
| Declarações do Pesquisador opcionais | Aceita `ResearcherDeclarations` (objetivo, origem dos dados, notas) opcional; exibe aviso explícito caso não fornecidas | Permite gerar relatórios mesmo em execuções automatizadas sem perder a separação de responsabilidades |

## User Stories

### US-M72-01 (Priority: P1) — Especificação e Renderização Determinística de Figuras
As an experimental ML researcher,  
I want pure-Python/NumPy figure builders and deterministic SVG, 300-DPI PNG, and PDF renderers,  
So that publication-ready visualizations are reproducible without heavy external plotting dependencies.

#### Acceptance Criteria
- **AC-M72-01-01**: WHEN invoking `build_figure_spec` with `ReportFamily` and `LoadedExperimentData`, the system SHALL construct a valid `PlotSpecification` with relative `ArtifactProvenance`, excluding non-finite/`UNDEFINED_NAN` points from plotted series and documenting exclusions in `notes`.
- **AC-M72-01-02**: WHEN invoking `render_figure` with format `"svg"`, `"png"`, or `"pdf"`, the system SHALL produce valid, deterministic bytes (`<svg...` for SVG, PNG signature + `pHYs` 300 DPI chunk for PNG, and `%PDF-1.4` with `%%EOF` for PDF) using only stdlib and NumPy (`XCUT-02`).
- **AC-M72-01-03**: IF an unsupported format is passed to `render_figure`, THEN the system SHALL raise `ConfigurationError`.

---

### US-M72-02 (Priority: P1) — Relatório Científico Completo (Markdown e HTML Autocontido)
As an experimental ML researcher,  
I want a full scientific report generator in Markdown and self-contained HTML,  
So that researcher declarations, computational facts, and statistical interpretations are clearly separated and auditable.

#### Acceptance Criteria
- **AC-M72-02-01**: WHEN invoking `render_full_report` with `LoadedExperimentData` and format `"markdown"` or `"html"`, the system SHALL structure the report into three explicit sections: (1) Researcher Declarations, (2) Registered Computational Facts (including selected family tables and figure references), and (3) Derived & Conditioned Interpretations (`StructuredConclusion`).
- **AC-M72-02-02**: The system SHALL preserve exact numeric values from `statistics/*.json` (`CA-E6-01`), exclude technical `*_hash` fields (`CA-E6-02`), and embed CSS inline in HTML output with zero external network references (`RNF03`).
- **AC-M72-02-03**: IF an unsupported report format is passed to `render_full_report`, THEN the system SHALL raise `ConfigurationError`.

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| REP-04 | AC-M72-01-01, AC-M72-01-02, AC-M72-01-03 | `experimental_ml.reporting.figures` | pending |
| REP-05 | AC-M72-02-01, AC-M72-02-02, AC-M72-02-03 | `experimental_ml.reporting.report` | pending |
