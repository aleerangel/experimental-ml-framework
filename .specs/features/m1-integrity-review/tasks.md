# m1-integrity-review Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m1-integrity-review/design.md`
**Status**: Draft
**Approved**: pending
**Build**: none - Read-only project integrity review; verification executed via pytest audit checks and non-interference diff gate
**Run audit**: .venv/bin/pytest .specs/features/m1-integrity-review/probes/test_audit_checks.py -v

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md` (AD-002) and read-only audit constraints in `.specs/features/m1-integrity-review/spec.md`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Audit Probes & Dimensional Reports (`.specs/features/m1-integrity-review/reports/*.md`) | integration | 1:1 AC mapping across all 48 criteria (`AUD`, `ARCH`, `INT`, `QUAL`, `TEST`, `DOC`, `READY`) with reproducible evidence | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` | `.venv/bin/pytest .specs/features/m1-integrity-review/probes/test_audit_checks.py -v` |
| Audit Verification Suite (`.specs/features/m1-integrity-review/probes/test_audit_checks.py`) | unit | All 48 checks (`C1`..`C48`) pass and verify non-interference (`git diff` empty on project files) | `.specs/features/m1-integrity-review/probes/test_audit_checks.py` | `.venv/bin/pytest .specs/features/m1-integrity-review/probes/test_audit_checks.py -v` |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | After probe or report creation | `.venv/bin/pytest tests/ -q` |
| Full | After audit verification suite updates | `.venv/bin/pytest .specs/features/m1-integrity-review/probes/test_audit_checks.py -v` |
| Build | After phase completion and final non-interference check | `.venv/bin/pytest tests/ -v` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Dimensional Probes & Technical Audit Reports (Dimensions A, B, C, D, E)

Execute non-intrusive probes and generate the baseline, specification criteria, architectural, integration, implementation quality, testing strategy, and documentation/traceability reports.

```
T1 → T2 → T3 → T4
```

### Phase 2: Findings Register, Prioritized Remediation Plan, M2 Readiness Verdict & Proof Suite (Dimension F)

Consolidate all findings with evidence and severity, build the prioritized remediation plan, compute the M2 readiness verdict, and execute the 48-check automated verification harness.

```
T5 → T6 → T7
```

---

## Task Breakdown

### Phase 1: Dimensional Probes & Technical Audit Reports (Dimensions A, B, C, D, E)

### T1: Execute baseline capture and Dimension A architectural integrity audit (`02-arquitetura.md`)

**What**: Create and run `probes/ast_and_arch_probe.py` to capture the repository baseline (`reports/00-baseline.md`), summarize the audit criteria (`reports/01-especificacao-criterios.md`), and generate the complete architectural integrity report (`reports/02-arquitetura.md`) covering AST import graph, dependency levels, cycle detection, ADR-008 class taxonomy, duplicated responsibilities, unused public symbols, and documentation-vs-API alignment.
**Where**: `.specs/features/m1-integrity-review/reports/02-arquitetura.md`
**Depends on**: None
**Reuses**: `engenharia_software/ARQUITETURA_E_CONTRATOS.md`
**Requirement**: AUD-01, AUD-03, AUD-04, ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05, ARCH-06, ARCH-07

**Done when**:

- [ ] `probes/ast_and_arch_probe.py` executed and outputs recorded
- [ ] `reports/00-baseline.md` records `HEAD` commit hash (`6acf6f8`), clean status, `.venv` Python/NumPy/pytest versions, and `81 passed` baseline
- [ ] `reports/01-especificacao-criterios.md` documents the 48 objective criteria and verdict decision rule
- [ ] `reports/02-arquitetura.md` documents full AST import graph, ADR-008 compliance, duplicated logic analysis, unused symbol check, and doc-vs-API comparison
- [ ] Gate check passes: `.venv/bin/pytest tests/ -q`
- [ ] Test count: 81 project tests pass (0 files modified in `src/` or `tests/`)

**Tests**: integration
**Gate**: quick

---

### T2: Execute Dimension B cross-module integration audit (`03-integracao.md`)

**What**: Create and run `probes/integration_probe.py` exercising end-to-end flows across `core`, `metrics`, and `data`, verifying `ObservationId`/`TaskType` identity, `ExperimentalMLError` exception hierarchy, cross-format `dataset_hash` behavior, cross-process `PYTHONHASHSEED` determinism, read-only buffer invariance across all 15 metrics, `bundle.dataset_hash` vs `core.dataset_hash` relation, and `int64`/`bool` column handling, recording all evidence in `reports/03-integracao.md`.
**Where**: `.specs/features/m1-integrity-review/reports/03-integracao.md`
**Depends on**: T1
**Reuses**: `src/experimental_ml/core/`, `src/experimental_ml/metrics/`, `src/experimental_ml/data/`
**Requirement**: INT-01, INT-02, INT-03, INT-04, INT-05, INT-06, INT-07, INT-08

**Done when**:

- [ ] `probes/integration_probe.py` executed under `PYTHONHASHSEED=0` and `PYTHONHASHSEED=12345`
- [ ] `reports/03-integracao.md` records end-to-end flow results, type/exception checks, CSV/TSV/dict hash comparison, read-only array preservation across all 15 metrics, and `int64`/`bool` dtype behavior
- [ ] Gate check passes: `.venv/bin/pytest tests/ -q`
- [ ] Test count: 81 project tests pass

**Tests**: integration
**Gate**: quick

---

### T3: Execute Dimensions C and D implementation quality, performance, coverage, mutation, and TLC validators audit (`04-qualidade-e-testes.md`)

**What**: Create and run `probes/quality_and_perf_probe.py` and `probes/testing_and_tlc_probe.py` to perform AST code-quality scanning, type-annotation checking, edge-case testing, 10k/100k scaling benchmarks, adversarial `DatasetBundle` immutability testing, interpreter checks, line coverage measurement, $\ge 12$ isolated mutations in `/tmp/m1-audit-mut/`, test isolation/order runs, and TLC validator audits (including `check_proofs.py` in `/tmp/m1-audit-clone/`), recording all results in `reports/04-qualidade-e-testes.md`.
**Where**: `.specs/features/m1-integrity-review/reports/04-qualidade-e-testes.md`
**Depends on**: T2
**Reuses**: `.agent/skills/tlc-spec-driven/scripts/`
**Requirement**: QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05, QUAL-06, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07, TEST-08

**Done when**:

- [ ] `probes/quality_and_perf_probe.py` and `probes/testing_and_tlc_probe.py` executed and temporary `/tmp/m1-audit-*` directories cleaned up
- [ ] `reports/04-qualidade-e-testes.md` records AST scan, type annotations, edge cases, 10k/100k scaling ratios, adversarial immutability attempts, interpreter matrix, per-file line coverage, $\ge 12$ mutations table, test isolation/ordering results, and TLC validator reliability results
- [ ] Gate check passes: `.venv/bin/pytest tests/ -q`
- [ ] Test count: 81 project tests pass

**Tests**: integration
**Gate**: quick

---

### T4: Execute Dimension E documentation, README code blocks, and requirement traceability audit (`05-rastreabilidade.md`)

**What**: Create and run `probes/docs_and_traceability_probe.py` to execute every fenced `python` block in `README.md`, compare the `README.md` directory tree against the filesystem, verify test counts/statuses/commits across all documents, check importability of all documented symbols, compare ADR-007 vs M1.4 spec vs code, build the complete `RF/RNF/CA/TA` traceability matrix, and verify M1.1–M1.4 governance records, writing `reports/05-rastreabilidade.md`.
**Where**: `.specs/features/m1-integrity-review/reports/05-rastreabilidade.md`
**Depends on**: T3
**Reuses**: `README.md`, `engenharia_software/ESPECIFICACAO_REQUISITOS.md`, `engenharia_software/ARQUITETURA_E_CONTRATOS.md`, `engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`, `.specs/STATE.md`
**Requirement**: DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07

**Done when**:

- [ ] `probes/docs_and_traceability_probe.py` executed
- [ ] `reports/05-rastreabilidade.md` records execution results of all `README.md` Python blocks, directory tree discrepancies, symbol import checks, ADR-007 vs M1.4 hash semantics comparison, full `RF/RNF/CA/TA` traceability matrix, and M1.1–M1.4 governance audit
- [ ] Gate check passes: `.venv/bin/pytest tests/ -q`
- [ ] Test count: 81 project tests pass

**Tests**: integration
**Gate**: quick

---

### Phase 2: Findings Register, Prioritized Remediation Plan, M2 Readiness Verdict & Proof Suite (Dimension F)

### T5: Compile consolidated findings register and prioritized remediation plan (`06-achados.md` & `07-plano-correcoes.md`)

**What**: Consolidate every finding identified across Dimensions A–F into `reports/06-achados.md` with unique ID (`AUD-F-NNN`), dimension, category (`DEFEITO`, `RISCO`, `MELHORIA`, `LIMITAÇÃO DOCUMENTADA`), severity (`CRÍTICO`, `ALTO`, `MODERADO`, `BAIXO`), location, evidence, impact, justification, and recommendation, and generate the prioritized remediation plan in `reports/07-plano-correcoes.md`.
**Where**: `.specs/features/m1-integrity-review/reports/06-achados.md`
**Depends on**: T4
**Reuses**: `.specs/features/m1-integrity-review/reports/02-arquitetura.md`, `.specs/features/m1-integrity-review/reports/03-integracao.md`, `.specs/features/m1-integrity-review/reports/04-qualidade-e-testes.md`, `.specs/features/m1-integrity-review/reports/05-rastreabilidade.md`
**Requirement**: READY-03, READY-04, READY-05

**Done when**:

- [ ] `reports/06-achados.md` lists all findings with complete mandatory metadata fields and citations for any `LIMITAÇÃO DOCUMENTADA`
- [ ] `reports/07-plano-correcoes.md` orders all `CRÍTICO`, `ALTO`, and actionable `MODERADO` items with affected files, milestone reopening recommendation, and M2 blocking status
- [ ] Gate check passes: `.venv/bin/pytest tests/ -q`
- [ ] Test count: 81 project tests pass

**Tests**: integration
**Gate**: quick

---

### T6: Produce M2 readiness assessment, final verdict report, and acceptance results (`08-parecer.md` & `RESULTS.md`)

**What**: Evaluate M1 readiness for every planned M2 contract (`profile_dataset`, `DatasetProfile`, `PreparationPlan`, `sanitize_dataset`, `SanitizedDatasetView`, `build_partition_plan`, `validate_partition_plan`, `PartitionPlan`, CLI `data`/`partition`), list open architectural questions for M2, compute the formal verdict (`APTO`, `APTO COM RESSALVAS`, or `NÃO APTO`) in `reports/08-parecer.md`, update `reports/00-baseline.md` with final non-interference diff evidence, and write `RESULTS.md`.
**Where**: `.specs/features/m1-integrity-review/reports/08-parecer.md`
**Depends on**: T5
**Reuses**: `.specs/features/m1-integrity-review/reports/06-achados.md`, `.specs/features/m1-integrity-review/reports/07-plano-correcoes.md`
**Requirement**: AUD-02, READY-01, READY-02, READY-06, READY-07, READY-08

**Done when**:

- [ ] `reports/08-parecer.md` documents M2 contract readiness table, open M2 architectural questions, finding counts by category/severity, declared audit limitations, and mechanical verdict
- [ ] `RESULTS.md` records executed validations and formal audit conclusions
- [ ] Non-interference diff against `6acf6f8` on project files is verified empty
- [ ] Gate check passes: `.venv/bin/pytest tests/ -q`
- [ ] Test count: 81 project tests pass

**Tests**: integration
**Gate**: quick

---

### T7: Implement and run 48-check automated audit verification suite (`probes/test_audit_checks.py`)

**What**: Create `.specs/features/m1-integrity-review/probes/test_audit_checks.py` implementing 48 deterministic pytest checks (`test_c01_aud_01_baseline_recorded` through `test_c48_ready_08_unreproduced_findings_policy`) that verify every report, evidence record, traceability row, decision rule calculation, and the non-interference `git diff` invariant.
**Where**: `.specs/features/m1-integrity-review/probes/test_audit_checks.py`
**Depends on**: T6
**Reuses**: `.specs/features/m1-integrity-review/reports/`
**Requirement**: AUD-01, AUD-02, AUD-03, AUD-04, ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05, ARCH-06, ARCH-07, INT-01, INT-02, INT-03, INT-04, INT-05, INT-06, INT-07, INT-08, QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05, QUAL-06, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07, TEST-08, DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, READY-01, READY-02, READY-03, READY-04, READY-05, READY-06, READY-07, READY-08

**Done when**:

- [ ] `probes/test_audit_checks.py` created with 48 test functions mapped 1:1 to `C1`..`C48`
- [ ] Full audit gate passes: `.venv/bin/pytest .specs/features/m1-integrity-review/probes/test_audit_checks.py -v` (48 passed)
- [ ] Project test suite passes: `.venv/bin/pytest tests/ -v` (81 passed)
- [ ] Non-interference diff is empty

**Tests**: unit
**Gate**: full

---

## Checks

**C1** - Baseline report records HEAD hash, git status, Python/NumPy/pytest versions, and 81 passing tests (AUD-01, AC 1)
Proof: run audit | test_c01_aud_01_baseline_recorded PASSED

**C2** - Non-interference diff against baseline across src, tests, pyproject.toml, .agent, and m1-1..m1-4 is empty (AUD-02, AC 2)
Proof: run audit | test_c02_aud_02_non_interference_diff_empty PASSED

**C3** - Every registered finding contains a reproducible command output excerpt or path:line reference (AUD-03, AC 3)
Proof: run audit | test_c03_aud_03_findings_have_reproducible_evidence PASSED

**C4** - Criteria not verifiable with host tools are marked NAO VERIFICAVEL naming the missing resource (AUD-04, AC 4)
Proof: run audit | test_c04_aud_04_unverifiable_criteria_marked PASSED

**C5** - Intra-package AST import graph is extracted and recorded with all module edges (ARCH-01, AC 1)
Proof: run audit | test_c05_arch_01_import_graph_recorded PASSED

**C6** - Import edges are validated against Section 2.3 dependency levels (ARCH-02, AC 2)
Proof: run audit | test_c06_arch_02_dependency_levels_checked PASSED

**C7** - Import graph is checked for cycles and confirms zero cycles (ARCH-03, AC 3)
Proof: run audit | test_c07_arch_03_zero_import_cycles PASSED

**C8** - Every class in src/ is classified against ADR-008 immutability and no-OOP business logic rules (ARCH-04, AC 4)
Proof: run audit | test_c08_arch_04_adr008_class_taxonomy PASSED

**C9** - Responsibilities implemented in more than one module are listed with path:line and divergence analysis (ARCH-05, AC 5)
Proof: run audit | test_c09_arch_05_duplicate_responsibilities_listed PASSED

**C10** - Public symbols in __all__ with zero external references in src/ or tests/ are inventoried (ARCH-06, AC 6)
Proof: run audit | test_c10_arch_06_unreferenced_public_symbols_checked PASSED

**C11** - Documented module responsibilities in ARQUITETURA_E_CONTRATOS.md are compared against implemented public APIs (ARCH-07, AC 7)
Proof: run audit | test_c11_arch_07_doc_vs_public_api_compared PASSED

**C12** - End-to-end flow across load_dataset, get_column_array, compute_metric, and aggregate_fold_metrics completes and is recorded (INT-01, AC 1)
Proof: run audit | test_c12_int_01_e2e_flow_executed PASSED

**C13** - DatasetBundle.observation_ids elements are ObservationId instances and schema task_type preserves TaskType identity (INT-02, AC 2)
Proof: run audit | test_c13_int_02_identifier_and_enum_identity PASSED

**C14** - Public error paths in data and metrics are checked against ExperimentalMLError hierarchy (INT-03, AC 3)
Proof: run audit | test_c14_int_03_exception_hierarchy_verified PASSED

**C15** - Tabular content loaded from CSV, TSV, and in-memory dict has dataset_hash compared against spec and ADR-007 (INT-04, AC 4)
Proof: run audit | test_c15_int_04_cross_format_dataset_hash_compared PASSED

**C16** - Separate processes with PYTHONHASHSEED=0 and PYTHONHASHSEED=12345 produce byte-identical hashes and metrics (INT-05, AC 5)
Proof: run audit | test_c16_int_05_cross_process_hashseed_determinism PASSED

**C17** - Read-only arrays from get_column_array(copy=False) work across all 15 metrics and remain byte-identical (INT-06, AC 6)
Proof: run audit | test_c17_int_06_readonly_arrays_across_all_metrics PASSED

**C18** - Exact relationship between bundle.dataset_hash and core.dataset_hash is verified and recorded (INT-07, AC 7)
Proof: run audit | test_c18_int_07_bundle_vs_core_dataset_hash_relation PASSED

**C19** - Behavior of int64 and bool bundle columns passed to regression and classification metrics is recorded (INT-08, AC 8)
Proof: run audit | test_c19_int_08_int64_and_bool_dtype_behavior_recorded PASSED

**C20** - AST scan of src/ lists bare excepts, swallowed exceptions, mutable defaults, runtime asserts, globals, and unused imports (QUAL-01, AC 1)
Proof: run audit | test_c20_qual_01_ast_code_quality_scan PASSED

**C21** - Public functions and methods in core, metrics, and data are checked for parameter and return type annotations (QUAL-02, AC 2)
Proof: run audit | test_c21_qual_02_public_type_annotations_checked PASSED

**C22** - Edge cases (empty, length mismatch, NaN, Inf, NFD Unicode, duplicate IDs, >int64) are probed and classified (QUAL-03, AC 3)
Proof: run audit | test_c22_qual_03_edge_cases_probed PASSED

**C23** - Scaling benchmark at 10k and 100k rows x 20 columns records wall-clock times and ratios for load_dataset and dataset_hash (QUAL-04, AC 4)
Proof: run audit | test_c23_qual_04_scaling_benchmark_recorded PASSED

**C24** - Adversarial mutation attempts on DatasetBundle attributes, mappings, buffers, and object elements are executed and verified (QUAL-05, AC 5)
Proof: run audit | test_c24_qual_05_adversarial_immutability_verified PASSED

**C25** - Available host Python interpreters >= 3.10 are tested and missing versions marked NAO VERIFICAVEL against RNF06 (QUAL-06, AC 6)
Proof: run audit | test_c25_qual_06_interpreter_compatibility_recorded PASSED

**C26** - Line coverage per file of src/experimental_ml/ is measured and uncovered lines of files < 90% are listed (TEST-01, AC 1)
Proof: run audit | test_c26_test_01_line_coverage_measured PASSED

**C27** - At least 12 manual mutations across core, metrics, data, and cli are executed in /tmp outside the repo (TEST-02, AC 2)
Proof: run audit | test_c27_test_02_twelve_mutations_executed PASSED

**C28** - Surviving mutations breaking a spec criterion are registered as findings naming the weak test assertion (TEST-03, AC 3)
Proof: run audit | test_c28_test_03_surviving_mutations_analyzed PASSED

**C29** - Existing tests in tests/ importing two or more of core, metrics, and data are counted and finding registered if zero (TEST-04, AC 4)
Proof: run audit | test_c29_test_04_cross_module_integration_tests_counted PASSED

**C30** - All 81 tests pass in single-test isolation and in forward and reversed file order (TEST-05, AC 5)
Proof: run audit | test_c30_test_05_test_isolation_and_ordering_verified PASSED

**C31** - TLC validators (validate_spec, validate_tasks, validate_verification, and disposable-clone check_proofs) are run across m1-1..m1-4 (TEST-06, AC 6)
Proof: run audit | test_c31_test_06_tlc_validators_executed PASSED

**C32** - Every acceptance criterion of m1-1..m1-4 spec.md is mapped to a Checks row in tasks.md and a passing proof in proofs.md (TEST-07, AC 7)
Proof: run audit | test_c32_test_07_criterion_check_proof_mapping_verified PASSED

**C33** - TLC validators are tested against structural defects and any undetected defect is registered as a finding (TEST-08, AC 8)
Proof: run audit | test_c33_test_08_tlc_validator_reliability_checked PASSED

**C34** - Every fenced python block in README.md is executed in a fresh subprocess and exceptions or comment mismatches are registered (DOC-01, AC 1)
Proof: run audit | test_c34_doc_01_readme_python_blocks_executed PASSED

**C35** - Every path in README.md directory tree is compared bidirectionally against src/ and tests/ on disk (DOC-02, AC 2)
Proof: run audit | test_c35_doc_02_readme_directory_tree_compared PASSED

**C36** - Test counts, milestone statuses, and commit hashes across all docs and RESULTS.md are verified against pytest and git log (DOC-03, AC 3)
Proof: run audit | test_c36_doc_03_counts_statuses_commits_verified PASSED

**C37** - Every symbol named as implemented for M1.1-M1.4 across project docs is checked for importability from its stated module (DOC-04, AC 4)
Proof: run audit | test_c37_doc_04_documented_symbols_importable_checked PASSED

**C38** - Contradictions between ADR-007, m1-4 spec.md, and implementation regarding dataset_hash are analyzed and registered (DOC-05, AC 5)
Proof: run audit | test_c38_doc_05_hash_contract_contradictions_checked PASSED

**C39** - Traceability matrix mapping RF, RNF, CA, and TA to feature IDs, tests, and proofs is complete in 05-rastreabilidade.md (DOC-06, AC 6)
Proof: run audit | test_c39_doc_06_traceability_matrix_complete PASSED

**C40** - Governance artifacts (spec, tasks, proofs, verification, ACCEPTANCE, RESULTS, Approved lines, STATE.md) are verified across M1.1-M1.4 (DOC-07, AC 7)
Proof: run audit | test_c40_doc_07_governance_artifacts_verified PASSED

**C41** - Every planned M2 contract is mapped to the M1 interfaces it consumes with shape compatibility evaluated (READY-01, AC 1)
Proof: run audit | test_c41_ready_01_m2_consumed_interfaces_evaluated PASSED

**C42** - Unsettled architectural decisions required by M2 are registered as RISCO with recommended owner phase (READY-02, AC 2)
Proof: run audit | test_c42_ready_02_open_m2_decisions_listed PASSED

**C43** - All findings in 06-achados.md contain ID, dimension, category, severity, location, evidence, impact, justification, and recommendation (READY-03, AC 3)
Proof: run audit | test_c43_ready_03_findings_register_schema_complete PASSED

**C44** - Every finding classified as LIMITACAO DOCUMENTADA cites a pre-existing document and section (READY-04, AC 4)
Proof: run audit | test_c44_ready_04_documented_limitations_cited PASSED

**C45** - Prioritized remediation plan in 07-plano-correcoes.md orders CRITICO, ALTO, and MODERADO items with files, reopening, and M2 blocking flags (READY-05, AC 5)
Proof: run audit | test_c45_ready_05_remediation_plan_prioritized PASSED

**C46** - Final verdict in 08-parecer.md matches the mechanical decision rule applied to 06-achados.md counts and declares audit limitations (READY-06, AC 6)
Proof: run audit | test_c46_ready_06_verdict_matches_decision_rule PASSED

**C47** - Independent Verifier re-execution of CRITICO/ALTO findings and >=20% sample of remaining findings is recorded (READY-07, AC 7)
Proof: run audit | test_c47_ready_07_independent_verification_recorded PASSED

**C48** - Policy for any NAO REPRODUZIDO finding is enforced with zero unresolved unconfirmed findings in the final verdict (READY-08, AC 8)
Proof: run audit | test_c48_ready_08_unreproduced_findings_policy PASSED

---

## Acceptance Walkthrough (ACCEPTANCE.md)

Alongside `tasks.md`, `ACCEPTANCE.md` is maintained defining:
1. Environment verification commands and baseline check (`81 passed`).
2. Step-by-step execution of the 5 read-only audit probes (`probes/*.py`).
3. Execution of the 48-check verification suite (`probes/test_audit_checks.py`).
4. Verification of the non-interference invariant (`git diff 6acf6f8` empty on project files).
5. Inspection table of the 8 audit deliverables (`reports/00..08-*.md` and `RESULTS.md`).

---

## Handoff

The feature's live state, written as it happens - a compaction gives no warning.

**Settled mid-build:** none
**Dispatched:** none
**Walked:** pending

---

## Phase Execution Map

```
Phase 1 → Phase 2

Phase 1:  T1 ------→ T2 ------→ T3 ------→ T4
Phase 2:  T5 ------→ T6 ------→ T7
```
