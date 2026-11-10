# m3-3-intra-fold-selection verification

**Verdict**: PASS
**Proofs**: `proofs.md` at 044bc2c
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/features/test_selection.py` `test_sel_01_selection_result_immutability` | yes |
| C2 | `tests/unit/features/test_selection.py` `test_sel_02_fixed_scenario_bypass` | yes |
| C3 | `tests/unit/features/test_selection.py` `test_sel_03_variance_threshold_selection` | yes |
| C4 | `tests/unit/features/test_selection.py` `test_sel_04_top_k_relevance_selection` | yes |
| C5 | `tests/unit/features/test_selection.py` `test_sel_05_apply_feature_selection` | yes |
| C6 | `tests/unit/features/test_stability.py` `test_sel_06_selection_stability_metrics` | yes |
| C7 | `tests/unit/features/test_selection.py` `test_sel_07_empty_selection_rejection` | yes |
| C8 | `tests/integration/features/test_selection_integration.py` `test_sel_08_multi_fold_selection_pipeline` | yes |

## Own examples

Five boundary, degenerated, out-of-order, and chance-correction edge cases were independently probed at `HEAD`:

1. **`VARIANCE_THRESHOLD` com valores `NaN` e colunas singulares**:
   - Avaliado array contendo apenas `NaN`, array com elemento único válido e array constante com `NaN`.
   - Constatado que o motor filtra valores ausentes com `~np.isnan(arr)`, computa a variância amostral com `ddof=1` quando `len(valid) > 1` e atribui pontuação `0.0` para colunas com 0 ou 1 valor válido, evitando exceções não tratadas e selecionando estritamente preditores com variância legítima superior ao limiar.

2. **Desempate determinístico em escores idênticos**:
   - Avaliado cenário com múltiplos preditores apresentando variância ou relevância idêntica.
   - Constatado que o algoritmo desempata ordenando canonicamente pelo nome do atributo (`key=lambda f: (-scores[f], f)`), assegurando reprodutibilidade matemática estrita sem dependência da ordem aleatória do dicionário de entrada.

3. **`TOP_K_RELEVANCE` com alvo categórico e preditores mistos**:
   - Avaliado alvo de classificação categórica (`class_a`, `class_b`) contra preditores contínuos e categóricos.
   - Constatado que o despachante calcula `compute_correlation_ratio` para pares contínuo/categórico e `compute_cramers_v` para pares categórico/categórico, ranqueando corretamente os atributos mais associados e descartando ruído.

4. **Casos de fronteira do índice de Kuncheva corrigido**:
   - Avaliado caso de seleção exaustiva ($k_1 = k_2 = N$), resultando em $K = 1.0$ e $J = 1.0$.
   - Avaliado caso assimétrico ($k_1 = 1$, $k_2 = 9$ para $N = 10$, com interseção $r = 1$), resultando analiticamente em $K = \frac{1 \cdot 10 - 1 \cdot 9}{\sqrt{1 \cdot 9 \cdot 9 \cdot 1}} = \frac{1}{9} \approx 0.111111$, exatamente concordante com a formulação canônica de Kuncheva (2007) e Lustgarten et al. (2009).

5. **Projeção de avaliação (`apply_feature_selection`) com colunas desordenadas e atributos excedentes**:
   - Avaliado mapeamento de validação contendo atributos extras e ordem invertida em relação a `selected_features`.
   - Constatado que a projeção isola estritamente os preditores selecionados, preserva a ordem canônica especificada no treino e rejeita ausências parciais com `ContractViolationError`.

## Findings

None - all 8 checks formally prove their acceptance criteria, anti-leakage invariants are strictly guarded across cross-validation splits, and stability metrics handle edge cases rigorously.
