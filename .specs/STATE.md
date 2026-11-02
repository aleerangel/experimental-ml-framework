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

- **Feature**: Processo de Aceite de Marcos (Milestone Acceptance)
- **Phase / Task**: Documentação retroativa de M1.1 e M1.2 concluída; integração com TLC formalizada
- **Completed**:
  - `PROCESSO_DE_ACEITE_DE_MARCOS.md` criado em `engenharia_software/`.
  - M1.1 documentado com `SPEC.md`, `ACCEPTANCE.md` e `RESULTS.md` sob `.specs/features/m1-1-setup-cli-smoke/`.
  - M1.2 documentado com `SPEC.md`, `ACCEPTANCE.md` e `RESULTS.md` sob `.specs/features/m1-2-core/`.
  - Implementação e testes automatizados de M1.1 (12/12) e M1.2 (18/18) aprovados.
  - Verificação independente de M1.2 aprovada (`verification.md` PASS).
- **In-progress**: Homologação manual de M1.1 e M1.2
- **Next step**: Execução da homologação manual de M1.1 e M1.2; em seguida, início da fase Specify de M1.3 (`metrics`)
- **Blockers**: none
- **Uncommitted files**: engenharia_software/, .specs/
- **Branch**: feat/m1-2-core
