# Registro de Validação e Aceite — Marco M3.3 (Seleção Dinâmica Intra-Fold de Features e Estabilidade)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M3.3 (`m3-3-intra-fold-selection`)  
> **Data de Validação:** 10 de Novembro de 2026  
> **Commit de Implementação:** [`044bc2c`](https://github.com/alexandrerangel/experimental-ml-framework/commit/044bc2cb321b212ae5da5295c01798e39f502ca7)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.2.6, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de execução (`numpy>=1.24.0`) | Validado via subprocess e ambiente `.venv` (XCUT-02) | **APROVADO** |
| **Testes Unitários Automatizados** | 8 testes em `tests/unit/features/test_selection.py` e `test_stability.py` | 8 testes aprovados (100%) | **APROVADO** |
| **Testes de Integração e Invariantes** | 2 testes em `tests/integration/features/test_selection_integration.py` | 2 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 228 testes em `pytest tests/` | 228 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e julgamento independente (`author != verifier`) | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Roteiro de Aceite** | Roteiro `ACCEPTANCE.md` (7 capacidades + cenário integrado) | Executado com sucesso via interfaces públicas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte de Seleção e Estabilidade (Unidade e Integração)

Execução no ambiente `.venv` (`.venv/bin/pytest tests/unit/features/test_selection.py tests/unit/features/test_stability.py tests/integration/features/test_selection_integration.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 10 items

tests/unit/features/test_selection.py::test_sel_01_selection_result_immutability PASSED [ 10%]
tests/unit/features/test_selection.py::test_sel_02_fixed_scenario_bypass PASSED [ 20%]
tests/unit/features/test_selection.py::test_sel_03_variance_threshold_selection PASSED [ 30%]
tests/unit/features/test_selection.py::test_sel_04_top_k_relevance_selection PASSED [ 40%]
tests/unit/features/test_selection.py::test_sel_07_empty_selection_rejection PASSED [ 50%]
tests/unit/features/test_selection.py::test_sel_05_apply_feature_selection PASSED [ 60%]
tests/unit/features/test_stability.py::test_sel_06_selection_stability_metrics PASSED [ 70%]
tests/unit/features/test_stability.py::test_stability_input_validations PASSED [ 80%]
tests/integration/features/test_selection_integration.py::test_sel_08_multi_fold_selection_pipeline PASSED [ 90%]
tests/integration/features/test_selection_integration.py::test_xcut_02_runtime_purity_selection PASSED [100%]

============================== 10 passed in 0.28s ==============================
```

### 2.2 Suíte Completa de Regressão

Execução no ambiente `.venv` (`.venv/bin/pytest tests/ -q`):

```text
228 passed in 2.71s
```

---

## 3. Conformidade com Decisões Arquiteturais e Invariantes

1. **RF2.4 / ADR-002 (Prevenção Rigorosa de Data Leakage na Seleção de Features):**
   - O despachante funcional puro `select_features_in_fold` opera exclusivamente sobre os dados de treino de cada fold de validação cruzada. Nenhuma informação ou linha da partição de validação/teste é consultada ou utilizada no ajuste de variâncias ou relevâncias.
2. **ADR-008 / RNF02 (Modelagem Funcional e Imutável sem Efeitos Colaterais):**
   - Os resultados `SelectionResult` e `SelectionStabilityReport` são imutáveis (`frozen=True, slots=True`), com coleções e dicionários protegidos via `MappingProxyType` e tuplas imutáveis, garantindo isolamento total entre folds paralelos.
3. **RF2.1 / CA-E2-01 (Estabilidade de Seleção Corrigida para o Acaso):**
   - Implementação canônica da similaridade de Jaccard e do Índice de Kuncheva corrigido para o acaso, fornecendo métricas de estabilidade rigorosas com valor 1.0 para concordância perfeita e ~0.0 para seleção estocástica independente.
4. **RNF05 / ADR-005 (Tratamento de Degenerescência e Fail-Fast):**
   - Seleções dinâmicas que resultam em 0 atributos selecionados (por limiares excessivos ou dados degenerados) levantam imediatamente `DataIntegrityError`, impedindo a criação de matrizes sem preditores na Etapa 4B de modelagem.
5. **SEL-05 (Projeção Determinística de Avaliação):**
   - `apply_feature_selection` aplica a máscara de treino na partição de validação com garantia de ordenação idêntica e verificação estrita de completude com `ContractViolationError`.
6. **XCUT-02 (Pureza de Runtime sem Dependências Externas):**
   - Todos os cálculos de variância amostral com `ddof=1`, correlações, Jaccard e Kuncheva foram implementados em `numpy` puro, sem importar `scipy`, `sklearn` ou `pandas`, comprovado via teste de isolamento em subprocesso.

---

## 4. Julgamento da Verificação Independente (`verification.md`)

- **Veredito:** `PASS`
- **Auditado por:** Sub-agente verificador independente (`author != verifier`).
- **Achados impeditivos:** Nenhum (`None`).
- **Avaliação de Checks C1..C8:** Todos os 8 testes selecionados comprovam formalmente seus critérios de aceitação sem asserções frouxas.
- **Provas com dados inéditos:** 5 baterias de testes independentes executadas com sucesso cobrindo `NaN` na variância amostral, desempate determinístico por nome, alvos categóricos mistos, casos de fronteira de Kuncheva ($k_i=N$ e $k_i \ne k_j$) e projeção com desordenação de colunas.

---

## 5. Validação Prática de Aceite pelo Consumidor (`ACCEPTANCE.md`)

Todos os exemplos executáveis do roteiro `ACCEPTANCE.md` foram testados através das interfaces públicas exportadas em `experimental_ml.features`:
- Criação e serialização JSON de `SelectionResult`.
- Bypass imediato de cálculo para cenários `FIXED`.
- Seleção não-supervisionada `VARIANCE_THRESHOLD` com ordenação por variância decrescente.
- Seleção supervisionada `TOP_K_RELEVANCE` exigindo `y_train` e ranqueando atributos.
- Projeção determinística de avaliação com `apply_feature_selection`.
- Medição de estabilidade com `compute_selection_stability` e validações de integridade.
- Rejeição de seleções vazias via `DataIntegrityError`.
- Simulação de validação cruzada 5-fold de ponta a ponta sem vazamento de dados.

---

## 6. Decisão Formal de Aceite

> **Decisão:** **`APROVADO`**  
>
> **Justificativa:** Todos os critérios de aceitação funcionais (SEL-01 a SEL-07), transversais (SEL-08, XCUT-02) e diretrizes arquiteturais (RF2.1, RF2.4, ADR-002, ADR-008) foram formalmente comprovados por testes automatizados, verificação independente e validação via interfaces públicas, sem pendências impeditivas.
