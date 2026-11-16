# Relatório da Mega Auditoria Técnica Transversal do MVP (`TA-POS.1` / `pos-1-mega-auditoria-mvp`)

**Data:** 16 de Novembro de 2026  
**Branch:** `feat/pos-1-mega-auditoria-mvp`  
**Status da Auditoria (Fase T2):** Levantamento Concluído — Aguardando Saneamento (Fase T3)  
**Open P0 Findings:** 6  
**Open P1 Findings:** 16  
**Open P2 Findings:** 6  

---

## 1. Resumo Executivo

A Mega Auditoria Transversal (`TA-POS.1`) inspecionou diretamente todos os módulos de `src/experimental_ml/` (Etapas 1 a 6 e camadas transversais), a suíte de testes (`tests/`), `pyproject.toml`, `.specs/STATE.md`, `README.md`, `REFERENCIAS_E_FUNDAMENTACAO.md` e todos os documentos de `engenharia_software/` (`ARQUITETURA_E_CONTRATOS.md`, `ESPECIFICACAO_REQUISITOS.md`, `ETAPA_ATUAL_ENGENHARIA.md`, `PROCESSO_DE_ACEITE_DE_MARCOS.md`), sem presumir que verificações anteriores comprovavam a ausência de defeitos transversais.

- **Verificações Automatizadas Transversais (T1):**
  - `test_audit_xcut02_runtime_purity_ast` (**C1**): **PASSED** (100% dos arquivos em `src/experimental_ml/` importam apenas biblioteca padrão do Python, `experimental_ml` e `numpy`).
  - `test_audit_stage_gates_cli_and_domain_neutrality` (**C2**): **PASSED** (7 portões presentes, `CLI-10` lazy import em `cli.main` e neutralidade de domínio `RNF02`).
- **Inspeção Independente Profunda (T2):**
  - Identificou **6 achados `P0`** (invariantes científicos, vazamento em holdout agrupado/temporal, aplicação de hiperparâmetros tunados na célula final, coerção de `UNDEFINED_NAN` em `TOP_K_RELEVANCE`, probabilidades em `roc_auc`/`log_loss`, precedência `ADR-005` / `compare_by_abs` em `mbe`, e semente em `RANDOM_SEARCH`).
  - Identificou **8 achados `P1` de código/contratos/CLI/portões** e **8 achados `P1` de sincronização documental/referências**.
  - Identificou **6 achados `P2`** (melhorias secundárias e de round-trip/metadados).

---

## 2. Achados `P0` — Invariantes Científicos, Anti-Leakage e Determinismo

### `ACH-POS1-P0-01`: Vazamento de Grupos e Temporal entre Desenvolvimento e Holdout em `CV_AND_HOLDOUT` / `HOLDOUT_ONLY`
- **Onde:** `src/experimental_ml/validation/engine.py:141-154`, `src/experimental_ml/validation/splitters.py:146-213`, `src/experimental_ml/validation/validators.py:135-165`
- **Evidência:** `build_partition_plan` chama `holdout_split` (permutação aleatória simples) mesmo quando `strategy` é `GROUP_KFOLD` ou `TEMPORAL`, dividindo observações do mesmo grupo entre `development_ids` e `holdout_ids` ou misturando passado/futuro no holdout. Além disso, `validate_partition_plan` verifica disjunção de grupos e ordem temporal apenas dentro dos folds de CV, sem validar `Group(development_ids) ∩ Group(holdout_ids) = ∅` nem `max(Time(development_ids)) <= min(Time(holdout_ids))`.
- **Ação de Saneamento (T3):** Respeitar isolamento de grupos e ordem cronológica na separação `development_ids` vs `holdout_ids` e reforçar `validate_partition_plan`.

### `ACH-POS1-P0-02`: Hiperparâmetros Otimizados (`best_params`) e `ModelSpec.parameters` Não Aplicados à Instância no Ajuste Final da Célula
- **Onde:** `src/experimental_ml/orchestration/execution.py:148-163, 185-186`, `src/experimental_ml/models/execution.py:74-110`
- **Evidência:** `execute_single_cell` atualiza `effective_spec.parameters` com `tuning_res.best_params`, mas `instantiate_fresh_model(effective_spec, seed=cell_seed)` chama apenas `model_spec.estimator_factory(seed)` sem aplicar `effective_spec.parameters` (via `set_params` / atributos) antes de `fit_model`.
- **Ação de Saneamento (T3):** Aplicar `model_spec.parameters` em `instantiate_fresh_model` (ou antes de `fit_model`) garantindo que o modelo final da célula use os hiperparâmetros configurados/tunados.

### `ACH-POS1-P0-03`: Coerção Silenciosa de `NaN` (`UNDEFINED_NAN`) para `0.0` em `select_features_in_fold` (`TOP_K_RELEVANCE`)
- **Onde:** `src/experimental_ml/features/selection.py:169-186`
- **Evidência:** Na linha 181 (`abs_val = abs(val) if not math.isnan(val) else 0.0`), features constantes/degeneradas com `MetricStatus.UNDEFINED_NAN` recebem score `0.0` e podem ser incluídas em `ranked_features[:k]`, violando `ADR-005` (`CA-GER-03`).
- **Ação de Saneamento (T3):** Excluir features com `MetricStatus.UNDEFINED_NAN` / `NaN` dos candidatos elegíveis ao ranking `TOP_K_RELEVANCE` e registrar `NaN` (ou desqualificação explícita) sem coerção para `0.0`.

### `ACH-POS1-P0-04`: `METRICS_CATALOG` Omite `requires_probabilities=True` em `roc_auc` e `log_loss` (e `requires_kernel_matrix=True` em `kta`) e `execute_single_cell` Ignora `y_proba`
- **Onde:** `src/experimental_ml/metrics/catalog.py:109-123, 194-222`, `src/experimental_ml/orchestration/execution.py:203-213`
- **Evidência:** `roc_auc` e `log_loss` estão registrados com `requires_probabilities=False` (default), fazendo `tuning/engine.py` e `orchestration/execution.py` passarem `y_pred` (rótulos discretos) em vez de `y_proba`.
- **Ação de Saneamento (T3):** Declarar `requires_probabilities=True` para `roc_auc` e `log_loss` e `requires_kernel_matrix=True` para `kta` em `METRICS_CATALOG`, e passar `pred_outputs["y_proba"]` em `execute_single_cell` quando `spec.requires_probabilities` for verdadeiro.

### `ACH-POS1-P0-05`: Precedência de Cobertura (`ADR-005`) em `_select_observed_leader` e `compare_by_abs=True` para `mbe`
- **Onde:** `src/experimental_ml/statistics/synthesis.py:19-45`, `src/experimental_ml/statistics/comparisons.py:334-340`, `src/experimental_ml/statistics/multiobjective.py:65-77`, `src/experimental_ml/tuning/engine.py:215-224`
- **Evidência:** `_select_observed_leader` não prioriza `MetricStatus.VALID` sobre `MetricStatus.PARTIAL_COVERAGE`, e a comparação de `mbe` (`compare_by_abs=True`) no tuning e na Etapa 5 usa o valor com sinal bruto em vez de `|v|`.
- **Ação de Saneamento (T3):** Priorizar cobertura `VALID` antes de `PARTIAL_COVERAGE` em `_select_observed_leader` e respeitar `compare_by_abs` (via `METRICS_CATALOG` / `is_better`) no tuning e na Etapa 5.

### `ACH-POS1-P0-06`: `RANDOM_SEARCH` Não Repassa `effective_seed` para `generate_candidates` quando `spec.seed` é `None`
- **Onde:** `src/experimental_ml/tuning/engine.py:108-109`, `src/experimental_ml/tuning/candidates.py:58`
- **Evidência:** `run_nested_tuning` calcula `effective_seed = seed if seed is not None else spec.seed`, mas chama `generate_candidates(spec)` sem passar `effective_seed`; quando `spec.seed is None`, `np.random.default_rng(None)` usa entropia do SO (`RNF01`).
- **Ação de Saneamento (T3):** Aceitar `seed: int | None = None` em `generate_candidates` e repassar `effective_seed` em `run_nested_tuning`.

---

## 3. Achados `P1` — Contratos de Código, CLI e Portões de Estágio

### `ACH-POS1-P1-01`: Violação de `CLI-11` em `expml models validate` e `expml models verify`
- **Onde:** `src/experimental_ml/cli/cmd_models.py:59, 93`
- **Evidência:** Imprime `Catalog hash: <64-hex>` diretamente no `stdout`.
- **Ação de Saneamento (T3):** Remover a impressão do hash bruto de 64 caracteres no `stdout` de `cmd_models.py`.

### `ACH-POS1-P1-02`: `TypeError` ao Desserializar `Finding` em `warnings` de `MetricValue` / `AggregatedMetricValue`
- **Onde:** `src/experimental_ml/orchestration/codecs.py:48-56, 81-94, 255-263, 307-319`
- **Evidência:** Serializa/desserializa `Finding` usando chaves inexistentes (`category`, `source_column`, `details`) em vez de `(severity, code, message, context)`.
- **Ação de Saneamento (T3):** Alinhar a serialização/desserialização de `Finding` em `orchestration/codecs.py` com a definição real de `Finding` em `core/findings.py`.

### `ACH-POS1-P1-03`: Consolidação OOF Automática em `CV_AND_HOLDOUT` Usa `sanitized_view.observation_ids` em vez de `partition_plan.development_ids`
- **Onde:** `src/experimental_ml/orchestration/engine.py:218-226, 439-447`
- **Evidência:** Passa todas as observações (incluindo holdout) como `target_observation_ids` para `consolidate_matrix_oof`, marcando incorretamente o OOF como `PARTIAL_COVERAGE` em `CV_AND_HOLDOUT`.
- **Ação de Saneamento (T3):** Passar `tuple(partition_plan.development_ids)` como `target_observation_ids` em `consolidate_matrix_oof`.

### `ACH-POS1-P1-04`: `expml run start/resume` Sem Métricas Default por `TaskType` Causa `IndexError` em `expml stats run`
- **Onde:** `src/experimental_ml/cli/cmd_run.py:84-95, 192-201`, `src/experimental_ml/cli/cmd_stats.py:103, 127`
- **Evidência:** Quando `metrics` não é especificado na execução da matriz, as células são gravadas sem métricas e `expml stats run` falha com `IndexError: tuple index out of range`.
- **Ação de Saneamento (T3):** Definir métricas default canônicas por `TaskType` quando não informadas em `cmd_run.py`/`run_experiment_matrix` e tratar ausência de métricas com `DataIntegrityError` claro em `cmd_stats.py`.

### `ACH-POS1-P1-05`: `expml report export` Falha quando `output_dir == exp_dir` (Default) em Modo `full_package`
- **Onde:** `src/experimental_ml/reporting/packaging.py:247-309`
- **Evidência:** Quando `output_dir` é o próprio `source_experiment_dir`, `data/*` já existe no mesmo caminho, disparando `ContractViolationError` (`force=False`) ou `shutil.SameFileError` (`force=True`).
- **Ação de Saneamento (T3):** Detectar quando `src_file.resolve() == dst_file.resolve()` em `build_reproducibility_package` (registrando os arquivos de `data/` no manifesto/checksums sem tentar sobrescrevê-los sobre si mesmos).

### `ACH-POS1-P1-06`: Fortalecimento dos Portões em `stages/stage_gates.py` e Re-exports em `stages/__init__.py`
- **Onde:** `src/experimental_ml/stages/stage_gates.py`, `src/experimental_ml/stages/__init__.py`
- **Evidência:** `stages/__init__.py` não re-exporta `verify_statistics_gate` e `verify_report_gate`; `verify_models_gate`/`load_models_catalog` não recalcula `catalog_hash`; `verify_runs_gate` usa `.replace("cell_", "")` em vez de `.removeprefix("cell_")` e pula gates upstream se arquivos forem deletados; `verify_partition_gate` não valida unicidade de `observation_id` em `splits.csv.gz` nem `validate_partition_plan`.
- **Ação de Saneamento (T3):** Exportar todos os 7 portões em `stages/__init__.py` e fortalecer as verificações de integridade em `stage_gates.py` e `models/catalog.py`.

### `ACH-POS1-P1-07`: Tabela da Família B (`B_FEATURE_SCENARIOS`) Lê Chave Incorreta para `selected_features`
- **Onde:** `src/experimental_ml/reporting/tables.py:125`
- **Evidência:** Busca `sc.get("features", sc.get("candidate_features", ()))`, mas `FeatureScenario.to_dict()` grava `"selected_features"`, resultando em `n_features = 0`.
- **Ação de Saneamento (T3):** Incluir `"selected_features"` (e `selection_strategy`) na extração da Família B em `reporting/tables.py`.

### `ACH-POS1-P1-08`: Mutabilidade Residual em `Finding.context`, `DatasetProfile` e `TwoLayerPreprocessingState`
- **Onde:** `src/experimental_ml/core/findings.py:32-40`, `src/experimental_ml/data/profiling.py:158-171`
- **Evidência:** `Finding.context` e `DatasetProfile` não convertem `dict`/`list` para `MappingProxyType`/`tuple` em `__post_init__`.
- **Ação de Saneamento (T3):** Adicionar `__post_init__` em `Finding` e `DatasetProfile` garantindo imutabilidade.

---

## 4. Achados `P1` — Documentação de Engenharia, `README.md`, `REFERENCIAS_E_FUNDAMENTACAO.md` e `.specs/STATE.md`

### `ACH-POS1-P1-09`: `ARQUITETURA_E_CONTRATOS.md` com Cabeçalho, Tabela 7.1 (M6/M7) e Seção 7.1 Defasados
- **Onde:** `engenharia_software/ARQUITETURA_E_CONTRATOS.md:4-6, 144, 272, 276, 696-697, 702-855`
- **Evidência:** Cabeçalho e Seção 7.1 ainda indicam parada no Marco M3 (236 testes) e Tabela 7.1 marca M6 e M7 como `*(Planejado)*`.

### `ACH-POS1-P1-10`: `ARQUITETURA_E_CONTRATOS.md` com Subcomandos CLI, Assinaturas e Caminhos de Artefatos Divergentes do Código Real
- **Onde:** `engenharia_software/ARQUITETURA_E_CONTRATOS.md:148, 150, 169-171, 213, 310-313, 355-356, 434, 480, 590, 620-636, 668, 696, 868`
- **Evidência:** Lista `expml stats compare|pareto|acquire` (real: `run|status|verify`), `expml report package` (real: `export`), ordem de argumentos antiga em `fit_model`/`predict_model`/`select_features_in_fold`, nomes antigos `holm_bonferroni`/`benjamini_hochberg` (real: `adjust_pvalues_holm`/`adjust_pvalues_bh`), `save_cell_result` (real: `save_cell_artifacts`) e caminhos antigos na Seção 5 (`splits.parquet`, `descriptive_summary.json`, etc.).

### `ACH-POS1-P1-11`: `ESPECIFICACAO_REQUISITOS.md` Sem Notas de Implementação para M4, M5, M6 e M7 e com Cabeçalho em M3
- **Onde:** `engenharia_software/ESPECIFICACAO_REQUISITOS.md:4-6, 52-58, 66-70, 76-81, 87-90, 137-138`
- **Evidência:** Cabeçalho indica M3 (236 testes) e `RF3.1–RF3.6`, `RF4.3–RF4.7`, `RF5.1–RF5.6`, `RF6.1–RF6.4`, `CA-E6-01` e `CA-E6-02` não trazem a anotação `*(Implementado no Marco M...)*`.

### `ACH-POS1-P1-12`: `PROCESSO_DE_ACEITE_DE_MARCOS.md` com Tabela da Seção 5 Parada em M1.2 (30 testes)
- **Onde:** `engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md:75, 103-108`
- **Evidência:** Lista `M1.3` como "Não Iniciado" e `M2 a M7` como "Planejados".

### `ACH-POS1-P1-13`: `README.md` com `report planejado` na Seção 4, Pacote `reporting/` Ausente da Árvore, Flags Incorretas em `expml run` e Soma de Testes por Domínio Defasada
- **Onde:** `README.md:138-151, 512-517, 534-545, 575-588`
- **Evidência:** Linha 138 usa `--error-policy FAULT_TOLERANT` (o parser exige `fault_tolerant`); linhas 141–151 usam `--experiment-dir` em `run resume|status|verify` (o parser exige `--run-dir`); linha 517 diz `report planejado`; árvore na Seção 5 omite `reporting/`; tabela da Seção 6 não inclui a linha do domínio de Relatórios e Reprodutibilidade (M7). *(Nota: em T3 serão corrigidas apenas as divergências factuais no `README.md`, sem adicionar novos blocos longos de exemplos, pois na etapa seguinte `TA-POS.2` o `README.md` será enxugado e apontará para o Guia do Usuário, `engenharia_software/` e `REFERENCIAS_E_FUNDAMENTACAO.md`).*

### `ACH-POS1-P1-14`: `REFERENCIAS_E_FUNDAMENTACAO.md` — Subcasos $s^2_d = 0$ no Nadeau-Bengio, Typo `CA-E5-03`, Nota `.tla` e Referências Kuncheva/KTA/Lentz
- **Onde:** `REFERENCIAS_E_FUNDAMENTACAO.md:4-5, 25-44, 133, 174, 253, 278, 284` (e `ARQUITETURA_E_CONTRATOS.md:192, 865`)
- **Evidência:** Documentar os dois subcasos de $s^2_d = 0$ ($\bar{d} = 0 \Rightarrow t=0, p=1$ vs $\bar{d} \ne 0 \Rightarrow t=\pm\infty, p=0$), corrigir `CA-E5-03` para `CA-E5-02`, atualizar a nota de `MatrixExecutionAndResume.tla` e incluir a fundamentação de Kuncheva (2007), KTA (Cristianini et al., 2001) e Lentz (Student-$t$ pura em NumPy).

### `ACH-POS1-P1-15`: Sincronização da Contagem Total de Testes em Todos os Documentos
- **Onde:** `README.md`, `engenharia_software/*.md`, `.specs/STATE.md`
- **Evidência:** Unificar a contagem total exata da suíte de testes automatizados em todos os documentos após a adição dos testes de regressão do `TA-POS.1`.

### `ACH-POS1-P1-16`: Atualização do Bloco `Handoff` e Decisão Arquitetural em `.specs/STATE.md`
- **Onde:** `.specs/STATE.md:190-202`
- **Evidência:** Atualizar o estado para refletir os merges de M7 na `main` e a conclusão da Mega Auditoria `TA-POS.1`.

---

## 5. Achados `P2` — Melhorias Secundárias (Também Incluídas no Saneamento T3)

- **`ACH-POS1-P2-01` (`models/catalog.py:166-185`):** Preservar todos os 9 campos de `ModelCapabilities` em `_capabilities_to_dict` / `_capabilities_from_dict`.
- **`ACH-POS1-P2-02` (`features/types.py:214-255`):** Restaurar `float("nan")` quando `None` é lido na `pairwise_redundancy_matrix` em `ExploratoryFeatureReport.from_dict`.
- **`ACH-POS1-P2-03` (`cli/cmd_stats.py:67-73`):** Passar o total real de features candidatas do dataset/cenário para `n_total_candidates_per_config` em `consolidate_descriptive` quando disponível.
- **`ACH-POS1-P2-04` (`engenharia_software/ARQUITETURA_E_CONTRATOS.md:496`):** Alinhar o texto sobre células `CANCELLED` na entrada da Etapa 5 com `CA-E5-01` e `AD-013`.
- **`ACH-POS1-P2-05` (`REFERENCIAS_E_FUNDAMENTACAO.md:233`):** Substituir menção a `run_meta.json` por `runs/execution_state.json` e `reproducibility/checksums.sha256`.
- **`ACH-POS1-P2-06` (`pyproject.toml:16-19`):** Adicionar classificadores Python `3.13` / `3.14` conforme `RNF06`.
