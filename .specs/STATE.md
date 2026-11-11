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

### AD-005
- **Decision**: Saneamento das estratégias supervisionadas de features na Onda 1 e formalização desacoplada do contrato funcional de modelos heterogêneos (`ModelSpec`, `ModelCapabilities`).
- **Reason**: Eliminar aliases não documentados (`MUTUAL_INFO_TOP_K`, `ACH-M3-01`) restringindo a seleção supervisionada da Onda 1 à estratégia formal `TOP_K_RELEVANCE` e `VARIANCE_THRESHOLD`, e padronizar o ciclo de modelos em funções puras (`instantiate_fresh_model`, `fit_model`, `predict_model`, `extract_model_diagnostics`) com suporte a modelos analíticos sem treino (`requires_fit=False`) e retorno padronizado tripartite (`y_pred`, `y_std`, `y_proba`).
- **Trade-off**: Redução de dimensionalidade via PCA e estimadores contínuos avançados de informação mútua são formalmente alocados para a Onda 2.
- **Scope**: Módulos `features` e `models`.
- **Date**: 2026-11-10
- **Status**: active

## Handoff

- **Feature**: m4-1-model-registry-contracts (Sub-marco M4.1 — Registro de Modelos, Capacidades e Contratos Funcionais)
- **Phase / Task**: Conclusão formal do Sub-marco M4.1 (Etapa 3 / Marco M4)
- **Completed**:
  - Conclusão e homologação formal de 100% dos Marcos M1 (`m1-1` a `m1-5`), M2 (`m2-1` a `m2-5`) e M3 (`m3-1` a `m3-4`).
  - Especificação, Design e Execução do Sub-marco M4.1 (`m4-1-model-registry-contracts`) com 8 tarefas granulares concluídas e 35 critérios de aceitação formalmente comprovados (`check_proofs.py`: 35 pass, 0 fail).
  - Implementação de `src/experimental_ml/models/` com `types.py` (`ModelFamily`, `ModelCapabilities`, `ModelDiagnostics`), `spec.py` (`ModelSpec`, `validate_model_spec`, `validate_models_catalog`), `execution.py` (`instantiate_fresh_model`, `fit_model`, `predict_model`), `diagnostics.py` (`extract_model_diagnostics`), `baselines.py` (`DummyBaselineModel`, `AnalyticalBiometricModel`) e `__init__.py`.
  - Isolamento estrito de memória (`CA-E3-01`) via rastreamento de instâncias e rejeição de singletons (`ContractViolationError`).
  - Contrato de predição tripartite verificado (`y_pred` 1D com $len = N$, `y_std` finito e $\ge 0$, `y_proba` 2D no simplex unitário).
  - Suporte nativo a modelos analíticos/biométricos sem treino (`requires_fit=False`, `RF3.2`) com bypass no-op.
  - Snapshot de diagnósticos imutável e independente com cópia defensiva profunda (`RF3.6`).
  - Pureza estrita de runtime (`XCUT-02`): dependência única de `numpy>=1.24.0`, zero dependências mandatórias de ML frameworks externos.
  - Verificação independente realizada com veredito `PASS` (0 findings) e portão `validate_verification.py` aprovado com 0 erros.
  - Artefatos de homologação gerados: `ACCEPTANCE.md` e `RESULTS.md`.
  - Suíte total do framework expandida de 236 para 272 testes automatizados (36 novos testes em `tests/unit/models/` e `tests/integration/models/`), 100% aprovados.
- **In-progress**: Transição para o Sub-marco M4.2 (`m4-2-two-layer-preprocessing` — Pipeline de Pré-processamento em 2 Camadas).
- **Next step**: Homologação / merge da branch `feat/m4-1-model-registry-contracts` e inicialização da especificação de M4.2.
- **Blockers**: none
- **Branch**: feat/m4-1-model-registry-contracts
