# Resultados da Auditoria Geral de Integridade do Projeto (`RESULTS.md`)

**Feature / Atividade:** `m1-integrity-review` — Auditoria Geral de Integridade do Projeto (M1 — Project Integrity Review)  
**Data:** 05 de Novembro de 2026  
**Branch:** `audit/m1-integrity-review` (baseada em `main` @ `6acf6f8e5d478cbc08bb29ef22ac1da267b56feb`)  
**Status:** Concluída (Auditoria Somente-Leitura com Verificação Independente)

---

## 1. Resumo Executivo

Foi conduzida a **Auditoria Geral de Integridade do Projeto (M1)** abrangendo as entregas concluídas `M1.1` (`setup-cli-smoke`), `M1.2` (`core`), `M1.3` (`metrics`) e `M1.4` (`datasets-schemas`), avaliando 48 critérios objetivos distribuídos nas 6 dimensões obrigatórias (`ARCH`, `INT`, `QUAL`, `TEST`, `DOC`, `READY`) e no protocolo de não interferência (`AUD`).

* **Não interferência comprovada (`AUD-02`):** `0` bytes modificados em `src/`, `tests/`, `pyproject.toml`, `README.md`, `engenharia_software/`, `.agent/` e `.specs/features/m1-{1,2,3,4}-*/`.
* **Suíte de testes existente:** `81 passed in 0.25s` (100% de aprovação em ordem direta, reversa e isolada).
* **Ensaio de mutação controlada (`TEST-03`):** `12/12` mutantes eliminados (`100.0%` de detecção sobre invariantes cobertos).
* **Achados identificados (`06-achados.md`):** `16` achados totais (`0 CRÍTICO`, `6 ALTO` [4 `DEFEITO`, 2 `RISCO`], `7 MODERADO`, `3 BAIXO`).
* **Parecer Final de Prontidão para o Marco M2 (`08-parecer.md`):** **`NÃO APTO`** no commit `6acf6f8` até a aplicação do lote corretivo cirúrgico da **Faixa P0** (6 itens localizados detalhados em `07-plano-correcoes.md`).

---

## 2. Entregáveis Produzidos

| # | Entregável | Caminho | Status |
| :---: | :--- | :--- | :---: |
| 0 | Linha de Base e Protocolo de Não Interferência | [00-baseline.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/00-baseline.md) | Concluído |
| 1 | Especificação e Critérios da Auditoria | [01-especificacao-criterios.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/01-especificacao-criterios.md) | Concluído |
| 2 | Relatório de Integridade Arquitetural (Dimensão A) | [02-arquitetura.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/02-arquitetura.md) | Concluído |
| 3 | Relatório de Integração entre Módulos (Dimensão B) | [03-integracao.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/03-integracao.md) | Concluído |
| 4 | Relatório de Qualidade e Estratégia de Testes (Dimensões C e D) | [04-qualidade-e-testes.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/04-qualidade-e-testes.md) | Concluído |
| 5 | Matriz de Conformidade e Rastreabilidade (Dimensão E) | [05-rastreabilidade.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/05-rastreabilidade.md) | Concluído |
| 6 | Registro Consolidado de Achados e Riscos | [06-achados.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/06-achados.md) | Concluído |
| 7 | Plano de Correções Priorizadas | [07-plano-correcoes.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/07-plano-correcoes.md) | Concluído |
| 8 | Parecer Final de Prontidão para o M2 (Dimensão F) | [08-parecer.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/08-parecer.md) | Concluído |

---

## 3. Síntese dos Achados Prioritários (Faixa P0 — Bloqueantes para o M2)

1. **`AUD-F-001` (`DEFEITO` / `ALTO`):** Blocos 3 e 4 de exemplo Python no `README.md` levantam `ConfigurationError` (`is_better(..., cand_b=None)`) e `TypeError` (`DatasetSchemaSpec(..., semantic_types=...)` em vez de `column_semantic_types=`).
2. **`AUD-F-004` (`DEFEITO` / `ALTO`):** `_hash_in_memory_tabular` em `core/hashing.py` concatena nomes de colunas sem prefixo de tamanho nem delimitador, causando colisão de `dataset_hash` entre `{"ab": [1.0], "c": [2.0]}` e `{"a": [1.0], "bc": [2.0]}`.
3. **`AUD-F-005` (`RISCO` / `ALTO`):** `bundle.dataset_hash` não incorpora `bundle.observation_ids`, gerando o mesmo hash para recortes com `observation_ids` distintos quando `observation_id_col=None`.
4. **`AUD-F-006` (`DEFEITO` / `ALTO`):** `slice_bundle_by_observation_ids` armazena `str` comuns em `DatasetBundle.observation_ids` quando o chamador passa `Sequence[str]`, violando a garantia de tipo `tuple[ObservationId, ...]`.
5. **`AUD-F-008` (`DEFEITO` / `ALTO`):** `np.float32(np.nan)` não é reconhecido por `isinstance(v, float) and math.isnan(v)`, resultando em `ColumnDescriptor.n_missing == 0` para arrays `float32` contendo `NaN`.
6. **`AUD-F-009` (`RISCO` / `ALTO`):** Colunas `dtype=object` em `load_dataset` validam mutabilidade por uma *blacklist* estreita (`list, dict, set, bytearray`), permitindo que objetos mutáveis como `SimpleNamespace` entrem no `DatasetBundle` e sejam alterados in-place.
