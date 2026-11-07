# M2.4 — Artifacts Persistence & Stage Gates (m2-4-artifacts-stage-gates) Specification

**Approved**: 2026-11-07 - user: "aprovada"

## Problem Statement

As Etapas 1 (Engenharia de Dados e Diagnóstico) e 4A (Particionamento e Validação) geram artefatos intermediários cruciais para a reprodutibilidade científica do framework: perfis estatísticos de dados (`DatasetProfile`), planos de saneamento (`PreparationPlan`), descritores da visão saneada (`SanitizedViewDescriptor`), planos de partição (`PartitionPlan`) e matrizes tabulares de divisão (`splits.csv.gz`).

A ausência de uma camada dedicada de persistência atômica e portões de validação entre etapas acarreta riscos severos de integridade:
1. **Corrupção por Falha Parcial**: Operações de escrita interrompidas (por exceções de I/O, falta de espaço ou encerramento forçado do processo) podem deixar arquivos JSON incompletos ou corrompidos em disco, violando a integridade do estado do experimento.
2. **Inconsistência de Serialização (Codecs Incompletos)**: A conversão ingênua de objetos complexos (contendo tuplas, `MappingProxyType`, enums, e tipos escalares do NumPy) pode introduzir perda de precisão, tipos mutáveis indesejados, ou valores não compatíveis com o padrão JSON (`NaN`, `Infinity`).
3. **Execução sobre Entradas Dessincronizadas**: Sem a validação estrita de vínculos criptográficos (`dataset_hash`, `plan_id`) entre os artefatos gerados nas etapas subsequentes, o particionamento ou os modelos poderiam operar silenciosamente sobre dados adulterados, defasados ou provenientes de planos de saneamento incompletos (`INCOMPLETE`).
4. **Ausência de Mapeamento Tabular Explícito**: Falta de uma representação universalmente legível e comprimida das divisões de treino, validação e teste para cada fold e para o holdout.

O Sub-marco M2.4 resolve estes problemas implementando a persistência atômica, codecs lossless bidirecionais e o validador de vínculos de integridade entre etapas (*stage gates*).

## Out of Scope

Explicitamente excluído para manter isolamento e controle de escopo:

| Feature | Reason |
| --- | --- |
| Subcomandos de linha de comando `expml data ...` e `expml partition ...` | Pertence ao Sub-marco M2.5 (CLI e Aceite Fim a Fim) |
| Formato de armazenamento colunar Apache Parquet | Decisão D6: uso exclusivo da biblioteca padrão (`gzip`, `csv`, `json`) sem dependências externas |
| Persistência de pesos e artefatos de modelos treinados | Pertence à Etapa 4B no módulo `orchestration` (Marco M5) |
| Rotação automática de logs ou armazenamento em nuvem | RNF03: operação 100% local, offline e em processo único |

---

## Assumptions & Open Questions

As premissas baseiam-se nos requisitos `STORE-01` a `STORE-07`, nas decisões D6, D10 e D11 do Marco M2 e nas diretrizes arquiteturais de governança:

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| D6: Armazenamento de Splits | `partitions/splits.csv.gz` mais `partitions/splits.schema.json`, com compressão gzip determinística via `gzip` e `csv` da stdlib | Preserva `numpy` como única dependência do framework e garante portabilidade multiplataforma | y |
| D10: Política de Sobrescrita | Toda escrita recusa sobrescrever arquivos existentes disparando `ConfigurationError`, exceto quando explicitamente solicitado com `overwrite=True` | Preserva a imutabilidade e auditabilidade dos experimentos científicos | y |
| D11: Descritor da Visão Saneada | Metadados leves gravados em `data/sanitized_view.json` (`dataset_hash`, contagens, regras deferidas, dropped IDs, hash do plano) sem duplicar os dados crus | Permite verificar o vínculo de integridade sem gerar arquivos redundantes de grande volume | y |
| STORE-01: Escrita Atômica | Escrita de JSON via arquivo temporário no mesmo diretório com substituição atômica (`os.replace`) e limpeza em caso de erro | Elimina qualquer possibilidade de arquivos parcialmente gravados em disco | y |
| STORE-02: Codecs Lossless | Conversão bidirecional sem perda `to_dict` / `from_dict` para todos os artefatos de etapa, garantindo JSON válido sem `NaN`/`Infinity` | Conformidade com padrão RFC 8259 e determinismo de bytes | y |
| STORE-05: Portão de Integridade | Bloqueio rigoroso via `DataIntegrityError` se hashes divergirem e via `ContractViolationError` se `preparation_plan` não estiver `READY` | Garante que nenhuma etapa avance com dados inconsistentes (CA-GER-01) | y |

**Open questions:** none - as decisões e requisitos de persistência foram formalmente aprovados no Marco M2.

---

## User Stories

### P1: M2.4 — Persistência Atômica de Artefatos e Bloqueio entre Etapas ⭐ MVP

**User Story**: Como pesquisador, quero que todos os artefatos gerados nas etapas de dados e validação sejam persistidos de forma atômica, determinística e auditável, com bloqueio rigoroso entre etapas caso ocorra qualquer divergência ou violação de integridade.

**Why P1**: Atende aos requisitos `STORE-01` a `STORE-07` e ao critério de governança `CA-GER-01`. É a base fundamental que viabiliza a execução segura da CLI no Sub-marco M2.5.

**Acceptance Criteria**:

1. WHEN `write_json_atomic(path, obj, overwrite=False)` is executed THEN the system SHALL serialize the payload to a temporary file in the target directory and rename it atomically via `os.replace`, and IF the write or serialization fails THEN the system SHALL clean up the temporary file and leave the target path absent or untouched (STORE-01).
2. The system SHALL provide lossless `to_dict` and `from_dict` codecs for `DatasetProfile`, `PreparationPlan`, `PartitionPlan`, and stage descriptors (`DatasetDescriptor`, `SanitizedViewDescriptor`) such that round-trip execution returns an identical object, produces deterministic JSON bytes, and contains no `NaN` or `Infinity` (STORE-02).
3. The system SHALL format and validate the standard experiment directory layout containing `data/dataset_descriptor.json`, `data/dataset_profile.json`, `configuration/preparation_plan.json`, `data/sanitized_view.json`, `partitions/partition_plan.json`, `partitions/splits.csv.gz`, and `partitions/splits.schema.json` (STORE-03).
4. WHEN `write_splits_csv_gz(path, plan, overwrite=False)` is executed THEN the system SHALL write a gzip-compressed CSV mapping every `observation_id` to its per-fold role (`TRAIN`, `VAL`) and holdout status (`HOLDOUT`, `DEVELOPMENT`), with deterministic byte content across repeated writes of the identical plan (STORE-04).
5. IF the dataset hash of the plan, descriptor, or profile diverges, or the reconstructed view hash diverges from `partition_plan.json` or `sanitized_view.json`, THEN the system SHALL raise `DataIntegrityError`, and IF `preparation_plan.json` is absent or not `READY` THEN the system SHALL raise `ContractViolationError` before allowing downstream artifact generation (STORE-05).
6. IF `splits.csv.gz` and `partition_plan.json` describe contradictory fold assignments, or an artifact was modified after generation THEN the system SHALL detect the divergence and raise `DataIntegrityError` (STORE-06).
7. IF any output artifact already exists at the destination path and `overwrite=False` THEN the system SHALL refuse to overwrite it and raise `ConfigurationError` (STORE-07).

---

## Requirement Traceability

| Requirement ID | Description | Source / Rationale | Status |
| :--- | :--- | :--- | :--- |
| STORE-01 | Escrita atômica de JSON com arquivo temporário e substituição segura | CA-GER-01, RNF03 | proposed |
| STORE-02 | Codecs bidirecionais sem perda `to_dict` / `from_dict` para artefatos de etapa | RFC 8259, ADR-008 | proposed |
| STORE-03 | Layout padronizado de artefatos no diretório do experimento | ARQUITETURA §5, D11 | proposed |
| STORE-04 | Serialização comprimida determinística de `splits.csv.gz` e `splits.schema.json` | D6, ADR-006 | proposed |
| STORE-05 | Verificação de vínculos de hash e bloqueio por plano incompleto | CA-GER-01, CA-E1-02 | proposed |
| STORE-06 | Verificação de consistência entre `splits.csv.gz` e `partition_plan.json` | CA-E4A-01, RNF05 | proposed |
| STORE-07 | Política de não-sobrescrita por padrão disparando `ConfigurationError` | D10, CA-GER-01 | proposed |
