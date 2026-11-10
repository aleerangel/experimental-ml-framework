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

- **Feature**: m3-1-exploratory-features (Sub-marco M3.1 — Relatório Exploratório de Relações de Features)
- **Phase / Task**: Concluído e Aceito — **Sub-marco M3.1 100% Homologado e Verificado**
- **Completed**:
  - Implementação dos modelos de dados imutáveis `ExploratoryFeatureReport`, `AssociationMeasure`, `RedundancyPair`, constante `SCOPE_EXPLORATORY_FULL_DATA = "EXPLORATORY_FULL_DATA"` e avisos metodológicos mandatórios (`CA-E2-01`, `EXP-01`, `EXP-07`).
  - Serialização determinística `.to_dict()` e reconstrução `.from_dict()` compatível com JSON RFC 8259 (`allow_nan=False`).
  - Implementação pura em NumPy dos algoritmos estatísticos `compute_pearson`, `compute_spearman` (com fractional ranking para empates), `compute_correlation_ratio` ($\eta$) e `compute_cramers_v` ($V$), com tratamento estrito de variância nula e degenerescência retornando `MetricStatus.UNDEFINED_NAN` (ADR-005, CA-GER-03, `EXP-02` a `EXP-05`).
  - Implementação de `explore_features(view, redundancy_threshold=0.85)` com despacho por tipo de tarefa, matriz de redundância preditor-preditor e extração canônica ordenada de pares de alta redundância (`EXP-06`, `EXP-08`).
  - Exportação da API pública em `src/experimental_ml/features/__init__.py`.
  - Suíte completa de testes expandida para **208 testes automatizados** com 100% de aprovação (0 regressões).
  - Parecer formal do *Independent Verifier* aprovado com veredito `PASS` (100% de conformidade, zero achados, `validate_verification.py` código 0).
  - Commits registrados na branch `main`: `18d73dd`, `0da194e`, `acfa913`, `ae252a9`, `b757812`, `2d19ae7`.
- **In-progress**: Preparação e especificação do Sub-marco M3.2 (Definição e Validação de Cenários de Features — `FeatureScenario`, `validate_scenarios`, `scenarios.json`).
- **Next step**: Elaborar a especificação do Sub-marco M3.2 sob `.specs/features/m3-2-feature-scenarios/spec.md`.
- **Blockers**: none
- **Branch**: main
