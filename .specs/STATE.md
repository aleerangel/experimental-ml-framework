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

### AD-003
- **Decision**: Decomposição modular do Marco M2 em 5 sub-marcos controláveis (M2.1 a M2.5) e catálogo canônico fechado de 15 achados diagnósticos com severidade imutável e ordenação lexicográfica determinística.
- **Reason**: Garantir isolamento conceitual e controle granular de escopo entre triagem/diagnóstico (`m2-1`), saneamento determinístico (`m2-2`), particionamento compartilhado (`m2-3`), CLI modularizada (`m2-4`) e integração transversal (`m2-5`), evitando acoplamento indevido entre camadas.
- **Trade-off**: Requer manutenção de contratos explícitos entre as sub-etapas (ex.: `SanitizedDatasetView` recebida por `validation` sem expor lógica interna de sanitização).
- **Scope**: Marco M2 e módulos `experimental_ml.data` e `experimental_ml.validation`.
- **Date**: 2026-11-06
- **Status**: active

## Handoff

- **Feature**: m2-2-preparation-plan-sanitization (Sub-marco M2.2 — Plano de Preparação e Visão Saneada de Datasets)
- **Phase / Task**: Concluído e Aceito (Branch `feat/m2-2-preparation-plan-sanitization`)
- **Completed**:
  - Sub-marco M2.2 (`m2-2-preparation-plan-sanitization`) implementado, testado e verificado:
    - `PreparationRule`, `UnresolvedFinding`, `PreparationPlan`, `SanitizedDatasetView`: estruturas de dados imutáveis com `frozen=True, slots=True`, proteção via `MappingProxyType` e arrays com `writeable = False`.
    - `_validate_rule_admissibility`: validador estrito do catálogo fechado de regras (`DROP_ROWS`, `EXCLUDE_COLUMN`, `MAP_BINARY_TARGET`, `DEFER_INTRA_FOLD`, `ACCEPT_AS_IS`), rejeitando regras órfãs, não confirmadas ou com parâmetros inválidos via `ConfigurationError`.
    - `create_preparation_plan`: construtor funcional com auditoria de cobertura completa dos achados `CONFIRMED_ISSUE`. Retorna `PreparationPlan` com `status = "READY"`, ordenação canônica e digest determinístico SHA-256 quando totalmente coberto, ou `status = "INCOMPLETE"` com listagem canônica de `unresolved_findings`.
    - `sanitize_dataset`: executor puro de pré-partição que aplica estritamente regras estruturais (`DROP_ROWS`, `EXCLUDE_COLUMN`, `MAP_BINARY_TARGET`), mantendo colunas deferidas (`DEFER_INTRA_FOLD`, `ACCEPT_AS_IS`) 100% bit a bit idênticas ao bundle original (prevenção de vazamento de dados — ADR-002).
    - Preservação da integridade: `bundle` original inalterado (`bundle.dataset_hash` intacto). A visão saneada expõe linhagem completa, ordenação relativa original de `ObservationId`, sequência de `dropped_observation_ids` e calcula deterministicamente seu novo `dataset_hash` via `core.dataset_hash(...)`.
    - Validação de não-vacuidade pós-saneamento ($N > 0$ e features candidatas $> 0$).
    - 23 símbolos públicos exportados em `experimental_ml.data.__all__`.
  - 10 requisitos de preparação (`PREP-01` a `PREP-10`) verificados por 10 checks determinísticos (`check_proofs.py`: 10 pass, 0 fail).
  - Suíte completa do repositório: 133 testes aprovados (100% de aprovação, 0 regressões).
  - Verificação independente por subagente (`author != verifier`) aprovada com veredito `PASS` (0 findings).
  - Validadores documentais TLC: `validate_spec.py`, `validate_tasks.py`, `validate_verification.py` todos com 0 erros e 0 alertas.
  - Artefatos de homologação e resultados (`ACCEPTANCE.md` e `RESULTS.md`) gerados e validados.
- **In-progress**: Sub-marco M2.2 concluído; pronto para avançar para o Sub-marco M2.3 (`partitioning-engine`)
- **Next step**: Iniciar Specify / Design do Sub-marco M2.3 (`PartitionPlan`, `create_partition_plan`, estratégias K-Fold / Group / Stratified / Time)
- **Blockers**: none
- **Branch**: feat/m2-2-preparation-plan-sanitization
