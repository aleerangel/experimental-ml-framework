# Resultados da Homologação — M1.5 Saneamento da Fundação M1 (`m1-5-foundation-hardening`)

## 1. Identificação da Entrega

- **Marco**: M1.5 — Saneamento e Hardening da Fundação M1 (transversal a M1.1, M1.2, M1.3 e M1.4)
- **Branch de Trabalho**: `fix/m1-5-foundation-hardening`
- **Data de Conclusão**: 2026-11-05
- **Objetivo**: Conduzir o saneamento dos 6 achados `ALTO` (P0) e 4 achados `MODERADO` (P1) apontados na Auditoria Geral de Integridade (`m1-integrity-review`), restabelecendo a prontidão da base técnica para a abertura do Marco M2.

---

## 2. Rastreabilidade e Resolução dos 16 Achados da Auditoria

Todos os 16 achados registrados em `.specs/features/m1-integrity-review/reports/06-achados.md` e priorizados em `07-plano-correcoes.md` foram integralmente auditados, tratados ou encaminhados:

| ID | Prioridade Original | Severidade | Descrição Sintética | Estado Final M1.5 | Evidência / Teste Automatizado |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`AUD-F-001`** | **P0.6** | `ALTO` | Blocos Python de exemplo no `README.md` com APIs desatualizadas | `RESOLVIDO` | `test_hard_12_readme_python_blocks_execute_cleanly` (subprocesso Python com exit code 0) |
| **`AUD-F-002`** | **P1.3** | `MODERADO` | Inconsistência na árvore de arquivos do `README.md` e contagens em `ETAPA_ATUAL_ENGENHARIA.md` | `RESOLVIDO` | `test_hard_13_documentation_and_symbol_counts_aligned` (`core.__all__`=28, `data.__all__`=13) |
| **`AUD-F-003`** | P1.2 | `MODERADO` | Otimização de `__slots__`, normalização e controle em `DomainIdentifier` | `ADIADO` | Mantido em escopo separado sem misturar refatoração de identificadores com saneamento P0 |
| **`AUD-F-004`** | **P0.1** | `ALTO` | Risco de colisão por concatenação de nomes de colunas e escalares em `dataset_hash` | `RESOLVIDO` | `test_hard_01_dataset_hash_column_boundary_framing_and_determinism`, `test_hard_02_dataset_hash_object_scalar_type_tags_and_missing` |
| **`AUD-F-005`** | **P0.5** | `ALTO` | `DatasetBundle.dataset_hash` insensível a `observation_ids` | `RESOLVIDO` | `test_hard_03_dataset_hash_observation_ids_and_architecture_direction`, `test_hard_04_bundle_dataset_hash_delegates_observation_ids` |
| **`AUD-F-006`** | **P0.3** | `ALTO` | `slice_bundle_by_observation_ids` não preservava instâncias tipadas `ObservationId` | `RESOLVIDO` | `test_hard_07_slice_bundle_preserves_observation_id_instances`, `test_hard_08_slice_bundle_rejects_invalid_observation_id_inputs` |
| **`AUD-F-007`** | **P1.1** | `MODERADO` | Inteiros fora da faixa de `int64` levantavam `OverflowError` em vez de `DataIntegrityError` | `RESOLVIDO` | `test_hard_11_int64_overflow_raises_data_integrity_error` |
| **`AUD-F-008`** | **P0.2** | `ALTO` | Detecção incompleta de `NaN` em tipos `numpy.floating` (`float16`, `float32`) | `RESOLVIDO` | `test_hard_05_is_nan_and_missing_scalar_centralized`, `test_hard_06_numpy_floating_nan_counted_across_data_layer` |
| **`AUD-F-009`** | **P0.4** | `ALTO` | Mutabilidade permissiva em colunas `object` por falta de *whitelist* estrita | `RESOLVIDO` | `test_hard_09_object_column_missingness_and_semantic_preservation`, `test_hard_10_object_column_rejects_non_whitelisted_types` |
| **`AUD-F-010`** | **P1.3** | `MODERADO` | Documentação arquitetural divergente sobre sensibilidade de ordenação em `dataset_hash` | `RESOLVIDO` | Alinhamento textual em `ARQUITETURA_E_CONTRATOS.md` e `README.md` |
| **`AUD-F-011`** | P1.4 | `MODERADO` | Ambiguidade de semântica de `pos_label` para classificação binária textual | `ADIADO` | Encaminhado para formalização na fase Specify do Marco M2 (`profile_dataset` / `PreparationPlan`) |
| **`AUD-F-012`** | P1.5 | `MODERADO` | Ausência de `verification.md` no Marco histórico M1.1 | `ADIADO` | Investigação comprova ciclo concluído em `2026-10-31` antes da adoção de `verification.md`; vedada fabricação retroativa; corrigido no `README.md` |
| **`AUD-F-013`** | **P1.6** | `MODERADO` | Ausência de suíte de testes de integração transversal entre `core`, `data` e `metrics` | `RESOLVIDO` | Criação de `tests/integration/test_m1_foundation_integration.py` (`test_hard_14_end_to_end_core_data_metrics_and_cross_process_hash`) |
| **`AUD-F-014`** | P2.2 | `BAIXO` | Validador do TLC sensível ao avanço do histórico git | `ADIADO` | Mantido encaminhamento de baixa prioridade em tooling interno |
| **`AUD-F-015`** | P2.1 | `BAIXO` | Micro-higiene em `_ALLOWED_AGG_SCOPES` e assertiva interna | `ADIADO` | Mantido encaminhamento de baixa prioridade |
| **`AUD-F-016`** | P2.3 | `BAIXO` | Ausência de binários Python 3.10 e 3.11 no host local | `ADIADO` | Mantido como limitação documentada de ambiente de desenvolvimento |

**Balanço Final**: 10 achados `RESOLVIDO`, 6 achados `ADIADO` (com encaminhamentos objetivos e justificados).

---

## 3. Investigação Histórica de AUD-F-012

A verificação do repositório confirma que o commit `d77cc48` (`2026-10-31`) encerrou a entrega do Marco M1.1 utilizando `proofs.md` como artefato formal de verificação mecânica, antes da introdução da exigência de `verification.md` por subagente independente (formalizada a partir do Marco M1.2). 

Em conformidade estrita com a integridade documental e com a vedação de fabricação retroativa de evidências:
- **Nenhum arquivo `verification.md` foi forjado ou criado retroativamente** em `.specs/features/m1-1-setup-cli-smoke/`.
- A menção errônea no `README.md` que listava `verification.md` em M1.1 foi corrigida via `AUD-F-002`.

---

## 4. Preservação dos Artefatos Originais de Auditoria

A pasta de artefatos da Auditoria Geral de Integridade (`.specs/features/m1-integrity-review/`) permaneceu rigorosamente **inalterada**:
- `git diff origin/audit/m1-integrity-review -- .specs/features/m1-integrity-review/` reporta exatamente **0 bytes** de alteração.
- O diagnóstico original, os relatórios de achados (01 a 08) e as sondagens automatizadas foram preservados intactos como registro histórico imutável.

---

## 5. Parecer de Prontidão Técnica para o Marco M2

Com a resolução dos 6 achados de severidade `ALTO` (P0) e dos 4 achados de severidade `MODERADO` (P1) selecionados, comprovada por 96 testes automatizados aprovados (80 unitários, 12 de fumaça e 4 de integração transversal):

> **PARECER FINAL: APTO PARA INÍCIO DO MARCO M2**
>
> A fundação transversal do framework experimental (`core`, `metrics` e `data`) encontra-se saneada, criptograficamente delimitada, imutável em nível de buffers, matematicamente consistente no tratamento de ausentes e integralmente integrada.
