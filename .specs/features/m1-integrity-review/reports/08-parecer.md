# 8. Parecer Final de Prontidão para o Segundo Marco (`08-parecer.md`)

**Dimensão:** F — Prontidão para o Segundo Marco (`READY-01` a `READY-08`)  
**Referências:** [06-achados.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/06-achados.md) | [07-plano-correcoes.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/07-plano-correcoes.md)

---

## 1. Avaliação de Prontidão das Interfaces Consumidas pelo Marco M2 (`READY-01`)

O Marco M2 (`Diagnóstico Estrutural, Sanitização e Particionamento Auditado`) implementará os contratos da Etapa 1 restante (`profile_dataset` $\rightarrow$ `DatasetProfile`, `create_preparation_plan` $\rightarrow$ `PreparationPlan`, `sanitize_dataset` $\rightarrow$ `SanitizedDatasetView`), da Etapa 4A (`build_partition_plan`, `validate_partition_plan` $\rightarrow$ `PartitionPlan`) e os subcomandos da CLI (`expml data`, `expml partition`).

A tabela abaixo avalia cada contrato planejado do M2 frente às estruturas e funções já implementadas no Marco M1:

| Contrato Planejado do Marco M2 | Interfaces do M1 Consumidas | Estado de Prontidão | Lacunas / Bloqueios Identificados na Fundação M1 |
| :--- | :--- | :---: | :--- |
| **`profile_dataset(bundle)` $\rightarrow$ `DatasetProfile`** | `DatasetBundle`, `ColumnDescriptor`, `ColumnSemanticType`, `Finding`, `FindingSeverity` (`CONFIRMED_ISSUE`, `HEURISTIC_WARNING`), `make_finding`, `make_warning` | **Requer Correção Pré-M2 (`AUD-F-008`, `AUD-F-009`)** | 1. `ColumnDescriptor.n_missing` reporta `0` quando a fonte contém `np.float32(np.nan)` (`AUD-F-008`), o que faria `profile_dataset` omitir valores ausentes reais.<br/>2. Colunas `object` permitem instâncias mutáveis não listadas na *blacklist* (`AUD-F-009`).<br/>3. `Finding` em `core/findings.py` não congela o dicionário opcional `context: Mapping[str, Any] \| None` com `MappingProxyType` (deve ser encapsulado ou copiado). |
| **`create_preparation_plan(...)` $\rightarrow$ `PreparationPlan`** | `DatasetBundle.dataset_hash`, `config_hash`, `FindingSeverity.CONFIRMED_ISSUE`, `ConfigurationError` | **Requer Correção Pré-M2 (`AUD-F-004`, `AUD-F-005`)** | `PreparationPlan` vincula-se ao `dataset_hash` de origem; a colisão de concatenação de nomes de colunas em `core.dataset_hash` (`AUD-F-004`) e a omissão de `observation_ids` (`AUD-F-005`) precisam ser corrigidas antes de persistir `preparation_plan.json`. |
| **`sanitize_dataset(bundle, profile, plan)` $\rightarrow$ `SanitizedDatasetView`** | `slice_bundle_by_observation_ids`, `get_column_array`, `ObservationId`, `dataset_hash` | **Requer Correção Pré-M2 (`AUD-F-005`, `AUD-F-006`)** | 1. `slice_bundle_by_observation_ids` degrada `ObservationId` para `str` quando recebe `Sequence[str]` (`AUD-F-006`).<br/>2. Remover linhas com `target` nulo via `slice_bundle_by_observation_ids` deve produzir um `dataset_hash` sensível aos `observation_ids` retidos (`AUD-F-005`). |
| **`build_partition_plan(...)` & `validate_partition_plan(...)` $\rightarrow$ `PartitionPlan`** | `PartitionPlanId`, `ObservationId`, `derive_seeds`, `spawn_child_seeds`, `config_hash`, `DataIntegrityError` | **Pronto com Ressalva (`AUD-F-003`)** | `derive_seeds` e `spawn_child_seeds` são 100% determinísticos (`SeedSequence`). Recomenda-se adicionar `__slots__ = ()` e normalização NFC em `PartitionPlanId` e `ObservationId` (`AUD-F-003`). |
| **Subcomandos da CLI (`expml data`, `expml partition`)** | `src/experimental_ml/cli/main.py` (`build_parser`, `main`) | **Atenção ao Teste Existente (`test_smoke.py:135`)** | `build_parser()` em `cli/main.py` está limpo e pronto para `parser.add_subparsers(dest="command")`. Contudo, o teste `test_cli_dependencies_pure_stdlib` em [test_smoke.py:135](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/tests/test_smoke.py#L135) possui uma asserção estática AST que proíbe `cli/main.py` de importar `{"core", "metrics", "data", "models", "partition", "features", "numpy"}` no topo do arquivo! No M2, `cli/main.py` deverá delegar para submódulos (`experimental_ml.cli.data`, `experimental_ml.cli.partition`) ou realizar importação tardia (*lazy import*) dentro dos handlers para não quebrar `test_smoke.py` e preservar startup rápido de `expml --version`/`--help`. |

---

## 2. Decisões Arquiteturais em Aberto que Precisam Ser Resolvidas na Entrada do M2 (`READY-02`)

1. **Inclusão de `observation_ids` no `dataset_hash` (`AUD-F-005`):**
   * Formalizar se `core.dataset_hash` deve aceitar um parâmetro opcional `observation_ids` (ou se `DatasetBundle` / `SanitizedDatasetView` devem incluir `observation_ids` no mapa passado a `core.dataset_hash`), cumprindo a exigência da Seção 7.1 de `ARQUITETURA_E_CONTRATOS.md` (linha 707).
2. **Regra para variáveis-alvo binárias com rótulos não numéricos (`dtype=object`, ex.: `["no", "yes"]`) (`AUD-F-011`):**
   * Definir no Specify do M2 se `profile_dataset` classificará alvo binário `object` como `CONFIRMED_ISSUE` (exigindo regra explícita de mapeamento de classe positiva para `{0, 1}` no `PreparationPlan`), garantindo compatibilidade universal com `precision`, `recall` e `f1` (`pos_label=1`).
3. **Estratégia de despacho de subcomandos em `experimental_ml.cli` frente a `test_smoke.py`:**
   * Manter `src/experimental_ml/cli/main.py` livre de imports pesados no topo (usando submódulos ou *lazy imports* nos subcomandos `data` e `partition`), preservando o contrato `CLI-04` (`test_cli_dependencies_pure_stdlib`).

---

## 3. Contabilização Final de Achados e Aplicação da Regra de Decisão (`READY-06`, `READY-07`)

Conforme o Registro Consolidado de Achados ([06-achados.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/06-achados.md)):

* **Achados `CRÍTICO`:** **`0`**
* **Achados `ALTO` classificados como `DEFEITO`:** **`4`** (`AUD-F-001`, `AUD-F-004`, `AUD-F-006`, `AUD-F-008`)
* **Achados `ALTO` classificados como `RISCO`:** **`2`** (`AUD-F-005`, `AUD-F-009`)
* **Achados `MODERADO`:** **`7`** (`2 DEFEITOS`: `AUD-F-002`, `AUD-F-007`; `4 RISCOS`: `AUD-F-003`, `AUD-F-010`, `AUD-F-011`, `AUD-F-012`; `1 MELHORIA`: `AUD-F-013`)
* **Achados `BAIXO`:** **`3`** (`2 MELHORIAS`: `AUD-F-014`, `AUD-F-015`; `1 LIMITAÇÃO DOCUMENTADA`: `AUD-F-016`)

### Regra Objetiva de Decisão Aplicada (`spec.md` — `READY-06`)
> *"O parecer final DEVE declarar `NÃO APTO` se houver $\ge 1$ achado `CRÍTICO` (qualquer categoria) ou $\ge 1$ achado `DEFEITO` `ALTO` não resolvido; `APTO COM RESSALVAS` se não houver `CRÍTICO` nem `DEFEITO` `ALTO`, mas houver achados `MODERADO`/`BAIXO` ou `RISCO`/`MELHORIA` `ALTO` com tratamento planejado antes ou durante o M2; e `APTO` apenas quando não houver nenhum achado acima de `BAIXO`."*

---

## 4. Parecer Formal de Prontidão para o Marco M2

> **VEREDITO FINAL NO ESTADO ATUAL DO COMMIT `6acf6f8`: `NÃO APTO` (Bloqueado por 4 Defeitos de Severidade `ALTO` de Correção Rápida — Faixa P0)**

### Fundamentação Técnica do Parecer
1. **A arquitetura do Marco M1 é estruturalmente sólida:** O grafo de dependências entre `core` ($L_0$), `metrics` ($L_1$), `data` ($L_1$) e `cli` ($L_2$) é 100% acíclico (`ARCH-01..03`), todas as 15 métricas vetorizadas e regras de agregação/ranking (`ADR-005`) operam com precisão matemática e 100% de detecção de mutações (`12/12 KILLED`), o determinismo inter-processos (`PYTHONHASHSEED`) é total (`INT-05`) e a proteção de buffers C (`np.frombuffer`) em arrays numéricos funciona como especificado (`QUAL-05`).
2. **Por que o estado atual recebe `NÃO APTO` imediato:** A auditoria independente descobriu **4 defeitos objetivos de severidade `ALTO`** (`AUD-F-001`, `AUD-F-004`, `AUD-F-006`, `AUD-F-008`) e **2 riscos `ALTO`** (`AUD-F-005`, `AUD-F-009`) que não haviam sido capturados pelos testes unitários isolados de M1.1–M1.4 e que impactam diretamente o código que será escrito no Marco M2 (`DatasetProfile`, `PreparationPlan`, `SanitizedDatasetView` e `PartitionPlan`).
3. **Caminho de Liberação para `APTO` / `APTO COM RESSALVAS`:** Todos os 6 itens da **Faixa P0** ([07-plano-correcoes.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/07-plano-correcoes.md)) são cirúrgicos e localizados (~60 linhas totais em `core/hashing.py`, `data/loader.py`, `data/query.py` e `README.md`), sem exigir redesenho arquitetural nem reabertura ampla dos marcos anteriores. Uma vez aplicado o lote corretivo P0 (e, opcionalmente, P1), o repositório transita imediatamente para **`APTO`** para iniciar o Marco M2.
