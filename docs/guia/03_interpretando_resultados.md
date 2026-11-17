# Interpretando Resultados Científicos *(Jornada 3)*

Este guia ajuda você a ler o resumo (`resultado.summary()`) e os relatórios (`reports/report.md`, `report.html`) — começando pela leitura básica de métricas até a fundamentação estatística e citações para artigos e TCCs.

---

## Parte 1 — Nível Básico *(Entendendo Seu Primeiro Resultado)*

### 1. Direção das Métricas (O que é "Melhor"?)

| Tarefa | Métrica | Direção Melhor | Observação Prática |
| :--- | :--- | :---: | :--- |
| **Regressão** | `rmse`, `mae`, `rmse_rel_pct` | **Menor** | Quanto mais próximo de `0`, menor o erro de predição. |
| **Regressão** | `mbe` *(Mean Bias Error)* | **Mais próximo de `0` (em módulo)** | Mede viés sistemático (superestimação ou subestimação); o framework compara `|mbe|`. |
| **Regressão** | `r2` | **Maior** (até `1.0`) | Proporção da variância explicada; valores negativos indicam desempenho pior que prever a média. |
| **Classificação** | `accuracy`, `balanced_accuracy`, `f1`, `roc_auc` | **Maior** (até `1.0`) | Em classes desbalanceadas, prefira `balanced_accuracy` ou `f1` em vez de `accuracy` isolada. |
| **Classificação** | `log_loss` | **Menor** | Penaliza previsões probabilísticas erradas com alta confiança. |

### 2. Como Ler Média, Desvio-Padrão e Cobertura (Exemplo Prático)

Suponha a saída abaixo em validação cruzada de 5 dobras (`CV_ONLY`):
- **Modelo A:** `rmse = 0.39 ± 0.15`, `Coverage = 100% (VALID)`
- **Modelo B:** `rmse = 0.42 ± 0.03`, `Coverage = 100% (VALID)`

Embora o **Modelo A** tenha média menor (`0.39`), seu desvio-padrão (`0.15`) é cinco vezes maior que o do **Modelo B** (`0.03`), indicando instabilidade entre dobras. Já o status **`VALID`** confirma que todas as 5 dobras rodaram sem falha (`PARTIAL_COVERAGE` indica que alguma dobra falhou; `UNDEFINED_NAN` indica métrica matematicamente indefinida, nunca convertida para `0.0`).

---

## Parte 2 — Nível Avançado *(Rigor Estatístico por Pergunta Científica)*

### 1. "Estou comparando 2 modelos na mesma validação cruzada. Posso usar o teste *t* comum?"
**Não.** Em validação cruzada $K$-fold, os conjuntos de treino se sobrepõem em $(K-2)/(K-1)$ dos dados, violando a independência do teste *t* clássico e inflando falsos positivos (**Dietterich, 1998**).
- **O que o framework faz:** Aplica o **teste *t* corrigido de Nadeau-Bengio** (**Nadeau & Bengio, 2003**), que ajusta a variância pela razão de sobreposição $1/K + n_{\text{test}}/n_{\text{train}}$.
- **Alternativa não-paramétrica:** Quando as diferenças entre dobras forem assimétricas ou tiverem *outliers*, o framework disponibiliza o **teste pareado de Wilcoxon** (**Demšar, 2006**), com a ressalva documentada de que a não-parametricidade não elimina a dependência entre dobras de um único *dataset*.
- **Por que aparece o alerta de $J < 6$?** Aqui $J$ é o número de dobras (unidades pareadas) com diferença não nula. Para $J = 5$, a menor probabilidade bicaudal combinatória possível no Wilcoxon é $2 \times (1/2)^5 = 0{,}0625 > 0{,}05$, tornando impossível atingir significância estatística a $\alpha = 0{,}05$ (**Demšar, 2006**; seção 6.2 de [REFERENCIAS_E_FUNDAMENTACAO.md](../REFERENCIAS_E_FUNDAMENTACAO.md)). Se precisar de inferência com Wilcoxon, utilize $K \ge 6$ dobras (ex.: 10-fold CV).

### 2. "Estou comparando 3 ou mais modelos ao mesmo tempo. Qual $p$-valor devo usar?"
Sempre utilize o **$p$-valor ajustado** (`adjusted_p_value`), nunca o $p$-valor bruto isolado:
- **`Holm-Bonferroni` (`adjust_pvalues_holm`):** Controla a taxa de erro familiar (*FWER* — probabilidade de cometer ao menos um falso positivo), dominando a correção simples de Bonferroni (**Holm, 1979**). Recomendado para poucas comparações planejadas.
- **`Benjamini-Hochberg` (`adjust_pvalues_bh`):** Controla a proporção esperada de falsas descobertas (*FDR*), evitando conservadorismo excessivo em matrizes grandes com muitos pares (**Benjamini & Hochberg, 1995**).

### 3. "O $p$-valor deu maior que 0,05 ($p \ge \alpha$). Os modelos são equivalentes?"
**Não.** Um $p \ge \alpha$ indica apenas **ausência de evidência estatística para rejeitar a hipótese nula** (muitas vezes por baixo número de dobras $J$), e **nunca** prova equivalência prática entre os modelos. Reporte sempre o **tamanho de efeito** ($d$ de Cohen pareado, $d_z = \bar{d}/s_d$) junto ao $p$-valor.

### 4. "Como avaliar kernels pré-computados, estabilidade de atributos e múltiplos objetivos?"
- **Alinhamento de Kernel (`kta`):** Mede a similaridade entre a matriz de Gram do kernel e a matriz alvo ideal (**Cristianini et al., 2001**).
- **Estabilidade de Seleção (`mean_kuncheva`):** Mede a consistência dos atributos escolhidos entre dobras corrigindo a sobreposição esperada por acaso (**Kuncheva, 2007**).
- **Fronteira de Pareto:** Identifica configurações **não dominadas** onde nenhum outro modelo é simultaneamente melhor ou igual em todos os objetivos (ex.: menor `rmse` e menor latência `predict_mean_s`).

---

## Parte 3 — Referências Científicas para Citação em Artigos e TCCs

Todas as deduções, premissas e limitações estão documentadas em [REFERENCIAS_E_FUNDAMENTACAO.md](../REFERENCIAS_E_FUNDAMENTACAO.md):

| Recurso / Métrica no Framework | Referência Científica Principal | Aplicação Metodológica |
| :--- | :--- | :--- |
| Teste *t* pareado corrigido em CV | **Nadeau & Bengio (2003)** — *Inference for the Generalization Error* (Machine Learning, 52(3), DOI: `10.1023/A:1024068626366`); **Dietterich (1998)** | Correção de variância devido à sobreposição das partições de treino na validação cruzada. |
| Teste não-paramétrico de Wilcoxon e limite $J < 6$ | **Demšar (2006)** — *Statistical Comparisons of Classifiers over Multiple Data Sets* (JMLR, 7) | Comparação robusta a assimetrias e fundamentação do poder amostral mínimo. |
| Controle de erro familiar (FWER) | **Holm (1979)** — *A Simple Sequentially Rejective Multiple Test Procedure* (Scand. J. Stat., 6(2)) | Ajuste sequencial de $p$-valores em múltiplas comparações mantendo FWER $\le \alpha$. |
| Controle de falsas descobertas (FDR) | **Benjamini & Hochberg (1995)** — *Controlling the False Discovery Rate* (JRSS-B, 57(1)) | Equilíbrio entre poder estatístico e controle de FDR em matrizes grandes de modelos/cenários. |
| Alinhamento de Kernel (`kta`) | **Cristianini et al. (2001)** — *On Kernel-Target Alignment* (NeurIPS) | Avaliação de qualidade de matrizes de Gram e kernels quânticos/pré-computados. |
| Estabilidade de seleção de features | **Kuncheva (2007)** — *A Stability Index for Feature Selection* (AIA) | Medição de consistência inter-dobras descontando sobreposição aleatória. |
