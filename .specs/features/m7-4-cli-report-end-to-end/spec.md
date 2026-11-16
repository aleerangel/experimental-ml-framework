# Feature: m7-4-cli-report-end-to-end

**Approved**: 2026-11-16 - user: "aprovado"

## Problem Statement

Com os contratos de tabelas (M7.1), figuras determinísticas e relatório científico completo (M7.2) e empacotamento de reprodutibilidade + portão `verify_report_gate` (M7.3) implementados e verificados, falta expor a **interface de linha de comando (`expml report`)** em `src/experimental_ml/cli/main.py` e validar o fluxo ponta a ponta completo (Estágio 1 até Estágio 6 — relatório e pacote verificado):

1. **`expml report generate`**: Gerar relatórios científicos (Markdown, HTML ou pacote completo de tabelas/figuras/relatórios) a partir de um diretório de experimento persistido (`--exp-dir`), respeitando seleção de audiência (`FULL_LAB`, `ARTICLE_COMPACT`, `CUSTOM`), famílias, modelos, cenários, métricas e declarações do pesquisador, operando exclusivamente em modo somente-leitura sobre os artefatos das Etapas 1–5 (`CA-E6-01`).
2. **`expml report export`**: Construir e exportar o pacote de reprodutibilidade (`tables/`, `figures/`, `reports/`, `reproducibility/`) nos modos `full_package` ou `reduced_no_raw_data` (`RF6.4`), com proteção `--force` / `force=False` (`STORE-05`).
3. **`expml report verify`**: Executar o portão de integridade Stage 6 (`verify_report_gate`), retornando código de saída `0` com resumo JSON estruturado quando íntegro e código de saída não-zero (`!= 0`) em caso de violação de integridade, ausência de artefato ou caminho não relativo (`CA-E6-02`).

## Out of Scope

- Alteração das lógicas estatísticas ou de execução das Etapas 1–5.
- Inclusão de dependências externas além de `numpy>=1.24.0` (`XCUT-02`).
- Acoplamento a qualquer domínio aplicado específico (`RNF02`, `CA02`).

## Assumptions & Open Questions

**Open questions:** none - os subcomandos `report generate`, `report export` e `report verify` seguem o mesmo padrão `argparse` e tratamento de exceções JSON de `src/experimental_ml/cli/main.py` (`data`, `partition`, `features`, `models`, `run`, `stats`).

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Estrutura de subcomandos CLI | `expml report {generate, export, verify}` em `src/experimental_ml/cli/main.py` | Consistência total com `data`, `partition`, `features`, `models`, `run`, `stats` |
| Diretório de saída padrão | `--output-dir` opcional (padrão: `<exp-dir>` no `export` e `<exp-dir>/reports` no `generate`) | Permite exportar in-place no experimento ou para um diretório isolado portátil |
| Modo padrão de exportação | `--mode full_package` ou `reduced_no_raw_data` (padrão `full_package`) | Alinhado diretamente com `PackageMode` de M7.3 e `RF6.4` |

## User Stories

### US-M74-01 (Priority: P1) — Subcomandos CLI `expml report generate` e `expml report export`
As an experimental ML researcher,  
I want CLI commands `expml report generate` and `expml report export` on `expml`,  
So that I can generate scientific reports and export portable reproducibility packages from the terminal without invoking model training.

#### Acceptance Criteria
- **AC-M74-01-01**: WHEN invoking `expml report generate --exp-dir <dir> [--audience ...] [--format markdown|html] [--output-dir <out>] [--force]`, the CLI SHALL load Stage 1–5 artifacts read-only and write `report.md` and/or `report.html` deterministically, exiting with code `0` and JSON summary.
- **AC-M74-01-02**: WHEN invoking `expml report export --exp-dir <dir> [--output-dir <out>] [--mode full_package|reduced_no_raw_data] [--force]`, the CLI SHALL build the complete reproducibility package (`tables/`, `figures/`, `reports/`, `reproducibility/`) and exit with code `0` and JSON manifest summary.
- **AC-M74-01-03**: IF destination artifacts already exist and `--force` is not passed, THEN `expml report generate` and `expml report export` SHALL exit with non-zero status (`ContractViolationError`) without overwriting existing files (`STORE-05`).

---

### US-M74-02 (Priority: P1) — Subcomando CLI `expml report verify` e Integração E2E
As an experimental ML researcher,  
I want `expml report verify --exp-dir <dir>` and an end-to-end pipeline test from Stage 1 to Stage 6,  
So that package integrity, 1-byte tamper detection, and full pipeline reproducibility are verified via CLI.

#### Acceptance Criteria
- **AC-M74-02-01**: WHEN invoking `expml report verify --exp-dir <dir>` on a valid package (including after moving the directory), the CLI SHALL exit with code `0` and print a JSON summary with `"status": "VERIFIED"`.
- **AC-M74-02-02**: IF any file is missing, tampered by 1 byte, or contains a non-relative path, THEN `expml report verify --exp-dir <dir>` SHALL exit with non-zero status (`DataIntegrityError`).
- **AC-M74-02-03**: WHEN running an end-to-end synthetic experiment from Stage 1 (`data`) through Stage 6 (`report export` + `report verify`), all stages SHALL complete and pass `verify_report_gate` with zero external runtime dependencies beyond `numpy` (`XCUT-02`).

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| REP-08 | AC-M74-01-01, AC-M74-01-02, AC-M74-01-03 | `experimental_ml.cli.main` | pending |
| REP-09 | AC-M74-02-01, AC-M74-02-02, AC-M74-02-03 | `experimental_ml.cli.main`, E2E Stage 1–6 | pending |
