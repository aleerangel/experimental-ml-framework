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

- **Feature**: m1-5-foundation-hardening (Marco M1.5 — Saneamento e Hardening da Fundação M1)
- **Phase / Task**: Concluído e Auditado (Branch `fix/m1-5-foundation-hardening`)
- **Completed**:
  - Marcos M1.1, M1.2, M1.3, M1.4 e M1.5 concluídos e formalmente homologados.
  - Auditoria Geral de Integridade M1 (`m1-integrity-review`) realizada com preservação integral de seus artefatos (0 bytes diff).
  - Saneamento M1.5 concluído com 100% de conformidade técnica:
    - 10 achados de auditoria resolvidos: P0 (`AUD-F-001`, `AUD-F-004`, `AUD-F-005`, `AUD-F-006`, `AUD-F-008`, `AUD-F-009`) e P1 selecionados (`AUD-F-002`, `AUD-F-007`, `AUD-F-010`, `AUD-F-013`).
    - 6 achados documentados como `ADIADO` com justificativa e destino formalizado (`AUD-F-003`, `AUD-F-011`, `AUD-F-012`, `AUD-F-014`, `AUD-F-015`, `AUD-F-016`).
    - Enquadramento binário de `dataset_hash` sem ambiguidade com suporte explícito a `observation_ids` preservando direção arquitetural `data -> core`.
    - Detecção centralizada de escalares `NaN` e ausentes (`is_nan_scalar`, `is_missing_scalar`) em `core` e reutilização estrita em `data`.
    - Preservação de instâncias `ObservationId` em fatiamento de dados (`slice_bundle_by_observation_ids`).
    - Whitelist estrita de escalares imutáveis e semântica unificada de ausentes em colunas `object`, além de captura de `OverflowError` em `int64`.
    - Exemplos executáveis e documentação sincronizados; criação de suíte de integração transversal `tests/integration/test_m1_foundation_integration.py`.
  - 15 requisitos de hardening (`HARD-01` a `HARD-15`) verificados por 15 checks determinísticos (`check_proofs.py`: 15 pass, 0 fail).
  - Suíte completa do repositório: 96 testes aprovados (100% de aprovação).
  - Auditoria independente pelo subagente verificador (`author != verifier`) aprovada com veredito `PASS` (0 findings).
  - Portões TLC validados: `validate_spec.py`, `validate_tasks.py`, `validate_verification.py` todos com 0 erros e 0 alertas.
  - Roteiro de homologação do consumidor (`ACCEPTANCE.md`) executado com sucesso e registrado em `RESULTS.md`.
  - Parecer técnico oficial atualizado: **`APTO PARA INÍCIO DO MARCO M2`**.
- **In-progress**: Concluído (aguardando merge do PR de hardening e abertura do Marco M2)
- **Next step**: Iniciar o ciclo de planejamento e especificação do Marco M2 (`data` + `validation` + CLI `data`/`partition`) da Fase 2 (Camada 1 / Triagem e Particionamento)
- **Blockers**: none
- **Branch**: fix/m1-5-foundation-hardening
