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

- **Feature**: m2-hardening-and-m3-readiness (Hardening Pós-Auditoria do Marco M2 e Transição para o Marco M3)
- **Phase / Task**: Concluído e Aceito — **Marco M2 (Stage 1 Data Pipeline) 100% Hardened, Homologado e Sincronizado**
- **Completed**:
  - Resolução formal dos 11 achados da auditoria de integridade do Marco M2:
    - `REV-M2-01`: Compatibilização de códigos entre profiling e preparation (`E1_FEATURE_CONSTANT`, `E1_SCALE_DISPARITY`, `W1_SCALE_DISPARITY`) e marcação irresolvível de `E1_TARGET_CONSTANT`.
    - `REV-M2-02`: Prevenção de folds vazios em `stratified_kfold_split`, `holdout_split`, `bootstrap_split`, `PartitionConfig` e asserção de invariante formal em `validate_partition_plan`.
    - `REV-M2-03`: Rejeição estrita de NaNs/missing values em partições temporais (`temporal_split` e `validate_partition_plan`).
    - `REV-M2-04`: Preservação de tipos primitivos (`int`, `bool`, `float`, `str`) em chaves de `target_label_mapping` via serialização JSON estruturada.
    - `REV-M2-05`: Verificação estrita de correspondência de `source_plan_digest` no `verify_partition_gate`.
    - `REV-M2-06`: Validação completa da matriz de splits para os 3 papéis (`TRAIN`, `VAL`, `EXCLUDED`).
    - `REV-M2-07`: Pureza de runtime da CLI via PEP 562 (`numpy` e `hashlib` ausentes de `sys.modules`).
    - `REV-M2-08`: Disponibilização das APIs públicas `slice_view_by_observation_ids` (`data/query.py`) e `reconstruct_sanitized_view` (`stages/stage_gates.py`).
    - `REV-M2-09`, `REV-M2-10`, `REV-M2-11`: Emissão de `E1_TARGET_ZERO_VARIANCE`, documentação metodológica de empates temporais e acesso defensivo a `Finding.context`.
  - Implementação de 17 testes de regressão dedicados em `tests/unit/test_m2_hardening_regression.py`.
  - Suíte completa do repositório: 193 testes automatizados aprovados (100% de sucesso, 0 regressões).
  - Parecer formal do *Independent Hardening Verifier* aprovado com veredito `PASS` (100% de conformidade).
  - Commit registrado na branch `main`: `de7e8d6`.
  - Documentação do repositório (`README.md`, `ETAPA_ATUAL_ENGENHARIA.md`, `ARQUITETURA_E_CONTRATOS.md`, `.specs/STATE.md`) integralmente sincronizada.
- **In-progress**: Preparação e especificação da etapa M3 (Stage 2 Feature Engineering).
- **Next step**: Iniciar especificação e design do Marco M3 (`.specs/features/m3-features/` e módulo `src/experimental_ml/features/`).
- **Blockers**: none
- **Branch**: main
