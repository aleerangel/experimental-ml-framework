# Feature: pos-1-mega-auditoria-mvp

**Approved**: 2026-11-16 - user: "aprovado"

## Problem Statement

Com a conclusão integral do MVP — Onda 1 (Marcos M1 a M7, Etapas 1 a 6), o plano de engenharia (`ARQUITETURA_E_CONTRATOS.md` Seção 7 `TA-POS.1`, `ETAPA_ATUAL_ENGENHARIA.md`) e o processo de aceite (`PROCESSO_DE_ACEITE_DE_MARCOS.md`) determinam a execução da **Mega Auditoria Técnica Transversal do MVP (`TA-POS.1`)** antes do congelamento do código e da elaboração do Guia Definitivo do Pesquisador (`TA-POS.2`).

Para garantir rigor científico e imparcialidade, a auditoria **não pode presumir** que testes ou verificações anteriores de marcos isolados comprovam a correção transversal do sistema: ela deve inspecionar diretamente o código-fonte, os invariantes entre etapas, as asserções dos testes, os metadados de empacotamento e toda a documentação:

1. **Auditoria Independente de Código, Portões e Contratos (Etapas 1–6):**
   - Módulos transversais (`core`, `metrics`) e todas as camadas (`data`, `features`, `models`, `tuning`, `validation`, `orchestration`, `statistics`, `reporting`, `stages`, `cli`).
   - Todos os portões de estágio (`verify_preparation_gate`, `verify_partition_gate`, `verify_scenarios_gate`, `verify_models_gate`, `verify_runs_gate`, `verify_statistics_gate`, `verify_report_gate`).
   - Invariantes científicos e transversais: prevenção estrutural de *data leakage*, imutabilidade, determinismo de sementes/hashes, semântica estrita de `UNDEFINED_NAN` (sem coerção silenciosa para zero), agnóstica a domínios (`RNF02`), conformidade CLI (`CLI-10` imports lazy, `CLI-11` sem hashes brutos no `stdout`) e pureza runtime (`XCUT-02`).
2. **Pureza de Runtime (`XCUT-02`) Livre de Falsos Positivos/Negativos:**
   - Inspeção AST completa em todo `src/experimental_ml/**/*.py` cobrindo `ast.Import`, `ast.ImportFrom` (incluindo imports relativos) e chamadas dinâmicas (`importlib.import_module`, `__import__`), validando contra `sys.stdlib_module_names`, `experimental_ml` e `numpy` (alinhado a `pyproject.toml`), sem falsos positivos em `TYPE_CHECKING` ou falsos negativos em imports condicionais dentro de funções.
3. **Auditoria Cruzada de Documentação, Referências e Estado:**
   - Verificação cruzada entre `src/experimental_ml/`, `tests/`, `pyproject.toml`, `.specs/features/m1..m7/` e os documentos:
     - `engenharia_software/ARQUITETURA_E_CONTRATOS.md`
     - `engenharia_software/ESPECIFICACAO_REQUISITOS.md`
     - `engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`
     - `engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md`
     - `README.md`
     - `REFERENCIAS_E_FUNDAMENTACAO.md`
     - `.specs/STATE.md`
4. **Saneamento e Fechamento Congelável:**
   - Classificação formal (`P0`, `P1`, `P2`), correção obrigatória de 100% dos achados `P0` e `P1` via TDD com testes de regressão e emissão de relatório auditável (`AUDIT_REPORT.md` + `ACCEPTANCE.md` + `RESULTS.md` + `verification.md` com `author != verifier`).

## Out of Scope

- Implementação de funcionalidades da Onda 2 (`MULTI_TARGET_REGRESSION`, `TargetTransformSpec`, `unlabeled_pool`, `PCA`, `BootstrapSplit`, `TemporalSplit`) ou Evoluções Posteriores (Seção 6.2 de `ARQUITETURA_E_CONTRATOS.md`).
- Elaboração do Guia Definitivo do Pesquisador & Cookbook Científico (`TA-POS.2`, sub-marco seguinte após congelamento do MVP).
- Homologação Científica Externa (`TA-POS.3` / `CA02`), conduzida exclusivamente pelo pesquisador fora do repositório.

## Assumptions & Open Questions

**Open questions:** none - o escopo completo de `TA-POS.1` foi alinhado com o usuário e com `ARQUITETURA_E_CONTRATOS.md`, `ESPECIFICACAO_REQUISITOS.md` e `PROCESSO_DE_ACEITE_DE_MARCOS.md`.

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Regra de independência da auditoria | Inspecionar código, testes e documentos diretamente; não aceitar `verification.md` prévios como prova suficiente | Evita pontos cegos entre marcos e cumpre o princípio `author != verifier` de `PROCESSO_DE_ACEITE_DE_MARCOS.md` |
| Definição de severidade (`P0` / `P1` / `P2`) | `P0`: violação científica (leakage, coerção de `NaN`, quebra de integridade/portão); `P1`: divergência contratual, de CLI/API, de pureza `XCUT-02` ou documental relevante; `P2`: melhoria menor/cosmética | Alinhado a `REV-M2`, `ACH-M5` e aos critérios `APROVADO` vs `REJEITADO` de `PROCESSO_DE_ACEITE_DE_MARCOS.md` |
| Critério de bloqueio para congelamento do MVP | `0` achados `P0` e `0` achados `P1` em aberto; todos os `P0`/`P1` corrigidos com testes de regressão | Garante base congelável antes de `TA-POS.2` e `CA02` |
| Verificação AST de pureza (`XCUT-02`) | Usar `sys.stdlib_module_names`, permitir apenas stdlib + `numpy` + `experimental_ml`, checando imports estáticos e dinâmicos | Elimina falsos positivos (stdlib/relativos) e falsos negativos (imports locais dentro de funções) |

## User Stories

### US-POS1-01 (Priority: P1) — Auditoria Independente de Código, Portões e Pureza Runtime (Etapas 1–6)
As a framework maintainer,  
I want an independent cross-stage technical audit inspecting code, stage gates, invariants, CLI compliance, and AST runtime purity (`XCUT-02`) without blindly trusting prior milestone checks,  
So that any hidden `P0`/`P1` defects across stages 1–6 are uncovered and fixed before freezing the MVP.

#### Acceptance Criteria
- **AC-POS1-01-01**: WHEN running automated AST and runtime import verification across all modules in `src/experimental_ml/`, the system SHALL detect both static (`import`/`from`) and dynamic (`importlib.import_module`/`__import__`) imports and confirm zero external runtime dependencies beyond Python stdlib (`sys.stdlib_module_names`) and `numpy` (`XCUT-02`), without false positives on relative or `TYPE_CHECKING`-only imports.
- **AC-POS1-01-02**: WHEN auditing cross-stage contracts (`core`, `metrics`, `data`, `features`, `models`, `tuning`, `validation`, `orchestration`, `statistics`, `reporting`, `cli`) and all 7 stage gates (`verify_preparation_gate` through `verify_report_gate`), the audit SHALL independently verify anti-leakage, `UNDEFINED_NAN` semantics, domain independence (`RNF02`), `CLI-10`/`CLI-11`, and fix all `P0`/`P1` findings with regression tests.

---

### US-POS1-02 (Priority: P1) — Auditoria Cruzada Documental e Critérios de Fechamento Congelável
As a framework maintainer,  
I want a systematic cross-check between codebase/tests/packaging and all engineering documents, references, and `.specs/STATE.md`, with traceable resolution of all `P0`/`P1` discrepancies,  
So that the MVP can be formally frozen with zero blocking findings for `TA-POS.2` and `CA02`.

#### Acceptance Criteria
- **AC-POS1-02-01**: WHEN cross-checking `engenharia_software/*.md`, `README.md`, `REFERENCIAS_E_FUNDAMENTACAO.md`, `pyproject.toml`, `.specs/STATE.md`, and `.specs/features/m1..m7/` against `src/experimental_ml/` and `tests/`, every `P0`/`P1` discrepancy between requirements, implementation, tests, and recorded state SHALL be logged and resolved.
- **AC-POS1-02-02**: WHEN closing `pos-1-mega-auditoria-mvp`, an auditable report SHALL record every finding (`P0`/`P1`/`P2`), its evidence, resolution commit/regression test, and confirm `0` open `P0`/`P1` findings, full `pytest` suite pass, and `validate_verification.py` = 0 errors (`author != verifier`).

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| AUD-01 | AC-POS1-01-01, AC-POS1-01-02 | `src/experimental_ml/*`, `tests/*` | pending |
| AUD-02 | AC-POS1-02-01, AC-POS1-02-02 | `engenharia_software/*`, `README.md`, `REFERENCIAS_E_FUNDAMENTACAO.md`, `pyproject.toml`, `.specs/STATE.md` | pending |
