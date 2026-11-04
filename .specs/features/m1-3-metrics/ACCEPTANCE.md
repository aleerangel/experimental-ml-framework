# Roteiro de Validação e Aceitação — Marco M1.3

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M1.3 (`m1-3-metrics`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e consumidores da biblioteca `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.metrics`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e o pacote instalado com NumPy:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e importação do módulo metrics
python -c "import experimental_ml.metrics; print('Metrics importado com sucesso! Exportacoes:', len(experimental_ml.metrics.__all__))"
```

- **Resultado Esperado:** Mensagem confirmando importação e 29 símbolos públicos exportados em `__all__`.
- **Critério de Falha:** `ModuleNotFoundError` para `experimental_ml.metrics` ou símbolos ausentes.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Estruturas Imutáveis, Enumeração de Escopo e Catálogo

```python
import pytest
from experimental_ml.metrics import (
    MetricEvaluationScope,
    MetricValue,
    AggregatedMetricValue,
    MetricSpec,
    RankedCandidate,
    METRICS_CATALOG,
    get_metric_spec,
    list_metrics,
    compute_metric,
)
from experimental_ml.core import MetricStatus, MetricDirection, AggregationScope, ConfigurationError

# 1. Validação de membros do catálogo
assert len(METRICS_CATALOG) == 15
assert len(list_metrics()) == 15
spec_mbe = get_metric_spec("mbe")
assert spec_mbe.compare_by_abs is True
assert spec_mbe.direction == MetricDirection.MINIMIZE

spec_rmse = get_metric_spec("rmse")
assert spec_rmse.compare_by_abs is False

# 2. Validação de rejeição de métrica inexistente
try:
    get_metric_spec("metrica_desconhecida_xyz")
    raise AssertionError("Deveria ter lançado ConfigurationError")
except ConfigurationError:
    pass

# 3. Imutabilidade e validação de escopo
mv = MetricValue(
    metric_id="rmse",
    value=0.15,
    status=MetricStatus.VALID,
    direction=MetricDirection.MINIMIZE,
    scope=MetricEvaluationScope.PER_FOLD,
    n_samples=100,
    warnings=(),
)
try:
    mv.value = 0.20  # type: ignore[misc]
    raise AssertionError("Deveria ter impedido mutação")
except (AttributeError, TypeError):
    pass

# 4. Rejeição de escopo arbitrário
try:
    MetricValue(
        metric_id="rmse",
        value=0.15,
        status=MetricStatus.VALID,
        direction=MetricDirection.MINIMIZE,
        scope="ESCOPO_ARBITRARIO",
        n_samples=100,
        warnings=(),
    )
    raise AssertionError("Deveria ter rejeitado escopo arbitrário")
except ConfigurationError:
    pass

print("✓ 2.1 Estruturas imutáveis, escopos e catálogo validados.")
```

---

### 2.2 Métricas de Regressão e Alinhamento de Kernel

```python
import math
import numpy as np
from experimental_ml.metrics import mae, rmse, mbe, r2, rmse_rel_pct, mape, pearson, kta
from experimental_ml.core import MetricStatus

y_true = np.array([10.0, 20.0, 30.0, 40.0])
y_pred = np.array([12.0, 19.0, 31.0, 42.0])

# 1. Erros em escala direta
res_mae = mae(y_true, y_pred)
res_rmse = rmse(y_true, y_pred)
res_mbe = mbe(y_true, y_pred)
assert math.isclose(res_mae.value, 1.5, rel_tol=1e-12)
assert res_mbe.value == 1.0  # (2 - 1 + 1 + 2) / 4 = +1.0 (superestimação)
assert res_mbe.status == MetricStatus.VALID

# 2. Homocedasticidade de escala em RMSE
res_rmse_scaled = rmse(10.0 * y_true, 10.0 * y_pred)
assert math.isclose(res_rmse_scaled.value, 10.0 * res_rmse.value, rel_tol=1e-12)

# 3. Razões adimensionais
res_r2 = r2(y_true, y_pred)
assert res_r2.value > 0.95
assert res_r2.status == MetricStatus.VALID

# 4. Casos degenerados retornando UNDEFINED_NAN
res_r2_single = r2(np.array([10.0]), np.array([10.0]))
assert math.isnan(res_r2_single.value)
assert res_r2_single.status == MetricStatus.UNDEFINED_NAN

res_mape_zero = mape(np.array([0.0, 10.0]), np.array([1.0, 10.0]))
assert math.isnan(res_mape_zero.value)
assert res_mape_zero.status == MetricStatus.UNDEFINED_NAN

res_rel_zero_mean = rmse_rel_pct(np.array([-10.0, 10.0]), np.array([-9.0, 9.0]))
assert math.isnan(res_rel_zero_mean.value)
assert res_rel_zero_mean.status == MetricStatus.UNDEFINED_NAN

# 5. KTA não centralizado e centralizado
K1 = np.eye(4)
K2 = np.eye(4)
res_kta = kta(K1, K2, centered=False)
assert math.isclose(res_kta.value, 1.0, rel_tol=1e-10)

print("✓ 2.2 Métricas de regressão e alinhamento validadas.")
```

---

### 2.3 Métricas de Classificação Discreta e Casos de Indefinição

```python
import math
import numpy as np
from experimental_ml.metrics import accuracy, balanced_accuracy, precision, recall, f1
from experimental_ml.core import MetricStatus

y_t = np.array([0, 0, 1, 1])
y_p = np.array([0, 1, 1, 1])

res_acc = accuracy(y_t, y_p)
assert math.isclose(res_acc.value, 0.75, rel_tol=1e-14)

# 1. Sem predições positivas para a classe 1 (TP_1 = 0, FP_1 = 0)
y_all_zero = np.array([0, 0, 0, 0])
res_prec_und = precision(y_t, y_all_zero, pos_label=1.0)
assert math.isnan(res_prec_und.value)
assert res_prec_und.status == MetricStatus.UNDEFINED_NAN

# Recall deve ser 0.0 legítimo (TP=0, FN=2 > 0)
res_rec_zero = recall(y_t, y_all_zero, pos_label=1.0)
assert res_rec_zero.value == 0.0
assert res_rec_zero.status == MetricStatus.VALID

# F1 deve ser 0.0 legítimo (denominador 2*0 + 0 + 2 = 2 > 0)
res_f1_zero = f1(y_t, y_all_zero, pos_label=1.0)
assert res_f1_zero.value == 0.0
assert res_f1_zero.status == MetricStatus.VALID

# 2. Classe totalmente ausente em y_true e y_pred (denominador do F1 = 0)
y_no_class2 = np.array([0, 1])
res_f1_und = f1(y_no_class2, y_no_class2, labels=[0, 1, 2], average="macro")
assert math.isnan(res_f1_und.value)
assert res_f1_und.status == MetricStatus.UNDEFINED_NAN

print("✓ 2.3 Métricas de classificação discreta e regras por classe validadas.")
```

---

### 2.4 Métricas Probabilísticas e de Ranqueamento (`roc_auc`, `log_loss`)

```python
import math
import numpy as np
from experimental_ml.metrics import roc_auc, log_loss
from experimental_ml.core import MetricStatus, DataIntegrityError

y_bin = np.array([0, 0, 1, 1])
scores_perfect = np.array([0.1, 0.2, 0.8, 0.9])
scores_tied = np.array([0.5, 0.5, 0.5, 0.5])

# 1. Separação perfeita e empates exatos por postos médios
assert math.isclose(roc_auc(y_bin, scores_perfect).value, 1.0, rel_tol=1e-9)
assert math.isclose(roc_auc(y_bin, scores_tied).value, 0.5, rel_tol=1e-9)

# 2. Log-loss com probabilidades extremas {0.0, 1.0} sob clipping eps=1e-15
probs_extreme = np.array([0.0, 0.0, 1.0, 1.0])
res_ll = log_loss(y_bin, probs_extreme)
assert res_ll.value > 0.0 and math.isfinite(res_ll.value)
assert res_ll.status == MetricStatus.VALID

# 3. Rejeição de probabilidades inválidas (fora de [0, 1])
try:
    log_loss(y_bin, np.array([-0.2, 0.1, 0.8, 1.5]))
    raise AssertionError("Deveria ter lançado DataIntegrityError")
except DataIntegrityError:
    pass

print("✓ 2.4 ROC AUC e Log Loss validados.")
```

---

### 2.5 Comparação, Agregação e Ranqueamento (ADR-005)

```python
from experimental_ml.metrics import (
    MetricValue,
    AggregatedMetricValue,
    MetricEvaluationScope,
    is_better,
    aggregate_fold_metrics,
    rank_configurations,
)
from experimental_ml.core import MetricStatus, MetricDirection, AggregationScope

# 1. Comparador de MBE por magnitude absoluta
mv_mbe1 = MetricValue("mbe", -0.05, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10, ())
mv_mbe2 = MetricValue("mbe", 0.50, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10, ())
assert is_better(mv_mbe1, mv_mbe2) is True  # |-0.05| < |0.50|

# 2. Valid sempre supera UNDEFINED_NAN
mv_und = MetricValue("rmse", float("nan"), MetricStatus.UNDEFINED_NAN, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10, ())
mv_valid = MetricValue("rmse", 2.5, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10, ())
assert is_better(mv_valid, mv_und) is True
assert is_better(mv_und, mv_valid) is False

# 3. Agregação com cobertura parcial (3/5 folds)
folds = [
    MetricValue("rmse", 1.0, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10, ()),
    MetricValue("rmse", 1.2, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10, ()),
    MetricValue("rmse", 0.8, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10, ()),
    MetricValue("rmse", float("nan"), MetricStatus.UNDEFINED_NAN, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10, ()),
    MetricValue("rmse", float("nan"), MetricStatus.UNDEFINED_NAN, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10, ()),
]
agg = aggregate_fold_metrics(folds)
assert agg.status == MetricStatus.PARTIAL_COVERAGE
assert agg.valid_folds == 3 and agg.total_folds == 5
assert agg.coverage == 0.6
assert len(agg.warnings) >= 1

# 4. Ranqueamento lexicográfico: VALID precede PARTIAL_COVERAGE
cands = {
    "cand_partial_otimo": agg,  # coverage=0.6, mean=1.0
    "cand_valid_regular": AggregatedMetricValue(
        "rmse", 1.1, 0.1, 1.1, 0.05, MetricStatus.VALID, MetricDirection.MINIMIZE,
        AggregationScope.FOLD_AGGREGATION, 5, 5, 1.0, (), ()
    ),
    "cand_quebrado": MetricValue("rmse", float("nan"), MetricStatus.UNDEFINED_NAN, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10, ()),
}
ranking = rank_configurations(cands)
assert ranking[0].candidate_id == "cand_valid_regular"
assert ranking[0].rank == 1
assert ranking[1].candidate_id == "cand_partial_otimo"
assert ranking[1].rank == 2
assert ranking[2].candidate_id == "cand_quebrado"
assert ranking[2].rank is None
assert ranking[2].status == MetricStatus.UNRANKABLE

print("✓ 2.5 Comparação, agregação e ranqueamento validados.")
```

---

## 3. Cenário Integrado de Aceitação

```bash
python - << 'EOF'
import numpy as np
from experimental_ml.metrics import (
    compute_metric,
    aggregate_fold_metrics,
    rank_configurations,
    MetricEvaluationScope,
)

# 1. Simulação de 3 modelos avaliados em 5 folds de regressão
y_real = [np.array([10.0, 20.0, 30.0]) for _ in range(5)]
# Modelo A: 5 folds completos, RMSE médio ~1.0
preds_a = [np.array([11.0, 19.0, 31.0]) for _ in range(5)]
# Modelo B: 4 folds completos muito bons (~0.2), 1 fold com falha (NaN)
preds_b = [np.array([10.2, 19.8, 30.1]) for _ in range(4)] + [np.array([10.0, 20.0, 30.0])]

folds_a = [compute_metric("rmse", y_real[i], preds_a[i], scope=MetricEvaluationScope.PER_FOLD) for i in range(5)]
folds_b = [compute_metric("rmse", y_real[i], preds_b[i], scope=MetricEvaluationScope.PER_FOLD) for i in range(4)]
# Adiciona 1 fold indefinido (simulando variância nula do preditor em r2 ou resíduo inválido)
from experimental_ml.metrics import MetricValue
from experimental_ml.core import MetricStatus, MetricDirection
folds_b.append(MetricValue("rmse", float("nan"), MetricStatus.UNDEFINED_NAN, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 3, ()))

agg_a = aggregate_fold_metrics(folds_a)
agg_b = aggregate_fold_metrics(folds_b)

assert agg_a.status == MetricStatus.VALID
assert agg_b.status == MetricStatus.PARTIAL_COVERAGE

# 2. Ranqueamento das configurações
cands = {"modelo_completo": agg_a, "modelo_instavel": agg_b}
res = rank_configurations(cands)

# Modelo completo DEVE preceder modelo instável apesar do menor erro médio do modelo instável
assert res[0].candidate_id == "modelo_completo"
assert res[0].rank == 1
assert res[1].candidate_id == "modelo_instavel"
assert res[1].rank == 2

print("✓ CENÁRIO INTEGRADO DO M1.3 EXECUTADO COM 100% DE SUCESSO!")
EOF
```

- **Resultado Esperado:** Mensagem `✓ CENÁRIO INTEGRADO DO M1.3 EXECUTADO COM 100% DE SUCESSO!` e código de saída 0.
- **Critério de Falha:** Qualquer exceção disparada ou violação da precedência de `VALID` sobre `PARTIAL_COVERAGE`.

---

## 4. Matriz de Critérios de Aprovação do Marco M1.3

| Item | Descrição do Teste | Tipo | Responsável | Critério de Aceite |
| :--- | :--- | :--- | :--- | :--- |
| **AC-M1.3-1** | Catálogo `METRICS_CATALOG` com as 15 métricas | Funcional / Catálogo | Consumidor | 15 especificações presentes com direções e metadados corretos |
| **AC-M1.3-2** | Escopos tipados e imutabilidade das estruturas | Tipagem / Robustez | Consumidor | Dataclasses congeladas e rejeição de escopos arbitrários |
| **AC-M1.3-3** | Erros de escala direta (`mae`, `rmse`, `mbe`) | Algorítmico / Regressão | Consumidor | Dupla precisão `1e-12`, homocedasticidade e sinal assinado em `mbe` |
| **AC-M1.3-4** | Razões adimensionais e KTA | Algorítmico / Regressão | Consumidor | `UNDEFINED_NAN` em $n < 2$, variância zero, alvos nulos e normas de Gram nulas |
| **AC-M1.3-5** | Classificação discreta por classe (`precision`, `recall`, `f1`, `balanced_accuracy`) | Algorítmico / Classificação | Consumidor | Regras individuais por classe sem coerção indevida para zero |
| **AC-M1.3-6** | Classificação probabilística (`roc_auc`, `log_loss`) | Algorítmico / Probabilidade | Consumidor | Empates exatos via postos médios, OVR e clipping $\epsilon = 10^{-15}$ |
| **AC-M1.3-7** | Comparador `is_better` e ranqueamento | Governança / ADR-005 | Consumidor | `compare_by_abs` em `mbe`, `VALID` precede `PARTIAL`, `UNRANKABLE` ao final |
| **AC-M1.3-8** | Suíte unitária `tests/unit/test_metrics.py` | Automatizado | Runner / Pytest | 100% de aprovação nos 22 checks `C1` a `C22` |
| **AC-M1.3-9** | Suíte geral de regressão (`pytest tests/`) | Regressão | Runner / Pytest | 100% de aprovação (smoke + core + metrics) |
| **AC-M1.3-10**| Portão TLC (`validate_verification.py`) | Verificação Mecânica | Agente Verificador | 0 erros, 0 avisos |

---

## 5. Homologação Manual do Marco M1.3

- **Data da Homologação:** 03 de Novembro de 2026
- **Status:** **HOMOLOGADO E APROVADO**
- **Manifestação Formal do Usuário:** *"O M1.3 — Metrics foi formalmente aprovado na homologação manual."*
- **Conclusão:** Roteiro de aceitação do consumidor cumprido em sua totalidade (seções 2.1 a 3), com comportamento verificado nas 15 métricas, agregação e ranqueamento ADR-005. Marco aprovado para encerramento.


