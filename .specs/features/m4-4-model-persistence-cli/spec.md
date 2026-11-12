# Feature: m4-4-model-persistence-cli

**Approved**: 2026-11-11 - user: "aprovado"

## Problem Statement

Na arquitetura do `experimental-ml-framework`, a Etapa 3 consolida o registro formal de modelos, pré-processamento em duas camadas e espaços de busca de hiperparâmetros (**RF3.1**, **RF3.4**, **RF3.5**, **STORE-03**, **STORE-05** e **ARQUITETURA §2.4, §5**):
1. **Persistência Declarativa de Modelos:** Para que a matriz experimental da Etapa 4 possa ser executada de forma reproduzível e auditável, o catálogo de modelos deve ser persistido atomicamente no arquivo canônico `configuration/models.json`, serializando metadados, famílias, capacidades declaradas, configurações de pré-processamento e especificações de busca de hiperparâmetros.
2. **Resolução Segura de Estimadores:** Na desserialização do catálogo, as fábricas de estimadores (`estimator_factory`) devem ser resolvidas deterministicamente a partir de identificadores canônicos para baselines nativos (`DUMMY_BASELINE_MEAN`, `DUMMY_BASELINE_MEDIAN`, `DUMMY_BASELINE_MOST_FREQUENT`, `ANALYTICAL_BIOMETRIC`) ou a partir de caminhos de importação padrão Python (`module:qualname`), com validação estrita de tipos e capacidades.
3. **Portão de Estágio de Modelos (`verify_models_gate`):** O framework deve fornecer um portão de transição determinístico em `src/experimental_ml/stages/stage_gates.py` que valide a pré-condição da Etapa 1 (`verify_preparation_gate`), a presença de `configuration/models.json`, a integridade do catálogo e a coerência entre pré-processamento, modelo e busca de hiperparâmetros antes do avanço para a execução matricial.
4. **Interface CLI Modularizada (`expml models`):** O pesquisador deve ser capaz de operar a validação e a verificação de modelos pelo terminal através dos subcomandos `expml models validate` e `expml models verify`, com códigos de saída padronizados (0 sucesso, 2 erro de domínio/validação), salvaguardas contra sobrescrita acidental e adesão rigorosa à pureza de importação da CLI (`CLI-10`: zero importações de NumPy ou bibliotecas pesadas no escopo do módulo `cmd_models.py`).

## Out of Scope

- Orquestração da matriz experimental $(M \times C \times F)$ — escopo do Marco M5 (`orchestration`).
- Serialização binária de pesos ou estados treinados (ex.: `.pkl`, `.onnx`, `.joblib`) — modelos são instanciados e ajustados dinamicamente em cada dobra da matriz da Etapa 4B.
- Subcomandos de execução `expml run` — escopo do Marco M5.
- Novas dependências de runtime além de `numpy>=1.24.0` e a biblioteca padrão (`XCUT-02`).

## Assumptions & Open Questions

**Open questions:** none - os padrões e contratos da CLI e dos portões de estágio já foram formalmente estabelecidos nos marcos M1.4, M2.4, M3.4 e na Arquitetura (§2.4 e §5).

| Assumption / Question | Chosen default | Rationale |
| :--- | :--- | :--- |
| Caminho canônico de persistência | `configuration/models.json` dentro do diretório do experimento | Alinhado com a taxonomia canônica da Arquitetura §5 e D11 |
| Resolução de fábrica declarativa | Nomes canônicos reservados para baselines e string `module:callable` para estimadores externos | Permite reprodutibilidade sem acoplamento a código proprietário ou caminhos rígidos |
| Gravação atômica | Escrita em `<path>.tmp.<pid>` seguida de `os.replace` atômico | Previne corrupção de arquivos em caso de falha ou interrupção durante a escrita |
| Pré-condição do portão de modelos | `verify_preparation_gate(experiment_dir)` | Etapa 3 exige que a base de dados esteja perfilada e pronta com status READY |
| Pureza de importação na CLI (`CLI-10`) | Importações diferidas no corpo dos handlers `cmd_models.py` | Garante inicialização instantânea e pureza de dependências no CLI dispatcher |

## User Stories

### US-M44-01 (Priority: P1) — ModelsCatalog Data Model and Codecs
As an experimental ML researcher,  
I want declarative serialization and deserialization codecs for `ModelsCatalog` and `ModelSpec`,  
So that models, capabilities, preprocessing specs, and tuning spaces can be represented in valid JSON.

### US-M44-02 (Priority: P1) — Estimator Factory Resolution
As a framework integrator,  
I want declarative factory resolution supporting canonical baseline identifiers and standard Python import paths (`module:callable`),  
So that estimators can be loaded reliably from configuration without hardcoded imports.

### US-M44-03 (Priority: P1) — Atomic Persistence and Catalog Loading
As a pipeline executor,  
I want `save_models_catalog` and `load_models_catalog` to write atomically and read configurations safely,  
So that partial writes or disk corruption never compromise `configuration/models.json`.

### US-M44-04 (Priority: P1) — Models Stage Gate Verification
As a workflow controller,  
I want `verify_models_gate` to check upstream preparation preconditions and validate the models catalog,  
So that matrix execution in Stage 4 cannot begin with missing, corrupt, or invalid model configurations.

### US-M44-05 (Priority: P1) — CLI models validate Subcommand
As a terminal operator,  
I want `expml models validate` to validate a JSON file of models and save it atomically to `configuration/models.json`,  
So that models can be configured and persisted from the command line with overwrite protection.

### US-M44-06 (Priority: P1) — CLI models verify Subcommand
As a CI/CD or audit system,  
I want `expml models verify` to check the models stage gate and return standardized exit codes (0 for valid, 2 for error),  
So that downstream execution gates can be verified non-interactively.

### US-M44-07 (Priority: P2) — CLI Import Purity and End-to-End Integration
As a software engineer,  
I want `src/experimental_ml/cli/cmd_models.py` to maintain zero module-level heavy imports and pass full pipeline tests,  
So that CLI responsiveness and architectural layering are preserved (`CLI-10`, `XCUT-01`, `XCUT-02`).

## Acceptance Criteria

### Criteria for US-M44-01 (ModelsCatalog Model and Codecs)
- **AC-M44-01-01 (Ubiquitous):** The system SHALL define `ModelsCatalog` as an immutable frozen dataclass with slots containing `models: tuple[ModelSpec, ...]`, `metadata: MappingProxyType[str, Any]`, and `catalog_hash: str`.
- **AC-M44-01-02 (Event-driven):** WHEN `ModelsCatalog.to_dict()` is called, THEN the system SHALL return a JSON-serializable dictionary representing all model specs, capabilities, preprocessing specs, and search specs.
- **AC-M44-01-03 (Event-driven):** WHEN `ModelsCatalog.from_dict(data)` is called with valid catalog dictionary, THEN the system SHALL reconstruct the immutable `ModelsCatalog` instance.

### Criteria for US-M44-02 (Estimator Factory Resolution)
- **AC-M44-02-01 (Event-driven):** WHEN resolving canonical identifiers `DUMMY_BASELINE_MEAN`, `DUMMY_BASELINE_MEDIAN`, `DUMMY_BASELINE_MOST_FREQUENT`, or `ANALYTICAL_BIOMETRIC`, THEN the system SHALL return the corresponding built-in estimator factory.
- **AC-M44-02-02 (Event-driven):** WHEN resolving a valid dotted path string in format `module:callable`, THEN the system SHALL import and return the referenced callable factory.
- **AC-M44-02-03 (Unwanted-behavior):** IF a factory string references a non-existent module, attribute, or non-callable object, THEN the system SHALL raise `ConfigurationError`.

### Criteria for US-M44-03 (Atomic Persistence and Loading)
- **AC-M44-03-01 (Event-driven):** WHEN `save_models_catalog` writes to disk, THEN the system SHALL write to a temporary file `<path>.tmp.<pid>` and atomically replace it onto the target path.
- **AC-M44-03-02 (Unwanted-behavior):** IF the destination file already exists and `overwrite=False`, THEN `save_models_catalog` SHALL raise `ConfigurationError`.
- **AC-M44-03-03 (Event-driven):** WHEN `load_models_catalog(path)` is called on an existing `models.json`, THEN the system SHALL parse, validate, and return the `ModelsCatalog`.

### Criteria for US-M44-04 (Models Stage Gate)
- **AC-M44-04-01 (Event-driven):** WHEN `verify_models_gate` is invoked on an experiment directory with valid Stage 1 and Stage 3 artifacts, THEN the system SHALL verify preparation gate preconditions and return the validated `ModelsCatalog`.
- **AC-M44-04-02 (Unwanted-behavior):** IF `configuration/models.json` is missing or contains duplicate `model_id` values, THEN `verify_models_gate` SHALL raise `DataIntegrityError` or `ContractViolationError`.
- **AC-M44-04-03 (Unwanted-behavior):** IF the upstream preparation gate is not READY, THEN `verify_models_gate` SHALL raise `ContractViolationError`.

### Criteria for US-M44-05 (CLI models validate Subcommand)
- **AC-M44-05-01 (Event-driven):** WHEN `expml models validate --experiment-dir <dir> --models <path>` is executed with valid inputs, THEN the system SHALL validate the models catalog, write `configuration/models.json`, print a summary, and exit with code 0.
- **AC-M44-05-02 (Unwanted-behavior):** IF `configuration/models.json` already exists and `--force` is not provided, THEN the CLI SHALL print an error and exit with code 2.
- **AC-M44-05-03 (Unwanted-behavior):** IF `--models` points to a non-existent or invalid JSON file, THEN the CLI SHALL print an error and exit with code 2.

### Criteria for US-M44-06 (CLI models verify Subcommand)
- **AC-M44-06-01 (Event-driven):** WHEN `expml models verify --experiment-dir <dir>` is executed on an experiment directory with a verified models gate, THEN the CLI SHALL print verification details and exit with code 0.
- **AC-M44-06-02 (Unwanted-behavior):** IF the models gate fails due to missing files or validation errors, THEN the CLI SHALL print an error to stderr and exit with code 2.

### Criteria for US-M44-07 (CLI Import Purity and End-to-End Suite)
- **AC-M44-07-01 (Ubiquitous):** The system SHALL ensure that `cmd_models.py` does not import `numpy`, `scipy`, `sklearn`, or heavy modules at file level (`CLI-10`).
- **AC-M44-07-02 (Ubiquitous):** The system SHALL provide an end-to-end integration test executing `expml models validate` and `expml models verify` via `subprocess.run`, verifying exit codes and generated artifacts.

## Requirement Traceability

| Requirement ID | Acceptance Criterion | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| MPC-01 | AC-M44-01-01, AC-M44-01-02, AC-M44-01-03 | Unit tests on ModelsCatalog dataclass and dictionary codecs (`test_models_codecs.py`) | pending |
| MPC-02 | AC-M44-02-01, AC-M44-02-02, AC-M44-02-03 | Unit tests on factory resolution for built-ins and custom paths (`test_models_resolution.py`) | pending |
| MPC-03 | AC-M44-03-01, AC-M44-03-02, AC-M44-03-03 | Unit tests on atomic saving, overwrite guard, and loading (`test_models_storage.py`) | pending |
| MPC-04 | AC-M44-04-01, AC-M44-04-02, AC-M44-04-03 | Unit tests on `verify_models_gate` precondition and invariant checks (`test_models_stage_gate.py`) | pending |
| MPC-05 | AC-M44-05-01, AC-M44-05-02, AC-M44-05-03 | Unit tests on `expml models validate` CLI handler and error branches (`test_cli_models_validate.py`) | pending |
| MPC-06 | AC-M44-06-01, AC-M44-06-02 | Unit tests on `expml models verify` CLI handler and error branches (`test_cli_models_verify.py`) | pending |
| MPC-07 | AC-M44-07-01, AC-M44-07-02 | Subprocess test asserting CLI import purity and full CLI pipeline (`test_models_cli_integration.py`) | pending |
