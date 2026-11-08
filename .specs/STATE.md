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

- **Feature**: m2-5-cli-end-to-end (Sub-marco M2.5 — Interface em Linha de Comando e Homologação Fim a Fim)
- **Phase / Task**: Concluído e Aceito (Branch `feat/m2-5-cli-end-to-end`) — **Marco M2 (Stage 1 Data Pipeline) Finalizado**
- **Completed**:
  - Sub-marco M2.5 (`m2-5-cli-end-to-end`) implementado, testado e verificado:
    - Despachante hierárquico `build_parser` e tratador uniforme `main` em `src/experimental_ml/cli/main.py`: captura `ExperimentalMLError` e `ValueError` emitindo mensagens instrutivas sem traceback no stderr e retornando código 2 (CLI-06); saída sem argumentos ou com `--help` e `--version` retornando código 0 preservando compatibilidade com M1.1 (CLI-09).
    - Subcomandos de dados `expml data profile` e `expml data sanitize` em `src/experimental_ml/cli/cmd_data.py`: perfilamento com saída descritiva de dimensões e achados sem expor hashes (CLI-01, CLI-11); saneamento com bloqueio rigoroso de planos `INCOMPLETE` exibindo pendências e retornando código 2 sem persistir o plano (CLI-03); persistência de `dataset_descriptor.json`, `dataset_profile.json`, `preparation_plan.json` e `sanitized_view.json` com proteção contra sobrescrita via `--force` (CLI-02, CLI-08).
    - Subcomandos de partição `expml partition build` e `expml partition verify` em `src/experimental_ml/cli/cmd_partition.py`: validação de portão a montante via `verify_preparation_gate` (CLI-07); suporte a `--seed` para sobrescrever `master_seed`; reconstrução determinística de visão saneada e geração de `partition_plan.json`, `splits.csv.gz` (com `mtime=0.0`) e `splits.schema.json` (CLI-04); verificação matemática de invariantes e detecção de adulterações via `verify_partition_gate` e `validate_partition_plan` retornando código 2 sob inconsistências (CLI-05).
    - Pureza arquitetural estrita (`CLI-10`): zero importações diretas ou indiretas de `numpy` ou `hashlib` em todos os módulos sob `src/experimental_ml/cli/`, verificado por AST.
    - Higiene de saída (`CLI-11`): zero digests hexadecimais SHA-256 de 64 caracteres impressos em stdout ou stderr.
    - Suíte de integração e homologação fim a fim (`CLI-12`): execução completa da sequência através do executável `expml` em dois diretórios isolados, comprovando bit a bit a equivalência dos bytes de `partition_plan.json` e do conteúdo descompactado de `splits.csv.gz`.
  - 10 critérios de aceitação (`CLI-01` a `CLI-12`) verificados por 10 checks determinísticos (`check_proofs.py`: 10 pass, 0 fail).
  - Suíte completa do repositório: 176 testes aprovados (100% de aprovação, 0 regressões).
  - Verificação independente por subagente (`author != verifier`) aprovada com veredito `PASS` (0 findings).
  - Validadores documentais TLC: `validate_spec.py`, `validate_tasks.py`, `validate_verification.py` todos com 0 erros e 0 alertas.
  - Artefatos de homologação e resultados (`ACCEPTANCE.md` e `RESULTS.md`) gerados e validados.
  - **Macro-Marco M2 (Stage 1 Data Pipeline)** integralmente entregue em seus 5 sub-marcos (M2.1 a M2.5).
- **In-progress**: Marco M2 concluído; pronto para aprovação do usuário e avanço para o Marco M3 (Stage 2 Feature Engineering).
- **Next step**: Integração das branches do Marco M2 na branch principal ou avanço para Marco M3 conforme direcionamento do usuário.
- **Blockers**: none
- **Branch**: feat/m2-5-cli-end-to-end
