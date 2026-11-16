# Verification Report: `m7-3-reproducibility-package-gate`

**Verdict**: `PASS`

## Checks

| Check | Criterion | Test | Holds |
| --- | --- | --- | --- |
| C1 | `PackageMode` (`FULL_PACKAGE`, `REDUCED_NO_RAW_DATA`) e `ReproducibilityPackageManifest` congelado definidos em `types.py`. (REP-06, AC-M73-01-01) | `tests/unit/reporting/test_reporting_packaging.py::test_m73_01_manifest_and_mode` | Yes |
| C2 | `build_reproducibility_package` exporta `tables/`, `figures/`, `reports/` e `reproducibility/` com caminhos 100% relativos POSIX e `checksums.sha256` ordenado. (REP-06, AC-M73-01-02) | `tests/unit/reporting/test_reporting_packaging.py::test_m73_01_relative_paths_and_structure` | Yes |
| C3 | Modo `REDUCED_NO_RAW_DATA` exclui dados brutos e documenta nível de reprodução em `REPRODUCE.md`. (REP-06, AC-M73-01-03) | `tests/unit/reporting/test_reporting_packaging.py::test_m73_01_reduced_mode_excludes_raw_data` | Yes |
| C4 | Sobrescrita com `force=False` lança `ContractViolationError` sem alterar arquivos existentes (`STORE-05`). (REP-06, AC-M73-01-04) | `tests/unit/reporting/test_reporting_packaging.py::test_m73_01_force_false_protects_overwrite` | Yes |
| C5 | `verify_report_gate` valida pacote completo e permanece aprovado após mover/renomear o diretório raiz. (REP-07, AC-M73-02-01) | `tests/unit/stages/test_stage_report_gate.py::test_m73_02_valid_and_portable_after_move` | Yes |
| C6 | Alteração de 1 byte, arquivo ausente ou artefato não listado em `checksums.sha256` lança `DataIntegrityError`. (REP-07, AC-M73-02-02) | `tests/unit/stages/test_stage_report_gate.py::test_m73_02_tampering_or_missing_raises` | Yes |
| C7 | Caminhos absolutos ou `..` traversal em `checksums.sha256` ou `artifact_provenance.json` lançam `DataIntegrityError`. (REP-07, AC-M73-02-03) | `tests/unit/stages/test_stage_report_gate.py::test_m73_02_absolute_or_traversal_rejected` | Yes |
| C8 | Fluxo integrado empacotamento -> movimentação de diretório -> `verify_report_gate` aprovado e módulo `packaging.py` puro conforme `XCUT-02`. (REP-06, REP-07, AC-M73-01-02, AC-M73-02-01) | `tests/integration/reporting/test_m73_integration.py::test_m73_end_to_end_packaging_and_gate` | Yes |

## Evidence Summary

- **Implementation**:
  - `src/experimental_ml/reporting/types.py` defines `PackageMode(StrEnum)` (`FULL_PACKAGE`, `REDUCED_NO_RAW_DATA`) and frozen dataclass `ReproducibilityPackageManifest` enforcing relative POSIX paths.
  - `src/experimental_ml/reporting/packaging.py` implements `build_reproducibility_package` exporting `tables/`, `figures/`, `reports/` (`report.md`, `report.html`), optional `data/` only in `FULL_PACKAGE` mode, and `reproducibility/` (`artifact_provenance.json`, `checksums.sha256`, `environment.json`, `seeds.json`, `REPRODUCE.md`) with atomic writes, sorted relative SHA-256 entries, and `force=False` overwrite protection (`ContractViolationError`).
  - `src/experimental_ml/reporting/__init__.py` exports `PackageMode`, `ReproducibilityPackageManifest`, and `build_reproducibility_package`.
  - `src/experimental_ml/stages/stage_gates.py` implements `verify_report_gate`, validating upstream `verify_statistics_gate` when `statistics/` is present, rejecting absolute paths and `..` traversal, verifying 100% provenance coverage in `checksums.sha256`, and recomputing byte-level SHA-256 hashes (raising `DataIntegrityError` on any mismatch or missing file).
- **Test Execution**:
  - `.venv/bin/pytest tests/unit/reporting/test_reporting_packaging.py tests/unit/stages/test_stage_report_gate.py tests/integration/reporting/test_m73_integration.py -v`: **8 passed** in 1.06s.
  - `python3 .agent/skills/tlc-spec-driven/scripts/check_proofs.py m7-3-reproducibility-package-gate`: **8 pass, 0 fail** (HEAD `880da31`, clean tree).

## Findings

None - all 8 checks (C1-C8) verified with 575 passing tests and clean `check_proofs.py` output.
