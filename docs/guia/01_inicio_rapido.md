# Início Rápido: Básico vs. Controle Granular *(Nível 1)*

Este guia mostra os dois modos de operar o `experimental-ml`: o **Modo Básico** (mínimo necessário para rodar um experimento completo) e o **Modo Granular / Avançado** (controle explícito etapa por etapa).

---

## Parte 1 — Modo Básico *(O Mínimo Necessário)*

### Instalação
```bash
pip install -e .
expml --version
```

### Pelo Terminal (2 Comandos)
```bash
expml init --output-dir exp_demo --task binary_classification
expml quickrun --experiment-dir exp_demo
```

### Por Python (Chamada Única)
Para um experimento padrão com 3 modelos, semente determinística e métricas personalizadas, basta passar um dicionário de modelos para `run_experiment` (veja os detalhes passo a passo em [Começando do Zero](00_comecando_do_zero.md)).

---

## Quando Migrar do Modo Básico para o Controle Granular (Avançado)?

| Necessidade do Seu Projeto | Use o Modo Básico (`run_experiment` / `quickrun`) | Migre para o Controle Granular (Parte 2) |
| :--- | :---: | :---: |
| Comparar modelos em `KFold` / `StratifiedKFold` / `GroupKFold` | Sim | Opcional |
| Definir seleção dinâmica intra-fold (`TOP_K_RELEVANCE`) e pré-processamento em 2 camadas | — | **Sim** |
| Configurar busca aninhada de hiperparâmetros (*Nested CV*) | — | **Sim** |
| Retomar execuções longas interrompidas (`expml run resume`) | — | **Sim** |
| Exportar tabelas `LaTeX`, figuras `SVG` e pacote hermético SHA-256 (`expml report export`) | — | **Sim** |

---

## Parte 2 — Controle Granular Etapa por Etapa *(Avançado)*

### Fluxo na CLI `expml`
> Antes de executar os comandos abaixo manualmente, use `expml init` para gerar os arquivos JSON ou consulte [Schemas JSON da CLI](../referencia/cli_schemas_json.md).

```bash
# Etapa 1: Diagnóstico e saneamento (--rules é opcional se não houver achados críticos)
expml data profile --data dados.csv --schema schema.json --output-dir exp_demo
expml data sanitize --experiment-dir exp_demo

# Etapas 2, 3 e 4A: Exploração, cenários, modelos e partições
expml features explore --experiment-dir exp_demo
expml features scenarios --experiment-dir exp_demo --scenarios scenarios.json
expml models validate --experiment-dir exp_demo --models models.json
expml partition build --experiment-dir exp_demo --config partition.json --seed 42

# Etapas 4B, 5 e 6: Execução, estatística e pacote de reprodutibilidade
expml run start --experiment-dir exp_demo --error-policy fault_tolerant --metrics accuracy f1
expml stats run --experiment-dir exp_demo
expml report generate --experiment-dir exp_demo --format both --audience FULL_LAB
expml report export --experiment-dir exp_demo --mode full_package --output-dir pacote_final
expml report verify --experiment-dir pacote_final
```

### Exemplo Completo Granular em Python *(Smoke Test)*

Quando precisar controlar cada estrutura declarativa em Python (`DatasetSchemaSpec`, `FeatureScenario`, `ModelSpec`, `PartitionPlan`, `run_experiment_matrix`):

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

- Para entender cada uma das 6 etapas (com o que é básico vs. avançado em cada uma), siga para o [Tutorial Passo a Passo das 6 Etapas](02_tutorial_6_etapas.md).
- Para interpretar métricas, testes pareados e gerar citações para seu artigo/TCC, veja [Interpretando Resultados Científicos](03_interpretando_resultados.md).
