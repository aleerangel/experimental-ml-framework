# Registro de Validação e Aceite — Marco M4.2 (Pipeline de Pré-processamento em Duas Camadas)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M4.2 (`m4-2-two-layer-preprocessing`)  
> **Data de Validação:** 11 de Novembro de 2026  
> **Commit de Implementação:** [`bece29c`](https://github.com/alexandrerangel/experimental-ml-framework/commit/bece29c)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via subprocesso e ambiente `.venv` (`XCUT-02`) | **APROVADO** |
| **Testes Unitários Automatizados** | 22 testes em `tests/unit/models/` (C1 a C22) | 22 testes de pré-processamento aprovados (56 testes totais em `tests/unit/models/`) | **APROVADO** |
| **Testes de Integração e Invariantes** | 2 testes em `tests/integration/models/` (C23 e C24) + 1 teste E2E | 3 testes aprovados (5 testes totais em `tests/integration/models/`) | **APROVADO** |
| **Testes de Regressão Geral** | 297 testes em `pytest tests/` | 297 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria independente | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (7 capacidades) | Executado com sucesso via interfaces públicas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Modelos Unitária e Integração

Execução no ambiente `.venv` (`.venv/bin/pytest tests/unit/models/ tests/integration/models/ -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 61 items

tests/unit/models/test_model_baselines.py::test_m41_08_01_dummy_baseline_regression_mean PASSED [  1%]
tests/unit/models/test_model_baselines.py::test_m41_08_02_dummy_baseline_regression_median PASSED [  3%]
tests/unit/models/test_model_baselines.py::test_m41_08_03_dummy_baseline_classification_most_frequent PASSED [  4%]
tests/unit/models/test_model_baselines.py::test_m41_08_04_analytical_biometric_model_direct_eval PASSED [  6%]
tests/unit/models/test_model_baselines.py::test_m41_08_05_analytical_biometric_model_missing_feature_rejection PASSED [  8%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_01_extract_model_diagnostics_structure PASSED [  9%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_02_extract_model_diagnostics_snapshot_independence PASSED [ 11%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection PASSED [ 13%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_04_extract_model_diagnostics_model_mutation_invariance PASSED [ 14%]
tests/unit/models/test_model_fit.py::test_m41_04_01_fit_model_trainable PASSED [ 16%]
tests/unit/models/test_model_fit.py::test_m41_04_02_fit_model_analytical_bypass PASSED [ 18%]
tests/unit/models/test_model_fit.py::test_m41_04_03_fit_model_dimension_mismatch_and_empty PASSED [ 19%]
tests/unit/models/test_model_instantiation.py::test_m41_03_01_instantiate_fresh_model_with_seed PASSED [ 21%]
tests/unit/models/test_model_instantiation.py::test_m41_03_02_instantiate_fresh_model_seed_none PASSED [ 22%]
tests/unit/models/test_model_instantiation.py::test_m41_03_03_instantiate_fresh_model_singleton_rejection PASSED [ 24%]
tests/unit/models/test_model_instantiation.py::test_m41_03_04_instantiate_fresh_model_factory_error_handling PASSED [ 26%]
tests/unit/models/test_model_instantiation.py::test_m41_03_05_instantiate_fresh_model_instance_isolation PASSED [ 27%]
tests/unit/models/test_model_predict.py::test_m41_05_01_predict_model_output_structure PASSED [ 29%]
tests/unit/models/test_model_predict.py::test_m41_05_02_predict_model_uncertainty_valid PASSED [ 31%]
tests/unit/models/test_model_predict.py::test_m41_05_03_predict_model_predict_proba_valid PASSED [ 32%]
tests/unit/models/test_model_predict.py::test_m41_05_04_predict_model_uncertainty_disabled_none PASSED [ 34%]
tests/unit/models/test_model_predict.py::test_m41_05_05_predict_model_predict_proba_disabled_none PASSED [ 36%]
tests/unit/models/test_model_predict.py::test_m41_05_06_predict_model_unfitted_rejection PASSED [ 37%]
tests/unit/models/test_model_predict.py::test_m41_05_07_predict_model_uncertainty_runtime_violation PASSED [ 39%]
tests/unit/models/test_model_predict.py::test_m41_05_08_predict_model_predict_proba_runtime_violation PASSED [ 40%]
tests/unit/models/test_model_spec.py::test_m41_02_01_model_spec_dataclass PASSED [ 42%]
tests/unit/models/test_model_spec.py::test_m41_02_02_validate_model_spec_valid PASSED [ 44%]
tests/unit/models/test_model_spec.py::test_m41_02_03_validate_model_spec_invalid_fields PASSED [ 45%]
tests/unit/models/test_model_spec.py::test_m41_02_04_validate_model_spec_contradictory_capabilities PASSED [ 47%]
tests/unit/models/test_model_spec.py::test_m41_07_01_validate_models_catalog_valid PASSED [ 49%]
tests/unit/models/test_model_spec.py::test_m41_07_02_validate_models_catalog_duplicate_ids PASSED [ 50%]
tests/unit/models/test_model_types.py::test_m41_01_01_model_family_enum PASSED [ 52%]
tests/unit/models/test_model_types.py::test_m41_01_02_model_capabilities_dataclass PASSED [ 54%]
tests/unit/models/test_model_types.py::test_m41_01_03_model_diagnostics_dataclass PASSED [ 55%]
tests/unit/models/test_preprocessing_apply.py::test_m42_04_01_apply_two_layer_preprocessing_projection PASSED [ 57%]
tests/unit/models/test_preprocessing_apply.py::test_m42_04_02_apply_two_layer_preprocessing_state_immutability PASSED [ 59%]
tests/unit/models/test_preprocessing_apply.py::test_m42_04_03_apply_two_layer_preprocessing_feature_count_mismatch PASSED [ 60%]
tests/unit/models/test_preprocessing_fit.py::test_m42_03_01_fit_two_layer_preprocessing_execution PASSED [ 62%]
tests/unit/models/test_preprocessing_fit.py::test_m42_03_02_fit_two_layer_preprocessing_anti_leakage PASSED [ 63%]
tests/unit/models/test_preprocessing_fit.py::test_m42_03_03_fit_two_layer_preprocessing_invalid_inputs PASSED [ 65%]
tests/unit/models/test_preprocessing_kernel.py::test_m42_06_01_kernel_adapter_fit_partition_passing PASSED [ 67%]
tests/unit/models/test_preprocessing_kernel.py::test_m42_06_02_kernel_adapter_transform_partition_passing PASSED [ 68%]
tests/unit/models/test_preprocessing_kernel.py::test_m42_06_03_kernel_adapter_invalid_matrix_rejection PASSED [ 70%]
tests/unit/models/test_preprocessing_scalers.py::test_m42_05_01_standard_scaler_zero_variance PASSED [ 72%]
tests/unit/models/test_preprocessing_scalers.py::test_m42_05_02_minmax_scaler_constant_columns PASSED [ 73%]
tests/unit/models/test_preprocessing_scalers.py::test_m42_05_03_maxabs_scaler_zero_columns PASSED [ 75%]
tests/unit/models/test_preprocessing_scalers.py::test_m42_05_04_robust_scaler_zero_iqr PASSED [ 77%]
tests/unit/models/test_preprocessing_scalers.py::test_m42_05_05_angular_scaler_quantum_gates PASSED [ 78%]
tests/unit/models/test_preprocessing_types.py::test_m42_01_01_scaler_type_enum PASSED [ 80%]
tests/unit/models/test_preprocessing_types.py::test_m42_01_02_preprocessing_step_spec PASSED [ 81%]
tests/unit/models/test_preprocessing_types.py::test_m42_01_03_two_layer_preprocessing_spec PASSED [ 83%]
tests/unit/models/test_preprocessing_types.py::test_m42_01_04_two_layer_preprocessing_state PASSED [ 85%]
tests/unit/models/test_preprocessing_validation.py::test_m42_02_01_validate_two_layer_valid PASSED [ 86%]
tests/unit/models/test_preprocessing_validation.py::test_m42_02_02_validate_two_layer_duplication_rejection PASSED [ 88%]
tests/unit/models/test_preprocessing_validation.py::test_m42_02_03_validate_two_layer_invalid_step PASSED [ 90%]
tests/unit/models/test_preprocessing_validation.py::test_m42_02_04_validate_two_layer_empty_passthrough PASSED [ 91%]
tests/integration/models/test_models_integration.py::test_m41_09_01_runtime_purity_numpy_only PASSED [ 93%]
tests/integration/models/test_models_integration.py::test_models_end_to_end_lifecycle_pipeline PASSED [ 95%]
tests/integration/models/test_preprocessing_integration.py::test_m42_07_01_public_api_exports PASSED [ 96%]
tests/integration/models/test_preprocessing_integration.py::test_m42_07_02_runtime_purity_numpy_only PASSED [ 98%]
tests/integration/models/test_preprocessing_integration.py::test_preprocessing_end_to_end_two_layer_pipeline PASSED [100%]

============================== 61 passed in 0.40s ==============================
```

### 2.2 Suíte Completa de Regressão

Execução no ambiente `.venv` (`.venv/bin/pytest tests/ -q`):

```text
297 passed in 4.80s
```

---

## 3. Julgamento do Verificador Independente (`verification.md`)

- **Veredito:** `PASS`
- **Compromisso Avaliado:** `proofs.md` at `bece29c`
- **Validação de Checks:** Todos os 24 checks (`C1` a `C24`) foram inspecionados frente aos testes associados e sustentam com rigor os critérios de aceitação formalmente especificados.
- **Sondagens com Exemplos Próprios:**
  - *Sondagem 1 (Escalonadores em N=1 amostra):* Verificado comportamento matemático de `StandardScaler` (variância zero `ddof=0` gerando 0.0), `MinMaxScaler` (min=max gerando limite inferior), e `RobustScaler` (IQR zero gerando 0.0), todos estáveis sem divisão por zero.
  - *Sondagem 2 (Especificação assimétrica com Camada 1 ou Camada 2 isolada):* Verificado ajuste e projeção contendo apenas Camada 1 ou apenas Camada 2, preservando validação e projeção corretas.
  - *Sondagem 3 (AngularScaler com intervalo simétrico $[-\pi, \pi]$):* Verificada projeção linear customizada de portas quânticas mapeando extremos para $[-\pi, \pi]$.
  - *Sondagem 4 (PrecomputedKernelAdapter unitário):* Verificado cálculo de Gram $1 \times 1$ com dimensões consistentes.
- **Apontamentos:** Nenhum achado impeditivo (`None`).

---

## 4. Conformidade Arquitetural e Metodológica

1. **Prevenção de Duplicação Acidental (`CA-E3-02`):**
   - `validate_two_layer_preprocessing` detecta e rejeita a declaração do mesmo transformador ou de escalonadores redundantes entre a Camada 1 (cenário) e a Camada 2 (modelo), garantindo que padronizações ou normalizações não sejam aplicadas repetidamente.
2. **Garantia Anti-Vazamento Intra-Fold (`CA-E4B-01`):**
   - `fit_two_layer_preprocessing` ajusta a Camada 1 sobre $X_{\text{train}}$, projeta o estado intermediário $X_{\text{inter}}$, e ajusta a Camada 2 estritamente sobre $X_{\text{inter}}$, assegurando que nenhuma estatística de teste ou avaliação participe da estimativa dos parâmetros.
3. **Projeção Funcional sem Estado (`PRE-04`):**
   - `apply_two_layer_preprocessing` projeta $X_{\text{eval}}$ utilizando exclusivamente os parâmetros pré-ajustados congelados em `TwoLayerPreprocessingState`, mantendo imutabilidade absoluta dos objetos de estado.
4. **Passagem de Partição para Kernels Pré-computados (`RF3.4`):**
   - `PrecomputedKernelAdapter` avalia $(X_{\text{train}}, X_{\text{train}})$ no ajuste do *fold* e $(X_{\text{eval}}, X_{\text{train}})$ na transformação de inferência, viabilizando o uso de modelos quânticos e kernels de Gram sem violar o isolamento das partições.
5. **Pureza de Runtime e Dependência Única (`XCUT-02`):**
   - Todo o subsistema de pré-processamento opera exclusivamente sobre `numpy>=1.24.0` e a biblioteca padrão, com zero dependências mandatórias de frameworks terceiros (`sklearn`, `scipy`, `torch`).

---

## 5. Decisão Formal de Aceite

- **Decisão:** `APROVADO`
- **Justificativa:** Todos os 7 requisitos (`PRE-01` a `PRE-07`) foram implementados com 100% de aprovação na suíte automatizada (25 testes específicos de pré-processamento, 61 testes no módulo de modelos e 297 testes na suíte global), verificação independente TLC com veredito `PASS` e conformidade metodológica comprovada no roteiro de aceitação.
