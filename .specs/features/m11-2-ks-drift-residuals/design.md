# Design — M11.2: Teste Kolmogorov-Smirnov, Detecção de *Dataset Shift* e Diagnóstico de Resíduos OOF

- **Feature**: `m11-2-ks-drift-residuals`
- **Spec**: [`spec.md`](./spec.md)
- **Decisions**: `AD-039`, `XCUT-02`

---

## 1. Matemática em NumPy Puro (`XCUT-02`)

1. **`ks_2samp(a, b)` (Kolmogorov 1933; Smirnov 1948):**
   - Filtra não-finitos; ordena `a` ($n_1$) e `b` ($n_2$); computa as ECDFs sobre os valores combinados ordenados e $D = \max |F_1(x) - F_2(x)|$.
   - $n_{\text{eff}} = \frac{n_1 n_2}{n_1 + n_2}$, $\lambda = (\sqrt{n_{\text{eff}}} + 0{,}12 + 0{,}11 / \sqrt{n_{\text{eff}}}) D$, e série assintótica $p = 2 \sum_{k=1}^{100} (-1)^{k-1} \exp(-2 k^2 \lambda^2)$ limitada a $[0, 1]$.
2. **`ks_normal_lilliefors(x)` (Lilliefors 1967; Stephens 1974):**
   - Padroniza $z = (x - \bar{x}) / s$ (com $s$ amostral `ddof=1`).
   - Calcula $\Phi(z)$ via `math.erf` vetorizado (`np.vectorize(math.erf)` ou aproximação de alta precisão) e $D = \max(\max_i (\frac{i}{n} - \Phi(z_{(i)})), \max_i (\Phi(z_{(i)}) - \frac{i-1}{n}))$.
   - Aplica correção de Stephens (1974) para parâmetros estimados: $D^* = D (\sqrt{n} - 0{,}01 + 0{,}85 / \sqrt{n})$ para aproximação do $p$-valor de Lilliefors (Massey/Stephens).
3. **Comparação AIC Normal vs. Student-$t$ sobre resíduos OOF:**
   - Normal ($k=2$: $\mu, \sigma$): MLE em forma fechada.
   - Student-$t$ ($k=3$: $\mu, \sigma, \nu$): grade determinística em $\nu \in \{2, 3, 4, 5, 7, 10, 15, 30, 100\}$ com atualização EM simples (ou log-verossimilhança exata com `math.lgamma`) escolhendo $(\hat{\mu}, \hat{\sigma}, \hat{\nu})$ de maior log-verossimilhança, comparando $\text{AIC} = 2k - 2\ell$.

---

## 2. Fluxo Opt-In e Isolamento

- `check_ks_drift: bool = False` e `analyze_oof_residuals: bool = False` em `run_experiment` e CLI (`--check-ks-drift`, `--analyze-oof-residuals`).
- Quando ativos, gravam artefatos opcionais em `statistics/` (`ks_drift_report.json` e `oof_residuals_diagnostics.json`), carregados por `reporting/loader.py` apenas se existirem.
- `reporting/figures.py`: função dedicada `build_residuals_diagnostic_figure_spec(...)` + renderização Matplotlib de painel duplo (`Resíduos vs. Predito` + `Q-Q Plot` Normal) em `PNG`, `SVG` e `PDF`.
- `reporting/report.py`: exibe subseção diagnóstica em `pt-BR` quando esses artefatos estiverem presentes em `LoadedExperimentData`.
