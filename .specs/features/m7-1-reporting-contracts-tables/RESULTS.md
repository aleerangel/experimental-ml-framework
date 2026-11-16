# Registro de Validação e Aceite — Marco M7.1 (Contratos, Leitura e Tabelas das 7 Famílias)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M7.1 (`m7-1-reporting-contracts-tables`)  
> **Data de Validação:** 16 de Novembro de 2026  
> **Commit de Implementação / Prova:** [`55ae9ab`](https://github.com/aleerangel/experimental-ml-framework/commit/55ae9ab)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.5.4, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única (`numpy>=1.24.0`, sem `matplotlib`/`scipy`/`pandas`) | Validado via subprocesso isolado (`XCUT-02`) | **APROVADO** |
| **Testes Unitários de Contratos, Loader e Tabelas** | 9 testes cobrindo C1 a C9 | 9 testes específicos aprovados | **APROVADO** |
| **Testes de Integração e Pureza** | 2 testes em `tests/integration/reporting/test_m71_integration.py` (C10, C11) | 2 testes aprovados | **APROVADO** |
| **Testes de Regressão Global** | Suíte completa em `pytest tests/` | **559 testes aprovados** (100% de sucesso) | **APROVADO** |
| **Verificação Independente TLC** | Auditoria por subagente independente (`author != verifier`) | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Sondagem Adversarial Independente** | 4 sondagens (paridade `float64`, exclusão estrutural de hashes, escape LaTeX, caminhos POSIX/Windows) | Todas as 4 sondagens adversariais aprovadas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte do Marco M7.1

```text
.venv/bin/pytest tests/unit/reporting/ tests/integration/reporting/ -v
11 passed in 0.39s
```

### 2.2 Provas TLC (`check_proofs.py`)

```text
**HEAD**: 55ae9ab
**Tree**: clean
**Shell**: /bin/sh
**Result**: 11 pass, 0 fail
```

### 2.3 Suíte de Regressão Global

```text
.venv/bin/pytest tests/ -q
559 passed in 12.71s
```

---

## 3. Registro do Verificador Independente

- **Veredito:** `PASS`
- **Sondagens Realizadas:**
  1. Paridade exata `float64` entre `statistics/*.json`, `TableModel.rows` e `render_table_csv`, com distinção estrita de `None` (`"N/A"`), `UNDEFINED_NAN` (`"UNDEFINED_NAN"`) e `±Inf`.
  2. Exclusão estrutural de campos `*_hash`, `*_digest`, `sha256` e `checksum` preservando IDs legítimos de 64 caracteres hexadecimais.
  3. Escape LaTeX `booktabs` (`_`, `%`, `&`, `#`, `$`).
  4. Rejeição de caminhos absolutos POSIX e Windows em `ArtifactProvenance`.
- **Apontamentos:** Nenhum (`None`). Todos os 11 critérios C1 a C11 sustentam suas garantias formais.

---

## 4. Decisão Formal de Aceite

O Marco M7.1 cumpre integralmente `RF6.1`, `RF6.2`, `RF6.3`, `CA-E6-01`, `CA-E6-02` e `XCUT-02`.

**Decisão:** `APROVADO`
