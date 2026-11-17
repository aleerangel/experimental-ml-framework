# pos-2-guia-pesquisador-cookbook Tasks (TA-POS.2 Guia do Pesquisador, Cookbook, Referências e README)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/pos-2-guia-pesquisador-cookbook/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-16 - user: "aprovado"  
**Build**: none - Python interpreted package and Markdown GFM documentation; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/test_documentation_integrity.py -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Integridade Documental em 5 Níveis (`tests/unit/test_documentation_integrity.py`) | unit | Links relativos e âncoras, sintaxe AST Python, imports reais da API pública, validação léxica CLI `expml` e smoke test executável do Quickstart | `tests/unit/test_documentation_integrity.py` | `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v` |
| Pureza e Invariantes Transversais | integration | Pureza `XCUT-02` e integridade global da suíte MVP (591+ testes) | `tests/integration/test_mvp_audit_invariants.py` | `.venv/bin/pytest tests/ -q` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After T1–T5 | `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v` |
| Full | After T5 | `.venv/bin/pytest tests/ -q` |
| Build | After feature completion | `.venv/bin/pytest tests/ -q` |

---

## Execution Plan

### Phase 1: Suíte de Integridade Documental (`P1`)

```
T1
```

### Phase 2: Índice Central e Guia do Pesquisador (`P2`)

```
T1 --> T2
```

### Phase 3: Scientific Cookbook e Referências de API/CLI (`P3`)

```
T2 --> T3
T2 --> T4
```

### Phase 4: Limpeza do README.md e Fechamento (`P4`)

```
T3 --> T5
T4 --> T5
```

---

## Task Breakdown

### Phase 1: Suíte de Integridade Documental

#### T1: Implementar testes automatizados de integridade documental em 5 níveis [x]

**What**: Criar `tests/unit/test_documentation_integrity.py` verificando em `README.md` e `docs/**/*.md`: (1) links relativos e âncoras; (2) sintaxe AST de blocos Python regulares; (3) resolução estática de imports de `experimental_ml.*` contra a API pública (`__init__.py`/`__all__`); (4) validação léxica de subcomandos `expml` em blocos `bash`; (5) execução ponta a ponta (smoke test) de blocos marcados com `# executable-smoke-test` no Quickstart.  
**Where**: `tests/unit/test_documentation_integrity.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/`  
**Requirement**: DOC-06  
**Tests**: `tests/unit/test_documentation_integrity.py`  
**Gate**: `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v`

---

### Phase 2: Índice Central e Guia do Pesquisador

#### T2: Elaborar `docs/README.md`, Início Rápido em 5 passos e Tutorial das 6 Etapas [x]

**What**: Criar `docs/README.md` (hub unificador em português com mapa pedagógico), `docs/guia/01_inicio_rapido.md` (5 passos com CLI conciso e script smoke-test executável) e `docs/guia/02_tutorial_6_etapas.md` (cobrindo rigorosamente as 6 etapas oficiais da Seção 3 de `ARQUITETURA_E_CONTRATOS.md`, incluindo 4A/4B na Etapa 4, invariantes anti-leakage e formulações matemáticas).  
**Where**: `docs/guia/`  
**Depends on**: T1  
**Reuses**: `engenharia_software/ARQUITETURA_E_CONTRATOS.md`, `REFERENCIAS_E_FUNDAMENTACAO.md`  
**Requirement**: DOC-01, DOC-02  
**Tests**: `tests/unit/test_documentation_integrity.py`  
**Gate**: `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v`

---

### Phase 3: Scientific Cookbook e Referências de API/CLI

#### T3: Elaborar as 5 receitas avançadas do Scientific Cookbook em `docs/cookbook/` [x]

**What**: Criar as 5 receitas autocontidas em português: `01_modelos_analiticos_vs_treinados.md`, `02_metricas_quanticas_e_probabilisticas.md`, `03_validacao_cruzada_agrupada_holdout.md`, `04_otimizacao_pareto_multiobjetivo.md` e `05_pacotes_reprodutibilidade_conferencias.md`, todas estritamente alinhadas aos contratos implementados no MVP.  
**Where**: `docs/cookbook/`  
**Depends on**: T2  
**Reuses**: `src/experimental_ml/models/`, `src/experimental_ml/metrics/`, `src/experimental_ml/validation/`, `src/experimental_ml/statistics/`, `src/experimental_ml/reporting/`  
**Requirement**: DOC-03  
**Tests**: `tests/unit/test_documentation_integrity.py`  
**Gate**: `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v`

---

#### T4: Elaborar os catálogos completos de API Python e CLI `expml` em `docs/referencia/` [x]

**What**: Criar `docs/referencia/api_python.md` catalogando as APIs públicas exportadas nos `__init__.py`/`__all__` dos 11 pacotes (`core`, `data`, `metrics`, `features`, `models`, `tuning`, `validation`, `orchestration`, `statistics`, `reporting`, `stages`), e `docs/referencia/cli_catalogo.md` catalogando todos os comandos, subcomandos, opções, artefatos e códigos de saída reais (`0`, `1`, `2`) do `expml`.  
**Where**: `docs/referencia/`  
**Depends on**: T2  
**Reuses**: `src/experimental_ml/*/__init__.py`, `src/experimental_ml/cli/`  
**Requirement**: DOC-04  
**Tests**: `tests/unit/test_documentation_integrity.py`  
**Gate**: `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v`

---

### Phase 4: Limpeza do README.md e Fechamento

#### T5: Enxugar `README.md`, validar integridade total e executar suíte completa de testes [ ]

**What**: Reestrurar `README.md` removendo blocos longos de código e detalhamento de engenharia/requisitos, mantendo badges, proposta de valor, instalação em 1 linha, fluxo CLI resumido de 1 linha e tabela completa de navegação para `docs/`, `engenharia_software/` e `REFERENCIAS_E_FUNDAMENTACAO.md`. Executar toda a suíte `pytest tests/ -q` e validar pureza `XCUT-02`.  
**Where**: `README.md`  
**Depends on**: T3, T4  
**Reuses**: `docs/README.md`, `engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`  
**Requirement**: DOC-05, DOC-06  
**Tests**: `tests/unit/test_documentation_integrity.py`, `tests/integration/test_mvp_audit_invariants.py`  
**Gate**: `.venv/bin/pytest tests/ -q`

---

## Checks

**C1** - Estrutura modular em português (`docs/README.md`, `docs/guia/`, `docs/cookbook/`, `docs/referencia/`) e links relativos válidos sem referências quebradas. (DOC-01, DOC-02, DOC-03, DOC-04, DOC-06, AC-POS2-01-01, AC-POS2-01-02, AC-POS2-06-01)  
Proof: run unit | tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid PASSED

**C2** - Sintaxe AST válida em blocos Python, resolução estática de imports públicos nos 11 pacotes e conformidade léxica dos comandos CLI `expml`. (DOC-04, DOC-06, AC-POS2-04-01, AC-POS2-04-02, AC-POS2-06-01)  
Proof: run unit | tests/unit/test_documentation_integrity.py::test_python_snippets_ast_and_public_imports PASSED

**C3** - Validação léxica de CLI `expml` em blocos shell e execução ponta a ponta (smoke test) do exemplo executável do Início Rápido. (DOC-02, DOC-06, AC-POS2-02-01, AC-POS2-06-01)  
Proof: run unit | tests/unit/test_documentation_integrity.py::test_cli_blocks_and_quickstart_smoke_execution PASSED

**C4** - `README.md` enxuto e equilibrado (sem exemplos extensos de código de implementação ou detalhamento de engenharia/requisitos), apontando diretamente para `docs/`, `engenharia_software/` e `REFERENCIAS_E_FUNDAMENTACAO.md`. (DOC-05, AC-POS2-05-01, AC-POS2-05-02)  
Proof: run unit | tests/unit/test_documentation_integrity.py::test_readme_lean_structure_and_pointers PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T5
- **Next Task:** Done
