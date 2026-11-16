# Feature: m6-1-descriptive-consolidation-suitability

**Approved**: 2026-11-16 - user: "aprovado"

## Problem Statement

Na arquitetura do `experimental-ml-framework`, a Etapa 5 (Consolidação dos Resultados e Comparação Estatística Rigorosa) tem como responsabilidade científica transformar os artefatos de execução matricial da Etapa 4B (`runs/`, `predictions/` e `PartitionPlan`) em consolidações descritivas rigorosas, avaliações formais de adequação metodológica, inferência estatística com correção de dependência e síntese auditável, eliminando declarações arbitrárias de superioridade ou "vencedores" sem evidência estatística.

Atualmente, o framework orquestra e persiste com sucesso a execução matricial tridimensional (M5), salvando células (`CellResultRecord`), predições individuais indexadas por `ObservationId` (`PredictionRecord`) e consolidações out-of-fold (`ConsolidatedOofPredictions`). No entanto, inexiste ainda no subsistema `src/experimental_ml/statistics/`:
1. Um contrato formal de validação de transição da Etapa 4B para a Etapa 5, que verifique o estado do experimento e bloqueie a consolidação caso haja células em estados não-terminais (`PENDING` ou `RUNNING`, indicando execução ainda ativa) ou se nenhuma célula tiver sido concluída com sucesso (`completed_cells == 0`), distinguindo estados terminais do processo de resultados utilizáveis (células `CANCELLED` e `FAILED` registradas como não-concluídas, sem coerção espúria para zero) (`CA-E5-01`).
2. O Submódulo 5A (`consolidate_descriptive`), capaz de reunir resultados por configuração `(model_id, scenario_id)`, calcular a taxa de cobertura efetiva de folds ($C = \text{completed\_folds} / \text{total\_folds}$), classificar o status de cobertura (`VALID` para $C = 1.0$, `PARTIAL_COVERAGE` para $0.0 < C < 1.0$ e `NO_COVERAGE` para $C = 0.0$), manter células `FAILED` e `CANCELLED` explicitamente documentadas em listas separadas (`failed_fold_ids`, `cancelled_fold_ids`) sem descarte silencioso, e computar estatísticas descritivas (média, desvio padrão amostral, mediana, IQR) para métricas e tempos computacionais desagregados com suporte a métricas sem valores válidos (`n_valid == 0`).
3. O Submódulo de Adequação Metodológica (`evaluate_method_suitability`), capaz de inspecionar a estrutura real do particionamento (`PartitionPlan` em seus regimes canônicos `CV_ONLY`, `HOLDOUT_ONLY` e `CV_AND_HOLDOUT`) e os resultados disponíveis para determinar quais testes de hipótese e procedimentos de multiplicidade são cientificamente válidos para aquele desenho experimental:
   - Alertando formalmente sobre a dependência induzida pela sobreposição de treino na validação cruzada através da razão de sobreposição média $r = \frac{1}{J} \sum r_j$ e razões por dobra $r_j = n_{\text{val}, j} / n_{\text{train}, j}$;
   - Exigindo pareamento estrito ($J_{\text{pareados}} \ge 2$) para testes entre partições de validação cruzada;
   - Bloqueando testes multi-fold em regimes de holdout único (`HOLDOUT_ONLY`, $J = 1$) por ausência de variabilidade amostral entre partições, sem recomendar erroneamente agregações out-of-fold inexistentes;
   - Emitindo alerta metodológico estrutural quando $J < 6$ (ou $J_{\text{pareados}} < 6$) no Wilcoxon, esclarecendo a impossibilidade matemática de rejeição bicaudal a $\alpha = 0.05$ (p-valor mínimo $2/2^5 = 0.0625$), sem assumir que $J \ge 6$ baste para conferir poder estatístico adequado;
   - Isolando estritamente a avaliação de holdout final em `CV_AND_HOLDOUT`, onde $J = \text{len}(plan.folds)$ refere-se exclusivamente às dobras de desenvolvimento, nunca tratando o holdout como dobra adicional de CV.
4. Uma política explícita para comparações incompletas (`IncompleteComparisonPolicy`), fornecendo suporte para execução restrita a subconjuntos comuns de folds pareados válidos (`ALLOW_COMMON_SUBSET`) exclusivamente como análise condicional/alternativa com aviso explícito de perda de cobertura e potencial viés de atrito, ou rejeição estrita (`STRICT_COMPLETE_ONLY`).
5. Estruturas imutáveis e puras em Python/NumPy, em estrita conformidade com `XCUT-02` e `RNF02`, reutilizando tipos já consolidados como `SelectionStabilityReport` (M3.3) e `MetricStatus` (M1.3), servindo de alicerce para a inferência pareada (M6.2), a Fronteira de Pareto e síntese estruturada (M6.3) e a CLI `expml stats` (M6.4).

## Out of Scope

- Implementação das funções numéricas de inferência pareada (teste $t$ corrigido de Nadeau-Bengio com correção de variância, teste pareado de postos com sinal de Wilcoxon com eliminação de empates em zero, Cohen's $d$, Holm-Bonferroni e Benjamini-Hochberg) — escopo do Sub-marco M6.2.
- Análise multiobjetivo, cálculo da Fronteira de Pareto e síntese explicativa em linguagem natural (`StructuredConclusion`, `synthesize_conclusions`) — escopo do Sub-marco M6.3.
- Persistência em disco de `statistics/` e portão de estágio `verify_statistics_gate` — escopo do Sub-marco M6.4.
- Interface de linha de comando `expml stats run/status/verify` — escopo do Sub-marco M6.4.
- Inclusão de qualquer dependência externa de runtime além de `numpy>=1.24.0` (`XCUT-02`).
- Acoplamento a qualquer domínio aplicado ou dados reais específicos (`RNF02`, `CA02`).

## Assumptions & Open Questions

**Open questions:** none - os contratos de consolidação descritiva, avaliação de adequação metodológica e política de incompletude foram previamente fixados na SRS (RF5.1, RF5.2, RF5.3, CA-E5-01) e no Documento de Arquitetura (Seção 3.5), refinados pela revisão técnica de consistência com M1–M5.

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Dependência de runtime do subsistema `statistics` | `numpy>=1.24.0` e biblioteca padrão Python | Atende a `XCUT-02` e `RNF03`, garantindo operação puramente offline e sem dependências pesadas de terceiros |
| Semântica de estados em `execution_state.json` | Estados não-terminais (`PENDING`, `RUNNING`) bloqueiam transição para Etapa 5; estados terminais (`COMPLETED`, `FAILED`, `CANCELLED`) são discriminados em listas separadas | Garante consistência estrita com M5 (`state.py`, `engine.py`, `stage_gates.py`), impedindo consolidação de processos ativos sem confundir falhas e cancelamentos com sucessos |
| Cobertura nula ($C = 0.0$) | Representada formalmente por `CoverageStatus.NO_COVERAGE` | Permite que configurações sem nenhuma partição concluída com sucesso constem no relatório sem fabricação de métricas artificiais |
| Tratamento de células com falha ou canceladas | Registradas em `failed_fold_ids` e `cancelled_fold_ids` respectivamente, com métricas `{}` e sem coerção para zero | Cumpre `CA-E5-01` e `RF5.3`, documentando a perda de cobertura sem mascarar problemas computacionais |
| Tratamento de métricas sem valores válidos em `AggregatedMetricStats` | `n_valid: int`, `n_total: int`, `status: MetricStatus`; se `n_valid == 0`, campos numéricos recebem `None` | Previne falhas de coerção, respeita a semântica de `MetricStatus.UNDEFINED_NAN` (ADR-005) e não injeta `0.0` artificial |
| Cálculo do desvio padrão amostral entre folds ($n_{\text{valid}} \ge 2$) | Desvio padrão amostral com graus de liberdade `ddof=1`; para $n_{\text{valid}} < 2$, retorna `None` | Cumpre `CA-GER-03` e `ACH-M5-01`, assegurando rigor estatístico e ausência de dispersão fabricada |
| Fator de correção de sobreposição de treino em CV | Razão média $r = \frac{1}{J} \sum_{j=1}^J \frac{n_{\text{val}, j}}{n_{\text{train}, j}}$ e preservação de tupla de razões por dobra $(r_1, \dots, r_J)$ | Modela com exatidão matemática a sobreposição em particionamentos com tamanhos de partição desiguais para Nadeau-Bengio |
| Regime `CV_AND_HOLDOUT` | $J = \text{len}(plan.folds)$ restrito estritamente às dobras de desenvolvimento; holdout isolado em escopo `FINAL_HOLDOUT` | Evita que a partição de teste final seja agregada erroneamente como dobra adicional de validação cruzada |
| Avaliação em `HOLDOUT_ONLY` ($J=1$) | Testes multi-fold (Nadeau-Bengio e Wilcoxon inter-dobras) são declarados `NOT_SUITABLE`; não sugere pooled OOF | Reflete a impossibilidade matemática de testes inter-dobras para partição única sem confundir escopos |
| Alerta amostral do teste de Wilcoxon ($J < 6$) | Emitido como alerta de impossibilidade matemática de rejeição bicaudal a $\alpha=0.05$ (p-valor mínimo $0.0625$); esclarece que $J \ge 6$ não garante poder adequado | Evita falsas expectativas metodológicas e prepara a distinção com $n_{\text{effective}}$ de M6.2 |
| Estabilidade de seleção de atributos | Reutiliza `SelectionStabilityReport` de M3.3; Jaccard = 1.0 para vazios mútuos, 0.0 para vazio unilateral, `None` se $J_{\text{completed}} < 2$ | Garante total consistência matemática com `compute_selection_stability` já aprovado no Marco M3 |
| Política para comparações incompletas (`IncompleteComparisonPolicy`) | Enum com modos `STRICT_COMPLETE_ONLY` e `ALLOW_COMMON_SUBSET` | Garante que análises parciais sejam explicitamente opt-in pelo pesquisador e sempre rotuladas como condicionais (`RF5.3`) |

## User Stories

### US-M61-01 (Priority: P1) — Estruturas Imutáveis de Consolidação Descritiva e Adequação
As an experimental ML researcher,  
I want immutable, typed data structures for descriptive statistics, coverage tracking, and methodological suitability,  
So that statistical consolidations, failure tracking, and methodological recommendations are transparent, immutable, and auditable.

#### Acceptance Criteria
- **AC-M61-01-01**: The system SHALL provide an enumeration `CoverageStatus` containing the values `VALID` ($C = 1.0$), `PARTIAL_COVERAGE` ($0.0 < C < 1.0$), and `NO_COVERAGE` ($C = 0.0$).
- **AC-M61-01-02**: The system SHALL provide an enumeration `IncompleteComparisonPolicy` containing the values `STRICT_COMPLETE_ONLY` and `ALLOW_COMMON_SUBSET`.
- **AC-M61-01-03**: The system SHALL provide frozen dataclasses `AggregatedMetricStats` containing `n_valid: int`, `n_total: int`, `status: MetricStatus`, `mean: float | None`, `std: float | None`, `median: float | None`, `iqr: float | None`, `q25: float | None`, `q75: float | None`, `min_value: float | None`, and `max_value: float | None`.
- **AC-M61-01-04**: The system SHALL provide frozen dataclasses `AggregatedTimingStats` containing mean and total durations in seconds for all cell phases (`data_extraction`, `preprocessing`, `feature_selection`, `tuning`, `fit`, `predict`, `evaluation`, and `total_cell`).
- **AC-M61-01-05**: The system SHALL provide a frozen dataclass `ConfigurationSummary` containing `model_id: str`, `scenario_id: str`, `total_folds: int`, `completed_folds: int`, `failed_folds: int`, `cancelled_folds: int`, `coverage: float`, `coverage_status: CoverageStatus`, `completed_fold_ids: tuple[str, ...]`, `failed_fold_ids: tuple[str, ...]`, `cancelled_fold_ids: tuple[str, ...]`, `fold_metrics: Mapping[str, Mapping[str, MetricValue]]`, `aggregated_metrics: Mapping[str, AggregatedMetricStats]`, `pooled_oof_metrics: Mapping[str, MetricValue]`, `aggregated_timing: AggregatedTimingStats | None`, and `feature_stability: SelectionStabilityReport | None`.
- **AC-M61-01-06**: The system SHALL provide a frozen dataclass `DescriptiveConsolidation` containing `experiment_id: str`, `partition_plan_id: str`, `total_configurations: int`, `configurations: Mapping[tuple[str, str], ConfigurationSummary]`, and `timestamp_utc: str`.
- **AC-M61-01-07**: When any attribute of `AggregatedMetricStats`, `AggregatedTimingStats`, `ConfigurationSummary`, or `DescriptiveConsolidation` is modified after instantiation, the system SHALL raise `FrozenInstanceError`.

---

### US-M61-02 (Priority: P1) — Validação de Transição da Etapa 4B para a Etapa 5
As an experimental ML researcher,  
I want strict validation of matrix execution completeness before entering Stage 5,  
So that incomplete or fully failed experiment matrices are blocked from advancing to statistical consolidation.

#### Acceptance Criteria
- **AC-M61-02-01**: IF `execution_state.json` is missing or cannot be parsed, THEN the system SHALL raise `ContractViolationError` blocking entry into Stage 5.
- **AC-M61-02-02**: IF `execution_state.json` contains any cell in non-terminal states (`PENDING` or `RUNNING`), THEN the system SHALL raise `ContractViolationError` with a clear message indicating execution is in progress and must be completed or resumed before Stage 5.
- **AC-M61-02-03**: IF `execution_state.json` reports `completed_cells == 0`, THEN the system SHALL raise `ContractViolationError` indicating that no successful cell results exist for consolidation.
- **AC-M61-02-04**: WHEN all cells in `execution_state.json` are in terminal states (`COMPLETED`, `FAILED`, or `CANCELLED`) and `completed_cells >= 1`, THEN the system SHALL permit execution of descriptive consolidation (Submodule 5A).

---

### US-M61-03 (Priority: P1) — Consolidação Descritiva e Rastreamento de Cobertura
As an experimental ML researcher,  
I want a pure functional aggregator that consolidates metrics and computational timings across cells for each configuration,  
So that predictive performance and computational costs are summarized descriptively with explicit coverage metrics and no data loss.

#### Acceptance Criteria
- **AC-M61-03-01**: WHEN invoking `consolidate_descriptive` with cell results and optional OOF predictions, the system SHALL group results by unique `(model_id, scenario_id)` configuration.
- **AC-M61-03-02**: The system SHALL compute configuration coverage as $C = \text{completed\_folds} / \text{total\_folds}$, assigning `CoverageStatus.VALID` when $C = 1.0$, `CoverageStatus.PARTIAL_COVERAGE` when $0.0 < C < 1.0$, and `CoverageStatus.NO_COVERAGE` when $C = 0.0$.
- **AC-M61-03-03**: IF one or more folds for a configuration have status `FAILED` or `CANCELLED`, THEN the system SHALL record their `fold_id` in `failed_fold_ids` and `cancelled_fold_ids` respectively, without coercing missing metrics to zero.
- **AC-M61-03-04**: WHEN computing `AggregatedMetricStats` for $n_{\text{valid}} \ge 2$ valid fold values, the system SHALL compute sample mean, sample standard deviation with `ddof=1`, median, IQR ($Q_{75} - Q_{25}$), min, and max using NumPy, setting `status = MetricStatus.VALID` if $n_{\text{valid}} == n_{\text{total}}$ and `MetricStatus.PARTIAL_COVERAGE` if $n_{\text{valid}} < n_{\text{total}}$.
- **AC-M61-03-05**: WHEN computing `AggregatedMetricStats` for $n_{\text{valid}} = 1$ valid fold value, the system SHALL compute mean, median, min, max, and IQR ($0.0$), but SHALL set `std = None`, preserving mathematical rigor without fabricating zero variance.
- **AC-M61-03-06**: WHEN computing `AggregatedMetricStats` for $n_{\text{valid}} = 0$ valid fold values, the system SHALL set all numerical summary fields (`mean`, `std`, `median`, `iqr`, `q25`, `q75`, `min_value`, `max_value`) to `None`, and set `status = MetricStatus.UNDEFINED_NAN`.
- **AC-M61-03-07**: WHERE consolidated OOF prediction records are available for a configuration, the system SHALL incorporate the global `pooled_oof_metrics` directly into `ConfigurationSummary`.
- **AC-M61-03-08**: WHEN aggregating timing breakdown across completed folds, the system SHALL compute the mean and sum for every cell sub-phase into `AggregatedTimingStats`, or set `aggregated_timing = None` when completed folds equal zero.
- **AC-M61-03-09**: WHERE dynamic feature selection results are present across completed folds with $J_{\text{completed}} \ge 2$, the system SHALL compute pairwise stability using `compute_selection_stability`, assigning Jaccard similarity of 1.0 when both sets are empty, 0.0 when exactly one set is empty, and returning `None` when $J_{\text{completed}} < 2$.

---

### US-M61-04 (Priority: P1) — Avaliação de Adequação Metodológica e Incompletude
As an experimental ML researcher,  
I want automated evaluation of statistical method suitability based on the experimental design and data structure,  
So that recommended hypothesis tests respect cross-validation dependencies, sample size limits, and fold pairing constraints.

#### Acceptance Criteria
- **AC-M61-04-01**: WHEN invoking `evaluate_method_suitability` with a `PartitionPlan` and `DescriptiveConsolidation`, the system SHALL extract the evaluation regime (`CV_ONLY`, `HOLDOUT_ONLY`, or `CV_AND_HOLDOUT`), total development partitions $J = \text{len}(plan.folds)$, fold-level ratios $r_j = n_{\text{val}, j} / n_{\text{train}, j}$, and mean representative ratio $r = \frac{1}{J} \sum_{j=1}^J r_j$.
- **AC-M61-04-02**: IF the evaluation regime is `CV_ONLY` or `CV_AND_HOLDOUT` with $J \ge 2$, THEN the system SHALL declare the corrected Nadeau-Bengio paired $t$-test and the paired Wilcoxon signed-rank test as applicable methods for development cross-validation comparisons.
- **AC-M61-04-03**: WHILE evaluating cross-validation designs, the system SHALL explicitly flag the uncorrected standard paired $t$-test as NOT SUITABLE due to violation of the independent observations assumption induced by overlapping training folds.
- **AC-M61-04-04**: IF the evaluation regime is `HOLDOUT_ONLY` ($J = 1$), THEN the system SHALL reject multi-fold paired tests (Nadeau-Bengio and fold-level Wilcoxon) as NOT SUITABLE due to absence of variance across partitions, and SHALL NOT recommend pooled out-of-fold comparisons.
- **AC-M61-04-05**: IF $J < 6$ (or paired valid folds $J_{\text{pareados}} < 6$) for paired Wilcoxon evaluation, THEN the system SHALL attach a methodological warning indicating mathematical inability to attain two-sided significance at $\alpha = 0.05$ (minimum exact p-value is $0.0625$), while noting that $J \ge 6$ does not guarantee adequate statistical power.
- **AC-M61-04-06**: WHERE the evaluation regime is `CV_AND_HOLDOUT`, the system SHALL isolate the holdout partition in `plan.holdout_ids`, ensuring that $J$ refers exclusively to development folds and holdout metrics remain in scope `FINAL_HOLDOUT`.
- **AC-M61-04-07**: WHEN comparing two configurations under `IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY`, IF either configuration has `coverage_status != CoverageStatus.VALID`, THEN the system SHALL declare pairwise statistical comparison NOT APPLICABLE.
- **AC-M61-04-08**: WHEN comparing two configurations under `IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET`, IF the number of shared valid folds satisfies $J_{\text{pareados}} \ge 2$, THEN the system SHALL permit comparison restricted to the intersection of folds, flagging the result with a mandatory conditional analysis caveat and warning of potential attrition bias.
- **AC-M61-04-09**: IF the number of shared valid folds satisfies $J_{\text{pareados}} < 2$, THEN the system SHALL declare pairwise statistical comparison NOT APPLICABLE regardless of the incompleteness policy.

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| STAT-01 | AC-M61-01-01, AC-M61-01-02, AC-M61-01-03, AC-M61-01-04, AC-M61-01-05, AC-M61-01-06, AC-M61-01-07 | `experimental_ml.statistics.consolidation` | pending |
| STAT-02 | AC-M61-02-01, AC-M61-02-02, AC-M61-02-03, AC-M61-02-04 | `experimental_ml.statistics.consolidation` | pending |
| STAT-03 | AC-M61-03-01, AC-M61-03-02, AC-M61-03-03, AC-M61-03-04, AC-M61-03-05, AC-M61-03-06, AC-M61-03-07, AC-M61-03-08, AC-M61-03-09 | `experimental_ml.statistics.consolidation` | pending |
| STAT-04 | AC-M61-04-01, AC-M61-04-02, AC-M61-04-03, AC-M61-04-04, AC-M61-04-05, AC-M61-04-06, AC-M61-04-07, AC-M61-04-08, AC-M61-04-09 | `experimental_ml.statistics.suitability` | pending |
