# pos-3-usabilidade-acessibilidade-pesquisador Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill.

---

**Design**: `.specs/features/pos-3-usabilidade-acessibilidade-pesquisador/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-17 - user: "Gostei da interface python de 10 linhas, mas nao vamos remover o que ja temos, somente flexbilizar"  
**Build**: none - Python interpreted package (`XCUT-02`: stdlib + numpy only)  
**Run unit**: .venv/bin/pytest tests/unit/test_usability_cli_and_facade.py tests/unit/test_documentation_integrity.py -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| CLI Ergonomia (`expml init`, `--metrics`, `--rules` opcional, `--experiment-dir`) | unit / integration | Fluxo completo CLI a partir de `expml init` sem editar código interno | `tests/unit/test_usability_cli_and_facade.py` | `.venv/bin/pytest tests/unit/test_usability_cli_and_facade.py -v` |
| Fachada Python (`experimental_ml.run_experiment`) | unit | Execução completa de regressão/classificação em ~15 linhas e validação de erros | `tests/unit/test_usability_cli_and_facade.py` | `.venv/bin/pytest tests/unit/test_usability_cli_and_facade.py -v` |
| Documentação por Jornadas | unit | Links, sintaxe AST, imports públicos e validação CLI via argparse | `tests/unit/test_documentation_integrity.py` | `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After T1–T4 | `.venv/bin/pytest tests/unit/test_usability_cli_and_facade.py -v` |
| Full | After T4 | `.venv/bin/pytest tests/ -q` |

---

## Execution Plan

```
T1 --> T2 --> T4
T1 --> T3 --> T4
```

---

## Task Breakdown

### Phase 1: Ergonomia da CLI (`USAB-01`)

#### T1: Implementar `expml init`, `--rules` opcional, `--metrics`, `--experiment-dir` em `run`, caminhos no `report` e erros orientados à resolução [x]

**What**: Criar `src/experimental_ml/cli/cmd_init.py` (`expml init`), atualizar `cli/main.py`, `cli/cmd_data.py`, `cli/cmd_models.py`, `cli/cmd_features.py`, `cli/cmd_run.py` e `cli/cmd_report.py`, com testes TDD em `tests/unit/test_usability_cli_and_facade.py`.  
**Where**: `src/experimental_ml/cli/`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/stages/`, `src/experimental_ml/metrics/catalog.py`  
**Requirement**: USAB-01  
**Tests**: `tests/unit/test_usability_cli_and_facade.py`  
**Gate**: `.venv/bin/pytest tests/unit/test_usability_cli_and_facade.py -v`

---

### Phase 2: Fachada Python de Alto Nível (`USAB-02`)

#### T2: Implementar `experimental_ml.run_experiment` e `ExperimentRunSummary` com PEP 562 lazy export [x]

**What**: Criar `src/experimental_ml/pipeline.py` orquestrando Etapas 1–6 de ponta a ponta com defaults metodológicos explícitos e exportação lazy via `__getattr__` em `src/experimental_ml/__init__.py` (preservando `CLI-10` e `XCUT-02`).  
**Where**: `src/experimental_ml/pipeline.py`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/data/`, `features/`, `models/`, `validation/`, `orchestration/`, `statistics/`, `reporting/`  
**Requirement**: USAB-02  
**Tests**: `tests/unit/test_usability_cli_and_facade.py`  
**Gate**: `.venv/bin/pytest tests/unit/test_usability_cli_and_facade.py -v`

---

### Phase 3: Documentação por Jornadas, Schemas JSON e Guia de Interpretação (`USAB-03`)

#### T3: Criar `cli_schemas_json.md`, `03_interpretando_resultados.md` e reorganizar `docs/README.md` pelas 5 Jornadas [ ]

**What**: Documentar todos os schemas JSON da CLI e aliases de `resolve_estimator_factory` em `docs/referencia/cli_schemas_json.md`, criar o guia prático `docs/guia/03_interpretando_resultados.md`, atualizar `docs/referencia/cli_catalogo.md` com `expml init` e as novas flags, e reorganizar `docs/README.md` pelas 5 Jornadas.  
**Where**: `docs/`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/cli/`  
**Requirement**: USAB-03  
**Tests**: `tests/unit/test_documentation_integrity.py`  
**Gate**: `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v`

---

### Phase 4: Verificação Ponta a Ponta e Suíte Completa

#### T4: Validar fluxo real completo (CLI + Python), pureza `XCUT-02` e suíte global [ ]

**What**: Executar teste ponta a ponta simulando pesquisador iniciante (`expml init` -> `report generate` sem editar código interno) e rodar toda a suíte `pytest tests/ -q`.  
**Where**: `tests/unit/test_usability_cli_and_facade.py`  
**Depends on**: T2, T3  
**Reuses**: `tests/integration/test_mvp_audit_invariants.py`  
**Requirement**: USAB-01, USAB-02, USAB-03  
**Tests**: `tests/unit/test_usability_cli_and_facade.py`, `tests/integration/test_mvp_audit_invariants.py`  
**Gate**: `.venv/bin/pytest tests/ -q`

---

## Checks

**C1** - `expml init` cria projeto válido e o pipeline CLI executa de ponta a ponta com `--rules` opcional, `--metrics` e `--experiment-dir` unificado. (USAB-01, AC-POS3-01-01..04)  
Proof: run unit | tests/unit/test_usability_cli_and_facade.py::test_cli_init_and_end_to_end_workflow PASSED

**C2** - `experimental_ml.run_experiment(...)` executa Etapas 1–6 preservando `CLI-10` e `XCUT-02`. (USAB-02, AC-POS3-02-01, AC-POS3-02-02)  
Proof: run unit | tests/unit/test_usability_cli_and_facade.py::test_python_facade_run_experiment_end_to_end PASSED

**C3** - Documentação por 5 Jornadas, schemas JSON e guia de interpretação passam na suíte de integridade documental. (USAB-03, AC-POS3-03-01, AC-POS3-03-02)  
Proof: run unit | tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T3
- **Next Task:** T4
