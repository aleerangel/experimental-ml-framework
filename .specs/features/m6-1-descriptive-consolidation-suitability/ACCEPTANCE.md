# Roteiro de Validação e Aceitação — Sub-marco M6.1 (Consolidação Descritiva e Adequação Metodológica)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M6.1 (`m6-1-descriptive-consolidation-suitability`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e integradores do subsistema de estatística do `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.statistics`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e as exportações do módulo de estatística estão íntegras:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de exportações dos símbolos públicos de statistics
python -c "
import experimental_ml.statistics as stats
print('Statistics exportacoes publicas:', len(stats.__all__))
for sym in [
    'CoverageStatus', 'IncompleteComparisonPolicy', 'ApplicabilityStatus',
    'AggregatedMetricStats', 'AggregatedTimingStats', 'ConfigurationSummary',
    'DescriptiveConsolidation', 'ApplicableMethod', 'MethodSuitabilityReport',
    'validate_stage5_entry', 'consolidate_descriptive',
    'evaluate_method_suitability', 'check_pairwise_comparison_eligibility',
]:
    assert sym in stats.__all__, f'Simbolo ausente: {sym}'
print('Simbolos publicos de statistics validados com sucesso!')
"

# 3. Verificação de pureza de runtime (XCUT-02: zero dependências externas alem de numpy)
python -c "
import sys
import experimental_ml.statistics
forbidden = ['scipy', 'pandas', 'sklearn', 'torch', 'matplotlib', 'seaborn', 'joblib']
loaded = [p for p in forbidden if any(m.startswith(p) for m in sys.modules)]
assert not loaded, f'Dependencias externas proibidas carregadas: {loaded}'
print('Pureza de runtime validada com sucesso (XCUT-02)!')
"
```

---

## 2. Roteiro de Validação por Capacidade

### 2.1 Enums e Tipos Imutáveis (`STAT-01`)

```python
from experimental_ml.statistics import (
    CoverageStatus,
    IncompleteComparisonPolicy,
    ApplicabilityStatus,
    AggregatedMetricStats,
    AggregatedTimingStats,
    ConfigurationSummary,
    DescriptiveConsolidation,
)
from experimental_ml.core.enums import MetricStatus
from dataclasses import FrozenInstanceError

# 1. Enums
assert CoverageStatus.VALID == "VALID"
assert CoverageStatus.PARTIAL_COVERAGE == "PARTIAL_COVERAGE"
assert CoverageStatus.NO_COVERAGE == "NO_COVERAGE"

assert IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY == "STRICT_COMPLETE_ONLY"
assert IncompleteComparisonPolicy.ALLOW_COMMON_SUBSET == "ALLOW_COMMON_SUBSET"

assert ApplicabilityStatus.APPLICABLE == "APPLICABLE"
assert ApplicabilityStatus.NOT_SUITABLE == "NOT_SUITABLE"

# 2. Imutabilidade
stats = AggregatedMetricStats(
    n_valid=3,
    n_total=5,
    status=MetricStatus.PARTIAL_COVERAGE,
    mean=0.25,
    std=0.02,
    median=0.25,
    iqr=0.01,
)
try:
    stats.mean = 0.50
    assert False, "Deveria ter levantado FrozenInstanceError"
except FrozenInstanceError:
    pass
print("Capacidade 2.1 aprovada!")
```

### 2.2 Portão de Validação de Entrada da Etapa 5 (`STAT-02`, `CA-E5-01`)

```python
from experimental_ml.statistics import validate_stage5_entry
from experimental_ml.core.findings import ContractViolationError

# 1. Bloqueio de células não-terminais ativas (PENDING / RUNNING)
state_pending = {
    "experiment_id": "exp_01",
    "run_id": "run_01",
    "created_at": "2026-11-16T12:00:00Z",
    "updated_at": "2026-11-16T12:01:00Z",
    "master_seed": 42,
    "total_cells": 2,
    "cell_statuses": {"cell_0": "COMPLETED", "cell_1": "PENDING"},
}
try:
    validate_stage5_entry(state_pending)
    assert False, "Deveria bloquear células em PENDING"
except ContractViolationError:
    pass

# 2. Bloqueio quando completed_cells == 0
state_zero = {
    "experiment_id": "exp_01",
    "run_id": "run_01",
    "created_at": "2026-11-16T12:00:00Z",
    "updated_at": "2026-11-16T12:01:00Z",
    "master_seed": 42,
    "total_cells": 2,
    "cell_statuses": {"cell_0": "FAILED", "cell_1": "CANCELLED"},
}
try:
    validate_stage5_entry(state_zero)
    assert False, "Deveria bloquear execução com zero completed_cells"
except ContractViolationError:
    pass

# 3. Liberação para estados terminais com completed_cells >= 1
state_valid = {
    "experiment_id": "exp_01",
    "run_id": "run_01",
    "created_at": "2026-11-16T12:00:00Z",
    "updated_at": "2026-11-16T12:01:00Z",
    "master_seed": 42,
    "total_cells": 3,
    "cell_statuses": {"cell_0": "COMPLETED", "cell_1": "FAILED", "cell_2": "CANCELLED"},
}
assert validate_stage5_entry(state_valid) is None
print("Capacidade 2.2 aprovada!")
```

### 2.3 Consolidação Descritiva e Rastreamento de Cobertura (`STAT-03`)

```python
from experimental_ml.statistics import consolidate_descriptive, CoverageStatus
from experimental_ml.orchestration.types import CellResultRecord, TimingBreakdown
from experimental_ml.core.types import CellId, ExperimentId, PartitionPlanId
from experimental_ml.metrics.types import MetricValue, MetricEvaluationScope
from experimental_ml.core.enums import MetricStatus, MetricDirection, ExecutionStatus

cells = [
    CellResultRecord(
        cell_id=CellId("c0"),
        experiment_id=ExperimentId("e"),
        partition_plan_id=PartitionPlanId("p"),
        model_id="ridge",
        scenario_id="sc1",
        fold_id="fold_0",
        timing=TimingBreakdown(total_cell_time_s=1.0),
        status=ExecutionStatus.COMPLETED,
        metrics={"rmse": MetricValue("rmse", 0.20, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 20)},
    ),
    CellResultRecord(
        cell_id=CellId("c1"),
        experiment_id=ExperimentId("e"),
        partition_plan_id=PartitionPlanId("p"),
        model_id="ridge",
        scenario_id="sc1",
        fold_id="fold_1",
        timing=TimingBreakdown(total_cell_time_s=2.0),
        status=ExecutionStatus.FAILED,
    ),
]

consol = consolidate_descriptive(
    cell_results=cells,
    total_folds_per_config={("ridge", "sc1"): 2},
    experiment_id="e",
    partition_plan_id="p",
)
summary = consol.configurations[("ridge", "sc1")]
assert summary.coverage == 0.5
assert summary.coverage_status == CoverageStatus.PARTIAL_COVERAGE
assert summary.completed_fold_ids == ("fold_0",)
assert summary.failed_fold_ids == ("fold_1",)
assert summary.aggregated_metrics["rmse"].mean == 0.20
assert summary.aggregated_metrics["rmse"].std is None  # n_valid == 1 -> std is None sem zero artificial
print("Capacidade 2.3 aprovada!")
```

### 2.4 Adequação Metodológica e Incompletude (`STAT-04`, `CA-E5-01`)

```python
from experimental_ml.statistics import (
    evaluate_method_suitability,
    check_pairwise_comparison_eligibility,
    IncompleteComparisonPolicy,
    ApplicabilityStatus,
)
from experimental_ml.validation.types import PartitionPlan, EvaluationRegime, PartitionStrategy, PartitionConfig, FoldPartition
from experimental_ml.core.types import ObservationId

folds = tuple(
    FoldPartition(
        fold_index=i,
        train_ids=tuple(ObservationId(f"tr_{k}") for k in range(80)),
        val_ids=tuple(ObservationId(f"val_{k}") for k in range(20)),
    )
    for i in range(5)
)
plan = PartitionPlan(
    plan_id="p",
    source_dataset_hash="h",
    regime=EvaluationRegime.CV_ONLY,
    strategy=PartitionStrategy.KFOLD,
    development_ids=tuple(ObservationId(f"id_{k}") for k in range(100)),
    holdout_ids=(),
    folds=folds,
    config=PartitionConfig(PartitionStrategy.KFOLD, 5, EvaluationRegime.CV_ONLY),
)

suitability = evaluate_method_suitability(plan)
assert suitability.mean_train_overlap_ratio == 0.25  # 20/80
assert suitability.applicable_methods["nadeau_bengio_paired_t"].status == ApplicabilityStatus.APPLICABLE
assert suitability.applicable_methods["wilcoxon_signed_rank_paired"].status == ApplicabilityStatus.APPLICABLE
assert len(suitability.applicable_methods["wilcoxon_signed_rank_paired"].warnings) >= 1  # Alerta J < 6
assert suitability.applicable_methods["paired_t_test_uncorrected"].status == ApplicabilityStatus.NOT_SUITABLE
print("Capacidade 2.4 aprovada!")
```
