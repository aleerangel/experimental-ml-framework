# Interpretando Resultados Científicos (Jornada 3)

Após executar um experimento, o `experimental-ml` gera relatórios em `reports/report.md` e `reports/report.html`, além de tabelas `CSV`/`LaTeX` e figuras `SVG`. Este guia explica como ler cada número com rigor científico.

---

## 1. Desempenho Preditivo e Cobertura

Na tabela de **Desempenho Preditivo**:
- **`Mean` e `SD`:** Média e desvio-padrão da métrica calculados **apenas sobre as dobras concluídas com sucesso**.
- **`Median` e `IQR`:** Mediana e intervalo interquartil (úteis quando há *outliers* entre dobras).
- **`Coverage` (`VALID`, `PARTIAL_COVERAGE`, `NO_COVERAGE`):** Indica se todas as dobras rodaram sem falha. Configurações `VALID` têm sempre precedência sobre configurações com cobertura parcial (`ADR-005`).
- **`UNDEFINED_NAN`:** Indica que a métrica é matematicamente indefinida naquele conjunto (ex.: $R^2$ quando a variância do alvo é zero). O framework **nunca** converte falhas em `0.0`.

### Métricas Mais Comuns
- **Regressão:** `rmse` e `mae` (quanto **menor**, melhor); `rmse_rel_pct` (erro percentual relativo à média); `mbe` (*Mean Bias Error* — avaliado em módulo pelo framework: quanto mais próximo de `0`, menor o viés sistemático); `r2` (quanto mais próximo de `1.0`, melhor).
- **Classificação:** `accuracy`, `balanced_accuracy`, `f1` e `roc_auc` (quanto **maior**, melhor); `log_loss` (quanto **menor**, melhor).

---

## 2. Comparações Estatísticas Pareadas

- **Por que não olhar só a média?** Em validação cruzada $K$-fold, os conjuntos de treino se sobrepõem. O framework usa o **teste *t* corrigido de Nadeau-Bengio** (paramétrico) e o **teste de Wilcoxon pareado** (não-paramétrico) sobre exatamente as mesmas dobras.
- **Multiplicidade (`Holm-Bonferroni` / `Benjamini-Hochberg`):** Ao comparar vários pares de modelos, use sempre o **valor-$p$ ajustado** (`adjusted_p_value`), nunca o valor-$p$ bruto isolado.
- **Tamanho de Efeito ($d$ de Cohen):** Mede se a diferença tem magnitude prática relevante, além da significância estatística.

> [!IMPORTANT]
> **Armadilha clássica ($p \ge \alpha$):** Se o valor-$p$ ajustado for maior ou igual a `0.05`, isso significa **ausência de evidência estatística para afirmar diferença**, e **nunca** prova que dois modelos são equivalentes.

---

## 3. Fronteira de Pareto (Multiobjetivo)

Na tabela **Fronteira de Pareto**, uma configuração é marcada como **ótima (não dominada)** quando nenhum outro modelo é simultaneamente melhor ou igual em todos os objetivos escolhidos (ex.: menor `rmse` **e** menor latência de inferência `predict_mean_s`).
