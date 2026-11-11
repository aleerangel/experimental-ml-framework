# Feature: m4-1-model-registry-contracts

**Approved**: 2026-11-11 - user: "podemos iniciar o marco m4.1"

## Problem Statement

Na arquitetura do `experimental-ml-framework`, a Etapa 3 (Modelos, Circuitos, Pré-processamento e Hiperparâmetros) é responsável por registrar e orquestrar modelos heterogêneos sob estruturas de dados estritamente padronizadas e contratos funcionais desacoplados.

Atualmente, o framework já consolidou as Fundações Transversais (Marco M1), o Pipeline de Diagnóstico e Particionamento (Marco M2) e a Engenharia e Cenários de Atributos (Marco M3). No entanto, não há ainda no subsistema `src/experimental_ml/models/` contratos unificados para:
1. Declarar metadados, identificadores e capacidades operacionais de modelos heterogêneos (`ModelSpec`, `ModelCapabilities`, `ModelFamily`), permitindo tratar sob uma mesma interface modelos clássicos, redes neurais, equações biométricas/analíticas, baselines e algoritmos quânticos.
2. Garantir o isolamento total de instâncias (`CA-E3-01`), evitando contaminação de pesos, coeficientes ajustados ou parâmetros entre partições/folds (`instantiate_fresh_model`).
3. Executar o ciclo de vida de treinamento (`fit_model`) e inferência (`predict_model`) de forma puramente funcional, com suporte nativo a modelos analíticos/biométricos sem ajuste artificial (`requires_fit=False`, `RF3.2`) e contrato de predição completo suportando predição pontual (`y_pred`), incerteza preditiva individual (`y_std`) e probabilidades de classe (`y_proba`).
4. Coletar diagnósticos e metadados internos estruturados (`extract_model_diagnostics`), distinguindo metadados de configuração, métricas globais e diagnósticos do algoritmo (`RF3.6`), garantindo imutabilidade por snapshot independente.
5. Validar catálogos de modelos em memória (`validate_models_catalog`), assegurando unicidade de identificadores e conformidade contratual sem acoplamento a persistência em disco ou interfaces CLI.

Este sub-marco M4.1 estabelece as fundações conceituais e os contratos funcionais executáveis do módulo `models`, viabilizando o subsequente pré-processamento em duas camadas (M4.2), a busca aninhada de hiperparâmetros (M4.3) e a persistência e CLI de modelos (M4.4).

## Out of Scope

- Implementação do pipeline de pré-processamento em 2 camadas (`fit_two_layer_preprocessing`, `apply_two_layer_preprocessing`) — escopo do Sub-marco M4.2.
- Otimização aninhada de hiperparâmetros (*Nested CV*, `run_nested_tuning`) — escopo do Sub-marco M4.3.
- Persistência em disco do catálogo (`models.json`), codecs de serialização de modelos e portão de validação `verify_models_gate` — escopo do Sub-marco M4.4.
- Subcomandos de linha de comando `expml models ...` — escopo do Sub-marco M4.4.
- Orquestração matricial e máquina de estados das células de execução — escopo do Marco M5 (`orchestration`).
- Inclusão de novas dependências de runtime obrigatórias além de `numpy>=1.24.0` (`XCUT-02`).
- Conversões heurísticas ou calibrações artificiais universais entre `decision_function` e probabilidades (`predict_proba`).

## Assumptions & Open Questions

**Open questions:** none - os padrões e contratos funcionais de modelos já foram formalmente especificados na SRS (RF3.1 a RF3.3, RF3.6) e na Arquitetura (Seção 3.3).

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Dependência externa de bibliotecas de ML no runtime principal | Duck-typing e wrappers funcionais sem dependência mandatória de `scikit-learn` no `pyproject.toml` | Preserva a pureza de runtime (`XCUT-02`), permitindo que estimadores scikit-learn, PyTorch, Qiskit ou callables customizados sejam passados via construtores externos sem inflar o runtime base |
| Formato de retorno da função funcional de predição `predict_model` | Retorna um dicionário `dict[str, np.ndarray \| None]` com chaves canônicas `y_pred`, `y_std` e `y_proba` | Atende aos requisitos da arquitetura (Seção 3.3) unificando tarefas de regressão, classificação e quantificação de incerteza em um único contrato imutável |
| Suporte a modelos analíticos / biométricos sem treino | Flag booleana `requires_fit: bool` em `ModelCapabilities` acionando no-op em `fit_model` | Cumpre `RF3.2` e corrige anomalias arquiteturais históricas onde modelos analíticos como Clutter precisavam de chamadas falsas de treino |
| Propagação determinística de sementes aleatórias | `instantiate_fresh_model` recebe `seed: int \| None` e disponibiliza para `estimator_factory(seed)` | Garante reprodutibilidade estrita (`RNF01`, `ADR-007`) gerando instâncias frescas limpas a cada partição/fold sem exigir infraestrutura genérica de injeção |
| Escopo de Registry no Marco M4.1 | Coleção em memória validada por `validate_models_catalog`, sem persistência em disco ou CLI | Delimita com clareza a responsabilidade de M4.1 aos contratos em memória, reservando persistência (`models.json`) e comandos CLI para M4.4 |
| Separação entre validação declarativa e execução | `validate_model_spec` valida estática e estruturalmente o `ModelSpec`; `predict_model` verifica em execução se as saídas respeitam as capacidades declaradas | Evita execuções artificiais prematuras na validação declarativa e garante que quebras de contrato em execução sejam barradas com `ContractViolationError` |

## User Stories

### US-M41-01 (Priority: P1) — Model Family Enum, Identifiers and Diagnostics Types
As an experimental ML researcher,  
I want canonical enumerations and immutable data structures for model families, capabilities, specifications, and diagnostics,  
So that every algorithm is described unambiguously regardless of its implementation technology.

### US-M41-02 (Priority: P1) — Declarative ModelSpec, Capabilities Semantics and Declarative Validation
As an experimental framework developer,  
I want a declarative `ModelSpec` structure validated by a pure `validate_model_spec` function without executing dummy inferences,  
So that invalid, malformed, or internally inconsistent model specifications are rejected before any execution begins.

### US-M41-03 (Priority: P1) — Fresh Model Instantiation, Factory Contract and Instance Isolation
As an experiment runner,  
I want `instantiate_fresh_model` to invoke `estimator_factory(seed)` and guarantee freshly allocated, unshared instances,  
So that states, weights, or hyperparameters never leak across folds, splits, or bootstrap resamples (`CA-E3-01`).

### US-M41-04 (Priority: P1) — Functional Model Fitting with Analytical Bypass
As an experiment runner,  
I want `fit_model` to train the instantiated model on `X_train, y_train` or transparently no-op when `requires_fit=False`,  
So that trainable ML algorithms and analytical equations operate under a unified execution contract (`RF3.2`).

### US-M41-05 (Priority: P1) — Functional Model Prediction, Output Contracts, and Execution Verification
As an evaluation pipeline,  
I want `predict_model` to produce standardized outputs with verified `y_pred`, `y_std`, and `y_proba`,  
So that metrics and subsequent statistical stages receive uniform numpy arrays and runtime capability violations are strictly rejected.

### US-M41-06 (Priority: P1) — Internal Diagnostics Snapshot and Immutability
As a scientific auditor,  
I want `extract_model_diagnostics` to capture an independent snapshot of internal model metadata converted to immutable types,  
So that domain-specific parameters, convergence metrics, and internal states are recorded for scientific reporting without post-extraction mutation (`RF3.6`).

### US-M41-07 (Priority: P1) — In-Memory Models Catalog Validation (Registry)
As an experiment configurator,  
I want `validate_models_catalog` to validate a collection of `ModelSpec` objects and ensure unique `model_id` identifiers,  
So that an experimental suite of models is verified in memory before partition scheduling.

### US-M41-08 (Priority: P2) — Canonical Baseline and Analytical Reference Implementations
As a framework consumer,  
I want reference baseline models (mean/median regression and most-frequent classification) and an analytical reference model,  
So that the framework can be fully verified end-to-end without external third-party model libraries.

### US-M41-09 (Priority: P2) — Runtime Purity and Architectural Compliance
As a software engineer,  
I want the models module to enforce single runtime dependency (`numpy>=1.24.0`) and architectural import boundaries,  
So that the core runtime remains lightweight, portable, and strictly layered (`XCUT-01`, `XCUT-02`).

## Acceptance Criteria

### Criteria for US-M41-01 (Types & Enums)
- **AC-M41-01-01 (Ubiquitous):** The system SHALL define `ModelFamily` as a closed `str, Enum` with members `CLASSICAL_ML`, `NEURAL_NETWORK`, `QUANTUM_CIRCUIT`, `QUANTUM_KERNEL`, `QUANTUM_SOLVER`, `ANALYTICAL_EQUATION`, `BIOMETRIC_MODEL`, `BASELINE`, and `CUSTOM`.
- **AC-M41-01-02 (Ubiquitous):** The system SHALL define `ModelCapabilities` as an immutable frozen dataclass with slots containing boolean flags `requires_fit`, `supports_predict`, `supports_uncertainty`, `supports_predict_proba`, `supports_decision_function`, `supports_sample_weight`, `supports_precomputed_kernel`, `supports_internal_parallelism_control`, and tuple `expected_input_types`.
- **AC-M41-01-03 (Ubiquitous):** The system SHALL define `ModelDiagnostics` as an immutable frozen dataclass with slots containing `model_id: str`, `phase: str`, `diagnostics: MappingProxyType[str, Any]`, and `extracted_at: str`.

### Criteria for US-M41-02 (ModelSpec & Declarative Validation)
- **AC-M41-02-01 (Ubiquitous):** The system SHALL define `ModelSpec` as an immutable frozen dataclass with slots containing `model_id: str`, `display_name: str`, `family: ModelFamily`, `estimator_factory: Callable`, `capabilities: ModelCapabilities`, `description: str`, `scientific_justification: str`, `parameters: MappingProxyType[str, Any]`, and `random_seed_policy: str`.
- **AC-M41-02-02 (Event-driven):** WHEN `validate_model_spec` is executed with a valid `ModelSpec`, THEN the system SHALL return the validated spec without mutating any field and without executing training or prediction.
- **AC-M41-02-03 (Unwanted-behavior):** IF `ModelSpec` contains an empty or non-alphanumeric `model_id` (not matching `^[a-zA-Z0-9_-]+$`), an empty `display_name`, empty `description`, empty `scientific_justification`, or a non-callable `estimator_factory`, THEN the system SHALL raise `ConfigurationError`.
- **AC-M41-02-04 (Unwanted-behavior):** IF `ModelCapabilities` declares an internally contradictory combination where `supports_predict=False` or where `requires_fit=False` is combined with `supports_sample_weight=True`, THEN `validate_model_spec` SHALL raise `ConfigurationError`.

### Criteria for US-M41-03 (Fresh Instantiation & Isolation)
- **AC-M41-03-01 (Event-driven):** WHEN `instantiate_fresh_model` is invoked with a `ModelSpec` and integer `seed`, THEN the system SHALL pass the seed to `estimator_factory(seed)` and return a newly instantiated model instance uncoupled from any previously returned object.
- **AC-M41-03-02 (Event-driven):** WHEN `instantiate_fresh_model` is invoked with `seed=None`, THEN the system SHALL invoke `estimator_factory(None)` and return a newly instantiated model instance.
- **AC-M41-03-03 (Unwanted-behavior):** IF `estimator_factory` returns a singleton or previously instantiated object matching the memory identity of an active instance, THEN `instantiate_fresh_model` SHALL raise `ContractViolationError`.
- **AC-M41-03-04 (Unwanted-behavior):** IF `estimator_factory` rejects the seed parameter or raises an exception during instantiation, THEN `instantiate_fresh_model` SHALL raise `ConfigurationError`.
- **AC-M41-03-05 (State-driven):** WHILE multiple calls to `instantiate_fresh_model` are made, the system SHALL ensure that modifying or training one model instance leaves the state, parameters, and attributes of all other instances untouched (`CA-E3-01`).

### Criteria for US-M41-04 (Functional Fitting)
- **AC-M41-04-01 (State-driven):** WHILE `model_spec.capabilities.requires_fit` is `True`, WHEN `fit_model` is executed with 2D `X_train` and 1D `y_train`, THEN the system SHALL fit the model exclusively on those training arrays and return a tuple `(fitted_model, fit_diagnostics)`.
- **AC-M41-04-02 (State-driven):** WHILE `model_spec.capabilities.requires_fit` is `False`, WHEN `fit_model` is executed, THEN the system SHALL return the model instance unmodified without invoking any training procedure (`RF3.2`).
- **AC-M41-04-03 (Unwanted-behavior):** IF `fit_model` receives `X_train` and `y_train` with mismatched sample counts ($N_X \neq N_y$) or empty arrays ($N=0$), THEN the system SHALL raise `ContractViolationError`.

### Criteria for US-M41-05 (Functional Prediction & Output Verification)
- **AC-M41-05-01 (Event-driven):** WHEN `predict_model` is executed with a fitted model and 2D `X_eval`, THEN the system SHALL return a dictionary containing keys `"y_pred"`, `"y_std"`, and `"y_proba"`, where `"y_pred"` is a 1D `np.ndarray` with length matching the number of evaluation samples.
- **AC-M41-05-02 (Optional-feature):** WHERE `model_spec.capabilities.supports_uncertainty` is `True`, the system SHALL produce a 1D `np.ndarray` in `y_std` whose length matches `len(y_pred)`, containing strictly finite non-negative values ($y_{\text{std}} \ge 0.0$).
- **AC-M41-05-03 (Optional-feature):** WHERE `model_spec.capabilities.supports_predict_proba` is `True`, the system SHALL produce a 2D `np.ndarray` in `y_proba` with shape `(n_samples, n_classes)` containing finite values in $[0.0, 1.0]$ whose row sums equal $1.0$ within numerical tolerance.
- **AC-M41-05-04 (State-driven):** WHILE `model_spec.capabilities.supports_uncertainty` is `False`, the system SHALL set `y_std` to `None` in the prediction dictionary.
- **AC-M41-05-05 (State-driven):** WHILE `model_spec.capabilities.supports_predict_proba` is `False`, even if `supports_decision_function` is `True`, the system SHALL set `y_proba` to `None` without converting decision scores into probabilities.
- **AC-M41-05-06 (Unwanted-behavior):** IF `predict_model` is invoked on a trainable model (`requires_fit=True`) that has not been fitted, THEN the system SHALL raise `ContractViolationError`.
- **AC-M41-05-07 (Unwanted-behavior):** IF `predict_model` detects that an estimator declared with `supports_uncertainty=True` produces `None`, an array with mismatched length, negative values, or non-finite values in `y_std`, THEN the system SHALL raise `ContractViolationError`.
- **AC-M41-05-08 (Unwanted-behavior):** IF `predict_model` detects that an estimator declared with `supports_predict_proba=True` produces `None`, an array with invalid dimensions, values outside $[0.0, 1.0]$, or row sums differing from $1.0$, THEN the system SHALL raise `ContractViolationError`.

### Criteria for US-M41-06 (Diagnostics Snapshot & Immutability)
- **AC-M41-06-01 (Event-driven):** WHEN `extract_model_diagnostics` is invoked with a fitted model, `ModelSpec`, and execution phase, THEN the system SHALL return an immutable `ModelDiagnostics` record with native scalar types and immutable mappings.
- **AC-M41-06-02 (Ubiquitous):** The system SHALL ensure that diagnostics extraction operates as an independent snapshot such that mutating the fitted model after extraction does not alter the values of the produced `ModelDiagnostics`.
- **AC-M41-06-03 (Unwanted-behavior):** IF an extracted diagnostic value contains unsupported mutable complex objects that cannot be safely converted to immutable primitives, THEN the system SHALL raise `ContractViolationError`.
- **AC-M41-06-04 (Ubiquitous):** The system SHALL ensure that diagnostics extraction never mutates the underlying model instance or alters its future predictions.

### Criteria for US-M41-07 (In-Memory Models Catalog Validation)
- **AC-M41-07-01 (Event-driven):** WHEN `validate_models_catalog` is invoked with a sequence of `ModelSpec` objects, THEN the system SHALL validate each specification and return an immutable `MappingProxyType[str, ModelSpec]` indexed by `model_id`.
- **AC-M41-07-02 (Unwanted-behavior):** IF `validate_models_catalog` detects duplicate `model_id` values across the provided specifications, THEN the system SHALL raise `ConfigurationError`.

### Criteria for US-M41-08 (Reference Implementations)
- **AC-M41-08-01 (Event-driven):** WHEN `DummyBaselineModel` is fitted on regression targets with strategy `"mean"`, THEN `predict_model` SHALL output the training target mean as `y_pred` and the training target sample standard deviation as `y_std`.
- **AC-M41-08-02 (Event-driven):** WHEN `DummyBaselineModel` is fitted on regression targets with strategy `"median"`, THEN `predict_model` SHALL output the training target median as `y_pred` and the sample median absolute deviation as `y_std`.
- **AC-M41-08-03 (Event-driven):** WHEN `DummyBaselineModel` is fitted on classification targets with strategy `"most_frequent"`, THEN `predict_model` SHALL output the majority class as `y_pred`, resolve count ties deterministically by lexicographical order, and output empirical relative frequencies as `y_proba`.
- **AC-M41-08-04 (Event-driven):** WHEN `AnalyticalBiometricModel` is instantiated with explicit mathematical parameters, THEN `fit_model` SHALL operate as a no-op and `predict_model` SHALL evaluate the mathematical expression directly on `X_eval`.
- **AC-M41-08-05 (Unwanted-behavior):** IF `AnalyticalBiometricModel` receives `X_eval` lacking any required input feature, THEN the system SHALL raise `ContractViolationError`.

### Criteria for US-M41-09 (Runtime Purity)
- **AC-M41-09-01 (Ubiquitous):** The system SHALL maintain single runtime dependency (`numpy>=1.24.0`), with zero mandatory third-party ML framework imports in `src/experimental_ml/models/__init__.py`.

## Requirement Traceability

| Requirement ID | Acceptance Criterion | Verification Method | Status |
| --- | --- | --- | --- |
| MOD-01 | AC-M41-01-01, AC-M41-01-02, AC-M41-01-03 | Unit tests on enums and dataclass immutability (`test_model_types.py`) | pending |
| MOD-02 | AC-M41-02-01, AC-M41-02-02, AC-M41-02-03, AC-M41-02-04 | Unit tests on `validate_model_spec` structural validation and contradictory capability checks (`test_model_registry.py`) | pending |
| MOD-03 | AC-M41-03-01, AC-M41-03-02, AC-M41-03-03, AC-M41-03-04, AC-M41-03-05 | Unit tests verifying fresh instance creation, seed handling, and memory decoupling (`test_model_execution.py`) | pending |
| MOD-04 | AC-M41-04-01, AC-M41-04-02, AC-M41-04-03 | Unit tests on `fit_model` for trainable estimators and analytical bypass (`test_model_execution.py`) | pending |
| MOD-05 | AC-M41-05-01, AC-M41-05-02, AC-M41-05-03, AC-M41-05-04, AC-M41-05-05, AC-M41-05-06, AC-M41-05-07, AC-M41-05-08 | Unit tests on `predict_model` output dict verification, probability bounds, and runtime violation checks (`test_model_execution.py`) | pending |
| MOD-06 | AC-M41-06-01, AC-M41-06-02, AC-M41-06-03, AC-M41-06-04 | Unit tests on `extract_model_diagnostics` snapshot independence, deep immutability, and rejection of complex mutables (`test_model_diagnostics.py`) | pending |
| MOD-07 | AC-M41-07-01, AC-M41-07-02 | Unit tests on `validate_models_catalog` in-memory collection validation and duplicate rejection (`test_model_registry.py`) | pending |
| MOD-08 | AC-M41-08-01, AC-M41-08-02, AC-M41-08-03, AC-M41-08-04, AC-M41-08-05 | Unit tests on regression/classification baselines and analytical reference model (`test_model_baselines.py`) | pending |
| MOD-09 | AC-M41-09-01 | Subprocess inspection asserting `sys.modules` contains only NumPy (`test_models_integration.py`) | pending |
