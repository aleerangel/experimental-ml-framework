# Feature: pos-3-usabilidade-acessibilidade-pesquisador

**Approved**: 2026-11-17 - user: "aprovado"

## Problem Statement

A Auditoria de Usabilidade e Acessibilidade Científica (`AUDITORIA_USABILIDADE.md`) constatou que, embora o MVP (M1–M7) execute com rigor metodológico e pureza `XCUT-02`, um pesquisador iniciante (ou mesmo um desenvolvedor sem consulta ao código interno) enfrenta barreiras relevantes de operação integrada:
1. A CLI `expml` não possui comando de inicialização (`expml init`) e exige a criação manual de até 6 arquivos JSON cujos schemas não estão documentados no `--help` nem em referência dedicada.
2. `expml data sanitize` exige `--rules` mesmo quando `profile` reporta zero achados.
3. `expml run start` não permite selecionar métricas via CLI (`--metrics`), bloqueando o uso de `rmse_rel_pct`, `mbe`, `roc_auc` ou `log_loss` sem recorrer à API Python.
4. `expml run {status,verify,resume}` exigem `--run-dir` em vez de aceitar `--experiment-dir` como os demais subcomandos.
5. Na API Python, executar um experimento completo exige importar manualmente 8 subpacotes e escrever código de cola repetitivo para consolidar células e salvar artefatos estatísticos.
6. Falta um guia dedicado de interpretação de resultados (Jornada 3) e uma referência dos schemas JSON da CLI (Jornada 2).

Este marco resolve essas lacunas preservando integralmente os contratos M1–M7, a pureza runtime `XCUT-02` e sem ocultar decisões metodológicas relevantes.

## Out of Scope

- Alteração de assinaturas ou remoção das funções puras existentes dos módulos `data`, `features`, `models`, `validation`, `orchestration`, `statistics`, `reporting` e `stages`.
- Implementação de funcionalidades da Onda 2 (`MULTI_TARGET_REGRESSION`, `PCA`, `BootstrapSplit`, `TemporalSplit`).
- Adição de dependências externas em runtime (`XCUT-02`).

## Assumptions & Open Questions

**Open questions:** none - o diagnóstico completo, as evidências do teste real e o plano priorizado estão registrados em `AUDITORIA_USABILIDADE.md`, `JORNADA_PESQUISADOR.md` e `PLANO_MELHORIAS_USABILIDADE.md` (homologado e verificado em 2026-11-17; os requisitos diagnósticos `USAB-01..07` de `PLANO_MELHORIAS_USABILIDADE.md` consolidam-se nos requisitos verificados `USAB-01..03` desta especificação, formalizando este marco como `TA-POS.3` e reservando `TA-POS.4` para a validação externa `CA02`).

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Preservação de contratos M1–M7 | Fachada Python e melhorias CLI atuam como camada aditiva | Garante compatibilidade retroativa com os 596 testes existentes |
| Decisões metodológicas explícitas | Valores padrão seguros apenas quando explicitamente informados/registrados | Cumpre `ADR-002` e `ADR-005` sem simplificações silenciosas |
| Pureza runtime `XCUT-02` | Apenas Python stdlib + `numpy` | Mantém invariante central do framework |

## User Stories

### US-POS3-01 (Priority: P1) — Inicialização de Projeto e Ergonomia da CLI (`expml init`, `--metrics`, `--experiment-dir`)
As an experimental ML researcher,  
I want a guided CLI workflow (`expml init`, optional `--rules`, `--metrics` on `run start`, unified `--experiment-dir`, actionable errors and next-step hints),  
So that I can run a full experiment via CLI without reading internal Python source files.

#### Acceptance Criteria
- **AC-POS3-01-01**: WHEN running `expml init --output-dir <dir>`, the CLI SHALL create a ready-to-run project skeleton containing an example tabular CSV and valid starter JSON templates (`schema.json`, `rules.json`, `scenarios.json`, `models.json`, `partition.json`, `stats_config.json`), and `expml quickrun --experiment-dir <dir>` SHALL execute all 6 stages sequentially with clear progress output.
- **AC-POS3-01-02**: WHEN running `expml data sanitize --experiment-dir <dir>` without `--rules` when no confirmed diagnostic issues exist, the CLI SHALL proceed with `rules=[]` instead of failing for a missing rules file.
- **AC-POS3-01-03**: WHEN running `expml run start` with `--metrics m1 m2 ...`, the CLI SHALL evaluate the requested metrics from `METRICS_CATALOG`, falling back to task-appropriate defaults only when `--metrics` is omitted.
- **AC-POS3-01-04**: WHEN running `expml run {status,verify,resume}`, the CLI SHALL accept `--experiment-dir` (inferring `<experiment-dir>/runs`) in addition to `--run-dir`, and `expml report generate` SHALL print the full output path of generated files.

---

### US-POS3-02 (Priority: P1) — Fachada Python de Alto Nível para Experimentos Integrados
As a researcher using Python or Jupyter Notebooks,  
I want a clean top-level helper `experimental_ml.run_experiment(...)` that orchestrates Stages 1–6 using explicit methodological parameters,  
So that I can run an end-to-end benchmark in ~15 lines without wiring internal codecs or stage gates manually.

#### Acceptance Criteria
- **AC-POS3-02-01**: WHEN calling `experimental_ml.run_experiment(...)` with either simple ML inputs (`data`, `target`, `task`, `models={"Nome": estimator}`, `cv_folds`) OR explicit framework specs (`DatasetSchemaSpec`, `ModelSpec`, `FeatureScenario`, `PartitionConfig`), the framework SHALL execute Stages 1–6 atomically, persist artifacts under `output_dir`, and return an immutable `ExperimentRunSummary` with `.summary()` in Portuguese.
- **AC-POS3-02-02**: WHERE invalid configurations or methodological violations occur, `run_experiment` and CLI JSON parsers SHALL raise `ExperimentalMLError` with actionable remediation hints without suppressing stage gates.

---

### US-POS3-03 (Priority: P1) — Documentação por Jornadas, Schemas JSON e Guia de Interpretação
As a beginner researcher or IC student,  
I want documentation organized by the 5 usage journeys including exact CLI JSON schemas and a result interpretation guide,  
So that I can configure experiments and interpret statistical reports accurately.

#### Acceptance Criteria
- **AC-POS3-03-01**: WHEN consulting `docs/referencia/cli_schemas_json.md` and `docs/guia/03_interpretando_resultados.md`, the documentation SHALL document every CLI JSON schema with working examples and explain how to interpret metrics, Nadeau-Bengio/Wilcoxon p-values, effect sizes, multiplicity, Pareto frontiers, and non-equivalence caveats.
- **AC-POS3-03-02**: WHEN validating the repository after implementation, all existing 596 tests plus new usability end-to-end tests SHALL pass with 0 skips and `XCUT-02` AST purity preserved.

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| USAB-01 | AC-POS3-01-01, AC-POS3-01-02, AC-POS3-01-03, AC-POS3-01-04 | `src/experimental_ml/cli/` | verified |
| USAB-02 | AC-POS3-02-01, AC-POS3-02-02 | `src/experimental_ml/__init__.py` | verified |
| USAB-03 | AC-POS3-03-01, AC-POS3-03-02 | `docs/`, `tests/` | verified |
