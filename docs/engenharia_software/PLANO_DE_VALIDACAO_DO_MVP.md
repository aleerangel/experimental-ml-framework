# Plano e Roteiro Prático de Validação do MVP

**Data:** 27 de Novembro de 2026  
**Escopo:** Roteiro executável de validação funcional, metodológica, de integração, de robustez e exploratória do `experimental-ml-framework` (estado pós-`M8`, `M9` e `M10`).  
**Documentos correlatos:** [AUDITORIA_TECNICA_DO_MVP.md](./AUDITORIA_TECNICA_DO_MVP.md) | [REGISTRO_DE_VALIDACAO_DO_MVP.md](./REGISTRO_DE_VALIDACAO_DO_MVP.md) | [ROADMAP_EVOLUCAO.md](./ROADMAP_EVOLUCAO.md)

---

## 1. Avaliação do Escopo Implementado e Estratégia de Validação

O `experimental-ml-framework` possui **632 testes automatizados** (`pytest tests/`) que cobrem a integridade algorítmica dos módulos, contratos intra-fold (`M9`), preparação tabular e visualização científica via Matplotlib/Pandas (`M10`), hashes determinísticos e fluxos ponta a ponta. Entretanto, a validação prática do pesquisador sobre dados reais continua essencial para inspecionar:

1. **Desconexões de schema entre etapas** (como `VAL-BUG-002` na Tabela A e `VAL-BUG-003` na Tabela G).
2. **Qualidade visual e legibilidade humana** das figuras geradas nas Etapas 2 e 6 (`VAL-BUG-006`, `VAL-QUAL-001`).
3. **Combinações específicas de configurações** (como `DEFER_INTRA_FOLD` em `VAL-BUG-001`, `DYNAMIC` + Nested CV em `VAL-BUG-005`, ou `CV_AND_HOLDOUT` em `VAL-BUG-008`).
4. **Interoperabilidade entre a fachada Python (`run_experiment`) e os subcomandos da CLI (`expml`)** (`VAL-BUG-007`).

Este plano organiza os testes de validação do desenvolvedor em cinco baterias complementares, priorizadas em:
- **`P0` (Crítico):** Valida garantias metodológicas centrais (anti-vazamento, determinismo, métricas, testes estatísticos) e fluxos onde a auditoria identificou falhas bloqueantes.
- **`P1` (Importante):** Valida fluxos completos por etapa, regimes avançados de particionamento, tuning, relatórios e interoperabilidade API/CLI.
- **`P2` (Desejável):** Valida casos de borda, recuperação de falhas, mensagens de erro e ergonomia.

---

## 2. Matriz de Testes Funcionais (`TV-F01` a `TV-F12`)

| ID | Módulo / Funcionalidade | Objetivo do Teste | Procedimento de Execução | Dados / Configurações Necessários | Resultado Esperado | Evidência a Coletar | Prioridade | Cobertura Atual |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **`TV-F01`** | Etapa 1 (`data/ingestion.py`) | Validar ingestão de CSV padrão e CSV regional brasileiro (`;`, decimal `,`, milhar `.`). | Executar `read_csv_dataset` via Python ou `expml data profile` em arquivo CSV com formato brasileiro e `CSVFormatConfig(delimiter=";", decimal=",", thousands=".")`. | CSV com 50 linhas, separador `;`, floats no formato `1.234,56` e encoding `utf-8` ou `latin-1`. | Matriz numérica e tipos semânticos inferidos sem perda de precisão; `dataset_hash` determinístico. | `data/dataset_descriptor.json` e `data/dataset_profile.json`. | `P0` | Automatizada (`test_csv_format.py`); validar com CSV real do pesquisador. |
| **`TV-F02`** | Etapa 1 (`data/profiling.py`, `gate.py`) | Validar detecção de achados bloqueantes e bloqueio do gate sem regra de preparação. | Rodar `expml data profile` em CSV contendo `NaN` no alvo (`E1_TARGET_MISSING`) ou coluna constante (`E1_CONSTANT_COLUMN`) e tentar rodar `expml data verify` com `preparation_plan.json` vazio (`{"rules": []}`). | CSV com 1 linha de alvo ausente e 1 coluna constante. | `expml data verify` deve falhar com código de saída `4` (`StageGateError`) listando os `finding_id`s não resolvidos. | Saída do terminal (stderr) e código de retorno `$? == 4`. | `P0` | Automatizada (`test_stage1_gate.py`). |
| **`TV-F03`** | Etapa 1 (`data/preparation.py`) | Validar regras estáticas de sanitização (`DROP_ROWS`, `EXCLUDE_COLUMN`, `CLIP_OUTLIERS`, `LOG1P_TRANSFORM`, `MAP_BINARY_TARGET`). | Configurar `preparation_plan.json` cobrindo cada tipo de regra estática, rodar `expml data sanitize` e `expml data verify`. | CSV com outliers, coluna ID monotônica e alvo binário em texto (`"Sim"`/`"Não"`). | `stage1_gate.json` com `"passed": true`, `sanitized_view.json` registrando `applied_actions` e novo `sanitized_dataset_hash`. | `data/sanitized_view.json` e `data/stage1_gate.json`. | `P1` | Automatizada (`test_data_preparation.py`). |
| **`TV-F04`** | Etapa 1→4B (`DEFER_INTRA_FOLD`) | Verificar comportamento de regras diferidas (`DEFER_INTRA_FOLD`) para missing e categóricos ao chegar na Etapa 4B. | Criar regra `DEFER_INTRA_FOLD` para `E1_FEATURE_MISSING` / `E1_CATEGORICAL_UNENCODED`, aprovar Etapa 1 e executar a matriz na Etapa 4B. | CSV com `NaN` e categóricas em texto + regra `DEFER_INTRA_FOLD`. | Imputação (`MEAN`/`MEDIAN`/`MODE`) e codificação (`ORDINAL`/`FREQUENCY`) calculadas estritamente por fold (incluindo Nested CV), sem leakage. | Log de execução da célula em `runs/execution_state.json` e `test_m9_deferred_preprocessing_e2e.py`. | `P0` | **Verificado em `M9` (`VAL-BUG-001` / `VAL-ENH-002`) — Validar em dados reais.** |
| **`TV-F05`** | Etapa 2 (`features/stats.py`, `visualization.py`) | Validar cálculo de relevância (Pearson, Spearman, MI, $\eta$, Cramér) e redundância (VIF) + geração de gráficos PNG (Matplotlib) e relatório MD/HTML. | Rodar `expml features explore --experiment-dir <dir>` ou `run_experiment` sobre base contínua e mista (incluindo categórica com `None`). | Base com atributos colineares ($X_2 \approx 2 X_1$), nomes longos com acentos UTF-8 e atributos irrelevantes. | `exploratory_features.{md,html}` ordena atributos, trata `None` em categóricas (`VAL-BUG-004`) e gera `exploratory_target.png` e `exploratory_redundancy.png` sem truncamento nem perda de acentuação. | `reports/exploratory_features.{md,html}`, `exploratory_target.png`, `exploratory_redundancy.png`. | `P0` | **Verificado em `M8` (`VAL-BUG-004`) e `M10` (`VAL-QUAL-001`) — Validar visualmente.** |
| **`TV-F06`** | Etapa 2 (`features/scenarios.py`, `selection.py`) | Validar catálogo de cenários `FIXED` e `DYNAMIC` (`TOP_K_RELEVANCE`, `CORRELATION_THRESHOLD`, `VIF_FILTER`). | Definir `scenarios.json` com 1 cenário `FIXED` e 3 cenários `DYNAMIC`, rodar `expml features scenarios` e `expml features verify`. | Catálogo `scenarios.json` com justificativas científicas preenchidas. | `features/stage2_gate.json` aprovado; na Etapa 4B, cada `cell_*.json` registra a lista exata `selected_features` escolhida no fold. | `configuration/scenarios.json`, `features/stage2_gate.json` e `runs/cells/cell_*.json`. | `P1` | Automatizada (`test_fold_selection.py`). |
| **`TV-F07`** | Etapa 3 (`models/`, `diagnostics.py`) | Validar catálogo de 11 famílias clássicas, scalers de Camada 2 (`Standard`, `MinMax`, `Robust`, `MaxAbs`, `Angular`) e extração de diagnósticos. | Configurar `models.json` com `LINEAR_REGRESSION`, `RIDGE`, `RANDOM_FOREST_REGRESSOR` (`oob_score=True`), `SVM_REGRESSOR` e `MLP_REGRESSOR` com `ANGULAR_SCALER`, rodar `expml models validate`, `verify` e executar Etapa 4B. | `models.json` com múltiplos modelos e scalers. | Cada `runs/cells/cell_*.json` deve conter `diagnostics` povoado (`coefficients`, `feature_importances`, `oob_score`, `n_support_vectors`, `loss_curve`). | Arquivos `runs/cells/cell_*.json` e `models/stage3_gate.json`. | `P1` | Automatizada (`test_model_diagnostics.py`). |
| **`TV-F08`** | Etapa 4A (`validation/partitioning.py`, `gate.py`) | Validar os 5 métodos de particionamento (`KFOLD`, `STRATIFIED_KFOLD`, `GROUP_KFOLD`, `TEMPORAL`, `REPEATED_KFOLD`) e o gate de verificação. | Gerar planos de partição para cada método via `expml partition build` e validar via `expml partition verify`. | Datasets com coluna de classe desbalanceada, coluna `group_id` e coluna `timestamp`. | `partitions/stage4a_gate.json` com `"passed": true`, `splits.csv.gz` com `train ∩ val = ∅`, grupos disjuntos e ordem temporal respeitada. | `partitions/partition_plan.json`, `splits.csv.gz`, `stage4a_gate.json`. | `P0` | Automatizada (`test_partitioning.py`). |
| **`TV-F09`** | Etapa 4B (`orchestration/engine.py`) | Validar execução matricial ($M \times C \times F$), persistência de predições por observação e retomada (`resume`). | Executar `expml run start`, verificar `runs/cells/` e `runs/predictions/`, simular interrupção (removendo 1 célula e marcando `FAILED` em `execution_state.json`) e rodar `expml run resume`. | Grade com 2 modelos $\times$ 2 cenários $\times$ 5 folds (20 células). | A retomada reexecuta apenas a célula pendente/falha, preservando as 19 concluídas, e `expml run verify` aprova `stage4b_gate.json`. | `runs/execution_state.json`, `runs/stage4b_gate.json`. | `P1` | Automatizada (`test_matrix_orchestration.py`). |
| **`TV-F10`** | Etapa 5 (`statistics/`) | Validar agregação descritiva, IC corrigido de Nadeau-Bengio, testes pareados ($t$ corrigido + Wilcoxon), Holm-Bonferroni, Kuncheva e Pareto. | Executar `expml stats run` e `expml stats verify` sobre experimento com $\ge 3$ configurações (modelo $\times$ cenário). | Experimento concluído na Etapa 4B com $K=5$ folds e $\ge 3$ configurações. | `descriptive_consolidation.json`, `statistical_comparisons.json` (com $p_{\text{raw}} \le p_{\text{adj}}$), `pareto_summary.json`, `mean_kuncheva` calculado em dinâmicos e `stage5_gate.json` aprovado. | Arquivos em `statistics/*.json`. | `P0` | **Verificado em `M8` (`VAL-BUG-009`).** |
| **`TV-F11`** | Etapa 6 (`reporting/tables.py`, `report.py`, `bundle.py`) | Validar geração de tabelas (Famílias A a G via Pandas → `TableModel`), relatório científico em `pt-BR` (`report.md`/`report.html` + Glossário) e pacote de reprodutibilidade. | Rodar `expml report generate`, `expml report export` e `expml report verify` em um experimento completo. | Experimento com Etapas 1 a 5 concluídas (incluindo cenários `DYNAMIC` e `cell_diagnostics`). | Todas as 7 famílias povoadas (A, B, C, D, E, F, G), `report.{md,html}` em `pt-BR` com figuras embutidas e Glossário Estatístico, e `checksums.sha256` aprovado. | `reports/report.{md,html}`, `reports/tables/*`, `reproducibility/`. | `P0` | **Verificado em `M8` e `M10` (`VAL-BUG-002/003`, `VAL-QUAL-002`) — Validar leitura.** |
| **`TV-F12`** | Etapa 6 (`reporting/figures.py`) | Validar inspeção visual humana das figuras exportadas via Matplotlib (`SVG`, `PNG 300 DPI`, `PDF`). | Abrir os arquivos `reports/figures/*.svg`, `*.png` e `*.pdf` gerados por `expml report export` ou `run_experiment`. | Experimento com $\ge 3$ configurações e fronteira de Pareto. | Figuras legíveis em UTF-8, com títulos, eixos numéricos, barras de erro, linha `Δ = 0` em `PAIRED_DIFF_CI` e Pareto nas coordenadas `(x, y)` reais. | Capturas das figuras em `reports/figures/`. | `P1` | **Verificado em `M10` (`VAL-BUG-006`) — Validar visualmente.** |
| **`TV-F13`** | Etapa 4A→6 (`CV_AND_HOLDOUT` + `FINAL_HOLDOUT`) | Validar criação/execução de células `FINAL_HOLDOUT`, isolamento de `DEV_CV` na Etapa 5 e exibição na Tabela D. | Configurar `EvaluationRegime.CV_AND_HOLDOUT` com `holdout_ratio > 0` e inspecionar `runs/cells/*final_holdout*`, `descriptive_consolidation.json` e Tabela D. | Dataset com $\ge 50$ linhas em `CV_AND_HOLDOUT` (com e sem `search_spec`). | `FINAL_HOLDOUT` treina sobre `development_ids` e avalia em `holdout_ids` sem contaminar `mean`/`std`/Nadeau-Bengio/OOF de `DEV_CV`, exibindo coluna `Holdout` na Tabela D. | `runs/cells/`, `statistics/descriptive_consolidation.json`, Tabela D. | `P0` | **Verificado em `M9` (`VAL-BUG-008` / `VAL-ENH-003`) — Validar em dados reais.** |

---

## 3. Matriz de Testes Metodológicos e Científicos (`TV-M01` a `TV-M08`)

Estes testes verificam as garantias científicas fundamentais do framework (`XCUT-01`, `XCUT-03`, `ADR-003`, `ADR-004`).

| ID | Garantia Metodológica | Objetivo do Teste | Procedimento de Execução | Critério de Sucesso Científico | Prioridade | Estado Atual |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **`TV-M01`** | **Prevenção de Data Leakage no Pré-processamento (Camada 2)** | Garantir que média/desvio (`StandardScaler`) ou min/max (`MinMaxScaler`, `AngularScaler`) do conjunto de validação `X_val` não influenciem a transformação. | Inserir um outlier extremo ($10^6$) apenas nas linhas do fold de validação `X_val` e comparar os parâmetros `mean_` / `scale_` ajustados no fold com uma execução onde `X_val` possui valores normais. | Os parâmetros do scaler e as predições de treino devem ser **bit a bit idênticos**, provando que `fit` ocorreu estritamente sobre `X_train`. | `P0` | Verificado em `tests/unit/test_preprocessing.py`. |
| **`TV-M02`** | **Prevenção de Data Leakage na Seleção Dinâmica de Atributos** | Garantir que `select_features_in_fold` não utilize `X_val` ou `y_val` do fold externo para ranquear atributos. | Criar um atributo sintético $X_{\text{leak}}$ que seja ruído puro em `X_train` ($r \approx 0$ com `y_train`), mas idêntico a `y_val` nas linhas de `X_val`. Executar seleção `TOP_K_RELEVANCE` ($k=1$). | O seletor **jamais** deve escolher $X_{\text{leak}}$ naquele fold, provando que `X_val` e `y_val` não foram consultados. | `P0` | Verificado para o fold externo em `tests/unit/test_fold_selection.py`. |
| **`TV-M03`** | **Isolamento Intra-Fold no Nested CV + Seleção Dinâmica (`ADR-003`)** | Verificar se a seleção dinâmica de atributos durante a busca de hiperparâmetros (`GRID_SEARCH`) respeita as fronteiras dos folds internos. | Executar célula combinando `ScenarioMode.DYNAMIC` (`TOP_K_RELEVANCE`) e `HyperparameterSearchSpec` (`GRID_SEARCH`) e inspecionar os atributos usados em cada fold interno do tuning. | Seleção dinâmica reexecutada dentro de cada `inner_train` durante o tuning (inclusive com `DEFER_INTRA_FOLD`). | `P1` | **Verificado em `M8` e `M9` (`VAL-BUG-005`).** |
| **`TV-M04`** | **Isolamento de Instâncias de Modelos (`ModelIsolationError`)** | Garantir que nenhuma instância de estimador scikit-learn mantenha estado residual entre folds ou células. | Verificar nos registros de execução que cada célula instancia um novo objeto via `instantiate_fresh_model` e que tentativas de reusar a mesma referência em memória lançam `ModelIsolationError`. | Zero compartilhamento de estado mutável entre células; `id(model_instance)` distinto ou liberado após término da célula. | `P0` | Verificado em `tests/unit/test_model_contracts.py`. |
| **`TV-M05`** | **Determinismo e Reprodutibilidade Bit a Bit (`XCUT-03`)** | Garantir que duas execuções independentes com a mesma `global_seed` produzam partições, seleções, hiperparâmetros, predições e métricas idênticos. | Executar o mesmo experimento duas vezes em diretórios distintos (`exp_run1` e `exp_run2`) com `--seed 42` e comparar os hashes SHA-256 de `splits.csv.gz`, `pred_*.json` e `descriptive_metrics.json`. | Hashes SHA-256 dos artefatos de dados, partições, predições e métricas 100% idênticos (inclusive com propagação de `seed` em instâncias prontas). | `P0` | **Verificado em `M8` (`VAL-BUG-007`).** |
| **`TV-M06`** | **Exatidão da Correção de Nadeau-Bengio e Intervalos de Confiança** | Validar que a variância corrigida $\hat{\sigma}^2_{\text{NB}} = (\frac{1}{K} + \frac{n_{\text{val}}}{n_{\text{train}}}) s^2$ é sempre maior que a variância ingênua $\frac{1}{K} s^2$ e que o IC usa $t_{K-1}$. | Para $K=5$ folds ($n_{\text{val}}/n_{\text{train}} = 0.25$), calcular manualmente a média, desvio-padrão amostral $s$, erro-padrão corrigido $\sqrt{(0.20 + 0.25) s^2} = \sqrt{0.45} s$ e quantil $t_{4, 0.975} = 2.7764$, confrontando com `descriptive_metrics.json`. | Diferença absoluta $< 10^{-12}$ entre o cálculo analítico manual e os campos `ci_lower` e `ci_upper` gravados pelo framework. | `P0` | Verificado em `tests/unit/test_statistics_aggregation.py`. |
| **`TV-M07`** | **Controle da Taxa de Erro Familiar (FWER) via Holm-Bonferroni** | Garantir que os $p$-valores ajustados em múltiplas comparações respeitem a monotonicidade step-down de Holm e $p_{\text{adj}} \in [p_{\text{raw}}, 1.0]$. | Executar Etapa 5 com 4 configurações (6 pares de comparação) e conferir a ordenação dos $p$-valores brutos $p_{(1)} \le \dots \le p_{(6)}$ e os fatores multiplicativos $(6, 5, 4, 3, 2, 1)$ com imposição de máximo cumulativo. | Todos os `p_value_adjusted` em `paired_comparisons.json` coincidem exatamente com o algoritmo de Holm (1979). | `P0` | Verificado em `tests/unit/test_statistics_comparisons.py`. |
| **`TV-M08`** | **Dominância de Pareto Multiobjetivo (`RF5.3`)** | Validar que a fronteira de Pareto identifica corretamente soluções não-dominadas ao combinar objetivos de direções opostas (ex.: maximizar `R2` e minimizar `mean_fit_time_s`). | Invocar `compute_pareto_frontier` com 4 configurações onde $A$ tem maior `R2` mas maior tempo, $B$ tem menor tempo e `R2` intermediário, e $C$ é dominada por $A$ e $B$. | `pareto_ranks` classifica $A$ e $B$ na Fronteira 1 (`is_pareto_optimal=True`) e $C$ na Fronteira 2 (`dominated_by=["A", "B"]`). | `P1` | Verificado na API (`test_statistics_pareto.py`); **expor múltiplos objetivos na CLI (`VAL-BUG-009` / `VAL-ENH-004`)**. |

---

## 4. Matriz de Testes de Integração e Ponta a Ponta (`TV-I01` a `TV-I06`)

| ID | Fluxo Ponta a Ponta | Procedimento Executável | Resultado Esperado | Prioridade | Estado Atual |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **`TV-I01`** | **Fluxo CLI `quickrun` em Regressão** | Executar em diretório temporário:<br>1. `expml init --output-dir /tmp/val_reg --task regression`<br>2. `expml quickrun --experiment-dir /tmp/val_reg` | Execução completa das Etapas 1 a 6 com código `0`, gerando 2 modelos, 10 células, 1 comparação pareada, todas as 7 tabelas e `reports/report.{md,html}` em `pt-BR`. | `P0` | **Verificado em `M8` e `M10`.** |
| **`TV-I02`** | **Fluxo CLI `quickrun` em Classificação Binária** | Executar em diretório temporário:<br>1. `expml init --output-dir /tmp/val_clf --task binary_classification`<br>2. `expml quickrun --experiment-dir /tmp/val_clf` | Execução concluída com código `0`, gerando 2 modelos e 1 comparação pareada. | `P1` | **Verificado em `M8` (`VAL-QUAL-003`).** |
| **`TV-I03`** | **Fluxo CLI Granular Etapa por Etapa (19 subcomandos)** | Executar sequencialmente `data profile`, `data sanitize`, `features explore`, `features scenarios`, `features verify`, `models validate`, `models verify`, `partition build`, `partition verify`, `run start`, `run status`, `run verify`, `stats run`, `stats status`, `stats verify`, `report generate`, `report export`, `report verify`. | Todos os portões `verify` aprovados com código `0`, todas as 7 tabelas e figuras exportadas em `tables/` e `figures/`, e `reproducibility/checksums.sha256` íntegro. | `P0` | **Verificado em `M8` e `M10`.** |
| **`TV-I04`** | **Interoperabilidade `run_experiment` (Python) → `expml` (CLI)** | Rodar `run_experiment(data="/tmp/dados.csv", models="default", output_dir="/tmp/val_interop", target="y", task="regression")` em Python e, em seguida, rodar `expml partition verify --experiment-dir /tmp/val_interop` e `expml report export --experiment-dir /tmp/val_interop` no terminal. | Todos os subcomandos `verify` e `export` da CLI funcionam normalmente sobre o diretório criado pela fachada Python, além de `run_experiment` já gerar PNGs da Etapa 2 e figuras/relatório `pt-BR` na Etapa 6. | `P1` | **Verificado em `M8` (`VAL-BUG-007`) e `M10`.** |
| **`TV-I05`** | **Execução Integral dos 4 Notebooks (`01` a `04`)** | Executar todas as células de `notebooks/01_primeiro_experimento_do_zero.ipynb` a `04_avancado_variantes_lssvm_prognose_florestal.ipynb` do início ao fim em kernel limpo. | Todas as células executam sem exceção, exibindo sumários estatísticos, gráficos exploratórios e relatórios finais consistentes. | `P1` | Funcional e verificado. |
| **`TV-I06`** | **Integridade Viva da Documentação (`test_documentation_integrity.py`)** | Executar `.venv/bin/pytest tests/unit/test_documentation_integrity.py -v`. | 100% dos links Markdown, âncoras de cabeçalhos, blocos Python (AST + imports reais) e blocos Bash (`expml` parser) aprovados sem erro. | `P0` | Funcional e verificado (`6/6 passed`). |

---

## 5. Matriz de Testes de Robustez e Casos de Borda (`TV-R01` a `TV-R08`)

| ID | Cenário de Borda / Falha | Procedimento de Teste | Comportamento Esperado do Framework | Prioridade |
| :--- | :--- | :--- | :--- | :---: |
| **`TV-R01`** | **Amostra insuficiente para $K$ folds ($N < K$)** | Tentar criar um plano `KFOLD` com `n_splits=10` em um dataset com apenas 8 linhas. | Lançar `PartitioningError` (código de saída `2` ou `3` na CLI) com mensagem clara indicando $N < K$. | `P1` |
| **`TV-R02`** | **Classe minoritária com menos exemplos que $K$ em `STRATIFIED_KFOLD`** | Tentar criar `STRATIFIED_KFOLD` ($K=5$) quando a classe `1` possui apenas 3 observações. | Lançar `PartitioningError` informando que a classe minoritária não possui amostras suficientes para garantir presença em todos os folds. | `P1` |
| **`TV-R03`** | **Número de grupos menor que $K$ em `GROUP_KFOLD`** | Tentar criar `GROUP_KFOLD` ($K=5$) quando a coluna `group_col` possui apenas 3 grupos distintos. | Lançar `PartitioningError` antes de gerar splits vazios. | `P1` |
| **`TV-R04`** | **Alta colinearidade / Matriz singular no cálculo de VIF** | Executar `compute_vif` na Etapa 2 sobre matriz onde $X_3 = X_1 + X_2$ (colinearidade perfeita). | Não lançar `LinAlgError`; retornar VIF elevado finito (ou `float("inf")` tratado) via pseudoinversa SVD (`np.linalg.pinv`). | `P1` |
| **`TV-R05`** | **Variância zero nas diferenças pareadas entre dois modelos** | Comparar na Etapa 5 dois modelos determinísticos que produzem predições idênticas em todos os folds ($d_i = 0, \forall i$). | `paired_t_test_corrected` e `wilcoxon_signed_rank` devem retornar estatística `0.0`, `p_value = 1.0` e `cohen_dz = 0.0` sem divisão por zero (`NaN`). | `P0` |
| **`TV-R06`** | **Adulteração manual de artefato em disco antes de `verify`** | Editar manualmente 1 número em `partitions/splits.csv.gz` ou `runs/predictions/pred_*.json` após a execução e rodar `expml partition verify` / `expml report verify`. | O gate deve detectar imediatamente a divergência de hash SHA-256 e falhar com `DataIntegrityError` / `StageGateError`. | `P0` |
| **`TV-R07`** | **Violação de pré-requisito de etapa (execução fora de ordem)** | Tentar rodar `expml run execute` em um diretório onde `expml partition verify` (`stage4a_gate.json`) ainda não foi executado. | Bloquear execução imediatamente com `StagePrerequisiteError` (código de saída `4` na CLI) informando qual gate anterior está ausente ou reprovado. | `P0` |
| **`TV-R08`** | **Parâmetro de modelo inválido no catálogo JSON** | Configurar `"n_estimators": -5` ou família inexistente em `configuration/models.json` e rodar `expml models register`. | Rejeitar com `ConfigurationError` (código de saída `2`) indicando o `model_id` e o parâmetro inválido. | `P2` |

---

## 6. Guia de Testes Exploratórios para o Desenvolvedor (`EXP-01` a `EXP-06`)

Além dos casos estruturados nas matrizes acima, recomenda-se ao desenvolvedor conduzir sessões livres de **testes exploratórios** usando conjuntos de dados reais de sua pesquisa de Iniciação Científica.

### `EXP-01` — Exploração com um Dataset Real do Domínio da Pesquisa
- **O que experimentar:** Carregar um arquivo CSV real da pesquisa (em vez dos datasets sintéticos gerados por `expml init`), contendo nomes reais de colunas (com acentos, espaços ou unidades de medida), diferentes ordens de grandeza entre variáveis e possíveis valores ausentes.
- **Por que vale a pena testar:** Datasets reais expõem combinações de tipos semânticos, nomes longos de colunas nos gráficos e distribuições assimétricas que dados sintéticos gaussianos não revelam.
- **Como executar:** Criar um diretório de experimento, apontar `raw_source_path` para o CSV real, rodar `expml data profile` e inspecionar `dataset_profile.json` e `exploratory_features.md`.
- **O que observar:**
  - Os tipos semânticos inferidos (`CONTINUOUS`, `CATEGORICAL`, `ORDINAL`, `IDENTIFIER`) fizeram sentido científico?
  - Alguma coluna numérica discreta foi classificada como categórica ou vice-versa?
  - Nos gráficos `relevance_ranking.png` e `redundancy_matrix.png`, os nomes das variáveis reais ficaram legíveis ou sofreram truncamento (`VAL-QUAL-001`)?

### `EXP-02` — Comparação entre Seleção Fixa (`FIXED`) e Seleção Dinâmica (`DYNAMIC`)
- **O que experimentar:** Configurar em um mesmo experimento três cenários de atributos: (1) `FIXED` com todas as variáveis, (2) `DYNAMIC` com `TOP_K_RELEVANCE` ($k=3$), e (3) `DYNAMIC` com `VIF_FILTER` (`threshold=5.0`).
- **Por que vale a pena testar:** Permite verificar se a estabilidade de seleção entre folds (índice de Kuncheva) e o ganho/perda preditiva nos modelos lineares vs. árvores são reportados de forma compreensível nas Etapas 5 e 6.
- **Como executar:** Definir os 3 cenários em `scenarios.json` (ou como dicionário em `run_experiment`), executar contra `Ridge` e `RandomForest` e inspecionar `runs/cells/cell_*.json` e `statistics/descriptive_metrics.json`.
- **O que observar:**
  - Quais variáveis foram escolhidas em cada fold? Houve variação entre o Fold 0 e o Fold 4?
  - O campo `mean_kuncheva` em `descriptive_metrics.json` refletiu essa variação ou ficou `None` (`VAL-BUG-009`)?
  - A Tabela B no `report.md` permite ao leitor entender qual estratégia cada cenário dinâmico usou (`VAL-QUAL-002`)?

### `EXP-03` — Sensibilidade ao Pré-processamento (Inclusive `AngularScaler` para Preparação Quântica)
- **O que experimentar:** Comparar um modelo sensível à escala (`SVM_REGRESSOR`, `MLP_REGRESSOR` ou `LOGISTIC_REGRESSION`) em três variantes de `ModelSpec`: sem pré-processamento, com `STANDARD_SCALER` e com `ANGULAR_SCALER` (que mapeia variáveis para ângulos em $[-\pi, \pi]$, preparando o terreno para codificação de rotação na Onda 2).
- **Por que vale a pena testar:** Valida na prática o funcionamento da Camada 2 de pré-processamento e permite observar o efeito da normalização angular sobre estimadores clássicos de kernel/rede neural.
- **Como executar:** Registrar três `ModelSpec`s variando apenas `preprocessing` e rodar a matriz completa.
- **O que observar:**
  - Os tempos de convergência e o erro preditivo mudam conforme esperado?
  - O relatório final (`report.md`) distingue claramente as três variantes na Tabela C (`VAL-QUAL-002`)?

### `EXP-04` — Injeção Deliberada de Atributo Colinear ou Ruidoso + Diagnósticos de Modelos
- **O que experimentar:** Adicionar ao dataset uma cópia quase exata de um atributo forte ($X_{\text{dup}} = X_1 + \epsilon$) e 3 colunas de ruído branco, rodando `Lasso`, `Ridge` e `RandomForest` (`oob_score=True`).
- **Por que vale a pena testar:** Testa se os diagnósticos extraídos nas células (`coefficients` do Lasso zerando o ruído, `feature_importances` do Random Forest dividindo importância entre $X_1$ e $X_{\text{dup}}$) são coerentes com o diagnóstico de VIF da Etapa 2.
- **Como executar:** Executar via `run_experiment` ou CLI e inspecionar `runs/cells/cell_*.json` e a seção da Família G no `report.md`.
- **O que observar:**
  - Os vetores `coefficients` e `feature_importances` nos JSONs das células têm o mesmo comprimento e ordem de `selected_features`?
  - Após a correção de `VAL-BUG-003` no Marco `M8`, como esses diagnósticos aparecem resumidos na Tabela G?

### `EXP-05` — Estresse de Retomada (`resume`) e Paralelismo (`outer_n_jobs`)
- **O que experimentar:** Rodar uma grade maior (ex.: 4 modelos $\times$ 3 cenários $\times$ 5 folds = 60 células) com `--n-jobs 2` ou `--n-jobs 4`, interromper o processo com `Ctrl+C` no meio da execução e retomar com `expml run resume`.
- **Por que vale a pena testar:** Verifica se a escrita atômica de arquivos (`os.replace`) evita JSONs truncados durante uma interrupção real e se o paralelismo multi-thread mantém o determinismo e o isolamento de instâncias (`VAL-BUG-010`).
- **Como executar:** Rodar `expml run execute --experiment-dir <dir> --n-jobs 2`, enviar `SIGINT` após ~20 células e rodar `expml run resume --experiment-dir <dir>`.
- **O que observar:**
  - Algum arquivo em `runs/cells/` ficou corrompido com `0 bytes`?
  - As células já `COMPLETED` foram preservadas sem reexecução?
  - O resultado final após o `resume` bate exatamente com uma execução contínua com `--n-jobs 1`?

### `EXP-06` — Avaliação Crítica do Relatório Científico como Leitor Externo
- **O que experimentar:** Abrir o `reports/report.html` e `reports/report.md` gerados por um experimento completo e lê-los sob a perspectiva de um orientador ou avaliador de Iniciação Científica que não conhece o código-fonte do framework.
- **Por que vale a pena testar:** Identifica lacunas de explicação, siglas sem legenda, tabelas difíceis de interpretar ou gráficos que precisam de ajustes de layout antes da publicação em relatórios acadêmicos.
- **O que observar:**
  - O leitor consegue saber exatamente qual foi o tamanho da base, quais variáveis entraram em cada cenário, quais hiperparâmetros foram testados e qual configuração venceu estatisticamente?
  - Anote qualquer dúvida de leitura e relate no chat para registro em [REGISTRO_DE_VALIDACAO_DO_MVP.md](./REGISTRO_DE_VALIDACAO_DO_MVP.md).

---

## 7. Sequência Recomendada de Validação para o Desenvolvedor (Pós-M8/M9/M10)

1. **Passo 1 — Push e Validação Automatizada Local:** Executar `.venv/bin/pytest tests/ -q` (`632 passed`) e validar `ACCEPTANCE.md` do `M10`.
2. **Passo 2 — Bateria Prática `P0` (`TV-F01`, `TV-F04`, `TV-F05`, `TV-F11`, `TV-F12`, `TV-F13`, `TV-I01`, `TV-I04`):** Executar experimentos reais contendo valores ausentes (`NaN`), atributos categóricos em texto (`DEFER_INTRA_FOLD`), regime `CV_AND_HOLDOUT` e inspecionar visualmente os gráficos `PNG`/`SVG`/`PDF` e o `report.html` em `pt-BR`.
3. **Passo 3 — Sessões Exploratórias (`EXP-01` a `EXP-06`) com Dados da Pesquisa (`CA02`):** Conduzir o estudo de caso experimental real da Iniciação Científica e registrar eventuais novos achados ou aprovar o aceite de `M9`/`M10`.
4. **Passo 4 — Próximas Evoluções Planejadas:** Avaliar e priorizar **`VAL-ENH-005`** (instrumentação de `train_metrics` e comparação visual Treino vs. Teste para diagnóstico de *overfitting*), **`VAL-ENH-004`** (múltiplos objetivos de Pareto e `planned_pairs` via CLI/`stats_config.json`) e a **Onda 2** (modelos quânticos e QML).
