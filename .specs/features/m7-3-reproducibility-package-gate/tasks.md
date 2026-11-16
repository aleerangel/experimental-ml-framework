# m7-3-reproducibility-package-gate Tasks (M7.3 Pacote de Reprodutibilidade e Portão Stage 6)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m7-3-reproducibility-package-gate/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-16 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/reporting/ tests/unit/stages/test_stage_report_gate.py tests/integration/reporting/ -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Reproducibility Packaging (`src/experimental_ml/reporting/packaging.py`, `types.py`) | unit | `PackageMode`, `ReproducibilityPackageManifest`, `build_reproducibility_package` (`tables/`, `figures/`, `reports/`, `reproducibility/`), caminhos 100% relativos, `REDUCED_NO_RAW_DATA` vs `FULL_PACKAGE`, proteção `force=False` | `tests/unit/reporting/test_reporting_packaging.py` | `.venv/bin/pytest tests/unit/reporting/test_reporting_packaging.py -v` |
| Stage 6 Gate (`src/experimental_ml/stages/stage_gates.py`) | unit | `verify_report_gate` (portabilidade após mover diretório, validação upstream Stage 5, detecção de 1 byte / ausência / cobertura incompleta, rejeição de caminhos absolutos e `..` traversal) | `tests/unit/stages/test_stage_report_gate.py` | `.venv/bin/pytest tests/unit/stages/test_stage_report_gate.py -v` |
| Integration & Purity (`tests/integration/reporting/test_m73_integration.py`) | integration | Fluxo `load_experiment_artifacts_readonly` -> `build_reproducibility_package` -> mover diretório -> `verify_report_gate` e pureza runtime `XCUT-02` | `tests/integration/reporting/test_m73_integration.py` | `.venv/bin/pytest tests/integration/reporting/test_m73_integration.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After unit tasks | `.venv/bin/pytest tests/unit/reporting/ tests/unit/stages/test_stage_report_gate.py -v` |
| Full | After integration task | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/unit/reporting/ tests/unit/stages/test_stage_report_gate.py -v` |

---

## Execution Plan

### Phase 1: Contratos e Empacotamento de Reprodutibilidade (`P1`)

```
T1
```

### Phase 2: Portão de Estágio Stage 6 (`P2`)

```
T1 --> T2
```

### Phase 3: API Pública e Integração (`P3`)

```
T2 --> T3
```

---

## Task Breakdown

### Phase 1: Contratos e Empacotamento de Reprodutibilidade

#### T1: Implementar PackageMode, ReproducibilityPackageManifest e build_reproducibility_package [x]

**What**: Adicionar `PackageMode` (`FULL_PACKAGE`, `REDUCED_NO_RAW_DATA`) e `ReproducibilityPackageManifest` em `src/experimental_ml/reporting/types.py`, e criar `src/experimental_ml/reporting/packaging.py` com `build_reproducibility_package` exportando `tables/`, `figures/`, `reports/` (`report.md`, `report.html`) e `reproducibility/` (`artifact_provenance.json`, `checksums.sha256`, `environment.json`, `seeds.json`, `REPRODUCE.md`) com escrita atômica, caminhos 100% relativos POSIX, exclusão de dados brutos em `REDUCED_NO_RAW_DATA` e proteção `force=False` (`ContractViolationError`). Adicionar testes em `tests/unit/reporting/test_reporting_packaging.py`.  
**Where**: `src/experimental_ml/reporting/packaging.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/reporting/tables.py`, `figures.py`, `report.py`, `src/experimental_ml/core/storage.py` (`write_json_atomic`)  
**Requirement**: REP-06  
**Tests**: `tests/unit/reporting/test_reporting_packaging.py`  
**Gate**: `.venv/bin/pytest tests/unit/reporting/test_reporting_packaging.py -v`

---

### Phase 2: Portão de Estágio Stage 6

#### T2: Implementar verify_report_gate em stage_gates.py [x]

**What**: Implementar `verify_report_gate` em `src/experimental_ml/stages/stage_gates.py`, validando upstream Stage 5 (`verify_statistics_gate`) quando `statistics/` estiver presente em `exp_dir`, checando ausência de caminhos absolutos ou `..` traversal em `artifact_provenance.json` e `checksums.sha256`, garantindo cobertura de 100% dos artefatos de `artifact_provenance.json` e recalculando SHA-256 byte-a-byte (lançando `DataIntegrityError` em qualquer divergência ou ausência). Adicionar testes em `tests/unit/stages/test_stage_report_gate.py`.  
**Where**: `src/experimental_ml/stages/stage_gates.py`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/stages/stage_gates.py` (`verify_statistics_gate`), `src/experimental_ml/core/storage.py` (`read_json`)  
**Requirement**: REP-07  
**Tests**: `tests/unit/stages/test_stage_report_gate.py`  
**Gate**: `.venv/bin/pytest tests/unit/stages/test_stage_report_gate.py -v`

---

### Phase 3: API Pública e Integração

#### T3: Expor API pública de M7.3 e validar integração e pureza XCUT-02 [ ]

**What**: Atualizar `src/experimental_ml/reporting/__init__.py` exportando `PackageMode`, `ReproducibilityPackageManifest` e `build_reproducibility_package`. Criar `tests/integration/reporting/test_m73_integration.py` validando fluxo completo de empacotamento, portabilidade após mover diretório raiz, `verify_report_gate` e pureza runtime `XCUT-02`.  
**Where**: `src/experimental_ml/reporting/__init__.py`  
**Depends on**: T2  
**Reuses**: `src/experimental_ml/reporting/packaging.py`, `src/experimental_ml/stages/stage_gates.py`  
**Requirement**: REP-06, REP-07  
**Tests**: `tests/integration/reporting/test_m73_integration.py`  
**Gate**: `.venv/bin/pytest tests/unit/reporting/ tests/unit/stages/test_stage_report_gate.py tests/integration/reporting/ -v`

---

## Checks

**C1** - `PackageMode` (`FULL_PACKAGE`, `REDUCED_NO_RAW_DATA`) e `ReproducibilityPackageManifest` congelado definidos em `types.py`. (REP-06, AC-M73-01-01)  
Proof: run unit | tests/unit/reporting/test_reporting_packaging.py::test_m73_01_manifest_and_mode PASSED

**C2** - `build_reproducibility_package` exporta `tables/`, `figures/`, `reports/` e `reproducibility/` com caminhos 100% relativos POSIX e `checksums.sha256` ordenado. (REP-06, AC-M73-01-02)  
Proof: run unit | tests/unit/reporting/test_reporting_packaging.py::test_m73_01_relative_paths_and_structure PASSED

**C3** - Modo `REDUCED_NO_RAW_DATA` exclui dados brutos e documenta nível de reprodução em `REPRODUCE.md`. (REP-06, AC-M73-01-03)  
Proof: run unit | tests/unit/reporting/test_reporting_packaging.py::test_m73_01_reduced_mode_excludes_raw_data PASSED

**C4** - Sobrescrita com `force=False` lança `ContractViolationError` sem alterar arquivos existentes (`STORE-05`). (REP-06, AC-M73-01-04)  
Proof: run unit | tests/unit/reporting/test_reporting_packaging.py::test_m73_01_force_false_protects_overwrite PASSED

**C5** - `verify_report_gate` valida pacote completo e permanece aprovado após mover/renomear o diretório raiz. (REP-07, AC-M73-02-01)  
Proof: run unit | tests/unit/stages/test_stage_report_gate.py::test_m73_02_valid_and_portable_after_move PASSED

**C6** - Alteração de 1 byte, arquivo ausente ou artefato não listado em `checksums.sha256` lança `DataIntegrityError`. (REP-07, AC-M73-02-02)  
Proof: run unit | tests/unit/stages/test_stage_report_gate.py::test_m73_02_tampering_or_missing_raises PASSED

**C7** - Caminhos absolutos ou `..` traversal em `checksums.sha256` ou `artifact_provenance.json` lançam `DataIntegrityError`. (REP-07, AC-M73-02-03)  
Proof: run unit | tests/unit/stages/test_stage_report_gate.py::test_m73_02_absolute_or_traversal_rejected PASSED

**C8** - Fluxo integrado empacotamento -> movimentação de diretório -> `verify_report_gate` aprovado e módulo `packaging.py` puro conforme `XCUT-02`. (REP-06, REP-07, AC-M73-01-02, AC-M73-02-01)  
Proof: run unit | tests/integration/reporting/test_m73_integration.py::test_m73_end_to_end_packaging_and_gate PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T1
- **Next Task:** T2
