# Registro de Validação e Aceite — Marco M7.2 (Figuras Determinísticas e Relatório Completo)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M7.2 (`m7-2-figures-full-report`)  
> **Data de Validação:** 16 de Novembro de 2026  
> **Commit de Implementação / Prova:** [`08ba64e`](https://github.com/aleerangel/experimental-ml-framework/commit/08ba64e)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.5.4, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única (`numpy>=1.24.0`, zero `matplotlib`/`pillow`) | Validado via subprocesso isolado (`XCUT-02`) | **APROVADO** |
| **Testes Unitários de Figuras e Relatório** | 6 testes cobrindo C1 a C6 | 6 testes específicos aprovados | **APROVADO** |
| **Testes de Integração e Pureza** | 2 testes em `tests/integration/reporting/test_m72_integration.py` (C7, C8) | 2 testes aprovados | **APROVADO** |
| **Testes de Regressão Global** | Suíte completa em `pytest tests/` | **567 testes aprovados** (100% de sucesso) | **APROVADO** |
| **Verificação Independente TLC** | Auditoria por subagente independente (`author != verifier`) | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Sondagem Adversarial Independente** | 3 sondagens (Famílias D/E/F com `NaN`/`Inf`, PNG CRC32/zlib + PDF `xref`, XSS/escape HTML) | Todas as 3 sondagens adversariais aprovadas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte do Marco M7.2 (`reporting/`)

```text
.venv/bin/pytest tests/unit/reporting/ tests/integration/reporting/ -v
19 passed in 0.70s
```

### 2.2 Provas TLC (`check_proofs.py`)

```text
**HEAD**: 08ba64e
**Tree**: clean
**Shell**: /bin/sh
**Result**: 8 pass, 0 fail
```

### 2.3 Suíte de Regressão Global

```text
.venv/bin/pytest tests/ -q
567 passed in 12.93s
```

---

## 3. Registro do Verificador Independente

- **Veredito:** `PASS`
- **Sondagens Realizadas:**
  1. `build_figure_spec` para Famílias D, E (`PAIRED_DIFF_CI`) e F (`PARETO_TRADEOFF`) excluindo `Inf`/`NaN` com notas explícitas.
  2. Determinismo bit a bit de `render_figure` em SVG, PNG (CRC32 válidos, `pHYs` = 11811 px/m, `zlib.decompress` = 1.200.500 bytes) e PDF 1.4 (`startxref` e offsets exatos).
  3. Escape HTML seguro contra `<script>`/`<img>`/`&` em `ResearcherDeclarations` e `figure_paths`, com zero URLs externas.
- **Apontamentos:** Nenhum (`None`). Todos os 8 critérios C1 a C8 sustentam suas garantias formais.

---

## 4. Decisão Formal de Aceite

O Marco M7.2 cumpre integralmente `RF6.1`, `RF6.2`, `RNF03`, `CA-E6-01`, `CA-E6-02` e `XCUT-02`.

**Decisão:** `APROVADO`
