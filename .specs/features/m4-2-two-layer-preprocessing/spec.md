# Feature: m4-2-two-layer-preprocessing

**Approved**: 2026-11-11 - user: "aprovado"

## Problem Statement

Na arquitetura do `experimental-ml-framework`, a Etapa 3 é responsável por preparar os dados para os modelos através de uma rigorosa arquitetura de pré-processamento em duas camadas (**ADR-002** e **RF3.4**):
1. **Camada 1 (Cenário / Domínio):** transformações vinculadas aos atributos do cenário experimental (ex.: imputação de valores ausentes, codificação de categorias, transformações de domínio).
2. **Camada 2 (Específica do Modelo):** transformações exigidas pelas restrições tecnológicas de cada família de modelo (ex.: escalonamento numérico `Standard`, `MinMax`, `MaxAbs`, `Robust`, normalização angular para circuitos quânticos, ou projeção para funções externas de kernel pré-computado).

Atualmente, o framework consolidou os contratos de modelos (M4.1) e a seleção dinâmica intra-fold (M3.3), mas ainda não possui um pipeline funcional que:
- Valide declarativamente a composição das duas camadas antes da execução, bloqueando duplicações acidentais da mesma transformação entre a Camada 1 e a Camada 2 (`CA-E3-02`).
- Ajuste todos os estimadores e parâmetros de transformação **estritamente sobre `X_train`** de cada partição externa (`fit_two_layer_preprocessing`), prevenindo qualquer contaminação ou vazamento de dados (*data leakage*, `CA-E4B-01`).
- Aplique o estado ajustado de forma puramente funcional e imutável sobre conjuntos de treino ou avaliação (`apply_two_layer_preprocessing`), sem recalcular estatísticas.
- Suporte a passagem não vazada de partições para funções de kernel pré-computado externo (`supports_precomputed_kernel=True`), entregando $(\mathbf{X}_{\text{train}}, \mathbf{X}_{\text{train}})$ no ajuste do *fold* e $(\mathbf{X}_{\text{eval}}, \mathbf{X}_{\text{train}})$ na inferência.
- Mantenha conformidade estrita com `numpy>=1.24.0` (`XCUT-02`), sem introduzir dependência obrigatória de bibliotecas externas no runtime principal.

## Out of Scope

- Otimização aninhada de hiperparâmetros (*Nested CV*, `run_nested_tuning`) — escopo do Sub-marco M4.3.
- Persistência em disco de `models.json` e subcomandos CLI `expml models` — escopo do Sub-marco M4.4.
- Orquestração matricial da matriz experimental — escopo do Marco M5 (`orchestration`).
- Implementação de algoritmos quânticos ou kernels internos (o framework atua exclusivamente como orquestrador e adaptador de partição via ADR-001 e ADR-002).
- Novas dependências de runtime além de `numpy>=1.24.0` (`XCUT-02`).

## Assumptions & Open Questions

**Open questions:** none - os padrões e contratos funcionais de pré-processamento já foram formalmente especificados na SRS (RF3.4) e na Arquitetura (Seção 3.3 e ADR-002).

| Assumption / Question | Chosen default | Rationale |
| :--- | :--- | :--- |
| Estrutura de estado ajustado de pré-processamento | Dataclass imutável `TwoLayerPreprocessingState` contendo estados ordenados da Camada 1 e Camada 2 | Substitui pipelines mutáveis com efeitos colaterais por estruturas funcionais puras com auditoria de linhagem |
| Bloqueio de transformações duplicadas | `validate_two_layer_preprocessing` rejeita a declaração do mesmo tipo de transformador de escalonamento em ambas as camadas | Cumpre `CA-E3-02`, impedindo que um usuário aplique acidentalmente padronização duas vezes no mesmo pipeline |
| Passagem para funções externas de kernel | `PrecomputedKernelAdapter` armazena referência imutável a $\mathbf{X}_{\text{train}}$ durante o *fit* e avalia $(\mathbf{X}_{\text{eval}}, \mathbf{X}_{\text{train}})$ no *transform* | Garante que kernels de Gram sejam avaliados sem vazamento de dados, cumprindo RF3.4 |
| Tratamento de colunas com variância zero nos escalonadores | Divisão por zero substituída por escala unitária (mantendo valor constante centralizado em 0.0) | Previne geração de `NaN` ou `Inf` durante transformações numéricas |
| Tipos de entrada e saída | 2D `np.ndarray` float64 tanto no treino quanto na avaliação | Garante interoperabilidade universal com estimadores numéricos e quânticos sob `XCUT-02` |

## User Stories

### US-M42-01 (Priority: P1) — Preprocessing Types, Step Enums and Declarative Specs
As an experimental ML researcher,  
I want declarative specifications and immutable data structures for preprocessing layers and steps,  
So that I can define data transformations for scenarios and model requirements in a structured, verifiable format.

### US-M42-02 (Priority: P1) — Accidental Duplication Detection and Validation
As a pipeline validator,  
I want `validate_two_layer_preprocessing` to inspect the composition of Layer 1 and Layer 2 and reject duplicate or contradictory transformations,  
So that redundant scalers or conflicting preprocessing steps are barred before any execution begins (`CA-E3-02`).

### US-M42-03 (Priority: P1) — Intra-Fold Two-Layer Fitting (Anti-Leakage)
As an experiment runner,  
I want `fit_two_layer_preprocessing` to estimate all transformer parameters exclusively from `X_train` of the current fold,  
So that no evaluation, validation, or test statistics leak into the feature transformation state (`CA-E4B-01`).

### US-M42-04 (Priority: P1) — Stateless Evaluation Projection
As an evaluation pipeline,  
I want `apply_two_layer_preprocessing` to transform `X_train` or `X_eval` using only the pre-fitted state,  
So that features are projected consistently without recalculating parameters or mutating the state.

### US-M42-05 (Priority: P1) — Numerical Scalers in Pure NumPy
As an algorithm developer,  
I want pure NumPy implementations of standard scalers (`StandardScaler`, `MinMaxScaler`, `MaxAbsScaler`, `RobustScaler`, and angular normalization for quantum gates),  
So that the framework scales numerical data accurately without requiring scikit-learn in the runtime (`XCUT-02`).

### US-M42-06 (Priority: P2) — Precomputed Kernel Partition Passing
As a quantum/kernel researcher,  
I want the Layer 2 preprocessor to pass $(\mathbf{X}_{\text{train}}, \mathbf{X}_{\text{train}})$ during fold training and $(\mathbf{X}_{\text{eval}}, \mathbf{X}_{\text{train}})$ during inference to my external kernel function,  
So that precomputed Gram matrices are constructed correctly without data leakage (`RF3.4`).

### US-M42-07 (Priority: P2) — Public API Exports and Runtime Purity
As a software engineer,  
I want `experimental_ml.models.preprocessing` to export its public API and enforce single runtime dependency (`numpy>=1.24.0`),  
So that the codebase remains modular, portable, and layered (`XCUT-01`, `XCUT-02`).

## Acceptance Criteria

### Criteria for US-M42-01 (Types & Enums)
- **AC-M42-01-01 (Ubiquitous):** The system SHALL define `ScalerType` as a closed `str, Enum` with members `STANDARD`, `MINMAX`, `MAXABS`, `ROBUST`, `ANGULAR`, and `NONE`.
- **AC-M42-01-02 (Ubiquitous):** The system SHALL define `PreprocessingStepSpec` as an immutable frozen dataclass with slots containing `step_id: str`, `transformer_type: str`, `parameters: MappingProxyType[str, Any]`, and `description: str`.
- **AC-M42-01-03 (Ubiquitous):** The system SHALL define `TwoLayerPreprocessingSpec` as an immutable frozen dataclass with slots containing `layer1_steps: tuple[PreprocessingStepSpec, ...]`, `layer2_steps: tuple[PreprocessingStepSpec, ...]`, and `description: str`.
- **AC-M42-01-04 (Ubiquitous):** The system SHALL define `TwoLayerPreprocessingState` as an immutable frozen dataclass with slots containing `spec: TwoLayerPreprocessingSpec`, `layer1_fitted_state: tuple[Any, ...]`, and `layer2_fitted_state: tuple[Any, ...]`.

### Criteria for US-M42-02 (Duplication Detection & Declarative Validation)
- **AC-M42-02-01 (Event-driven):** WHEN `validate_two_layer_preprocessing` is invoked with a valid `TwoLayerPreprocessingSpec`, THEN the system SHALL return the validated spec without mutating fields.
- **AC-M42-02-02 (Unwanted-behavior):** IF `TwoLayerPreprocessingSpec` declares the same scaler or standardization transformation in both Layer 1 and Layer 2, THEN `validate_two_layer_preprocessing` SHALL raise `ConfigurationError` (`CA-E3-02`).
- **AC-M42-02-03 (Unwanted-behavior):** IF any `PreprocessingStepSpec` contains an empty `step_id`, an unrecognized `transformer_type`, or invalid parameters, THEN the system SHALL raise `ConfigurationError`.
- **AC-M42-02-04 (State-driven):** WHILE `layer1_steps` and `layer2_steps` are empty, `validate_two_layer_preprocessing` SHALL accept the empty specification as a valid pass-through pipeline.

### Criteria for US-M42-03 (Intra-Fold Fitting)
- **AC-M42-03-01 (Event-driven):** WHEN `fit_two_layer_preprocessing` is executed with 2D `X_train` and a valid `TwoLayerPreprocessingSpec`, THEN the system SHALL fit Layer 1 on `X_train`, apply Layer 1 to produce intermediate `X_inter`, fit Layer 2 on `X_inter`, and return an immutable `TwoLayerPreprocessingState`.
- **AC-M42-03-02 (State-driven):** WHILE fitting the two-layer preprocessing, the system SHALL ensure that all fitted statistics (means, standard deviations, minimums, maximums, quantiles) depend strictly on `X_train` without referencing evaluation data (`CA-E4B-01`).
- **AC-M42-03-03 (Unwanted-behavior):** IF `fit_two_layer_preprocessing` receives a 1D array, an array with $N=0$ samples, or non-finite values, THEN the system SHALL raise `ContractViolationError`.

### Criteria for US-M42-04 (Stateless Evaluation Projection)
- **AC-M42-04-01 (Event-driven):** WHEN `apply_two_layer_preprocessing` is executed with 2D `X_eval` and a fitted `TwoLayerPreprocessingState`, THEN the system SHALL project `X_eval` through Layer 1 followed by Layer 2 using strictly the stored state parameters and return a transformed 2D `np.ndarray`.
- **AC-M42-04-02 (Ubiquitous):** The system SHALL ensure that `apply_two_layer_preprocessing` does not re-estimate or alter any parameter in `TwoLayerPreprocessingState`.
- **AC-M42-04-03 (Unwanted-behavior):** IF `apply_two_layer_preprocessing` receives `X_eval` with a feature count differing from the feature count expected by the fitted state, THEN the system SHALL raise `ContractViolationError`.

### Criteria for US-M42-05 (Pure NumPy Scalers)
- **AC-M42-05-01 (Event-driven):** WHEN `StandardScaler` is fitted on `X_train`, THEN `transform` SHALL produce features centered to mean $0.0$ and unit variance $1.0$, handling constant columns (zero variance) by outputting $0.0$ without division-by-zero errors.
- **AC-M42-05-02 (Event-driven):** WHEN `MinMaxScaler` is fitted on `X_train` with range $[a, b]$, THEN `transform` SHALL scale features into $[a, b]$, handling constant columns by outputting the lower bound $a$.
- **AC-M42-05-03 (Event-driven):** WHEN `MaxAbsScaler` is fitted on `X_train`, THEN `transform` SHALL scale features into $[-1.0, 1.0]$ based on maximum absolute value, handling all-zero columns by outputting $0.0$.
- **AC-M42-05-04 (Event-driven):** WHEN `RobustScaler` is fitted on `X_train`, THEN `transform` SHALL center by median and scale by interquartile range (IQR), handling zero IQR columns by outputting $0.0$.
- **AC-M42-05-05 (Event-driven):** WHEN `AngularScaler` is fitted on `X_train`, THEN `transform` SHALL scale features linearly into $[0.0, \pi]$ (or $[-\pi, \pi]$) for parameterized quantum gate encoding.

### Criteria for US-M42-06 (Precomputed Kernel Adapter)
- **AC-M42-06-01 (Event-driven):** WHEN a precomputed kernel function is configured in Layer 2, THEN `fit_two_layer_preprocessing` SHALL invoke the external kernel function passing $(\mathbf{X}_{\text{train}}, \mathbf{X}_{\text{train}})$ and store a defensive copy of $\mathbf{X}_{\text{train}}$ in the fitted state (`RF3.4`).
- **AC-M42-06-02 (Event-driven):** WHEN `apply_two_layer_preprocessing` is invoked on evaluation data $\mathbf{X}_{\text{eval}}$ for a precomputed kernel, THEN the system SHALL invoke the external kernel function passing $(\mathbf{X}_{\text{eval}}, \mathbf{X}_{\text{train}})$ and produce the Gram matrix of shape $(N_{\text{eval}}, N_{\text{train}})$.
- **AC-M42-06-03 (Unwanted-behavior):** IF the external kernel function produces non-square matrices during training, non-finite values, or dimensions mismatched with $N_{\text{train}}$, THEN `fit_two_layer_preprocessing` SHALL raise `ContractViolationError`.

### Criteria for US-M42-07 (Public API and Runtime Purity)
- **AC-M42-07-01 (Ubiquitous):** The system SHALL export all preprocessing models, scalers, and functions via `src/experimental_ml/models/preprocessing/__init__.py` and re-export primary functions in `src/experimental_ml/models/__init__.py`.
- **AC-M42-07-02 (Ubiquitous):** The system SHALL maintain single runtime dependency (`numpy>=1.24.0`), with zero mandatory third-party ML framework imports in the preprocessing subsystem (`XCUT-02`).

## Requirement Traceability

| Requirement ID | Acceptance Criterion | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| PRE-01 | AC-M42-01-01, AC-M42-01-02, AC-M42-01-03, AC-M42-01-04 | Unit tests on enums, frozen specs, and state immutability (`test_preprocessing_types.py`) | pending |
| PRE-02 | AC-M42-02-01, AC-M42-02-02, AC-M42-02-03, AC-M42-02-04 | Unit tests on `validate_two_layer_preprocessing` conflict and duplication rejection (`test_preprocessing_validation.py`) | pending |
| PRE-03 | AC-M42-03-01, AC-M42-03-02, AC-M42-03-03 | Unit tests verifying that `fit_two_layer_preprocessing` parameters depend strictly on `X_train` (`test_preprocessing_fit.py`) | pending |
| PRE-04 | AC-M42-04-01, AC-M42-04-02, AC-M42-04-03 | Unit tests verifying stateless projection and dimension checks in `apply_two_layer_preprocessing` (`test_preprocessing_apply.py`) | pending |
| PRE-05 | AC-M42-05-01, AC-M42-05-02, AC-M42-05-03, AC-M42-05-04, AC-M42-05-05 | Unit tests on NumPy scalers under standard and degenerate zero-variance conditions (`test_preprocessing_scalers.py`) | pending |
| PRE-06 | AC-M42-06-01, AC-M42-06-02, AC-M42-06-03 | Unit tests on precomputed kernel passing $(X_{\text{train}}, X_{\text{train}})$ and $(X_{\text{eval}}, X_{\text{train}})$ (`test_preprocessing_kernel.py`) | pending |
| PRE-07 | AC-M42-07-01, AC-M42-07-02 | Subprocess inspection verifying runtime purity without external ML imports (`test_preprocessing_integration.py`) | pending |
