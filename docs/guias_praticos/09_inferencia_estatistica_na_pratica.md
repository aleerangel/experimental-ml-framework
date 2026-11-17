# Guia Prático 9: Inferência Estatística na Prática (Nadeau-Bengio, Wilcoxon e Multiplicidade)

## Contexto Científico

Comparar modelos apenas pela média das métricas em validação cruzada $K$-fold leva a conclusões enganosas:
1. As dobras de treino se sobrepõem, violando a independência do teste *t* pareado clássico e subestimando a variância real;
2. Comparar múltiplos pares de modelos sem correção de multiplicidade infla drasticamente a taxa de falsos positivos;
3. Um valor-$p \ge \alpha$ indica **ausência de evidência para rejeitar $H_0$**, e **nunca** comprova que dois modelos são equivalentes.

O módulo `experimental_ml.statistics` oferece testes pareados corrigidos, tamanho de efeito e controle de erro familiar/descoberta falsa em Python e NumPy puro.

---

## Aplicação Executável em Python

```python
from experimental_ml.statistics import (
    adjust_pvalues_bh,
    adjust_pvalues_holm,
    compute_paired_cohens_d,
    paired_nadeau_bengio_test,
    paired_wilcoxon_test,
)

# Desempenho pareado por dobra (ex.: 10-fold CV com 90% treino e 10% validação)
scores_modelo_a = [0.84, 0.86, 0.83, 0.85, 0.87, 0.82, 0.85, 0.86, 0.84, 0.85]
scores_modelo_b = [0.80, 0.82, 0.79, 0.81, 0.83, 0.79, 0.81, 0.82, 0.80, 0.81]
scores_modelo_c = [0.83, 0.85, 0.84, 0.84, 0.86, 0.83, 0.85, 0.85, 0.84, 0.84]

# 1. Teste t corrigido de Nadeau-Bengio (razão n_val / n_train = 1/9)
nb_ab = paired_nadeau_bengio_test(
    scores_modelo_a,
    scores_modelo_b,
    train_val_ratios=1.0 / 9.0,
    alpha=0.05,
)
nb_ac = paired_nadeau_bengio_test(
    scores_modelo_a,
    scores_modelo_c,
    train_val_ratios=1.0 / 9.0,
    alpha=0.05,
)

# 2. Alternativa não-paramétrica pareada (Wilcoxon signed-rank) e tamanho de efeito
wilcox_ab = paired_wilcoxon_test(scores_modelo_a, scores_modelo_b, alpha=0.05)
efeito_ab = compute_paired_cohens_d(scores_modelo_a, scores_modelo_b, alpha=0.05)

# 3. Controle de multiplicidade (FWER via Holm-Bonferroni e FDR via Benjamini-Hochberg)
p_brutos = [nb_ab.p_value, nb_ac.p_value]
p_holm = adjust_pvalues_holm(p_brutos)
p_bh = adjust_pvalues_bh(p_brutos)

assert len(p_holm) == 2 and len(p_bh) == 2
assert efeito_ab.cohens_d > 0.0
assert wilcox_ab.p_value >= 0.0
```

---

## Guia Rápido de Interpretação

- **Nadeau-Bengio vs. Wilcoxon:** Utilize Nadeau-Bengio quando a distribuição das diferenças entre dobras for aproximadamente simétrica/normal; utilize Wilcoxon como alternativa não-paramétrica robusta a assimetrias ou *outliers*.
- **Holm-Bonferroni (`adjust_pvalues_holm`):** Controla a probabilidade de pelo menos um falso positivo (*FWER*), sendo recomendado quando poucas comparações críticas são planejadas.
- **Benjamini-Hochberg (`adjust_pvalues_bh`):** Controla a proporção esperada de falsas descobertas (*FDR*), indicado para estudos exploratórios com dezenas de pares comparados.
- **Tamanho de Efeito ($d$ de Cohen):** Sempre reporte a magnitude da diferença (`cohens_d` e intervalo de confiança) junto ao valor-$p$ para distinguir significância estatística de relevância prática.
