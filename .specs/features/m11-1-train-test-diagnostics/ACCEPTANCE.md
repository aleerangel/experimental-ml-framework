# Roteiro de Aceite do Consumidor — Submarco M11.1 (`VAL-ENH-005`)

- **Submarco:** `M11.1` (`m11-1-train-test-diagnostics`)
- **Branch:** `feat/m11-1-train-test-diagnostics`
- **Critério:** Validação pelo pesquisador usando exclusivamente interfaces públicas (`run_experiment` / CLI `expml`).

---

## 1. Pré-requisitos
- Ambiente virtual `.venv` com dependências instaladas (`pip install -e ".[dev]"`).

## 2. Passos de Validação
1. **Comportamento padrão (opt-in desativado):**
   - Executar `run_experiment(..., output_dir=...)` sem `collect_train_metrics=True` (ou `expml quickrun` sem `--collect-train-metrics`).
   - Confirmar que nenhuma avaliação de treino foi executada e que a Tabela D não exibe `Train Mean`.
2. **Ativação explícita (`collect_train_metrics=True` / `--collect-train-metrics`):**
   - Executar `run_experiment(..., collect_train_metrics=True)` (ou `expml quickrun --collect-train-metrics`).
   - Confirmar que `Train Mean` aparece na Tabela D ao lado de `Mean` (`DEV_CV`), que a Figura D (`reports/figures/fig_family_d.png`) exibe as barras `Treino` vs. `DEV_CV`, e que os valores de `DEV_CV` e testes estatísticos pareados permanecem idênticos ao passo 1.

## 3. Critério de Aprovação
- [ ] Passos 1 e 2 validados sem divergência numérica ou vazamento.
