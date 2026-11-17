# Tutorial Metodológico das 6 Etapas

O `experimental-ml` estrutura todo experimento científico em **6 etapas metodológicas oficiais**, separadas por **portões de estágio (*stage gates*)** e contratos imutáveis que garantem isolamento estrito contra *data leakage* (vazamento de dados) e reprodutibilidade determinística.

```mermaid
flowchart LR
    E1["Etapa 1<br/>Entrada, Triagem e<br/>Diagnóstico"] --> E2["Etapa 2<br/>Exploração e Cenários<br/>de Features"]
    E2 --> E3["Etapa 3<br/>Modelos, Pré-proc. e<br/>Nested Tuning"]
    E3 --> E4["Etapa 4<br/>4A: Particionamento<br/>4B: Execução Matricial"]
    E4 --> E5["Etapa 5<br/>Consolidação e<br/>Inferência Estatística"]
    E5 --> E6["Etapa 6<br/>Relatórios, Figuras e<br/>Reprodutibilidade"]
```

---

## Etapa 1: Entrada, Triagem e Diagnóstico Estrutural

**Módulos:** `experimental_ml.data`, `experimental_ml.stages`  
**Portão:** `verify_preparation_gate`

A primeira etapa protege a integridade da base bruta antes de qualquer divisão ou modelagem:
- **Imutabilidade e Hashes Tripartites:** `load_dataset` ingere o conjunto tabular em um `DatasetBundle` imutável, gerando identificadores estáveis (`ObservationId`) e hashes SHA-256 independentes para fonte bruta (`raw_source_hash`), esquema (`schema_hash`) e dados (`dataset_hash`).
- **Diagnóstico Estrutural:** `profile_dataset` audita tipos semânticos, valores ausentes, colunas constantes e inconsistências de alvo.
- **Saneamento Pré-Partição:** Regras determinísticas independentes da distribuição (como remoção de linhas com alvo ausente) são declaradas em um `PreparationPlan` e materializadas em uma `SanitizedDatasetView` via `sanitize_dataset`, sem jamais alterar os dados brutos.

```bash
expml data profile --input dados.csv --target alvo --task binary_classification --output-dir exp_dir
expml data sanitize --exp-dir exp_dir --allow-unresolved
```

---

## Etapa 2: Exploração de Relações e Cenários de Features

**Módulos:** `experimental_ml.features`, `experimental_ml.stages`  
**Portão:** `verify_scenarios_gate`

Para evitar que a escolha de atributos vaze informações da validação:
- **Rotulagem Exploratória Obrigatória:** `explore_features` calcula correlações univariadas (Pearson, Spearman, $\eta$ e V de Cramér) e matriz de redundância sob o rótulo explícito `EXPLORATORY_FULL_DATA`, acompanhado de alertas metodológicos sobre o risco de usar essa análise para seleção definitiva.
- **Cenários Fixos vs. Dinâmicos:** `FeatureScenario` distingue conjuntos previamente justificados na literatura (`ScenarioMode.FIXED`) de estratégias de seleção executadas estritamente dentro de cada dobra de treino (`ScenarioMode.DYNAMIC`, ex.: `VARIANCE_THRESHOLD`, `TOP_K_RELEVANCE`), avaliando sua estabilidade inter-dobras pelos índices de Jaccard e Kuncheva corrigido (`compute_selection_stability`).

```bash
expml features explore --exp-dir exp_dir
expml features scenarios --exp-dir exp_dir --scenarios-json cenarios.json
expml features verify --exp-dir exp_dir
```

---

## Etapa 3: Registro de Modelos, Pré-processamento em 2 Camadas e Nested Tuning

**Módulos:** `experimental_ml.models`, `experimental_ml.tuning`, `experimental_ml.stages`  
**Portão:** `verify_models_gate`

Esta etapa formaliza os modelos candidatos e suas restrições operacionais antes da execução:
- **Capacidades Declarativas:** `ModelSpec` e `ModelCapabilities` explicitam se o modelo requer ajuste (`requires_fit`), suporta probabilidades (`supports_predict_proba`), pesos amostrais (`supports_sample_weight`) ou kernels pré-computados (`supports_precomputed_kernel`).
- **Pré-processamento em 2 Camadas sem Duplicação:** A camada de cenário (Etapa 2) e a camada do modelo (Etapa 3) são validadas em conjunto por `validate_two_layer_preprocessing` para impedir transformações redundantes (como padronização dupla) e ajustadas estritamente no treino de cada dobra.
- **Nested Tuning (Busca Aninhada):** `HyperparameterSearchSpec` e `run_nested_tuning` (`grid_search` ou `random_search`) subdividem exclusivamente $(X_{\text{train}}, y_{\text{train}})$ da dobra externa, garantindo que o conjunto de validação externo nunca influencie a escolha de hiperparâmetros $\theta^*$.

```bash
expml models validate --exp-dir exp_dir --models-json modelos.json
expml models verify --exp-dir exp_dir
```

---

## Etapa 4: Particionamento Compartilhado (4A) e Execução Matricial (4B)

**Módulos:** `experimental_ml.validation`, `experimental_ml.orchestration`, `experimental_ml.stages`  
**Portões:** `verify_partition_gate`, `verify_runs_gate`

A Etapa 4 é composta por dois subestágios acoplados por contrato:

### Subetapa 4A — Particionamento Compartilhado (`validation`)
Todos os modelos e cenários competem sobre **exatamente os mesmos subconjuntos de observações** definidos em um único `PartitionPlan` (`build_partition_plan`, `validate_partition_plan`). O framework suporta:
- Regimes `CV_ONLY`, `HOLDOUT_ONLY` e `CV_AND_HOLDOUT`;
- Estratégias `KFOLD`, `STRATIFIED_KFOLD`, `GROUP_KFOLD` (isolamento estrito de grupos entre dobras e entre desenvolvimento e holdout) e `TEMPORAL`.

### Subetapa 4B — Execução Matricial Tolerante a Falhas (`orchestration`)
Para cada célula $(m, c, f)$ da matriz `(modelo × cenário × dobra)`:
1. `instantiate_fresh_model` cria uma instância virgem com os parâmetros declarados (ou $\theta^*$ do *nested tuning*);
2. Seleção dinâmica, pré-processamento e ajuste ocorrem **unicamente** em $X_{\text{train}}$;
3. Em modo `FAULT_TOLERANT`, falhas pontuais registram a célula como `FAILED` preservando o estado das demais; métricas indefinidas recebem `MetricStatus.UNDEFINED_NAN` e **nunca** são convertidas silenciosamente para zero;
4. O progresso é salvo atomicamente em disco, permitindo retomada via `resume_experiment_matrix` com verificação de compatibilidade de `dataset_hash` e `partition_plan_id`.

```bash
expml partition build --exp-dir exp_dir --strategy stratified_kfold --n-splits 5 --seed 42
expml run start --exp-dir exp_dir --metrics accuracy f1 roc_auc
expml run verify --exp-dir exp_dir
```

---

## Etapa 5: Consolidação e Comparação Estatística Rigorosa

**Módulos:** `experimental_ml.statistics`, `experimental_ml.stages`  
**Portão:** `verify_statistics_gate`

A análise estatística consome os registros de `runs/` e `predictions/` de forma desacoplada:
- **Consolidação Descritiva e Cobertura:** `consolidate_descriptive` calcula médias, desvios, medianas e intervalos interquartis apenas sobre dobras válidas, classificando cada configuração em `VALID`, `PARTIAL_COVERAGE` ou `NO_COVERAGE`. Líderes `VALID` têm precedência sobre configurações com cobertura parcial (`ADR-005`).
- **Inferência Pareada com Correção de Variância:** Em validação cruzada com $K$ dobras, as partições de treino se sobrepõem, violando a independência do teste *t* clássico. O framework implementa o teste corrigido de **Nadeau-Bengio**:

$$
t_{\text{NB}} = \frac{\bar{d}}{\sqrt{\left(\frac{1}{K} + \frac{n_{\text{test}}}{n_{\text{train}}}\right) s_d^2}}
$$

- **Alternativa Não-Paramétrica e Multiplicidade:** Oferece `paired_wilcoxon_test`, tamanho de efeito ($d$ de Cohen pareado) e correções para múltiplas comparações via Holm-Bonferroni (`adjust_pvalues_holm`) e Benjamini-Hochberg (`adjust_pvalues_bh`).
- **Análise Multiobjetivo e Síntese:** `compute_pareto_frontier` identifica configurações não dominadas combinando métricas preditivas, tempo de inferência e estabilidade de seleção, enquanto `synthesize_conclusions` gera conclusões estruturadas evitando confundir $p \ge \alpha$ com equivalência.

```bash
expml stats run --exp-dir exp_dir --primary-metric accuracy --alpha 0.05
expml stats verify --exp-dir exp_dir
```

---

## Etapa 6: Relatórios Científicos, Figuras e Pacote de Reprodutibilidade

**Módulos:** `experimental_ml.reporting`, `experimental_ml.stages`  
**Portão:** `verify_report_gate`

A última etapa opera em modo estritamente somente-leitura sobre os artefatos persistidos (sem retreinar ou recalcular métricas ocultamente):
- **Relatórios e Tabelas:** Gera relatórios offline completos em Markdown e HTML (`render_full_report`) e 7 famílias de tabelas científicas exportáveis em `CSV`, `Markdown` e `LaTeX booktabs` (`build_table_model`).
- **Figuras Determinísticas:** Renderiza gráficos vetoriais e matriciais (`SVG`, `PNG` 300 DPI, `PDF`) em Python/NumPy puro.
- **Pacote Portátil de Reprodutibilidade:** `build_reproducibility_package` empacota artefatos, linhagem (`artifact_provenance.json`), ambiente (`environment.json`), sementes (`seeds.json`) e hashes relativos POSIX em `reproducibility/checksums.sha256`, nos modos `FULL_PACKAGE` (com dados) ou `REDUCED_NO_RAW_DATA` (sem dados brutos para revisão cega ou restrições de privacidade).

```bash
expml report generate --exp-dir exp_dir --format both
expml report export --exp-dir exp_dir --mode REDUCED_NO_RAW_DATA --output-dir pacote_submissao
expml report verify --exp-dir exp_dir
```
