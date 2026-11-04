# STATE

## Decisions

### AD-001
- **Decision**: Adotar Hatchling (`hatchling.build`) como build-backend padronizado no `pyproject.toml` e layout `src/experimental_ml/`.
- **Reason**: Backend moderno em conformidade com PEP 517/518/621, suporte nativo ao layout `src/` e empacotamento enxuto sem dependências de compilação C/C++.
- **Trade-off**: Exige ferramentas de empacotamento compatíveis com padrões modernos (PEP 621), sem suporte nativo a extensões C legadas de `setuptools`.
- **Scope**: Todo o framework `experimental-ml-framework`.
- **Date**: 2026-10-31
- **Status**: active

### AD-002
- **Decision**: Adotar o processo de aceite de marcos (*Milestone Acceptance*) baseado em três registros (`SPEC.md`, `ACCEPTANCE.md`, `RESULTS.md`), integrado ao fluxo TLC Spec-Driven.
- **Reason**: Diferenciar a aprovação em testes automatizados do aceite formal da entrega, prevendo validação prática por interfaces públicas sob a perspectiva do consumidor e registro explícito de pendências.
- **Trade-off**: Requer a elaboração e manutenção de três documentos por marco (`SPEC.md`, `ACCEPTANCE.md`, `RESULTS.md`), mantendo pendências manuais registradas explicitamente como PENDENTE.
- **Scope**: Todos os marcos do framework (retroativo a M1.1 e M1.2; mandatório de M1.3 a M7).
- **Date**: 2026-11-02
- **Status**: active

## Handoff

- **Feature**: m1-3-metrics (Marco M1.3 — Metrics)
- **Phase / Task**: Tasks aprovadas (`tasks.md`, `design.md`, `ACCEPTANCE.md`)
- **Completed**:
  - `PROCESSO_DE_ACEITE_DE_MARCOS.md` estabelecido em `engenharia_software/`.
  - M1.1 e M1.2 implementados, verificados e aceitos (`APROVADO`).
  - Especificação do Marco M1.3 (`SPEC.md` e `spec.md`) aprovada.
  - Arquitetura técnica (`design.md`) aprovada.
  - Roteiro de aceitação do consumidor (`ACCEPTANCE.md`) criado.
  - Plano de tarefas atômicas (`tasks.md`) aprovado e validado via `validate_tasks.py`.
- **In-progress**: Início da fase Execute de M1.3
- **Next step**: Execução sequencial das tarefas T1 a T7 conforme `tasks.md`
- **Blockers**: none
- **Uncommitted files**: .specs/features/m1-3-metrics/design.md, .specs/features/m1-3-metrics/ACCEPTANCE.md, .specs/features/m1-3-metrics/tasks.md, .specs/STATE.md
- **Branch**: feat/m1-3-metrics
