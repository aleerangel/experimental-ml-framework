# M4.3 — Otimização de Hiperparâmetros Aninhada Intra-Fold Design

**Spec**: `.specs/features/m4-3-nested-tuning/spec.md`  
**Status**: Approved  

---

## Architecture Overview

O Sub-marco M4.3 estabelece o subsistema de otimização aninhada de hiperparâmetros da Etapa 3B (`experimental_ml.tuning`), materializando as decisões arquiteturais **ADR-003**, **ADR-005**, **RF3.5**, **CA-E4B-01** e **XCUT-02**.

A arquitetura organiza a busca de hiperparâmetros em três camadas funcionais desacopladas:
1. **Especificação e Validação Declarativa:** Tipos imutáveis (`HyperparameterSearchSpec`, `TuningTrialRecord`, `TuningResult`) validados contra o catálogo formal de métricas (`METRICS_CATALOG`), exigindo compatibilidade de direção (`MAXIMIZE` | `MINIMIZE`), orçamentos válidos e $K_{\text{inner}} \ge 2$.
2. **Geração Determinística de Candidatos:** Geradores puros para `FIXED`, `GRID_SEARCH` (produto cartesiano lexicográfico) e `RANDOM_SEARCH` (amostragem determinística reproduzível via semente).
3. **Motor de Execução Aninhada (*Nested CV Engine*):** Particionamento interno estritamente confinado ao conjunto de treino externo ($X_{\text{train}}, y_{\text{train}}$), instanciação limpa de estimadores (`instantiate_fresh_model`), avaliação fold a fold, desqualificação de candidatos com `UNDEFINED_NAN` e seleção objetiva do melhor parâmetro $\theta^*$.

```mermaid
flowchart TD
    subgraph DeclarativeValidation ["1. Especificação e Validação Declarativa"]
        Spec["HyperparameterSearchSpec<br/>(strategy, param_grid, metric, direction, folds, seed)"]
        ValFn["validate_search_spec(spec)"]
        CatCheck{"Validação contra<br/>METRICS_CATALOG<br/>e K_inner >= 2"}
        
        Spec --> ValFn --> CatCheck
        CatCheck -->|Inválido / Incompatível| CfgError["ConfigurationError"]
        CatCheck -->|Válido| ValidSpec["Validated Search Spec"]
    end

    subgraph CandidateGen ["2. Geração Determinística de Candidatos"]
        ValidSpec --> GenFn["generate_candidates(spec)"]
        GenFn --> CandList["tuple[CandidateParams, ...]<br/>(Ordenação Determinística / Amostragem com Seed)"]
    end

    subgraph NestedEngine ["3. Motor de Nested CV (Anti-Leakage Intra-Fold)"]
        XTrain["X_train (2D np.ndarray)"]
        YTrain["y_train (1D np.ndarray)"]
        SplitFn["split_inner_folds(N_train, K_inner)"]
        
        XTrain --> SplitFn
        YTrain --> SplitFn
        SplitFn --> InnerFolds["K_inner Folds:<br/>(Train_inner, Val_inner) com interseção nula"]
        
        CandList --> EvalLoop["Para cada candidato theta_i:"]
        InnerFolds --> EvalLoop
        
        subgraph FoldEvaluation ["Avaliação por Fold Interno"]
            EvalLoop --> InstFresh["instantiate_fresh_model(model_spec, seed)"]
            InstFresh --> FitInner["fit_model(instance, X_inner_train, y_inner_train)"]
            FitInner --> PredInner["predict_model(instance, X_inner_val)"]
            PredInner --> MetricEval["metrics.calculate(y_inner_val, y_pred)"]
        end
        
        MetricEval --> Aggregation{"Algum fold produziu<br/>UNDEFINED_NAN?"}
        Aggregation -->|Sim| Disqualify["TrialStatus = UNDEFINED_NAN<br/>(Candidato Desqualificado)"]
        Aggregation -->|Não| MeanScore["Mean Score = avg(fold_scores)<br/>TrialStatus = VALID"]
        
        Disqualify --> Selection
        MeanScore --> Selection
        
        subgraph Selection ["4. Seleção do Vencedor e Registro"]
            AllNanCheck{"Todos os candidatos<br/>são UNDEFINED_NAN / erro?"}
            AllNanCheck -->|Sim (ADR-005)| OptError["TuningOptimizationError"]
            AllNanCheck -->|Não| BestSelect["Selecionar theta* pelo melhor score<br/>(Desempate determinístico pelo menor índice)"]
            BestSelect --> Result["TuningResult<br/>(best_params, best_score, trials)"]
        end
    end
```

---

## Code Reuse Analysis

### Existing Components to Leverage

- **`experimental_ml.core`**:
  - `ConfigurationError`, `ContractViolationError`: hierarquia padronizada de exceções.
  - `MetricDirection`: enum canônico (`MAXIMIZE`, `MINIMIZE`).
  - `MetricStatus`: enum de integridade (`VALID`, `UNDEFINED_NAN`).
  - `derive_seeds`: derivação determinística de sementes via `SeedSequence`.
- **`experimental_ml.metrics`**:
  - `METRICS_CATALOG`: catálogo canônico de 15 métricas de regressão e classificação com direções formais.
  - `is_better`: comparação com tratamento de direção (`MAXIMIZE` vs `MINIMIZE`).
- **`experimental_ml.models`**:
  - `ModelSpec`: especificação declarativa de modelos.
  - `instantiate_fresh_model`: instanciação com semente e garantia de novas instâncias (`CA-E3-01`).
  - `fit_model`: ajuste em arrays NumPy.
  - `predict_model`: predição retornando predições e incertezas (`y_pred`, `y_std`, `y_proba`).

### New Components to Create in `src/experimental_ml/tuning/`

- **`types.py`**:
  - `SearchStrategy` (`str, Enum`): `FIXED`, `GRID_SEARCH`, `RANDOM_SEARCH`, `CUSTOM_TUNER`.
  - `HyperparameterSearchSpec`: especificação imutável congelada com slots.
  - `TuningTrialRecord`: registro congelado de cada tentativa individual com slots.
  - `TuningResult`: resultado congelado consolidado com slots.
  - `TuningOptimizationError`: exceção especializada herdando de `ContractViolationError`.
- **`validation.py`**:
  - `validate_search_spec`: função pura de validação declarativa contra `METRICS_CATALOG` e restrições de folds ($K_{\text{inner}} \ge 2$) e orçamentos.
- **`candidates.py`**:
  - `generate_candidates`: gerador puramente determinístico de combinações de hiperparâmetros (produto cartesiano ordenado e amostragem controlada por semente).
- **`partitioning.py`**:
  - `split_inner_folds`: particionador K-Fold interno puro em NumPy gerando índices disjuntos $0 \dots N-1$ sobre o conjunto de treino externo.
- **`engine.py`**:
  - `run_nested_tuning`: executor de nested cross-validation com instanciação limpa, avaliação fold a fold, agregação estrita de métricas e seleção determinística de $\theta^*$.
- **`__init__.py`**:
  - Ponto de entrada público exportando todos os símbolos do subsistema `tuning`.

---

## Technical Decisions & Risk Mitigations

### 1. Prevenção Absoluta de Vazamento de Dados (Anti-Leakage / CA-E4B-01)
- **Risco:** Dados do conjunto de validação ou teste externo serem passados direta ou indiretamente para a busca de hiperparâmetros.
- **Mitigação:** A assinatura de `run_nested_tuning` aceita exclusivamente `X_train` e `y_train`. Não há parâmetros para dados de avaliação. A partição de validação é gerada internamente a partir de subfatias de `X_train`.

### 2. Tratamento Estrito de `UNDEFINED_NAN` (ADR-005)
- **Risco:** Um modelo que converge para predições degeneradas (ex.: variância zero, ausência de classes positivas) produzir `NaN` em $R^2$ ou `Precision` e ser silenciosamente convertido para $0.0$, vencendo candidatos legítimos ou mascarando falhas científicas.
- **Mitigação:** Qualquer dobra interna que resulte em `UNDEFINED_NAN` ou `isnan(value)` marca o trial como desqualificado. Se todas as tentativas falharem ou gerarem `UNDEFINED_NAN`, `run_nested_tuning` dispara `TuningOptimizationError` e interrompe o pipeline da célula.

### 3. Isolamento e Reuso de Estimadores (CA-E3-01)
- **Risco:** Parâmetros ajustados em uma dobra interna persistirem na instância do estimador e contaminarem dobras subsequentes.
- **Mitigação:** `run_nested_tuning` invoca compulsóriamente `instantiate_fresh_model(model_spec, seed=...)` para cada par $(\text{candidato}, \text{fold})$, garantindo instâncias frescas de memória sem vazamento de estado.

### 4. Pureza de Runtime (XCUT-02)
- **Risco:** Dependência acidental de `scikit-learn.model_selection` (GridSearchCV) ou `optuna` no runtime de produção.
- **Mitigação:** Toda a infraestrutura de particionamento interno e busca de hiperparâmetros é implementada em NumPy puro e na biblioteca padrão (`itertools`, `random`), com teste de integração em subprocesso isolado verificando ausência de módulos de terceiros em `sys.modules`.
