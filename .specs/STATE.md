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

- **Feature**: m2-4-artifacts-stage-gates (Sub-marco M2.4 — Persistência de Artefatos e Bloqueio entre Etapas)
- **Phase / Task**: Concluído e Aceito (Branch `feat/m2-4-artifacts-stage-gates`)
- **Completed**:
  - Sub-marco M2.4 (`m2-4-artifacts-stage-gates`) implementado, testado e verificado:
    - `write_json_atomic` e `read_json` em `src/experimental_ml/core/storage.py`: escrita atômica via arquivo temporário e `os.replace`, remoção limpa do temporário em falha (STORE-01) e proteção rigorosa contra sobrescrita com `ConfigurationError` quando `overwrite=False` (STORE-07).
    - Descritores leves `DatasetDescriptor` e `SanitizedViewDescriptor` em `src/experimental_ml/data/descriptors.py` com frozen slots e proteção imutável (STORE-02, D11).
    - Codecs bidirecionais sem perda `to_dict` / `from_dict` em `src/experimental_ml/data/codecs.py` e `src/experimental_ml/validation/codecs.py` para `DatasetDescriptor`, `SanitizedViewDescriptor`, `DatasetProfile`, `PreparationPlan` e `PartitionPlan`, sanitizando floats (`allow_nan=False`, sem `NaN` ou `Infinity` conforme RFC 8259) (STORE-02).
    - Mapeamento tabular de divisões `write_splits_csv_gz`, `read_splits_csv_gz` e `write_splits_schema` em `src/experimental_ml/validation/storage.py` com `gzip.GzipFile(mtime=0.0)` para garantir determinismo binário bit a bit entre execuções repetidas (STORE-04, D6).
    - Portões de validação entre etapas `verify_preparation_gate` e `verify_partition_gate` em `src/experimental_ml/stages/stage_gates.py`: validação de layout canônico de diretório, bloqueio de planos `INCOMPLETE` com `ContractViolationError` (STORE-05), detecção de divergência de hashes de dataset com `DataIntegrityError` (STORE-05) e detecção de contradições/adulterações entre `splits.csv.gz` e `partition_plan.json` com `DataIntegrityError` (STORE-06).
    - Módulo `experimental_ml.stages` com exportações públicas e constantes de layout canônico.
  - 7 critérios de aceitação (`STORE-01` a `STORE-07`) verificados por 7 checks determinísticos (`check_proofs.py`: 7 pass, 0 fail).
  - Suíte completa do repositório: 162 testes aprovados (100% de aprovação, 0 regressões).
  - Verificação independente por subagente (`author != verifier`) aprovada com veredito `PASS` (0 findings).
  - Validadores documentais TLC: `validate_spec.py`, `validate_tasks.py`, `validate_verification.py` todos com 0 erros e 0 alertas.
  - Artefatos de homologação e resultados (`ACCEPTANCE.md` e `RESULTS.md`) gerados e validados.
- **In-progress**: Sub-marco M2.4 concluído; pronto para avançar para o Sub-marco M2.5 (`m2-5-cli-end-to-end`)
- **Next step**: Iniciar Specify / Design do Sub-marco M2.5 (CLI `data` e `partition`, cenários de aceite fim a fim e códigos de saída)
- **Blockers**: none
- **Branch**: feat/m2-4-artifacts-stage-gates
