# Roteiro de Aceite do Consumidor — Submarco M11.2 (`VAL-ENH-006`)

- **Submarco:** `M11.2` (`m11-2-ks-drift-residuals`)
- **Branch:** `feat/m11-2-ks-drift-residuals`
- **Critério:** Validação pelo pesquisador usando exclusivamente interfaces públicas (`run_experiment` e relatórios gerados).

---

## 1. Pré-requisitos
- Ambiente virtual `.venv` com dependências instaladas (`pip install -e ".[dev]"`).

## 2. Passos de Validação
1. **Comportamento padrão (opt-in desativado):**
   - Executar `run_experiment(..., output_dir=...)` sem `check_ks_drift=True` nem `analyze_oof_residuals=True`.
   - Confirmar que nenhum artefato `ks_drift_report.json`, `oof_residuals_diagnostics.json` ou `fig_oof_residuals_qq.*` é gerado e que as seções de *Dataset Shift* e *Resíduos OOF* não aparecem no relatório.
2. **Ativação explícita (`check_ks_drift=True`, `analyze_oof_residuals=True`):**
   - Executar `run_experiment(..., validation=..., check_ks_drift=True, analyze_oof_residuals=True)` em experimento com `CV_AND_HOLDOUT` ou `TEMPORAL` e tarefa de regressão.
   - Confirmar a criação de `ks_drift_report.json`, `oof_residuals_diagnostics.json` e `reports/figures/fig_oof_residuals_qq.png` (`SVG`/`PDF` quando habilitados).
   - Confirmar no relatório Markdown/HTML as tabelas `Diagnóstico de Dataset Shift` e `Diagnóstico de Resíduos OOF`, e que as estatísticas `DEV_CV` permanecem idênticas ao passo 1.

## 3. Critério de Aprovação
- [ ] Passos 1 e 2 validados sem execução oculta e sem alteração das estatísticas `DEV_CV`.
