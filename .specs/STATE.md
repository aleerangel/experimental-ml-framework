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
- **Phase / Task**: Concluído e Integrado na `main` (PR #4 Merged)
- **Completed**:
  - Marcos M1.1, M1.2, M1.3 e M1.4 concluídos e formalmente homologados.
  - Marco M1.4 implementado com 100% de conformidade: módulo `experimental_ml.data` (`schema`, `types`, `parsing`, `validation`, `loader`, `query`, `__init__`).
  - 29 requisitos (`DATA-01` a `DATA-29`) implementados com testes unitários em `tests/unit/test_data_schemas.py` (29/29 pass).
  - Suíte completa do repositório: 81 testes aprovados (100% de aprovação).
  - Auditoria independente pelo subagente verificador (`author != verifier`) aprovada com veredito `PASS` (0 findings).
  - Portões TLC validados: `validate_spec.py`, `validate_tasks.py`, `validate_verification.py` todos com 0 erros e 0 alertas.
  - Homologação manual executada e formalmente aprovada pelo usuário em 2026-11-04 (`user: "aprovado"`).
  - Fase 1 (Setup e Fundações Transversais) integralmente concluída com sucesso (M1.1, M1.2, M1.3 e M1.4).
  - Pull Request #4 (`feat/m1-4-datasets-schemas`) integrado na branch `main` (commit `c3eb1e6`).
  - Documentação geral do projeto atualizada (`ARQUITETURA_E_CONTRATOS.md`, `ESPECIFICACAO_REQUISITOS.md`, `ETAPA_ATUAL_ENGENHARIA.md`, `README.md`, `.specs/STATE.md`).
- **In-progress**: Concluído
- **Next step**: Iniciar o ciclo de planejamento e especificação do Marco M2 (`data` + `validation` + CLI `data`/`partition`) da Fase 2 (Camada 1 / Triagem e Particionamento)
- **Blockers**: none
- **Branch**: main
