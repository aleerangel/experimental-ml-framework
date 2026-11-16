# M7.3 Results — `m7-3-reproducibility-package-gate`

## Summary

- **PackageMode & ReproducibilityPackageManifest** (`src/experimental_ml/reporting/types.py`): Contratos imutáveis com validação de caminhos relativos POSIX.
- **build_reproducibility_package** (`src/experimental_ml/reporting/packaging.py`): Exportação atômica de `tables/`, `figures/`, `reports/` (`report.md`, `report.html`) e `reproducibility/` (`artifact_provenance.json`, `checksums.sha256`, `environment.json`, `seeds.json`, `REPRODUCE.md`), suportando `FULL_PACKAGE` e `REDUCED_NO_RAW_DATA` com proteção `force=False` (`ContractViolationError`).
- **verify_report_gate** (`src/experimental_ml/stages/stage_gates.py`): Validação upstream de Stage 5 quando `statistics/` está presente, rejeição de caminhos absolutos ou `..` traversal, cobertura de 100% em `artifact_provenance.json` e verificação SHA-256 byte-a-byte (`DataIntegrityError`).

## Verification

- `check_proofs.py m7-3-reproducibility-package-gate`: **8 pass, 0 fail**
- `.venv/bin/pytest tests/ -q`: **575 passed in 13.64s**
- `verification.md`: **PASS**
