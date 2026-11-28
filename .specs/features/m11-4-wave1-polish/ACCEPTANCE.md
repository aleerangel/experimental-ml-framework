# Roteiro de Aceite do Consumidor — Submarco M11.4 (`VAL-ENH-004`, `VAL-QUAL-004`, Desempenho)

- **Submarco:** `M11.4` (`m11-4-wave1-polish`)
- **Branch:** `feat/m11-4-wave1-polish`
- **Critério:** Validação pelo pesquisador usando exclusivamente interfaces públicas (`run_experiment`, `run_experiment_matrix`, `run_nested_tuning` e documentação).

---

## 1. Pré-requisitos
- Ambiente virtual `.venv` com dependências instaladas (`pip install -e ".[dev]"`).

## 2. Passos de Validação
1. **Pareto e Pares Planejados via `run_experiment` (`VAL-ENH-004`):**
   - Executar `run_experiment(..., comparison_scope=ComparisonScope.PLANNED_HYPOTHESES, planned_pairs=(...), pareto_objectives=(...))`.
   - Confirmar em `statistics/statistical_comparisons.json` que apenas os pares planejados foram avaliados e em `statistics/pareto_summary.json` que os objetivos configurados foram usados.
2. **Desempenho (`Nested CV` e `ProcessPoolExecutor`):**
   - Confirmar que `run_nested_tuning` com múltiplos candidatos não altera resultados numéricos e que `run_experiment_matrix(..., outer_n_jobs=2, execution_backend="process")` executa e persiste células normalmente com estimadores serializáveis.
3. **Documentação (`VAL-QUAL-004`):**
   - Conferir `docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md` (`EvaluationRegime` / `PartitionStrategy`) e `docs/referencia/api_python.md` (símbolos `M8`–`M11.4`).

## 3. Critério de Aprovação
- [ ] Passos 1, 2 e 3 validados sem regressão nos padrões existentes.
