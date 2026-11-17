# pos-2b-notebooks-interativos Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill.

---

**Design**: `.specs/features/pos-2b-notebooks-interativos/design.md`  
**Status**: Completed  
**Approved**: 2026-11-16 - user: "Vamos fazer isso agora"  
**Build**: none - Notebooks JSON nbformat 4.5 e testes pytest  
**Run unit**: .venv/bin/pytest tests/unit/test_notebooks_execution.py tests/unit/test_documentation_integrity.py -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Execução de Notebooks (`tests/unit/test_notebooks_execution.py`) | unit | Validação nbformat v4+, pureza AST `XCUT-02` e execução sequencial de 100% das células | `tests/unit/test_notebooks_execution.py` | `.venv/bin/pytest tests/unit/test_notebooks_execution.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After T1–T4 | `.venv/bin/pytest tests/unit/test_notebooks_execution.py -v` |
| Full | After T4 | `.venv/bin/pytest tests/ -q` |

---

## Execution Plan

```
T1 --> T2 --> T4
T1 --> T3 --> T4
```

---

## Task Breakdown

### Phase 1: Suíte de Validação de Notebooks

#### T1: Criar suíte de validação e execução de notebooks (`tests/unit/test_notebooks_execution.py`) [x]

**What**: Implementar teste que valida estrutura `nbformat >= 4`, ausência de dependências proibidas (`XCUT-02`) e executa todas as células de código de `notebooks/*.ipynb` em `tmp_path`.  
**Where**: `tests/unit/test_notebooks_execution.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/`  
**Requirement**: NB-01  
**Tests**: `tests/unit/test_notebooks_execution.py`  
**Gate**: `.venv/bin/pytest tests/unit/test_notebooks_execution.py -v`

---

### Phase 2: Notebooks 01 e 02

#### T2: Criar `01_tour_6_etapas.ipynb` e `02_ablacao_lssvm_prognose_florestal.ipynb` [x]

**What**: Gerar os dois primeiros notebooks interativos completos cobrindo o tour das 6 etapas e o estudo de ablação LS-SVM em prognose florestal.  
**Where**: `notebooks/`  
**Depends on**: T1  
**Reuses**: `docs/guia/02_tutorial_6_etapas.md`, `docs/guias_praticos/06_ablacao_variantes_algoritmo_lssvm.md`  
**Requirement**: NB-02  
**Tests**: `tests/unit/test_notebooks_execution.py`  
**Gate**: `.venv/bin/pytest tests/unit/test_notebooks_execution.py -v`

---

### Phase 3: Notebooks 03 e 04

#### T3: Criar `03_validacao_agrupada_e_prevencao_leakage.ipynb` e `04_pos_experimento_relatorios_artigo.ipynb` [x]

**What**: Gerar os notebooks de validação agrupada + bloqueios ao vivo de portões e de pós-experimento somente-leitura com exportação LaTeX/SVG e pacote reduzido.  
**Where**: `notebooks/`  
**Depends on**: T1  
**Reuses**: `docs/guias_praticos/03_validacao_cruzada_agrupada_holdout.md`, `docs/guias_praticos/08_fluxo_desacoplado_jupyter_relatorios.md`  
**Requirement**: NB-02  
**Tests**: `tests/unit/test_notebooks_execution.py`  
**Gate**: `.venv/bin/pytest tests/unit/test_notebooks_execution.py -v`

---

### Phase 4: Navegação e Fechamento

#### T4: Atualizar `README.md` e `docs/README.md` com seção de Notebooks e validar suíte completa [x]

**What**: Adicionar links para `notebooks/` em `README.md` e `docs/README.md` e executar toda a suíte `pytest tests/ -q`.  
**Where**: `README.md`  
**Depends on**: T2, T3  
**Reuses**: `tests/unit/test_documentation_integrity.py`  
**Requirement**: NB-01, NB-02  
**Tests**: `tests/unit/test_notebooks_execution.py`, `tests/unit/test_documentation_integrity.py`  
**Gate**: `.venv/bin/pytest tests/ -q`

---

## Checks

**C1** - Todos os 4 notebooks em `notebooks/` possuem esquema `nbformat >= 4`, zero dependências fora de stdlib/`numpy` e executam 100% das células sem erro. (NB-01, NB-02, AC-NB-01-01, AC-NB-02-01..04)  
Proof: run unit | tests/unit/test_notebooks_execution.py::test_all_notebooks_valid_and_executable PASSED

**C2** - `README.md` e `docs/README.md` apontam para `notebooks/` e todos os links e invariantes `XCUT-02` passam. (NB-02, AC-NB-02-05)  
Proof: run unit | tests/unit/test_documentation_integrity.py::test_markdown_links_and_anchors_valid PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T4
- **Next Task:** Done
