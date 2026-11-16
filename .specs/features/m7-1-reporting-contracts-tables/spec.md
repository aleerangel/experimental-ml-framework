# Feature: m7-1-reporting-contracts-tables

**Approved**: 2026-11-16 - user: "aprovado"

## Problem Statement

Na arquitetura do `experimental-ml-framework`, a Etapa 6 (`experimental_ml.reporting`, Marco M7) tem como responsabilidade consumir exclusivamente em modo **somente-leitura** os artefatos persistidos das Etapas 1 a 5 para gerar tabelas científicas, visualizações, relatórios completos e pacotes de reprodutibilidade, mantendo paridade numérica estrita com `statistics/*.json` (`CA-E6-01`) e mantendo hashes técnicos `SHA-256` restritos aos arquivos internos de auditoria sem poluir as tabelas científicas (`CA-E6-02`).

Atualmente, o pacote `src/experimental_ml/reporting/` ainda não existe. Este Sub-marco M7.1 estabelece o alicerce contratual e tabular da Etapa 6:
1. **Contratos Imutáveis de Publicação (`types.py`)**: Enumerações (`ReportFamily` A–G, `ReportAudience`, `PlotType`, `ColumnAlignment`) e dataclasses congeladas (`ReportContentSelection`, `TableColumn`, `TableModel`, `PlotSeries`, `PlotSpecification`, `ArtifactProvenance`, `LoadedExperimentData`), garantindo imutabilidade e rastreabilidade completa (`RF6.3`).
2. **Carregamento Somente-Leitura e Seleção de Conteúdo (`loader.py`, `select_report_content`)**: Leitura estrita dos artefatos persistidos das Etapas 1–5 (validada via `verify_statistics_gate`) sem jamais importar ou invocar funções de ajuste/predição de modelos (`CA-E6-01`), com critérios determinísticos e explícitos para `FULL_LAB`, `ARTICLE_COMPACT` e `CUSTOM` (`RF6.1`).
3. **Construtores de Tabelas das 7 Famílias e Renderizadores Puros (`tables.py`)**: `build_table_model` cobrindo todas as 7 famílias (`A` a `G` — `RF6.2`), preservando em `TableModel.rows` os valores numéricos exatos de `statistics/*.json` sem recálculo ou arredondamento (`CA-E6-01`), distinguindo rigorosamente `None` (`"N/A"`), `MetricStatus.UNDEFINED_NAN` (`"UNDEFINED_NAN"`) e infinitos (`"Inf"` / `"-Inf"`) sem coerção para zero (`ADR-005`), excluindo campos estruturais de hash (`*_hash`, `*_digest`, `checksum`) das tabelas (`CA-E6-02`), e renderizadores determinísticos `render_table_csv`, `render_table_markdown` e `render_table_latex` (padrão `booktabs`).

## Out of Scope

- Renderização de figuras (`render_figure` em PNG/SVG/PDF) e composição do Relatório Científico Completo (`render_full_report` em Markdown/HTML) — escopo do Sub-marco M7.2.
- Empacotamento de reprodutibilidade (`build_reproducibility_package`, `checksums.sha256`, `REPRODUCE.md`) e portão `verify_report_gate` — escopo do Sub-marco M7.3.
- Interface CLI `expml report` (`generate`, `export`, `verify`) — escopo do Sub-marco M7.4.
- Inclusão de dependências externas de runtime além de `numpy>=1.24.0` (`XCUT-02`).
- Acoplamento a qualquer domínio aplicado ou dados reais específicos (`RNF02`, `CA02`).

## Assumptions & Open Questions

**Open questions:** none - os contratos de `TableModel`, `PlotSpecification`, `ArtifactProvenance`, as 7 famílias (A–G), os formatos de saída (`.csv`, `.md`, `.tex` `booktabs`) e as garantias `CA-E6-01`/`CA-E6-02` estão formalmente especificados em `ARQUITETURA_E_CONTRATOS.md` (Seção 3.6) e `ESPECIFICACAO_REQUISITOS.md` (`RF6.1`–`RF6.3`).

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Dependência de runtime | Apenas Python padrão (`csv`, `json`, `dataclasses`) e `numpy>=1.24.0` | Cumpre `XCUT-02` e `RNF03` mantendo geração 100% determinística e offline |
| Ocultação de hashes SHA-256 (`CA-E6-02`) | Exclusão estrutural explícita de campos técnicos de hash/digest (`*_hash`, `*_digest`, `sha256`, `checksum`) e metadados internos de auditoria na construção de `TableModel` | Preserva conteúdo legítimo do usuário sem falsos positivos de regex e garante `CA-E6-02` |
| Distinção entre ausentes, `UNDEFINED_NAN` e não-finitos (`ADR-005`) | `None` (dado ausente/não aplicável, ex.: `std=None` em $n=1$) $\to$ `"N/A"`; `MetricStatus.UNDEFINED_NAN` / `NaN` $\to$ `"UNDEFINED_NAN"`; `+Inf`/`-Inf` $\to$ `"Inf"`/`"-Inf"` | Impede transformar ausência de dado ou dispersão inexistente em indefinição matemática ou zero |
| Paridade numérica (`CA-E6-01`) | `TableModel.rows` armazena os valores numéricos exatos (`float`/`int`) de `statistics/*.json` sem arredondamento; formatação visual (`numeric_format`) ocorre apenas nos renderizadores de texto (`Markdown`/`LaTeX`) | Garante paridade numérica exata na estrutura de dados e no CSV sem perda de precisão |
| Critérios de `ReportAudience` (`FULL_LAB`, `ARTICLE_COMPACT`, `CUSTOM`) | `FULL_LAB` seleciona todas as 7 famílias (A–G) e todos os IDs ordenados; `ARTICLE_COMPACT` seleciona as famílias centrais (D, E, F); `CUSTOM` exige e aplica seleção explícita de famílias/IDs | Comportamento 100% determinístico e coerente com `ARQUITETURA §3.6` (visão completa vs. recorte enxuto) |
| Formatação LaTeX (`render_table_latex`) | Ambiente `table` / `tabular` com `\toprule`, `\midrule`, `\bottomrule` (`booktabs`) e escape de `_`, `%`, `&`, `#`, `$` | Cumpre `RF6.1` com código LaTeX compilável imediatamente |
| Caminhos em `ArtifactProvenance` (`CA-E6-02`) | Exclusivamente caminhos relativos ao diretório do experimento | Garante portabilidade do pacote entre máquinas e diretórios |

## User Stories

### US-M71-01 (Priority: P1) — Contratos Imutáveis e Proveniência de Artefatos
As an experimental ML researcher,  
I want immutable, typed data structures for report content selection, tables, plots, and artifact provenance,  
So that every exported scientific artifact is self-describing, traceable, and immutable.

#### Acceptance Criteria
- **AC-M71-01-01**: The system SHALL provide enumerations `ReportFamily` (`A_DATA_CHARACTERIZATION`, `B_FEATURE_SCENARIOS`, `C_MODELS_CONFIG`, `D_PREDICTIVE_PERFORMANCE`, `E_STATISTICAL_COMPARISONS`, `F_STABILITY_COST_PARETO`, `G_MODEL_SPECIFIC_ARTIFACTS`), `ReportAudience` (`FULL_LAB`, `ARTICLE_COMPACT`, `CUSTOM`), `PlotType`, and `ColumnAlignment`.
- **AC-M71-01-02**: The system SHALL provide frozen dataclasses `ReportContentSelection`, `TableColumn`, `TableModel`, `PlotSeries`, `PlotSpecification`, `ArtifactProvenance`, and `LoadedExperimentData` with structural validations and `FrozenInstanceError` on mutation.
- **AC-M71-01-03**: IF any path inside `ArtifactProvenance.source_relative_paths` is an absolute path, THEN the system SHALL raise `ContractViolationError`.

---

### US-M71-02 (Priority: P1) — Carregamento Somente-Leitura e Seleção de Conteúdo
As an experimental ML researcher,  
I want a read-only loader and content filter operating purely on persisted Stage 1–5 artifacts,  
So that reporting never retrains models and supports compact vs. full laboratory views.

#### Acceptance Criteria
- **AC-M71-02-01**: WHEN invoking `load_experiment_artifacts_readonly` on an experiment directory, the system SHALL verify `verify_statistics_gate` and load persisted artifacts without importing or invoking model fitting/prediction modules (`CA-E6-01`).
- **AC-M71-02-02**: WHEN invoking `select_report_content`, the system SHALL apply deterministic filtering according to `ReportAudience`: `FULL_LAB` (all families A–G and all sorted IDs), `ARTICLE_COMPACT` (families D, E, F with optional ID filters), and `CUSTOM` (explicit non-empty family selection and ID filters).

---

### US-M71-03 (Priority: P1) — Tabelas das 7 Famílias e Renderização (CSV, Markdown, LaTeX)
As an experimental ML researcher,  
I want pure table builders for all 7 families (A–G) and renderers for CSV, Markdown, and LaTeX `booktabs`,  
So that tables match `statistics/*.json` numerically, hide technical hash fields, and are ready for publication.

#### Acceptance Criteria
- **AC-M71-03-01**: WHEN invoking `build_table_model` for each of the 7 `ReportFamily` values (`A` through `G`), the system SHALL construct a valid `TableModel` with attached `ArtifactProvenance` using exclusively relative source paths.
- **AC-M71-03-02**: The system SHALL store exact unrounded numeric values from `statistics/*.json` inside `TableModel.rows` (`CA-E6-01`), and SHALL distinguish `None` (`"N/A"`), `MetricStatus.UNDEFINED_NAN`/`NaN` (`"UNDEFINED_NAN"`), and `±Inf` (`"Inf"`/`"-Inf"`) without zero coercion (`ADR-005`).
- **AC-M71-03-03**: The system SHALL structurally exclude technical hash/digest fields (`*_hash`, `*_digest`, `sha256`, `checksum`) from all user-facing `TableModel` columns, rows, and notes without stripping legitimate user identifiers (`CA-E6-02`).
- **AC-M71-03-04**: WHEN invoking `render_table_csv`, `render_table_markdown`, and `render_table_latex`, the system SHALL output deterministic RFC 4180 CSV (preserving full numeric precision), aligned GitHub Markdown, and LaTeX `booktabs` (`\toprule`, `\midrule`, `\bottomrule` with escaped special characters) respectively, applying `numeric_format` only during text presentation.

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| REP-01 | AC-M71-01-01, AC-M71-01-02, AC-M71-01-03 | `experimental_ml.reporting.types` | pending |
| REP-02 | AC-M71-02-01, AC-M71-02-02 | `experimental_ml.reporting.loader` | pending |
| REP-03 | AC-M71-03-01, AC-M71-03-02, AC-M71-03-03, AC-M71-03-04 | `experimental_ml.reporting.tables` | pending |
