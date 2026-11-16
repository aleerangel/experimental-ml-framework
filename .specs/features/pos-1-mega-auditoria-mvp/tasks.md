# pos-1-mega-auditoria-mvp Tasks (TA-POS.1 Mega Auditoria Transversal do MVP)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/pos-1-mega-auditoria-mvp/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-16 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/integration/test_mvp_audit_invariants.py -v  

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| Transversal Audit Invariants (`tests/integration/test_mvp_audit_invariants.py`) | integration | Pureza AST estática/dinâmica `XCUT-02` em `src/experimental_ml/`, presença e assinaturas dos 7 portões em `stage_gates.py`, conformidade `CLI-10`/`CLI-11` e neutralidade `RNF02` | `tests/integration/test_mvp_audit_invariants.py` | `.venv/bin/pytest tests/integration/test_mvp_audit_invariants.py -v` |
| Cross-Doc & Code Audit (`AUDIT_REPORT.md`) | audit | Inspeção direta de código, testes, `engenharia_software/*.md`, `README.md`, `REFERENCIAS_E_FUNDAMENTACAO.md`, `pyproject.toml`, `.specs/STATE.md` e saneamento de 100% dos `P0`/`P1` | `.specs/features/pos-1-mega-auditoria-mvp/AUDIT_REPORT.md` | `.venv/bin/pytest tests/ -q` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After T1/T3 | `.venv/bin/pytest tests/integration/test_mvp_audit_invariants.py -v` |
| Full | After T2/T3 | `.venv/bin/pytest tests/ -q` |
| Build | After feature completion | `.venv/bin/pytest tests/ -q` |

---

## Execution Plan

### Phase 1: Invariantes Transversais (`P1`)

```
T1
```

### Phase 2: Auditoria Cruzada Independente (`P2`)

```
T1 --> T2
```

### Phase 3: Saneamento TDD de Achados P0/P1 (`P3`)

```
T2 --> T3
```

---

## Task Breakdown

### Phase 1: Invariantes Transversais

#### T1: Criar suíte automatizada de invariantes transversais do MVP (`XCUT-02`, 7 portões, `CLI-10`, `RNF02`) [x]

**What**: Criar `tests/integration/test_mvp_audit_invariants.py` validando via AST que 100% de `src/experimental_ml/**/*.py` importa apenas stdlib (`sys.stdlib_module_names`), `experimental_ml` e `numpy` (incluindo detecção de `importlib.import_module`/`__import__` e sem falsos positivos em `TYPE_CHECKING`), validando a presença dos 7 portões (`verify_preparation_gate` a `verify_report_gate`), conformidade `CLI-10` (sem NumPy no import inicial de `cli.main`) e independência de domínio (`RNF02`).  
**Where**: `tests/integration/test_mvp_audit_invariants.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/`  
**Requirement**: AUD-01  
**Tests**: `tests/integration/test_mvp_audit_invariants.py`  
**Gate**: `.venv/bin/pytest tests/integration/test_mvp_audit_invariants.py -v`

---

### Phase 2: Auditoria Cruzada Independente

#### T2: Executar auditoria cruzada independente (Código ↔ Docs de Engenharia ↔ `README.md` ↔ `REFERENCIAS_E_FUNDAMENTACAO.md`) [ ]

**What**: Inspecionar diretamente o código das Etapas 1–6, suíte de testes, `pyproject.toml`, `engenharia_software/*.md`, `README.md`, `REFERENCIAS_E_FUNDAMENTACAO.md` e `.specs/STATE.md`, registrando todos os achados classificados por severidade (`P0`/`P1`/`P2`) em `.specs/features/pos-1-mega-auditoria-mvp/AUDIT_REPORT.md`.  
**Where**: `.specs/features/pos-1-mega-auditoria-mvp/AUDIT_REPORT.md`  
**Depends on**: T1  
**Reuses**: `engenharia_software/*`, `README.md`, `REFERENCIAS_E_FUNDAMENTACAO.md`, `.specs/STATE.md`  
**Requirement**: AUD-01, AUD-02  
**Tests**: `tests/integration/test_mvp_audit_invariants.py`  
**Gate**: `.venv/bin/pytest tests/integration/test_mvp_audit_invariants.py -v`

---

### Phase 3: Saneamento TDD de Achados P0/P1

#### T3: Sanear 100% dos achados `P0`/`P1` e validar fechamento congelável do MVP [ ]

**What**: Corrigir todos os achados `P0` e `P1` registrados em `AUDIT_REPORT.md` (código, testes de regressão e/ou documentação), atualizar `AUDIT_REPORT.md` comprovando `0` achados `P0`/`P1` abertos e rodar a suíte completa de testes (`pytest tests/ -q`).  
**Where**: `.specs/features/pos-1-mega-auditoria-mvp/AUDIT_REPORT.md`  
**Depends on**: T2  
**Reuses**: `tests/integration/test_mvp_audit_invariants.py`  
**Requirement**: AUD-01, AUD-02  
**Tests**: `tests/integration/test_mvp_audit_invariants.py`  
**Gate**: `.venv/bin/pytest tests/ -q`

---

## Checks

**C1** - Inspeção AST em todo `src/experimental_ml/` confirma pureza runtime `XCUT-02` (apenas stdlib + `numpy`) sem falsos positivos/negativos. (AUD-01, AC-POS1-01-01)  
Proof: run unit | tests/integration/test_mvp_audit_invariants.py::test_audit_xcut02_runtime_purity_ast PASSED

**C2** - Todos os 7 portões de estágio, `CLI-10` (imports lazy) e neutralidade de domínio `RNF02` verificados transversalmente. (AUD-01, AC-POS1-01-02)  
Proof: run unit | tests/integration/test_mvp_audit_invariants.py::test_audit_stage_gates_cli_and_domain_neutrality PASSED

**C3** - Auditoria cruzada completa documentada em `AUDIT_REPORT.md` com `0` achados `P0` e `0` achados `P1` em aberto após saneamento. (AUD-02, AC-POS1-02-01, AC-POS1-02-02)  
Proof: run unit | tests/integration/test_mvp_audit_invariants.py::test_audit_report_zero_open_p0_p1 PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T1
- **Next Task:** T2
