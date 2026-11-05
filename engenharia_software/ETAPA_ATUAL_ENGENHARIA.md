# Engenharia de Software — `experimental-ml-framework`

> **Documento de Registro de Estado da Engenharia**  
> **Data:** 03 de Novembro de 2026  
> **Repositório de Origem (Referência Científica):** `prognose_florestal`  
> **Novo Repositório (Framework Científico Agnóstico):** `experimental-ml-framework`  
> **Especificação de Requisitos (SRS v2.0):** [`ESPECIFICACAO_REQUISITOS.md`](./ESPECIFICACAO_REQUISITOS.md)  
> **Arquitetura, Contratos e Modelo de Dados:** [`ARQUITETURA_E_CONTRATOS.md`](./ARQUITETURA_E_CONTRATOS.md)  
> **Governança de Validação e Aceite:** [`PROCESSO_DE_ACEITE_DE_MARCOS.md`](./PROCESSO_DE_ACEITE_DE_MARCOS.md)

---

## 1. Etapa Atual no Ciclo de Vida da Engenharia

O projeto encontra-se na **Fase 4: Implementação Guiada por Testes (TDD) do MVP**, seguindo o processo de aceite de marcos ([`PROCESSO_DE_ACEITE_DE_MARCOS.md`](./PROCESSO_DE_ACEITE_DE_MARCOS.md)) integrado à skill `tlc-spec-driven`.

As entregas **Marco M1.1 (`m1-1-setup-cli-smoke`)**, **Marco M1.2 (`core`)**, **Marco M1.3 (`metrics`)** e **Marco M1.4 (`datasets-schemas`)** foram concluídas e formalmente aceitas com aprovação em testes automatizados e homologação manual. A Fase 1 (Setup e Fundações Transversais) está integralmente concluída. O próximo passo de desenvolvimento é o **Marco M2 (`data` + `validation` + CLI `data`/`partition`)**.

```mermaid
flowchart LR
    Fase1["Fase 1: Auditoria Técnica<br/>(Concluída)"] --> Fase2["Fase 2: Requisitos das 6 Etapas<br/>(Concluída — SRS v2.0)"]
    Fase2 --> Fase3["Fase 3: Arquitetura, Contratos & MVP<br/>(Concluída)"]
    Fase3 --> Fase4["Fase 4: Implementação TDD do MVP<br/>(Fase 1 Concluída — M1.1 a M1.4 Homologados)"]
    Fase4 --> Fase5["Fase 5: Verificação Experimental<br/>(Pendente)"]
    
    style Fase1 fill:#d4edda,stroke:#28a745
    style Fase2 fill:#d4edda,stroke:#28a745
    style Fase3 fill:#d4edda,stroke:#28a745
    style Fase4 fill:#d4edda,stroke:#28a745,stroke-width:2px
    style Fase5 fill:#f8f9fa,stroke:#6c757d
```

### O que já foi realizado:
1. **Fase 1 — Auditoria Técnica e Baseline (`prognose_florestal`):**
   * Mapeamento integral de dados, scripts, algoritmos clássicos, modelos biométricos e resolvedores quânticos (HHL).
   * Catalogação das métricas validadas de referência e identificação de vulnerabilidades metodológicas.
2. **Fase 2 — Engenharia de Requisitos das 6 Etapas ([`ESPECIFICACAO_REQUISITOS.md`](./ESPECIFICACAO_REQUISITOS.md)):**
   * Especificação detalhada das **6 etapas operacionais** do ciclo experimental:
     * **Etapa 1:** Entrada, triagem exploratória somente-leitura, separação entre problemas confirmados e alertas heurísticos, e plano explícito de preparação.
     * **Etapa 2:** Exploração de relações rotulada como exploratória, criação manual (`mode="FIXED"`) e guiada/dinâmica (`mode="DYNAMIC"` ajustado por *fold*) com rastreabilidade de estabilidade.
     * **Etapa 3:** Registro de modelos heterogêneos (`ModelSpec`), suporte a modelos analíticos sem `fit` artificial, pré-processamento em duas camadas auditadas, *tuning* aninhado (*Nested CV*) e coleta extensível de diagnósticos internos.
     * **Etapa 4:** `PartitionPlan` imutável e compartilhado (CV, Holdout e CV + Holdout Final), módulo de orquestração com máquina de estados por célula, tolerância a falhas sem mascaramento, controle de paralelismo em dois níveis, *checkpoint/resume*, tempos desagregados e predições *out-of-fold* indexadas por `observation_id`.
     * **Etapa 5:** Consolidação descritiva e comparação estatística separando desempenho observado, incerteza, significância estatística, tamanho de efeito, relevância prática e custo computacional (Fronteira de Pareto), com síntese textual estritamente auditável.
     * **Etapa 6:** Geração desacoplada de Relatórios Científicos Completos (Markdown/HTML) e artefatos modulares das 7 famílias de tabelas e figuras, com manifesto de proveniência (`ArtifactProvenance`) e pacote portável de reprodutibilidade.
3. **Fase 3 — Arquitetura Geral, Contratos e Recorte de MVP ([`ARQUITETURA_E_CONTRATOS.md`](./ARQUITETURA_E_CONTRATOS.md)):**
   * Definição da arquitetura em três camadas (Definição e Triagem, Validação e Execução Matricial, Comparação Estatística e Publicação), do pipeline operacional de dados em seis etapas e das dependências entre os módulos de `src/experimental_ml/`.
   * Formalização das entradas, saídas, invariantes e pontos de extensão de cada etapa e módulo.
   * Modelagem de dados completa do experimento e estrutura de diretórios do pacote de reprodutibilidade.
   * Definição explícita do **MVP Essencial** vs. **Evoluções Posteriores**.
4. **Fase 4 — Marco M1.1 Concluído (`m1-1-setup-cli-smoke`):**
   * Configuração de empacotamento com `pyproject.toml` baseada no backend Hatchling (`hatchling.build`) e declaração `requires-python = ">=3.10"`.
   * Inicialização do layout `src/experimental_ml/` expondo `__version__ = "0.1.0.dev0"`.
   * Implementação do ponto de entrada da CLI modularizada em `src/experimental_ml/cli/main.py` com `argparse` da biblioteca padrão, suportando `--version`, `--help` e código de saída 2 para argumentos inválidos.
   * Criação e aprovação integral da suíte de fumaça automatizada em `tests/test_smoke.py` (12 testes aprovados via `pytest`).
   * Validação da instalação editável (`pip install -e ".[dev]"`) no ambiente virtual `.venv` local (Python 3.12), com o executável `expml` disponível diretamente no PATH.
5. **Fase 4 — Marco M1.2 Concluído (`m1-2-core`):**
   * Adição da dependência `numpy>=1.24.0` ao `pyproject.toml`.
   * Implementação do módulo `src/experimental_ml/core/` (Nível 0 transversal, sem OOP para lógica de negócio conforme **ADR-008**):
     * `types.py`: tipos de identificadores de domínio imutáveis (`ExperimentId`, `PartitionPlanId`, `ScenarioId`, `ModelId`, `CellId`, `ComparisonId`, `ArtifactId`, `ObservationId`) com validação de preenchimento e rejeição de strings inválidas.
     * `enums.py`: enumerações canônicas baseadas em `str, Enum` (`TaskType`, `ExecutionStatus`, `FindingSeverity`, `MetricDirection`, `AggregationScope`, `MetricStatus`, `ErrorPolicy`).
     * `findings.py`: estrutura imutável `Finding`, construtores `make_finding` e `make_warning` e hierarquia de exceções de integridade (`ExperimentalMLError`, `ContractViolationError`, `DataIntegrityError`, `ConfigurationError`).
     * `seeds.py`: geradores determinísticos puros `derive_seeds` e `spawn_child_seeds` baseados em `numpy.random.SeedSequence` (RNF01, ADR-007).
     * `hashing.py`: implementação de `config_hash` e `dataset_hash` cumprindo 100% das regras canônicas do **ADR-007** (NFC, ordenação estável por code points UTF-8, distinção de tipos escalares e coleções, normalização de `-0.0 -> 0.0`, `NaN` e `+/-Inf`).
     * `__init__.py`: re-exportação pública via `__all__`.
   * Implementação da suíte de testes unitários `tests/unit/test_core.py` com 18 testes automatizados aprovados (totalizando 30 testes aprovados na suíte geral).
   * Execução do portão de verificação independente da skill `tlc-spec-driven` (`proofs.md` e `verification.md` com veredito `PASS`, 18/18 checks aprovados).
6. **Fase 4 — Marco M1.3 Concluído (`m1-3-metrics`):**
   * Implementação do módulo `src/experimental_ml/metrics/` (Nível 1 transversal, sem lógica de negócio em OOP):
     * `types.py`: estruturas imutáveis de avaliação (`MetricValue`, `AggregatedMetricValue`, `MetricSpec`, `RankedCandidate`) e enumeração canônica fechada `MetricEvaluationScope` com validação estrita.
     * `validation.py`: validações numéricas puras em `float64`, integridade dimensional e mitigação de overflow quadrático intermediário via `scaled_quadratic_sum`.
     * `regression.py`: funções puramente vetorizadas em `float64` de erros em escala direta (`mae`, `rmse`, `mbe` preservando viés assinado), razões adimensionais (`r2`, `rmse_rel_pct`, `mape`, `pearson`) e alinhamento de Gram (`kta` uncentered e centered $HKH$), tratando casos degenerados com `MetricStatus.UNDEFINED_NAN`.
     * `classification.py`: métricas discretas (`accuracy`, `balanced_accuracy`, `precision`, `recall`, `f1` avaliado diretamente pelo próprio denominador $2TP + FP + FN$) e probabilísticas (`roc_auc` com empates exatos via postos médios e OVR, `log_loss` com validação estrita de distribuições e clipping $\epsilon = 10^{-15}$).
     * `catalog.py`: registro imutável centralizado `METRICS_CATALOG` com as 15 especificações canônicas (`compare_by_abs=True` exclusivamente em `mbe`), funções de consulta `get_metric_spec`, `list_metrics` e despacho `compute_metric`.
     * `aggregation.py`: comparador `is_better` compatível com `compare_by_abs`, agregador inter-dobras `aggregate_fold_metrics` gerando `VALID`, `PARTIAL_COVERAGE` e `UNDEFINED_NAN`, e ranqueador lexicográfico `rank_configurations` (ADR-005) com precedência estrita de cobertura.
     * `__init__.py`: re-exportação de 27 símbolos públicos com `__all__`.
   * Aprovação integral da suíte de testes unitários `tests/unit/test_metrics.py` com 22/22 checks automatizados aprovados (totalizando 52 testes aprovados na suíte geral).
   * Verificação independente TLC (`proofs.md` e `verification.md` com veredito `PASS`, 0 findings e 0 erros em `validate_verification.py`).
   * Execução e aprovação completa do roteiro de aceitação do consumidor (`ACCEPTANCE.md`) e cenário integrado registrado em `RESULTS.md`.

---

## 2. Síntese da Arquitetura em Camadas, Pipeline de Etapas e Módulos (`src/experimental_ml/`)

| Camada Arquitetural | Nível de Dependência | Módulo (`src/experimental_ml/`) | Etapa no Pipeline Operacional | Funções e Estruturas Principais de Saída (Sem OOP) |
| :--- | :--- | :--- | :--- | :--- |
| **Fundação Transversal** | Nível 0 | `core` | Transversal (Etapas 1–6) | Tipos de IDs, `derive_seeds` (`SeedSequence`), `config_hash`, `dataset_hash` e funções de validação/alertas |
| **Fundação Transversal** | Nível 1 | `metrics` | Transversal (Etapas 2, 3, 4 e 5) | `METRICS_CATALOG`, `MetricValue`, `AggregatedMetricValue`, `aggregate_fold_metrics`, `is_better` e 15 funções de métricas vetorizadas |
| **Camada 1: Definição e Triagem** | Nível 1 | `data` | Etapa 1 | `load_dataset`, `profile_dataset`, `create_preparation_plan`, `sanitize_dataset` $\rightarrow$ `DatasetBundle`, `DatasetProfile`, `PreparationPlan`, `SanitizedDatasetView` |
| **Camada 1: Definição e Triagem** | Nível 2 | `features` | Etapa 2 | `explore_features`, `validate_scenarios`, `select_features_in_fold` (seletores e `PCA`) $\rightarrow$ `ExploratoryFeatureReport`, catálogo `scenarios` (`FIXED`/`DYNAMIC`) |
| **Camada 1: Definição e Triagem** | Nível 2 | `models` | Etapa 3A | `instantiate_fresh_model`, `fit_model`, `predict_model`, `extract_model_diagnostics`, `fit_two_layer_preprocessing` (incluindo roteamento para kernels externos) $\rightarrow$ `ModelSpec`, `ModelDiagnostics` |
| **Camada 1: Definição e Triagem** | Nível 3 | `tuning` | Etapa 3B | `run_nested_tuning` (`fixed`, `grid_search`, `random_search`) $\rightarrow$ `HyperparameterSearchSpec`, histórico de tentativas |
| **Camada 2: Validação e Execução Matricial** | Nível 2 | `validation` | Etapa 4A | `build_partition_plan`, `validate_partition_plan` (`kfold_split`, `stratified_kfold_split`, `group_kfold_split`, `bootstrap_split`, `temporal_split`, `holdout_split`) $\rightarrow$ `PartitionPlan` |
| **Camada 2: Validação e Execução Matricial** | Nível 4 | `orchestration` | Etapa 4B | `run_experiment_matrix`, `resume_experiment_matrix`, `save_cell_result` $\rightarrow$ `CellResultRecord`, `PredictionRecord` (com `y_std` e comitê $\hat{\mu}_i, \hat{\sigma}_i$), `TimingBreakdown` |
| **Camada 3: Comparação Estatística e Publicação** | Nível 5 | `statistics` | Etapa 5 | `consolidate_descriptive`, `evaluate_method_suitability`, `run_statistical_comparisons`, `compute_pareto_frontier`, `score_candidate_acquisition`, `synthesize_conclusions` $\rightarrow$ `StatisticalComparisonReport`, `StructuredConclusion` |
| **Camada 3: Comparação Estatística e Publicação** | Nível 6 | `reporting` | Etapa 6 | `select_report_content`, `build_table_model`, `build_figure_spec`, `render_full_report`, `build_reproducibility_package` $\rightarrow$ `TableModel`, `PlotSpecification`, `ArtifactProvenance` |
| **Interface de Terminal** | Nível 7 | `cli` | Subcomandos por Etapa | CLI modularizada (`expml data`, `features`, `models`, `partition`, `run`, `stats`, `report`) separada da lógica de negócio |

---

## 3. Roadmap Incremental de Implementação TDD (Marcos M1 a M7)

Todo marco segue o processo de governança estabelecido em [`PROCESSO_DE_ACEITE_DE_MARCOS.md`](./PROCESSO_DE_ACEITE_DE_MARCOS.md), estruturado em `SPEC.md`, `ACCEPTANCE.md` e `RESULTS.md`.

1. **Marco M1 (`core` + `metrics` + `datasets` + esqueleto `cli`) — Entregas Verificáveis:**
   * **M1.1 (Concluído e Aceito — Configuração, `.venv`, Esqueleto da CLI e *Smoke Tests*):** Criação do `.venv` (Python 3.12), `pyproject.toml` (Hatchling, declaração `requires-python = ">=3.10"`, entrypoint `expml`), esqueleto modular em `src/experimental_ml/cli/main.py`, aprovação de `tests/test_smoke.py` com 12/12 testes e homologação manual aprovada. Registrado com `SPEC.md`, `ACCEPTANCE.md` e `RESULTS.md` sob `.specs/features/m1-1-setup-cli-smoke/`.
   * **M1.2 (Concluído e Aceito — Contratos, Implementação Funcional e Testes de `core`):** Identificadores imutáveis, constantes/enums, função pura `derive_seeds` (`SeedSequence`), `config_hash` e `dataset_hash` (ADR-007: Unicode NFC, `-0.0`, `NaN`/`Inf`, coleções aninhadas), construtores de achados e exceções de contrato, com aprovação de `tests/unit/test_core.py` (18/18 testes), verificação independente TLC (`proofs.md`, `verification.md`) e homologação manual aprovada. Registrado com `SPEC.md`, `ACCEPTANCE.md` e `RESULTS.md` sob `.specs/features/m1-2-core/`.
   * **M1.3 (Concluído e Aceito — Contratos, Implementação Funcional e Testes de `metrics`):** `MetricValue`, `AggregatedMetricValue`, `MetricSpec`, `RankedCandidate`, catálogo `METRICS_CATALOG` com as 15 métricas, regras de propagação de `MetricStatus.UNDEFINED_NAN`, `is_better`, `aggregate_fold_metrics`, `rank_configurations` (ADR-005) e as 15 funções de métricas vetorizadas testadas com tolerâncias específicas (`rtol`/`atol`) por família (`tests/unit/test_metrics.py` com 22/22 checks aprovados), verificação independente TLC (`proofs.md`, `verification.md`) e roteiro `ACCEPTANCE.md` com evidências em `RESULTS.md`.
   * **M1.4 (Concluído e Aceito — Contratos, Ingestão Tabular, Imutabilidade e Esquemas de `data`):** `DatasetSchemaSpec`, `ColumnSemanticType`, `ColumnDescriptor`, `DatasetBundle` com buffers imutáveis em nível de C-API (recusando `setflags(write=True)` com `ValueError`), parser estrito RFC 4180 com sniffer de delimitadores e detecção de *ragged rows*, geração/validação de `ObservationId`, cópias defensivas na memória, cálculo dos hashes tripartites (`dataset_hash` canônico, `raw_source_hash` e `schema_hash`) e utilitários somente-leitura `get_column_array` e `slice_bundle_by_observation_ids`. Aprovado com 29/29 testes unitários em `tests/unit/test_data_schemas.py`, 81/81 testes na suíte geral, verificação independente TLC (`proofs.md`, `verification.md` com 0 findings) e homologação manual aprovada sob `.specs/features/m1-4-datasets-schemas/`.
2. **Marco M2 (`data` + `validation` + CLI `data`/`partition` — Próximo Marco):** Funções de triagem estatística (`profile_dataset` separando problemas confirmados vs. alertas heurísticos), plano de preparação (`create_preparation_plan`), saneamento (`sanitize_dataset`) e geração/validação matemática do `PartitionPlan` (`build_partition_plan`, `validate_partition_plan`).
3. **Marco M3 (`features` + CLI `features`):** Função `explore_features` rotulada, validação de cenários (`FIXED` e `DYNAMIC`) e seleção dinâmica ajustada estritamente no treino de cada *fold* (`select_features_in_fold`), com medição de estabilidade de seleção.
4. **Marco M4 (`models` + `tuning` + CLI `models`):** Funções `instantiate_fresh_model`, `fit_model`, `predict_model` (clássicos, analíticos com `requires_fit=False` e quânticos/customizados), pré-processamento funcional em 2 camadas (`fit_two_layer_preprocessing`, `apply_two_layer_preprocessing`) com bloqueio de duplicação e *Nested Tuning* (`run_nested_tuning`).
5. **Marco M5 (`orchestration` + CLI `run`):** Funções `run_experiment_matrix` e `resume_experiment_matrix` com máquina de estados, modos `FAULT_TOLERANT` / `FAIL_FAST`, paralelismo em dois níveis, persistência atômica (`save_cell_result`) e retomada verificada (*Checkpoint & Resume*).
6. **Marco M6 (`statistics` + CLI `stats`):** Funções de consolidação descritiva, adequação metodológica, tratamento de *folds* incompletos, Nadeau-Bengio, Wilcoxon, Holm-Bonferroni, Benjamini-Hochberg, tamanho de efeito, relevância prática, Fronteira de Pareto, funções de aquisição e `synthesize_conclusions`.
7. **Marco M7 (`reporting` + CLI `report` + Verificação `prognose_florestal`):** Funções de geração de relatórios completos (MD/HTML), 7 famílias de tabelas (CSV/MD/LaTeX `booktabs`) e figuras (PNG/SVG/PDF), manifesto de proveniência (`ArtifactProvenance`), pacote de reprodutibilidade e reprodução agnóstica do experimento de referência `prognose_florestal`.
