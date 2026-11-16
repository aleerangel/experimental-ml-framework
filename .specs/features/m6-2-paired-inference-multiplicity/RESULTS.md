# Registro de Validação e Aceite — Marco M6.2 (Inferência Estatística Pareada, Tamanho de Efeito e Multiplicidade)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M6.2 (`m6-2-paired-inference-multiplicity`)  
> **Data de Validação:** 16 de Novembro de 2026  
> **Commit de Implementação / Prova:** [`e07c5e2`](https://github.com/aleerangel/experimental-ml-framework/commit/e07c5e2)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.5.4, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de runtime (`numpy>=1.24.0`, zero `scipy`) | Validado via subprocesso isolado (`XCUT-02`) | **APROVADO** |
| **Testes Unitários de Inferência & Multiplicidade** | 17 testes cobrindo C1 a C16 | 17 testes específicos de M6.2 + 36 de M6.1 aprovados | **APROVADO** |
| **Testes de Integração e Pureza** | 2 testes em `tests/integration/statistics/test_m62_integration.py` (C17, C18) | 2 testes de integração e pureza aprovados | **APROVADO** |
| **Testes de Regressão Global** | Suíte completa em `pytest tests/` | **524 testes aprovados** (100% de sucesso) | **APROVADO** |
| **Verificação Independente TLC** | Auditoria por subagente independente (`author != verifier`) | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Sondagem Adversarial Independente** | 5 sondagens numéricas (Student-$t$ CDF/PPF, DP Wilcoxon/Pratt, $S^2_d=0$, multiplicidade com empates, `UNDEFINED_NAN` em `COMPLETED`) | Todas as 5 sondagens adversariais aprovadas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte do Pacote `statistics/` (M6.1 + M6.2)

```text
.venv/bin/pytest tests/unit/statistics/ tests/integration/statistics/ -v
53 passed in 0.56s
```

### 2.2 Provas TLC (`check_proofs.py`)

```text
**HEAD**: e07c5e2
**Tree**: clean
**Shell**: /bin/sh
**Result**: 18 pass, 0 fail
```

### 2.3 Suíte de Regressão Global

```text
.venv/bin/pytest tests/ -q
524 passed in 11.47s
```

---

## 3. Registro do Verificador Independente

- **Veredito:** `PASS`
- **Sondagens Realizadas:**
  1. Precisão de `student_t_cdf` / `student_t_ppf` contra Cauchy (`df=1`, erro $< 10^{-12}$), roundtrips `df in {1, 3, 5, 30, 100}` e convergência assintótica (`df=100000`).
  2. DP exata de Wilcoxon e fórmula de Pratt validadas contra enumeração exaustiva $2^n$ com empates e zeros (`< 1e-12`).
  3. Casos degenerados de variância nula no Nadeau-Bengio ($\bar{d}=0$ e $\bar{d}<0$) e alerta `fold_size_cv > 20%`.
  4. Ajustes de Holm-Bonferroni e Benjamini-Hochberg com empates e limites $[0.0, 1.0]$.
  5. Filtragem de `UNDEFINED_NAN` dentro de células `COMPLETED` em `CV_AND_HOLDOUT` sob ambas as políticas (`STRICT_COMPLETE_ONLY` vs `ALLOW_COMMON_SUBSET`).
- **Apontamentos:** Nenhum (`None`). Todos os 18 critérios C1 a C18 sustentam suas garantias formais.

---

## 4. Decisão Formal de Aceite

O Marco M6.2 cumpre integralmente os requisitos arquiteturais (`ARQUITETURA §3.5`, `ADR-004`, `ADR-005`), os critérios `RF5.1`–`RF5.4`, `CA-E5-01`, `CA-E5-02` e as restrições transversais (`XCUT-02`, `RNF02`).

**Decisão:** `APROVADO`
