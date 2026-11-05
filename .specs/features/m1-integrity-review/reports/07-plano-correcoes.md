# 7. Plano de Correções Priorizadas (`07-plano-correcoes.md`)

**Referência:** Registro Consolidado de Achados ([06-achados.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/06-achados.md))  
**Objetivo:** Estruturar e priorizar o tratamento dos achados identificados na Auditoria Geral de Integridade do Marco M1 antes e durante o avanço para o Marco M2.

---

## 1. Faixa P0 — Correções Obrigatórias Antes de Iniciar o Marco M2 (Bloqueantes)

Estes itens compreendem todos os achados de severidade **`ALTO`** (`4 DEFEITOS` e `2 RISCOS`) e os defeitos correlatos de rápida resolução no mesmo arquivo. Devem ser resolvidos em um ciclo curto de saneamento pré-M2 (`m1-5-foundation-hardening` ou PR corretivo na `main`) antes da abertura da implementação do Marco M2:

| Prioridade | Achado | Severidade / Categoria | Arquivos Alvo | Ação Corretiva Objetiva | Complexidade Estimada |
| :---: | :---: | :---: | :--- | :--- | :---: |
| **P0.1** | `AUD-F-004` | `ALTO` / `DEFEITO` | `src/experimental_ml/core/hashing.py` | Em `_hash_in_memory_tabular`, gravar `struct.pack("<Q", len(col_names))` e, para cada nome de coluna, gravar `struct.pack("<Q", len(col_bytes))` antes de `hasher.update(col_bytes)`, eliminando colisões por concatenação como `{"ab": ..., "c": ...}` vs. `{"a": ..., "bc": ...}`. | Baixa (~10 linhas + teste unitário) |
| **P0.2** | `AUD-F-008` | `ALTO` / `DEFEITO` | `src/experimental_ml/data/loader.py`, `data/query.py`, `data/validation.py`, `core/hashing.py` | Substituir `isinstance(v, float) and math.isnan(v)` por uma função auxiliar única `is_nan_scalar(v)` que verifique `isinstance(v, (float, np.floating)) and math.isnan(float(v))`, garantindo que `np.float32(np.nan)` e `np.float16(np.nan)` sejam contabilizados em `ColumnDescriptor.n_missing` e normalizados no hash. | Baixa (~15 linhas + teste unitário) |
| **P0.3** | `AUD-F-006` | `ALTO` / `DEFEITO` | `src/experimental_ml/data/query.py` | Em `slice_bundle_by_observation_ids`, construir `observation_ids=tuple(bundle.observation_ids[i] for i in indices)` para preservar sempre instâncias de `ObservationId` mesmo quando o chamador passar `Sequence[str]`. | Muito Baixa (1 linha + teste unitário) |
| **P0.4** | `AUD-F-009` | `ALTO` / `RISCO` | `src/experimental_ml/data/loader.py` | Em `_coerce_column_values` (ramo `object`), substituir a *blacklist* `isinstance(v, (list, dict, set, bytearray))` por uma *whitelist* estrita de escalares imutáveis (`str`, `bytes`, `int`, `float`, `bool`, `np.number`, `np.bool_`), levantando `DataIntegrityError` para qualquer outro objeto (como `SimpleNamespace` ou instâncias mutáveis). | Baixa (~8 linhas + teste unitário) |
| **P0.5** | `AUD-F-005` | `ALTO` / `RISCO` | `src/experimental_ml/data/loader.py`, `data/query.py` (e/ou `core/hashing.py`) | Incluir a sequência de `observation_ids` na composição do `bundle.dataset_hash` (ou passar `observation_ids` ao cálculo canônico), garantindo que dois `DatasetBundle` com mesmas colunas mas `observation_ids` distintos tenham `dataset_hash` distintos conforme `ARQUITETURA_E_CONTRATOS.md:210,707`. | Baixa (~15 linhas + teste unitário) |
| **P0.6** | `AUD-F-001` | `ALTO` / `DEFEITO` | `README.md` | Corrigir os blocos 3 (`metrics`: passar segundo `MetricValue` válido ou `UNDEFINED_NAN` em `is_better` em vez de `None`, e ajustar `spec.rtol`) e 4 (`data`: usar `column_semantic_types=` em vez de `semantic_types=`, e `len(bundle.feature_cols)` em vez de `bundle.n_features`). | Baixa (~10 linhas) |

---

## 2. Faixa P1 — Correções Recomendadas no Saneamento Pré-M2 ou na Entrada do Marco M2

Estes itens abrangem os achados de severidade **`MODERADO`** que fortalecem a fundação transversal e eliminam inconsistências documentais e de governança:

| Prioridade | Achado | Severidade / Categoria | Arquivos Alvo | Ação Corretiva Objetiva | Complexidade Estimada |
| :---: | :---: | :---: | :--- | :--- | :---: |
| **P1.1** | `AUD-F-007` | `MODERADO` / `DEFEITO` | `src/experimental_ml/data/loader.py` | Capturar `OverflowError` em `np.array(int_vals, dtype=np.int64)` e levantar `DataIntegrityError("Integer value exceeds int64 bounds")`. | Muito Baixa (4 linhas) |
| **P1.2** | `AUD-F-003` | `MODERADO` / `RISCO` | `src/experimental_ml/core/types.py` | Adicionar `__slots__ = ()` em `DomainIdentifier` e nas 8 subclasses; normalizar strings via `unicodedata.normalize("NFC", ...)` e rejeitar caracteres de controle ASCII (`ord(c) < 32` ou `ord(c) == 127`). | Baixa (~20 linhas) |
| **P1.3** | `AUD-F-002` & `AUD-F-010` | `MODERADO` / `DEFEITO` & `RISCO` | `README.md`, `engenharia_software/ARQUITETURA_E_CONTRATOS.md`, `engenharia_software/ETAPA_ATUAL_ENGENHARIA.md` | Corrigir árvore de diretórios no `README.md` (`core/types.py`), contagem de símbolos em `ETAPA_ATUAL_ENGENHARIA.md` (13 símbolos em `data`) e descrição da sensibilidade de `dataset_hash` à ordem das colunas. | Baixa (~20 linhas) |
| **P1.4** | `AUD-F-011` | `MODERADO` / `RISCO` | Especificação do Marco M2 (`profile_dataset` / `PreparationPlan`) e/ou `metrics/classification.py` | Formalizar no Specify do M2 a regra para alvos binários com rótulos textuais (`dtype=object`): exigir codificação explícita para `{0, 1}` no `PreparationPlan` (`CONFIRMED_ISSUE`) e/ou permitir que `precision`/`recall`/`f1` utilizem a classe positiva canônica ordenada quando `pos_label` não for especificado. | Baixa |
| **P1.5** | `AUD-F-012` | `MODERADO` / `RISCO` | `.specs/features/m1-1-setup-cli-smoke/verification.md` | Gerar o registro `verification.md` ausente de `m1-1-setup-cli-smoke` para eliminar o alerta recorrente em `check_commit.py` e `validate_verification.py`. | Baixa (1 arquivo markdown) |
| **P1.6** | `AUD-F-013` | `MODERADO` / `MELHORIA` | `tests/integration/test_m1_foundation_integration.py` | Incorporar uma suíte de testes de integração validando o fluxo combinado `core` + `data` + `metrics` e a execução dos blocos Python do `README.md`. | Baixa (~80 linhas) |

---

## 3. Faixa P2 — Melhorias de Baixa Prioridade e Limitações Monitoradas

| Prioridade | Achado | Severidade / Categoria | Encaminhamento |
| :---: | :---: | :---: | :--- |
| **P2.1** | `AUD-F-015` | `BAIXO` / `MELHORIA` | Converter `_ALLOWED_AGG_SCOPES` em `frozenset` (`aggregation.py:21`) e substituir `assert source_path_str is not None` (`loader.py:317`) no próximo ciclo de manutenção. |
| **P2.2** | `AUD-F-014` | `BAIXO` / `MELHORIA` | Manter ciência de que `validate_verification.py` verifica a igualdade entre o hash gravado em `proofs.md` e o `HEAD` atual do repositório. |
| **P2.3** | `AUD-F-016` | `BAIXO` / `LIMITAÇÃO DOCUMENTADA` | Manter documentada a ausência dos interpretadores Python 3.10 e 3.11 no host local até a adição de pipeline CI multi-versão. |
