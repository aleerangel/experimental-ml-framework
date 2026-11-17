# Guia Prático 3: Validação Cruzada Agrupada (`GroupKFold`) com Isolamento Estrito de Holdout

## Contexto Científico

Em estudos longitudinais, clínicos ou biométricos, múltiplas amostras (exames, sessões, medições temporais) pertencem a um mesmo sujeito ou paciente (`group_col`). Se observações de um mesmo indivíduo forem distribuídas entre treino e validação ou entre desenvolvimento e *holdout*, o modelo memorizará características do indivíduo, inflando artificialmente as métricas (*subject leakage*).

O `experimental-ml` garante matematicamente o isolamento completo em dois níveis quando configurado com `PartitionStrategy.GROUP_KFOLD` e `EvaluationRegime.CV_AND_HOLDOUT`:
1. **Isolamento Desenvolvimento ↔ Holdout:** Grupos inteiros são permutados e alocados ao *holdout*; nenhuma observação de um grupo presente no *holdout* entra no conjunto de desenvolvimento;
2. **Isolamento Treino ↔ Validação em cada Dobra:** `group_kfold_split` distribui os grupos restantes entre as $K$ dobras com balanceamento guloso (*bin-packing*), assegurando conjuntos disjuntos de grupos em cada dobra;
3. **Auditoria Matemática:** `validate_partition_plan` verifica ambas as propriedades de disjunção e bloqueia o fluxo se houver qualquer sobreposição.

---

## Implementação via Python

```python
from experimental_ml.core.enums import TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.validation import (
    EvaluationRegime,
    PartitionConfig,
    PartitionStrategy,
    build_partition_plan,
    validate_partition_plan,
)

# 1. Base sintética com 6 pacientes (P1..P6), 3 medições por paciente
dados = {
    "paciente_id": [f"P{g}" for g in range(1, 7) for _ in range(3)],
    "biomarcador_a": [float(i) * 0.1 for i in range(18)],
    "biomarcador_b": [float(18 - i) * 0.2 for i in range(18)],
    "diagnostico": [0 if g <= 3 else 1 for g in range(1, 7) for _ in range(3)],
}

schema = DatasetSchemaSpec(
    target_col="diagnostico",
    task_type=TaskType.BINARY_CLASSIFICATION,
    group_col="paciente_id",
)
bundle = load_dataset(dados, schema)
profile = profile_dataset(bundle)
plan = create_preparation_plan(profile, rules=[])
view = sanitize_dataset(bundle, profile, plan)

# 2. Configuração GroupKFold com Holdout isolado por grupo
config = PartitionConfig(
    strategy=PartitionStrategy.GROUP_KFOLD,
    regime=EvaluationRegime.CV_AND_HOLDOUT,
    n_splits=3,
    holdout_fraction=0.33,
    group_col="paciente_id",
    master_seed=42,
)

partition_plan = build_partition_plan(view, config)
validate_partition_plan(partition_plan, view)

# Verificando isolamento estrito entre desenvolvimento e holdout
assert set(partition_plan.development_ids).isdisjoint(set(partition_plan.holdout_ids))
```

---

## Fluxo Equivalente via CLI

```bash
expml data profile --input clinico.csv --target diagnostico --group-col paciente_id --task binary_classification --output-dir exp_clinico
expml data sanitize --exp-dir exp_clinico --allow-unresolved
expml partition build --exp-dir exp_clinico --strategy group_kfold --regime cv_and_holdout --group-col paciente_id --n-splits 3 --holdout-fraction 0.33 --seed 42
expml partition verify --exp-dir exp_clinico
```
