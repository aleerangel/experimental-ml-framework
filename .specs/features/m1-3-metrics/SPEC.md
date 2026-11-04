# Marco M1.3 — Metrics: Catálogo, Funções Vetorizadas e Propagação de `UNDEFINED_NAN`

> **Registro de Especificação do Marco (SPEC.md)**  
> **Identificador do Marco:** M1.3 (`m1-3-metrics`)  
> **Camada Arquitetural:** Nível 1 (Fundação transversal às Etapas 2, 3, 4 e 5)  
> **Status:** Especificação Aprovada (Fase Specify)  
> **Aprovação da Especificação:** `**Approved**: 2026-11-03 - user: "aprovado. commita"`  
> **Especificação EARS Detalhada:** [`spec.md`](./spec.md)  
> **Documentos de Referência:** [`ARQUITETURA_E_CONTRATOS.md`](../../../engenharia_software/ARQUITETURA_E_CONTRATOS.md), [`ESPECIFICACAO_REQUISITOS.md`](../../../engenharia_software/ESPECIFICACAO_REQUISITOS.md), [`PROCESSO_DE_ACEITE_DE_MARCOS.md`](../../../engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md)

---

## 1. Propósito e Problema Abordado

O marco **M1.3** especifica o pacote transversal `experimental_ml.metrics` (Nível 1 da arquitetura), responsável pelo cálculo determinístico e vetorizado de métricas de avaliação em precisão dupla (`float64`), pelo registro de metadados no catálogo `METRICS_CATALOG` e pelas regras de propagação, comparação e agregação de métricas indefinidas (**ADR-005**).

O módulo atende quatro requisitos estruturais do framework:
1. **Padronização de cálculo e metadados:** Fornece funções puras vetorizadas sem dependência de estimadores ou classes com estado mutável (**ADR-008**), acompanhadas de direção de otimização (`MetricDirection`), flag de comparação por valor absoluto (`compare_by_abs`), modalidades aplicáveis (`TaskType`) e tolerâncias numéricas de referência (`rtol`, `atol`).
2. **Estabilidade numérica e prevenção de distorções:** Elimina truncamentos inteiros, arredondamentos prematuros (como `math.ceil`) e overflow quadrático intermediário em somas de quadrados.
3. **Tratamento explícito de indefinições matemáticas (`CA-GER-03`, ADR-005):** Representa divisões por zero, amostras insuficientes ($n < 2$), variância nula e classes ausentes por meio de `MetricStatus.UNDEFINED_NAN` e `value = float("nan")` acompanhados de diagnóstico estruturado (`Finding`), vedando a coerção silenciosa para `0.0`.
4. **Comparação, agregação e ranqueamento seguros entre partições:** Impede que configurações com métrica indefinida vençam candidatos válidos (`is_better`), calcula cobertura de dobras válidas (`aggregate_fold_metrics`) e ordena lexicograficamente candidatos `VALID`, `PARTIAL_COVERAGE` e `UNRANKABLE` (`rank_configurations`).

---

## 2. Escopo do Marco

### 2.1 Incluído no Marco M1.3
- **Pacote `src/experimental_ml/metrics/`:**
  - Enumeração fechada de escopo de avaliação `MetricEvaluationScope(StrEnum)` com membros `"PER_FOLD"`, `"FOLD_AGGREGATION"`, `"POOLED_OOF"` e `"FINAL_HOLDOUT"` (`RF4.7`).
  - Estruturas imutáveis (`@dataclass(frozen=True, slots=True)`): `MetricValue`, `AggregatedMetricValue`, `MetricSpec` e `RankedCandidate`.
  - Catálogo imutável `METRICS_CATALOG` e funções de consulta/despacho (`get_metric_spec`, `list_metrics`, `compute_metric`).
  - **15 funções de métricas vetorizadas (`float64`) divididas em 4 famílias:**
    1. *Erros em escala direta (Regressão — 3 métricas):* `mae`, `rmse`, `mbe` (Viés Médio).
    2. *Razões adimensionais e alinhamento (Regressão / Kernel — 5 métricas):* `r2`, `rmse_rel_pct`, `mape`, `pearson`, `kta` (*Kernel Target Alignment*).
    3. *Proporções discretas (Classificação binária e multiclasse — 5 métricas):* `accuracy`, `balanced_accuracy`, `precision`, `recall`, `f1`.
    4. *Métricas probabilísticas e de ranqueamento (Classificação — 2 métricas):* `roc_auc`, `log_loss`.
  - **Funções de propagação, comparação e agregação (ADR-005):**
    - `is_better(cand_a, cand_b, direction=None)`
    - `aggregate_fold_metrics(fold_values, *, scope=AggregationScope.FOLD_AGGREGATION)`
    - `rank_configurations(candidates, *, direction=None)`
  - Re-exportação pública em `src/experimental_ml/metrics/__init__.py` via `__all__`.
- **Suíte de Testes Unitários:** `tests/unit/test_metrics.py` verificando as 4 famílias com suas respectivas tolerâncias (`rtol`, `atol`), estabilidade numérica, casos degenerados e regras do ADR-005.

### 2.2 Fora de Escopo
- Testes estatísticos inferenciais pareados (`Nadeau-Bengio`, `Wilcoxon`) e correções de comparações múltiplas (`Holm-Bonferroni`, `Benjamini-Hochberg`) — pertencem ao **Marco M6 (`statistics`)**.
- Análise multiobjetivo por Fronteira de Pareto, avaliação de relevância prática ($\Delta_{\text{min}}$) e funções de aquisição sequencial (`EI`, `UCB`/`LCB`, `Exploitation`, `Exploration`) — pertencem ao **Marco M6 (`statistics`)**.
- Ingestão de dados tabulares, perfilamento diagnóstico e geração de `PartitionPlan` — pertencem ao **Marco M2 (`data` e `validation`)**.
- Avaliação agregada de matrizes multialvo simultâneas (`MULTI_TARGET_REGRESSION` como matriz $(n, M)$ consolidada) — planejada para a **Onda 2**.
- Subcomandos da CLI voltados à execução de experimentos e análise estatística (`expml run`, `expml stats`) — pertencem aos **Marcos M5 e M6**.

---

## 3. Dependências com M1.1 e M1.2

O módulo `experimental_ml.metrics` situa-se no **Nível 1** de dependências arquiteturais e depende exclusivamente da biblioteca padrão do Python, de `numpy>=1.24.0` (declarado em `pyproject.toml` no M1.2) e dos contratos públicos de `experimental_ml.core` (Nível 0):

| Origem | Símbolos Reutilizados | Finalidade em `experimental_ml.metrics` |
| :--- | :--- | :--- |
| `experimental_ml.core.enums` | `StrEnum`, `TaskType` | Base de enumeração compatível com JSON e declaração das modalidades suportadas no `METRICS_CATALOG`. |
| `experimental_ml.core.enums` | `MetricDirection` | Direção de otimização (`MAXIMIZE`, `MINIMIZE`) no catálogo, em `is_better` e em `rank_configurations`. |
| `experimental_ml.core.enums` | `MetricStatus` | Classificação de estado do resultado (`VALID`, `UNDEFINED_NAN`, `PARTIAL_COVERAGE`, `UNRANKABLE`). |
| `experimental_ml.core.enums` | `AggregationScope` | Escopos de agregação multinível (`FOLD_AGGREGATION`, `REPETITION_AGGREGATION`, `OVERALL_AGGREGATION`). |
| `experimental_ml.core.findings` | `Finding`, `make_warning`, `make_finding` | Emissão de alertas estruturados (`HEURISTIC_WARNING`) quando uma métrica resulta em `UNDEFINED_NAN` ou `PARTIAL_COVERAGE`. |
| `experimental_ml.core.findings` | `DataIntegrityError`, `ConfigurationError`, `ContractViolationError` | Exceções formais para entradas corrompidas (`NaN`/`Inf`, dimensões incompatíveis, probabilidades inválidas) ou configuração desconhecida. |

---

## 4. Contratos Públicos e Especificações Matemáticas (`experimental_ml.metrics`)

### 4.1 Contrato Fechado de Escopo (`MetricEvaluationScope` e `AggregationScope`)
Para atender ao requisito `RF4.7` e à Seção 2.3/3.4 de `ARQUITETURA_E_CONTRATOS.md` sem permitir strings arbitrárias e sem alterar o contrato `len(AggregationScope) == 3` validado em `tests/unit/test_core.py` (M1.2):
- Define-se `MetricEvaluationScope(StrEnum)` em `experimental_ml.metrics` com exatamente 4 membros canônicos:
  - `PER_FOLD = "PER_FOLD"`
  - `FOLD_AGGREGATION = "FOLD_AGGREGATION"`
  - `POOLED_OOF = "POOLED_OOF"`
  - `FINAL_HOLDOUT = "FINAL_HOLDOUT"`
- **Validação estrita em `MetricValue`:** O campo `scope` (padrão `MetricEvaluationScope.PER_FOLD`) aceita apenas instâncias de `MetricEvaluationScope` ou `AggregationScope` (ou strings idênticas aos seus valores canônicos, convertidas em `__post_init__` para a respectiva instância de enum). Qualquer string arbitrária ou tipo inválido dispara `ConfigurationError`.
- **Validação estrita em `AggregatedMetricValue` e `aggregate_fold_metrics`:** O campo `scope` (padrão `AggregationScope.FOLD_AGGREGATION`) aceita exclusivamente os escopos de agregação (`AggregationScope.FOLD_AGGREGATION`, `AggregationScope.REPETITION_AGGREGATION`, `AggregationScope.OVERALL_AGGREGATION` ou `MetricEvaluationScope.FOLD_AGGREGATION`). Passar `PER_FOLD`, `POOLED_OOF`, `FINAL_HOLDOUT` ou qualquer string arbitrária a `aggregate_fold_metrics` dispara `ConfigurationError`.

### 4.2 Estruturas de Dados Imutáveis
- **`MetricValue`:**
  - `metric_id: str` — identificador canônico em minúsculas (ex.: `"rmse"`, `"r2"`, `"f1"`).
  - `value: float` — valor escalar em `float64`. Invariante: se `status == MetricStatus.VALID`, `math.isfinite(value) == True`; se `status == MetricStatus.UNDEFINED_NAN`, `math.isnan(value) == True`.
  - `status: MetricStatus` — `MetricStatus.VALID` ou `MetricStatus.UNDEFINED_NAN`.
  - `direction: MetricDirection` — `MetricDirection.MAXIMIZE` ou `MetricDirection.MINIMIZE`.
  - `scope: MetricEvaluationScope | AggregationScope` — validado contra os enums fechados (padrão `MetricEvaluationScope.PER_FOLD`).
  - `n_samples: int` — número de observações avaliadas ($n \ge 1$).
  - `warnings: tuple[Finding, ...]` — diagnósticos emitidos durante o cálculo (vazio quando `VALID`).
- **`AggregatedMetricValue`:**
  - `metric_id: str`
  - `mean: float`, `std: float`, `median: float`, `iqr: float` — estatísticas descritivas calculadas sobre as $k$ dobras válidas (`std` amostral com `ddof=1` para $k \ge 2$ e `0.0` para $k = 1$; `iqr = Q_{75} - Q_{25}`; todos `float("nan")` quando $k = 0$).
  - `status: MetricStatus` — `VALID` ($k = K$), `PARTIAL_COVERAGE` ($0 < k < K$) ou `UNDEFINED_NAN` ($k = 0$).
  - `direction: MetricDirection`
  - `scope: AggregationScope | MetricEvaluationScope` — restrito aos escopos de agregação (padrão `AggregationScope.FOLD_AGGREGATION`).
  - `valid_folds: int`, `total_folds: int`, `coverage: float` — razão $k / K \in [0.0, 1.0]$.
  - `fold_values: tuple[MetricValue, ...]` — valores originais preservados para rastreabilidade.
  - `warnings: tuple[Finding, ...]` — alertas consolidados das dobras e da cobertura parcial/nula.
- **`MetricSpec`:**
  - `metric_id: str`, `name: str`, `family: str`
  - `direction: MetricDirection`
  - `compare_by_abs: bool` — `True` exclusivamente para `"mbe"` (onde o ótimo é $0.0$ e o erro é medido por $|\text{MBE}|$); `False` para as demais 14 métricas.
  - `supported_tasks: tuple[TaskType, ...]`
  - `func: Callable[..., MetricValue]`
  - `rtol: float`, `atol: float`
  - `requires_probabilities: bool`, `requires_kernel_matrix: bool`
- **`RankedCandidate`:**
  - `candidate_id: str`
  - `metric: MetricValue | AggregatedMetricValue`
  - `rank: int | None` — posição inteira sequencial iniciando em `1` para candidatos ranqueáveis (`VALID` e `PARTIAL_COVERAGE`); `None` para candidatos `UNRANKABLE`.
  - `status: MetricStatus` — preserva `VALID` ou `PARTIAL_COVERAGE`, ou atribui `MetricStatus.UNRANKABLE` quando a métrica de origem é `UNDEFINED_NAN`.

### 4.3 Catálogo das 15 Métricas Vetorizadas

| ID Canônico | Função Pública | Família | Direção | `compare_by_abs` | Tarefas Suportadas (`TaskType`) | `rtol` | `atol` |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: | :---: |
| `"mae"` | `mae(y_true, y_pred, *, scope=...)` | Escala Direta | `MINIMIZE` | `False` | `REGRESSION` | `1e-12` | `1e-12` |
| `"rmse"` | `rmse(y_true, y_pred, *, scope=...)` | Escala Direta | `MINIMIZE` | `False` | `REGRESSION` | `1e-12` | `1e-12` |
| `"mbe"` | `mbe(y_true, y_pred, *, scope=...)` | Escala Direta | `MINIMIZE` | `True` | `REGRESSION` | `1e-12` | `1e-12` |
| `"r2"` | `r2(y_true, y_pred, *, scope=...)` | Razão Adimensional | `MAXIMIZE` | `False` | `REGRESSION` | `1e-10` | `1e-12` |
| `"rmse_rel_pct"` | `rmse_rel_pct(y_true, y_pred, *, scope=...)` | Razão Adimensional | `MINIMIZE` | `False` | `REGRESSION` | `1e-10` | `1e-12` |
| `"mape"` | `mape(y_true, y_pred, *, scope=...)` | Razão Adimensional | `MINIMIZE` | `False` | `REGRESSION` | `1e-10` | `1e-12` |
| `"pearson"` | `pearson(y_true, y_pred, *, scope=...)` | Razão Adimensional | `MAXIMIZE` | `False` | `REGRESSION` | `1e-10` | `1e-12` |
| `"kta"` | `kta(k_true, k_pred, *, centered=False, scope=...)` | Alinhamento de Kernel | `MAXIMIZE` | `False` | `REGRESSION`, `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION` | `1e-10` | `1e-12` |
| `"accuracy"` | `accuracy(y_true, y_pred, *, scope=...)` | Proporção Discreta | `MAXIMIZE` | `False` | `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION` | `1e-14` | `1e-15` |
| `"balanced_accuracy"` | `balanced_accuracy(y_true, y_pred, *, labels=None, scope=...)` | Proporção Discreta | `MAXIMIZE` | `False` | `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION` | `1e-14` | `1e-15` |
| `"precision"` | `precision(y_true, y_pred, *, average="binary", pos_label=1.0, labels=None, scope=...)` | Proporção Discreta | `MAXIMIZE` | `False` | `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION` | `1e-14` | `1e-15` |
| `"recall"` | `recall(y_true, y_pred, *, average="binary", pos_label=1.0, labels=None, scope=...)` | Proporção Discreta | `MAXIMIZE` | `False` | `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION` | `1e-14` | `1e-15` |
| `"f1"` | `f1(y_true, y_pred, *, average="binary", pos_label=1.0, labels=None, scope=...)` | Proporção Discreta | `MAXIMIZE` | `False` | `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION` | `1e-14` | `1e-15` |
| `"roc_auc"` | `roc_auc(y_true, y_score, *, average="macro", labels=None, scope=...)` | Probabilística / Ranking | `MAXIMIZE` | `False` | `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION` | `1e-9` | `1e-11` |
| `"log_loss"` | `log_loss(y_true, y_prob, *, eps=1e-15, labels=None, scope=...)` | Probabilística / Ranking | `MINIMIZE` | `False` | `BINARY_CLASSIFICATION`, `MULTICLASS_CLASSIFICATION` | `1e-9` | `1e-11` |

---

## 5. Formalização Matemática, Casos Degenerados e Estabilidade Numérica

### 5.1 Semântica do Viés Médio (`mbe`)
- **Cálculo Assinado:** $\text{MBE}(y, \hat{y}) = \frac{1}{n}\sum_{i=1}^n (\hat{y}_i - y_i) \in (-\infty, +\infty)$. O sinal é preservado em `MetricValue.value` e nas estatísticas agregadas de `AggregatedMetricValue` (`mean`, `median`), permitindo diagnosticar superestimação ($\text{MBE} > 0$) e subestimação ($\text{MBE} < 0$) sistemáticas (Willmott, 1982).
- **Comparação por Magnitude Absoluta:** No catálogo, `METRICS_CATALOG["mbe"]` define `direction = MetricDirection.MINIMIZE` e `compare_by_abs = True`. Nas funções `is_better` e `rank_configurations`, quando os candidatos avaliados têm `metric_id == "mbe"` (ou `compare_by_abs == True`), a comparação de desempenho utiliza $|v|$ (`abs(value)` para `MetricValue` e `abs(mean)` para `AggregatedMetricValue`), de modo que um modelo com $\text{MBE} = -0.05$ vence um modelo com $\text{MBE} = -2.0$ ou $+0.50$.

### 5.2 Regressão Adimensional (`r2`, `rmse_rel_pct`, `mape`, `pearson`) e Alinhamento (`kta`)
- **`r2` (Coeficiente de Determinação):**
  $$R^2(y, \hat{y}) = 1 - \frac{\sum_{i=1}^n (y_i - \hat{y}_i)^2}{\sum_{i=1}^n (y_i - \bar{y})^2}$$
  - *Amostras insuficientes ($n = 1$):* Como $n - 1 = 0$, a soma de quadrados total é identicamente zero ($SS_{\text{tot}} = 0$). Retorna `MetricStatus.UNDEFINED_NAN`, `value = float("nan")` e `Finding` (`code="W_METRIC_INSUFFICIENT_SAMPLES"`).
  - *Variância nula ($n \ge 2$ e $SS_{\text{tot}} = 0$):* Mesmo quando $\hat{y} = y$ ($0/0$), jamais converte para `1.0` ou `0.0`. Retorna `MetricStatus.UNDEFINED_NAN`, `value = float("nan")` e `Finding` (`code="W_METRIC_ZERO_VARIANCE"`).
  - *Preditor constante ($\hat{y}_i = \bar{y}$ com $SS_{\text{tot}} > 0$):* Retorna `0.0` com `MetricStatus.VALID`.
- **`mape` (Erro Percentual Absoluto Médio):**
  $$\text{MAPE}(y, \hat{y}) = \frac{100.0}{n} \sum_{i=1}^n \left| \frac{y_i - \hat{y}_i}{y_i} \right|$$
  - *Tratamento de $y_i = 0$ (Hyndman & Koehler, 2006):* Se qualquer observação satisfizer $y_i == 0.0$ (independentemente de $\hat{y}_i = 0$ ou $\hat{y}_i \neq 0$), a função **não** descarta a observação, **não** adiciona $\epsilon$ ao denominador e **não** substitui $0/0$ por $0.0$; retorna `MetricStatus.UNDEFINED_NAN`, `value = float("nan")` e `Finding` (`code="W_METRIC_ZERO_TARGET"`, registrando `n_zero_targets` em `context`).
- **`rmse_rel_pct`:** $\text{RMSE\_rel\_pct} = 100.0 \times \frac{\text{RMSE}(y, \hat{y})}{|\bar{y}|}$. Se $|\bar{y}| == 0.0$, retorna `MetricStatus.UNDEFINED_NAN`, `value = float("nan")` e `Finding`.
- **`pearson`:** Coeficiente de correlação amostral de Pearson. Se $n < 2$, $\text{Var}(y) = 0$ ou $\text{Var}(\hat{y}) = 0$, retorna `MetricStatus.UNDEFINED_NAN`, `value = float("nan")` e `Finding`.
- **`kta` (*Kernel Target Alignment* — Cristianini et al., 2001; Cortes et al., 2012):**
  - Assinatura: `kta(k_true, k_pred, *, centered: bool = False, scope: MetricEvaluationScope = MetricEvaluationScope.PER_FOLD) -> MetricValue`.
  - Se `k_true` ou `k_pred` for vetor 1D $v \in \mathbb{R}^n$ (ou coluna $(n, 1)$), constrói a matriz de Gram $K = v v^T \in \mathbb{R}^{n \times n}$. Ambas as matrizes devem ter shape quadrado idêntico $(n, n)$ (caso contrário, lança `DataIntegrityError`).
  - *Convenção de centralização:*
    - `centered=False` (padrão — Cristianini et al., 2001): $\tilde{K}_1 = K_{\text{true}}, \tilde{K}_2 = K_{\text{pred}}$.
    - `centered=True` (Cortes et al., 2012): aplica dupla centralização $\tilde{K}_m = H K_m H$ com $H = I_n - \frac{1}{n}\mathbf{1}\mathbf{1}^T$.
  - *Fórmula:*
    $$\text{KTA}(\tilde{K}_1, \tilde{K}_2) = \frac{\langle \tilde{K}_1, \tilde{K}_2 \rangle_F}{\|\tilde{K}_1\|_F \|\tilde{K}_2\|_F}, \quad \langle A, B \rangle_F = \sum_{i=1}^n \sum_{j=1}^n A_{ij} B_{ij}$$
  - *Caso degenerado:* Se $\|\tilde{K}_1\|_F = 0$ ou $\|\tilde{K}_2\|_F = 0$ (matriz nula em `centered=False` ou matriz constante em `centered=True`), retorna `MetricStatus.UNDEFINED_NAN`, `value = float("nan")` e `Finding` (`code="W_METRIC_ZERO_GRAM_NORM"`).

### 5.3 Classificação Discreta Binária e Multiclasse (`precision`, `recall`, `f1`, `balanced_accuracy`)
Seja $\mathcal{C}$ o conjunto ordenado de classes avaliadas:
- Em modo binário (`average="binary"`): $\mathcal{C} = \{\text{pos\_label}\}$ (rejeitando entradas com mais de 2 classes únicas em $y_{\text{true}} \cup \hat{y}$ com `DataIntegrityError`).
- Quando `labels` é informado: $\mathcal{C} = \text{unique}(\text{labels})$.
- Quando `labels=None` em `precision`, `recall`, `f1` (`average in ("macro", "weighted")`) e `balanced_accuracy`: $\mathcal{C} = \text{unique}(y_{\text{true}}) \cup \text{unique}(\hat{y})$.

Para cada classe $c \in \mathcal{C}$, definem-se $TP_c$, $FP_c$, $FN_c$, o total de predições positivas $P_{\text{pred}, c} = TP_c + FP_c$ e o suporte real $S_c = TP_c + FN_c$:

| Métrica | Condição de Indefinição (`MetricStatus.UNDEFINED_NAN`) | Condição de Valor Zero Válido (`0.0`, `MetricStatus.VALID`) | Justificativa da Propagação em Multiclasse (`macro`/`weighted`) |
| :--- | :--- | :--- | :--- |
| **`precision`** | Existe $c \in \mathcal{C}$ com $TP_c + FP_c = 0$ (nenhuma predição positiva para a classe $c$), ou $\sum_{c \in \mathcal{C}} S_c = 0$. | Para todo $c \in \mathcal{C}$, $TP_c + FP_c > 0$, e $TP_c = 0$ com $FP_c > 0$ ($\frac{0}{FP_c} = 0.0$). | Substituir $\frac{0}{0}$ por $0.0$ em uma classe sem predições positivas confunde abstenção do classificador com 100% de falsos positivos (Sokolova & Lapalme, 2009; ADR-005). |
| **`recall`** | Existe $c \in \mathcal{C}$ com $TP_c + FN_c = 0$ (classe ausente em $y_{\text{true}}$, seja por ter sido predita em $\hat{y}$ sem existir em $y_{\text{true}}$ ou listada em `labels`). | Para todo $c \in \mathcal{C}$, $TP_c + FN_c > 0$, mesmo que $TP_c + FP_c = 0$ ($\frac{0}{FN_c} = 0.0$). | Uma classe sem exemplares reais na partição possui taxa de verdadeiros positivos indefinida ($\frac{0}{0}$); não pode ser tratada como revocação zero nem silenciosamente omitida de $\|\mathcal{C}\|$. |
| **`f1`** | Existe $c \in \mathcal{C}$ com $TP_c + FP_c = 0$ ($\text{Precision}_c$ indefinida) **ou** $TP_c + FN_c = 0$ ($\text{Recall}_c$ indefinida). | Para todo $c \in \mathcal{C}$, $TP_c + FP_c > 0$ e $TP_c + FN_c > 0$; se $TP_c = 0$ (com $FP_c > 0$ e $FN_c > 0$), $\text{Precision}_c = 0.0$ e $\text{Recall}_c = 0.0$ são ambos válidos e $\text{F1}_c = \frac{2 TP_c}{2 TP_c + FP_c + FN_c} = 0.0$. | Como média harmônica entre Precisão e Revocação, o `F1` só é definido quando ambos os seus componentes são definidos; quando ambos valem $0.0$ com denominadores positivos, o limite contínuo na origem é $0.0$. |
| **`balanced_accuracy`** | $\|\mathcal{C}\| < 2$ (partição monoclasse) **ou** existe $c \in \mathcal{C}$ com $TP_c + FN_c = 0$. | $\|\mathcal{C}\| \ge 2$ e todo $c \in \mathcal{C}$ possui $TP_c + FN_c > 0$. | A acurácia balanceada é a média aritmética da revocação entre pelo menos duas classes; se uma classe não tem suporte real ou só há uma classe, a média entre classes é indefinida. |

### 5.4 Métricas Probabilísticas e de Ranqueamento (`roc_auc`, `log_loss`)
- **`roc_auc` (Hanley & McNeil, 1982; Hand & Till, 2001; Fawcett, 2006):**
  - *Validação de classes:* Seja $\mathcal{C} = \text{unique}(y_{\text{true}})$ ordenado (ou `tuple(labels)` quando fornecido). Se $|\text{unique}(y_{\text{true}})| < 2$, retorna `MetricStatus.UNDEFINED_NAN`, `value = float("nan")` e `Finding`.
  - *Caso Binário ($|\mathcal{C}| = 2$, classes $\{c_0, c_1\}$):* Aceita `y_score` 1D de shape $(n,)$, 2D de coluna única $(n, 1)$ (escore da classe positiva $c_1$) ou 2D de shape $(n, 2)$ (usando a coluna `1` correspondente a $c_1$).
  - *Tratamento determinístico de escores empatados:* Calcula a estatística exata de Mann-Whitney $U$ / integração trapezoidal por postos médios (*mid-ranks*):
    $$\text{AUC}_{\text{bin}}(y, s) = \frac{1}{N_+ N_-} \sum_{i: y_i = c_1} \sum_{j: y_j = c_0} \left[ \mathbb{I}(s_i > s_j) + \frac{1}{2}\mathbb{I}(s_i = s_j) \right] = \frac{\sum_{i: y_i = c_1} R_i - \frac{N_+(N_+ + 1)}{2}}{N_+ N_-}$$
    onde observações empatadas recebem a média aritmética das posições que ocupam na ordenação crescente. Escores constantes ($s_1 = \dots = s_n$) retornam exatamente `0.5`.
  - *Caso Multiclasse One-vs-Rest ($|\mathcal{C}| = K \ge 3$):* Exige matriz `y_score` 2D de shape $(n, K)$ em que a coluna $k \in \{0, \dots, K-1\}$ corresponde à classe $\mathcal{C}[k]$ (lançando `DataIntegrityError` se `y_score` for 1D ou $K \neq |\mathcal{C}|$). Para cada classe $c_k$, calcula $\text{AUC}_k$ binário ($y_i == c_k$ vs. $y_i \neq c_k$). Se qualquer $c_k \in \mathcal{C}$ tiver $N_{+, k} = 0$ ou $N_{-, k} = 0$, propaga `MetricStatus.UNDEFINED_NAN` com `Finding`. Agrega via `average="macro"` ($\frac{1}{K}\sum_k \text{AUC}_k$) ou `average="weighted"` ($\frac{1}{n}\sum_k N_{+, k} \text{AUC}_k$).
- **`log_loss` (Entropia Cruzada — Bishop, 2006):**
  - *Formato esperado e mapeamento coluna-classe:*
    - Seja $\mathcal{C} = \text{unique}(y_{\text{true}})$ ordenado quando `labels=None`, ou `tuple(labels)` quando `labels` é informado. Se $|\text{unique}(y_{\text{true}})| < 2$, retorna `MetricStatus.UNDEFINED_NAN` com `Finding`. Se algum valor de `y_true` não pertencer a $\mathcal{C}$, lança `DataIntegrityError`.
    - Para $|\mathcal{C}| = 2$: aceita vetor 1D $(n,)$ (ou $(n, 1)$) com $p_i = P(Y_i = \mathcal{C}[1])$, formando $(1 - p_i, p_i)$, ou matriz 2D $(n, 2)$ com $[P(Y_i = \mathcal{C}[0]), P(Y_i = \mathcal{C}[1])]$.
    - Para $|\mathcal{C}| = K \ge 3$: exige matriz 2D $(n, K)$ onde a coluna $k$ corresponde a $\mathcal{C}[k]$. Vetor 1D para $K \ge 3$ ou número de colunas diferente de $|\mathcal{C}|$ lança `DataIntegrityError`.
  - *Validação das distribuições e Clipping ($\epsilon = 10^{-15}$):*
    - Valida $0 < \text{eps} < 0.5$ (`ConfigurationError` caso contrário).
    - Verifica que toda entrada satisfaz $-10^{-12} \le p_{i,k} \le 1.0 + 10^{-12}$ e, para matrizes 2D, que a soma de cada linha satisfaz $|\sum_{k=0}^{K-1} p_{i,k} - 1.0| \le 10^{-6}$; violações disparam `DataIntegrityError`.
    - Aplica clipping $\tilde{p}_{i,k} = \text{clip}(p_{i,k}, \epsilon, 1 - \epsilon)$, renormaliza as linhas no caso 2D ($\hat{p}_{i,k} = \tilde{p}_{i,k} / \sum_j \tilde{p}_{i,j}$) e calcula $-\frac{1}{n}\sum_{i=1}^n \ln(\hat{p}_{i, y_i})$.

### 5.5 Estabilidade Numérica e Prevenção de Overflow (Higham, 2002; IEEE 754)
1. **Estabilização analítica contra overflow quadrático:**
   - Em `rmse`: seja $m = \max_i |y_i - \hat{y}_i|$. Se $m == 0.0$, retorna $0.0$; se $m > 0.0$, avalia $m \sqrt{\frac{1}{n}\sum_{i=1}^n ((y_i - \hat{y}_i)/m)^2}$, impedindo overflow quando $|y_i - \hat{y}_i| > 1.34 \times 10^{154}$.
   - Em `r2` e `pearson`: reescalona os desvios pelo máximo absoluto antes de elevar ao quadrado.
   - Em `kta`: reescalona cada matriz $\tilde{K}_m$ por $\max_{i,j} |(\tilde{K}_m)_{ij}|$ antes do produto interno de Frobenius.
   - Em `pearson` e `kta`: limita (*clamp*) resíduos de arredondamento nas bordas para $[-1.0, 1.0]$.
2. **Guarda de pós-condição para resultados não finitos:**
   - Se qualquer operação intermediária ou final ainda produzir `+Inf`, `-Inf` ou `NaN` a partir de entradas finitas (ex.: quando a própria diferença $y_i - \hat{y}_i$ ou soma linear exceder `float64.max` $\approx 1.79769 \times 10^{308}$), a função converte o retorno para `value = float("nan")`, `status = MetricStatus.UNDEFINED_NAN` e anexa um `Finding` (`code="W_METRIC_NUMERICAL_OVERFLOW"`).
   - Garante-se por contrato que nenhum `MetricValue` com `status == MetricStatus.VALID` contenha `NaN` ou `±Inf`.

### 5.6 Ordenação Formal em `is_better` e `rank_configurations` (**ADR-005**)
- **Partição de Candidatos:**
  - *Ranqueáveis:* candidatos com `status in (MetricStatus.VALID, MetricStatus.PARTIAL_COVERAGE)` e valor numérico finito.
  - *Não ranqueáveis:* candidatos com `status in (MetricStatus.UNDEFINED_NAN, MetricStatus.UNRANKABLE)` ou valor não finito. Recebem `status = MetricStatus.UNRANKABLE` e `rank = None`, posicionados ao final da lista em ordem crescente de `candidate_id`.
- **Chave Lexicográfica de Ordenação dos Candidatos Ranqueáveis:**
  Para cada candidato ranqueável, define-se a tupla de ordenação crescente:
  $$\text{key}(c) = \left( \mathbb{I}(\text{status}_c \neq \text{VALID}), \; -\text{coverage}_c, \; v^{\text{dir}}_c, \; \text{candidate\_id}_c \right)$$
  onde:
  1. $\mathbb{I}(\text{status}_c \neq \text{VALID}) \in \{0, 1\}$: todo candidato `VALID` ($K/K$ dobras, prioridade $0$) precede qualquer candidato `PARTIAL_COVERAGE` ($k < K$ dobras, prioridade $1$), prevenindo viés de sobrevivência (`CA-E5-01`).
  2. $-\text{coverage}_c = -k/K$: entre candidatos com `PARTIAL_COVERAGE`, maior fração de dobras válidas precede menor cobertura.
  3. $v^{\text{dir}}_c$: valor direcionado da métrica (`|v|` se `compare_by_abs=True`; `+v` se `MINIMIZE`; `-v` se `MAXIMIZE`, onde $v$ é `value` em `MetricValue` ou `mean` em `AggregatedMetricValue`).
  4. $\text{candidate\_id}_c$: desempate determinístico por ordem lexicográfica de string.

---

## 6. Matriz de Requisitos Rastreáveis e Critérios de Aceitação (MET-01 a MET-22)

| ID | Requisito EARS (`spec.md`) | Critério Objetivo de Aceitação |
| :--- | :--- | :--- |
| **MET-01** | Estruturas imutáveis `MetricValue`, `AggregatedMetricValue`, `MetricSpec`, `RankedCandidate` | Instâncias congeladas (`frozen=True`); tentativa de mutação de atributo levanta `FrozenInstanceError` / `AttributeError`. |
| **MET-02** | Catálogo `METRICS_CATALOG` com as 15 métricas e `compare_by_abs` | Expõe as 15 especificações com funções, direções, `compare_by_abs=True` para `"mbe"` (`False` nas demais), `TaskType` e tolerâncias `rtol`/`atol`. |
| **MET-03** | Consulta e despacho via `get_metric_spec` e `compute_metric` | Resolve métricas válidas (case-insensitive) e lança `ConfigurationError` para identificadores inexistentes. |
| **MET-04** | Conversão segura para `float64` e validação dimensional | Converte entradas sem mutar os arrays de origem; rejeita $n=0$ ou tamanhos distintos com `DataIntegrityError`. |
| **MET-05** | Rejeição de `NaN` e `Inf` nas entradas | Qualquer `NaN`, `+Inf` ou `-Inf` em `y_true`, `y_pred` ou `y_score` levanta `DataIntegrityError`. |
| **MET-06** | Cálculo de `mae`, `rmse` e `mbe` assinado (`rtol=1e-12`, `atol=1e-12`) | Valores coincidem com referências analíticas dentro de `1e-12`; `mbe.value` preserva sinal positivo e negativo; $\hat{y}=y$ retorna `0.0`. |
| **MET-07** | Homocedasticidade de escala em `rmse` sem arredondamento | $\text{RMSE}(c \cdot y, c \cdot \hat{y}) == |c| \cdot \text{RMSE}(y, \hat{y})$ com `rtol=1e-12` e `atol=0.0`. |
| **MET-08** | Cálculo regular de `r2`, `rmse_rel_pct`, `mape`, `pearson`, `kta` | Predição perfeita retorna `1.0` (`r2`, `pearson`, `kta`) e `0.0` (`rmse_rel_pct`, `mape`); modelo constante $\hat{y}=\bar{y}$ retorna `r2 == 0.0` (`rtol=1e-10`, `atol=1e-12`). |
| **MET-09** | `UNDEFINED_NAN` em `r2` e `pearson` para $n < 2$ ou variância nula | $n = 1$ ou variância zero em `y_true` (ou `y_pred` para `pearson`) retorna `MetricStatus.UNDEFINED_NAN`, `isnan(value)` e `Finding` específico (`W_METRIC_INSUFFICIENT_SAMPLES` ou `W_METRIC_ZERO_VARIANCE`). |
| **MET-10** | `UNDEFINED_NAN` em `rmse_rel_pct` ($\bar{y}=0$) e `mape` ($y_i=0$) | Média zero em `rmse_rel_pct` ou qualquer $y_i == 0.0$ em `mape` retorna `MetricStatus.UNDEFINED_NAN`, `isnan(value)` e `Finding` sem descartar amostras nem somar $\epsilon$. |
| **MET-11** | `kta` com `centered: bool = False` e `UNDEFINED_NAN` sob norma nula | Calcula alinhamento não centralizado (`centered=False`) e centralizado $HKH$ (`centered=True`); retorna `UNDEFINED_NAN` e `Finding` quando $\|\tilde{K}\|_F = 0$. |
| **MET-12** | Cálculo de `accuracy`, `balanced_accuracy`, `precision`, `recall`, `f1` (`rtol=1e-14`, `atol=1e-15`) | Resultados binários e multiclasse (`macro`, `weighted`) coincidem com vetores analíticos em matrizes de confusão conhecidas. |
| **MET-13** | Tratamento individual de $TP_c + FP_c = 0$ em `precision`, `recall`, `f1`, `balanced_accuracy` | Quando $TP_c + FP_c = 0$ e $TP_c + FN_c > 0$: `precision` e `f1` retornam `UNDEFINED_NAN` com `Finding` (jamais `0.0`), enquanto `recall` e `balanced_accuracy` permanecem `VALID` (`0.0` para a classe $c$). |
| **MET-14** | Tratamento individual de $TP_c + FN_c = 0$ e $TP_c = 0$ ($FP_c>0, FN_c>0$) | Quando $TP_c + FN_c = 0$: `recall`, `f1` e `balanced_accuracy` retornam `UNDEFINED_NAN` com `Finding` (e `balanced_accuracy` também para $|\mathcal{C}| < 2$); quando $TP_c = 0$ com $FP_c > 0$ e $FN_c > 0$, `precision`, `recall` e `f1` retornam `0.0` (`VALID`). |
| **MET-15** | `roc_auc` (empates via postos médios, 1D/2D e OVR) e `log_loss` ($\epsilon=10^{-15}$) | `roc_auc` trata empates via Mann-Whitney $U$ (`0.5` para escores constantes) e multiclasse OVR (`macro`, `weighted`); `log_loss` mapeia 1D/2D para $\mathcal{C}$ e aplica clipping em $\{0, 1\}$ (`rtol=1e-9`, `atol=1e-11`). |
| **MET-16** | `UNDEFINED_NAN` em `roc_auc` e `log_loss` para alvo monoclasse ou classe OVR vazia | `y_true` com menos de 2 classes únicas (ou classe em `labels` com $N_{+,k}=0$ ou $N_{-,k}=0$ em `roc_auc`) retorna `MetricStatus.UNDEFINED_NAN`, `isnan(value)` e `Finding`. |
| **MET-17** | Validação de formato, mapeamento de classes e distribuições em `log_loss` | Probabilidades fora de $[0, 1]$, linhas 2D com soma $\neq 1.0$ (além de `1e-6`), número de colunas $\neq |\mathcal{C}|$, 1D para $|\mathcal{C}| \ge 3$ ou alvo fora de `labels` levantam `DataIntegrityError`. |
| **MET-18** | Comparador `is_better` com `compare_by_abs` (`mbe`), cobertura e `UNDEFINED_NAN` | Ranqueável vence `UNDEFINED_NAN`; `VALID` vence `PARTIAL_COVERAGE`; maior `coverage` vence menor `coverage`; em `mbe` compara $|\text{MBE}|$; dois `UNDEFINED_NAN` retornam `False`. |
| **MET-19** | Agregação `aggregate_fold_metrics` ($K/K$, $k/K$ e $0/K$ dobras) | Produz `VALID` ($K/K$), `PARTIAL_COVERAGE` com `Finding` ($0 < k < K$) e `UNDEFINED_NAN` com `Finding` ($0/K$). |
| **MET-20** | Ranqueamento lexicográfico `rank_configurations` (`VALID`, `PARTIAL_COVERAGE`, `UNRANKABLE`) | Ordena por `(status != VALID, -coverage, directed_value, candidate_id)` com `rank=1..R` e posiciona `UNDEFINED_NAN` ao final com `status=MetricStatus.UNRANKABLE` e `rank=None`. |
| **MET-21** | Estabilização numérica contra overflow quadrático e guarda de não-finitos | Evita overflow intermediário em `rmse`, `r2`, `pearson` e `kta` para entradas de ordem $10^{200}$; converte overflow residual em `UNDEFINED_NAN` com `Finding` (`W_METRIC_NUMERICAL_OVERFLOW`). |
| **MET-22** | Validação estrita de `MetricEvaluationScope` e `AggregationScope` | Aceita apenas escopos canônicos fechados (`PER_FOLD`, `FOLD_AGGREGATION`, `POOLED_OOF`, `FINAL_HOLDOUT`, `REPETITION_AGGREGATION`, `OVERALL_AGGREGATION`); rejeita strings arbitrárias ou escopos incompatíveis com `ConfigurationError`. |

---

## 7. Estratégia Prevista de Testes Automatizados e Validação Manual

1. **Testes Unitários Automatizados (`tests/unit/test_metrics.py`):**
   - Verificação 1:1 para os 22 requisitos (`MET-01` a `MET-22`), mapeados aos checks `C1` a `C22` na fase Tasks.
   - Asserções numéricas parametrizadas com `np.isclose(..., rtol=..., atol=...)` respeitando os limiares estritos de cada família definidos na Seção 7.1 de `ARQUITETURA_E_CONTRATOS.md`.
   - Testes explícitos de todos os casos degenerados, de estabilidade sob grandes magnitudes ($10^{200}$ e overflow de `float64`) e das regras de ordenação entre `VALID`, `PARTIAL_COVERAGE` e `UNRANKABLE`.
2. **Testes de Regressão e Fumaça (`pytest tests/`):**
   - Execução conjunta de `tests/test_smoke.py`, `tests/unit/test_core.py` e `tests/unit/test_metrics.py`.
3. **Roteiro de Aceitação do Consumidor (`ACCEPTANCE.md` — a ser elaborado na fase Tasks):**
   - Exemplos executáveis utilizando exclusivamente a interface pública de `experimental_ml.metrics`.
   - Cenário integrado simulando avaliação de múltiplos modelos em validação cruzada com dobras regulares e degeneradas, agregação via `aggregate_fold_metrics` e ranqueamento via `rank_configurations`.
