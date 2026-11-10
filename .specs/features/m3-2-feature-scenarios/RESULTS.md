# Registro de Validação e Aceite — Marco M3.2 (Definição e Validação de Cenários de Features)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M3.2 (`m3-2-feature-scenarios`)  
> **Data de Validação:** 10 de Novembro de 2026  
> **Commit de Implementação:** [`f4b21f4`](https://github.com/alexandrerangel/experimental-ml-framework/commit/f4b21f411990edd7f480d5e08a6fe3c49f856970)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via subprocess e ambiente `.venv` (XCUT-02) | **APROVADO** |
| **Testes Unitários Automatizados** | 8 testes específicos em `tests/unit/features/` | 8 testes aprovados (100%) | **APROVADO** |
| **Testes de Integração e Invariantes** | 2 testes em `tests/integration/features/test_scenarios_integration.py` | 2 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 218 testes em `pytest tests/` | 218 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria independente | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (5 capacidades) | Executado com sucesso via interfaces públicas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Cenários Unitária e Integração

Execução no ambiente `.venv` (`.venv/bin/pytest tests/unit/features/test_feature_scenarios.py tests/unit/features/test_scenarios_storage.py tests/integration/features/test_scenarios_integration.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 10 items

tests/unit/features/test_feature_scenarios.py::test_scn_01_feature_scenario_immutability PASSED [ 10%]
tests/unit/features/test_feature_scenarios.py::test_scn_02_fixed_scenario_constraints PASSED [ 20%]
tests/unit/features/test_feature_scenarios.py::test_scn_03_dynamic_scenario_anti_leakage PASSED [ 30%]
tests/unit/features/test_feature_scenarios.py::test_scn_04_validate_scenarios_success PASSED [ 40%]
tests/unit/features/test_feature_scenarios.py::test_scn_05_validate_scenarios_rejections PASSED [ 50%]
tests/unit/features/test_feature_scenarios.py::test_scn_06_roundtrip_serialization PASSED [ 60%]
tests/unit/features/test_scenarios_storage.py::test_scn_07_save_and_load_scenarios PASSED [ 70%]
tests/unit/features/test_scenarios_storage.py::test_verify_scenarios_gate_valid_and_failures PASSED [ 80%]
tests/integration/features/test_scenarios_integration.py::test_scn_08_end_to_end_scenarios_gate PASSED [ 90%]
tests/integration/features/test_scenarios_integration.py::test_xcut_02_runtime_purity_scenarios PASSED [100%]

============================== 10 passed in 0.25s ==============================
```

### 2.2 Suíte Completa de Regressão

Execução no ambiente `.venv` (`.venv/bin/pytest tests/ -q`):

```text
218 passed in 2.57s
```

---

## 3. Conformidade com Decisões Arquiteturais e Invariantes

1. **RF2.4 / ADR-002 (Prevenção Rigorosa de Data Leakage em Cenários Dinâmicos):**
   - Instâncias `FeatureScenario` em modo `DYNAMIC` proíbem estritamente qualquer especificação pré-calculada de `selected_features` na Etapa 2, garantindo que algoritmos de seleção dependentes de dados só possam ser executados dentro de cada fold de validação cruzada.
2. **ADR-008 / RNF02 (Modelagem Declarativa Imutável sem Herança OOP):**
   - `FeatureScenario` e `ScenariosCatalog` são dataclasses imutáveis (`frozen=True, slots=True`), parametrizadas declarativamente por `mode`, com mapeamentos convertidos para cópias defensivas em `MappingProxyType`.
3. **CA-GER-01 / ADR-007 (Linhagem Criptográfica com a Visão Saneada):**
   - O catálogo gerado por `validate_scenarios` é vinculado de forma imutável a `view.dataset_hash`. O portão de etapa `verify_scenarios_gate` rejeita qualquer divergência de hash com `DataIntegrityError`.
4. **CA-E2-02 / SCN-05 (Disjunção Estrita de Papéis Protegidos):**
   - A validação assegura que nenhum cenário `FIXED` selecione a variável-alvo, colunas de agrupamento (`group_col`), identificadores de observação, carimbos temporais ou variáveis declaradas em `ignore_cols`.
5. **STORE-01 / STORE-07 (Persistência Atômica e Concorrência Segura):**
   - `save_scenarios` utiliza `write_json_atomic` com substituição via `os.replace`, garantindo que leituras concorrentes nunca encontrem arquivos corrompidos ou parciais.
6. **XCUT-02 (Pureza de Runtime sem Dependências Externas):**
   - O módulo de cenários e o portão de etapa não importam bibliotecas externas além do NumPy e módulos padrão da biblioteca Python, validado via teste de isolamento em subprocesso.
