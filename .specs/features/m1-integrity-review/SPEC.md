# m1-integrity-review Specification

**Approved**: 2026-11-05 - user: "confirmo todas recomendacoes"

## Problem Statement

O Marco M1 (M1.1 `setup-cli-smoke`, M1.2 `core`, M1.3 `metrics`, M1.4 `datasets-schemas`) foi aprovado entrega a entrega, cada uma com sua própria suíte de testes, verificação TLC e homologação manual. A aprovação individual não demonstra a integridade do conjunto: não há testes que exercitem `core`, `metrics` e `data` em um mesmo fluxo, a documentação geral foi reescrita após o merge do M1.4 sem execução dos exemplos de código, e os contratos do Marco M2 (`profile_dataset`, `PreparationPlan`, `sanitize_dataset`, `PartitionPlan`) dependerão diretamente de tipos, hashes e garantias de imutabilidade do M1. Esta auditoria verifica, com evidência reproduzível no estado atual do repositório, se a fundação é arquiteturalmente consistente, integrada, testada de forma significativa, documentada sem contradições e apta a receber o M2.

A atividade é exclusivamente de auditoria e diagnóstico. Nenhum código-fonte, teste ou configuração do projeto é alterado; os achados geram recomendações cujo tratamento é decidido separadamente.

## Goals

- [ ] Produzir os 8 entregáveis da auditoria (especificação, 4 relatórios dimensionais, matriz de rastreabilidade, registro de achados, plano de correções e parecer), cada afirmação ancorada em evidência reproduzível (comando + saída, ou `arquivo:linha`).
- [ ] Cobrir as seis dimensões A–F com critérios objetivos, cada um resultando em `CONFORME`, `NÃO CONFORME` (com achado) ou `NÃO VERIFICÁVEL` (com motivo).
- [ ] Classificar 100% dos achados por categoria (`DEFEITO`, `RISCO`, `MELHORIA`, `LIMITAÇÃO DOCUMENTADA`) e severidade (`CRÍTICO`, `ALTO`, `MODERADO`, `BAIXO`).
- [ ] Emitir parecer final `APTO`, `APTO COM RESSALVAS` ou `NÃO APTO` derivado mecanicamente da regra de decisão desta especificação.
- [ ] Encerrar com `git diff <baseline> -- src tests pyproject.toml .agent` vazio.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Correção de qualquer defeito encontrado | Restrição obrigatória da atividade: a implementação de correções é decidida após o parecer. |
| Alteração de `src/`, `tests/`, `pyproject.toml`, `.agent/` ou dos registros de milestones (`spec.md`, `tasks.md`, `proofs.md`, `verification.md`, `ACCEPTANCE.md`, `RESULTS.md`) de M1.1–M1.4 | Preservação dos mecanismos de governança e separação entre auditoria e implementação. |
| Inclusão de novos testes na suíte do projeto | Testes de sondagem da auditoria vivem fora de `tests/` e não passam a integrar o gate do projeto. |
| Design ou especificação do Marco M2 | A auditoria avalia prontidão; não antecipa decisões do próximo marco. |
| Reabertura de milestones concluídos | Só é recomendada mediante defeito comprovado registrado no registro de achados. |
| Configuração de CI, linters ou ferramentas no `pyproject.toml` | Alteração de configuração vedada; pode constar apenas como recomendação. |
| Auditoria de `REFERENCIAS_E_FUNDAMENTACAO.md` quanto ao mérito científico das referências | Fora das dimensões A–F; apenas a existência das referências citadas pelos ADRs é conferida quando pertinente. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Localização dos artefatos da auditoria | `.specs/features/m1-integrity-review/` com `spec.md`, `tasks.md`, `proofs.md`, `verification.md` e os relatórios `reports/01..08-*.md`; `ACCEPTANCE.md` descreve como reproduzir cada verificação; `RESULTS.md` registra o parecer | Mantém a estrutura TLC e a tríade de aceite (AD-002) sem criar diretório paralelo em `engenharia_software/`. | y |
| Branch de trabalho | Criar `audit/m1-integrity-review` a partir de `main` (`6acf6f8`); commits contêm exclusivamente arquivos sob `.specs/features/m1-integrity-review/` | Isola a auditoria de `main` e permite revisão por PR. | y |
| Sondas executáveis da auditoria | Scripts em `.specs/features/m1-integrity-review/probes/`, executados com `.venv/bin/python`, importando apenas APIs públicas; fora de `tests/` e fora do gate do projeto | Permite testes de integração e de casos extremos sem violar a restrição de não modificar testes. | y |
| Medição de cobertura | Cobertura de linhas via biblioteca padrão (`python -m trace --count --missing`) ou rastreador baseado em `sys.settrace`, sem instalar pacotes no `.venv` | `pytest-cov`, `coverage`, `mypy` e `ruff` não estão instalados; instalar exigiria rede e altera o ambiente. O número é reportado com o método explícito. | y |
| Análise de mutação (força dos testes) | Mutações manuais aplicadas a uma cópia de `src/` em `/tmp/m1-audit-mut/`, com `PYTHONPATH` apontando para a cópia; repositório nunca é tocado | Mede se os testes falham quando a regra que afirmam proteger é quebrada, sem alterar o código auditado. | y |
| Execução de `check_proofs.py` | Executado em clone local descartável (`git clone . /tmp/m1-audit-clone`), nunca na árvore de trabalho | O script reescreve `proofs.md`; executá-lo no repositório alteraria registros de governança de milestones concluídos. | y |
| Regra de decisão do parecer | `NÃO APTO` se existir ≥ 1 achado `CRÍTICO` ou ≥ 1 `DEFEITO` `ALTO`; `APTO COM RESSALVAS` se existirem apenas achados `MODERADO`/`BAIXO` ou `RISCO`/`MELHORIA` `ALTO` com tratamento planejado; `APTO` se não houver achado acima de `BAIXO` | Traduz a definição fornecida ("ALTO: deve ser tratado antes de avançar") em regra mecânica, distinguindo defeito comprovado de risco. | y |
| Compatibilidade de interpretadores (`RNF06`, `requires-python = ">=3.10"`) | Executar a suíte em todo interpretador ≥ 3.10 disponível no host com `numpy` importável; 3.10 e 3.11 não existem no host (`/usr/bin`: 3.9, 3.12, 3.14) e são registrados como `NÃO VERIFICÁVEL`, sem instalação | Verificação empírica limitada ao ambiente existente, sem alterar o sistema. | y |
| Independência da verificação | Cada dimensão é executada por subagente com contexto novo; um Verifier distinto (author ≠ verifier) reexecuta ≥ 1 evidência por achado `CRÍTICO`/`ALTO` e uma amostra de ≥ 20% dos demais; a limitação de que todos os agentes compartilham a mesma família de modelo é declarada no parecer | Atende ao pedido de verificação independente dentro dos meios disponíveis. | y |
| Exemplos de código do `README.md` | São tratados como objeto de auditoria comum; os blocos de `experimental_ml.metrics` e `experimental_ml.data` foram redigidos no commit `6acf6f8` sem execução | Transparência sobre a origem de um risco documental conhecido antes da auditoria. | y |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Protocolo, Linha de Base e Não Interferência ⭐ MVP

**User Story**: Como responsável pelo projeto, quero que a auditoria registre exatamente o estado auditado e comprove que não alterou o projeto, para que o parecer seja reproduzível e confiável.

**Why P1**: Sem linha de base e prova de não interferência, nenhum achado é reproduzível.

**Acceptance Criteria**:

1. WHEN the audit starts THEN the auditor SHALL record in `reports/00-baseline.md` the commit hash of `HEAD`, the output of `git status --porcelain`, the Python version of `.venv`, the installed `numpy` and `pytest` versions, and the result line of `.venv/bin/pytest tests/ -q`.
2. WHEN the audit ends THEN the auditor SHALL record the output of `git diff --stat <baseline> -- src tests pyproject.toml .agent .specs/features/m1-1-setup-cli-smoke .specs/features/m1-2-core .specs/features/m1-3-metrics .specs/features/m1-4-datasets-schemas`, and that output SHALL be empty.
3. The audit SHALL support every finding with at least one reproducible evidence item: a command with its captured output excerpt, or a `path:line` reference with the quoted content.
4. IF a criterion cannot be checked with the tools available on the host THEN the auditor SHALL mark it `NÃO VERIFICÁVEL` with the missing tool or resource named, and SHALL NOT mark it `CONFORME`.

**Independent Test**: Reexecutar os comandos de `00-baseline.md` em clone de `<baseline>` e obter os mesmos valores; o diff do critério 2 é vazio.

---

### P1: Integridade Arquitetural (Dimensão A) ⭐ MVP

**User Story**: Como responsável pelo projeto, quero saber se a implementação respeita a arquitetura documentada, para que o M2 seja construído sobre fronteiras de módulo corretas.

**Why P1**: Violações de nível de dependência ou de ADR-008 propagam-se para todos os módulos seguintes.

**Acceptance Criteria**:

1. WHEN the audit inspects `src/experimental_ml/` THEN the auditor SHALL extract the intra-package import graph by AST parsing (including imports inside functions) and record every edge `module -> module` in `reports/02-arquitetura.md`.
2. IF an import edge violates the allowed dependency levels of `ARQUITETURA_E_CONTRATOS.md` Section 2.3 (`core` depends on nothing internal; `metrics` and `data` depend only on `core`; `cli` may depend on any) THEN the auditor SHALL register a finding.
3. IF the import graph contains a cycle THEN the auditor SHALL register a finding of severity `CRÍTICO`.
4. The auditor SHALL classify every `class` defined under `src/` as `frozen data structure`, `enum`, `exception` or `other`, and SHALL register a finding for each `other` or each non-frozen data structure, citing ADR-008.
5. The auditor SHALL list every responsibility implemented in more than one module (including hashing, Unicode NFC normalization, numeric validation and identifier validation) with the `path:line` of each implementation, and SHALL register a finding for each duplicate that can produce divergent results.
6. The auditor SHALL list every public symbol (`__all__`) of `core`, `metrics` and `data` that has zero references in `src/` outside its defining module and zero references in `tests/`, recording each as a candidate premature abstraction.
7. The auditor SHALL compare the responsibilities attributed to `core`, `metrics` and `data` in `ARQUITETURA_E_CONTRATOS.md` Sections 2.3 and 3.1 against the implemented public API and SHALL register a finding for each responsibility documented as implemented but absent, or implemented but undocumented.

**Independent Test**: O grafo de importações é regenerado pela sonda `probes/import_graph.py` e coincide com o registrado no relatório.

---

### P1: Integração entre Módulos (Dimensão B) ⭐ MVP

**User Story**: Como pesquisador que usará o M2, quero ter certeza de que dados carregados por `data` fluem para `metrics` com tipos, hashes, identificadores e imutabilidade preservados, para que a composição dos módulos não introduza erros silenciosos.

**Why P1**: Não existe teste que exercite `core`, `metrics` e `data` em um mesmo fluxo.

**Acceptance Criteria**:

1. WHEN the probe `probes/e2e_flow.py` loads a CSV file and an equivalent in-memory `dict` with `load_dataset`, extracts target and one feature with `get_column_array`, computes `rmse` and `r2` through `compute_metric`, and aggregates two fold values with `aggregate_fold_metrics` THEN every step SHALL complete without exception, and IF any step raises THEN the auditor SHALL register a finding.
2. The auditor SHALL verify that every element of `DatasetBundle.observation_ids` is an instance of `experimental_ml.core.ObservationId` and that `DatasetSchemaSpec.task_type` accepts and stores the `experimental_ml.core.TaskType` member by identity.
3. The auditor SHALL verify that every exception raised by `data` and `metrics` in the probes is a subclass of `experimental_ml.core.ExperimentalMLError`, and SHALL register a finding for each public error path raising a type outside that hierarchy.
4. WHEN the same tabular content is loaded from a `,`-delimited CSV, a `\t`-delimited TSV and an in-memory `dict` THEN the auditor SHALL record whether `dataset_hash` is identical across the three, and IF it differs THEN the auditor SHALL compare the result against the contract stated in `m1-4-datasets-schemas/spec.md` and ADR-007 and register a finding when the behaviour contradicts either.
5. WHEN `probes/e2e_flow.py` runs twice in separate processes with `PYTHONHASHSEED=0` and `PYTHONHASHSEED=12345` THEN its printed hashes and metric values SHALL be byte-identical, and IF they differ THEN the auditor SHALL register a finding of severity at least `ALTO`.
6. WHEN arrays obtained from `get_column_array(..., copy=False)` are passed to every metric function in `METRICS_CATALOG` applicable to the task THEN the metric functions SHALL NOT raise because of the read-only flag, and the arrays SHALL remain byte-identical before and after the call.
7. The auditor SHALL verify whether `bundle.dataset_hash` equals `core.dataset_hash` applied to the bundle's public columns and schema as documented in ADR-007, and SHALL record the exact relation found.
8. IF a column of physical type `int64` or `bool` is passed from a bundle to a regression or classification metric THEN the metric SHALL either compute a value or raise a documented error type, and the auditor SHALL record which of the two occurs for each metric family.

**Independent Test**: Executar `probes/e2e_flow.py` e `probes/boundary_checks.py` e comparar a saída com a registrada em `reports/03-integracao.md`.

---

### P1: Qualidade da Implementação (Dimensão C) ⭐ MVP

**User Story**: Como responsável pelo projeto, quero conhecer defeitos de tratamento de erro, mutabilidade, determinismo e desempenho já presentes no código, para decidir o que corrigir antes do M2.

**Why P1**: Defeitos latentes de fundação tornam-se defeitos de todos os consumidores.

**Acceptance Criteria**:

1. The auditor SHALL scan `src/` by AST and list every occurrence of: bare `except:`, `except Exception` that does not re-raise, mutable default arguments, `assert` statements used for runtime validation, module-level mutable globals, and unused imports, with `path:line`.
2. The auditor SHALL list every public function and method in `core`, `metrics` and `data` lacking a type annotation on any parameter or on the return value.
3. WHEN the probe `probes/edge_cases.py` exercises each public entry point of `data` and `metrics` with empty input, length mismatch, `NaN`, `±Inf`, non-NFC Unicode column names, duplicate observation identifiers and integers beyond `int64` range THEN each case SHALL end in either a documented valid result or an exception of the `ExperimentalMLError` hierarchy, and IF a case returns a silently wrong value or raises another exception type THEN the auditor SHALL register a finding.
4. WHEN the probe `probes/perf_scaling.py` measures wall-clock time of `load_dataset` (CSV and in-memory) and of `dataset_hash` at 10 000 and 100 000 rows with 20 numeric columns THEN the auditor SHALL record both times, and IF the time ratio exceeds 20 THEN the auditor SHALL register a finding of severity `MODERADO` with the responsible code path identified.
5. The auditor SHALL attempt to mutate the content of a loaded `DatasetBundle` through every public attribute and every reference returned by the public API (including `setflags`, item assignment, `MappingProxyType` access, descriptor fields and `object` column elements), and IF any attempt changes `dataset_hash` recomputation or observable content THEN the auditor SHALL register a finding of severity `CRÍTICO`.
6. WHEN the test suite runs under each interpreter ≥ 3.10 available on the host with `numpy` importable THEN the auditor SHALL record the result per interpreter, and IF a declared-supported version cannot be executed THEN the auditor SHALL record it as `NÃO VERIFICÁVEL` against `RNF06`.

**Independent Test**: Reexecutar `probes/ast_scan.py`, `probes/edge_cases.py` e `probes/perf_scaling.py` e obter as mesmas listas e a mesma ordem de grandeza de tempos.

---

### P1: Estratégia de Testes e Confiabilidade do TLC (Dimensão D) ⭐ MVP

**User Story**: Como responsável pelo projeto, quero saber se os 81 testes aprovados protegem de fato os contratos que afirmam proteger, para não confundir suíte verde com fundação correta.

**Why P1**: A força da suíte de testes e dos gates TLC determina se regressões do M2 serão detectadas.

**Acceptance Criteria**:

1. The auditor SHALL measure line coverage per file of `src/experimental_ml/` under `.venv/bin/pytest tests/` with the method recorded in the report, and SHALL list the uncovered line ranges of each file with coverage below 90%.
2. The auditor SHALL apply at least 12 manual mutations (at least 3 each to `core`, `metrics` and `data`, plus at least 1 to `cli`) to a copy of `src/` outside the repository, each mutation breaking one rule stated in an approved spec criterion, and SHALL record for each mutation the criterion, the diff, the test expected to fail and whether the suite failed.
3. IF a mutation that breaks a spec criterion leaves the full suite passing THEN the auditor SHALL register a finding naming the criterion and the test whose assertion is weaker than the criterion.
4. The auditor SHALL count the tests that import from two or more of `core`, `metrics` and `data` and exercise them in one flow, and IF the count is zero THEN the auditor SHALL register a finding.
5. WHEN every collected test is run in isolation (`pytest <nodeid>` per test) and the full suite is run in forward and reversed file order THEN every test SHALL pass in every mode, and IF results diverge THEN the auditor SHALL register a finding identifying the order dependency.
6. The auditor SHALL run `validate_spec.py --strict`, `validate_tasks.py --strict` and `validate_verification.py --strict` for each of the four M1 features in the working tree, and `check_proofs.py` for each feature in a disposable clone, recording exit code and output of each run.
7. The auditor SHALL verify for each of the four M1 features that every acceptance criterion of `spec.md` maps to one `## Checks` row in `tasks.md` and to a passing proof line in `proofs.md`, and SHALL register a finding for each criterion without a check or proof.
8. IF a TLC validator exits 0 while a structural defect it is documented to detect is present in the audited artifacts THEN the auditor SHALL register a finding against the reliability of that validator.

**Independent Test**: O Verifier reexecuta pelo menos 3 mutações escolhidas por ele e obtém o mesmo resultado de suíte.

---

### P1: Documentação e Rastreabilidade (Dimensão E) ⭐ MVP

**User Story**: Como leitor da documentação, quero que README, arquitetura, requisitos, estado da engenharia e registros de governança descrevam o código que existe, para não tomar decisões do M2 com base em informação falsa.

**Why P1**: A documentação geral foi reescrita após o M1.4 e contém exemplos não executados.

**Acceptance Criteria**:

1. WHEN each fenced `python` block of `README.md` is executed in a fresh `.venv/bin/python` process from the repository root THEN it SHALL complete without exception and every value stated in its comments SHALL match the printed value, and IF either fails THEN the auditor SHALL register a finding per block.
2. The auditor SHALL compare every path in the `README.md` directory tree against the filesystem and every file under `src/experimental_ml/` and `tests/` against the tree, and SHALL register a finding per missing or unlisted path.
3. The auditor SHALL compare every test count, milestone status and commit reference stated in `README.md`, `ARQUITETURA_E_CONTRATOS.md`, `ESPECIFICACAO_REQUISITOS.md`, `ETAPA_ATUAL_ENGENHARIA.md`, `.specs/STATE.md` and the four `RESULTS.md` files against `pytest --collect-only` and `git log`, and SHALL register a finding per mismatch.
4. The auditor SHALL verify that every function, class and enum member named as implemented for M1.1–M1.4 in those documents is importable from the module the document names, and SHALL register a finding per symbol that is absent or located elsewhere.
5. The auditor SHALL check for contradictions between ADR-007 (`dataset_hash` for file input combines file bytes and schema hash), `m1-4-datasets-schemas/spec.md` (canonical content hash) and the implementation, and SHALL register a finding for each contradiction with the three statements quoted.
6. The auditor SHALL produce `reports/05-rastreabilidade.md` mapping each `RF`, `RNF`, `CA` and `TA` that any document declares implemented (fully or partially) in M1 to the feature requirement IDs, the test function, and the proof line, marking each row `RASTREADO`, `PARCIAL` or `SEM EVIDÊNCIA`.
7. The auditor SHALL verify that each of the four M1 feature directories contains `spec.md`, `tasks.md`, `proofs.md`, `verification.md`, `ACCEPTANCE.md` and `RESULTS.md`, that `spec.md` and `tasks.md` carry an `**Approved**:` line, that `RESULTS.md` carries an explicit acceptance decision, and that `.specs/STATE.md` `## Handoff` agrees with `git log`.

**Independent Test**: Sonda `probes/readme_blocks.py` reexecuta os blocos; sonda `probes/doc_symbols.py` reexecuta a verificação de símbolos.

---

### P1: Prontidão para o Marco M2 (Dimensão F) e Parecer ⭐ MVP

**User Story**: Como responsável pelo projeto, quero um parecer fundamentado sobre a capacidade da fundação de suportar o M2 e um plano priorizado de correções, para decidir se avanço, corrijo antes ou avanço com acompanhamento.

**Why P1**: É o resultado esperado da atividade.

**Acceptance Criteria**:

1. The auditor SHALL list, for each M2 contract named in `ARQUITETURA_E_CONTRATOS.md` Sections 3.1 and 3.4 (`profile_dataset`, `DatasetProfile`, `PreparationPlan`, `sanitize_dataset`, `SanitizedDatasetView`, `build_partition_plan`, `validate_partition_plan`, `PartitionPlan`, CLI `data`/`partition`), the M1 interfaces it consumes and whether each exists with the required shape.
2. The auditor SHALL list every architectural decision that M2 requires and that no ADR, `AD-NNN` or approved spec currently settles, each as a `RISCO` with recommended owner phase.
3. The auditor SHALL record every finding in `reports/06-achados.md` with the fields: ID (`AUD-F-NNN`), dimension, category (`DEFEITO`, `RISCO`, `MELHORIA`, `LIMITAÇÃO DOCUMENTADA`), severity (`CRÍTICO`, `ALTO`, `MODERADO`, `BAIXO`), location, evidence, impact, severity justification and recommendation.
4. IF a finding is classified `LIMITAÇÃO DOCUMENTADA` THEN the auditor SHALL cite the document and section where the limitation was already recorded before the audit baseline.
5. The auditor SHALL produce `reports/07-plano-correcoes.md` ordering every `CRÍTICO` and `ALTO` finding, and every `MODERADO` finding with a recommended timing, with: recommended action, affected files, whether a milestone reopening is recommended, and whether it blocks M2.
6. The auditor SHALL produce `reports/08-parecer.md` stating exactly one verdict (`APTO`, `APTO COM RESSALVAS`, `NÃO APTO`) computed by the decision rule recorded in this specification, with the count of findings per severity and category, and the declared limitations of the audit.
7. WHEN all reports are written THEN a Verifier sub-agent that did not author any report SHALL re-execute the evidence of every `CRÍTICO` and `ALTO` finding and of at least 20% of the remaining findings, and SHALL record per finding `CONFIRMADO` or `NÃO REPRODUZIDO` in `verification.md`.
8. IF the Verifier marks a finding `NÃO REPRODUZIDO` THEN the auditor SHALL either correct the evidence and obtain confirmation, or withdraw the finding with the reason recorded, before the verdict is final.

**Independent Test**: Aplicar a regra de decisão às contagens de `06-achados.md` e obter o mesmo veredito de `08-parecer.md`.

---

## Edge Cases

- IF the full test suite fails at the audit baseline THEN the auditor SHALL record the failing tests as findings of severity `CRÍTICO` and continue the remaining dimensions.
- IF a probe script itself contains a defect THEN the auditor SHALL fix the probe, not the audited code, and SHALL record the probe revision in the report.
- IF a mutation cannot be applied without breaking import of the package THEN the auditor SHALL discard it and replace it with another mutation of the same module.
- IF a documented behaviour and the implementation disagree and no approved spec settles which is correct THEN the auditor SHALL register a `RISCO` (not a `DEFEITO`) and list the question in Dimension F.
- IF a finding duplicates one already recorded in a milestone `RESULTS.md` or `verification.md` as accepted THEN the auditor SHALL classify it `LIMITAÇÃO DOCUMENTADA` and cite that record.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| AUD-01 | P1: Protocolo - baseline | Phase 1 (T1, T7) | Verified |
| AUD-02 | P1: Protocolo - não interferência | Phase 2 (T6, T7) | In Tasks |
| AUD-03 | P1: Protocolo - evidência por achado | Phase 1 (T1, T7) | Verified |
| AUD-04 | P1: Protocolo - NÃO VERIFICÁVEL | Phase 1 (T1, T7) | Verified |
| ARCH-01 | P1: Arquitetura - grafo de importações | Phase 1 (T1, T7) | Verified |
| ARCH-02 | P1: Arquitetura - níveis de dependência | Phase 1 (T1, T7) | Verified |
| ARCH-03 | P1: Arquitetura - ciclos | Phase 1 (T1, T7) | Verified |
| ARCH-04 | P1: Arquitetura - ADR-008 | Phase 1 (T1, T7) | Verified |
| ARCH-05 | P1: Arquitetura - responsabilidades duplicadas | Phase 1 (T1, T7) | Verified |
| ARCH-06 | P1: Arquitetura - abstrações sem consumidor | Phase 1 (T1, T7) | Verified |
| ARCH-07 | P1: Arquitetura - doc vs API pública | Phase 1 (T1, T7) | Verified |
| INT-01 | P1: Integração - fluxo ponta a ponta | Phase 1 (T2, T7) | Verified |
| INT-02 | P1: Integração - identificadores e enums | Phase 1 (T2, T7) | Verified |
| INT-03 | P1: Integração - hierarquia de exceções | Phase 1 (T2, T7) | Verified |
| INT-04 | P1: Integração - hash entre formatos | Phase 1 (T2, T7) | Verified |
| INT-05 | P1: Integração - determinismo entre processos | Phase 1 (T2, T7) | Verified |
| INT-06 | P1: Integração - imutabilidade na fronteira | Phase 1 (T2, T7) | Verified |
| INT-07 | P1: Integração - relação bundle/core hash | Phase 1 (T2, T7) | Verified |
| INT-08 | P1: Integração - dtypes int64/bool | Phase 1 (T2, T7) | Verified |
| QUAL-01 | P1: Qualidade - varredura AST | Phase 1 (T3, T7) | Verified |
| QUAL-02 | P1: Qualidade - anotações de tipo | Phase 1 (T3, T7) | Verified |
| QUAL-03 | P1: Qualidade - casos extremos | Phase 1 (T3, T7) | Verified |
| QUAL-04 | P1: Qualidade - escalabilidade | Phase 1 (T3, T7) | Verified |
| QUAL-05 | P1: Qualidade - imutabilidade adversarial | Phase 1 (T3, T7) | Verified |
| QUAL-06 | P1: Qualidade - interpretadores | Phase 1 (T3, T7) | Verified |
| TEST-01 | P1: Testes - cobertura | Phase 1 (T3, T7) | Verified |
| TEST-02 | P1: Testes - mutações aplicadas | Phase 1 (T3, T7) | Verified |
| TEST-03 | P1: Testes - mutações sobreviventes | Phase 1 (T3, T7) | Verified |
| TEST-04 | P1: Testes - testes de integração | Phase 1 (T3, T7) | Verified |
| TEST-05 | P1: Testes - isolamento e ordem | Phase 1 (T3, T7) | Verified |
| TEST-06 | P1: Testes - validadores TLC | Phase 1 (T3, T7) | Verified |
| TEST-07 | P1: Testes - critério→check→proof | Phase 1 (T3, T7) | Verified |
| TEST-08 | P1: Testes - confiabilidade dos validadores | Phase 1 (T3, T7) | Verified |
| DOC-01 | P1: Documentação - exemplos do README | Phase 1 (T4, T7) | Verified |
| DOC-02 | P1: Documentação - árvore de diretórios | Phase 1 (T4, T7) | Verified |
| DOC-03 | P1: Documentação - contagens e estados | Phase 1 (T4, T7) | Verified |
| DOC-04 | P1: Documentação - símbolos citados | Phase 1 (T4, T7) | Verified |
| DOC-05 | P1: Documentação - contradições de hash | Phase 1 (T4, T7) | Verified |
| DOC-06 | P1: Documentação - matriz RF/CA/TA | Phase 1 (T4, T7) | Verified |
| DOC-07 | P1: Documentação - governança | Phase 1 (T4, T7) | Verified |
| READY-01 | P1: Prontidão - interfaces consumidas pelo M2 | Phase 2 (T6, T7) | In Tasks |
| READY-02 | P1: Prontidão - decisões em aberto | Phase 2 (T6, T7) | In Tasks |
| READY-03 | P1: Prontidão - registro de achados | Phase 2 (T5, T7) | Verified |
| READY-04 | P1: Prontidão - limitações documentadas | Phase 2 (T5, T7) | Verified |
| READY-05 | P1: Prontidão - plano de correções | Phase 2 (T5, T7) | Verified |
| READY-06 | P1: Prontidão - parecer | Phase 2 (T6, T7) | In Tasks |
| READY-07 | P1: Prontidão - verificação independente | Phase 2 (T6, T7) | In Tasks |
| READY-08 | P1: Prontidão - achados não reproduzidos | Phase 2 (T6, T7) | In Tasks |

**Coverage:** 48 total, 48 mapped to tasks, 0 unmapped

---

## Sources

- `engenharia_software/ARQUITETURA_E_CONTRATOS.md` - níveis de dependência (2.3), contratos da Etapa 1 (3.1) e 4A (3.4), ADR-007, ADR-008, roadmap (7).
- `engenharia_software/ESPECIFICACAO_REQUISITOS.md` - RF1.1–RF1.7, RNF01–RNF07, CA-GER-01..03, CA-E1-01.
- `engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md` e `.specs/STATE.md` (AD-001, AD-002) - governança.
- `.specs/features/m1-{1,2,3,4}-*/` - specs, tasks, proofs, verification, ACCEPTANCE e RESULTS das quatro entregas.
- Solicitação de auditoria M1 — Project Integrity Review (escopo A–F, classificação, entregáveis, restrições).

---

## Success Criteria

- [ ] Os 8 entregáveis existem em `.specs/features/m1-integrity-review/` e cada critério AUD/ARCH/INT/QUAL/TEST/DOC/READY tem resultado `CONFORME`, `NÃO CONFORME` ou `NÃO VERIFICÁVEL`.
- [ ] Todo achado `CRÍTICO`/`ALTO` foi reproduzido pelo Verifier independente.
- [ ] O diff de não interferência (AUD-02) é vazio.
- [ ] O veredito de `08-parecer.md` é reproduzível aplicando a regra de decisão às contagens de `06-achados.md`.

