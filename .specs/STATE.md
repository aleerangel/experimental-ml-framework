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
- **Phase / Task**: Concluído e Formalmente Homologado (`APROVADO`)
- **Completed**:
  - `PROCESSO_DE_ACEITE_DE_MARCOS.md` estabelecido em `engenharia_software/`.
  - M1.1 (`m1-1-setup-cli-smoke`) e M1.2 (`core`) implementados, verificados e formalmente aceitos (`APROVADO`).
  - M1.3 (`metrics`) especificado, implementado (T1 a T7), testado (22 checks unitários, 52 testes no total) e verificado (`proofs.md`, `verification.md` PASS).
  - Roteiro de aceitação do consumidor (`ACCEPTANCE.md`) executado com 100% de sucesso.
  - Homologação manual do usuário formalmente concedida em 03/11/2026: *"O M1.3 — Metrics foi formalmente aprovado na homologação manual."* Registrada em `RESULTS.md` e `ACCEPTANCE.md`.
  - Encerramento documental do M1.3 finalizado e sincronizado com `README.md` e `ETAPA_ATUAL_ENGENHARIA.md`.
- **In-progress**: Transição para o próximo marco do roadmap
- **Next step**: Iniciar o Marco M1.4 — Datasets & Schemas
- **Blockers**: none
- **Branch**: feat/m1-3-metrics (pronto para merge em main conforme governança do projeto)
