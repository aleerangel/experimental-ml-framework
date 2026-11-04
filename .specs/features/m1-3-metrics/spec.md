# m1-3-metrics Specification

**Approved**: 2026-11-03 - user: "aprovado. commita"

## Problem Statement

O `experimental-ml-framework` necessita de um motor transversal de métricas (`experimental_ml.metrics`, Nível 1 da arquitetura) que execute avaliações determinísticas e vetorizadas em dupla precisão (`float64`) para tarefas de regressão, alinhamento de matrizes de kernel e classificação discreta ou probabilística. Sem esse módulo, as etapas de seleção de atributos (`features`), busca de hiperparâmetros (`tuning`), execução matricial (`orchestration`) e comparação estatística (`statistics`) não dispõem de funções puras padronizadas nem de tratamento explícito para divisões degeneradas (`MetricStatus.UNDEFINED_NAN`), correndo o risco de coerções silenciosas para zero, overflow numérico, ambiguidade em classificação multiclasse ou seleção indevida de candidatos inválidos.

## Goals

- [ ] Definir as estruturas de dados imutáveis de avaliação e metadados (`MetricValue`, `AggregatedMetricValue`, `MetricSpec`, `RankedCandidate`) e o enum fechado de escopo de avaliação `MetricEvaluationScope`.
- [ ] Disponibilizar o catálogo modular `METRICS_CATALOG` e funções de consulta (`get_metric_spec`, `compute_metric`, `list_metrics`) mapeando as 15 métricas do MVP às suas funções puras, direções de otimização (`MetricDirection`), flag de comparação por magnitude absoluta (`compare_by_abs`), modalidades de tarefa (`TaskType`) e tolerâncias numéricas de referência (`rtol`, `atol`).
- [ ] Implementar as 3 métricas vetorizadas de erro em escala direta para regressão (`mae`, `rmse`, `mbe`) com estabilização contra overflow quadrático, preservação do sinal em `mbe` e comparação por magnitude absoluta $|\text{MBE}|$ (`rtol=1e-12`, `atol=1e-12`).
- [ ] Implementar as 5 métricas vetorizadas de razão adimensional e alinhamento (`r2`, `rmse_rel_pct`, `mape`, `pearson`, `kta`) com convenção explícita de centralização em `kta` (`centered: bool = False`), tratamento de amostras insuficientes ($n < 2$), variância nula e alvos iguais a zero (`MetricStatus.UNDEFINED_NAN`, `rtol=1e-10`, `atol=1e-12`).
- [ ] Implementar as 5 métricas vetorizadas de proporção discreta para classificação binária e multiclasse (`accuracy`, `balanced_accuracy`, `precision`, `recall`, `f1`), especificando individualmente as condições de indefinição por classe e proibindo coerção silenciosa para `0.0` (`rtol=1e-14`, `atol=1e-15`).
- [ ] Implementar as 2 métricas probabilísticas e de ranqueamento para classificação (`roc_auc`, `log_loss`) com tratamento determinístico de empates por postos médios, suporte multiclasse OVR, mapeamento explícito entre colunas e classes, clipping $\epsilon = 10^{-15}$ e validação de distribuições (`rtol=1e-9`, `atol=1e-11`).
- [ ] Implementar as funções de propagação, comparação e agregação de métricas (`is_better`, `aggregate_fold_metrics`, `rank_configurations`) em conformidade com o **ADR-005**, com ordenação lexicográfica estrita entre `VALID`, `PARTIAL_COVERAGE` e `UNRANKABLE`.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Testes inferenciais pareados (Nadeau-Bengio, Wilcoxon) e correções de multiplicidade (Holm, Benjamini-Hochberg) | Pertencem ao Marco M6 (`experimental_ml.statistics`). |
| Fronteira de Pareto e funções de aquisição sequencial (`EI`, `UCB`/`LCB`) | Pertencem ao Marco M6 (`experimental_ml.statistics`). |
| Ingestão de dados tabulares, perfilamento e planos de partição | Pertencem ao Marco M2 (`experimental_ml.data` e `experimental_ml.validation`). |
| Subcomandos da CLI para execução e consolidação estatística (`expml run`, `expml stats`) | Pertencem aos Marcos M5 e M6 (`experimental_ml.cli`). |
| Classes de serviço com estado interno mutável | Vedação arquitetural permanente do projeto (**ADR-008**). |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Dependências numéricas | Utilizar exclusivamente `numpy>=1.24.0` e a biblioteca padrão do Python | `numpy` já integra `pyproject.toml` desde o M1.2 e suporta todas as 15 métricas vetorizadas em `float64` sem dependências externas adicionais. | y |
| Semântica de sinal e comparação do `MBE` (Viés Médio) | `mbe` retorna o valor assinado $\frac{1}{n}\sum (\hat{y}_i - y_i) \in \mathbb{R}$, registra `direction = MetricDirection.MINIMIZE` e `compare_by_abs = True` em `MetricSpec`; `is_better` e `rank_configurations` comparam $\|\text{MBE}\|$ | Preserva o sinal para diagnóstico de superestimação/subestimação e agregação entre dobras, enquanto a seleção de modelos minimiza a distância ao viés nulo $\|\text{MBE}\| \to 0.0$ (Willmott, 1982). | y |
| Contrato fechado de escopo (`MetricEvaluationScope` e `AggregationScope`) | Definir `MetricEvaluationScope(StrEnum)` com `PER_FOLD`, `FOLD_AGGREGATION`, `POOLED_OOF`, `FINAL_HOLDOUT` e validar estritamente `scope` contra `MetricEvaluationScope` e `AggregationScope`, rejeitando strings arbitrárias com `ConfigurationError` | Elimina strings não validadas, atende aos escopos do `RF4.7` e preserva inalterado o contrato `len(AggregationScope) == 3` de `experimental_ml.core.enums` (M1.2). | y |
| Ordenação formal entre `VALID`, `PARTIAL_COVERAGE` e `UNDEFINED_NAN` | Chave lexicográfica: (1) status `VALID` precede `PARTIAL_COVERAGE`; (2) maior `coverage` ($k/K$) precede menor cobertura; (3) valor direcionado da métrica; (4) `candidate_id` crescente; `UNDEFINED_NAN` recebe `UNRANKABLE` (`rank=None`) ao final | Evita viés de sobrevivência (*survivorship bias*) de configurações avaliadas em subconjuntos parciais de dobras (**ADR-005**, `CA-E5-01`). | y |
| Convenção de centralização no `KTA` (*Kernel Target Alignment*) | Fórmula de alinhamento de Frobenius com parâmetro explícito `centered: bool = False` (padrão não centralizado de Cristianini et al., 2001; opção `centered=True` aplicando $H K H$ conforme Cortes et al., 2012) | Mantém correspondência direta com a condição $\|K\|_F = 0$ da Seção 7.1 de `ARQUITETURA_E_CONTRATOS.md` no padrão e suporta centralização no espaço de atributos. | y |
| Tratamento de empates e OVR no `ROC_AUC` | Cálculo exato via postos médios (estatística de Mann-Whitney $U$ / integração trapezoidal nos limiares únicos) no caso binário, e média One-vs-Rest (`macro` ou `weighted`) no caso multiclasse | Assegura invariância à ordem das observações em escores empatados (retornando `0.5` para escores constantes) e equivalência exata com a área sob a curva ROC empírica (Hanley & McNeil, 1982; Hand & Till, 2001). | y |
| Estabilidade numérica e prevenção de overflow | Reescalonamento analítico pelo máximo absoluto antes de somas quadráticas (`rmse`, `r2`, `pearson`, `kta`) e conversão de qualquer resultado não finito residual (`±Inf`, `NaN`) em `MetricStatus.UNDEFINED_NAN` com `Finding` | Garante a invariante de que todo `MetricValue` com `status == VALID` possui `math.isfinite(value) == True` (Higham, 2002; IEEE 754). | y |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Estruturas Imutáveis, Escopos Fechados e Catálogo `METRICS_CATALOG` ⭐ MVP

**User Story**: Como desenvolvedor de módulos do framework, quero estruturas de dados imutáveis (`MetricValue`, `AggregatedMetricValue`, `MetricSpec`, `RankedCandidate`), uma enumeração fechada de escopos (`MetricEvaluationScope`) e um catálogo centralizado (`METRICS_CATALOG`), para consultar metadados e executar métricas sem risco de mutação ou escopos arbitrários.

**Why P1**: Todas as etapas consumidoras (`features`, `tuning`, `orchestration`, `statistics`) dependem dessas estruturas e do catálogo para invocar métricas e inspecionar seus estados.

**Acceptance Criteria**:

1. The system SHALL provide frozen, immutable data structures `MetricValue`, `AggregatedMetricValue`, `MetricSpec`, and `RankedCandidate` in `experimental_ml.metrics`.
2. The system SHALL define `MetricEvaluationScope(StrEnum)` with canonical members `"PER_FOLD"`, `"FOLD_AGGREGATION"`, `"POOLED_OOF"`, and `"FINAL_HOLDOUT"`, validating that `MetricValue.scope` accepts only members of `MetricEvaluationScope` or `AggregationScope` (or their exact canonical strings coerced to enum instances) and that `AggregatedMetricValue.scope` accepts only aggregation scopes (`FOLD_AGGREGATION`, `REPETITION_AGGREGATION`, `OVERALL_AGGREGATION`), raising `ConfigurationError` for any arbitrary string or invalid scope.
3. The system SHALL ensure that `MetricSpec` records `metric_id: str`, `name: str`, `family: str`, `direction: MetricDirection`, `compare_by_abs: bool`, `supported_tasks: tuple[TaskType, ...]`, `func: Callable`, `rtol: float`, `atol: float`, `requires_probabilities: bool`, and `requires_kernel_matrix: bool`, where `compare_by_abs` is `True` for `"mbe"` and `False` for the remaining 14 metrics.
4. The system SHALL expose `METRICS_CATALOG` mapping all 15 canonical metric identifiers (`"mae"`, `"rmse"`, `"mbe"`, `"r2"`, `"rmse_rel_pct"`, `"mape"`, `"pearson"`, `"kta"`, `"accuracy"`, `"balanced_accuracy"`, `"precision"`, `"recall"`, `"f1"`, `"roc_auc"`, `"log_loss"`) to their corresponding `MetricSpec` instances.
5. WHEN `compute_metric(metric_id, y_true, y_pred_or_score, **kwargs)` or `get_metric_spec(metric_id)` is called with a registered identifier (case-insensitive), THEN the system SHALL resolve the canonical metric specification and return a `MetricValue` or `MetricSpec`.
6. IF an unregistered `metric_id` is passed to `get_metric_spec` or `compute_metric`, THEN the system SHALL raise a `ConfigurationError`.

**Independent Test**: Inspecionar `METRICS_CATALOG` confirmando a presença das 15 métricas e `compare_by_abs=True` em `"mbe"`, verificar a imutabilidade das estruturas e comprovar que escopos ou identificadores desconhecidos disparam `ConfigurationError`.

---

### P1: Validação Estrita de Entradas e Estabilidade Numérica (`float64`) ⭐ MVP

**User Story**: Como pesquisador, quero que todas as funções de métricas validem dimensões, comprimentos amostrais e finitude das entradas e apliquem estabilização numérica contra overflow intermediário, para garantir que resultados `VALID` sejam sempre números finitos em `float64`.

**Why P1**: Exigência direta dos requisitos de integridade `CA-COND-REG-01`, `CA-COND-CLAS-01`, `CA-GER-03` e RNF07.

**Acceptance Criteria**:

1. WHEN any metric function receives input arrays, THEN the system SHALL convert valid numeric sequences to `numpy.ndarray` of dtype `float64` without mutating the caller's original arrays.
2. IF `y_true` and `y_pred` (or `y_score` along its first axis) have different sample lengths, or if the sample count is zero ($n = 0$), THEN the system SHALL raise a `DataIntegrityError`.
3. IF `y_true`, `y_pred`, or `y_score` contains `NaN`, `+Inf`, or `-Inf` values in input observations, THEN the system SHALL raise a `DataIntegrityError`.
4. The system SHALL apply analytical scaling stabilization before squaring residuals or deviations in `rmse`, `r2`, `pearson`, and `kta`, preventing intermediate floating-point overflow when input differences are finite but exceed $\sqrt{\text{float64.max}} \approx 1.34 \times 10^{154}$.
5. IF an intermediate or final metric computation overflows `float64` or produces a non-finite value (`+Inf`, `-Inf`, or `NaN`) from finite inputs, THEN the system SHALL return a `MetricValue` with `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN`, and a heuristic warning `Finding` (`code="W_METRIC_NUMERICAL_OVERFLOW"`), ensuring that every `MetricValue` with `status == MetricStatus.VALID` has `math.isfinite(value) == True`.

**Independent Test**: Invocar métricas com arrays vazios, comprimentos distintos e entradas contendo `np.nan`/`np.inf` (verificando `DataIntegrityError`), testar vetores de magnitude $10^{200}$ em `rmse`, `r2`, `pearson` e `kta` (verificando ausência de overflow quadrático), e testar diferenças que excedam `float64.max` (verificando retorno `UNDEFINED_NAN` com `Finding`).

---

### P1: Métricas de Regressão de Erro em Escala Direta (`MAE`, `RMSE`, `MBE`) ⭐ MVP

**User Story**: Como pesquisador avaliando modelos de regressão, quero calcular `MAE`, `RMSE` e `MBE` (Viés Médio) em ponto flutuante de dupla precisão, preservando o sinal algébrico do `MBE` no valor reportado e comparando-o por magnitude absoluta $|\text{MBE}|$.

**Why P1**: Constituem as métricas primárias de erro em unidades da variável-alvo (`ARQUITETURA_E_CONTRATOS.md` Seção 7.1).

**Acceptance Criteria**:

1. The system SHALL implement vectorized functions `mae(y_true, y_pred)`, `rmse(y_true, y_pred)`, and `mbe(y_true, y_pred)` operating in `float64` precision with reference accuracy within `rtol=1e-12` and `atol=1e-12`.
2. The system SHALL compute `mbe(y_true, y_pred)` as the signed arithmetic mean $\frac{1}{n}\sum_{i=1}^n (\hat{y}_i - y_i)$, returning a negative `MetricValue.value` when $\hat{y}$ underestimates $y$ on average and a positive `MetricValue.value` when $\hat{y}$ overestimates $y$ on average, while registering `direction = MetricDirection.MINIMIZE` and `compare_by_abs = True` in `METRICS_CATALOG["mbe"]`.
3. WHEN `y_pred` equals `y_true` element-wise, THEN `mae`, `rmse`, and `mbe` SHALL return `MetricValue` with `value == 0.0` and `status == MetricStatus.VALID`.
4. WHEN inputs are scaled by a non-zero scalar constant $c$, THEN `rmse(c * y_true, c * y_pred)` SHALL equal $|c| \cdot \text{rmse}(y_true, y_pred)$ within `rtol=1e-12` and `atol=0.0`, without integer rounding or `math.ceil` truncation.

**Independent Test**: Avaliar `mae`, `rmse` e `mbe` sobre vetores analíticos conhecidos (verificando preservação do sinal negativo e positivo em `mbe.value`), verificar erro zero para $\hat{y} = y$ e comprovar a homocedasticidade de escala $\text{RMSE}(c y, c \hat{y}) = |c| \text{RMSE}(y, \hat{y})$.

---

### P1: Métricas de Razão Adimensional e Alinhamento (`R2`, `RMSE_rel_pct`, `MAPE`, `Pearson`, `KTA`) ⭐ MVP

**User Story**: Como pesquisador avaliando qualidade de ajuste adimensional e alinhamento de kernels, quero calcular `R2`, `RMSE_rel_pct`, `MAPE`, `Pearson` e `KTA` com regras explícitas para amostras insuficientes ($n < 2$), variância nula, alvos zero ($y_i = 0$) e centralização opcional de matrizes de Gram.

**Why P1**: Garante o cumprimento de `CA-GER-03`, `CA-COND-REG-01`, `CA-COND-MOD-02` e **ADR-005** para métricas baseadas em razões e produtos internos de Frobenius.

**Acceptance Criteria**:

1. The system SHALL implement vectorized functions `r2(y_true, y_pred)`, `rmse_rel_pct(y_true, y_pred)`, `mape(y_true, y_pred)`, `pearson(y_true, y_pred)`, and `kta(k_true, k_pred, *, centered=False)` operating in `float64` with reference accuracy within `rtol=1e-10` and `atol=1e-12`.
2. WHEN `y_pred` equals `y_true` with $n \ge 2$, non-zero variance, and non-zero target values, THEN `r2`, `pearson`, and `kta` SHALL return `1.0` and `rmse_rel_pct` and `mape` SHALL return `0.0` with `status == MetricStatus.VALID`; WHEN `y_pred` is constant and equal to $\bar{y}$ for `y_true` with non-zero variance ($n \ge 2$), THEN `r2` SHALL return `0.0` with `status == MetricStatus.VALID`.
3. IF the sample size is $n < 2$ ($n = 1$) or if `y_true` has zero variance ($\sum_{i=1}^n (y_i - \bar{y})^2 = 0$), THEN `r2` and `pearson` SHALL return `MetricValue` with `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN`, and a heuristic warning `Finding` distinguishing `W_METRIC_INSUFFICIENT_SAMPLES` ($n < 2$) from `W_METRIC_ZERO_VARIANCE` ($SS_{\text{tot}} = 0$), never coercing $0/0$ to `1.0` or `0.0`.
4. IF `y_pred` has zero variance ($\sum_{i=1}^n (\hat{y}_i - \bar{\hat{y}})^2 = 0$), THEN `pearson` SHALL return `MetricValue` with `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN`, and a heuristic warning `Finding`.
5. IF the sample mean of `y_true` is zero ($|\bar{y}| = 0$), THEN `rmse_rel_pct` SHALL return `MetricValue` with `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN`, and a heuristic warning `Finding`.
6. IF any observation in `y_true` equals zero ($y_i == 0.0$, whether $\hat{y}_i = 0$ or $\hat{y}_i \neq 0$), THEN `mape` SHALL return `MetricValue` with `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN`, and a heuristic warning `Finding` (`code="W_METRIC_ZERO_TARGET"`, recording `n_zero_targets` in `context`), without dropping zero-target observations or adding an arbitrary $\epsilon$ to the denominator.
7. WHEN `kta(k_true, k_pred, *, centered=False)` is called, THEN the system SHALL convert 1D vectors $v \in \mathbb{R}^n$ to outer-product Gram matrices $v v^T \in \mathbb{R}^{n \times n}$, apply double-centering $\tilde{K} = H K H$ with $H = I_n - \frac{1}{n}\mathbf{1}\mathbf{1}^T$ when `centered=True` (keeping $\tilde{K} = K$ when `centered=False`), and compute $\frac{\langle \tilde{K}_{\text{true}}, \tilde{K}_{\text{pred}} \rangle_F}{\|\tilde{K}_{\text{true}}\|_F \|\tilde{K}_{\text{pred}}\|_F}$; IF $\|\tilde{K}_{\text{true}}\|_F = 0$ or $\|\tilde{K}_{\text{pred}}\|_F = 0$, THEN `kta` SHALL return `MetricValue` with `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN`, and a heuristic warning `Finding`.

**Independent Test**: Testar casos analíticos regulares ($R^2=1$, $R^2=0$, $\text{Pearson}=\pm 1$, $\text{KTA}$ com `centered=False` e `centered=True`) e todos os casos degenerados ($n=1$, variância zero em $y$ e $\hat{y}$, média zero, $y_i=0$ em `mape`, matriz nula ou constante em `kta`), verificando `isnan(result.value)`, `status == MetricStatus.UNDEFINED_NAN` e presença de `Finding`.

---

### P1: Métricas de Classificação Discreta Binária e Multiclasse (`Accuracy`, `Balanced_Accuracy`, `Precision`, `Recall`, `F1`) ⭐ MVP

**User Story**: Como pesquisador avaliando classificadores binários e multiclasse, quero regras individuais e verificáveis para `Accuracy`, `Balanced_Accuracy`, `Precision`, `Recall` e `F1` diante de classes ausentes e classes sem predições positivas, impedindo coerções silenciosas para zero.

**Why P1**: Exigência expressa da Seção 7.1 de `ARQUITETURA_E_CONTRATOS.md`, `CA-COND-CLAS-01` e **ADR-005**.

**Acceptance Criteria**:

1. The system SHALL implement vectorized functions `accuracy(y_true, y_pred)`, `balanced_accuracy(y_true, y_pred, *, labels=None)`, `precision(y_true, y_pred, *, average="binary", pos_label=1.0, labels=None)`, `recall(y_true, y_pred, *, average="binary", pos_label=1.0, labels=None)`, and `f1(y_true, y_pred, *, average="binary", pos_label=1.0, labels=None)` with reference accuracy within `rtol=1e-14` and `atol=1e-15`.
2. The system SHALL determine the evaluated class set $\mathcal{C}$ as $\{\text{pos\_label}\}$ when `average="binary"`, as $\text{unique}(\text{labels})$ when `labels` is provided, as $\text{unique}(y_{\text{true}}) \cup \text{unique}(y_{\text{pred}})$ for `precision`, `recall`, and `f1` when `average in ("macro", "weighted")` and `labels=None`, and as $\text{unique}(y_{\text{true}}) \cup \text{unique}(y_{\text{pred}})$ for `balanced_accuracy` when `labels=None`.
3. IF any evaluated class $c \in \mathcal{C}$ in `precision` has zero positive predictions ($TP_c + FP_c = 0$), THEN `precision` SHALL return `MetricValue` with `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN`, and a heuristic warning `Finding` identifying the undefined class(es) in `context`, never coercing $0/0$ to `0.0`; WHEN $TP_c = 0$ and $FP_c > 0$ (with $TP_c + FP_c > 0$ for all $c \in \mathcal{C}$ and $\sum_{c \in \mathcal{C}} (TP_c + FN_c) > 0$), THEN $\text{Precision}_c = 0.0$ SHALL be treated as a valid `0.0`.
4. IF any evaluated class $c \in \mathcal{C}$ in `recall` has zero true instances ($TP_c + FN_c = 0$, such as an absent `pos_label`, a class predicted in `y_pred` that does not exist in `y_true`, or an absent class in `labels`), THEN `recall` SHALL return `MetricValue` with `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN`, and a heuristic warning `Finding`; WHEN all $c \in \mathcal{C}$ have $TP_c + FN_c > 0$ and a class has $TP_c + FP_c = 0$ (so $TP_c = 0$), THEN $\text{Recall}_c = 0 / (TP_c + FN_c) = 0.0$ SHALL be treated as a valid `0.0` (`MetricStatus.VALID`).
5. IF any evaluated class $c \in \mathcal{C}$ in `f1` has either zero positive predictions ($TP_c + FP_c = 0$, making $\text{Precision}_c$ undefined) OR zero true instances ($TP_c + FN_c = 0$, making $\text{Recall}_c$ undefined), THEN `f1` SHALL propagate `MetricStatus.UNDEFINED_NAN` with `value = float("nan")` and a heuristic warning `Finding`; WHEN every $c \in \mathcal{C}$ has both $TP_c + FP_c > 0$ and $TP_c + FN_c > 0$ (even if $TP_c = 0$, where $\text{Precision}_c = 0.0$ and $\text{Recall}_c = 0.0$ are both validly defined), THEN $\text{F1}_c$ SHALL evaluate to `0.0` with `status == MetricStatus.VALID`.
6. IF `balanced_accuracy` is evaluated on fewer than 2 classes ($|\mathcal{C}| < 2$, e.g., monoclass `y_true` and `y_pred`) or if any class $c \in \mathcal{C}$ has zero true instances ($TP_c + FN_c = 0$), THEN `balanced_accuracy` SHALL return `MetricValue` with `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN`, and a heuristic warning `Finding`.

**Independent Test**: Testar matrizes de confusão binárias e multiclasse (`macro` e `weighted`) cobrindo individualmente: (a) $TP_c + FP_c = 0$ com $TP_c + FN_c > 0$ (`precision` e `f1` $\rightarrow$ `UNDEFINED_NAN`, `recall` e `balanced_accuracy` $\rightarrow$ `VALID`); (b) $TP_c + FN_c = 0$ com $FP_c > 0$ (`recall`, `f1` e `balanced_accuracy` $\rightarrow$ `UNDEFINED_NAN`, `precision` $\rightarrow$ `VALID`); e (c) $TP_c = 0$ com $FP_c > 0$ e $FN_c > 0$ (todas $\rightarrow$ `VALID` com valor `0.0`).

---

### P1: Métricas Probabilísticas e de Ranqueamento (`ROC_AUC`, `Log_Loss`) ⭐ MVP

**User Story**: Como pesquisador avaliando probabilidades e escores contínuos em classificação, quero contratos formais para `ROC_AUC` (empates via postos médios, formatos 1D/2D e multiclasse OVR) e `Log_Loss` (mapeamento coluna-classe, validação de axiomas de probabilidade e clipping $\epsilon = 10^{-15}$).

**Why P1**: Atende aos requisitos de classificação probabilística `CA-COND-CLAS-01` e Seção 7.1 de `ARQUITETURA_E_CONTRATOS.md`.

**Acceptance Criteria**:

1. The system SHALL implement vectorized functions `roc_auc(y_true, y_score, *, average="macro", labels=None)` and `log_loss(y_true, y_prob, *, eps=1e-15, labels=None)` operating in `float64` with reference accuracy within `rtol=1e-9` and `atol=1e-11`.
2. WHEN computing binary `roc_auc` ($|\mathcal{C}| = 2$, accepting a 1D score array of shape $(n,)$, a 2D single-column array $(n, 1)$ for $\mathcal{C}[1]$, or a 2D two-column array $(n, 2)$ where column `1` corresponds to $\mathcal{C}[1]$), THEN the system SHALL compute the exact area under the ROC curve handling tied scores via mid-ranks (Mann-Whitney $U$ statistic $\frac{1}{N_+ N_-}\sum_{i \in +} \sum_{j \in -} [\mathbb{I}(s_i > s_j) + 0.5\,\mathbb{I}(s_i = s_j)]$), returning `0.5` when all scores are tied.
3. WHEN computing multiclass One-vs-Rest `roc_auc` ($|\mathcal{C}| \ge 3$, requiring a 2D `y_score` matrix of shape $(n, K)$ where column $k$ maps to class $\mathcal{C}[k]$ in ascending order of `unique(y_true)` or in the order of `labels`), THEN the system SHALL compute binary OVR AUC for each class $c_k$ and aggregate via `average="macro"` (unweighted mean) or `average="weighted"` (weighted by true class support $N_{+, k} / n$).
4. IF `y_true` passed to `roc_auc` or `log_loss` contains fewer than 2 distinct classes, or if any class in `labels` has zero positive instances ($N_{+, k} = 0$) or zero negative instances ($N_{-, k} = 0$) in `roc_auc`, THEN the system SHALL return `MetricValue` with `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN`, and a heuristic warning `Finding`.
5. WHEN computing `log_loss`, THEN the system SHALL map a 1D array `y_prob` of shape $(n,)$ (or $(n, 1)$) in binary classification to $(P(Y = \mathcal{C}[0]) = 1 - p_i, P(Y = \mathcal{C}[1]) = p_i)$, and map column $k$ of a 2D matrix `y_prob` of shape $(n, K)$ to class $\mathcal{C}[k]$ (where $\mathcal{C}$ is `unique(y_true)` sorted ascending when `labels=None`, or `tuple(labels)` when `labels` is provided), clipping probabilities to $[\epsilon, 1 - \epsilon]$ with default $\epsilon = 10^{-15}$ and normalizing 2D clipped rows before computing $-\frac{1}{n}\sum_{i=1}^n \ln(\hat{p}_{i, y_i})$.
6. IF `y_prob` passed to `log_loss` contains values outside $[0.0, 1.0]$ (beyond tolerance `1e-12`), 2D probability rows whose sum deviates from `1.0` by more than `1e-6`, incompatible column count $K \neq |\mathcal{C}|$, 1D probabilities when $|\mathcal{C}| \ge 3$, or target values in `y_true` not present in `labels`, THEN the system SHALL raise a `DataIntegrityError`.

**Independent Test**: Avaliar `roc_auc` em binário (1D e 2D, separação perfeita $= 1.0$, inversa $= 0.0$, empates parciais e totais $= 0.5$) e multiclasse OVR (`macro` e `weighted`), avaliar `log_loss` em 1D e 2D com probabilidades extremas $\{0.0, 1.0\}$ e `labels` explícitos, testar `y_true` monoclasse retornando `UNDEFINED_NAN` e verificar que probabilidades fora de $[0, 1]$, somas $\neq 1$ ou número incorreto de colunas disparam `DataIntegrityError`.

---

### P1: Propagação, Comparação e Ranqueamento de `UNDEFINED_NAN` (**ADR-005**) ⭐ MVP

**User Story**: Como desenvolvedor dos módulos de otimização (`tuning`), orquestração (`orchestration`) e estatística (`statistics`), quero regras determinísticas para `is_better`, `aggregate_fold_metrics` e `rank_configurations` que respeitem o **ADR-005**, a comparação por magnitude absoluta do `MBE` e a precedência entre `VALID`, `PARTIAL_COVERAGE` e `UNRANKABLE`.

**Why P1**: Implementa diretamente o contrato transversal do **ADR-005** e o critério `CA-GER-03`.

**Acceptance Criteria**:

1. WHEN `is_better(cand_a, cand_b, direction=None)` compares two candidates where one is rankable (`MetricStatus.VALID` or `MetricStatus.PARTIAL_COVERAGE` with finite value) and the other has `status == MetricStatus.UNDEFINED_NAN` or `MetricStatus.UNRANKABLE` (or `NaN` value), THEN `is_better` SHALL always return `True` for the rankable candidate and `False` for the undefined candidate, regardless of whether `direction` is `MAXIMIZE` or `MINIMIZE`.
2. WHEN both candidates passed to `is_better` have `status == MetricStatus.UNDEFINED_NAN` (or `UNRANKABLE`), THEN `is_better` SHALL return `False`.
3. WHEN `is_better` compares two rankable candidates (`MetricValue` or `AggregatedMetricValue`), THEN a candidate with `status == MetricStatus.VALID` SHALL precede a candidate with `status == MetricStatus.PARTIAL_COVERAGE`, a higher `coverage` ratio SHALL precede a lower `coverage` ratio when both have `PARTIAL_COVERAGE`, and for equal status and coverage the candidate with better directed metric value SHALL win (using $|v_a| < |v_b|$ when `metric_id == "mbe"` / `compare_by_abs == True`, $v_a < v_b$ for `MINIMIZE`, and $v_a > v_b$ for `MAXIMIZE`).
4. WHEN `aggregate_fold_metrics(fold_values, *, scope=AggregationScope.FOLD_AGGREGATION)` aggregates a non-empty sequence of $K$ `MetricValue` items of the same `metric_id`, THEN the system SHALL compute `mean`, `std` (sample standard deviation with `ddof=1` for $k \ge 2$, `0.0` for $k = 1$), `median`, `iqr` (percentile 75 minus percentile 25), `valid_folds = k`, `total_folds = K`, and `coverage = k / K` over the $k$ valid finite folds.
5. WHEN all $K/K$ folds are `VALID`, THEN `aggregate_fold_metrics` SHALL return an `AggregatedMetricValue` with `status == MetricStatus.VALID` and `coverage == 1.0`.
6. WHEN $0 < k < K$ folds are `VALID`, THEN `aggregate_fold_metrics` SHALL compute summary statistics over the $k$ valid folds, set `status = MetricStatus.PARTIAL_COVERAGE`, set `coverage = k / K`, and attach a heuristic warning `Finding` (`code="W_METRIC_PARTIAL_COVERAGE"`).
7. WHEN $0/K$ folds are `VALID`, THEN `aggregate_fold_metrics` SHALL set `mean`, `std`, `median`, and `iqr` to `float("nan")`, set `status = MetricStatus.UNDEFINED_NAN`, set `coverage = 0.0`, and attach a heuristic warning `Finding` (`code="W_METRIC_ZERO_COVERAGE"`).
8. WHEN `rank_configurations(candidates, *, direction=None)` orders a mapping or sequence of candidate configurations, THEN the system SHALL sort rankable candidates (`VALID` and `PARTIAL_COVERAGE`) by the strict lexicographic key `(0 if status == VALID else 1, -coverage, directed_value, candidate_id)` attaching 1-based sequential integer ranks (`1, 2, ...`), and place all `UNDEFINED_NAN` candidates at the end ordered by `candidate_id` with `status = MetricStatus.UNRANKABLE` and `rank = None`.

**Independent Test**: Testar `is_better` (incluindo `mbe` com valores negativos e positivos, `VALID` vs `PARTIAL_COVERAGE` e `UNDEFINED_NAN`), testar `aggregate_fold_metrics` com $K/K$, $k/K$ e $0/K$, e testar `rank_configurations` comprovando a ordem lexicográfica `(VALID, PARTIAL_COVERAGE por coverage decrescente, UNRANKABLE com rank=None)`.

---

## Edge Cases

- IF input arrays are 2D column vectors of shape $(n, 1)$ in single-target metrics, THEN the system SHALL squeeze them to 1D $(n,)$ seamlessly; IF arrays have incompatible multidimensional shapes, THEN the system SHALL raise `DataIntegrityError`.
- IF a fold sequence with $k = 1$ valid fold is passed to `aggregate_fold_metrics`, THEN `std` and `iqr` SHALL be `0.0` while `mean` and `median` equal the single valid fold value.
- IF an empty sequence of folds or folds with mismatched `metric_id` are passed to `aggregate_fold_metrics`, THEN the system SHALL raise a `DataIntegrityError`.
- IF `average` in `precision`, `recall`, `f1`, or `roc_auc` is not one of the supported modes (`"binary"`, `"macro"`, `"weighted"`), or if `eps` in `log_loss` is not in $(0.0, 0.5)$, THEN the system SHALL raise a `ConfigurationError`.
- IF `average="binary"` is requested on a dataset with more than 2 distinct classes in `y_true` or `y_pred`, THEN the system SHALL raise a `DataIntegrityError`.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| MET-01 | P1: Estruturas Imutáveis, Escopos e Catálogo | Specify | pending |
| MET-02 | P1: Estruturas Imutáveis, Escopos e Catálogo | Specify | pending |
| MET-03 | P1: Estruturas Imutáveis, Escopos e Catálogo | Specify | pending |
| MET-04 | P1: Validação Estrita e Estabilidade Numérica | Specify | pending |
| MET-05 | P1: Validação Estrita e Estabilidade Numérica | Specify | pending |
| MET-06 | P1: Métricas de Regressão em Escala Direta | Specify | pending |
| MET-07 | P1: Métricas de Regressão em Escala Direta | Specify | pending |
| MET-08 | P1: Métricas de Razão Adimensional e Alinhamento | Specify | pending |
| MET-09 | P1: Métricas de Razão Adimensional e Alinhamento | Specify | pending |
| MET-10 | P1: Métricas de Razão Adimensional e Alinhamento | Specify | pending |
| MET-11 | P1: Métricas de Razão Adimensional e Alinhamento | Specify | pending |
| MET-12 | P1: Métricas de Classificação Discreta | Specify | pending |
| MET-13 | P1: Métricas de Classificação Discreta | Specify | pending |
| MET-14 | P1: Métricas de Classificação Discreta | Specify | pending |
| MET-15 | P1: Métricas de Classificação Probabilística | Specify | pending |
| MET-16 | P1: Métricas de Classificação Probabilística | Specify | pending |
| MET-17 | P1: Métricas de Classificação Probabilística | Specify | pending |
| MET-18 | P1: Propagação, Comparação e Ranqueamento (ADR-005) | Specify | pending |
| MET-19 | P1: Propagação, Comparação e Ranqueamento (ADR-005) | Specify | pending |
| MET-20 | P1: Propagação, Comparação e Ranqueamento (ADR-005) | Specify | pending |
| MET-21 | P1: Validação Estrita e Estabilidade Numérica | Specify | pending |
| MET-22 | P1: Propagação, Comparação e Ranqueamento (ADR-005) | Specify | pending |

---

## Sources

- `engenharia_software/ARQUITETURA_E_CONTRATOS.md` Seção 2.3, 3.5, 6.1, 7.1 — Define o módulo `experimental_ml.metrics` (Nível 1), o catálogo `METRICS_CATALOG`, os escopos de avaliação, as 4 famílias de métricas com tolerâncias `rtol`/`atol` justificadas e os critérios de aceitação `TA-M1.3`.
- `engenharia_software/ARQUITETURA_E_CONTRATOS.md` ADR-005 — Define as 4 regras de propagação, comparação (`is_better`), agregação (`aggregate_fold_metrics`) e ranqueamento (`rank_configurations`) para `MetricStatus.UNDEFINED_NAN`.
- `engenharia_software/ARQUITETURA_E_CONTRATOS.md` ADR-008 — Diretriz de programação funcional e modular baseada em funções puras vetorizadas e estruturas de dados imutáveis.
- `engenharia_software/ESPECIFICACAO_REQUISITOS.md` `RF4.7`, `CA-GER-03`, `CA-COND-REG-01`, `CA-COND-CLAS-01`, `CA-COND-MOD-02`, `CA-E5-01`, RNF01, RNF07 — Escopos de avaliação, critérios para divisões por zero, condições de contorno em regressão e classificação, KTA, cobertura parcial e códigos de integridade.
- Referências teórico-metodológicas das métricas: Cristianini et al. (2001) e Cortes et al. (2012) para `KTA`; Hanley & McNeil (1982), Hand & Till (2001) e Fawcett (2006) para `ROC_AUC`; Sokolova & Lapalme (2009) para métricas multiclasse; Hyndman & Koehler (2006) e Willmott (1982) para `MAPE` e `MBE`; Higham (2002) para estabilidade numérica em ponto flutuante.

---

## Success Criteria

- [ ] Estruturas imutáveis `MetricValue`, `AggregatedMetricValue`, `MetricSpec`, `RankedCandidate` e enum fechado `MetricEvaluationScope` definidos e exportados em `experimental_ml.metrics`.
- [ ] Catálogo `METRICS_CATALOG` contendo todas as 15 métricas com metadados completos (incluindo `compare_by_abs=True` para `"mbe"`) e funções de consulta validadas.
- [ ] Funções das 15 métricas vetorizadas (`mae`, `rmse`, `mbe`, `r2`, `rmse_rel_pct`, `mape`, `pearson`, `kta`, `accuracy`, `balanced_accuracy`, `precision`, `recall`, `f1`, `roc_auc`, `log_loss`) cumprindo as tolerâncias `rtol`/`atol` de suas famílias e estabilizadas contra overflow quadrático.
- [ ] Detecção explícita de todos os casos degenerados com retorno de `MetricStatus.UNDEFINED_NAN`, `value=float("nan")` e `Finding` de alerta heurístico, sem coerção silenciosa para `0.0`.
- [ ] Funções `is_better`, `aggregate_fold_metrics` e `rank_configurations` cumprindo integralmente as 4 regras do **ADR-005** e a ordenação lexicográfica `(VALID, PARTIAL_COVERAGE, UNRANKABLE)`.
- [ ] Suíte de testes unitários `tests/unit/test_metrics.py` implementada e aprovada na fase Execute.
