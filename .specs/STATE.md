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

- **Feature**: m2-3-partitioning-engine (Sub-marco M2.3 — Motor de Particionamento Compartilhado e Validado)
- **Phase / Task**: Concluído e Aceito (Branch `feat/m2-3-partitioning-engine`)
- **Completed**:
  - Sub-marco M2.3 (`m2-3-partitioning-engine`) implementado, testado e verificado:
    - `PartitionStrategy` (StrEnum: KFOLD, STRATIFIED_KFOLD, GROUP_KFOLD, BOOTSTRAP, TEMPORAL, HOLDOUT) e `EvaluationRegime` (StrEnum: CV_ONLY, HOLDOUT_ONLY, CV_AND_HOLDOUT).
    - `FoldPartition`, `PartitionConfig`, `PartitionPlan`: modelos de dados imutáveis com `frozen=True, slots=True`. `PartitionConfig` valida limites estritos em `__post_init__` (`n_splits >= 2`, `0 < holdout_fraction < 1.0`, colunas obrigatórias presentes).
    - Splitters funcionais puros: `kfold_split`, `stratified_kfold_split`, `group_kfold_split`, `bootstrap_split`, `temporal_split` e `holdout_split`.
    - `validate_partition_plan`: validador formal de integridade matemática que verifica disjunção estrita ($\text{Train}_k \cap \text{Val}_k = \emptyset$), isolamento de holdout ($\text{Train}_k/\text{Val}_k \cap \text{Holdout} = \emptyset$), disjunção estrita de grupos ($\text{Groups}(Train_k) \cap \text{Groups}(Val_k) = \emptyset$) e monotonicidade temporal estrita ($\max(\text{Time}(Train_k)) \le \min(\text{Time}(Val_k))$), disparando `DataIntegrityError` se violado.
    - `build_partition_plan`: motor de construção de `PartitionPlan` que orquestra a extração via contratos de `SanitizedDatasetView` ou `DatasetBundle`, separação de holdout (D7), partição de validação cruzada sobre `development_ids`, geração de `plan_id` canônico SHA-256 (D8) e auto-validação antes do retorno.
    - 7 símbolos públicos exportados em `experimental_ml.validation.__all__`.
  - 10 critérios de aceitação (`PART-01` a `PART-10`) verificados por 10 checks determinísticos (`check_proofs.py`: 10 pass, 0 fail).
  - Suíte completa do repositório: 151 testes aprovados (100% de aprovação, 0 regressões).
  - Verificação independente por subagente (`author != verifier`) aprovada com veredito `PASS` (0 findings).
  - Validadores documentais TLC: `validate_spec.py`, `validate_tasks.py`, `validate_verification.py` todos com 0 erros e 0 alertas.
  - Artefatos de homologação e resultados (`ACCEPTANCE.md` e `RESULTS.md`) gerados e validados.
- **In-progress**: Sub-marco M2.3 concluído; pronto para avançar para o Sub-marco M2.4 (`m2-4-data-cli`)
- **Next step**: Iniciar Specify / Design do Sub-marco M2.4 (CLI modular de dados `data inspect`, `data profile`, `data prepare`, `data partition`)
- **Blockers**: none
- **Branch**: feat/m2-3-partitioning-engine
