# Registro de Validação e Aceite — Marco M4.1 (Registro de Modelos, Capacidades e Contratos Funcionais)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M4.1 (`m4-1-model-registry-contracts`)  
> **Data de Validação:** 11 de Novembro de 2026  
> **Commit de Implementação:** [`6d0aa19`](https://github.com/alexandrerangel/experimental-ml-framework/commit/6d0aa19)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via subprocesso e ambiente `.venv` (`XCUT-02`) | **APROVADO** |
| **Testes Unitários Automatizados** | 34 testes em `tests/unit/models/` | 34 testes aprovados (100%) | **APROVADO** |
| **Testes de Integração e Invariantes** | 2 testes em `tests/integration/models/` | 2 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 272 testes em `pytest tests/` | 272 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria independente | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (6 capacidades) | Executado com sucesso via interfaces públicas | **APROVADO** |

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
collecting ... collected 36 items

tests/unit/models/test_model_types.py::test_m41_01_01_model_family_enum PASSED [  2%]
tests/unit/models/test_model_types.py::test_m41_01_02_model_capabilities_dataclass PASSED [  5%]
tests/unit/models/test_model_types.py::test_m41_01_03_model_diagnostics_dataclass PASSED [  8%]
tests/unit/models/test_model_spec.py::test_m41_02_01_model_spec_dataclass PASSED [ 11%]
tests/unit/models/test_model_spec.py::test_m41_02_02_validate_model_spec_valid PASSED [ 13%]
tests/unit/models/test_model_spec.py::test_m41_02_03_validate_model_spec_invalid_fields PASSED [ 16%]
tests/unit/models/test_model_spec.py::test_m41_02_04_validate_model_spec_contradictory_capabilities PASSED [ 19%]
tests/unit/models/test_model_spec.py::test_m41_07_01_validate_models_catalog_valid PASSED [ 22%]
tests/unit/models/test_model_spec.py::test_m41_07_02_validate_models_catalog_duplicate_ids PASSED [ 25%]
tests/unit/models/test_model_instantiation.py::test_m41_03_01_instantiate_fresh_model_with_seed PASSED [ 27%]
tests/unit/models/test_model_instantiation.py::test_m41_03_02_instantiate_fresh_model_seed_none PASSED [ 30%]
tests/unit/models/test_model_instantiation.py::test_m41_03_03_instantiate_fresh_model_singleton_rejection PASSED [ 33%]
tests/unit/models/test_model_instantiation.py::test_m41_03_04_instantiate_fresh_model_factory_error_handling PASSED [ 36%]
tests/unit/models/test_model_instantiation.py::test_m41_03_05_instantiate_fresh_model_instance_isolation PASSED [ 38%]
tests/unit/models/test_model_fit.py::test_m41_04_01_fit_model_trainable PASSED [ 41%]
tests/unit/models/test_model_fit.py::test_m41_04_02_fit_model_analytical_bypass PASSED [ 44%]
tests/unit/models/test_model_fit.py::test_m41_04_03_fit_model_dimension_mismatch_and_empty PASSED [ 47%]
tests/unit/models/test_model_predict.py::test_m41_05_01_predict_model_output_structure PASSED [ 50%]
tests/unit/models/test_model_predict.py::test_m41_05_02_predict_model_uncertainty_valid PASSED [ 52%]
tests/unit/models/test_model_predict.py::test_m41_05_03_predict_model_predict_proba_valid PASSED [ 55%]
tests/unit/models/test_model_predict.py::test_m41_05_04_predict_model_uncertainty_disabled_none PASSED [ 58%]
tests/unit/models/test_model_predict.py::test_m41_05_05_predict_model_predict_proba_disabled_none PASSED [ 61%]
tests/unit/models/test_model_predict.py::test_m41_05_06_predict_model_unfitted_rejection PASSED [ 63%]
tests/unit/models/test_model_predict.py::test_m41_05_07_predict_model_uncertainty_runtime_violation PASSED [ 66%]
tests/unit/models/test_model_predict.py::test_m41_05_08_predict_model_predict_proba_runtime_violation PASSED [ 69%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_01_extract_model_diagnostics_structure PASSED [ 72%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_02_extract_model_diagnostics_snapshot_independence PASSED [ 75%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection PASSED [ 77%]
tests/unit/models/test_model_diagnostics.py::test_m41_06_04_extract_model_diagnostics_model_mutation_invariance PASSED [ 80%]
tests/unit/models/test_model_baselines.py::test_m41_08_01_dummy_baseline_regression_mean PASSED [ 83%]
tests/unit/models/test_model_baselines.py::test_m41_08_02_dummy_baseline_regression_median PASSED [ 86%]
tests/unit/models/test_model_baselines.py::test_m41_08_03_dummy_baseline_classification_most_frequent PASSED [ 88%]
tests/unit/models/test_model_baselines.py::test_m41_08_04_analytical_biometric_model_direct_eval PASSED [ 91%]
tests/unit/models/test_model_baselines.py::test_m41_08_05_analytical_biometric_model_missing_feature_rejection PASSED [ 94%]
tests/integration/models/test_models_integration.py::test_m41_09_01_runtime_purity_numpy_only PASSED [ 97%]
tests/integration/models/test_models_integration.py::test_models_end_to_end_lifecycle_pipeline PASSED [100%]

============================== 36 passed in 0.32s ==============================
```

### 2.2 Suíte Completa de Regressão

Execução no ambiente `.venv` (`.venv/bin/pytest tests/ -q`):

```text
272 passed in 4.92s
```

---

## 3. Julgamento do Verificador Independente (`verification.md`)

- **Veredito:** `PASS`
- **Compromisso Avaliado:** `proofs.md` at `6d0aa19`
- **Validação de Checks:** Todos os 35 checks (`C1` a `C35`) foram inspecionados frente aos testes associados e sustentam o valor estrito dos critérios de aceitação.
- **Sondagens com Exemplos Próprios:**
  - *Sondagem 1 (Regressão baseline com N=1):* Verificado cálculo de incerteza padrão com fallback determinístico (`ddof=0` para $N=1$, gerando `std=0.0`).
  - *Sondagem 2 (Catálogo vazio):* Verificado comportamento de sequência vazia `validate_models_catalog([])`, retornando `MappingProxyType({})` imutável.
  - *Sondagem 3 (Modelo analítico unário):* Avaliação direta com único índice de feature `required_features=(0,)`.
  - *Sondagem 4 (Simplex probabilístico nos limites):* Verificação de probabilidades estritamente em $\{0.0, 1.0\}$ com soma unitária.
- **Apontamentos:** Nenhum achado impeditivo (`None`).

---

## 4. Conformidade Arquitetural e Metodológica

1. **Pureza de Runtime (`XCUT-02`):**
   - Módulo `src/experimental_ml/models` opera estritamente sob `numpy>=1.24.0` e biblioteca padrão, sem importação mandatória de frameworks terceiros (`sklearn`, `scipy`, `torch`).
2. **Isolamento de Memória (`CA-E3-01`):**
   - Instanciações frescas protegidas contra vazamento de referências e compartilhamento acidental de instâncias singleton via registro `WeakSet` em `instantiate_fresh_model`.
3. **Bypass Analítico Transparente (`RF3.2`):**
   - Modelos analíticos/biométricos (`requires_fit=False`) eliminam execuções falsas de treinamento em `fit_model`.
4. **Contrato Tripartite de Inferência (`MOD-05`):**
   - Saídas padronizadas com chaves `y_pred`, `y_std` e `y_proba`, prevenindo calibrações heurísticas arbitrárias.
5. **Snapshot Imutável de Diagnósticos (`RF3.6`):**
   - Conversão defensiva recursiva para tuplas, escalares nativos e `MappingProxyType`, blindando registros históricos contra mutações pós-ajuste.

---

## 5. Decisão Formal de Aceite

- **Decisão:** `APROVADO`
- **Justificativa:** Todos os 9 requisitos (`MOD-01` a `MOD-09`) foram implementados com 100% de aprovação na suíte de testes (36 testes específicos de modelos e 272 testes de regressão global), verificação independente TLC com veredito `PASS` e conformidade comprovada no roteiro de aceitação.
