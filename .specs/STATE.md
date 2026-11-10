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

- **Feature**: m3-3-intra-fold-selection (Sub-marco M3.3 — Seleção Dinâmica Intra-Fold de Features e Estabilidade)
- **Phase / Task**: Concluído e Aceito — **Sub-marco M3.3 100% Homologado e Verificado**
- **Completed**:
  - Implementação do modelo imutável `SelectionResult(frozen=True, slots=True)` com tuplas imutáveis, mapeamentos protegidos via `MappingProxyType`, e roundtrip `.to_dict()` / `.from_dict()` (`SEL-01`).
  - Implementação de `select_features_in_fold`: bypass funcional puro imediato para cenários `FIXED` sem exigir `y_train` e sem efetuar cálculos redundantes (`SEL-02`).
  - Implementação de seleção dinâmica via `VARIANCE_THRESHOLD` ajustada estritamente sobre `X_train` (`SEL-03`).
  - Implementação de seleção dinâmica via `TOP_K_RELEVANCE` ranqueando preditores pelo grau de associação com `y_train` via métricas em NumPy puro (`SEL-04`).
  - Implementação de `apply_feature_selection(X_eval, selection_result)` projetando colunas estritamente na ordem definida no treino e rejeitando ausências parciais com `ContractViolationError` (`SEL-05`).
  - Implementação do modelo `SelectionStabilityReport` e da função `compute_selection_stability(fold_selections, n_total_candidates)` calculando similaridade pareada de Jaccard e índice de Kuncheva corrigido para o acaso com tratamento rigoroso de casos de fronteira (`SEL-06`).
  - Salvaguarda mandatória contra seleções vazias (lançando `DataIntegrityError` quando 0 preditores atendem aos critérios de seleção dinâmica) (`SEL-07`).
  - Re-exportação pública em `experimental_ml.features` e suíte de integração ponta a ponta validando ausência de leakage e pureza estrita de runtime sem bibliotecas externas de ML (`SEL-08`, `XCUT-02`).
  - Suíte completa de testes expandida para **228 testes automatizados** com 100% de aprovação (0 regressões).
  - Parecer formal do *Independent Verifier* aprovado com veredito `PASS` (100% de conformidade, zero achados, `validate_verification.py` código 0).
  - Commits registrados na branch `feat/m3-3-intra-fold-selection`: `8c224fa`, `8fa8430`, `0d386c7`, `abe1685`, `044bc2c`, `fe9f201`.
- **In-progress**: Preparação do Sub-marco M3.4 (CLI de Features e Homologação Ponta a Ponta — `expml features explore` e `expml features scenarios`).
- **Next step**: Fazer merge da branch `feat/m3-3-intra-fold-selection` na `main`, criar branch `feat/m3-4-cli-end-to-end` e elaborar a especificação sob `.specs/features/m3-4-cli-end-to-end/spec.md`.
- **Blockers**: none
- **Branch**: feat/m3-3-intra-fold-selection
