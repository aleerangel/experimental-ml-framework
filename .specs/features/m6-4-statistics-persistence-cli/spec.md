# Feature: m6-4-statistics-persistence-cli

**Approved**: 2026-11-16 - user: "aprovado"

## Problem Statement

Com os submódulos analíticos 5A (M6.1), 5B (M6.2) e 5C (M6.3) implementados em memória sob `src/experimental_ml/statistics/`, falta ainda fechar a Etapa 5 do `experimental-ml-framework` com:
1. **Persistência Atômica e Codecs Tipados (`src/experimental_ml/statistics/storage.py`)**: Serializar e reconstruir com fidelidade estrita (inclusive `MetricStatus.UNDEFINED_NAN`, `float("inf")` em casos degenerados de variância nula, chaves compostas `(model_id, scenario_id)` e enums) os artefatos da Etapa 5 em `{experiment_dir}/statistics/`, utilizando escrita atômica (`STORE-03`) e proteção contra sobrescrita acidental (`STORE-05`).
2. **Portão de Estágio Stage 5 (`verify_statistics_gate` em `src/experimental_ml/stages/stage_gates.py`)**: Validar de forma determinística os portões upstream (Stage 4 / `verify_runs_gate`), a existência e integridade estrutural de todos os arquivos obrigatórios em `statistics/` e a consistência de linhagem (`partition_plan_id`, `experiment_id`), bloqueando o avanço para a Etapa 6 (`reporting`) caso qualquer pré-requisito falhe (`CA-GER-01`).
3. **Interface de Linha de Comando `expml stats` (`src/experimental_ml/cli/cmd_stats.py` e `cli/main.py`)**: Disponibilizar os subcomandos `run`, `status` e `verify` com códigos de saída padronizados (`0` sucesso, `2` erro de domínio/contrato sem traceback, `1` falha sistêmica — `CLI-06`), supressão de hashes criptográficos brutos na saída padrão (`CLI-11`) e isolamento de imports pesados no nível de módulo (`CLI-10`).

## Out of Scope

- Geração de tabelas CSV/Markdown/LaTeX, gráficos e relatórios completos da Etapa 6 (`experimental_ml.reporting`) — escopo do Marco M7.
- Inclusão de `scipy` ou qualquer dependência de runtime além de `numpy>=1.24.0` (`XCUT-02`).
- Acoplamento a qualquer domínio aplicado ou dados reais específicos (`RNF02`, `CA02`).

## Assumptions & Open Questions

**Open questions:** none - os contratos de persistência (`STORE-01`–`STORE-05`), portões de estágio (`CA-GER-01`) e ergonomia CLI (`CLI-06`–`CLI-11`) já estão estabelecidos e padronizados nos Marcos M1–M5.

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Estrutura de arquivos em `{experiment_dir}/statistics/` | `descriptive_consolidation.json`, `method_suitability.json`, `statistical_comparisons.json`, `structured_conclusion.json`, `statistics_manifest.json` e opcional `pareto_summary.json` | Separa cada artefato conceitual da Etapa 5 para leitura somente-leitura granular pela Etapa 6 (`CA-E6-01`) |
| Representação JSON de valores não-finitos (`NaN`/`Inf`) | Codificação explícita via marcadores JSON tipados (`{"__nonfinite__": "NaN" | "Inf" | "-Inf"}`) em `storage.py` | Preserva estrita conformidade RFC 8259 sem `allow_nan` silencioso nem coerção espúria para `0.0` (`ADR-005`) |
| Configuração padrão de `expml stats run` sem `--config` | Comparação `ALL_PAIRWISE` sobre todas as métricas `VALID` presentes nos resultados com `HOLM_BONFERRONI` e direção `MINIMIZE` padrão (ou sobreescrita via JSON `--config`) | Garante ergonomia imediata para o pesquisador sem exigir preenchimento manual de arquivo de configuração em casos padrão |
| Portão de estágio `verify_statistics_gate` | Verifica `verify_runs_gate` (se `runs/` presente), integridade dos arquivos em `statistics/` e alinhamento de `partition_plan_id` | Garante `CA-GER-01` antes da entrada na Etapa 6 |

## User Stories

### US-M64-01 (Priority: P1) — Persistência Atômica e Fidelidade de Roundtrip em `statistics/`
As an experimental ML researcher,  
I want atomic JSON persistence and faithful roundtrip loading for all Stage 5 statistical artifacts,  
So that Stage 6 reporting can consume verified results read-only without recomputing experiments.

#### Acceptance Criteria
- **AC-M64-01-01**: WHEN invoking `save_statistics_artifacts`, the system SHALL atomically write `descriptive_consolidation.json`, `method_suitability.json`, `statistical_comparisons.json`, `structured_conclusion.json`, `statistics_manifest.json`, and optional `pareto_summary.json` inside `{experiment_dir}/statistics/`.
- **AC-M64-01-02**: IF target files already exist in `statistics/` and `force=False`, THEN `save_statistics_artifacts` SHALL raise `ContractViolationError` or `ConfigurationError` without overwriting existing artifacts (`STORE-05`).
- **AC-M64-01-03**: WHEN invoking `load_statistics_artifacts`, the system SHALL reconstruct all Stage 5 frozen dataclasses with exact field, enum, tuple-key, and non-finite (`NaN`/`Inf`) fidelity.

---

### US-M64-02 (Priority: P1) — Portão de Estágio da Etapa 5 (`verify_statistics_gate`)
As an experimental ML researcher,  
I want a deterministic stage gate verifying Stage 5 completeness and upstream lineage,  
So that Stage 6 reporting is blocked if statistical artifacts are missing, corrupted, or misaligned with Stage 4.

#### Acceptance Criteria
- **AC-M64-02-01**: IF any required Stage 5 file (`descriptive_consolidation.json`, `method_suitability.json`, `statistical_comparisons.json`, `structured_conclusion.json`, `statistics_manifest.json`) is missing or unparseable, THEN `verify_statistics_gate` SHALL raise `DataIntegrityError`.
- **AC-M64-02-02**: IF `partition_plan_id` in `statistics/` artifacts diverges from the upstream `PartitionPlan` or `execution_state.json`, THEN `verify_statistics_gate` SHALL raise `DataIntegrityError`.
- **AC-M64-02-03**: WHEN all upstream Stage 4 gates and Stage 5 artifacts are valid and consistent, THEN `verify_statistics_gate` SHALL return a structured verification summary dictionary.

---

### US-M64-03 (Priority: P1) — Interface de Linha de Comando `expml stats`
As an experimental ML researcher,  
I want CLI subcommands `expml stats run`, `expml stats status`, and `expml stats verify`,  
So that I can execute, inspect, and audit Stage 5 statistical consolidation directly from the terminal.

#### Acceptance Criteria
- **AC-M64-03-01**: WHEN executing `expml stats run --experiment-dir <dir>` on a valid completed Stage 4 experiment, the system SHALL execute Stage 5 consolidation, suitability, comparisons, and synthesis, persist artifacts under `statistics/`, and exit with code `0` without printing raw cryptographic hashes (`CLI-11`).
- **AC-M64-03-02**: WHEN executing `expml stats status --experiment-dir <dir>`, the system SHALL display a read-only summary of coverage, executed/skipped comparisons, and observed leader, exiting with code `0` (or `2` if Stage 5 artifacts are absent).
- **AC-M64-03-03**: WHEN executing `expml stats verify --experiment-dir <dir>`, the system SHALL run `verify_statistics_gate`, exiting with code `0` when valid or `2` without traceback on integrity/contract errors (`CLI-06`).
- **AC-M64-03-04**: WHEN importing `experimental_ml.cli.main` or `experimental_ml.cli.cmd_stats`, the module SHALL NOT eagerly import heavy Stage 5 statistical submodules before command dispatch (`CLI-10`).

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| STAT-12 | AC-M64-01-01, AC-M64-01-02, AC-M64-01-03 | `experimental_ml.statistics.storage` | pending |
| STAT-13 | AC-M64-02-01, AC-M64-02-02, AC-M64-02-03 | `experimental_ml.stages.stage_gates` | pending |
| STAT-14 | AC-M64-03-01, AC-M64-03-02, AC-M64-03-03, AC-M64-03-04 | `experimental_ml.cli.cmd_stats`, `experimental_ml.cli.main` | pending |
