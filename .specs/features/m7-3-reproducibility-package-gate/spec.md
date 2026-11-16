# Feature: m7-3-reproducibility-package-gate

**Approved**: 2026-11-16 - user: "aprovado"

## Problem Statement

Com os construtores/renderizadores de tabelas (M7.1), figuras determinísticas e relatório completo (M7.2) implementados em `src/experimental_ml/reporting/`, a Etapa 6 necessita agora do subsistema de **Empacotamento de Reprodutibilidade (`packaging.py`)** e do **Portão de Estágio Stage 6 (`verify_report_gate`)** para cumprir integralmente `RF6.3`, `RF6.4`, `CA-E6-02` e `CA-GER-01`:

1. **`build_reproducibility_package` (`packaging.py`)**: Exportar de forma atômica os artefatos de publicação (`tables/`, `figures/`, `reports/`) juntamente com o diretório `reproducibility/` contendo `artifact_provenance.json`, `checksums.sha256`, `environment.json`, `seeds.json` e `REPRODUCE.md`, utilizando exclusivamente **caminhos relativos** ao diretório raiz do pacote, suportando modos `FULL_PACKAGE` e `REDUCED_NO_RAW_DATA` (sem dados sensíveis/brutos) e proteção contra sobrescrita (`force=False`).
2. **`verify_report_gate` (`stage_gates.py`)**: Validar o portão upstream Stage 5 (`verify_statistics_gate`), verificar que 100% dos artefatos exportados constam em `artifact_provenance.json` e `checksums.sha256` com caminhos estritamente relativos (garantindo portabilidade após mover o diretório), e recalcular o SHA-256 de cada arquivo, falhando com `DataIntegrityError` se qualquer arquivo estiver ausente ou tiver sofrido alteração de 1 byte (`CA-E6-02`).

## Out of Scope

- Interface de linha de comando `expml report` (`generate`, `export`, `verify`) e integração ponta a ponta CLI — escopo do Sub-marco M7.4.
- Inclusão de dependências externas de runtime além de `numpy>=1.24.0` (`XCUT-02`).
- Acoplamento a qualquer domínio aplicado ou dados reais específicos (`RNF02`, `CA02`).

## Assumptions & Open Questions

**Open questions:** none - a estrutura de diretórios (`tables/`, `figures/`, `reports/`, `reproducibility/`), os arquivos de auditoria (`artifact_provenance.json`, `checksums.sha256`, `environment.json`, `seeds.json`, `REPRODUCE.md`), a portabilidade por caminhos relativos e a detecção de alteração de 1 byte estão formalmente definidos em `ARQUITETURA_E_CONTRATOS.md` (Seção 3.6 e Tabela 7.1 `TA-M7.2`) e `ESPECIFICACAO_REQUISITOS.md` (`RF6.3`, `RF6.4`, `CA-E6-02`).

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Formato de `reproducibility/checksums.sha256` | Linhas canônicas `<64-hex>  <relative_posix_path>` ordenadas lexicograficamente pelo caminho relativo | Compatível com `sha256sum -c` padrão POSIX e 100% portável entre máquinas/diretórios |
| Modos de exportação (`PackageMode`) | `FULL_PACKAGE` e `REDUCED_NO_RAW_DATA` (exclui `data/` bruto ao exportar pacote compartilhável) | Cumpre `RF6.4` permitindo compartilhamento seguro sob restrição de dados sensíveis |
| Verificação de portabilidade em `verify_report_gate` | Rejeita qualquer caminho absoluto (POSIX ou Windows) ou `..` traversal em `checksums.sha256` e `artifact_provenance.json` | Garante `CA-E6-02` e aprovação após mover o diretório de experimento |
| Proteção contra sobrescrita | `force: bool = False` lança `ContractViolationError` se artefatos de destino já existirem | Cumpre `STORE-05` evitando perda acidental de pacotes publicados |

## User Stories

### US-M73-01 (Priority: P1) — Empacotamento de Reprodutibilidade e Proveniência
As an experimental ML researcher,  
I want an automated reproducibility packager exporting tables, figures, reports, provenance, environment, seeds, and relative SHA-256 checksums,  
So that my experiment results are portable, self-contained, and auditable.

#### Acceptance Criteria
- **AC-M73-01-01**: The system SHALL provide enum `PackageMode` (`FULL_PACKAGE`, `REDUCED_NO_RAW_DATA`) and frozen dataclass `ReproducibilityPackageManifest`.
- **AC-M73-01-02**: WHEN invoking `build_reproducibility_package` on `LoadedExperimentData`, the system SHALL write `tables/`, `figures/`, `reports/` (`report.md`, `report.html`), and `reproducibility/` (`artifact_provenance.json`, `checksums.sha256`, `environment.json`, `seeds.json`, `REPRODUCE.md`) with 100% relative POSIX paths.
- **AC-M73-01-03**: IF `mode == PackageMode.REDUCED_NO_RAW_DATA`, THEN `build_reproducibility_package` SHALL exclude raw/sanitized dataset files from the exported package and document the reproduction level in `REPRODUCE.md`.
- **AC-M73-01-04**: IF destination files already exist and `force=False`, THEN `build_reproducibility_package` SHALL raise `ContractViolationError` without overwriting (`STORE-05`).

---

### US-M73-02 (Priority: P1) — Portão de Integridade Stage 6 (`verify_report_gate`)
As an experimental ML researcher,  
I want a deterministic stage gate verifying provenance coverage, relative paths, and byte-level SHA-256 checksums,  
So that any missing, unregistered, or 1-byte-modified artifact is immediately detected even after moving the directory.

#### Acceptance Criteria
- **AC-M73-02-01**: WHEN invoking `verify_report_gate` on a valid package directory (including after moving/renaming the root directory), the system SHALL verify all checksums and provenance entries and return a structured verification summary dictionary.
- **AC-M73-02-02**: IF any file in `checksums.sha256` is missing, modified by 1 byte, or any artifact in `artifact_provenance.json` lacks a checksum entry, THEN `verify_report_gate` SHALL raise `DataIntegrityError`.
- **AC-M73-02-03**: IF `checksums.sha256` or `artifact_provenance.json` contains any absolute path or parent-traversal (`..`), THEN `verify_report_gate` SHALL raise `DataIntegrityError`.

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| REP-06 | AC-M73-01-01, AC-M73-01-02, AC-M73-01-03, AC-M73-01-04 | `experimental_ml.reporting.packaging` | pending |
| REP-07 | AC-M73-02-01, AC-M73-02-02, AC-M73-02-03 | `experimental_ml.stages.stage_gates` | pending |
