# Início Rápido em 5 Passos

Este guia mostra como instalar o `experimental-ml` e conduzir seu primeiro experimento científico reprodutível em **5 passos operacionais**, tanto pela interface de linha de comando (`expml`) quanto pela API Python pura.

---

## Passo 1: Instalação

O framework possui núcleo em Python padrão e `numpy` (`XCUT-02`), sem dependências pesadas obrigatórias em runtime. Instale em ambiente virtual ativo:

```bash
pip install -e .
expml --version
```

---

## Passo 2: Preparação e Diagnóstico dos Dados (Etapa 1)

Gere o diagnóstico estrutural da base (`profile`) e aplique um plano de saneamento (`sanitize`) preservando os dados originais imutáveis:

```bash
expml data profile --input dados.csv --target alvo --task binary_classification --output-dir exp_demo
expml data sanitize --exp-dir exp_demo --allow-unresolved
```

---

## Passo 3: Particionamento, Features e Modelos (Etapas 2, 3 e 4A)

Defina os cenários de atributos, valide o catálogo de modelos e gere o plano de particionamento compartilhado (com semente determinística):

```bash
expml features scenarios --exp-dir exp_demo --scenarios-json cenarios.json
expml models validate --exp-dir exp_demo --models-json modelos.json
expml partition build --exp-dir exp_demo --strategy stratified_kfold --n-splits 5 --seed 42
```

---

## Passo 4: Execução Matricial e Consolidação Estatística (Etapas 4B e 5)

Execute toda a matriz `(modelo x cenário x fold)` em modo tolerante a falhas e rode a consolidação descritiva e inferência estatística:

```bash
expml run start --exp-dir exp_demo --metrics accuracy f1
expml stats run --exp-dir exp_demo --primary-metric accuracy
```

---

## Passo 5: Relatório Científico e Pacote de Reprodutibilidade (Etapa 6)

Gere o relatório offline (`Markdown`/`HTML`), tabelas (`CSV`/`LaTeX`) e o pacote portátil auditável por checksums SHA-256:

```bash
expml report generate --exp-dir exp_demo --format both
expml report export --exp-dir exp_demo --mode FULL_PACKAGE --output-dir pacote_final
expml report verify --exp-dir exp_demo
```

---

## Exemplo Completo Executável em Python (Smoke Test)

O script abaixo executa todo o fluxo científico em memória/disco temporário utilizando apenas a API pública do framework:

```python
# executable-smoke-test
from pathlib import Path
import numpy as np

from experimental_ml.core.enums import TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features import FeatureScenario, ScenarioMode
from experimental_ml.models import (
    DummyBaselineModel,
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
)
from experimental_ml.orchestration import load_cell_artifacts, run_experiment_matrix
from experimental_ml.statistics import consolidate_descriptive
from experimental_ml.validation import (
    EvaluationRegime,
    PartitionConfig,
    PartitionStrategy,
    build_partition_plan,
)

work_dir = Path(globals().get("SMOKE_TMP_DIR", Path("./exp_quickstart_tmp")))
work_dir.mkdir(parents=True, exist_ok=True)

# 1. Dados tabulares sintéticos (30 amostras, 2 features numéricas, alvo binário)
rng = np.random.default_rng(42)
raw_data = {
    "x1": rng.normal(0.0, 1.0, size=30).tolist(),
    "x2": rng.normal(1.0, 0.5, size=30).tolist(),
    "alvo": [0 if i < 15 else 1 for i in range(30)],
}
schema = DatasetSchemaSpec(target_col="alvo", task_type=TaskType.BINARY_CLASSIFICATION)
bundle = load_dataset(raw_data, schema)

# 2. Etapa 1: Diagnóstico e saneamento determinístico
profile = profile_dataset(bundle)
prep_plan = create_preparation_plan(profile, rules=[])
view = sanitize_dataset(bundle, profile, prep_plan)

# 3. Etapa 2 e Etapa 3: Cenário de features e especificação de modelo baseline
scenario = FeatureScenario(
    scenario_id="todas_features",
    name="Todas as Features",
    description="Conjunto completo de preditores numéricos",
    scientific_justification="Baseline inicial sem seleção",
    mode=ScenarioMode.FIXED,
    selected_features=("x1", "x2"),
)
model_spec = ModelSpec(
    model_id="baseline_freq",
    display_name="Dummy Most Frequent",
    family=ModelFamily.BASELINE,
    estimator_factory=lambda seed=None: DummyBaselineModel(strategy="most_frequent"),
    capabilities=ModelCapabilities(supports_predict_proba=True),
    description="Baseline majoritário determinístico",
    scientific_justification="Referência mínima de classificação",
)

# 4. Etapa 4: Particionamento (4A) e Execução Matricial (4B)
part_config = PartitionConfig(
    strategy=PartitionStrategy.STRATIFIED_KFOLD,
    regime=EvaluationRegime.CV_ONLY,
    n_splits=3,
    master_seed=42,
)
partition_plan = build_partition_plan(view, part_config)
run_state = run_experiment_matrix(
    model_specs=[model_spec],
    scenarios=[scenario],
    partition_plan=partition_plan,
    sanitized_view=view,
    run_dir=work_dir / "runs",
    metrics=("accuracy", "f1"),
    master_seed=42,
    overwrite=True,
)

# 5. Etapa 5: Consolidação descritiva sem coerção silenciosa
cell_results = [
    load_cell_artifacts(cid, work_dir / "runs")[0]
    for cid in run_state.cell_statuses
]
consolidation = consolidate_descriptive(
    cell_results,
    total_folds_per_config=len(partition_plan.folds),
)
assert len(consolidation.configurations) == 1
```

---

## Próximos Passos

- Para dominar os fundamentos teóricos, portões de estágio e prevenção de *data leakage*, siga para o [Tutorial Passo a Passo das 6 Etapas](02_tutorial_6_etapas.md).
- Para cenários avançados, consulte o [Scientific Cookbook](../cookbook/01_modelos_analiticos_vs_treinados.md).
