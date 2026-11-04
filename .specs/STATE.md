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

- **Feature**: m1-4-datasets-schemas (Marco M1.4 — Datasets & Schemas)
- **Phase / Task**: Proposta de Especificação em Revisão (Specify)
- **Completed**:
  - Marcos M1.1, M1.2 e M1.3 concluídos e homologados.
  - Proposta de especificação do Marco M1.4 elaborada (`spec.md` e `SPEC.md`) com 20 requisitos rastreáveis em notação EARS (`DATA-01` a `DATA-20`).
  - Validação determinística de especificação executada com 0 erros e 0 alertas (`validate_spec.py m1-4-datasets-schemas --strict`).
- **In-progress**: Revisão da especificação do Marco M1.4 pelo usuário
- **Next step**: Aguardar revisão/aprovação da especificação antes de avançar para a fase Design
- **Blockers**: none
- **Branch**: feat/m1-4-datasets-schemas
