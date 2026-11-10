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

### AD-004
- **Decision**: Hardening de integridade pós-auditoria da etapa M2 com salvaguardas matemáticas contra folds vazios, tipagem estruturada em JSON codecs, APIs públicas de view slicing/reconstrução e exportações dinâmicas via PEP 562 para pureza de runtime na CLI.
- **Reason**: Sanar as divergências identificadas na auditoria transversal do Marco M2 (`REV-M2-01` a `REV-M2-11`), eliminando fragilidades em partições temporais com NaN, preservando fidelidade estrita de tipos primitivos em mapeamentos de rótulos e evitando que a CLI ou consumidores externos dependam de código privado.
- **Trade-off**: Requer manutenção de estruturas tipadas explícitas em codecs JSON (`key`, `key_type`, `value`) e recálculo canônico de hash de subconjuntos no fatiamento de views.
- **Scope**: Módulos `core`, `data`, `validation`, `stages` e `cli`.
- **Date**: 2026-11-09
- **Status**: active

## Handoff

- **Feature**: m3-4-cli-end-to-end (Sub-marco M3.4 — CLI de Features e Homologação Ponta a Ponta)
- **Phase / Task**: Concluído e Aceito — **Marco M3 Integralmente Homologado e Verificado**
- **Completed**:
  - Implementação de `src/experimental_ml/cli/cmd_features.py` e registro do subcomando `features` no despachante principal `expml` (`FEAT-01`).
  - Implementação de `expml features explore`: reconstituição da visão saneada, execução de `explore_features`, gravação atômica de `reports/exploratory_features.json` com rotulagem `EXPLORATORY_FULL_DATA` e proteção `--force` (`FEAT-02`, `FEAT-03`).
  - Implementação de `expml features scenarios`: validação semântica e anti-leakage contra a base e gravação de `configuration/scenarios.json` (`FEAT-04`).
  - Tratamento de exceções e padronização de códigos de saída: rejeição de cenários inválidos com código `2` e mensagens limpas no `stderr` sem tracebacks Python (`FEAT-05`).
  - Implementação de `expml features verify`: verificação de portão de validação de cenários via `verify_scenarios_gate` (`FEAT-06`).
  - Cumprimento rigoroso do contrato `CLI-10`: pureza arquitetural sem `numpy` ou `hashlib` em `sys.modules` na carga inicial da CLI (`FEAT-07`).
  - Homologação integrada multi-etapa via subprocessos independentes encadeando Etapa 1, Etapa 2 e Etapa 4A com zero hashes de 64 caracteres expostos em terminal (`FEAT-08`).
  - Suíte completa de testes expandida para **236 testes automatizados** com 100% de aprovação (0 regressões).
  - Parecer formal do *Independent Verifier* aprovado com veredito `PASS` (100% de conformidade, zero achados, `validate_verification.py` código 0).
  - Commits registrados na branch `feat/m3-4-cli-end-to-end`: `f9e0929`, `cbdfb32`, `196d734`, `e418c20`, `37f4f71`.
- **In-progress**: Conclusão da Etapa 2 (Feature Engineering & Scenarios) e preparação para o Marco M4 (Modelos e Tuning).
- **Next step**: Fazer merge da branch `feat/m3-4-cli-end-to-end` na `main`, atualizar governança e iniciar a especificação do Marco M4.
- **Blockers**: none
- **Branch**: feat/m3-4-cli-end-to-end
